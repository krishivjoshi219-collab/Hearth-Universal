"""Proof Engine contracts: receipts derive from real recorded events, chain
with SHA-256, re-derive from their own fields, and a hand-edit is provably
detectable by the exact same verification.

The suite runs against a throwaway state dir (see conftest), so these tests
seed their own audit events first — the engine must work on any real ledger.
"""
import os
import sys

import pytest
from starlette.testclient import TestClient

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "mcp-server"))

import server  # noqa: E402

from hearth import audit, receipts  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(server.mcp.streamable_http_app())


@pytest.fixture(scope="module", autouse=True)
def seeded_events():
    """Real ledger events for the engine to receipt: a VPP settlement and two
    executed approvals (one with a money-bearing order receipt)."""
    audit.append("sim", "microgrid_dispatch_settled", {
        "trade_id": "vpp_test_unit", "allocated_kw": 3.8, "price": 0.18,
        "community_dividend": 1.71,
    })
    audit.append("sim", "execution_applied", {
        "id": "p_test_order",
        "execution": {"applied": True, "at": 1_700_000_000,
                      "note": "order staged for 'Test order' at $12.34 (checkout simulated)",
                      "receipt_code": "RC-TEST",
                      "qr_payload": "hearth://receipt/RC-TEST?total=12.34"},
    })
    audit.append("sim", "execution_applied", {
        "id": "p_test_treaty",
        "execution": {"applied": True, "at": 1_700_000_100,
                      "note": "approved household_treaty_ratification recorded"},
    })


def test_rebuild_is_idempotent_and_chain_verifies():
    added = receipts.rebuild()
    assert added >= 3  # at least the three seeded events
    assert receipts.rebuild() == 0  # idempotent: nothing new the second time
    led = receipts.ledger()
    assert led["receipts_count"] >= 3
    assert led["chain_valid"] is True
    assert len(led["chain_head"]) == 64
    assert led["verified_usd"] == round(led["saved_usd"] + led["earned_usd"], 2)
    assert led["by_kind"].get("vpp_dispatch", 0) >= 1


def test_dispatch_events_become_receipts():
    dispatches = 0
    with open(receipts._audit_path()) as fh:
        for line in fh:
            if "microgrid_dispatch_settled" in line:
                dispatches += 1
    vpp = [r for r in receipts._load() if r.get("kind") == "vpp_dispatch"]
    assert len(vpp) == dispatches
    sample = vpp[-1]
    assert sample["money"]["earned_usd"] > 0
    assert "kW" in sample["claim"] and "$" in sample["claim"]
    assert sample["source_events"] and len(sample["source_events"][0]) == 64
    # the money-bearing order also produced an order receipt
    orders = [r for r in receipts._load() if r.get("kind") == "order_staged"]
    assert orders and orders[-1]["money"]["spent_usd"] == 12.34


def test_verify_recomputes_matching_hash():
    r = receipts._load()[-1]
    out = receipts.verify_receipt(r["receipt_id"], tamper=False)
    assert out is not None
    assert out["ok"] is True
    assert out["match"] is True
    assert out["recomputed_hash"] == out["stated_hash"]
    assert out["chain_valid"] is True


def test_tamper_fails_verification_and_names_the_field():
    r = receipts._load()[-1]
    out = receipts.verify_receipt(r["receipt_id"], tamper=True)
    assert out is not None
    assert out["ok"] is False
    t = out["tamper"]
    assert t["detected"] is True
    assert t["match"] is False
    assert t["field"].startswith("money.") or t["field"] == "claim"
    assert t["recomputed_hash"] != out["stated_hash"]
    # the stored receipt itself is untouched
    again = receipts.verify_receipt(r["receipt_id"], tamper=False)
    assert again["ok"] is True


def test_record_tool_applied_extends_the_chain_then_cleanup():
    before = len(receipts._load())
    rec = receipts.record_tool_applied(
        "hearth_forge_test_tool",
        {"schedule_hour": 22},
        {"status": "scheduled", "applied_hour": 22, "savings_usd": 3.2, "eco_mode": True},
        "unit-test-source-hash",
    )
    after = receipts._load()
    assert len(after) == before + 1
    assert rec["money"]["saved_usd"] == 3.2
    assert "saved" in rec["claim"]
    assert rec["prev_receipt_hash"] == (after[-2]["receipt_hash"] if before else "GENESIS")
    assert receipts.chain_valid() is True
    # cleanup: this test's receipt must not linger
    path = receipts._receipts_path()
    lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
    path.write_text("\n".join(lines[:-1]) + "\n")
    assert len(receipts._load()) == before
    assert receipts.chain_valid() is True


def test_http_receipts_endpoint(client):
    res = client.get("/api/receipts?limit=5")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["ok"] is True
    assert isinstance(data["receipts"], list) and 1 <= len(data["receipts"]) <= 5
    led = data["ledger"]
    assert led["chain_valid"] is True
    assert data["receipts_count"] == led["receipts_count"]
    top = data["receipts"][0]
    for key in ("receipt_id", "kind", "claim", "money", "receipt_hash",
                "prev_receipt_hash", "source_events"):
        assert key in top


def test_http_verify_and_tamper_endpoints(client):
    rid = client.get("/api/receipts?limit=1").json()["receipts"][0]["receipt_id"]
    ok = client.post("/api/receipts/verify", json={"receipt_id": rid}).json()
    assert ok["ok"] is True and ok["match"] is True
    bad = client.post("/api/receipts/verify",
                      json={"receipt_id": rid, "tamper": True}).json()
    assert bad["ok"] is False
    assert bad["tamper"]["detected"] is True
    assert bad["tamper"]["recomputed_hash"] != bad["stated_hash"]
    missing = client.post("/api/receipts/verify", json={"receipt_id": "rcpt_nope"})
    assert missing.status_code == 404
