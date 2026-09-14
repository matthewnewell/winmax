"""
WinMax: a P(Win)/P(Go)/Bid-No-Bid gated pursuit tracker — this company's own replacement for
the Deltek WinMax vendor product, built to the definitions in the WinMaxxing project's own
`metrics.md` (P(Win): can we win it, P(Go): will the government follow through, Bid/No-Bid:
should we fund the chase — three independent judgment calls, not one blended score).

Every score and every bid/no-bid call is a **living, re-assessed-at-each-gate judgment**, never
a one-time computation — `metrics.md`'s own words: "should be visible and tracked over time, not
just point-in-time snapshots" and "flag when scores diverge significantly... and prompt the
capture manager to explain why." So there is no live `p_win`/`p_go`/`decision` column on
`Pursuit` at all — current state is always the *latest* `ScoreEntry`/`BidDecision` for that
pursuit, same "compute from the latest record, never duplicate a stored current value" pattern
as DWMP's `current_status()` and Scope Manager's `ScopeProgressEvent`. A `note` is required on
every entry for the same reason Scope Manager requires one on every %-complete update: the
number is a judgment call, and the note is what keeps it honest.

**Deliberately not modeled**: a structured field per named scoring factor (metrics.md lists 9
for P(Win), 8 for P(Go), 9 for Bid/No-Bid — 26 inputs per assessment). That's real complexity
for a v2 if it turns out to matter; v1 surfaces the factor list as reference/guidance next to
the score input instead, and the `note` is where an assessor actually weighs them in their own
words — same "start with one AI assistant, not six specialized agent roles" restraint the
original teaser's own brainstorm called for.
"""

from datetime import datetime, timezone

from bands import p_go_band, p_win_band
from db import _uuid, db


def _now():
    return datetime.now(timezone.utc)


# 15288-adjacent gate names, but this is DoD/govcon capture convention (qualification through
# final proposal review), not a 15288 clause — matches metrics.md's own "Lifecycle cadence" and
# "Gate investment model" sections exactly.
GATES = ("qualification", "capture_plan", "pre_proposal", "rfp_release", "final_proposal_review")
GATE_LABEL = {
    "qualification": "Qualification",
    "capture_plan": "Capture Plan",
    "pre_proposal": "Pre-Proposal",
    "rfp_release": "RFP Release",
    "final_proposal_review": "Final Proposal Review",
}

PURSUIT_STATUSES = ("active", "no_bid", "lost", "won")

METRICS = ("p_win", "p_go")
METRIC_LABEL = {"p_win": "P(Win)", "p_go": "P(Go)"}

BID_DECISIONS = ("go", "no_go")


class Pursuit(db.Model):
    """One opportunity being tracked. `project`/`portfolio` are the same plain-text labels used
    everywhere else in this ecosystem — set once a pursuit is actually won and becomes a real
    project (matching DWMP/DWMO's own "not every part/order has a project yet" nullability), not
    required to start tracking a pursuit."""

    __tablename__ = "pursuit"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    name = db.Column(db.String(300), nullable=False)
    customer = db.Column(db.String(200), nullable=True)
    project = db.Column(db.String(200), nullable=True, index=True)
    portfolio = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    current_gate = db.Column(db.String(30), nullable=False, default="qualification")
    status = db.Column(db.String(20), nullable=False, default="active")
    created_by = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=_now, nullable=False)

    score_entries = db.relationship(
        "ScoreEntry", backref="pursuit", cascade="all, delete-orphan", order_by="ScoreEntry.created_at",
    )
    bid_decisions = db.relationship(
        "BidDecision", backref="pursuit", cascade="all, delete-orphan", order_by="BidDecision.created_at",
    )

    def latest_score(self, metric: str) -> "ScoreEntry | None":
        entries = [e for e in self.score_entries if e.metric == metric]
        return entries[-1] if entries else None

    def latest_bid_decision(self) -> "BidDecision | None":
        return self.bid_decisions[-1] if self.bid_decisions else None

    def to_dict(self, include_history: bool = False) -> dict:
        p_win = self.latest_score("p_win")
        p_go = self.latest_score("p_go")
        bid = self.latest_bid_decision()
        d = {
            "id": self.id,
            "name": self.name,
            "customer": self.customer,
            "project": self.project,
            "portfolio": self.portfolio,
            "description": self.description,
            "current_gate": self.current_gate,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "p_win": p_win.to_dict() if p_win else None,
            "p_go": p_go.to_dict() if p_go else None,
            "bid_decision": bid.to_dict() if bid else None,
        }
        if include_history:
            d["score_history"] = [e.to_dict() for e in self.score_entries]
            d["bid_history"] = [b.to_dict() for b in self.bid_decisions]
        return d


class PursuitEvent(db.Model):
    """The pursuit's general journal — separate from `ScoreEntry`/`BidDecision` on purpose,
    same split as Scope Manager's `ScopeEvent` vs `ScopeProgressEvent`. This covers auto-
    captured edits to the pursuit's own static fields (name, customer, gate, status) and
    freestanding manual notes; a P(Win)/P(Go) score or a bid/no-bid call always carries its own
    required rationale already, so those never duplicate into this feed."""

    __tablename__ = "pursuit_event"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    pursuit_id = db.Column(db.String(36), db.ForeignKey("pursuit.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=_now, nullable=False, index=True)
    author = db.Column(db.String(120), nullable=True)

    kind = db.Column(db.String(20), nullable=False, default="note")  # "note" | "change"

    field = db.Column(db.String(60), nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)

    note = db.Column(db.Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pursuit_id": self.pursuit_id,
            "created_at": self.created_at.isoformat(),
            "author": self.author,
            "kind": self.kind,
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "note": self.note,
        }


class ScoreEntry(db.Model):
    """One P(Win) or P(Go) assessment, at a gate, with a required note explaining it — see
    module docstring. `score` is 0-100; band (no-bid/caution/competitive/strong for P(Win),
    the equivalent four for P(Go)) is computed from `metrics.md`'s own threshold table, not
    stored — thresholds are meant to be "configurable at the organization level" per that doc,
    so deriving the band at read time (see `bands.py`) means changing them later doesn't
    require rewriting history."""

    __tablename__ = "score_entry"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    pursuit_id = db.Column(db.String(36), db.ForeignKey("pursuit.id"), nullable=False, index=True)
    metric = db.Column(db.String(10), nullable=False)  # "p_win" | "p_go"
    score = db.Column(db.Integer, nullable=False)
    gate = db.Column(db.String(30), nullable=False)
    note = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=_now, nullable=False)

    def to_dict(self) -> dict:
        band = (p_win_band if self.metric == "p_win" else p_go_band)(self.score)
        return {
            "id": self.id,
            "pursuit_id": self.pursuit_id,
            "metric": self.metric,
            "score": self.score,
            "band": band,
            "gate": self.gate,
            "note": self.note,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
        }


class BidDecision(db.Model):
    """One bid/no-bid call, at a gate — a decision, not a score (see metrics.md: "even a pursuit
    with high scores on both [P(Win) and P(Go)] may be a wrong investment... at this time").
    Required note is the rationale — strategic fit, cost to pursue, ROI, capacity, whatever the
    assessor actually weighed."""

    __tablename__ = "bid_decision"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    pursuit_id = db.Column(db.String(36), db.ForeignKey("pursuit.id"), nullable=False, index=True)
    decision = db.Column(db.String(10), nullable=False)  # "go" | "no_go"
    gate = db.Column(db.String(30), nullable=False)
    note = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=_now, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pursuit_id": self.pursuit_id,
            "decision": self.decision,
            "gate": self.gate,
            "note": self.note,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
        }
