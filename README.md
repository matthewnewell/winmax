# WinMax

A gated pursuit tracker — P(Win), P(Go), and Bid/No-Bid, each its own honest number, re-assessed
at every gate. This company's own replacement for the Deltek WinMax vendor product, built to
the definitions in the original WinMaxxing project's own `metrics.md`.

## The idea

**Three independent judgment calls, never blended into one score:**

- **P(Win)** — can we win it, if the procurement proceeds? Customer relationship strength,
  competitive position, solution fit, past performance alignment, price-to-win gap, incumbent
  advantage, teaming posture, black hat assessment, discriminators.
- **P(Go)** — will the government actually follow through on this procurement, independent of
  whether we could win it? Budget appropriation status, requirement stability, program office
  track record, congressional/administration priority, urgency of need, acquisition strategy
  lock, incumbent protest exposure, market research signals.
- **Bid/No-Bid** — should the company fund the chase at all, independent of the other two?
  Strategic fit, cost to pursue, expected value vs. pursuit cost, resource availability,
  capacity impact, pipeline opportunity cost, margin expectations, risk profile, teaming
  dependencies.

Gating order matters: **P(Go) gates first** (if the government won't follow through, nothing
else matters), **P(Win) gates second** (don't invest in proving you can win something you
can't), **Bid/No-Bid gates third** (walk away even from a probable win if the economics don't
work). The seed data includes a real example of this: a pursuit with a decent P(Win) (55%)
correctly killed by a low P(Go) (30%, Continuing-Resolution funding risk) — the anti-pattern
`metrics.md` warns about, avoided.

**Every score and every bid call requires a note.** The number is a judgment call; the note is
what keeps it honest — same "no fake precision" convention as every sibling app's required-note
history (Scope Manager's `%complete`, The Fixer's journal). Thresholds (the 4 bands per metric)
live in `backend/bands.py`, computed at read time rather than stored, so changing them re-bands
history automatically — `metrics.md` calls these "configurable at the organization level."

**Deliberately not modeled**: a structured field per named scoring factor (26 across all three
metrics). v1 surfaces the factor list as reference/guidance (the "?" button next to each score)
rather than 26 required inputs per assessment — the note is where an assessor actually weighs
them in their own words. **One AI assistant**, not the original teaser's six specialized agent
roles (Capture Manager, Competitive Intel, Price-to-Win, Customer Intel, Proposal Strategist,
Color Team Reviewer) — same restraint applied to Value Stream's chat pane.

## Stack

Same as the rest of this ecosystem — Flask + SQLAlchemy + SQLite backend, React + TypeScript +
Vite frontend, the same provider-agnostic `ai_client.py` (Claude/Gemini/Ollama, off by default).

## Running locally

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python app.py            # :8099, seeds 3 demo pursuits on first run

cd frontend
npm install
npm run dev                        # :5185, proxies /api to :8099
```

## Data model

- **Pursuit** — name, customer, project/portfolio (set once won), current gate, status.
- **ScoreEntry** — one P(Win) or P(Go) assessment: score 0–100, gate, required note, author.
  Current value is always the *latest* entry for that metric — no live column duplicating it.
- **BidDecision** — one go/no-go call: gate, required note, author. Same "latest wins" rule.
- **PursuitEvent** — the general journal (auto-captured field edits + manual notes). Separate
  from the two above on purpose: those already carry mandatory rationale.

## Status

v1 — pursuit list/detail, P(Win)/P(Go) assessment history with band-derived color coding, the
bid/no-bid call, a journal, and an AI chat pane. Seeded with 3 demo pursuits: a healthy climb
(Next-Gen Avionics Sustainment IDIQ), the P(Go)-kills-a-decent-P(Win) anti-pattern avoided
correctly (Legacy Radar Depot Repair Recompete), and a freshly qualified pursuit with no bid
call yet (Fleet Readiness Center Depot-Level Repair).
