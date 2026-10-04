"""Echo Show surface tests.

An Echo Show is an ambient, glanceable, voice-first device. These tests lock the
properties that make it one:

  * it is actually served at /echo with the same CSP as the rest of the app
    (no inline script/style, since the server sets script-src 'self')
  * every asset it references resolves (a missing file means a blank screen for
    a judge, and nothing else would catch it)
  * its type scale and touch targets are meaningfully larger than the ops
    cockpit -- that difference *is* the point of the surface
  * each showcase button calls a real endpoint with the exact payload it sends,
    and the renderer in echo.js only touches fields that endpoint returns
  * display modes mirror the four modes the MCP server implements
"""
import json
import os
import re
import sys

import pytest
from starlette.testclient import TestClient

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "mcp-server"))

import server  # noqa: E402

ECHO_HTML = os.path.join(ROOT, "web2", "echo.html")
ECHO_CSS = os.path.join(ROOT, "web2", "css", "echo.css")
ECHO_JS = os.path.join(ROOT, "web2", "js", "echo.js")


@pytest.fixture(scope="module")
def client():
    return TestClient(server.mcp.streamable_http_app())


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# --- serving -----------------------------------------------------------------

def test_echo_surface_is_served(client):
    r = client.get("/echo")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Hearth" in r.text


def test_echo_assets_are_served_with_correct_content_types(client):
    for path, ctype in (("/web2/echo.html", "text/html"),
                        ("/web2/css/echo.css", "text/css"),
                        ("/web2/js/echo.js", "javascript")):
        r = client.get(path)
        assert r.status_code == 200, path
        assert ctype in r.headers["content-type"], (path, r.headers["content-type"])


def test_echo_page_has_no_inline_script_or_style(client):
    """CSP is script-src 'self'; style-src 'self' -- inline code would be blocked."""
    html = client.get("/echo").text
    assert "<script>" not in html
    assert "javascript:" not in html.lower()
    assert not re.search(r"<style[\s>]", html)
    assert not re.search(r'<div[^>]+style="', html)
    # Script + stylesheet must be external files.
    assert '<script src="/web2/js/echo.js">' in html
    assert 'href="/web2/css/echo.css"' in html


def test_every_asset_referenced_by_echo_html_resolves(client):
    html = client.get("/echo").text
    refs = re.findall(r'(?:href|src)="(/[^"]+)"', html)
    assert refs, "expected at least one asset reference"
    for ref in refs:
        assert client.get(ref).status_code == 200, f"missing asset: {ref}"


def test_echo_page_inherits_security_headers(client):
    r = client.get("/echo")
    csp = r.headers.get("content-security-policy", "")
    assert "script-src 'self'" in csp
    assert r.headers.get("x-content-type-options") == "nosniff"


# --- design intent -----------------------------------------------------------

def test_type_scale_is_much_larger_than_the_ops_cockpit():
    """The whole justification for this surface is room readability."""
    css = _read(ECHO_CSS)
    m = re.search(r"--e-body:\s*(\d+(?:\.\d+)?)px", css)
    assert m, "expected an --e-body token in echo.css"
    echo_body = float(m.group(1))

    cockpit = _read(os.path.join(ROOT, "web2", "css", "tokens.css"))
    m2 = re.search(r"--fs-body:\s*(\d+(?:\.\d+)?)px", cockpit)
    assert m2, "expected --fs-body in the cockpit tokens"
    cockpit_body = float(m2.group(1))

    assert echo_body >= cockpit_body * 1.4, (
        f"Echo body type ({echo_body}px) must be far larger than the cockpit "
        f"({cockpit_body}px) or the surface is unreadable across a room."
    )


def test_touch_targets_meet_echo_minimum():
    css = _read(ECHO_CSS)
    # .btn (tray actions + mic) and .ask (phrase chips) are the touch surface.
    btn = re.search(r"\.btn\s*\{[^}]*min-height:\s*(\d+)px", css, re.S)
    ask = re.search(r"\.ask\s*\{[^}]*min-height:\s*(\d+)px", css, re.S)
    assert btn and ask, "expected min-height on .btn and .ask"
    assert int(btn.group(1)) >= 64
    assert int(ask.group(1)) >= 64


