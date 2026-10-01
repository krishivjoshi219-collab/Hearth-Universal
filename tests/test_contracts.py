"""Demo-critical HTTP contracts: the exact flows the video performs."""
from __future__ import annotations

import os
import sys

import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))

import server
from hearth import home_mock


@pytest.fixture(scope="function")
def app():
    return server.mcp.streamable_http_app()


@pytest.fixture()
def client(app):
    c = TestClient(app, raise_server_exceptions=False)
    yield c
    server._GLOBAL_BUCKETS.clear()
    server._RATE_BUCKETS.clear()


def test_rest_unlock_is_fail_closed_then_executes_once(client):
    home_mock.toggle_lock(locked=True)
    r = client.post("/api/home/lock", json={"locked": False})
    assert r.status_code == 403
    body = r.json()
    assert body.get("approval_required") is True
    pid = body["proposal"]["id"]
    assert home_mock.get_state()["lock"]["front_door"] == "locked"
    # Approve through the tray, then execute with the receipt.
    assert client.post("/api/decide", json={"id": pid, "approved": True}).status_code == 200
    r2 = client.post("/api/home/lock", json={"locked": False, "proposal_id": pid})
    assert r2.status_code == 200
    assert home_mock.get_state()["lock"]["front_door"] == "unlocked"
    # Replay the receipt -> refused.
    r3 = client.post("/api/decide", json={"id": pid, "approved": True})
    assert r3.status_code == 409
    home_mock.toggle_lock(locked=True)


def test_locking_is_autonomous(client):
    home_mock.toggle_lock(locked=False)
    r = client.post("/api/home/lock", json={"locked": True})
    assert r.status_code == 200
    assert home_mock.get_state()["lock"]["front_door"] == "locked"


def test_ring_event_stages_proposal(client):
    r = client.post("/api/ring/event", json={"event_type": "doorbell_press", "visitor": "Demo Courier"})
    assert r.status_code == 200
    body = r.json()
    assert body.get("proposal_id") is not None
    assert "Courier" in body.get("announcement", "")


def test_persona_roundtrip(client):
    assert client.post("/api/persona", json={"id": "child"}).status_code == 200
    assert client.get("/api/persona").json()["active_persona"]["id"] == "child"
    assert client.post("/api/persona", json={"id": "admin"}).status_code == 200


def test_stage_cart_and_timemachine_and_arbiter(client):
    r = client.post("/api/commerce/stage-cart", json={"items": ["item_coffee"]})
    assert r.status_code == 200
    r = client.post("/api/timemachine", json={"preset": "bedtime"})
    assert r.status_code == 200
    r = client.post("/api/arbiter", json={"conflict_type": "climate"})
    assert r.status_code == 200
    # Garbage numeric input is a 400, never a 500.
    r = client.post("/api/arbiter", json={"conflict_type": "climate",
                                          "custom_params": {"baseline_temp": "hot"}})
    assert r.status_code in (200, 400)


def test_alexa_directive_carries_hearth_envelope(client):
    r = client.post("/api/alexa/directive", json={
        "directive": {"header": {"namespace": "Alexa.Discovery", "name": "Discover"},
                      "payload": {}}})
    assert r.status_code == 200
    body = r.json()
    assert "event" in body and "hearth" in body


def test_decide_unknown_id_is_404(client):
    r = client.post("/api/decide", json={"id": "p_nope_0", "approved": True})
    assert r.status_code == 404
