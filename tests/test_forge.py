"""Hearth Forge contracts: a household rule becomes a real, callable MCP tool.

The demo claim is strong ("it writes and mounts a new tool"), so the tests prove
the whole chain, not a mock: synthesis -> Sentinel/AST/smoke reports -> the tool
appears in the live MCP catalog -> it answers calls with schema defaults.
"""
import asyncio
import contextlib
import os
import sys

import pytest
from starlette.testclient import TestClient

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "mcp-server"))

import server  # noqa: E402

REQUIREMENT = "Charge the EV with at least 8 kWh after 10pm, never pay above $0.28/kWh"


@pytest.fixture(scope="module")
def client():
    return TestClient(server.mcp.streamable_http_app())


@pytest.fixture(scope="module")
def forged(client):
    res = client.post("/api/forge/synthesize", json={"requirement": REQUIREMENT})
    assert res.status_code == 200, res.text
    data = res.json()
    yield data
    # Keep the catalog deterministic for the rest of the suite.
    server._FORGED_TOOLS.pop(data.get("mcp_tool", ""), None)
    with contextlib.suppress(Exception):
        server.mcp.remove_tool(data["mcp_tool"])


def test_forge_compiles_and_mounts_a_real_mcp_tool(forged):
    assert forged["ok"] is True
    assert forged["mcp_tool"].startswith("hearth_forge_")
    assert forged["test_report"]["ok"] is True
    assert forged["ast_report"]["ok"] is True
    assert "def execute_plan" in forged["code"]
    names = {t.name for t in server.mcp._tool_manager.list_tools()}
    assert forged["mcp_tool"] in names
    assert forged["tools_count"] == len(names)


def test_forged_tool_is_callable_over_mcp_protocol(forged):
    content = asyncio.run(server.mcp.call_tool(forged["mcp_tool"], {}))
    text = content[0].text
    assert "savings_usd" in text
    assert '"applied_hour": 22' in text


def test_forged_tool_invokes_with_schema_defaults(client, forged):
    res = client.post("/api/forge/invoke", json={"tool": forged["mcp_tool"], "params": {}})
    data = res.json()
    assert data["ok"] is True
    assert data["result"]["applied_hour"] == 22
    assert data["result"]["savings_usd"] >= 0


def test_forge_catalog_lists_the_tool(client, forged):
    data = client.get("/api/forge/tools").json()
    assert data["ok"] is True
    assert any(t["name"] == forged["mcp_tool"] for t in data["tools"])


def test_forge_rejects_vague_requests(client):
    res = client.post("/api/forge/synthesize", json={"requirement": "hi"})
    assert res.status_code == 400
