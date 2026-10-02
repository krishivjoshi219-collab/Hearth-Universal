"""Tests for Alexa+ Agent Skills Runtime and Declarative Manifest."""
import json
import os
import pytest
from hearth import agent_skills


def test_agent_skills_manifest():
    manifest = agent_skills.agent_skills_runtime.export_agent_skills_manifest()
    assert manifest["manifestVersion"] == "1.0"
    assert manifest["agentSkillsSpec"] == "2026-09-16"
    assert len(manifest["skills"]) >= 3
    skill_names = [s["name"] for s in manifest["skills"]]
    assert any("Household Operations" in n for n in skill_names)
    assert any("Commerce Optimizer" in n for n in skill_names)
    assert any("Family Arbiter" in n for n in skill_names)
    assert any("Strands" in n for n in skill_names)


def test_agent_skills_invocation():
    res = agent_skills.agent_skills_runtime.invoke_skill(
        skill_id="amzn1.ask.skill.hearth.household_ops",
        action="get_state",
        parameters={},
    )
    assert res["ok"] is True
    assert "result" in res


def test_declarative_manifest_file_exists():
    manifest_path = os.path.join(os.path.dirname(__file__), "..", "skill", "agent_skills_manifest.json")
    assert os.path.exists(manifest_path)
    with open(manifest_path) as f:
        data = json.load(f)
    assert data["manifestVersion"] == "1.0"
    assert len(data["skills"]) >= 3
