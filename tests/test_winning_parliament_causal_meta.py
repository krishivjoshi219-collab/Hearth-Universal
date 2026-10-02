"""Comprehensive test suite for the Winning Tri-Pillar Architecture and Universal Model Mesh.

Tests:
1. Household Parliament (Dialectic debate between FrugalMind, BioComfort, EcoSovereign, Nash equilibrium).
2. Causal Digital Twin (Monte Carlo forward simulations, vulnerability detection, pre-emptive contingency plans).
3. Meta-Skill Synthesizer (Autonomous skill generation, Sentinel safety validation, live hot-mounting).
4. Universal Model Mesh (Any API support, endpoint health discovery, Amazon Nova Pro default).
5. FastMCP / Starlette HTTP Companion Endpoints.
"""
import os
import sys
import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))

from hearth import causal_twin, meta_skill, model_mesh, parliament, agent_skills
import server


@pytest.fixture
def client():
    app = server.mcp.streamable_http_app()
    return TestClient(app)


class TestHouseholdParliament:
    def test_parliament_deliberation_and_nash_equilibrium(self):
        topic = "Severe heatwave during $0.52/kWh peak tariff"
        session = parliament.parliament.deliberate(
            topic=topic,
            context={"peak_tariff": 0.52, "target_temp": 70, "battery_soc": 90}
        )
        assert session.session_id.startswith("parliament_")
        assert len(session.speeches) == 3
        assert len(session.cross_examination) >= 3

        ministers = [s.minister for s in session.speeches]
        assert "FrugalMind" in ministers
        assert "BioComfort" in ministers
        assert "EcoSovereign" in ministers

        assert session.nash_equilibrium_score > 0
        assert "annualized_impact" in session.pareto_compromise
        assert session.staged_proposal_id is not None

    def test_parliament_ministers_info(self):
        info = parliament.parliament.get_ministers_info()
        assert "FrugalMind" in info["ministers"]
        assert "BioComfort" in info["ministers"]
        assert "EcoSovereign" in info["ministers"]


class TestCausalDigitalTwin:
    def test_monte_carlo_simulation_and_contingency(self):
        sim = causal_twin.causal_twin.run_simulation(days_ahead=7, iterations=150)
        assert sim.days_ahead == 7
        assert sim.monte_carlo_iterations == 150
        assert len(sim.vulnerabilities) > 0
        assert len(sim.contingency_plans) > 0
        assert sim.grid_resilience_score > 0
        assert sim.staged_proposal_id is not None

        # Check vulnerability structure
        v = sim.vulnerabilities[0]
        assert v.hazard_type in ("energy_tariff_spike", "brownout_risk", "pantry_depletion")
        assert v.probability_pct >= 0

    def test_fast_vulnerabilities_snapshot(self):
        snap = causal_twin.causal_twin.get_latest_vulnerabilities()
        assert "vulnerability_count" in snap
        assert "contingency_plans" in snap


class TestMetaSkillSynthesizer:
    def test_autonomous_synthesis_and_mounting(self):
        res = meta_skill.meta_synthesizer.synthesize(
            requirement="Smart EV charging with solar peak matching",
            author_persona="Alex",
        )
        assert res["ok"] is True
        assert res["status"] == "mounted_live"
        skill_id = res["skill_id"]

        # Verify mounted in live runtime
        discovered = [s["skill_id"] for s in agent_skills.agent_skills_runtime.list_skills()]
        assert skill_id in discovered

        # Invoke dynamically mounted skill
        inv_res = agent_skills.agent_skills_runtime.invoke_skill(
            skill_id=skill_id,
            action="execute_plan",
            parameters={"schedule_hour": 13, "eco_mode": True},
        )
        assert inv_res["ok"] is True

    def test_synthesis_blocked_for_child_persona(self):
        # Child persona attempting to compile privileged system logic
        res = meta_skill.meta_synthesizer.synthesize(
            requirement="Modify external door security gates",
            author_persona="Leo",
        )
        assert res["ok"] is False
        assert "Sentinel Safety" in res["error"] or "Child" in res["error"]


class TestUniversalModelMesh:
    def test_default_is_amazon_nova_pro(self):
        status = model_mesh.model_mesh.get_mesh_status()
        assert "nova-pro" in status["default_model"]
        assert status["active_provider"] == "bedrock"

    def test_register_and_switch_custom_provider(self):
        res = model_mesh.model_mesh.register_custom_provider(
            name="Mock Local LLM",
            base_url="http://127.0.0.1:9999/v1",
            api_key="",
        )
        assert res["ok"] is True
        assert res["provider_slug"] == "mock_local_llm"

        # Switch active model
        switch_res = model_mesh.model_mesh.set_active_model(
            model_id="mistral-7b-instruct",
            provider_name="mock_local_llm",
        )
        assert switch_res["ok"] is True
        assert switch_res["active_model"] == "mistral-7b-instruct"

        # Revert back to Amazon Nova Pro
        revert = model_mesh.model_mesh.set_active_model(
            model_id="us.amazon.nova-pro-v1:0",
            provider_name="bedrock",
        )
        assert revert["ok"] is True
        assert revert["is_default_nova"] is True

    def test_discover_all_models(self):
        disc = model_mesh.model_mesh.discover_all_models()
        assert "bedrock" in disc["providers"]
        assert "us.amazon.nova-pro-v1:0" in disc["providers"]["bedrock"]["models"]


class TestFastMCPRoutes:
    def test_health_includes_winning_subsystems(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["parliament_ok"] is True
        assert data["causal_twin_ok"] is True
        assert data["meta_synthesizer_ok"] is True
        assert "nova-pro" in data["active_model"]

    def test_parliament_endpoints(self, client):
        r = client.get("/api/parliament/ministers")
        assert r.status_code == 200
        assert "FrugalMind" in r.json()["ministers"]

        delib = client.post("/api/parliament/deliberate", json={"topic": "Weekend laundry and solar charge"})
        assert delib.status_code == 200
        assert "pareto_compromise" in delib.json()

    def test_causal_twin_endpoints(self, client):
        r = client.get("/api/causal/vulnerabilities")
        assert r.status_code == 200
        assert "vulnerability_count" in r.json()

        sim = client.post("/api/causal/simulate", json={"days_ahead": 5, "iterations": 50})
        assert sim.status_code == 200
        assert sim.json()["days_ahead"] == 5

    def test_meta_skills_endpoints(self, client):
        r = client.get("/api/meta-skills")
        assert r.status_code == 200
        assert "skills" in r.json()

        synth = client.post("/api/meta-skills/synthesize", json={
            "requirement": "Automated greenhouse ventilation",
            "persona": "Alex"
        })
        assert synth.status_code == 200
        assert synth.json()["ok"] is True

    def test_model_mesh_endpoints(self, client):
        r = client.get("/api/models")
        assert r.status_code == 200
        assert "providers" in r.json()

        set_active = client.post("/api/models/active", json={
            "model_id": "us.amazon.nova-pro-v1:0",
            "provider": "bedrock"
        })
        assert set_active.status_code == 200
        assert set_active.json()["ok"] is True
