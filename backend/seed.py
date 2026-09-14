"""
Demo seed — three pursuits chosen to show the actual point of the app: P(Go) gates P(Win), and
a pursuit can look winnable and still be a correct no-bid.

1. "Next-Gen Avionics Sustainment IDIQ" — the healthy case. P(Win) climbed as competitive
   intel came in (45% at Qualification -> 68% at Pre-Proposal), P(Go) has stayed strong
   throughout (funded, stable requirement), bid/no-bid re-confirmed "go" at each gate.
2. "Legacy Radar Depot Repair Recompete" — the anti-pattern metrics.md warns about, avoided
   correctly: a *decent* P(Win) (55%) killed by a *low* P(Go) (30%, Continuing-Resolution
   funding risk) — the team said no-bid at Capture Plan rather than chasing a proposal for a
   procurement that might not happen.
3. "Fleet Readiness Center Depot-Level Repair" — freshly qualified, one score each, no bid
   call yet — the ordinary starting state, not a solved case.
"""

from datetime import timedelta

from db import db
from models import BidDecision, Pursuit, ScoreEntry, _now

DAY = timedelta(days=1)
_PORTFOLIO = "Industrial Programs"

# Fixed (not random-uuid) id on the healthy demo pursuit — same convention as The Fixer's
# DEMO_CASE_ID — so the splash page's figure and the nav's "Demo" link can point straight at it.
DEMO_PURSUIT_ID = "demo-avionics-idiq"


def _pursuit(name, customer, gate, status, created_offset, id=None):
    return Pursuit(
        id=id, name=name, customer=customer, portfolio=_PORTFOLIO,
        current_gate=gate, status=status, created_by="Sam Ortiz (PM)",
        created_at=_now() + created_offset * DAY,
    )


def seed_if_empty():
    if Pursuit.query.count() > 0:
        return

    now = _now()

    # ── 1. Healthy case ──
    avionics = _pursuit(
        "Next-Gen Avionics Sustainment IDIQ", "Air Force Sustainment Center",
        "pre_proposal", "active", -75, id=DEMO_PURSUIT_ID,
    )
    db.session.add(avionics)
    db.session.flush()
    db.session.add_all([
        ScoreEntry(pursuit_id=avionics.id, metric="p_win", score=45, gate="qualification",
                   note="Early read — no incumbent relationship yet, but our sustainment past performance is directly relevant.",
                   author="Sam Ortiz (PM)", created_at=now - 70 * DAY),
        ScoreEntry(pursuit_id=avionics.id, metric="p_go", score=80, gate="qualification",
                   note="Fully funded in the enacted appropriation; program office has a clean history of awarding on schedule.",
                   author="Sam Ortiz (PM)", created_at=now - 70 * DAY),
        BidDecision(pursuit_id=avionics.id, decision="go", gate="qualification",
                    note="Strong strategic fit — grows our sustainment portfolio in exactly the segment we're targeting.",
                    author="Sam Ortiz (PM)", created_at=now - 68 * DAY),
        ScoreEntry(pursuit_id=avionics.id, metric="p_win", score=58, gate="capture_plan",
                   note="Black hat session identified the likely incumbent team's weak spot: aging test equipment. We can discriminate on modernized diagnostics.",
                   author="Sam Ortiz (PM)", created_at=now - 40 * DAY),
        ScoreEntry(pursuit_id=avionics.id, metric="p_go", score=82, gate="capture_plan",
                   note="Requirement has been stable for two review cycles; no acquisition strategy disputes visible.",
                   author="Sam Ortiz (PM)", created_at=now - 40 * DAY),
        BidDecision(pursuit_id=avionics.id, decision="go", gate="capture_plan",
                    note="Capture investment authorized — CI and PTW work confirmed the discriminator is real, not assumed.",
                    author="Sam Ortiz (PM)", created_at=now - 38 * DAY),
        ScoreEntry(pursuit_id=avionics.id, metric="p_win", score=68, gate="pre_proposal",
                   note="Price-to-win gap closed to within 4% after the latest should-cost model; teaming with a small-business partner fills our one capability gap.",
                   author="Sam Ortiz (PM)", created_at=now - 5 * DAY),
        ScoreEntry(pursuit_id=avionics.id, metric="p_go", score=78, gate="pre_proposal",
                   note="Still on track; one Congressional staffer inquiry noted but not a red flag yet.",
                   author="Sam Ortiz (PM)", created_at=now - 5 * DAY),
    ])

    # ── 2. The anti-pattern, avoided ──
    radar = _pursuit(
        "Legacy Radar Depot Repair Recompete", "Naval Air Systems Command",
        "capture_plan", "no_bid", -50,
    )
    db.session.add(radar)
    db.session.flush()
    db.session.add_all([
        ScoreEntry(pursuit_id=radar.id, metric="p_win", score=55, gate="qualification",
                   note="We're the incumbent's closest competitor on past performance; solution fit is solid.",
                   author="Dana Kim (PM)", created_at=now - 48 * DAY),
        ScoreEntry(pursuit_id=radar.id, metric="p_go", score=30, gate="qualification",
                   note="Program is operating under a Continuing Resolution with no new-start authority yet; two industry days announced then quietly postponed.",
                   author="Dana Kim (PM)", created_at=now - 48 * DAY),
        BidDecision(pursuit_id=radar.id, decision="no_go", gate="capture_plan",
                    note="P(Go) hasn't moved off high-risk in 6 weeks despite a decent P(Win) — this is exactly the trap metrics.md warns about. Declining to invest capture budget until the CR resolves.",
                    author="Dana Kim (PM)", created_at=now - 20 * DAY),
    ])

    # ── 3. Freshly qualified, no bid call yet ──
    frc = _pursuit(
        "Fleet Readiness Center Depot-Level Repair", "Naval Air Systems Command",
        "qualification", "active", -6,
    )
    db.session.add(frc)
    db.session.flush()
    db.session.add_all([
        ScoreEntry(pursuit_id=frc.id, metric="p_win", score=40, gate="qualification",
                   note="No customer access yet — score reflects solution fit alone until we get a call with the program office.",
                   author="Dana Kim (PM)", created_at=now - 4 * DAY),
        ScoreEntry(pursuit_id=frc.id, metric="p_go", score=55, gate="qualification",
                   note="Budget line exists but requirement (PWS) has changed twice already this year.",
                   author="Dana Kim (PM)", created_at=now - 4 * DAY),
    ])

    db.session.commit()
