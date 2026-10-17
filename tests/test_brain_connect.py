"""Bring-your-own-key brain: the preview's "enter your own API key" flow.

The product promise these tests lock down:

  * the status endpoint is redacted — a raw key never appears in any response,
  * validation fails fast with friendly messages,
  * the key persists at state/brain_config.json with 0600 permissions,
  * a connected key *genuinely* reaches a provider: brains.chat completes a
    real HTTP round-trip to a mock OpenAI-compatible endpoint over a socket,
    and the answer comes back through the same path the UI uses, and
  * the echo surface declares and wires the ask input + connect dialog.

Everything runs offline: the "provider" is a local mock speaking just enough
OpenAI wire protocol. No real keys, no egress.
"""
import json
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from starlette.testclient import TestClient

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "mcp-server"))

import server  # noqa: E402
from hearth import brain_config  # noqa: E402

ECHO_HTML = os.path.join(ROOT, "web2", "echo.html")
ECHO_JS = os.path.join(ROOT, "web2", "js", "echo.js")

MOCK_KEY = "sk-mock-key-123456"
MOCK_ANSWER = "MOCK-BRAIN-ANSWER"

# Every env var brain_config writes. Snapshot + restore so a connect test can
# never leak into the rest of the suite (some tests assert the local provider).
_BRAIN_ENV = (
    "HEARTH_BRAIN_PROVIDER",
    "HEARTH_BASE_URL",
    "HEARTH_MODEL",
    "VAULT_MODEL_KEY",
    "AWS_BEDROCK_ENABLED",
    "AWS_BEDROCK_MODEL",
    "AWS_DEFAULT_REGION",
)


@pytest.fixture(scope="module")
def client():
    return TestClient(server.mcp.streamable_http_app())


@pytest.fixture(autouse=True)
def _isolated_brain(tmp_path, monkeypatch):
    """Per-test state dir + full env snapshot/restore around the test."""
    saved = {k: os.environ.get(k) for k in _BRAIN_ENV}
    monkeypatch.setenv("HEARTH_STATE_DIR", str(tmp_path))
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# --- mock OpenAI-compatible provider -----------------------------------------

class _MockProvider(BaseHTTPRequestHandler):
    """Just enough OpenAI wire protocol for brains.chat + the pre-flight test."""

    last_auth = None
    last_payload = None

    def _send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/").endswith("/models"):
            self._send_json(200, {"data": [{"id": "mock-small"}, {"id": "mock-large"}]})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if not self.path.rstrip("/").endswith("/chat/completions"):
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        type(self).last_payload = json.loads(self.rfile.read(length) or b"{}")
        type(self).last_auth = self.headers.get("Authorization", "")
        if type(self).last_auth != "Bearer " + MOCK_KEY:
            self._send_json(401, {"error": {"message": "bad key"}})
            return
        self._send_json(200, {
            "choices": [{"message": {"content": MOCK_ANSWER}}],
            "usage": {"total_tokens": 7},
        })

    def log_message(self, *args):  # keep pytest output clean
        pass


@pytest.fixture()
def mock_provider():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _MockProvider)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:%d/v1" % srv.server_address[1]
    finally:
        srv.shutdown()
        srv.server_close()


