import os

from flask import Blueprint, jsonify, request

from bands import p_win_band
from models import GATE_LABEL, METRIC_LABEL, BidDecision, Pursuit, PursuitEvent, ScoreEntry

bp = Blueprint("summary", __name__, url_prefix="/api")

# Where this app's own frontend lives, for building a deep link into the summarized pursuit —
# not read from Conway's Depot, same "stays unaware of the Depot" stance Value Stream's own
# /api/summary takes (see its routes/summary.py).
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "http://localhost:5185")


@bp.get("/summary")
def summary():
    """The Launchpad's app-summary contract (see Conway's Depot's routes/applications.py for
    the proxy that calls this, and Value Stream's routes/summary.py for the sibling
    implementation this one mirrors). `project_id` here is never Conway's Depot's own project
    id — the Depot translates it through its ProjectAppLink.external_ref crosswalk into one of
    this app's own pursuit ids before calling in. No match (missing id, a pursuit that was
    never linked) is a normal state, not an error — same null-headline shape Depot itself falls
    back to.

    Surfaces the two things a PM glancing at a Launchpad tile actually wants from a capture:
    P(Win) as the headline (the number that drives bid/no-bid), and the current gate as the
    label (where the pursuit sits in the qualification->final-proposal-review cadence).
    metrics.md's own threshold bands set the status color — no_bid is critical, caution is
    warn, competitive/strong is ok — the same reading the app's own ScoreBadge uses."""
    pursuit_id = request.args.get("project_id")
    p = Pursuit.query.get(pursuit_id) if pursuit_id else None
    if p is None:
        return jsonify({"headline": None, "label": "No pursuit linked yet", "status": None, "href": None})

    p_win = p.latest_score("p_win")
    gate_label = GATE_LABEL.get(p.current_gate, p.current_gate)

    if p_win is None:
        return jsonify({
            "headline": None,
            "label": f"{gate_label} gate — not yet scored",
            "status": None,
            "href": f"{FRONTEND_BASE_URL}/pursuits/{p.id}",
        })

    band = p_win_band(p_win.score)
    status = "critical" if band["key"] == "no_bid" else "warn" if band["key"] == "caution" else "ok"

    return jsonify({
        "headline": f"{p_win.score}% P(Win)",
        "label": f"{gate_label} gate · {band['label']}",
        "status": status,
        "href": f"{FRONTEND_BASE_URL}/pursuits/{p.id}",
    })


@bp.get("/journal")
def journal():
    """The Launchpad's cross-app journal contract (see Value Stream's routes/summary.py for the
    sibling implementation this one mirrors, and Conway's Depot's project-level aggregator for
    how these get merged with every other connected app's entries). `project_id` here is one of
    this app's own pursuit ids, translated the same way /summary's is.

    Merges three tables into one timeline, not just PursuitEvent: a P(Win)/P(Go) score or a
    bid/no-bid call is exactly the kind of thing "how we got here" needs, and each already
    carries its own required rationale (see ScoreEntry/BidDecision's own docstrings) — leaving
    them out because they live in a separate table would make this feed actively misleading,
    not just incomplete. This app owns the wording of every `summary` line; the Depot never
    parses it back apart."""
    pursuit_id = request.args.get("project_id")
    p = Pursuit.query.get(pursuit_id) if pursuit_id else None
    if p is None:
        return jsonify({"entries": []})

    href = f"{FRONTEND_BASE_URL}/pursuits/{p.id}"
    rows: list[dict] = []

    for e in PursuitEvent.query.filter_by(pursuit_id=p.id).all():
        if e.kind == "change":
            summary = f"{e.field} changed from “{e.old_value}” to “{e.new_value}”"
            if e.note:
                summary += f" — {e.note}"
        else:
            summary = e.note or ""
        rows.append({"id": e.id, "timestamp": e.created_at, "author": e.author, "summary": summary})

    for s in ScoreEntry.query.filter_by(pursuit_id=p.id).all():
        gate_label = GATE_LABEL.get(s.gate, s.gate)
        metric_label = METRIC_LABEL.get(s.metric, s.metric)
        summary = f"{metric_label} scored {s.score}% at {gate_label} — “{s.note}”"
        rows.append({"id": s.id, "timestamp": s.created_at, "author": s.author, "summary": summary})

    for b in BidDecision.query.filter_by(pursuit_id=p.id).all():
        gate_label = GATE_LABEL.get(b.gate, b.gate)
        call = "GO" if b.decision == "go" else "NO-GO"
        summary = f"Bid decision: {call} at {gate_label} — “{b.note}”"
        rows.append({"id": b.id, "timestamp": b.created_at, "author": b.author, "summary": summary})

    rows.sort(key=lambda r: r["timestamp"], reverse=True)
    entries = [{**r, "timestamp": r["timestamp"].isoformat(), "href": href} for r in rows[:200]]
    return jsonify({"entries": entries})
