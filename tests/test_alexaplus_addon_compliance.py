"""Automated Test Suite for Official Amazon Alexa+ Add-on & OAuth 2.1 RFC 9728 Compliance.

Validates against official Amazon Developer documentation:
https://developer.amazon.com/docs/alexaplus/add-ons/home.html
1. RFC 9728 Protected Resource Metadata (PRM)
2. OAuth 2.1 Authorization Server Metadata
3. Tier 1: Client Credentials Grant (M2M) -> mcp:service
4. Tier 2: Authorization Code Grant with PKCE S256 -> mcp:tools mcp:resources
5. Refresh Token Grant
6. Display Modes: Inline, Fullscreen, Hydrated, Voice-only
7. Privacy Policy & Terms of Service endpoints
"""
import base64
import hashlib
import json
import os
import sys
import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))

from hearth.alexaplus_addon import alexaplus_engine
import server


@pytest.fixture
def client():
    app = server.mcp.streamable_http_app()
    return TestClient(app)


def _get_client(client=None):
    if client is not None:
        return client
    app = server.mcp.streamable_http_app()
    return TestClient(app)


def test_rfc9728_protected_resource_metadata(client=None):
    """Verify RFC 9728 Protected Resource Metadata document at /.well-known/oauth-protected-resource."""
    c = _get_client(client)
    resp = c.get("/.well-known/oauth-protected-resource")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    
    assert data["resource"].endswith("/mcp")
    assert "mcp:service" in data["scopes_supported"]
    assert "mcp:tools" in data["scopes_supported"]
    assert "mcp:resources" in data["scopes_supported"]
    assert "header" in data["bearer_methods_supported"]
    assert data["protocol_version"] == "2025-11-25"
    assert data["transport"] == "streamable-http"
    print("✓ RFC 9728 Protected Resource Metadata verified")


def test_oauth_authorization_server_metadata(client=None):
    """Verify OAuth 2.1 Authorization Server Metadata document at /.well-known/oauth-authorization-server."""
    c = _get_client(client)
    resp = c.get("/.well-known/oauth-authorization-server")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    
    assert data["authorization_endpoint"].endswith("/oauth/authorize")
    assert data["token_endpoint"].endswith("/oauth/token")
    assert "S256" in data["code_challenge_methods_supported"]
    assert "authorization_code" in data["grant_types_supported"]
    assert "client_credentials" in data["grant_types_supported"]
    assert "refresh_token" in data["grant_types_supported"]
    print("✓ OAuth 2.1 Authorization Server Metadata verified")


def test_tier1_client_credentials_grant(client=None):
    """Verify Tier 1 Machine-to-Machine Client Credentials Grant for service discovery."""
    c = _get_client(client)
    resp = c.post("/oauth/token", json={
        "grant_type": "client_credentials",
        "client_id": "alexa-plus-crawler",
        "client_secret": "test_sec_9941"
    })
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["token_type"] == "Bearer"
    assert data["scope"] == "mcp:service"
    assert data["access_token"].startswith("mcp_svc_")
    assert data["expires_in"] == 3600
    print("✓ Tier 1 Client Credentials (M2M) Grant verified")


def test_tier2_pkce_authorization_code_grant(client=None):
    """Verify Tier 2 User-Level Account Linking with PKCE S256 verification."""
    c = _get_client(client)
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk_TEST_SUITE"
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest()).decode("utf-8").rstrip("=")
    
    # 1. Authorize step
    resp = c.get(f"/oauth/authorize?client_id=alexa-hub&code_challenge={challenge}&code_challenge_method=S256&scope=mcp:tools+mcp:resources")
    assert resp.status_code == 200
    auth_data = resp.json()
    code = auth_data["code"]
    assert code.startswith("authcode_")
    
    # 2. Token exchange step with code_verifier
    resp2 = c.post("/oauth/token", json={
        "grant_type": "authorization_code",
        "code": code,
        "code_verifier": verifier,
        "client_id": "alexa-hub"
    })
    assert resp2.status_code == 200
    data = resp2.json()
    
    assert data["token_type"] == "Bearer"
    assert "mcp:tools" in data["scope"]
    assert "mcp:resources" in data["scope"]
    assert data["access_token"].startswith("Atza|")
    assert data["refresh_token"].startswith("Atzr|")
    
    # 3. Token refresh step
    resp3 = c.post("/oauth/token", json={
        "grant_type": "refresh_token",
        "refresh_token": data["refresh_token"]
    })
    assert resp3.status_code == 200
    ref_data = resp3.json()
    assert ref_data["token_type"] == "Bearer"
    assert ref_data["access_token"].startswith("Atza|")
    print("✓ Tier 2 PKCE S256 Authorization Code & Refresh Token Grants verified")


