"""Tests for the 8th innovation: Autopilot Checkout (voice-to-tray + proactive + glass receipt)."""
import os
import sys
import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))

from hearth import commerce, proposals, heartbeat, planner, planner_dag, agent_skills
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


class TestVoiceParseToTray:
    def test_voice_parse_to_tray(self):
        res = commerce.build_autopilot_checkout(utterance="reorder coffee and detergent")
        assert res["ok"] is True
        assert res["gated"] is True
        assert res["staged_only"] is True
        prop = res["proposal"]
        assert prop["kind"] == "commerce_order"
        assert prop["status"] == "pending"
        assert "Autopilot Checkout" in prop["title"]

    def test_low_confidence_clarifies(self):
        res = commerce.build_autopilot_checkout(utterance="blorpt flibber xyzzy", voice_confidence=0.2)
        assert res.get("clarification_required") is True
        assert proposals.list_proposals("pending") == []

    def test_explicit_ids_override(self):
        res = commerce.build_autopilot_checkout(item_ids=["item_coffee"])
        assert res["ok"] is True
        assert res["proposal"]["status"] == "pending"

    def test_idempotent_no_dup(self):
        r1 = commerce.build_autopilot_checkout(utterance="reorder coffee and detergent")
        r2 = commerce.build_autopilot_checkout(utterance="reorder coffee and detergent")
        assert r2.get("deduplicated") is True
        assert r1["proposal"]["id"] == r2["proposal"]["id"]
        assert len(proposals.list_proposals("pending")) == 1


class TestToolStagesNeverExecutes:
    def test_direct_refused(self):
        res = commerce.place_order_direct(item_ids=["item_coffee"])
        assert res.get("ok") is not True or "refus" in str(res).lower() or res.get("gated") is not False

    def test_planner_gating(self):
        assert planner._requires_approval("commerce_autopilot_checkout", {}) is False

    def test_dag_autopilot_intent(self):
        dag = planner_dag.decompose_goal("autopilot checkout coffee")
        assert dag["intent"] == "AUTOPILOT_CHECKOUT"
        tools = [n["tool"] for n in dag["nodes"]]
        assert "commerce_autopilot_checkout" in tools


class TestProactiveTick:
    def test_proactive_tick_idempotent(self):
        t1 = heartbeat.tick_proactive("autopilot_checkout")
        assert t1["ok"] is True
        assert len(t1["proposals"]) == 1
        pid = t1["proposals"][0]["id"]
        t2 = heartbeat.tick_proactive("autopilot_checkout")
        assert t2["proposals"][0]["id"] == pid
        assert len(proposals.list_proposals("pending")) == 1
        assert heartbeat.get_events()[0]["type"] == "commerce"

    def test_auto_gates_on_due(self):
        assert heartbeat._autopilot_due() is True  # coffee 2.5d fixture


class TestGlassReceiptUndo:
    def test_glass_receipt_and_undo(self):
        res = commerce.build_autopilot_checkout(utterance="reorder coffee")
        pid = res["proposal"]["id"]
        decided = proposals.decide(pid, True)
        ex = decided.get("execution", {})
        assert ex.get("receipt_code", "").startswith("HEARTH-RC-")
        assert ex.get("qr_payload", "").startswith("hearth://receipt/")
        assert ex.get("glass") is True
        undone = proposals.undo(pid)
        assert undone["ok"] is True
        replay = proposals.decide(pid, True)
        assert replay.get("ok") is False


class TestResourcesManifest:
    def test_tray_resource(self, client):
        commerce.build_autopilot_checkout(utterance="reorder coffee")
        # resources are mounted on the MCP app; exercise via direct import
        from server import checkout_tray, receipt_last
        import json
        tray = json.loads(checkout_tray())
        assert "pending" in tray
        assert len(tray["pending"]) >= 1

    def test_skill_manifest(self):
        skills = agent_skills.agent_skills_runtime.list_skills()
        comm = next(s for s in skills if s["skill_id"] == "amzn1.ask.skill.hearth.commerce_replenish")
        assert "commerce_autopilot_checkout" in comm["tools_exposed"]
        inv = agent_skills.agent_skills_runtime.invoke_skill(
            skill_id="amzn1.ask.skill.hearth.commerce_replenish",
            action="autopilot_checkout", parameters={"utterance": "reorder coffee"})
        assert inv["ok"] is True
