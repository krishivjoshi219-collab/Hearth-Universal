"""Regression tests from the adversarial code-critic pass (2026-10-19).

Covers:
- P0: front-door unlock via /api/devices patch merge (bypass, no proposal)
- P1: child profile staging/approving money via direct REST (the planner path
  was already blocked; REST was not)
- P1: clawback idempotency past the proposal list cap (get_proposal used to
  read only the newest LIST_DEFAULT_LIMIT items, so an older claim read
  "missing" and a second $5 claim could be staged)
"""
from __future__ import annotations

import json
import os
import sys

import pytest
from starlette.testclient import TestClient

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "mcp-server"))

import server  # noqa: E402

from hearth import atomic, delivery_clawback, proposals  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(server.mcp.streamable_http_app())


@pytest.fixture(autouse=True)
def _clean_claim_state():
    proposals.clear_proposals()
    delivery_clawback.clear_claims()
    yield
    proposals.clear_proposals()
    delivery_clawback.clear_claims()


def test_device_patch_cannot_unlock_the_front_door(client):
    r = client.post(
        "/api/devices",
        json={"room": "entryway", "device": "lock", "patch": {"front_door": "unlocked"}},
    )
    assert r.status_code == 403, r.text
    body = r.json()
    assert body.get("approval_required") is True
    assert body.get("ok") is False


def test_child_profile_cannot_stage_clawback_via_rest(client):
    client.post("/api/persona", json={"id": "child"})
    try:
        r = client.post("/api/commerce/delivery-clawback", json={})
        assert r.status_code == 403, r.text
        assert r.json().get("blocked") is True
    finally:
        client.post("/api/persona", json={"id": "admin"})


def test_child_profile_cannot_approve_a_staged_claim_via_rest(client):
    staged = client.post("/api/commerce/delivery-clawback", json={}).json()
    pid = (staged.get("proposal") or {}).get("id")
    assert pid, f"expected a staged claim, got: {staged}"
    client.post("/api/persona", json={"id": "child"})
    try:
        r = client.post(f"/api/proposals/{pid}/decide", json={"approved": True})
        assert r.status_code == 403, r.text
        assert r.json().get("blocked") is True
    finally:
        client.post("/api/persona", json={"id": "admin"})


def test_clawback_idempotency_beyond_the_proposal_cap(client):
    first = client.post("/api/commerce/delivery-clawback", json={}).json()
    assert first.get("ok") is True, first

    # Bury the staged claim under more proposals than LIST_DEFAULT_LIMIT, so a
    # capped lookup reads it as "missing" and re-stages (the critic's repro).
    p = proposals._path()
    items = json.loads(p.read_text(encoding="utf-8"))
    filler = [
        {"id": f"prop_fill_{i}", "status": "rejected", "title": "filler proposal"}
        for i in range(proposals.LIST_DEFAULT_LIMIT + 20)
    ]
    atomic.atomic_write_text(p, json.dumps(items + filler))

    second = client.post("/api/commerce/delivery-clawback", json={}).json()
    assert second.get("ok") is True, second
    assert second.get("already") is True, (
        "second stage must be idempotent even when the claim is older than the "
        f"list cap: {json.dumps(second)[:300]}"
    )


def test_undo_is_refused_while_execution_is_in_flight(monkeypatch):
    """decide() executes outside its lock; undo() must not reverse an action
    whose side effect is still landing (adversarial pass, P1#5)."""
    import threading

    staged = proposals.propose(
        kind="demo_action", title="race demo", reasons="critic regression harness"
    )
    item = staged.get("proposal") or staged
    pid = item.get("id")
    assert pid, staged

    started = threading.Event()
    release = threading.Event()

    def slow_execute(target):
        started.set()
        assert release.wait(timeout=10)
        return {"applied": True, "at": 1, "note": "slow action"}

    monkeypatch.setattr(proposals, "_execute_approved_action", slow_execute)

    decided = {}

    def _run_decide():
        decided["out"] = proposals.decide(pid, True)

    worker = threading.Thread(target=_run_decide)
    worker.start()
    assert started.wait(timeout=5), "execution never started"

    raced = proposals.undo(pid)
    assert raced.get("ok") is False, raced
    assert "still" in str(raced.get("error", "")).lower(), raced

    release.set()
    worker.join(timeout=10)
    assert decided.get("out", {}).get("status") == "approved", decided

    after = proposals.undo(pid)
    assert after.get("ok") is True, after
