"""Unit tests for standalone mcp-strands-adapter package."""
import pytest
from mcp_strands_adapter import StrandsMCPToolBridge


def dummy_tool(query: str, limit: int = 10, enabled: bool = True) -> dict:
    """A dummy strands tool for searching."""
    return {"query": query, "limit": limit, "enabled": enabled, "results": ["match_1"]}


def test_schema_generation():
    bridge = StrandsMCPToolBridge(name_prefix="custom_")
    schema = bridge.register_strands_tool("search", dummy_tool)

    assert schema["name"] == "custom_search"
    assert "dummy strands tool" in schema["description"]
    props = schema["inputSchema"]["properties"]
    assert props["query"]["type"] == "string"
    assert props["limit"]["type"] == "number"
    assert props["enabled"]["type"] == "boolean"
    assert "query" in schema["inputSchema"]["required"]
    assert "limit" not in schema["inputSchema"]["required"]


def test_tool_invocation():
    bridge = StrandsMCPToolBridge()
    bridge.register_strands_tool("search", dummy_tool)

    res = bridge.invoke_from_mcp("strands_search", {"query": "household energy", "limit": 5})
    assert res["query"] == "household energy"
    assert res["limit"] == 5
    assert res["results"] == ["match_1"]


def test_unknown_tool_raises():
    bridge = StrandsMCPToolBridge()
    with pytest.raises(KeyError, match="Strands tool 'non_existent' not registered"):
        bridge.invoke_from_mcp("non_existent", {})
