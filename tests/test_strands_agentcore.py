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
