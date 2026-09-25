import os
import sys

os.environ["DATA_DIR"] = os.path.join(os.path.dirname(__file__), "_tmp_data")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import shutil

import pytest

from app import create_app
from db import db


@pytest.fixture()
def client():
    shutil.rmtree(os.environ["DATA_DIR"], ignore_errors=True)
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    with app.app_context():
        db.session.remove()
    shutil.rmtree(os.environ["DATA_DIR"], ignore_errors=True)


def test_seeded_pursuits(client):
    res = client.get("/api/pursuits")
    assert res.status_code == 200
    pursuits = res.get_json()
    assert len(pursuits) == 4

    avionics = next(p for p in pursuits if "Avionics" in p["name"])
    assert avionics["p_win"]["score"] == 68
    assert avionics["p_win"]["band"]["key"] == "competitive"
    assert avionics["p_go"]["band"]["key"] == "reasonable"
    assert avionics["bid_decision"]["decision"] == "go"

    radar = next(p for p in pursuits if "Radar" in p["name"])
    assert radar["status"] == "no_bid"
    assert radar["p_win"]["band"]["key"] == "competitive"  # 55% -> competitive (50-70 band)
    assert radar["p_go"]["band"]["key"] == "high_risk"  # 30% -> high risk
    assert radar["bid_decision"]["decision"] == "no_go"


def test_get_pursuit_includes_history(client):
    pursuits = client.get("/api/pursuits").get_json()
    avionics = next(p for p in pursuits if "Avionics" in p["name"])
    detail = client.get(f"/api/pursuits/{avionics['id']}").get_json()
    p_win_history = [e for e in detail["score_history"] if e["metric"] == "p_win"]
    assert len(p_win_history) == 3
    assert [e["score"] for e in p_win_history] == [45, 58, 68]


def test_create_pursuit_requires_name(client):
    res = client.post("/api/pursuits", json={"customer": "X"})
    assert res.status_code == 400


def test_create_and_update_pursuit_journals_changes(client):
    created = client.post("/api/pursuits", json={"name": "Test Pursuit", "customer": "Test Agency"})
    assert created.status_code == 201
    pid = created.get_json()["id"]

    updated = client.put(f"/api/pursuits/{pid}", json={
        "current_gate": "capture_plan", "author": "Tester", "journal_note": "Advancing after qual review.",
    })
    assert updated.status_code == 200
    assert updated.get_json()["current_gate"] == "capture_plan"

    events = client.get(f"/api/pursuits/{pid}/events").get_json()
    kinds = {e["kind"] for e in events}
    assert "change" in kinds
    assert "note" in kinds
    change = next(e for e in events if e["kind"] == "change")
    assert change["field"] == "gate"
    assert change["old_value"] == "qualification"
    assert change["new_value"] == "capture_plan"


def test_add_score_requires_note_and_valid_range(client):
    created = client.post("/api/pursuits", json={"name": "Test Pursuit"})
    pid = created.get_json()["id"]

    res = client.post(f"/api/pursuits/{pid}/scores", json={"metric": "p_win", "score": 50})
    assert res.status_code == 400  # missing note

    res = client.post(f"/api/pursuits/{pid}/scores", json={"metric": "p_win", "score": 150, "note": "x"})
    assert res.status_code == 400  # out of range

    res = client.post(f"/api/pursuits/{pid}/scores", json={"metric": "bogus", "score": 50, "note": "x"})
    assert res.status_code == 400  # bad metric

    res = client.post(f"/api/pursuits/{pid}/scores", json={"metric": "p_go", "score": 90, "note": "Funded and stable."})
    assert res.status_code == 201
    assert res.get_json()["p_go"]["score"] == 90
    assert res.get_json()["p_go"]["band"]["key"] == "high_confidence"


