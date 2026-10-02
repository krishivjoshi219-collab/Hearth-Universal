"""Integration tests for new creative MCP tools and REST endpoints."""
import pytest
from starlette.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))
import server


@pytest.fixture(scope="function")
def app():
    return server.mcp.streamable_http_app()


@pytest.fixture()
def client(app):
    c = TestClient(app, raise_server_exceptions=False)
    yield c
    server._GLOBAL_BUCKETS.clear()
    server._RATE_BUCKETS.clear()


def test_health_includes_creative_telemetry(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["strands_harness_ok"] is True
    assert data["agent_skills_count"] >= 3


def test_strands_rest_endpoints(client):
    r1 = client.get("/api/strands/telemetry")
    assert r1.status_code == 200
    assert r1.json()["framework"] == "AWS Strands Agents SDK + Bedrock AgentCore"

    r2 = client.post("/api/strands/orchestrate", json={"goal": "Audit food stock and verify house security"})
    assert r2.status_code == 200
    assert r2.json()["ok"] is True


def test_agent_skills_manifest_endpoint(client):
    r = client.get("/api/agent-skills")
    assert r.status_code == 200
    assert r.json()["manifestVersion"] == "1.0"
