from datetime import date

from flask import Blueprint, jsonify, request

import journal
from db import db
from models import BID_DECISIONS, GATES, METRICS, PURSUIT_STATUSES, BidDecision, Pursuit, PursuitEvent, ScoreEntry

bp = Blueprint("pursuits", __name__, url_prefix="/api")


# ── Pursuits ─────────────────────────────────────────────────────────────────────────────────

@bp.get("/pursuits")
def list_pursuits():
    q = Pursuit.query
    if project := request.args.get("project"):
        q = q.filter(Pursuit.project == project)
    if portfolio := request.args.get("portfolio"):
        q = q.filter(Pursuit.portfolio == portfolio)
    if status := request.args.get("status"):
        q = q.filter(Pursuit.status == status)
    pursuits = q.order_by(Pursuit.created_at.desc()).all()
    return jsonify([p.to_dict() for p in pursuits])


@bp.get("/pursuits/<pursuit_id>")
def get_pursuit(pursuit_id):
    p = Pursuit.query.get_or_404(pursuit_id)
    return jsonify(p.to_dict(include_history=True))


@bp.get("/projects")
def list_projects():
    rows = db.session.query(Pursuit.project).filter(Pursuit.project.isnot(None)).distinct().all()
    return jsonify(sorted({r[0] for r in rows if r[0]}))


def _parse_planning(body: dict) -> tuple[dict, str | None]:
    """The two planning fields, for whichever of them the body carries. Null or "" clears one.
    Returns (values to set, error message)."""
    out: dict = {}
    if "estimated_value" in body:
        v = body["estimated_value"]
        if v is None or v == "":
            out["estimated_value"] = None
        else:
            try:
                n = round(float(v))
            except (TypeError, ValueError):
                return {}, "estimated_value must be a dollar amount"
            if n < 0:
                return {}, "estimated_value can't be negative"
            out["estimated_value"] = n
    if "expected_award_date" in body:
        v = body["expected_award_date"]
        if v is None or v == "":
            out["expected_award_date"] = None
        else:
            try:
                out["expected_award_date"] = date.fromisoformat(str(v))
            except ValueError:
                return {}, "expected_award_date must be a date (YYYY-MM-DD)"
    return out, None


def _validate_create(body: dict) -> tuple[dict, int] | None:
    if not (body.get("name") or "").strip():
        return {"error": "name is required"}, 400
    if body.get("current_gate") and body["current_gate"] not in GATES:
        return {"error": f"current_gate must be one of {GATES}"}, 400
    if body.get("status") and body["status"] not in PURSUIT_STATUSES:
        return {"error": f"status must be one of {PURSUIT_STATUSES}"}, 400
    return None


@bp.post("/pursuits")
def create_pursuit():
    body = request.get_json(force=True) or {}
    err = _validate_create(body)
    if err:
        return jsonify(err[0]), err[1]
    planning, planning_err = _parse_planning(body)
    if planning_err:
        return jsonify({"error": planning_err}), 400

    p = Pursuit(
        **planning,
        name=body["name"].strip(),
        customer=(body.get("customer") or "").strip() or None,
        project=(body.get("project") or "").strip() or None,
        portfolio=(body.get("portfolio") or "").strip() or None,
        description=(body.get("description") or "").strip() or None,
        current_gate=body.get("current_gate") or "qualification",
        status=body.get("status") or "active",
        created_by=(body.get("created_by") or "").strip() or None,
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict()), 201


def _journal_snapshot(p: Pursuit) -> dict:
    return {f: getattr(p, f) for f in journal.PURSUIT_FIELDS}


@bp.put("/pursuits/<pursuit_id>")
def update_pursuit(pursuit_id):
    """Static fields — name, customer, portfolio, gate, status, estimated value, expected award
    date. Every changed field is auto-logged to the journal; an optional `journal_note` (plus
    `author`) rides along in the same save."""
    p = Pursuit.query.get_or_404(pursuit_id)
    body = request.get_json(force=True) or {}
    if body.get("current_gate") and body["current_gate"] not in GATES:
        return jsonify({"error": f"current_gate must be one of {GATES}"}), 400
    if body.get("status") and body["status"] not in PURSUIT_STATUSES:
        return jsonify({"error": f"status must be one of {PURSUIT_STATUSES}"}), 400
    planning, planning_err = _parse_planning(body)
    if planning_err:
        return jsonify({"error": planning_err}), 400

    before = _journal_snapshot(p)
    for field, value in planning.items():
        setattr(p, field, value)
    if "name" in body:
        if not (body.get("name") or "").strip():
            return jsonify({"error": "name is required"}), 400
        p.name = body["name"].strip()
    if "customer" in body:
        p.customer = (body.get("customer") or "").strip() or None
    if "project" in body:
        p.project = (body.get("project") or "").strip() or None
    if "portfolio" in body:
        p.portfolio = (body.get("portfolio") or "").strip() or None
    if "description" in body:
        p.description = (body.get("description") or "").strip() or None
    if "current_gate" in body:
        p.current_gate = body["current_gate"]
    if "status" in body:
        p.status = body["status"]

    journal.record_changes(
        p.id, before, _journal_snapshot(p), author=body.get("author"), note=body.get("journal_note"),
    )
    db.session.commit()
    return jsonify(p.to_dict())