def test_addon_manifest(client=None):
    """Verify official addon.json manifest structure."""
    c = _get_client(client)
    resp = c.get("/addon.json")
    assert resp.status_code == 200
    manifest = resp.json()
    
    assert "addon" in manifest
    assert manifest["addon"]["id"] == "amzn1.ask.addon.hearth.operations"
    assert "inline" in manifest["display"]["supportedModes"]
    assert "fullscreen" in manifest["display"]["supportedModes"]
    assert manifest["runtime"]["protocolVersion"] == "2025-11-25"
    assert manifest["authentication"]["type"] == "oauth2.1"
    print("✓ Alexa+ Add-on manifest (addon.json) verified")


def test_display_modes_and_voice_sanitization():
    """Verify display mode formatting and voice-only text sanitization for headless devices."""
    dirty_text = "| Metric | Value |\n|---|---|\n| Climate | **21.5°C** |\n[View Dashboard](http://localhost/view) #heading"
    clean_voice = alexaplus_engine.sanitize_voice_output(dirty_text)
    
    assert "|" not in clean_voice, "Pipes must be stripped for voice"
    assert "[" not in clean_voice and "]" not in clean_voice, "Markdown brackets stripped"
    assert "#" not in clean_voice and "**" not in clean_voice
    
    # Display response with MCP Apps resourceUri
    resp = alexaplus_engine.format_display_response(
        content={"temperature": 21.5, "mode": "eco"},
        display_mode="fullscreen",
        resource_uri="ui://hearth/views/energy_mesh",
        voice_summary="The living room climate is set to 21.5 degrees Celsius in eco mode."
    )
    assert resp["display_mode"] == "fullscreen"
    assert resp["resourceUri"] == "ui://hearth/views/energy_mesh"
    assert resp["speech"]["type"] == "PlainText"
    assert "21.5 degrees" in resp["speech"]["text"]
    print("✓ Display Modes and Voice Sanitization verified")


def test_privacy_and_terms(client=None):
    """Verify legal policy endpoints required by Alexa+ certification."""
    c = _get_client(client)
    resp_priv = c.get("/privacy")
    assert resp_priv.status_code == 200
    priv_data = resp_priv.json()
    assert "Privacy Policy" in priv_data["name"]
    
    resp_terms = c.get("/terms")
    assert resp_terms.status_code == 200
    terms_data = resp_terms.json()
    assert "Terms of Service" in terms_data["name"]
    print("✓ Privacy Policy and Terms of Service endpoints verified")


if __name__ == "__main__":
    print("\n=======================================================")
    print("  RUNNING ALEXA+ ADD-ON & OAUTH 2.1 COMPLIANCE TESTS  ")
    print("=======================================================")
    test_rfc9728_protected_resource_metadata()
    test_oauth_authorization_server_metadata()
    test_tier1_client_credentials_grant()
    test_tier2_pkce_authorization_code_grant()
    test_addon_manifest()
    test_display_modes_and_voice_sanitization()
    test_privacy_and_terms()
    print("\n=======================================================")
    print("🏆 ALL 7 ALEXA+ ADD-ON COMPLIANCE TESTS PASSED (100%)!")
    print("=======================================================\n")
