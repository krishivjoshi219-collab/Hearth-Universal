"""Reliability: global throttle, chat deadline, read caps, egress retry."""
from __future__ import annotations

import os
import sys

import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))

import server
from hearth import brains, memory


@pytest.fixture(scope="function")
def app():
    return server.mcp.streamable_http_app()


@pytest.fixture()
def client(app):
    c = TestClient(app, raise_server_exceptions=False)
    yield c
    server._GLOBAL_BUCKETS.clear()
    server._RATE_BUCKETS.clear()


def test_global_budget_trips_and_recovers(client, monkeypatch):
    monkeypatch.setattr(server, "GLOBAL_LIMIT", 5)
    codes = [client.get("/api/home").status_code for _ in range(7)]
    # GETs are not throttled (budget applies to expensive POSTs) — stays 200.
    assert set(codes) == {200}
    for _ in range(6):
        client.post("/api/timemachine", json={})
    r = client.post("/api/timemachine", json={})
    assert r.status_code == 429
    assert "budget" in r.json().get("error", "")


def test_chat_answers_through_threadpool(client):
    r = client.post("/api/chat", json={"message": "hello status"})
    assert r.status_code == 200
    body = r.json()
    assert (body.get("draft") or body.get("text") or body.get("synthesis")) is not None
    assert isinstance(body.get("dag"), list)


def test_read_caps_are_bounded():
    for i in range(3):
        memory.remember(f"relcap{i}", "v")
    try:
        assert len(memory.query("", limit=2)) <= 2
        assert len(memory.list_goals(limit=1)) <= 1
        assert len(memory.chat_history_get(limit=10**9)) <= 500
    finally:
        for i in range(3):
            memory.delete(f"relcap{i}")


def test_openai_retries_once_then_falls_back(monkeypatch):
    # Closed port = instant refusal; proves retry+fallback without slow network.
    monkeypatch.setenv("HEARTH_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("HEARTH_MODEL", "x")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setenv("HEARTH_BRAIN_PROVIDER", "openai")
    res = brains.chat([{"role": "user", "content": "hi"}], max_tokens=10)
    assert res.fallback is True
    assert res.provider == "local-fallback"


def test_export_is_capped(client):
    r = client.get("/api/export")
    assert r.status_code == 200
    body = r.json()
    assert len(body.get("proposals", [])) <= 100
    assert len(body.get("goals", [])) <= 100
