"""Tests for the 4 Frontier Innovations in Hearth Universal:
1. Black Box Forensic Incident Reconstruction Engine
2. Acoustic Mechanical Doctor & Appliance Predictive Diagnostics
3. Confidential Family Mediation & Zero-Knowledge Treaty Synthesizer
4. Neighborhood Swarm Grid & Decentralized Virtual Power Plant (VPP)
"""
import os
import sys
import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))

from hearth import forensics, acoustic, mediation, swarm, proposals, audit
import server


@pytest.fixture
def client():
    app = server.mcp.streamable_http_app()
    return TestClient(app)


class TestBlackBoxForensics:
    def test_reconstruct_perimeter_anomaly(self):
        res = forensics.forensics_engine.reconstruct_incident("perimeter_anomaly")
        assert res["incident_type"] == "perimeter_anomaly"
        assert res["verdict"] == "BENIGN_PHYSICAL_DISPLACEMENT"
        assert res["confidence_score"] >= 0.90
        assert len(res["timeline"]) >= 3
        # Verify physical causal factors
        factors = " ".join([e["causal_factor"] for e in res["timeline"]])
        assert "pressure differential" in factors or "wood door" in factors or "wind" in factors
        assert len(res["automated_countermeasures"]) >= 2
        assert "audit_proof" in res

    def test_reconstruct_freezer_thaw(self):
        res = forensics.forensics_engine.reconstruct_incident("freezer_thaw")
        assert res["incident_type"] == "freezer_thaw"
        assert res["verdict"] == "EQUIPMENT_POWER_STARVATION"
        assert res["confidence_score"] >= 0.90
        assert len(res["timeline"]) >= 2

    def test_get_latest_incident(self):
        latest = forensics.forensics_engine.get_latest_incident()
        assert "incident_id" in latest
        assert "verdict" in latest


class TestAcousticDiagnosticDoctor:
    def test_scan_appliance_acoustics_anomalous_fridge(self):
        res = acoustic.acoustic_doctor.scan_appliance_acoustics(target_appliance="all", stage_remedy=True)
        assert res["appliances_analyzed"] >= 3
        assert len(res["spectral_bins"]) >= 10
        assert res["urgent_actions_required"] >= 1

        fridge = next((a for a in res["appliances"] if a["id"] == "app_fridge_01"), None)
        assert fridge is not None
        assert fridge["status"] == "DEGRADED_BEARING_WEAR"
        assert fridge["detected_peak_hz"] == 124.5
        assert fridge["failure_probability_14d"] > 0.80
        assert fridge["remedy"]["subscribe_and_save_discount"] == 0.15

        # Verify staged proposal in approval tray
        assert res["staged_proposal_id"] is not None
        prop = proposals.get_proposal(res["staged_proposal_id"])
        assert prop is not None
        assert "Acoustic Wear Alert" in prop["title"]
        assert prop["status"] == "pending"

    def test_scan_appliance_healthy_targets(self):
        res = acoustic.acoustic_doctor.scan_appliance_acoustics(target_appliance="HVAC", stage_remedy=False)
        assert len(res["appliances"]) >= 1
        hvac = res["appliances"][0]
        assert hvac["status"] == "HEALTHY"
        assert hvac["health_score"] >= 90


class TestConfidentialFamilyMediator:
    def test_draft_household_treaty(self):
        res = mediation.family_mediator.draft_household_treaty(topic="screen_time_and_energy")
        assert res["status"] == "AWAITING_HOUSEHOLD_RATIFICATION"
        assert res["fairness_index_out_of_10"] >= 9.0
        assert res["friction_reduction_estimate_pct"] >= 70
        assert len(res["covenants"]) == 3
        assert "Zero-Knowledge" in res["privacy_guarantee"]

        # Ensure raw grievances are not leaked verbatim in the covenant titles
        covenant_texts = " ".join([c["concession_granted"] for c in res["covenants"]])
        assert "Minecraft" in covenant_texts
        assert "cleanup" in covenant_texts

        # Verify staged proposal for household ratification
        assert res["staged_proposal_id"] is not None
        prop = proposals.get_proposal(res["staged_proposal_id"])
        assert prop is not None
        assert "Family Treaty Ratification" in prop["title"]

    def test_get_active_treaty(self):
        treaty = mediation.family_mediator.get_active_treaty()
        assert "treaty_id" in treaty
        assert treaty["fairness_index_out_of_10"] >= 9.0


class TestNeighborhoodSwarmGrid:
    def test_coordinate_microgrid(self):
        res = swarm.swarm_grid.coordinate_microgrid(export_kw=3.8)
        assert res["swarm_status"] == "OPTIMAL_COOPERATIVE_DISPATCH"
        assert res["active_nodes_count"] >= 3
        assert res["cooperative_rate_kwh"] == 0.18

        # Economic validation: seller gain and buyer savings are positive
        econ = res["economic_impact"]
        assert econ["seller_hourly_gain_usd"] > 0
        assert econ["buyer_hourly_savings_usd"] > 0
        assert econ["total_community_dividend_hourly_usd"] > 0

        # Environmental validation
        env = res["environmental_impact"]
        assert env["carbon_offset_kg_co2e_hr"] > 0
        assert env["avoided_fossil_peaker_dispatch"] is True

        # Transaction proof
        assert len(res["p2p_transactions"]) >= 1
        tx = res["p2p_transactions"][0]
        assert tx["power_kw"] == 3.8
        assert "Oak Lane" in tx["from_node"]


class TestFrontierRESTEndpoints:
    def test_forensics_endpoint(self, client):
        r = client.post("/api/forensics/reconstruct", json={"incident_type": "perimeter_anomaly"})
        assert r.status_code == 200
        data = r.json()
        assert data["incident_type"] == "perimeter_anomaly"
        assert data["verdict"] == "BENIGN_PHYSICAL_DISPLACEMENT"

    def test_acoustic_endpoint(self, client):
        r = client.get("/api/acoustic/scan")
        assert r.status_code == 200
        data = r.json()
        assert data["appliances_analyzed"] >= 3
        assert len(data["spectral_bins"]) >= 10

    def test_mediation_endpoint(self, client):
        r = client.post("/api/mediation/treaty", json={"topic": "weekend_chores"})
        assert r.status_code == 200
        data = r.json()
        assert data["topic"] == "weekend_chores"
        assert data["fairness_index_out_of_10"] >= 9.0

    def test_swarm_endpoint(self, client):
        r = client.get("/api/swarm/grid")
        assert r.status_code == 200
        data = r.json()
        assert data["cooperative_rate_kwh"] == 0.18
        assert len(data["nodes"]) >= 3

    def test_diagnostics_includes_all_four_frontier_engines(self, client):
        r = client.get("/api/diagnostics")
        assert r.status_code == 200
        d = r.json()
        assert d["forensics"]["ready"] is True
        assert d["acoustic"]["ready"] is True
        assert d["mediation"]["ready"] is True
        assert d["swarm_grid"]["ready"] is True
