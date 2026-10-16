"""Tests for AWS Strands Multi-Agent SDK and Bedrock AgentCore Memory."""
import pytest

from hearth import agentcore, strands_agent


def test_agentcore_memory_append_and_search(tmp_path):
    mem_file = tmp_path / "test_agentcore_mem.json"
    store = agentcore.AgentCoreMemoryStore(memory_file=mem_file)

    entry1 = store.append_turn("ses_01", "user", "Remember that Leo is allergic to peanuts.")
    assert entry1["session_id"] == "ses_01"
    assert "peanuts" in entry1["content"]

    entry2 = store.append_turn("ses_01", "assistant", "Noted, peanut allergy recorded.")
    assert entry2["session_id"] == "ses_01"
    assert "peanut allergy" in entry2["content"]
    turns = store.get_session_turns("ses_01")
    assert len(turns) == 2

    # Episodic search
    matches = store.search_episodic_context("peanut allergy")
    assert len(matches) >= 1
    assert any("peanut" in m["content"] for m in matches)


def test_agentcore_gateway_registration():
    gw = agentcore.AgentCoreGateway()
    gw.register_tool(
        name="test_tool",
        description="A test tool",
        parameters_schema={"type": "object", "properties": {"val": {"type": "string"}}},
        handler=lambda args: f"handled {args.get('val')}",
    )
    tools = gw.list_agentcore_tools()
    assert len(tools) == 1
    assert tools[0]["toolSpec"]["name"] == "test_tool"

    res = gw.execute_tool("test_tool", {"val": "hello"})
    assert res["ok"] is True
    assert res["result"] == "handled hello"


def test_strands_subagents():
    arbiter_agent = strands_agent.ArbiterNegotiatorAgent()
    res1 = arbiter_agent.run("Resolve temperature conflict between Alex and Sarah")
    assert res1.agent_name == "ArbiterNegotiatorAgent"
    assert "Arbiter resolved" in res1.summary

    replenish_agent = strands_agent.ReplenishmentDepletionAgent()
    res2 = replenish_agent.run("Audit low pantry stock and restock coffee")
    assert replenish_agent.name == "ReplenishmentDepletionAgent"
    assert len(res2.proposals_staged) >= 1
    assert "commerce_replenish" in res2.proposals_staged[0]["kind"]

    guardian_agent = strands_agent.SentinelGuardianAgent()
    res3 = guardian_agent.run("Verify audit ledger and front door safety")
    assert res3.agent_name == "SentinelGuardianAgent"
    assert "Sentinel Guardian verified" in res3.summary


def test_strands_supervisor_orchestration():
    supervisor = strands_agent.StrandsSupervisor()
    goal = "Prepare family weekend: balance thermostat preferences, restock low milk and coffee, and verify safety"
    res = supervisor.orchestrate_goal(goal)
    assert res["ok"] is True
    assert "AWS Strands Agents Multi-Agent Supervisor Pattern" in res["architecture"]
    assert len(res["delegated_agents"]) >= 2
    assert len(res["subagent_executions"]) >= 2
    assert len(res["plan_summary"]) > 20


# ---------------------------------------------------------------------------
# AWS Strands Agents SDK integration
#
# These tests assert the SDK integration is *real* rather than claimed: when the
# optional dependency is installed the module must construct genuine
# strands.Agent objects whose tool schemas are produced by the SDK, and when it
# is absent the module must degrade honestly to the deterministic fallback.
# Both branches are asserted, so the tests pass in CI with or without the extra.
# ---------------------------------------------------------------------------

def test_strands_sdk_status_reports_backend_honestly():
    status = strands_agent.StrandsSupervisor().strands_sdk_status()
    assert status["backend"] in (
        "aws-strands-sdk",
        "aws-strands-sdk-no-inference",
        "pattern-fallback",
    )
    assert status["integration"]
    assert status["install_hint"]
    if strands_agent.STRANDS_AVAILABLE:
        assert status["sdk_installed"] is True
        # No live-inference claim unless Bedrock is actually enabled.
        assert status["backend"] != "aws-strands-sdk" or status["bedrock_enabled"] is True
    else:
        assert status["sdk_installed"] is False
        assert status["sdk_import_error"]


@pytest.mark.skipif(not strands_agent.STRANDS_AVAILABLE,
                    reason="strands-agents optional extra not installed")
def test_real_strands_agents_and_agents_as_tools_are_constructed():
    """The supervisor must build real strands.Agent objects wired with as_tool."""
    from strands import Agent

    sup = strands_agent.StrandsSupervisor()
    sup._build_sdk_agents()
    assert sup._sdk_agents is not None, sup._sdk_error
    assert sup._sdk_supervisor is not None, sup._sdk_error

    # Three genuine sub-agents, each exposing SDK-derived tools.
    assert set(sup._sdk_agents) == {"arbiter", "replenishment", "guardian"}
    for agent in sup._sdk_agents.values():
        assert isinstance(agent, Agent)
        specs = [t.tool_spec for t in agent.tool_registry.registry.values()]
        assert specs, "each sub-agent must expose at least one SDK-derived tool spec"
        for spec in specs:
            # Schemas come from the SDK: name/description + JSON-Schema object.
            assert spec["name"]
            assert spec["description"]
            assert spec["inputSchema"]["json"]["type"] == "object"

    # Supervisor composed via the SDK's agents-as-tools delegation pattern.
    delegate_names = set(sup._sdk_supervisor.tool_registry.registry.keys())
    assert delegate_names == {"delegate_arbiter", "delegate_replenishment", "delegate_guardian"}

    status = sup.strands_sdk_status()
    assert status["sdk_installed"] is True
    assert status["construction_error"] is None
    assert status["subagent_tool_names"]["guardian"] == ["judge_action_safety", "verify_audit_chain"]


@pytest.mark.skipif(not strands_agent.STRANDS_AVAILABLE,
                    reason="strands-agents optional extra not installed")
def test_orchestration_reports_backend_and_still_gates_actions():
    """SDK presence must not change the Propose-Never-Execute contract."""
    res = strands_agent.StrandsSupervisor().orchestrate_goal(
        "Prepare family weekend: balance thermostat, restock milk and coffee, verify safety"
    )
    assert res["ok"] is True
    assert res["strands_backend"].startswith("aws-strands-sdk")
    assert res["strands_sdk"]["sdk_installed"] is True
    # Deterministic sub-agents still ran and anything consequential is only staged.
    assert res["delegated_agents"]
    for p in res["proposals_staged"]:
        assert p["status"] == "pending", "agents must never auto-approve a proposal"


def test_fallback_path_is_used_when_sdk_is_unavailable(monkeypatch):
    """With the SDK unavailable the supervisor must degrade, not crash."""
    monkeypatch.setattr(strands_agent, "STRANDS_AVAILABLE", False)
    sup = strands_agent.StrandsSupervisor()
    sup._sdk_agents = None
    sup._sdk_supervisor = None
    assert sup.backend == "pattern-fallback"

    res = sup.orchestrate_goal("verify the front door and audit the pantry")
    assert res["ok"] is True
    assert res["strands_backend"] == "pattern-fallback"
    assert res["delegated_agents"]
