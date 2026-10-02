"""Fortress batch 2: retention, locks, deep health, metrics, boot validation."""
from __future__ import annotations

import json
import os
import sys
import threading

import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))

import server
from hearth import audit, commerce, proposals


@pytest.fixture(scope="function")
def app():
    return server.mcp.streamable_http_app()


@pytest.fixture()
def client(app):
    c = TestClient(app, raise_server_exceptions=False)
    yield c
    server._GLOBAL_BUCKETS.clear()
    server._RATE_BUCKETS.clear()


def test_proposals_cap_never_drops_pending(monkeypatch):
    # Isolated: clear tray so cross-test pending doesn't pollute the cap.
    proposals.clear_proposals()
    monkeypatch.setattr(proposals, "PROPOSALS_MAX", 6)
    ids = [proposals.propose(kind="cap-probe", title=f"t{i}", reasons="r",
                             risk_level="low", diff="d", meta={})["id"] for i in range(4)]
    for pid in ids[:2]:
        proposals.decide(pid, True)
    for i in range(4):
        proposals.propose(kind="cap-probe", title=f"u{i}", reasons="r",
                         risk_level="low", diff="d", meta={})
    items = proposals.list_proposals(limit=1000)
    pend = {it["id"] for it in items if it.get("status") == "pending"}
    decided = [it for it in items if it.get("status") != "pending"]
    assert set(ids[2:]).issubset(pend)  # no new pending shed
    assert len(items) <= 6  # total bounded (pending + decided)
    assert len(decided) <= 6  # oldest decided shed to the cap


def test_audit_rotation_keeps_verify_true(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "_log_path", lambda: tmp_path / "audit.jsonl")
    monkeypatch.setattr(audit, "AUDIT_MAX_LINES", 5)
    for i in range(6):
        audit.append("test", f"rot{i}", {"i": i})
    assert audit.verify() is True
    archives = list(tmp_path.glob("audit-archive-*.jsonl"))
    assert len(archives) == 1
    first = json.loads((tmp_path / "audit.jsonl").read_text().splitlines()[0])
    assert first["action"] == "ledger_rotated"
    assert first["prev"].startswith("ARCHIVED:")


def test_concurrent_reschedule_storm():
    outs = []
    def worker(slot):
        try:
            outs.append(commerce.reschedule_delivery_slot(slot, reason="storm"))
        except Exception as e:  # noqa: BLE001 — storm must not raise
            outs.append({"ok": False, "error": str(e)})
    threads = [threading.Thread(target=worker,
                                args=("slot_overnight_urgent" if i % 2 else "slot_tuesday_household",))
               for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(outs) == 20 and all(o.get("ok") for o in outs)
    # File is valid JSON with a real slot after the storm.
    slot = commerce.get_scheduled_delivery_slot()
    assert slot["slot_id"] in ("slot_overnight_urgent", "slot_tuesday_household")
    commerce.reschedule_delivery_slot("slot_tuesday_household", reason="test hermetic pin")


def test_health_is_deep(client):
    body = client.get("/health").json()
    for key in ("status", "version", "uptime_s", "db_ok", "state_writable",
                "auth_enforced", "audit_events", "tools_count"):
        assert key in body, f"missing /health key: {key}"
    assert body["db_ok"] is True and body["state_writable"] is True
    assert body["audit_ok"] is True


def test_metrics_exposes_http_counters(client):
    client.post("/api/chat", json={"message": "hello status"})
    body = client.get("/api/metrics").json()
    http = body.get("http", {})
    assert http.get("chat", 0) >= 1
    assert "audit_events" in body


def test_boot_validation_clamps_bad_env(monkeypatch):
    monkeypatch.setenv("PORT", "not-a-port")
    monkeypatch.setenv("HEARTH_CHAT_RPM", "-5")
    server._validate_env()
    assert os.environ["PORT"] == "8787"
    assert os.environ["HEARTH_CHAT_RPM"] == "30"