@bp.delete("/pursuits/<pursuit_id>")
def delete_pursuit(pursuit_id):
    p = Pursuit.query.get_or_404(pursuit_id)
    # Journal events aren't on a cascading relationship (scores and bid calls are), and foreign
    # keys are enforced, so an edited pursuit can't be deleted until its events are gone.
    PursuitEvent.query.filter_by(pursuit_id=p.id).delete()
    db.session.delete(p)
    db.session.commit()
    return "", 204


# ── P(Win) / P(Go) scores ────────────────────────────────────────────────────────────────────

@bp.post("/pursuits/<pursuit_id>/scores")
def add_score(pursuit_id):
    """The only way P(Win)/P(Go) ever change — a fresh, noted assessment, not a field flip.
    `note` is required (see models.py)."""
    p = Pursuit.query.get_or_404(pursuit_id)
    body = request.get_json(force=True) or {}

    metric = body.get("metric")
    if metric not in METRICS:
        return jsonify({"error": f"metric must be one of {METRICS}"}), 400

    score = body.get("score")
    if not isinstance(score, int) or not (0 <= score <= 100):
        return jsonify({"error": "score must be an integer 0-100"}), 400

    gate = body.get("gate") or p.current_gate
    if gate not in GATES:
        return jsonify({"error": f"gate must be one of {GATES}"}), 400

    note = (body.get("note") or "").strip()
    if not note:
        return jsonify({"error": "note is required — say what evidence moved the score"}), 400

    entry = ScoreEntry(
        pursuit_id=p.id, metric=metric, score=score, gate=gate, note=note,
        author=(body.get("author") or "").strip() or None,
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(p.to_dict()), 201


# ── Bid / No-Bid ─────────────────────────────────────────────────────────────────────────────

@bp.post("/pursuits/<pursuit_id>/bid-decisions")
def add_bid_decision(pursuit_id):
    p = Pursuit.query.get_or_404(pursuit_id)
    body = request.get_json(force=True) or {}

    decision = body.get("decision")
    if decision not in BID_DECISIONS:
        return jsonify({"error": f"decision must be one of {BID_DECISIONS}"}), 400

    gate = body.get("gate") or p.current_gate
    if gate not in GATES:
        return jsonify({"error": f"gate must be one of {GATES}"}), 400

    note = (body.get("note") or "").strip()
    if not note:
        return jsonify({"error": "note is required — the rationale for this call"}), 400

    entry = BidDecision(
        pursuit_id=p.id, decision=decision, gate=gate, note=note,
        author=(body.get("author") or "").strip() or None,
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(p.to_dict()), 201


# ── Journal ──────────────────────────────────────────────────────────────────────────────────

@bp.get("/pursuits/<pursuit_id>/events")
def list_events(pursuit_id):
    Pursuit.query.get_or_404(pursuit_id)
    events = (
        PursuitEvent.query.filter_by(pursuit_id=pursuit_id)
        .order_by(PursuitEvent.created_at.desc(), PursuitEvent.kind.asc(), PursuitEvent.id.asc())
        .all()
    )
    return jsonify([e.to_dict() for e in events])


@bp.post("/pursuits/<pursuit_id>/events")
def add_event(pursuit_id):
    Pursuit.query.get_or_404(pursuit_id)
    body = request.get_json(force=True) or {}
    note = (body.get("note") or "").strip()
    if not note:
        return jsonify({"error": "note is required"}), 400

    ev = PursuitEvent(
        pursuit_id=pursuit_id, kind="note", note=note, author=(body.get("author") or "").strip() or None,
    )
    db.session.add(ev)
    db.session.commit()
    return jsonify(ev.to_dict()), 201


@bp.delete("/events/<event_id>")
def delete_event(event_id):
    ev = PursuitEvent.query.get_or_404(event_id)
    if ev.kind != "note":
        return jsonify({"error": "only manual notes can be deleted; change history is permanent"}), 400
    db.session.delete(ev)
    db.session.commit()
    return "", 204
