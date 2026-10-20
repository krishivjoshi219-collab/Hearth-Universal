"""The consumer landing page (/) — first thing a judge sees.

These tests keep it honest and on-brand: served by this same app with the
app's CSP (no inline script/style), every asset resolves, the product copy
stays consumer-first (no protocol jargon above the labelled "under the hood"
band, no emoji iconography), the CTAs point at the real surfaces, and the
controller only touches the DOM through textContent + CSS custom properties.
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

LANDING_HTML = os.path.join(ROOT, "web2", "landing.html")
LANDING_JS = os.path.join(ROOT, "web2", "js", "landing.js")
LANDING_CSS = os.path.join(ROOT, "web2", "css", "landing.css")

EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D\U0001F3FB-\U0001F3FF]"
)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="module")
def client():
    return TestClient(server.mcp.streamable_http_app())


def test_landing_is_served_at_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Hearth" in r.text
    assert "Save me $800" in r.text


def test_landing_has_no_inline_script_or_style():
    html = _read(LANDING_HTML)
    assert "<style" not in html.lower()
    assert 'style="' not in html, "inline style attributes break the page CSP"
    assert not re.search(r"\son[a-z]+\s*=", html), "no inline event handlers"
    scripts = re.findall(r"<script\b[^>]*>", html, re.IGNORECASE)
    assert scripts, "the landing needs its controller script"
    for tag in scripts:
        assert "src=" in tag, "scripts must be external under script-src 'self'"
    assert "<script>" not in html


def test_landing_asset_links_resolve(client):
    html = _read(LANDING_HTML)
    refs = re.findall(r'(?:href|src)="(/[^"]+)"', html)
    assert "/web2/css/landing.css" in refs
    assert "/web2/js/landing.js" in refs
    # The master film is a 28.6MB release artifact and is deliberately not
    # versioned (*.mp4 is gitignored), so a clean CI checkout has no bytes
    # behind this link. Assert the link is present in the page, then skip the
    # 200 check for that one unversioned artifact.
    assert "/demo_film/HEARTH_DEMO_FINAL.mp4" in refs
    for ref in sorted(set(refs)):
        if ref == "/demo_film/HEARTH_DEMO_FINAL.mp4":
            continue
        assert client.get(ref).status_code == 200, f"{ref} does not resolve"


def test_landing_ctas_point_at_the_real_surfaces():
    html = _read(LANDING_HTML)
    assert 'href="/echo"' in html, "the demo is the primary CTA"
    assert 'href="/wire"' in html, "judges need the live-standard page"
    assert 'href="/web2/index.html"' in html, "the engineering view stays reachable"


def test_product_copy_stays_consumer_first():
    html = _read(LANDING_HTML)
    above_the_fold = html.split('<section class="built"')[0]
    for jargon in ("MCP", "2025-11-25", "JSON", "RPC", "SHA-256", "endpoint", "API"):
        assert jargon not in above_the_fold, (
            f"{jargon!r} leaks above the labelled 'under the hood' band"
        )
    # The labelled tech band may name the standard — that is the point of it.
    assert "MCP spec 2025-11-25" in html


def test_no_emoji_iconography():
    assert not EMOJI.search(_read(LANDING_HTML)), "icons are SVG, never emoji"
    assert not EMOJI.search(_read(LANDING_JS))


def test_controller_hydrates_from_the_live_server_only():
    js = _read(LANDING_JS)
    assert '"/api/renewals"' in js
    assert '"/health"' in js
    # Never trust server output as markup.
    assert js.count("textContent") >= 6
    for m in re.finditer(r"\.innerHTML\s*=\s*([^;\n]+)", js):
        assert m.group(1).strip().startswith('""'), "innerHTML must only be cleared"


def test_controller_keeps_the_style_hygiene():
    js = _read(LANDING_JS)
    assert ".style.transform" not in js, "tilt rides CSS custom properties"
    assert "setProperty" in js
    assert "--rx" in js and "--ry" in js


def test_css_keeps_the_ambient_palette():
    css = _read(LANDING_CSS)
    assert "--amber: #f0a85c" in css
    assert "@font-face" in css
    font_block = css.split("@font-face")[1].split("}")[0]
    assert "https://" not in font_block, "fonts are self-hosted"
    assert "prefers-reduced-motion" in css
    assert "scripting: none" in css, "no-JS visitors still get the whole page"
