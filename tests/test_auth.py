"""Auth fortress tests: adult PIN + per-persona tokens on Tier-2 REST.

Zero-config stays open (no env -> all pass). The moment HEARTH_ADULT_PIN or
HEARTH_TOKENS is set, money/unlock/reset/brain/persona-escalation go fail-closed.
"""
from __future__ import annotations

import os
import sys

import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))

import server
from hearth import auth, memory, proposals


@pytest.fixture(scope="function")
def app():
    return server.mcp.streamable_http_app()


@pytest.fixture()
def client(app):
    # No lifespan: FastMCP session manager runs once per process.
    c = TestClient(app, raise_server_exceptions=False)
    yield c


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in ("HEARTH_ADULT_PIN", "HEARTH_TOKENS", "HEARTH_TOKENS_FILE"):
        monkeypatch.delenv(var, raising=False)
    yield
    # Direct os.environ writes below must never leak into other test files.
    for var in ("HEARTH_ADULT_PIN", "HEARTH_TOKENS", "HEARTH_TOKENS_FILE"):
        os.environ.pop(var, None)


def _mk_pending(kind="test-auth-probe"):
    item = proposals.propose(kind=kind, title="auth probe", reasons="test",
                             risk_level="low", diff="none", meta={})
    assert item["status"] == "pending"
    return item["id"]


# --- unit: inactive means open (zero-config demo preserved) ---

def test_inactive_is_open():
    assert not auth.auth_configured()
    ident = auth.identify()
    assert ident.full is True


def test_pin_check():
    os.environ["HEARTH_ADULT_PIN"] = "correct-horse"
    assert auth.check_pin("correct-horse") is True
    assert auth.check_pin("wrong") is False
    assert auth.check_pin("") is False


def test_token_identity_scopes():
    os.environ["HEARTH_TOKENS"] = "admintok123:admin,leotok:child"
    assert auth.identify(bearer="admintok123").full is True
    child = auth.identify(bearer="leotok")
    assert child.full is False and child.persona == "child"
    assert auth.identify(bearer="bogus").persona == "intruder"


# --- HTTP: reset + brain switch gated only when configured ---

def test_reset_open_when_unconfigured(client):
    assert client.post("/api/reset").status_code == 200


def test_reset_gated_with_pin(client):
    os.environ["HEARTH_ADULT_PIN"] = "s3cret-pin"
    assert client.post("/api/reset").status_code == 401
    r = client.post("/api/reset", headers={"X-Hearth-PIN": "s3cret-pin"})
    assert r.status_code == 200


def test_brain_switch_gated_with_pin(client):
    os.environ["HEARTH_ADULT_PIN"] = "s3cret-pin"
    r = client.post("/api/brain", json={"provider": "local"})
    assert r.status_code == 401
    r = client.post("/api/brain", json={"provider": "local"},
                    headers={"X-Hearth-PIN": "s3cret-pin"})
    assert r.status_code == 200


# --- HTTP: approve needs adulthood; reject stays open (no side effect) ---

def test_approve_gated_reject_open(client):
    os.environ["HEARTH_ADULT_PIN"] = "s3cret-pin"
    pid = _mk_pending()
    assert client.post("/api/decide", json={"id": pid, "approved": True}).status_code == 401
    r = client.post("/api/decide", json={"id": pid, "approved": False})
    assert r.status_code == 200
    assert proposals.get_proposal(pid)["status"] == "rejected"


def test_approve_with_pin_and_replay_409(client):
    os.environ["HEARTH_ADULT_PIN"] = "s3cret-pin"
    pid = _mk_pending()
    h = {"X-Hearth-PIN": "s3cret-pin"}
    assert client.post("/api/decide", json={"id": pid, "approved": True}, headers=h).status_code == 200
    r = client.post("/api/decide", json={"id": pid, "approved": True}, headers=h)
    assert r.status_code == 409


def test_child_token_cannot_approve(client):
    os.environ["HEARTH_TOKENS"] = "admintok123:admin,leotok:child"
    pid = _mk_pending()
    r = client.post("/api/decide", json={"id": pid, "approved": True},
                    headers={"Authorization": "Bearer leotok"})
    assert r.status_code == 403
    r = client.post("/api/decide", json={"id": pid, "approved": True},
                    headers={"Authorization": "Bearer admintok123"})
    assert r.status_code == 200


# --- HTTP: owner binding follows the token, not the body ---

def test_owner_bound_to_token(client):
    os.environ["HEARTH_TOKENS"] = "leotok:child"
    r = client.post("/api/memory", json={"key": "authprobe", "value": "x", "owner": "admin"},
                    headers={"Authorization": "Bearer leotok"})
    assert r.status_code == 200
    rows = memory.query("authprobe")
    assert rows and rows[0]["owner"] == "child"
    memory.delete("authprobe")


# --- HTTP: persona escalation gated ---

def test_persona_escalation_gated(client):
    os.environ["HEARTH_ADULT_PIN"] = "s3cret-pin"
    assert client.post("/api/persona", json={"id": "admin"}).status_code == 401
    r = client.post("/api/persona", json={"id": "admin"},
                    headers={"X-Hearth-PIN": "s3cret-pin"})
    assert r.status_code == 200
