"""Tests for Complete Product Experience, Human Trust & Reversibility Engine,
and Production Diagnostics Telemetry.
"""
import os
import sys
import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))

from hearth import proposals, home_mock, audit, heartbeat, sentinel
import server


@pytest.fixture
def client():
    app = server.mcp.streamable_http_app()
    return TestClient(app)


class TestReversibilityAndUndoEngine:
    def test_undo_home_lock_reversal(self, client):
        # 1. Propose unlocking front door
        prop = proposals.propose(
            kind="home_lock",
            title="Unlock Front Door Entryway",
            reasons="Delivery courier arrival",
            meta={"door": "front_door", "locked": False},
        )
        pid = prop["id"]

        # 2. Decide: approve it
        r_decide = client.post("/api/decide", json={"id": pid, "approved": True})
        assert r_decide.status_code == 200
        assert home_mock.get_state()["entryway"]["lock"]["front_door"] == "unlocked"

        # 3. Undo: reverse the action
        r_undo = client.post("/api/undo", json={"id": pid})
        assert r_undo.status_code == 200
        undo_data = r_undo.json()
        assert undo_data["ok"] is True
        assert undo_data["proposal"]["status"] == "undone"

        # Verify door was relocked back to prior safe state!
        assert home_mock.get_state()["entryway"]["lock"]["front_door"] == "locked"

        # Verify audit ledger recorded the reversal
        audit_res = audit.verify()
        assert audit_res is True

    def test_undo_thermostat_arbitration_reversal(self, client):
        # 1. Propose arbiter compromise
        prop = proposals.propose(
            kind="arbiter_compromise",
            title="Nash Equilibrium 20.5C Setpoint",
            reasons="Energy savings during peak rate",
            meta={"proposed_action": {"device": "thermostat", "setpoint": 20.5}},
        )
        pid = prop["id"]

        # 2. Approve it
        client.post("/api/decide", json={"id": pid, "approved": True})
        assert home_mock.get_state()["living_room"]["climate"]["target_c"] == 20.5

        # 3. Undo it
        r_undo = client.post("/api/undo", json={"id": pid})
        assert r_undo.status_code == 200
        # Thermostat is restored to baseline 22.0C comfort
        assert home_mock.get_state()["living_room"]["climate"]["target_c"] == 22.0

    def test_undo_unapproved_proposal_rejected(self, client):
        prop = proposals.propose(kind="home_scene", title="Test Scene", reasons="Evening scene setup")
        pid = prop["id"]
        # Attempt to undo a pending (not approved) proposal
        r = client.post("/api/undo", json={"id": pid})
        assert r.status_code == 400
        assert "not approved" in r.json()["error"]


class TestProductionDiagnosticsTelemetry:
    def test_diagnostics_endpoint_contract(self, client):
        r = client.get("/api/diagnostics")
        assert r.status_code == 200
        data = r.json()

        assert data["status"] == "healthy"
        assert data["spec_version"] == "2025-11-25"
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0
        assert data["active_brain"] is not None
        assert data["active_provider"] is not None
        assert data["audit_ledger"]["valid"] is True
        assert data["parliament"]["ministers_count"] == 3
        assert data["causal_twin"]["resilience_score"] > 0
        assert "meta_skills" in data
        assert "active_persona" in data


class TestLivingHouseholdSimulator:
    def test_simulate_scenarios(self, client):
        # Test energy peak scenario
        r1 = client.post("/api/simulate/tick", json={"scenario": "energy_peak"})
        assert r1.status_code == 200
        assert r1.json()["ok"] is True
        assert "Peak Tariff" in r1.json()["event"]["title"]

        # Test pantry alert scenario (stages restock proposal)
        r2 = client.post("/api/simulate/tick", json={"scenario": "pantry_alert"})
        assert r2.status_code == 200
        assert r2.json()["ok"] is True
        assert len(r2.json()["proposals"]) > 0

        # Test security perimeter sweep
        r3 = client.post("/api/simulate/tick", json={"scenario": "security"})
        assert r3.status_code == 200
        assert r3.json()["ok"] is True
        assert "Perimeter" in r3.json()["event"]["title"]


class TestWeb2ProductExperienceAssets:
    def test_web2_features_rendered(self, client):
        r = client.get("/web2")
        assert r.status_code == 200
        html = r.text

        # Verify psychological and product ergonomics elements
        assert 'id="lightWaveBar"' in html
        assert 'id="quickChips"' in html
        assert 'id="chimeBtn"' in html
        assert 'id="diagBox"' in html
        assert 'Living Household Simulator' in html
        assert 'data-scenario="energy_peak"' in html
        assert 'data-cmd="Surge solar' in html
