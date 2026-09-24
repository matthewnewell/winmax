"""
Chat assist — same stateless, rebuild-context-every-call shape as every sibling app's. One
persistent assistant per pursuit, not the six specialized agent roles (Capture Manager,
Competitive Intel, Price-to-Win, Customer Intel, Proposal Strategist, Color Team Reviewer) the
original WinMaxxing teaser sketched — same restraint that pulled Value Stream back to one
chat pane instead of a per-field "AI Suggest" button.
"""

from flask import Blueprint, jsonify, request

import ai_client
from bands import p_go_band, p_win_band
from models import GATE_LABEL, Pursuit

bp = Blueprint("ai", __name__, url_prefix="/api")

SYSTEM_PROMPT = """You are the assistant embedded in WinMax, a P(Win)/P(Go)/Bid-No-Bid gated
pursuit tracker for government contract capture. These are three independent judgment calls,
scored/decided fresh at each gate, never blended into one number:

- P(Win): can we win it, if the procurement proceeds? Factors worth asking about: customer
  relationship strength, competitive position, solution fit, past performance alignment,
  price-to-win gap, incumbent advantage, teaming posture, black hat assessment (what the
  strongest competitor will propose), and provable discriminators.
- P(Go): will the government actually follow through on this procurement? Factors: budget
  appropriation status, requirement stability, program office track record, congressional/
  administration priority, urgency of need, acquisition strategy lock, incumbent protest
  exposure, market research signals.
- Bid/No-Bid: should the company fund the chase at all, independent of whether it could win?
  Factors: strategic fit, cost to pursue, expected value vs. pursuit cost, resource
  availability, capacity impact, pipeline opportunity cost, margin expectations, risk profile,
  teaming dependencies.

Gating order matters: P(Go) gates first (if the government won't follow through, nothing else
matters), P(Win) gates second (don't invest in proving you can win something you can't), Bid/
No-Bid gates third (walk away even from a probable win if the economics don't work).

Your job:
- Challenge a score if the note doesn't support it — a P(Win) of 75% with a note that only says
  "good relationship" is under-evidenced; say so, and ask what price-to-win, competitive
  position, and discriminator evidence backs the number.
- Notice when P(Go) is being ignored while capture investment ramps on P(Win) alone — that's
  the exact anti-pattern metrics.md warns about.
- Never invent facts about this pursuit that aren't in the context below.
"""


def _build_portfolio_context() -> str:
    """Same idea as `_build_context`, one level up — every pursuit's current state, for the
    Pursuits list page's Agent (no single pursuit in view there). Scores/bid only show the
    latest call at each metric, not the full history — this is a pipeline-wide skim, not a
    replacement for a specific pursuit's own deeper chat."""
    pursuits = Pursuit.query.order_by(Pursuit.created_at.desc()).all()
    if not pursuits:
        return "No pursuits tracked yet."
    lines = [f"{len(pursuits)} pursuits tracked:"]
    for p in pursuits:
        p_win = p.latest_score("p_win")
        p_go = p.latest_score("p_go")
        bid = p.latest_bid_decision()
        bits = [
            f'"{p.name}"',
            f"customer: {p.customer or 'unknown'}",
            f"gate: {GATE_LABEL[p.current_gate]}",
            f"status: {p.status}",
            f"P(Win): {f'{p_win.score}%' if p_win else 'not assessed'}",
            f"P(Go): {f'{p_go.score}%' if p_go else 'not assessed'}",
            f"Bid/No-Bid: {bid.decision if bid else 'not decided'}",
        ]
        lines.append("  - " + ", ".join(bits))
    return "\n".join(lines)


def _build_context(p: Pursuit) -> str:
    lines = [f'Pursuit: "{p.name}" (customer: {p.customer or "unknown"}, gate: {GATE_LABEL[p.current_gate]}, status: {p.status})']
    if p.description:
        lines.append(f"Description: {p.description}")

    p_win = p.latest_score("p_win")
    p_go = p.latest_score("p_go")
    bid = p.latest_bid_decision()

    if p_win:
        band = p_win_band(p_win.score)["label"]
        lines.append(f"\nCurrent P(Win): {p_win.score}% ({band}) — {p_win.note}")
    else:
        lines.append("\nCurrent P(Win): not yet assessed")

    if p_go:
        band = p_go_band(p_go.score)["label"]
        lines.append(f"Current P(Go): {p_go.score}% ({band}) — {p_go.note}")
    else:
        lines.append("Current P(Go): not yet assessed")

    lines.append(f"Current Bid/No-Bid: {f'{bid.decision} — {bid.note}' if bid else 'not yet decided'}")

    lines.append("\nP(Win) history:")
    p_win_entries = [e for e in p.score_entries if e.metric == "p_win"]
    if p_win_entries:
        for e in p_win_entries:
            lines.append(f"  [{GATE_LABEL[e.gate]}] {e.score}% — {e.note}")
    else:
        lines.append("  (none)")

    lines.append("\nP(Go) history:")
    p_go_entries = [e for e in p.score_entries if e.metric == "p_go"]
    if p_go_entries:
        for e in p_go_entries:
            lines.append(f"  [{GATE_LABEL[e.gate]}] {e.score}% — {e.note}")
    else:
        lines.append("  (none)")

    return "\n".join(lines)


@bp.post("/chat")
def chat():
    if not ai_client.is_configured():
        return jsonify({"reply": "", "error": ai_client.NOT_CONFIGURED_MESSAGE})

    body = request.get_json(force=True) or {}
    messages = body.get("messages") or []
    if not messages:
        return jsonify({"error": "messages is required"}), 400

    # pursuit_id is optional: the Pursuits list page's Agent has no single pursuit in view, so
    # it gets a pipeline-wide skim instead (see _build_portfolio_context).
    pursuit_id = body.get("pursuit_id")
    context = _build_context(Pursuit.query.get_or_404(pursuit_id)) if pursuit_id else _build_portfolio_context()

    system = SYSTEM_PROMPT + "\n\n" + context
    reply = ai_client.chat(messages, system=system, max_tokens=1024)
    return jsonify({"reply": reply})
