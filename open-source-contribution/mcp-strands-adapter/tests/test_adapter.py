"""Unit tests for the standalone mcp-strands-adapter package.

Covers both supported input paths: real Strands ``@tool`` objects (schema reused
from the SDK rather than re-derived) and plain Python callables (signature
reflection). Strands-specific tests skip automatically when the optional
dependency is absent.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp_strands_adapter import (  # noqa: E402
    MCPServerBridge,
    StrandsMCPToolBridge,
    strands_available,
    to_mcp_tool,
)

needs_strands = pytest.mark.skipif(
    not strands_available(), reason="strands-agents optional dependency not installed"
)


def dummy_tool(query: str, limit: int = 10, enabled: bool = True) -> dict:
    """A dummy strands tool for searching.

    Args:
        query: the search text
        limit: maximum results
        enabled: whether to search at all
    """
    return {"query": query, "limit": limit, "enabled": enabled, "results": ["match_1"]}


# -- plain-callable path ---------------------------------------------------

def test_reflected_schema_types_and_required():
    bridge = MCPServerBridge(prefix="custom_")
    definition = bridge.add(dummy_tool)

    assert definition["name"] == "custom_dummy_tool"
    assert "dummy strands tool" in definition["description"]
    props = definition["inputSchema"]["properties"]
    assert props["query"]["type"] == "string"
    # int must map to "integer", not "number".
    assert props["limit"]["type"] == "integer"
    assert props["enabled"]["type"] == "boolean"
    assert props["limit"]["default"] == 10
    assert definition["inputSchema"]["required"] == ["query"]


def test_docstring_arg_descriptions_are_extracted():
    definition = MCPServerBridge().add(dummy_tool)
    props = definition["inputSchema"]["properties"]
    assert props["query"]["description"] == "the search text"
    assert props["limit"]["description"] == "maximum results"


def test_call_coerces_json_scalars():
    bridge = MCPServerBridge()
    bridge.add(dummy_tool)
    # JSON transport can deliver an int as a float or numeric string.
    result = bridge.call("dummy_tool", {"query": "energy", "limit": "5", "enabled": "false"})
    assert result["limit"] == 5 and isinstance(result["limit"], int)
    assert result["enabled"] is False


def test_call_unknown_tool_raises_with_available_list():
    bridge = MCPServerBridge()
    bridge.add(dummy_tool)
    with pytest.raises(KeyError, match="not registered"):
        bridge.call("nope", {})


def test_unexpected_argument_is_rejected():
    bridge = MCPServerBridge()
    bridge.add(dummy_tool)
    with pytest.raises(TypeError):
        bridge.call("dummy_tool", {"query": "x", "bogus": 1})


def test_to_mcp_tool_oneshot():
    definition = to_mcp_tool(dummy_tool, prefix="h_")
    assert definition["name"] == "h_dummy_tool"
    assert "inputSchema" in definition


def test_legacy_alias_is_exported():
    assert StrandsMCPToolBridge is MCPServerBridge


def test_non_callable_is_rejected():
    with pytest.raises(TypeError):
        MCPServerBridge().add(42)


def test_list_tools_reports_every_definition():
    bridge = MCPServerBridge()
    bridge.add(dummy_tool)
    bridge.add(lambda: None, name="anon")
    assert len(bridge.list_tools()) == 2
    assert set(bridge.tool_names) == {"dummy_tool", "anon"}


# -- real Strands path -----------------------------------------------------

@needs_strands
def test_reuses_sdk_tool_spec_instead_of_rederiving():
    """A Strands tool's schema must come from the SDK, not from our reflection.

    This is the library's core value: the SDK already derives correct schemas via
    Pydantic + docstring_parser, and it nests them at inputSchema.json. Reusing
    that (rather than approximating it) is why this adapter stays short.
    """
    from strands import tool

    @tool
    def tariff_shift(kwh: float, hours: int = 2) -> dict:
        """Shift load off the peak tariff window.

        Args:
            kwh: energy to shift
            hours: how long to defer
        """
        return {"shifted_kwh": kwh, "hours": hours}

    definition = MCPServerBridge().add(tariff_shift)

    # MCP expects a flat inputSchema; the SDK nests under inputSchema.json.
    assert definition["inputSchema"]["type"] == "object"
    assert "json" not in definition["inputSchema"]
    assert definition["inputSchema"]["properties"]["kwh"]["type"] == "number"
    assert definition["inputSchema"]["required"] == ["kwh"]
    # SDK docstring parsing produced these descriptions.
    assert "energy to shift" in definition["inputSchema"]["properties"]["kwh"]["description"]


@needs_strands
def test_strands_tool_invocation_through_mcp_dispatch():
    from strands import tool

    @tool
    def verify_chain() -> dict:
        """Verify the audit chain.

        Returns:
            dict: chain status
        """
        return {"chain_intact": True}

    bridge = MCPServerBridge(prefix="hearth_")
    bridge.add(verify_chain)
    assert bridge.call("hearth_verify_chain", {}) == {"chain_intact": True}


@needs_strands
def test_agent_is_exported_via_as_tool():
    """A bare Agent must be exportable; its as_tool() result is not callable, so
    the bridge has to adapt the SDK's async stream() to a sync MCP call."""
    from strands import Agent

    agent = Agent(
        name="hearth_arbiter",
        description="Resolves household conflicts.",
        system_prompt="You arbitrate conflicts.",
    )
    bridge = MCPServerBridge()
    definition = bridge.add(agent)

    assert definition["name"] == "hearth_arbiter"
    assert "conflicts" in definition["description"].lower()
    assert definition["inputSchema"]["type"] == "object"
    # The registered handler must be invocable by MCP's synchronous dispatch.
    from mcp_strands_adapter.adapter import _AgentToolHandler
    assert isinstance(bridge._tools["hearth_arbiter"], _AgentToolHandler)


