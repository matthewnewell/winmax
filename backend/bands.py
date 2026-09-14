"""
Threshold bands for P(Win) and P(Go), exactly as defined in the WinMaxxing project's own
`metrics.md`. Kept as pure functions, not stored on `ScoreEntry` — metrics.md calls these
"configurable at the organization level," so a later change here re-bands every existing score
automatically instead of requiring a backfill.
"""

# (max_exclusive, band_key, label, guidance) — checked in order, first match wins.
P_WIN_BANDS = [
    (25, "no_bid", "No-bid territory", "Recommend no-bid or a major strategy pivot."),
    (50, "caution", "Proceed with caution", "Identify what would need to change to improve the score."),
    (70, "competitive", "Competitive position", "Continue with active capture."),
    (101, "strong", "Strong position", "Maintain discipline — don't get complacent."),
]

P_GO_BANDS = [
    (40, "high_risk", "High cancellation/delay risk", "Do not invest significantly; monitor only."),
    (65, "careful", "Proceed carefully", "Build contingencies and set investment caps."),
    (85, "reasonable", "Reasonable confidence", "Proceed with standard capture investment."),
    (101, "high_confidence", "High confidence", "Full capture investment justified."),
]


def _band(score: int, table: list[tuple[int, str, str, str]]) -> dict:
    for max_exclusive, key, label, guidance in table:
        if score < max_exclusive:
            return {"key": key, "label": label, "guidance": guidance}
    return {"key": table[-1][1], "label": table[-1][2], "guidance": table[-1][3]}


def p_win_band(score: int) -> dict:
    return _band(score, P_WIN_BANDS)


def p_go_band(score: int) -> dict:
    return _band(score, P_GO_BANDS)
