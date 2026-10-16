"""Tests for the vendored re-export of the standalone mcp-strands-adapter package.

The implementation lives in open-source-contribution/mcp-strands-adapter/. These
tests exist to prove that (a) the vendored module resolves that single
implementation rather than carrying its own copy, and (b) the bridge behaves
correctly when imported through the main project.
"""
import pytest

from hearth import mcp_strands_adapter


def sample_calc(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def test_vendored_module_re_exports_single_implementation():
    """The vendored module must not carry a second copy of the logic."""
    standalone = pytest.importorskip("mcp_strands_adapter")
    # Same class objects => one implementation, imported by path.
    assert mcp_strands_adapter.MCPServerBridge is standalone.MCPServerBridge
    assert mcp_strands_adapter.to_mcp_tool is standalone.to_mcp_tool


def test_vendored_module_has_no_duplicate_class_definitions():
    """Guard against reintroducing a parallel implementation in src/hearth."""
    import inspect
    source = inspect.getsource(mcp_strands_adapter)
    assert "class StrandsMCPToolBridge" not in source
    assert "class MCPServerBridge" not in source


def test_bridge_reflection_and_invocation():
    bridge = mcp_strands_adapter.MCPServerBridge(prefix="test_")
    definition = bridge.add(sample_calc)
    assert definition["name"] == "test_sample_calc"
    assert "Add two numbers" in definition["description"]
    assert "a" in definition["inputSchema"]["properties"]
    assert "b" in definition["inputSchema"]["properties"]
    assert definition["inputSchema"]["required"] == ["a", "b"]

    assert len(bridge.list_tools()) == 1
    assert bridge.call("test_sample_calc", {"a": 10, "b": 25}) == 35


def test_bridge_is_exported_from_hearth_package():
    assert callable(mcp_strands_adapter.to_mcp_tool)
    assert callable(mcp_strands_adapter.strands_available)