def test_display_modes_match_the_mcp_server_implementation(client):
    """The chips must offer exactly the modes format_display_response accepts."""
    from hearth.alexaplus_addon import alexaplus_engine

    supported = set(alexaplus_engine.format_display_response("x", display_mode="inline")["supported_modes"])
    html = _read(ECHO_HTML)
    chips = set(re.findall(r'data-mode="([a-z-]+)"', html))
    assert chips == supported, f"echo chips {chips} != server modes {supported}"


def test_reduced_motion_is_respected():
    assert "prefers-reduced-motion" in _read(ECHO_CSS)


def test_voice_only_mode_hides_the_visual_surfaces():
    css = _read(ECHO_CSS)
    assert 'body[data-display="voice-only"]' in css


# --- showcase buttons: real endpoints, exact payloads -------------------------

SHOWCASE = [
    ("/api/forensics/reconstruct", {"incident_type": "perimeter_anomaly"},
     ["verdict", "confidence_score", "summary", "timeline", "audit_proof"]),
    ("/api/parliament/deliberate", {"topic": "evening tariff vs comfort"},
     ["speeches", "nash_equilibrium_score", "vote", "candidate_count"]),
    ("/api/causal/simulate", {"days_ahead": 7, "iterations": 250},
     ["vulnerabilities", "grid_resilience_score", "monte_carlo_iterations",
      "quantiles", "expected_savings_usd"]),
    ("/api/swarm/grid", {},
     ["p2p_transactions", "cooperative_rate_kwh", "economic_impact",
      "environmental_impact", "voice_summary"]),
    ("/api/mediation/treaty", {},
     ["covenants", "fairness_index_out_of_10", "nash_achievement",
      "cooperation_coverage_pct", "envy_gap", "projected_monthly_savings_usd"]),
    ("/api/acoustic/scan", {}, ["appliances", "voice_summary"]),
]


def _showcase_buttons():
    html = _read(ECHO_HTML)
    out = []
    for m in re.finditer(r'<button class="ask"[^>]*data-go="([^"]+)"[^>]*data-body=\'([^\']*)\'', html):
        out.append((m.group(1), json.loads(m.group(2))))
    return out


def test_every_showcase_button_maps_to_a_tested_endpoint():
    buttons = _showcase_buttons()
    assert len(buttons) >= 6, f"expected the full showcase row, found {len(buttons)}"
    known = {path for path, _, _ in SHOWCASE}
    for path, _ in buttons:
        assert path in known, f"showcase button targets untested endpoint: {path}"


@pytest.mark.parametrize("path,body,fields", SHOWCASE, ids=[p for p, _, _ in SHOWCASE])
def test_showcase_call_succeeds_and_satisfies_the_renderer(client, path, body, fields):
    r = client.post(path, json=body)
    assert r.status_code == 200, f"{path} returned {r.status_code}"
    data = r.json()
    missing = [f for f in fields if f not in data]
    assert not missing, f"{path} response lacks {missing}, which echo.js renders"


def test_showcase_payloads_in_markup_match_the_tested_bodies():
    """The payload in the HTML must be the payload we verified above."""
    tested = {path: body for path, body, _ in SHOWCASE}
    for path, body in _showcase_buttons():
        assert body == tested[path], (
            f"echo.html sends {body} to {path} but the test verifies {tested[path]}"
        )


# --- renderer field usage ----------------------------------------------------

def test_renderer_paths_all_exist_in_the_javascript():
    js = _read(ECHO_JS)
    renderers = set(re.findall(r'("(/api/[a-z/-]+)"):\s*\(d\)', js))
    renderers = {inner for _, inner in renderers}
    assert renderers, "expected per-endpoint renderers"
    known = {path for path, _, _ in SHOWCASE}
    for path in renderers:
        assert path in known, f"echo.js has a renderer for untested endpoint: {path}"


def test_javascript_avoids_retired_field_names():
    js = _read(ECHO_JS)
    for retired in ("data.skill.name", "audit_proof_sha256"):
        assert retired not in js


def test_supporting_endpoints_used_by_the_surface_respond(client):
    """The status pill and tray poll these; a 404 would leave the surface stale."""
    assert client.post("/api/chat", json={"message": "home state"}).status_code == 200
    assert client.get("/api/audit?limit=3").status_code == 200
    assert client.get("/health").status_code == 200