@needs_strands
def test_agent_tool_handler_drives_the_async_stream():
    """The sync adapter must drain AgentTool.stream() and surface SDK errors."""
    from strands import Agent
    from mcp_strands_adapter.adapter import _AgentToolHandler

    agent = Agent(
        name="echo_agent",
        description="Echoes its input.",
        system_prompt="Echo.",
    )
    handler = _AgentToolHandler(agent.as_tool(name="echo_agent"), "echo_agent")
    # No Bedrock credentials here, so the SDK must report an error rather than
    # the adapter silently returning a fabricated success.
    with pytest.raises((RuntimeError, Exception)):
        handler(prompt="hello")


@needs_strands
def test_register_all_mounts_on_fastmcp():
    from mcp.server.fastmcp import FastMCP
    from strands import tool

    @tool
    def probe(x: int) -> dict:
        """Probe the mount.

        Args:
            x: a number
        """
        return {"x": x}

    mcp = FastMCP("test")
    definitions = MCPServerBridge(prefix="t_").register_all(mcp, [probe])
    assert [d["name"] for d in definitions] == ["t_probe"]
    # FastMCP must expose the mounted tool with the same input schema.
    tools = {t.name: t for t in mcp._tool_manager.list_tools()}
    assert "t_probe" in tools
    schema = tools["t_probe"].parameters
    assert schema["properties"]["x"]["type"] == "integer"
    assert schema["required"] == ["x"]


@needs_strands
def test_register_all_preserves_declared_defaults():
    """The mounted FastMCP schema must keep each parameter's real default.

    A wrapper that defaults optional parameters to None advertises
    "default": null to MCP hosts, so the mounted schema silently diverges from
    the definition the bridge reports.
    """
    from mcp.server.fastmcp import FastMCP
    from strands import tool

    @tool
    def shift(device: str, hours: int = 2, peak_rate: float = 0.48) -> dict:
        """Shift a load.

        Args:
            device: appliance
            hours: deferral window
            peak_rate: current peak price
        """
        return {"device": device, "hours": hours, "peak_rate": peak_rate}

    mcp = FastMCP("defaults")
    MCPServerBridge().register_all(mcp, [shift])
    tools = {t.name: t for t in mcp._tool_manager.list_tools()}
    props = tools["shift"].parameters["properties"]
    assert props["hours"]["default"] == 2
    assert props["peak_rate"]["default"] == 0.48
    assert tools["shift"].parameters["required"] == ["device"]