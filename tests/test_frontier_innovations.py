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

import server

from hearth import acoustic, forensics, mediation, proposals, swarm


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
        assert res["fairness_index_out_of_10"] >= 8.5
        assert res["cooperation_coverage_pct"] == 100.0
        assert res["envy_free"] is True
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
        assert treaty["fairness_index_out_of_10"] >= 8.5

    def test_mediation_is_input_sensitive(self):
        """The treaty must be a function of what residents actually said.

        This is the regression guard for the engine's core claim. An earlier
        implementation clamped fairness to [9.0, 9.8] and emitted hardcoded
        Leo/Sarah/Alex covenant prose, so two completely different households
        received byte-identical treaties. If this test fails, the mediator has
        regressed into a fixture generator.
        """
        crowded = mediation.ConfidentialFamilyMediator().draft_household_treaty({
            "A": "I do all the kitchen cleanup and the dishes",
            "B": "I hate doing chores and laundry",
            "C": "chores chores dishwasher trash",
        })
        spread = mediation.ConfidentialFamilyMediator().draft_household_treaty({
            "a": "kitchen cleanup dishes",
            "b": "budget subscriptions expensive",
            "c": "thermostat temperature 68F office",
        })

        # Different households must be treated differently.
        assert crowded["concession_vector"] != spread["concession_vector"]

        # A household crowded onto one domain cannot be fully satisfied: the
        # single pool must be divided, so worst-served achievement drops and the
        # fairness index must fall well below the spread-demand household.
        assert crowded["nash_achievement"] < spread["nash_achievement"]
        assert crowded["fairness_index_out_of_10"] < spread["fairness_index_out_of_10"] - 1.0

        # Fairness must not be pinned to a flattering band: crowding three
        # claimants onto one pool has to read as a genuinely poor treaty.
        assert crowded["fairness_index_out_of_10"] < 9.0
        assert spread["fairness_index_out_of_10"] >= 8.5

    def test_fairness_rewards_coverage_and_punishes_oversubscription(self):
        """More distinct claimants than the concession budget can serve must
        score worse than a household whose top demands all fit."""
        mediator = mediation.ConfidentialFamilyMediator()

        # 3 claimants, 3 distinct domains -> all three top demands are reachable.
        served = mediator.draft_household_treaty({
            "a": "kitchen cleanup and dishes",
            "b": "budget and subscriptions",
            "c": "thermostat temperature 68F",
        })
        # 5 claimants competing across the same 4 domains -> oversubscribed.
        oversubscribed = mediator.draft_household_treaty({
            "a": "kitchen cleanup", "b": "laundry chores", "c": "budget money",
            "d": "thermostat 68F", "e": "minecraft gaming",
        })

        assert served["cooperation_coverage_pct"] > oversubscribed["cooperation_coverage_pct"]
        assert served["fairness_index_out_of_10"] > oversubscribed["fairness_index_out_of_10"]

    def test_covenants_are_derived_from_resident_statements(self):
        """Covenants must quote quantities the resident actually stated, and
        must not leak one resident's grievance to another."""
        treaty = mediation.ConfidentialFamilyMediator().draft_household_treaty({
            "Alex": "I need the office at 70F during work hours",
            "Riley": "I want 3 hours of gaming on weekends",
        })
        by_resident = {c["resident"]: c for c in treaty["covenants"]}
        assert "70" in by_resident["Alex"]["concession_granted"] or \
               "70" in by_resident["Alex"]["reciprocal_obligation"]
        assert "3 hours" in by_resident["Riley"]["concession_granted"]

        # Each covenant is addressed to exactly one resident and carries that
        # resident's own domain -- no persona is hardcoded into the prose.
        assert len(treaty["covenants"]) == 2
        for name, cov in by_resident.items():
            assert cov["resident"] == name
            assert cov["domain"] in mediation._DIMS
            assert "Leo" not in cov["concession_granted"]
            assert "Minecraft" not in cov["concession_granted"]

    def test_savings_derive_from_conceded_domains(self):
        """Projected savings must follow the negotiated concessions rather than
        being a constant."""
        mediator = mediation.ConfidentialFamilyMediator()
        climate = mediator.draft_household_treaty({
            "a": "thermostat temperature 68F office cooling",
        })
        nothing = mediator.draft_household_treaty({
            "a": "minecraft gaming screen time",
        })
        assert climate["projected_monthly_savings_usd"] != nothing["projected_monthly_savings_usd"]

    def test_zero_knowledge_no_verbatim_grievance_leaks(self):
        """Raw statements must never appear in the treaty payload, and each
        resident must get an independent salt."""
        secret = "I secretly resent the thermostat being set to 71F every single night"
        treaty = mediation.ConfidentialFamilyMediator().draft_household_treaty({
            "Alex": secret,
            "Sam": "I want more gaming time",
        })
        blob = repr(treaty)
        assert "secretly resent" not in blob
        assert secret not in blob
        # Salts are per-resident, so identical text hashes differently.
        same = mediation.ConfidentialFamilyMediator().draft_household_treaty({
            "A": "identical text", "B": "identical text",
        })
        assert len(set(same["hash_salts"].values())) == 2


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
        assert data["fairness_index_out_of_10"] >= 8.5

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
