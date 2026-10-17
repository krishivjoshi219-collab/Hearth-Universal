"""HTTP hardening contracts: request ids, cache policy, and 304s.

These are production behaviours, not cosmetics — a regression here breaks log
correlation, leaks household state into shared caches, or silently turns every
static asset into a full re-download.
"""
import os
import sys

import pytest
from starlette.testclient import TestClient

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "mcp-server"))

import server  # noqa: E402
from http_hardening import _etag_matches  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(server.mcp.streamable_http_app())


def test_every_response_carries_a_request_id(client):
    first = client.get("/health")
    second = client.get("/health")
    assert first.status_code == 200
    assert first.headers.get("x-request-id")
    assert first.headers["x-request-id"] != second.headers["x-request-id"]
    assert first.headers.get("x-content-type-options") == "nosniff"


def test_api_responses_are_never_cached(client):
    res = client.get("/api/metrics")
    assert res.status_code == 200
    assert res.headers.get("cache-control") == "no-store"


def test_static_assets_revalidate_with_etag(client):
    path = "/web2/css/cockpit.css"
    first = client.get(path)
    assert first.status_code == 200
    assert first.headers.get("cache-control") == "no-cache"
    etag = first.headers.get("etag")
    assert etag

    second = client.get(path, headers={"If-None-Match": etag})
    assert second.status_code == 304
    assert second.content == b""
    assert second.headers.get("x-request-id")


def test_etag_matching_rules():
    assert _etag_matches('"abc"', '"abc"')
    assert _etag_matches("W/\"abc\"", '"abc"')
    assert _etag_matches('"other", "abc"', '"abc"')
    assert _etag_matches("*", '"abc"')
    assert not _etag_matches('"other"', '"abc"')
    assert not _etag_matches("", '"abc"')
