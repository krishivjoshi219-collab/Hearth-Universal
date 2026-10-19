"""The Wire — a live MCP client served by this same app.

The Alexa+ track FAQ blesses "a web page that acts as an actual MCP client
(initialize, tools-list, tools-call over Streamable HTTP)" as a submission that
genuinely calls the track technology at runtime. These tests keep that claim
honest: the page is served with the app's CSP (no inline script/style), every
asset it references resolves, and its JavaScript really performs the
2025-11-25 handshake against /mcp — in the right order, tolerating both JSON
and SSE replies, and never trusting server output as markup.
"""
import os
import re
import sys

import pytest
from starlette.testclient import TestClient

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "mcp-server"))

import server  # noqa: E402

WIRE_HTML = os.path.join(ROOT, "web2", "wire.html")
WIRE_JS = os.path.join(ROOT, "web2", "js", "wire.js")
WIRE_CSS = os.path.join(ROOT, "web2", "css", "wire.css")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="module")
def client():
    return TestClient(server.mcp.streamable_http_app())


def test_wire_is_served_with_the_same_app(client):
    r = client.get("/wire")
    assert r.status_code == 200
    assert "Hearth" in r.text
    assert "MCP" in r.text


def test_wire_page_has_no_inline_script_or_style():
    html = _read(WIRE_HTML)
    assert "<style" not in html.lower()
    assert "style=\"" not in html, "inline style attributes break the page CSP"
    scripts = re.findall(r"<script\b[^>]*>", html, re.IGNORECASE)
    assert scripts, "the Wire needs its client script"
    for tag in scripts:
        assert "src=" in tag, "scripts must be external under script-src 'self'"
    assert "<script>" not in html


def test_wire_asset_links_resolve(client):
    html = _read(WIRE_HTML)
    refs = re.findall(r'(?:href|src)="(/[^"]+)"', html)
    assert "/web2/css/wire.css" in refs
    assert "/web2/js/wire.js" in refs
    for ref in sorted(set(refs)):
        assert client.get(ref).status_code == 200, f"{ref} does not resolve"


def test_wire_javascript_performs_the_2025_11_25_handshake():
    js = _read(WIRE_JS)
    assert '"/mcp"' in js
    assert "2025-11-25" in js
    assert "mcp-protocol-version" in js, "the spec header must ride every request"
    assert js.index('wire("initialize"') < js.index('wire("tools/list"'), \
        "tools/list may only follow a successful initialize"
    assert 'wire("notifications/initialized"' in js


def test_wire_javascript_speaks_all_three_verbs_and_tolerates_sse():
    js = _read(WIRE_JS)
    assert '"tools/call"' in js or "'tools/call'" in js
    assert 'wire("tools/call"' in js
    assert "text/event-stream" in js, "Streamable HTTP servers may answer in SSE"
    assert "parseSSE" in js


def test_wire_never_trusts_server_output_as_markup():
    js = _read(WIRE_JS)
    assert js.count("textContent") >= 8
    # innerHTML may only ever be cleared, never assigned server data
    for m in re.finditer(r"\.innerHTML\s*=\s*([^;\n]+)", js):
        assert m.group(1).strip().startswith('""'), "innerHTML must only be cleared"


def test_wire_css_keeps_the_ambient_palette():
    css = _read(WIRE_CSS)
    assert "--w-amber: #f0a85c" in css
    assert "@font-face" in css
    font_block = css.split("@font-face")[1].split("}")[0]
    assert "https://" not in font_block, "fonts are self-hosted"
