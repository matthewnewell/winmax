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
# The other pursuits' ids are pinned too: they're the same ids as their Depot projects (and Good
# Plan's plans), so Labor Supply & Demand's Outlook can join a plan to its P(Win) by id.
RADAR_PURSUIT_ID = "253e7b04-1bab-4467-83fe-b2249cbcbe5f"
FRC_PURSUIT_ID = "058bf4bb-5a4b-44c9-9163-8e9935e883a3"
COASTAL_PURSUIT_ID = "d4e7a1b9-5c28-4360-9f1a-e83b0c6d72f5"


# Illustrative demo numbers: estimated value (total contract value with options, or the IDIQ
# ceiling) and expected award date, as days from today so the demo never goes stale.
PLANNING = {
    DEMO_PURSUIT_ID: (185_000_000, 150),
    RADAR_PURSUIT_ID: (32_000_000, 60),
    FRC_PURSUIT_ID: (64_000_000, 300),
    COASTAL_PURSUIT_ID: (27_000_000, 200),
}


def _pursuit(name, customer, gate, status, created_offset, id=None, portfolio=_PORTFOLIO):
    value, award_in_days = PLANNING.get(id, (None, None))
    return Pursuit(
        id=id, name=name, customer=customer, portfolio=portfolio,
        current_gate=gate, status=status, created_by="Sam Ortiz (PM)",
        created_at=_now() + created_offset * DAY,
        estimated_value=value,
        expected_award_date=(_now() + award_in_days * DAY).date() if award_in_days else None,
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
        "capture_plan", "no_bid", -50, id=RADAR_PURSUIT_ID,
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
        "qualification", "active", -6, id=FRC_PURSUIT_ID,
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


def seed_coastal_if_missing():
    """The Depot's "Prospect: Coastal Patrol Recompete" as a pursuit, so it carries a P(Win) too.
    Idempotent: added to a live database that was seeded before it existed."""
    if db.session.get(Pursuit, COASTAL_PURSUIT_ID) is not None:
        return
    now = _now()
    coastal = _pursuit(
        "Prospect: Coastal Patrol Recompete", "Coast Guard Surface Forces Logistics Center",
        "capture_plan", "active", -40, id=COASTAL_PURSUIT_ID, portfolio="Defense Systems",
    )
    db.session.add(coastal)
    db.session.flush()
    db.session.add_all([
        ScoreEntry(pursuit_id=coastal.id, metric="p_win", score=30, gate="qualification",
                   note="Incumbent recompete; the incumbent's CPARS are strong and we have no patrol-boat past performance yet.",
                   author="Dana Kim (PM)", created_at=now - 38 * DAY),
        ScoreEntry(pursuit_id=coastal.id, metric="p_go", score=70, gate="qualification",
                   note="Funded in the current budget and on the forecast; RFP expected next quarter.",
                   author="Dana Kim (PM)", created_at=now - 38 * DAY),
        BidDecision(pursuit_id=coastal.id, decision="go", gate="qualification",
                    note="Go, on the teaming agreement with a patrol-boat yard for the past-performance gap.",
                    author="Dana Kim (PM)", created_at=now - 30 * DAY),
        ScoreEntry(pursuit_id=coastal.id, metric="p_win", score=35, gate="capture_plan",
                   note="Teaming partner signed; still an underdog against the incumbent.",
                   author="Dana Kim (PM)", created_at=now - 10 * DAY),
        ScoreEntry(pursuit_id=coastal.id, metric="p_go", score=72, gate="capture_plan",
                   note="Draft RFP released; requirement matches the forecast.",
                   author="Dana Kim (PM)", created_at=now - 10 * DAY),
    ])
    db.session.commit()
