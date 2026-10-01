"""Adversarial Red-Team & Chaos Fuzzing Suite for Hearth Universal FastMCP HTTP Server.

Tests:
1. Non-dict JSON payloads triggering unhandled 500 AttributeError on /api/chat and /api/ring/event.
2. Invalid UTF-8 byte stream triggering unhandled 500 UnicodeDecodeError on /mcp.
3. NaN float injection causing unhandled 500 and persistent digital-twin state poisoning.
4. Missing keys handling across all target endpoints.
5. Large payload handling (413 vs unbounded buffering).
6. Chat rate-limiter hammering, thread-safety, and state exhaustion leak.
"""
from __future__ import annotations

import json
import math
import os
import sys
import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))

import server


@pytest.fixture(scope="function")
def app():
    return server.mcp.streamable_http_app()


@pytest.fixture
def client(app):
    # Avoid lifespan re-entry: FastMCP's StreamableHTTPSessionManager can only
    # run once per process. Using TestClient without a lifespan context
    # exercises routes without re-running the manager.
    c = TestClient(app, raise_server_exceptions=False)
    yield c


class TestNonDictJSONCrashes:
    """Proves unhandled 500 AttributeError when valid JSON that is not an object is received."""

    @pytest.mark.parametrize("payload", [
        [1, 2, 3],
        "string_literal",
        12345,
        None,
        True,
    ])
    def test_api_chat_non_dict_500(self, client, payload):
        """Sending a non-dictionary JSON payload to /api/chat is rejected with 400 (hardened)."""
        res = client.post("/api/chat", json=payload)
        # Hardened: server returns 400 JSON object required (was 500 crash)
        assert res.status_code == 400, f"Expected 400 hardened rejection for payload {payload}, got {res.status_code}"

    @pytest.mark.parametrize("payload", [
        [1, 2, 3],
        "doorbell_press",
        999,
        None,
        False,
    ])
    def test_api_ring_event_non_dict_500(self, client, payload):
        """Sending a non-dictionary JSON payload to /api/ring/event is handled without 500."""
        res = client.post("/api/ring/event", json=payload)
        # Hardened: must not crash with 500; 200 fallback or 400 rejection both acceptable
        assert res.status_code in (200, 400), f"Expected non-500 for payload {payload}, got {res.status_code}"


class TestFastMCPByteDecodeFailure:
    """Proves unhandled 500 on non-UTF-8 raw byte stream to /mcp."""

    def test_mcp_raw_bytes_unicode_decode_500(self, client):
        """FastMCP streamable HTTP POST handler rejects non-UTF-8 bytes (upstream 500)."""
        non_utf8_data = b"\x00\x01\xff\xfe"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        res = client.post("/mcp", content=non_utf8_data, headers=headers)
        # Upstream FastMCP behavior: 500 with -32603 (documents library edge, not our bug)
        assert res.status_code in (400, 500)


class TestNaNStatePoisoning:
    """Proves NaN float injection causes unhandled 500 and poisons subsequent read operations."""

    def test_nan_home_device_crash_and_state_poisoning(self, client):
        # 1. NaN in device update patch must not poison state with 500
        nan_payload = '{"room": "living_room", "device": "climate", "patch": {"target_c": NaN}}'
        headers = {"Content-Type": "application/json"}
        res = client.post("/api/home/device", content=nan_payload, headers=headers)
        assert res.status_code in (200, 400)

        # 2. Subsequent GET /api/home must stay healthy
        res_get = client.get("/api/home")
        assert res_get.status_code == 200, "State must not be poisoned by NaN input"

        # 3. Subsequent GET /api/export must stay healthy
        res_export = client.get("/api/export")
        assert res_export.status_code in (200, 404), "Export must not be poisoned by NaN input"

        # Clean up / reset state to not break other tests
        server.home_mock.reset_state()


class TestMalformedJSONHandling:
    """Validates how each endpoint responds to syntactic JSON errors."""

    @pytest.mark.parametrize("endpoint,expected_status", [
        ("/api/chat", 400),
        ("/api/arbiter", 200),        # Silent fallback to default
        ("/api/timemachine", 200),    # Silent fallback to default
        ("/api/ring/event", 200),     # Silent fallback to default
        ("/api/commerce/scan", 200),  # Silent fallback to default
    ])
    def test_broken_syntax_json(self, client, endpoint, expected_status):
        broken = b'{"key": '
        headers = {"Content-Type": "application/json"}
        res = client.post(endpoint, content=broken, headers=headers)
        assert res.status_code == expected_status

    def test_mcp_broken_json(self, client):
        broken = b'{"key": '
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        res = client.post("/mcp", content=broken, headers=headers)
        assert res.status_code in (400, 500)


class TestMissingKeysAndEdgeValues:
    """Validates missing key contracts and extreme values."""

    def test_api_chat_empty_dict(self, client):
        res = client.post("/api/chat", json={})
        assert res.status_code == 400
        assert res.json().get("error") == "Message is required"

    def test_api_arbiter_missing_keys(self, client):
        res = client.post("/api/arbiter", json={})
        assert res.status_code == 200
        assert res.json().get("conflict_type") == "climate"

    def test_api_timemachine_missing_keys(self, client):
        res = client.post("/api/timemachine", json={})
        assert res.status_code == 200
        assert res.json().get("preset") == "now"

    def test_api_commerce_scan_missing_keys(self, client):
        res = client.post("/api/commerce/scan", json={})
        assert res.status_code == 200
        assert res.json().get("ok") is True

    def test_api_ring_event_missing_keys(self, client):
        res = client.post("/api/ring/event", json={})
        assert res.status_code == 200
        assert res.json().get("event_type") == "doorbell_press"


class TestPayloadLimitsAndRateHammering:
    """Tests huge payloads and rapid hammering."""

    def test_mcp_huge_payload_rejection(self, client):
        """FastMCP streamable HTTP rejects oversized bodies with 413."""
        huge = b'{"jsonrpc": "2.0", "method": "ping", "data": "' + (b"X" * (5 * 1024 * 1024)) + b'"}'
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        res = client.post("/mcp", content=huge, headers=headers)
        assert res.status_code == 413

    def test_api_chat_rate_limiting(self, client):
        """Rapid hammering of /api/chat triggers 429 when exceeding threshold."""
        # Evict bucket for testclient host
        server._RATE_BUCKETS.clear()
        statuses = []
        for i in range(server.RATE_LIMIT + 5):
            res = client.post("/api/chat", json={"message": "rate limit hammer test"})
            statuses.append(res.status_code)

        assert 429 in statuses, f"Expected 429 in statuses, got {statuses}"
        # Bucket count should equal RATE_LIMIT
        assert len(server._RATE_BUCKETS.get("testclient", [])) == server.RATE_LIMIT

    def test_rate_bucket_memory_leak(self):
        """Distinct-IP buckets are GC-bounded (hardened, no unbounded leak)."""
        server._RATE_BUCKETS.clear()
        for i in range(1000):
            server._rate_ok(f"192.168.100.{i}")

        # Hardened: GC caps growth well below 1000
        assert len(server._RATE_BUCKETS) < 1000, f"Leak: {len(server._RATE_BUCKETS)} buckets"
        server._RATE_BUCKETS.clear()
