"""Tests for Alexa+ Agent Skills Runtime and Declarative Manifest."""
import json
import os
from hearth import agent_skills


def test_agent_skills_manifest():
    manifest = agent_skills.agent_skills_runtime.export_agent_skills_manifest()
    assert manifest["manifestVersion"] == "1.0"
    # Reported as `declaredAgainst`, not `agentSkillsSpec`: no public Alexa+
    # agent-skills schema is published, so claiming conformance to a spec version
    # would be false. See the sibling honesty guard below.
    assert manifest["declaredAgainst"] == "2026-09-16"
    assert "agentSkillsSpec" not in manifest
    assert manifest["manifestKind"] == "hearth-self-hosted-agent-skills"
    assert len(manifest["skills"]) >= 3
    skill_names = [s["name"] for s in manifest["skills"]]
    assert any("Household Operations" in n for n in skill_names)
    assert any("Commerce Optimizer" in n for n in skill_names)
    assert any("Family Arbiter" in n for n in skill_names)
    assert any("Strands" in n for n in skill_names)


def test_static_agent_skills_manifest_has_no_dead_schema_or_spec_claim():
    """skill/agent_skills_manifest.json must not cite an unresolvable schema.

    Same defect class as addon.json: Amazon publishes no public agent-skills
    manifest schema, so a $schema URL pointing at developer.amazon.com 404s and
    reads as spec-padding.
    """
    path = os.path.join(os.path.dirname(__file__), "..", "skill", "agent_skills_manifest.json")
    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)

    assert "$schema" not in manifest, "manifest must not reference an unpublished schema URL"
    assert manifest["manifestKind"] == "hearth-self-hosted-agent-skills"
    assert manifest["_note"], "manifest must state that it is self-authored"
    assert "declaredAgainst" in manifest
    assert len(manifest["skills"]) >= 3


def test_static_and_generated_agent_skills_declare_the_same_date():
    """The committed file and the runtime export must not drift apart."""
    root = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(root, "skill", "agent_skills_manifest.json"), encoding="utf-8") as fh:
        static = json.load(fh)
    generated = agent_skills.agent_skills_runtime.export_agent_skills_manifest()
    assert static["declaredAgainst"] == generated["declaredAgainst"]
    assert static["manifestVersion"] == generated["manifestVersion"]
    assert len(static["skills"]) == len(generated["skills"])


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
