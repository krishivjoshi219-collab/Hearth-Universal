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
import urllib.request
import urllib.error
from hearth.alexaplus_addon import alexaplus_engine

BASE_URL = "http://localhost:8787"


def test_rfc9728_protected_resource_metadata():
    """Verify RFC 9728 Protected Resource Metadata document at /.well-known/oauth-protected-resource."""
    url = f"{BASE_URL}/.well-known/oauth-protected-resource"
    resp = urllib.request.urlopen(url)
    assert resp.status == 200, f"Expected 200, got {resp.status}"
    data = json.loads(resp.read().decode())
    
    assert data["resource"].endswith("/mcp")
    assert "mcp:service" in data["scopes_supported"]
    assert "mcp:tools" in data["scopes_supported"]
    assert "mcp:resources" in data["scopes_supported"]
    assert "header" in data["bearer_methods_supported"]
    assert data["protocol_version"] == "2025-11-25"
    assert data["transport"] == "streamable-http"
    print("✓ RFC 9728 Protected Resource Metadata verified")


def test_oauth_authorization_server_metadata():
    """Verify OAuth 2.1 Authorization Server Metadata document at /.well-known/oauth-authorization-server."""
    url = f"{BASE_URL}/.well-known/oauth-authorization-server"
    resp = urllib.request.urlopen(url)
    assert resp.status == 200, f"Expected 200, got {resp.status}"
    data = json.loads(resp.read().decode())
    
    assert data["authorization_endpoint"].endswith("/oauth/authorize")
    assert data["token_endpoint"].endswith("/oauth/token")
    assert "S256" in data["code_challenge_methods_supported"]
    assert "authorization_code" in data["grant_types_supported"]
    assert "client_credentials" in data["grant_types_supported"]
    assert "refresh_token" in data["grant_types_supported"]
    print("✓ OAuth 2.1 Authorization Server Metadata verified")


def test_tier1_client_credentials_grant():
    """Verify Tier 1 Machine-to-Machine Client Credentials Grant for service discovery."""
    url = f"{BASE_URL}/oauth/token"
    payload = json.dumps({
        "grant_type": "client_credentials",
        "client_id": "alexa-plus-crawler",
        "client_secret": "test_sec_9941"
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    assert resp.status == 200
    data = json.loads(resp.read().decode())
    
    assert data["token_type"] == "Bearer"
    assert data["scope"] == "mcp:service"
    assert data["access_token"].startswith("mcp_svc_")
    assert data["expires_in"] == 3600
    print("✓ Tier 1 Client Credentials (M2M) Grant verified")


def test_tier2_pkce_authorization_code_grant():
    """Verify Tier 2 User-Level Account Linking with PKCE S256 verification."""
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk_TEST_SUITE"
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest()).decode("utf-8").rstrip("=")
    
    # 1. Authorize step
    auth_url = f"{BASE_URL}/oauth/authorize?client_id=alexa-hub&code_challenge={challenge}&code_challenge_method=S256&scope=mcp:tools+mcp:resources"
    resp = urllib.request.urlopen(auth_url)
    assert resp.status == 200
    auth_data = json.loads(resp.read().decode())
    code = auth_data["code"]
    assert code.startswith("authcode_")
    
    # 2. Token exchange step with code_verifier
    token_url = f"{BASE_URL}/oauth/token"
    payload = json.dumps({
        "grant_type": "authorization_code",
        "code": code,
        "code_verifier": verifier,
        "client_id": "alexa-hub"
    }).encode()
    req = urllib.request.Request(token_url, data=payload, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    assert resp.status == 200
    data = json.loads(resp.read().decode())
    
    assert data["token_type"] == "Bearer"
    assert "mcp:tools" in data["scope"]
    assert "mcp:resources" in data["scope"]
    assert data["access_token"].startswith("Atza|")
    assert data["refresh_token"].startswith("Atzr|")
    
    # 3. Token refresh step
    ref_payload = json.dumps({
        "grant_type": "refresh_token",
        "refresh_token": data["refresh_token"]
    }).encode()
    req_ref = urllib.request.Request(token_url, data=ref_payload, headers={"Content-Type": "application/json"})
    resp_ref = urllib.request.urlopen(req_ref)
    assert resp_ref.status == 200
    ref_data = json.loads(resp_ref.read().decode())
    assert ref_data["token_type"] == "Bearer"
    assert ref_data["access_token"].startswith("Atza|")
    print("✓ Tier 2 PKCE S256 Authorization Code & Refresh Token Grants verified")


def test_addon_manifest():
    """Verify official addon.json manifest structure."""
    url = f"{BASE_URL}/addon.json"
    resp = urllib.request.urlopen(url)
    assert resp.status == 200
    manifest = json.loads(resp.read().decode())
    
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


def test_privacy_and_terms():
    """Verify legal policy endpoints required by Alexa+ certification."""
    resp_priv = urllib.request.urlopen(f"{BASE_URL}/privacy")
    assert resp_priv.status == 200
    priv_data = json.loads(resp_priv.read().decode())
    assert "Privacy Policy" in priv_data["name"]
    
    resp_terms = urllib.request.urlopen(f"{BASE_URL}/terms")
    assert resp_terms.status == 200
    terms_data = json.loads(resp_terms.read().decode())
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
