"""Track B: Amazon Prime late-delivery clawback.

Covers the SLA-miss rule, idempotent claim staging through the Approval Tray,
the hash-chained ``credit_claimed`` receipt, withdrawal/restage via undo, and
the Sentinel child guardrail on the planner path.
"""
import pytest

from hearth import delivery_clawback, planner, proposals, receipts

LATE_ORDER = "113-8675309-2401984"
ONTIME_ORDER = "114-2201437-7783052"
TRANSIT_ORDER = "112-9051749-3922417"


@pytest.fixture(autouse=True)
def _clean_claim_state():
    proposals.clear_proposals()
    delivery_clawback.clear_claims()
    yield
    proposals.clear_proposals()
    delivery_clawback.clear_claims()


def test_scan_flags_the_late_delivery_only():
    s = delivery_clawback.scan()
    assert s["ok"] is True and s["sandbox"] is True
    by_id = {d["order_id"]: d for d in s["deliveries"]}
    late = by_id[LATE_ORDER]
    assert late["delay_minutes"] == 152
    assert late["delay_label"] == "2h 32m"
    assert late["late"] is True and late["eligible"] is True and late["claimed"] is False
    assert by_id[ONTIME_ORDER]["late"] is False
    assert by_id[TRANSIT_ORDER].get("status") == "in_transit"
    assert LATE_ORDER in s["claimable_order_ids"]
    assert s["credit_usd"] == 5.0


def test_credit_threshold_is_two_hours():
    assert delivery_clawback.qualifies(119) is False
    assert delivery_clawback.qualifies(120) is True
    assert delivery_clawback.qualifies(152) is True
    assert delivery_clawback.qualifies(None) is False
    assert delivery_clawback.qualifies("nonsense") is False


def test_stage_claim_builds_gated_proposal_without_yr_convention():
    out = delivery_clawback.stage_claim()
    assert out["ok"] is True and out["already"] is False
    prop = out["proposal"]
    assert prop["kind"] == "delivery_credit_claim"
    assert prop["status"] == "pending"
    assert prop["risk_level"] == "low"
    assert "$5.00" in prop["title"] and "2h 32m" in prop["title"]
    # A one-off credit must never wear the recurring "/yr" money convention.
    assert prop["cost_delta_yr"] == 0.0
    assert "/yr" not in prop["title"] and "/yr" not in prop["reasons"] and "/yr" not in prop["diff"]
    meta = prop["meta"]
    assert meta["order_id"] == LATE_ORDER
    assert meta["credit_usd"] == 5.0
    assert meta["delay_minutes"] == 152
    assert meta["tracking_number"] == "TBA3094827731"
    assert [p["id"] for p in proposals.list_proposals("pending")] == [prop["id"]]


def test_stage_claim_is_idempotent_per_order():
    first = delivery_clawback.stage_claim()
    again = delivery_clawback.stage_claim()
    assert again["ok"] is True and again["already"] is True
    assert again["proposal"]["id"] == first["proposal"]["id"]
    by_order = delivery_clawback.stage_claim(order_id=LATE_ORDER)
    assert by_order["already"] is True
    assert len(proposals.list_proposals("pending")) == 1
    claims = delivery_clawback.list_claims()
    assert len(claims) == 1
    assert claims[0]["status"] == "pending" and claims[0]["order_id"] == LATE_ORDER


def test_on_time_and_in_transit_deliveries_are_refused():
    on_time = delivery_clawback.stage_claim(order_id=ONTIME_ORDER)
    assert on_time["ok"] is False and "on time" in on_time["error"]
    in_transit = delivery_clawback.stage_claim(order_id=TRANSIT_ORDER)
    assert in_transit["ok"] is False and "in transit" in in_transit["error"]
    assert proposals.list_proposals("pending") == []


def test_approve_mints_hash_chained_credit_receipt():
    out = delivery_clawback.stage_claim()
    pid = out["proposal"]["id"]
    decided = proposals.decide(pid, True)
    ex = decided["execution"]
    assert ex["applied"] is True
    assert ex["credit_usd"] == 5.0
    assert ex["receipt_code"].startswith("HEARTH-RC-AMZ-CREDIT-")
    assert ex["order_id"] == LATE_ORDER

    assert receipts.rebuild() >= 1
    rs = [r for r in receipts.list_receipts(100)["receipts"]
          if r.get("kind") == "credit_claimed" and (r.get("settled") or {}).get("credit_usd") == 5.0]
    assert rs, "approval must mint a credit_claimed receipt"
    r = rs[0]
    assert r["money"]["earned_usd"] == 5.0
    assert "+$5.00" in r["claim"]
    assert r["receipt_hash"] and r["prev_receipt_hash"]
    assert r["source_events"]

    v = receipts.verify_receipt(r["receipt_id"])
    assert v["ok"] is True and v["match"] is True and v["chain_valid"] is True
    t = receipts.verify_receipt(r["receipt_id"], tamper=True)
    assert t["ok"] is False and t["tamper"]["detected"] is True

    ledger = receipts.list_receipts(100)["ledger"]
    assert ledger["earned_usd"] >= 5.0


def test_undo_withdraws_claim_and_restage_is_allowed():
    out = delivery_clawback.stage_claim()
    pid = out["proposal"]["id"]
    proposals.decide(pid, True)
    undone = proposals.undo(pid)
    assert undone["ok"] is True
    assert "withdrawn" in undone["note"]

    s = delivery_clawback.scan()
    late = next(d for d in s["deliveries"] if d["order_id"] == LATE_ORDER)
    assert late["claimed"] is False
    assert LATE_ORDER in s["claimable_order_ids"]

    fresh = delivery_clawback.stage_claim()
    assert fresh["ok"] is True and fresh["already"] is False
    assert fresh["proposal"]["id"] != pid


def test_reject_then_restage_is_allowed():
    out = delivery_clawback.stage_claim()
    pid = out["proposal"]["id"]
    proposals.decide(pid, False)
    fresh = delivery_clawback.stage_claim()
    assert fresh["ok"] is True and fresh["already"] is False
    assert fresh["proposal"]["id"] != pid


def test_child_persona_cannot_stage_claim(monkeypatch):
    monkeypatch.setenv("HEARTH_ACTIVE_PERSONA", "child")
    res = planner.plan("did anything slip with my package?")
    # Whatever the guardrail path, nothing may be staged or filed for a child.
    assert proposals.list_proposals("pending") == []
    assert delivery_clawback.list_claims() == []
    assert res["proposals_created"] == []
    assert "leo" in res["draft"].lower() or "blocked" in res["draft"].lower()


def test_planner_route_stages_claim_for_adult(monkeypatch):
    monkeypatch.setenv("HEARTH_ACTIVE_PERSONA", "admin")
    res = planner.plan("did anything slip with my delivery?")
    assert res["intent"] == "DELIVERY_CLAWBACK"
    assert "courtesy credit" in res["draft"].lower()
    assert len(res["proposals_created"]) == 1
    pending = proposals.list_proposals("pending")
    assert len(pending) == 1 and pending[0]["kind"] == "delivery_credit_claim"
    # The planner path must register the same idempotence ledger.
    assert delivery_clawback.list_claims()[0]["proposal_id"] == pending[0]["id"]
