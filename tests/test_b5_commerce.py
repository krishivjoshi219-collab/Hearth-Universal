"""B5 purchasing-differentiator tests: depletion math, bundle match, propose-gating."""
import copy

import pytest

from hearth import commerce, delivery, proposals


@pytest.fixture(autouse=True)
def _restore_commerce_state():
    snap = copy.deepcopy(commerce.HOUSEHOLD_ESSENTIALS)
    slot = commerce._SCHEDULED_SLOT_ID
    yield
    commerce.HOUSEHOLD_ESSENTIALS.clear()
    commerce.HOUSEHOLD_ESSENTIALS.extend(snap)
    commerce._SCHEDULED_SLOT_ID = slot
    proposals.clear_proposals()


def test_b5_depletion_velocity_computed():
    item = {"id": "item_coffee", "level_pct": 15}
    days = commerce.compute_days_until_empty(item)
    assert days == round(15 / commerce.DAILY_CONSUMPTION_RATE_PCT["item_coffee"], 1)
    assert days == 2.5
    # Forecast sorted + computed flags + sandbox marking.
    fc = commerce.get_depletion_forecast()
    days_list = [f["days_until_empty"] for f in fc]
    assert days_list == sorted(days_list)
    assert all(f.get("depletion_computed") for f in fc)
    assert all(f.get("sandbox_fixture") for f in fc)
    assert fc[0]["days_until_empty"] < 5.0


def test_b5_bundle_15pct_match():
    m = commerce.match_bundle_discount(item_ids=["item_coffee", "item_detergent"])
    assert m["ok"] is True
    assert m["discount_pct"] == 15.0
    assert m["sandbox"] is True
    for line in m["items"]:
        assert line["discount_pct"] == 15.0
        assert line["matched_price"] == round(line["regular_price"] * 0.85, 2)
    # Full optimizer still unlocks 5+ tier and exposes 15% baseline.
    b = commerce.optimize_bundles(auto_fill_tier=True, target_tier_items=5)
    assert b["tier_unlocked"] is True
    assert b["pricing"]["standard_15pct_savings"] > 0
    assert b["item_count"] >= 5


def test_b5_cart_propose_gating_no_direct_execution():
    proposals.clear_proposals()
    # Direct execution must fail closed.
    refused = commerce.place_order_direct({"items": ["item_coffee"]})
    assert refused["ok"] is False
    assert refused.get("approval_required") is True
    assert len(proposals.list_proposals("pending")) == 0
    # Cart builder ALWAYS goes via actions_propose (Tier-2 Ask).
    res = commerce.build_cart_proposal(item_ids=["item_coffee"], bundle_optimized=False)
    assert res["ok"] is True
    assert res["gated"] is True
    assert res["via"] == "actions_propose"
    assert res["tier"] == "tier-2-ask"
    assert res["single_use"] is True
    pid = res["proposal"]["id"]
    assert res["proposal"]["kind"] == "commerce_order"
    assert res["proposal"]["status"] == "pending"
    # Single-use receipt: approve once, replay refused.
    first = proposals.decide(pid, True)
    assert first["status"] == "approved"
    assert "execution" in first
    replay = proposals.decide(pid, True)
    assert replay["ok"] is False
    assert "already" in replay["error"]
    proposals.clear_proposals()


def test_b5_transit_milestones_and_upc_restock():
    t = delivery.get_live_transit()
    assert t["ok"] is True
    assert t["sandbox"] is True
    assert len(t["milestones"]) >= 5
    assert t["live_transit"]["stops_away"] == 2
    assert any(m["id"] == "m_out_for_delivery" and m["done"] for m in t["milestones"])
    # UPC hook resolves synthetic barcode + recomputes velocity.
    scan = delivery.restock_via_upc("012345678905", "deplete")
    assert scan["ok"] is True
    assert scan["item_id"] == "item_coffee"
    assert scan["computed"] is True
    assert scan["item"]["status"] == "critical"
    back = delivery.restock_via_upc("UPC-COFFEE-2LB", "replenish")
    assert back["ok"] is True
    assert back["item"]["level_pct"] == 100


def test_b5_roi_audit_sandbox():
    roi = commerce.audit_subscription_roi()
    assert roi["ok"] is True
    assert roi["sandbox"] is True
    assert roi["potential_annual_savings"] > 0
    assert roi["roi_pct"] == round(roi["potential_annual_savings"] / roi["total_annual_spend"] * 100, 1)
    assert roi["keep_annual_cost"] == round(roi["total_annual_spend"] - roi["potential_annual_savings"], 2)