def test_add_bid_decision_requires_note(client):
    created = client.post("/api/pursuits", json={"name": "Test Pursuit"})
    pid = created.get_json()["id"]

    res = client.post(f"/api/pursuits/{pid}/bid-decisions", json={"decision": "go"})
    assert res.status_code == 400

    res = client.post(f"/api/pursuits/{pid}/bid-decisions", json={"decision": "go", "note": "Strategic fit is strong."})
    assert res.status_code == 201
    assert res.get_json()["bid_decision"]["decision"] == "go"


def test_manual_journal_note_add_and_delete(client):
    created = client.post("/api/pursuits", json={"name": "Test Pursuit"})
    pid = created.get_json()["id"]

    added = client.post(f"/api/pursuits/{pid}/events", json={"note": "Customer call scheduled.", "author": "Tester"})
    assert added.status_code == 201
    eid = added.get_json()["id"]

    deleted = client.delete(f"/api/events/{eid}")
    assert deleted.status_code == 204


def test_cannot_delete_change_event(client):
    created = client.post("/api/pursuits", json={"name": "Test Pursuit"})
    pid = created.get_json()["id"]
    client.put(f"/api/pursuits/{pid}", json={"customer": "New Agency"})
    events = client.get(f"/api/pursuits/{pid}/events").get_json()
    change = next(e for e in events if e["kind"] == "change")
    res = client.delete(f"/api/events/{change['id']}")
    assert res.status_code == 400


def test_delete_pursuit(client):
    created = client.post("/api/pursuits", json={"name": "Test Pursuit"})
    pid = created.get_json()["id"]
    assert client.delete(f"/api/pursuits/{pid}").status_code == 204
    assert client.get(f"/api/pursuits/{pid}").status_code == 404


def test_delete_edited_pursuit(client):
    # An edit writes journal events; the delete used to hit the foreign key and 500.
    pid = client.post("/api/pursuits", json={"name": "Edited Pursuit"}).get_json()["id"]
    client.put(f"/api/pursuits/{pid}", json={"customer": "NAVAIR", "journal_note": "why"})
    assert client.delete(f"/api/pursuits/{pid}").status_code == 204
    assert client.get(f"/api/pursuits/{pid}").status_code == 404


def test_estimated_value_and_award_date(client):
    pid = client.get("/api/pursuits").get_json()[0]["id"]

    res = client.put(f"/api/pursuits/{pid}", json={"estimated_value": 12_500_000, "expected_award_date": "2027-03-15"})
    assert res.status_code == 200
    p = res.get_json()
    assert p["estimated_value"] == 12_500_000
    assert p["expected_award_date"] == "2027-03-15"
    # Weighted (factored) value = estimated value x P(Win), derived, only when both exist.
    if p["p_win"]:
        assert p["weighted_value"] == round(12_500_000 * p["p_win"]["score"] / 100)

    changes = {e["field"]: e for e in client.get(f"/api/pursuits/{pid}/events").get_json() if e["kind"] == "change"}
    assert changes["estimated value"]["new_value"] == "$12,500,000"
    assert changes["expected award date"]["new_value"] == "2027-03-15"

    # Empty clears; bad input is rejected.
    cleared = client.put(f"/api/pursuits/{pid}", json={"estimated_value": "", "expected_award_date": None}).get_json()
    assert cleared["estimated_value"] is None and cleared["expected_award_date"] is None
    assert cleared["weighted_value"] is None
    assert client.put(f"/api/pursuits/{pid}", json={"estimated_value": "lots"}).status_code == 400
    assert client.put(f"/api/pursuits/{pid}", json={"estimated_value": -5}).status_code == 400
    assert client.put(f"/api/pursuits/{pid}", json={"expected_award_date": "next spring"}).status_code == 400


def test_create_pursuit_with_planning_fields(client):
    res = client.post("/api/pursuits", json={"name": "New IDIQ", "estimated_value": "48000000.4", "expected_award_date": "2027-06-30"})
    assert res.status_code == 201
    p = res.get_json()
    assert p["estimated_value"] == 48_000_000
    assert p["expected_award_date"] == "2027-06-30"
    assert p["weighted_value"] is None  # no P(Win) scored yet
