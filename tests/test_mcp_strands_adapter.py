"""Tests for Open Source Strands MCP Bridge Adapter."""
import pytest
from hearth import mcp_strands_adapter


def sample_calc(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def test_strands_mcp_tool_bridge_reflection():
    bridge = mcp_strands_adapter.StrandsMCPToolBridge(name_prefix="test_")
    spec = bridge.register_strands_tool("add", sample_calc)
    assert spec["name"] == "test_add"
    assert "Add two numbers" in spec["description"]
    assert "a" in spec["inputSchema"]["properties"]
    assert "b" in spec["inputSchema"]["properties"]
    assert "a" in spec["inputSchema"]["required"]

    tools = bridge.list_mcp_tools()
    assert len(tools) == 1

    # Invocations
    result = bridge.invoke_from_mcp("test_add", {"a": 10, "b": 25})
    assert result == 35
