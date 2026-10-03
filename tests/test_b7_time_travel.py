"""Tests for the 9th innovation: agent time-travel debugger (read-only replay)."""
import os
import sys
import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))

from hearth import commerce, proposals, replay, parliament
import server


@pytest.fixture
def client():
    app = server.mcp.streamable_http_app()
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_tray():
    proposals.clear_proposals()
    yield
    proposals.clear_proposals()


class TestReplayReadOnly:
    def test_pending_replay(self):
        res = commerce.build_autopilot_checkout(utterance="reorder coffee")
        pid = res["proposal"]["id"]
        d = replay.replay_decision(pid)
        assert d["ok"] is True
        assert d["status"] == "pending"
        assert d["undo_available"] is False
        assert d["chain_valid"] is True
        assert d["why"]["kind"] == "commerce_order"
        assert len(d["audit_trail"]) >= 1  # staged entry always present

    def test_approved_replay_with_receipt(self):
        res = commerce.build_autopilot_checkout(utterance="reorder coffee")
        pid = res["proposal"]["id"]
        proposals.decide(pid, True)
        d = replay.replay_decision(pid)
        assert d["status"] == "approved"
        assert d["undo_available"] is True
        assert d["execution"]["receipt_code"].startswith("HEARTH-RC-")
        assert "single-use receipt spent" in d["replay_note"]

    def test_undone_replay(self):
        res = commerce.build_autopilot_checkout(utterance="reorder coffee")
        pid = res["proposal"]["id"]
        proposals.decide(pid, True)
        proposals.undo(pid)
        d = replay.replay_decision(pid)
        assert d["status"] == "undone"
        assert d["undo_available"] is False
        assert "reversal recorded" in d["replay_note"]

    def test_parliament_replay_has_nash(self):
        s = parliament.parliament.deliberate("bench replay", {"peak_tariff": 0.5})
        d = replay.replay_decision(s.staged_proposal_id)
        assert d["ok"] is True
        assert d["why"]["kind"] == "parliament_consensus"
        assert d["why"]["nash"] == s.nash_equilibrium_score

    def test_missing_proposal(self):
        d = replay.replay_decision("p_nope_not_real")
        assert d["ok"] is False

    def test_replay_is_read_only(self):
        res = commerce.build_autopilot_checkout(utterance="reorder coffee")
        pid = res["proposal"]["id"]
        before = proposals.get_proposal(pid)["status"]
        replay.replay_decision(pid)
        replay.replay_decision(pid)
        assert proposals.get_proposal(pid)["status"] == before


class TestReplayEndpoints:
    def test_rest_replay(self, client):
        res = commerce.build_autopilot_checkout(utterance="reorder coffee")
        pid = res["proposal"]["id"]
        r = client.get(f"/api/audit/replay?id={pid}")
        assert r.status_code == 200
        assert r.json()["ok"] is True
        assert r.json()["proposal_id"] == pid

    def test_rest_replay_missing_id(self, client):
        r = client.get("/api/audit/replay")
        assert r.status_code == 400

    def test_mcp_tool_registered(self):
        names = [t.name for t in server.mcp._tool_manager.list_tools()]
        assert "audit_replay_decision" in names
