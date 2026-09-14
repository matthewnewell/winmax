"""Journal capture for a pursuit's own static fields — same shape as Scope Manager's/The
Fixer's journal.py. Score and bid/no-bid changes are NOT logged here; those go through
ScoreEntry/BidDecision, which already require their own rationale."""

from datetime import datetime, timezone

from db import db
from models import PursuitEvent

PURSUIT_FIELDS = {
    "name": "name",
    "customer": "customer",
    "portfolio": "portfolio",
    "current_gate": "gate",
    "status": "status",
}


def _fmt(value) -> str:
    if value is None or value == "":
        return "—"
    return str(value)


def record_changes(
    pursuit_id: str,
    before: dict,
    after: dict,
    fields: dict = PURSUIT_FIELDS,
    *,
    author: str | None = None,
    note: str | None = None,
) -> bool:
    author = (author or "").strip() or None
    ts = datetime.now(timezone.utc)
    changed = False
    for field, label in fields.items():
        old, new = before.get(field), after.get(field)
        if old == new:
            continue
        changed = True
        db.session.add(
            PursuitEvent(
                pursuit_id=pursuit_id, created_at=ts, author=author,
                kind="change", field=label, old_value=_fmt(old), new_value=_fmt(new),
            )
        )
    if note and note.strip():
        db.session.add(
            PursuitEvent(pursuit_id=pursuit_id, created_at=ts, author=author, kind="note", note=note.strip())
        )
    return changed