def _connect(client, base_url, **extra):
    payload = {"provider": "custom", "base_url": base_url, "model": "mock-small",
               "api_key": MOCK_KEY}
    payload.update(extra)
    r = client.post("/api/brain/connect", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


# --- status + redaction ------------------------------------------------------

def test_status_is_redacted_and_offers_presets(client):
    r = client.get("/api/brain/connect")
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    ids = {p["id"] for p in d["presets"]}
    assert {"openai", "ollama", "custom", "bedrock"} <= ids
    assert d["key_hint"] == "", "a disconnected box must not hint at any key"
    assert "api_key" not in json.dumps(d)


def test_connect_masks_the_key_everywhere(client):
    r = client.post("/api/brain/connect", json={
        "provider": "groq", "api_key": "gsk_secret_987654321", "model": "llama-3.3-70b-versatile",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is True
    assert body["provider"] == "groq"
    assert body["key_hint"] == "…4321"
    assert "gsk_secret_987654321" not in r.text
    # And a fresh status read is equally redacted.
    assert "gsk_secret_987654321" not in client.get("/api/brain/connect").text


def test_validation_fails_fast_with_friendly_errors(client, monkeypatch):
    r = client.post("/api/brain/connect", json={"provider": "definitely-not"})
    assert r.status_code == 400 and "Unknown provider" in r.json()["error"]

    r = client.post("/api/brain/connect", json={
        "provider": "custom", "base_url": "ftp://nope", "api_key": "k",
    })
    assert r.status_code == 400 and "http(s)" in r.json()["error"]

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    r = client.post("/api/brain/connect", json={"provider": "openai"})
    assert r.status_code == 400 and "API key is required" in r.json()["error"]


def test_openai_preset_can_use_the_env_key(client, monkeypatch):
    """When the machine already exports OPENAI_API_KEY, the field can stay blank."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-provided-123456")
    r = client.post("/api/brain/connect", json={"provider": "openai", "model": "gpt-4o-mini"})
    assert r.status_code == 200
    assert r.json()["configured"] is True
    from hearth import brains
    assert brains._get_active_provider() == "openai"


# --- persistence -------------------------------------------------------------

def test_key_persists_at_0600_and_survives_restart(client):
    _connect(client, "https://mock.example.com/v1", provider="custom",
             api_key="sk-persist-secret-4242", model="mock-small")

    f = brain_config.config_file()
    assert f.exists()
    assert oct(f.stat().st_mode & 0o777) == "0o600", "the key file must not be world-readable"
    assert json.loads(f.read_text())["api_key"] == "sk-persist-secret-4242"

    # Simulate a server restart: drop the env overlay, then load() from disk.
    brain_config._unapply()
    assert os.environ.get("HEARTH_BRAIN_PROVIDER") is None
    assert brain_config.load() is True
    assert os.environ["HEARTH_BRAIN_PROVIDER"] == "custom"
    assert os.environ["HEARTH_BASE_URL"] == "https://mock.example.com/v1"
    assert os.environ["VAULT_MODEL_KEY"] == "sk-persist-secret-4242"


def test_disconnect_clears_file_and_env(client):
    _connect(client, "https://mock.example.com/v1", provider="custom",
             api_key="sk-clear-secret-7777", model="mock-small")
    r = client.post("/api/brain/disconnect")
    assert r.status_code == 200
    assert r.json()["configured"] is False
    assert not brain_config.config_file().exists()
    assert "VAULT_MODEL_KEY" not in os.environ
    assert os.environ.get("HEARTH_BRAIN_PROVIDER") is None


def test_bedrock_credentials_never_come_back(client):
    r = client.post("/api/brain/connect", json={
        "provider": "bedrock", "model": "us.amazon.nova-pro-v1:0", "region": "us-west-2",
        "access_key_id": "AKIAEXAMPLE123", "secret_access_key": "very-secret-value",
    })
    assert r.status_code == 200
    assert r.json()["configured"] is True
    assert "very-secret-value" not in r.text
    assert os.environ["AWS_BEDROCK_ENABLED"] == "1"
    assert os.environ["AWS_DEFAULT_REGION"] == "us-west-2"

    r = client.post("/api/brain/connect", json={"provider": "bedrock", "region": "mars-1"})
    assert r.status_code == 400 and "us-east-1" in r.json()["error"]


# --- the real thing: bytes on a socket ---------------------------------------

def test_connected_key_reaches_the_provider_over_the_wire(client, mock_provider):
    out = _connect(client, mock_provider)
    assert out["configured"] is True and out["host"].startswith("127.0.0.1")

    from hearth import brains
    res = brains.chat([{"role": "user", "content": "hello there"}])
    assert res.provider == "openai-compatible"
    assert MOCK_ANSWER in res.text
    assert res.fallback is False
    assert _MockProvider.last_auth == "Bearer " + MOCK_KEY
    assert _MockProvider.last_payload["model"] == "mock-small"


def test_preflight_test_reports_reachable_models(client, mock_provider):
    r = client.post("/api/brain/connect", json={
        "provider": "custom", "base_url": mock_provider, "model": "mock-small",
        "api_key": MOCK_KEY, "test": True,
    })
    assert r.status_code == 200
    t = r.json()["test"]
    assert t["ok"] is True
    assert "mock-small" in t["models"]


def test_ask_with_connected_brain_answers_and_never_autosends(client, mock_provider):
    """The /api/chat path the composer uses stays 200 and returns a draft."""
    _connect(client, mock_provider)
    r = client.post("/api/chat", json={"message": "what is the household doing tonight"})
    assert r.status_code == 200
    d = r.json()
    assert d.get("draft"), "every free-form turn must come back with an answer"
    # Anything consequential is staged, never executed: the id is a proposal.
    for pid in d.get("proposals_created", []):
        assert isinstance(pid, str) and pid


def test_wrong_key_fails_over_to_the_offline_engine(client, mock_provider):
    """A bad key must degrade gracefully, not 500 the household."""
    client.post("/api/brain/connect", json={
        "provider": "custom", "base_url": mock_provider, "model": "mock-small",
        "api_key": "sk-totally-wrong-key",
    })
    from hearth import brains
    res = brains.chat([{"role": "user", "content": "still there?"}])
    assert res.fallback is True  # honest posture: local engine answered instead
    assert "401" in res.text or "HTTPError" in res.text or "Unauthorized" in res.text


# --- UI wiring ---------------------------------------------------------------

def test_echo_declares_the_ask_input_and_connect_dialog():
    html = _read(ECHO_HTML)
    for needle in (
        'id="brainBtn"', 'id="brainCallout"', 'id="askForm"', 'id="askText"',
        'id="askSend"', 'id="keyBackdrop"', 'id="keyProvider"', 'id="keyApiKey"',
        'id="keySaveBtn"', 'id="keyTestBtn"', 'id="keyClearBtn"',
    ):
        assert needle in html, f"echo.html is missing {needle}"


def test_echo_javascript_wires_free_form_ask_and_brain():
    js = _read(ECHO_JS)
    assert '"/api/chat"' in js, "the composer must call the planner"
    assert '"/api/brain/connect"' in js, "the connect dialog must call the brain API"
    assert '"/api/brain/disconnect"' in js
    # New endpoints must stay OUT of the RENDERERS showcase map.
    renderers = {inner for _, inner in re.findall(r'("(/api/[a-z/-]+)"):\s*\(d\)', js)}
    assert "/api/chat" not in renderers
    assert not any("brain" in p for p in renderers)
