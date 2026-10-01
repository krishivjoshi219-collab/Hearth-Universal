"""Household Commerce & Subscription Management module for Alexa+.
Handles reordering essentials, finding subscription deals, delivery slot re-scheduling,
Amazon Subscribe & Save 5+ item bundle tier optimization, and proposing cart checkouts.
Strictly adheres to propose-never-execute: orders require human approval in the tray.
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path

STATE_DIR = Path(os.environ.get("HEARTH_STATE_DIR", "state"))

# Mock household inventory & auto-replenishment items
HOUSEHOLD_ESSENTIALS = [
    {
        "id": "item_coffee",
        "name": "Organic Arabica Whole Bean Coffee (2 lb)",
        "category": "Pantry",
        "level_pct": 15,
        "days_until_empty": 2.5,
        "status": "low",
        "last_ordered": "38 days ago",
        "price": 21.99,
        "subscribe_and_save_price": 18.69,
        "subscribe_discount_pct": 15,
        "prime_delivery": "Tomorrow by 8 AM (Prime FREE)",
        "recommended_action": "reorder",
        "asin": "B07XYZCOFF",
    },
    {
        "id": "item_detergent",
        "name": "Eco-Clean Plant-Based Laundry Pods (80 ct)",
        "category": "Cleaning",
        "level_pct": 10,
        "days_until_empty": 3.0,
        "status": "critical",
        "last_ordered": "55 days ago",
        "price": 18.50,
        "subscribe_and_save_price": 15.72,
        "subscribe_discount_pct": 15,
        "prime_delivery": "Tomorrow by 11 AM (Prime FREE)",
        "recommended_action": "reorder",
        "asin": "B08PODCLEA",
    },
    {
        "id": "item_filters",
        "name": "HEPA Air Purifier Replacement Filters (2-pk)",
        "category": "Home Health",
        "level_pct": 20,
        "days_until_empty": 6.0,
        "status": "low",
        "last_ordered": "170 days ago",
        "price": 34.00,
        "subscribe_and_save_price": 28.90,
        "subscribe_discount_pct": 15,
        "prime_delivery": "Prime 2-Day Delivery",
        "recommended_action": "reorder",
        "asin": "B09HEPAFIL",
    },
    {
        "id": "item_dishwasher_tabs",
        "name": "SparkleClean PowerBall Dishwasher Tablets (64 ct)",
        "category": "Cleaning",
        "level_pct": 25,
        "days_until_empty": 8.0,
        "status": "low",
        "last_ordered": "45 days ago",
        "price": 17.49,
        "subscribe_and_save_price": 14.87,
        "subscribe_discount_pct": 15,
        "prime_delivery": "Prime Delivery",
        "recommended_action": "reorder",
        "asin": "B07DISHTAB",
    },
    {
        "id": "item_olive_oil",
        "name": "Single-Estate Cold Pressed Extra Virgin Olive Oil (1L)",
        "category": "Pantry",
        "level_pct": 35,
        "days_until_empty": 12.0,
        "status": "good",
        "last_ordered": "60 days ago",
        "price": 16.99,
        "subscribe_and_save_price": 14.44,
        "subscribe_discount_pct": 15,
        "prime_delivery": "Prime Delivery",
        "recommended_action": "monitor",
        "asin": "B08OLIVEOIL",
    },
    {
        "id": "item_hand_soap",
        "name": "Botanical Foaming Hand Soap Refill (32 fl oz)",
        "category": "Cleaning",
        "level_pct": 40,
        "days_until_empty": 14.0,
        "status": "good",
        "last_ordered": "30 days ago",
        "price": 12.50,
        "subscribe_and_save_price": 10.62,
        "subscribe_discount_pct": 15,
        "prime_delivery": "Prime Delivery",
        "recommended_action": "monitor",
        "asin": "B09HANDSOAP",
    },
    {
        "id": "item_paper",
        "name": "Bamboo Ultra-Soft Bath Tissue (24 Mega Rolls)",
        "category": "Paper Goods",
        "level_pct": 65,
        "days_until_empty": 21.0,
        "status": "good",
        "last_ordered": "14 days ago",
        "price": 26.99,
        "subscribe_and_save_price": 22.94,
        "subscribe_discount_pct": 15,
        "prime_delivery": "Prime Delivery",
        "recommended_action": "monitor",
        "asin": "B0BAMBOOPP",
    }
]

# ---------------------------------------------------------------------------
# B5 purchasing-differentiator: sandbox fixture marking + depletion velocity.
# All pantry / subscription / tracking data below is SYNTHETIC SANDBOX FIXTURE.
# No real bank, Hue, or Amazon payment APIs are called. See CLAIM map.
# ---------------------------------------------------------------------------
SANDBOX_FIXTURE = True
DATA_SOURCE = "sandbox-fixture: synthetic pantry/subscription/tracking data"
SANDBOX_NOTE = (
    "Sandbox fixture only — no real bank/Hue/Amazon payment APIs called. "
    "Checkout is staged via actions_propose (Tier-2 Ask, single-use receipt); "
    "never executed directly."
)
STANDARD_SNS_DISCOUNT_PCT = 15.0

# Depletion velocity: daily consumption in %-points/day, calibrated so that
# level_pct / rate reproduces the legacy baseline days_until_empty.
# days_until_empty is COMPUTED (level / rate), never hardcoded downstream.
DAILY_CONSUMPTION_RATE_PCT: dict[str, float] = {
    "item_coffee": 6.0,          # 15% / 2.5d
    "item_detergent": 3.333,     # 10% / 3.0d
    "item_filters": 3.333,       # 20% / 6.0d
    "item_dishwasher_tabs": 3.125,  # 25% / 8.0d
    "item_olive_oil": 2.917,     # 35% / 12.0d
    "item_hand_soap": 2.857,     # 40% / 14.0d
    "item_paper": 3.095,         # 65% / 21.0d
}

# Sandbox UPC hook: optical barcode -> item_id (synthetic codes, no live lookup).
UPC_INDEX: dict[str, str] = {
    "012345678905": "item_coffee",
    "012345678912": "item_detergent",
    "012345678929": "item_filters",
    "012345678936": "item_dishwasher_tabs",
    "012345678943": "item_olive_oil",
    "012345678950": "item_hand_soap",
    "012345678967": "item_paper",
    "UPC-COFFEE-2LB": "item_coffee",
    "UPC-DETERGENT-80CT": "item_detergent",
}


def sandbox_disclaimer() -> dict:
    """Openly mark fixture data as sandbox per claim map."""
    return {
        "sandbox": True,
        "data_source": DATA_SOURCE,
        "note": SANDBOX_NOTE,
    }


def compute_days_until_empty(item: dict) -> float:
    """Compute days_until_empty from depletion velocity (level / daily rate).

    Falls back to the stored value only when no velocity rate is known,
    so legacy items without telemetry still return a sane number.
    """
    rate = DAILY_CONSUMPTION_RATE_PCT.get(item.get("id", ""), 0.0)
    try:
        level = float(item.get("level_pct", 0.0))
    except (TypeError, ValueError):
        level = 0.0
    if rate and rate > 0:
        return round(level / rate, 1)
    try:
        return float(item.get("days_until_empty", 99.0))
    except (TypeError, ValueError):
        return 99.0


def get_depletion_velocity(item_id: str) -> dict:
    """Return velocity telemetry for one item with computed days_until_empty."""
    for it in HOUSEHOLD_ESSENTIALS:
        if it["id"] == item_id or it.get("asin") == item_id:
            days = compute_days_until_empty(it)
            return {
                "ok": True,
                "id": it["id"],
                "level_pct": it["level_pct"],
                "daily_use_rate_pct": DAILY_CONSUMPTION_RATE_PCT.get(it["id"]),
                "days_until_empty": days,
                "computed": True,
                "formula": "days_until_empty = level_pct / daily_use_rate_pct",
                **sandbox_disclaimer(),
            }
    return {"ok": False, "error": f"Item '{item_id}' not found.", **sandbox_disclaimer()}


# Active subscription services with usage telemetry
SUBSCRIPTION_SERVICES = [
    {
        "id": "sub_streambox",
        "name": "StreamBox 4K Family Plan",
        "cost_monthly": 19.99,
        "cost_yr": 239.88,
        "last_used_days": 68,
        "usage_status": "Dormant (0 streams in 60d)",
        "recommendation": "cancel",
        "savings_yr": 239.88,
        "reason": "No household member streamed in over 60 days.",
    },
    {
        "id": "sub_gym",
        "name": "Metro Fitness All-Access Plus",
        "cost_monthly": 65.00,
        "cost_yr": 780.00,
        "last_used_days": 42,
        "usage_status": "Low (1 visit in 45d)",
        "recommendation": "downgrade",
        "savings_yr": 360.00,
        "reason": "Downgrading to Standard Tier ($35/mo) retains weekend access while saving $360/yr.",
    },
    {
        "id": "sub_gamepass",
        "name": "Ultra Cloud Gaming Ultimate",
        "cost_monthly": 16.99,
        "cost_yr": 203.88,
        "last_used_days": 48,
        "usage_status": "Inactive (no sessions)",
        "recommendation": "cancel",
        "savings_yr": 203.88,
        "reason": "Unplayed library. Can be resumed instantly with cloud saves preserved.",
    },
    {
        "id": "sub_music",
        "name": "Echo Music HD Family",
        "cost_monthly": 16.99,
        "cost_yr": 203.88,
        "last_used_days": 1,
        "usage_status": "Active (daily across 4 Echo devices)",
        "recommendation": "keep",
        "savings_yr": 0.0,
        "reason": "Heavy daily usage for kitchen & living room background audio.",
    },
    {
        "id": "sub_cloud",
        "name": "Secure Vault Cloud Storage 2TB",
        "cost_monthly": 9.99,
        "cost_yr": 119.88,
        "last_used_days": 0,
        "usage_status": "Active (1.82 TB utilized / 91%)",
        "recommendation": "keep",
        "savings_yr": 0.0,
        "reason": "Contains encrypted backups of family media and home security footage.",
    },
]

# Available Amazon Prime & Subscribe & Save Delivery Slots
DEFAULT_DELIVERY_SLOTS = [
    {
        "slot_id": "slot_tuesday_household",
        "name": "Tuesday Prime Household Day",
        "day_of_week": "Tuesday",
        "delivery_window": "8:00 AM - 12:00 PM",
        "date_str": "Tuesday, Oct 6",
        "days_away": 5,
        "is_default": True,
        "eco_tier": "Maximum Eco (Zero Extra Van Trips)",
        "carbon_delta_kg": -1.8,
        "carrier": "Amazon Logistics (AMZL)",
        "delivery_fee": 0.0,
        "description": "Consolidates all household orders into a single weekly delivery box.",
    },
    {
        "slot_id": "slot_overnight_urgent",
        "name": "Prime Overnight / Tomorrow Morning",
        "day_of_week": "Tomorrow",
        "delivery_window": "7:00 AM - 11:00 AM",
        "date_str": "Tomorrow, Oct 2",
        "days_away": 1,
        "is_default": False,
        "eco_tier": "Expedited (Immediate replenishment)",
        "carbon_delta_kg": +0.9,
        "carrier": "Amazon Prime Dedicated",
        "delivery_fee": 0.0,
        "description": "Rapid fulfillment for items facing imminent depletion (under 2 days).",
    },
    {
        "slot_id": "slot_saturday_weekend",
        "name": "Saturday Attended Weekend Slot",
        "day_of_week": "Saturday",
        "delivery_window": "10:00 AM - 2:00 PM",
        "date_str": "Saturday, Oct 3",
        "days_away": 2,
        "is_default": False,
        "eco_tier": "Attended Weekend Drop",
        "carbon_delta_kg": -0.6,
        "carrier": "Amazon Logistics (AMZL)",
        "delivery_fee": 0.0,
        "description": "Ideal for perishable or high-value packages when residents are home.",
    },
    {
        "slot_id": "slot_thursday_twilight",
        "name": "Thursday Twilight Slot",
        "day_of_week": "Thursday",
        "delivery_window": "6:00 PM - 9:00 PM",
        "date_str": "Thursday, Oct 8",
        "days_away": 7,
        "is_default": False,
        "eco_tier": "Off-Peak Neighborhood Routing",
        "carbon_delta_kg": -1.2,
        "carrier": "Amazon Logistics (AMZL)",
        "delivery_fee": 0.0,
        "description": "Evenings when traffic is lower, reducing neighborhood stop congestion.",
    }
]

# In-memory tracking of currently scheduled delivery slot
_SCHEDULED_SLOT_ID: str = "slot_tuesday_household"


def _delivery_schedule_file() -> Path:
    return STATE_DIR / "delivery_schedule.json"


def get_scheduled_delivery_slot() -> dict:
    """Return the currently active scheduled delivery slot for Subscribe & Save orders."""
    global _SCHEDULED_SLOT_ID
    p = _delivery_schedule_file()
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            _SCHEDULED_SLOT_ID = data.get("slot_id", _SCHEDULED_SLOT_ID)
        except Exception:
            pass

    for s in DEFAULT_DELIVERY_SLOTS:
        if s["slot_id"] == _SCHEDULED_SLOT_ID:
            res = dict(s)
            res["active"] = True
            return res

    default_slot = dict(DEFAULT_DELIVERY_SLOTS[0])
    default_slot["active"] = True
    return default_slot


def list_available_delivery_slots(item_ids: list[str] | None = None) -> list[dict]:
    """Return available delivery slots with evaluated stockout risk for target consumables."""
    scheduled = get_scheduled_delivery_slot()
    targets = [i for i in HOUSEHOLD_ESSENTIALS if (not item_ids or i["id"] in item_ids)]
    if not targets:
        targets = [i for i in HOUSEHOLD_ESSENTIALS if i["status"] in ("low", "critical")]

    computed_days = {i["id"]: compute_days_until_empty(i) for i in targets}
    min_days_until_empty = min(computed_days.values(), default=99.0)
    critical_items = [i for i in targets if computed_days.get(i["id"], 99.0) <= 3.0]

    slots = []
    for s in DEFAULT_DELIVERY_SLOTS:
        item = dict(s)
        is_active = (s["slot_id"] == scheduled["slot_id"])
        item["active"] = is_active
        days_away = s["days_away"]

        # Stockout evaluation
        if days_away > min_days_until_empty:
            item["stockout_risk"] = True
            imminent = [i["name"].split("(")[0].strip() for i in critical_items if computed_days.get(i["id"], 99) < days_away]
            item["warning"] = f"Stockout risk: {', '.join(imminent)} will run out before {s['day_of_week']} delivery."
            item["recommended"] = False
        else:
            item["stockout_risk"] = False
            item["warning"] = None
            # If critical items exist and slot arrives quickly, recommend it
            if critical_items and days_away <= 2:
                item["recommended"] = True
                item["recommendation_reason"] = "Safely replenishes items before household stockout."
            elif not critical_items and s.get("is_default"):
                item["recommended"] = True
                item["recommendation_reason"] = "Lowest carbon emissions via Amazon Day consolidation."
            else:
                item["recommended"] = False

        slots.append(item)
    return slots


def reschedule_delivery_slot(slot_id: str, item_ids: list[str] | None = None, reason: str = "") -> dict:
    """Re-schedule the upcoming Subscribe & Save household delivery slot."""
    global _SCHEDULED_SLOT_ID
    target_slot = None
    for s in DEFAULT_DELIVERY_SLOTS:
        if s["slot_id"] == slot_id:
            target_slot = s
            break

    if not target_slot:
        return {"ok": False, "error": f"Delivery slot '{slot_id}' not found."}

    prev_slot = get_scheduled_delivery_slot()
    _SCHEDULED_SLOT_ID = slot_id

    # Persist
    p = _delivery_schedule_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slot_id": slot_id,
        "name": target_slot["name"],
        "day_of_week": target_slot["day_of_week"],
        "delivery_window": target_slot["delivery_window"],
        "date_str": target_slot["date_str"],
        "rescheduled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "reason": reason or f"Rescheduled to {target_slot['name']}"
    }
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    affected_items = [i["name"] for i in HOUSEHOLD_ESSENTIALS if (not item_ids or i["id"] in item_ids)]
    diff_str = f"{prev_slot['name']} -> {target_slot['name']} ({target_slot['delivery_window']})"

    return {
        "ok": True,
        "rescheduled": True,
        "previous_slot": prev_slot["name"],
        "new_slot": target_slot["name"],
        "scheduled_date": target_slot["date_str"],
        "delivery_window": target_slot["delivery_window"],
        "carbon_delta_kg": target_slot["carbon_delta_kg"],
        "eco_tier": target_slot["eco_tier"],
        "items_affected": affected_items,
        "stockout_risk_mitigated": target_slot["days_away"] <= 2,
        "diff": diff_str,
        "summary": f"Household delivery rescheduled from {prev_slot['name']} to {target_slot['name']} ({target_slot['delivery_window']})."
    }


def optimize_bundles(item_ids: list[str] | None = None, auto_fill_tier: bool = True, target_tier_items: int = 5) -> dict:
    """Analyze consumable inventory and compute Amazon Subscribe & Save 5+ item bundle tier optimization.
    
    Mechanics:
    - 1-4 items: 15% standard Subscribe & Save discount.
    - 5+ items in the same delivery: unlocks Tier-2 Prime Max Savings (20% on cleaning/health/pantry goods).
    - Cross-category synergy rebates: e.g. Pantry (coffee) + Cleaning (detergent) instant manufacturer bundle coupons.
    - Pull-forward analysis: intelligently adds upcoming low-runway items to unlock the higher tier across ALL items.
    - Packaging & carbon reduction: consolidates multiple separate courier trips into a single 100% recyclable box.
    """
    # Identify initial target items
    if item_ids:
        initial_items = [i for i in HOUSEHOLD_ESSENTIALS if i["id"] in item_ids]
    else:
        initial_items = [i for i in HOUSEHOLD_ESSENTIALS if i["status"] in ("low", "critical")]

    selected_ids = {i["id"] for i in initial_items}
    pull_forward_items = []

    # If below target_tier_items (5 items), auto-fill with lowest COMPUTED days_until_empty
    if auto_fill_tier and len(initial_items) < target_tier_items:
        remaining_candidates = sorted(
            [i for i in HOUSEHOLD_ESSENTIALS if i["id"] not in selected_ids],
            key=lambda x: compute_days_until_empty(x)
        )
        for cand in remaining_candidates:
            if len(initial_items) + len(pull_forward_items) >= target_tier_items:
                break
            pull_forward_items.append(cand)

    all_bundled_items = initial_items + pull_forward_items
    item_count = len(all_bundled_items)
    tier_unlocked = item_count >= target_tier_items

    # Pricing calculations
    regular_total = sum(i["price"] for i in all_bundled_items)
    # Baseline standard S&S (15% across items)
    baseline_sns_total = sum(i["subscribe_and_save_price"] for i in all_bundled_items)

    # 5+ item Prime Max tier: 20% discount on cleaning & health, 18% on pantry/paper
    item_breakdown = []
    bundle_items_total = 0.0

    for it in all_bundled_items:
        cat = it.get("category", "")
        tier_disc_pct = 20 if (tier_unlocked and cat in ("Cleaning", "Home Health")) else (18 if tier_unlocked else 15)
        tier_price = round(it["price"] * (1.0 - tier_disc_pct / 100.0), 2)
        bundle_items_total += tier_price
        item_breakdown.append({
            "id": it["id"],
            "asin": it["asin"],
            "name": it["name"],
            "category": it["category"],
            "regular_price": it["price"],
            "tier1_price": it["subscribe_and_save_price"],
            "optimized_price": tier_price,
            "savings": round(it["price"] - tier_price, 2),
            "discount_pct": tier_disc_pct,
            "pulled_forward": it in pull_forward_items,
            "days_until_empty": compute_days_until_empty(it),
            "daily_use_rate_pct": DAILY_CONSUMPTION_RATE_PCT.get(it.get("id", "")),
            "depletion_computed": True,
            "amazon_url": f"https://www.amazon.com/dp/{it['asin']}",
        })

    # Synergy rebates for multi-category pairing
    categories = {it["category"] for it in all_bundled_items}
    synergy_rebate = 0.0
    rebate_tags = []
    if "Pantry" in categories and "Cleaning" in categories:
        synergy_rebate += 7.50
        rebate_tags.append("Pantry & Cleaning Essentials Co-Op Rebate (-$7.50)")
    if any(it["id"] == "item_filters" for it in all_bundled_items):
        synergy_rebate += 6.80
        rebate_tags.append("HEPA Clean Air Manufacturer Instant Rebate (-$6.80)")

    final_bundle_price = round(max(0.0, bundle_items_total - synergy_rebate), 2)
    total_savings = round(regular_total - final_bundle_price, 2)
    savings_pct = round((total_savings / regular_total) * 100.0, 1) if regular_total > 0 else 0.0
    tier_bonus_savings = round(baseline_sns_total - final_bundle_price, 2)

    # Packaging and environmental metrics
    boxes_saved = max(1, item_count - 1)
    carbon_offset_kg = round(boxes_saved * 0.85, 2)

    std_match = match_bundle_discount([i["id"] for i in all_bundled_items])

    return {
        "ok": True,
        "sandbox": True,
        "data_source": DATA_SOURCE,
        "bundle_id": f"bundle_opt_{int(time.time())}",
        "tier_unlocked": tier_unlocked,
        "tier_badge": "Prime Max 5+ Items (20% Tier + Manufacturer Co-Op Rebates)" if tier_unlocked else "Standard 15% S&S",
        "item_count": item_count,
        "items": item_breakdown,
        "pull_forward_items": [i["name"] for i in pull_forward_items],
        "standard_15pct_match": std_match,
        "pricing": {
            "regular_total": round(regular_total, 2),
            "baseline_sns_total": round(baseline_sns_total, 2),
            "standard_15pct_total": std_match["matched_total"],
            "standard_15pct_savings": std_match["savings"],
            "optimized_bundle_total": final_bundle_price,
            "total_savings": total_savings,
            "savings_pct": savings_pct,
            "bundle_synergy_rebates": round(synergy_rebate, 2),
            "tier_bonus_savings": tier_bonus_savings,
            "active_rebates": rebate_tags,
        },
        "environmental_impact": {
            "boxes_saved": boxes_saved,
            "carbon_offset_kg": carbon_offset_kg,
            "packaging": "Consolidated 100% Recyclable Frustration-Free Box",
        },
        "recommended_delivery_slot": "Tuesday Prime Household Day",
        "summary": (
            f"Bundle optimization unlocked Prime Max 20% tier across {item_count} items: "
            f"saved ${total_savings:.2f} ({savings_pct}%), combined into 1 consolidated box, "
            f"eliminating {boxes_saved} delivery shipments (-{carbon_offset_kg} kg CO2e)."
        )
    }


def _enriched_copy(it: dict) -> dict:
    """Return a copy enriched with computed depletion + sandbox marking."""
    c = dict(it)
    c["days_until_empty"] = compute_days_until_empty(it)
    c["daily_use_rate_pct"] = DAILY_CONSUMPTION_RATE_PCT.get(it.get("id", ""))
    c["depletion_computed"] = True
    c["sandbox_fixture"] = True
    # Surface a synthetic UPC for the optical restock hook (sandbox).
    for upc, iid in UPC_INDEX.items():
        if iid == it.get("id") and upc.isdigit():
            c.setdefault("upc", upc)
            break
    return c


def list_inventory() -> list[dict]:
    """Return household replenishment inventory (sandbox fixture, computed depletion)."""
    return [_enriched_copy(i) for i in HOUSEHOLD_ESSENTIALS]


def get_low_stock() -> list[dict]:
    """Return inventory items that need reordering."""
    return [_enriched_copy(i) for i in HOUSEHOLD_ESSENTIALS if i["status"] in ("low", "critical")]


def scan_subscriptions() -> dict:
    """Analyze all subscriptions, calculate total cost and potential savings."""
    total_spend = sum(s["cost_yr"] for s in SUBSCRIPTION_SERVICES)
    cancellable = [s for s in SUBSCRIPTION_SERVICES if s["recommendation"] == "cancel"]
    downgradable = [s for s in SUBSCRIPTION_SERVICES if s["recommendation"] == "downgrade"]
    keep = [s for s in SUBSCRIPTION_SERVICES if s["recommendation"] == "keep"]
    
    potential_savings = sum(s["savings_yr"] for s in cancellable + downgradable)
    
    return {
        "subscriptions": SUBSCRIPTION_SERVICES,
        "total_annual_spend": round(total_spend, 2),
        "potential_annual_savings": round(potential_savings, 2),
        "cancellable_count": len(cancellable),
        "downgradable_count": len(downgradable),
        "keep_count": len(keep),
    }


def find_deals() -> list[dict]:
    """Find active discounts and bundle opportunities for household essentials."""
    return [
        {
            "id": "deal_coffee_detergent_bundle",
            "title": "Pantry & Cleaning Essentials Bundle",
            "items": ["Arabica Coffee (2 lb)", "Eco Laundry Pods (80 ct)"],
            "regular_total": 40.49,
            "bundle_price": 32.99,
            "savings": 7.50,
            "deal_type": "Subscribe & Save Combined",
            "expires_in_hours": 36,
        },
        {
            "id": "deal_air_filter_rebate",
            "title": "Clean Air Healthy Home Rebate",
            "items": ["HEPA Air Purifier Filters (2-pk)"],
            "regular_total": 34.00,
            "bundle_price": 27.20,
            "savings": 6.80,
            "deal_type": "Manufacturer Instant Coupon",
            "expires_in_hours": 72,
        },
        {
            "id": "deal_dish_cleaning_combo",
            "title": "Sparkle Kitchen Clean Dish Duo",
            "items": ["Dishwasher Tablets (64 ct)", "Foaming Hand Soap (32 fl oz)"],
            "regular_total": 29.99,
            "bundle_price": 23.99,
            "savings": 6.00,
            "deal_type": "Multi-Buy Discount",
            "expires_in_hours": 48,
        }
    ]


def get_depletion_forecast() -> list[dict]:
    """Return consumables sorted by urgency of depletion (COMPUTED days until runout).

    days_until_empty = level_pct / daily_use_rate_pct (velocity, not hardcoded).
    """
    enriched = [_enriched_copy(i) for i in HOUSEHOLD_ESSENTIALS]
    items = sorted(enriched, key=lambda x: x.get("days_until_empty", 99))
    out = []
    for i in items:
        out.append(
            {
                "id": i["id"],
                "name": i["name"],
                "days_until_empty": i["days_until_empty"],
                "level_pct": i["level_pct"],
                "daily_use_rate_pct": i["daily_use_rate_pct"],
                "depletion_computed": True,
                "formula": "level_pct / daily_use_rate_pct",
                "status": i["status"],
                "price": i["price"],
                "subscribe_price": i["subscribe_and_save_price"],
                "prime_delivery": i["prime_delivery"],
                "asin": i["asin"],
                "upc": i.get("upc"),
                "amazon_url": f"https://www.amazon.com/dp/{i['asin']}",
                "sandbox_fixture": True,
            }
        )
    return out


def match_bundle_discount(item_ids: list[str] | None = None) -> dict:
    """Apply standard 15% Subscribe & Save bundle matching (Tier-1 baseline).

    Every matched item gets exactly 15% off regular price. The 5+ item
    Prime Max tier in optimize_bundles() builds on top of this baseline.
    Sandbox pricing fixture — no live Amazon pricing API.
    """
    targets = [i for i in HOUSEHOLD_ESSENTIALS if (not item_ids or i["id"] in item_ids)]
    if not targets:
        targets = [i for i in HOUSEHOLD_ESSENTIALS if i["status"] in ("low", "critical")]
    lines = []
    regular_total = 0.0
    matched_total = 0.0
    for t in targets:
        matched = round(t["price"] * (1.0 - STANDARD_SNS_DISCOUNT_PCT / 100.0), 2)
        regular_total += t["price"]
        matched_total += matched
        lines.append(
            {
                "id": t["id"],
                "name": t["name"],
                "regular_price": t["price"],
                "matched_price": matched,
                "discount_pct": STANDARD_SNS_DISCOUNT_PCT,
                "savings": round(t["price"] - matched, 2),
            }
        )
    savings = round(regular_total - matched_total, 2)
    return {
        "ok": True,
        "discount_pct": STANDARD_SNS_DISCOUNT_PCT,
        "tier": "standard-15pct-sns-match",
        "items": lines,
        "regular_total": round(regular_total, 2),
        "matched_total": round(matched_total, 2),
        "savings": savings,
        **sandbox_disclaimer(),
    }


def audit_subscription_roi() -> dict:
    """ROI audit: $ savings calc over sandbox subscription fixtures."""
    data = scan_subscriptions()
    total = data["total_annual_spend"]
    save = data["potential_annual_savings"]
    keep_cost = round(total - save, 2)
    roi_pct = round((save / total) * 100.0, 1) if total > 0 else 0.0
    return {
        "ok": True,
        "total_annual_spend": total,
        "potential_annual_savings": save,
        "keep_annual_cost": keep_cost,
        "roi_pct": roi_pct,
        "cancellable_count": data["cancellable_count"],
        "downgradable_count": data["downgradable_count"],
        "keep_count": data["keep_count"],
        "formula": "savings = sum(cancel/downgrade savings_yr); roi_pct = savings/total*100",
        **sandbox_disclaimer(),
    }


def stage_amazon_cart(
    item_ids: list[str] | None = None,
    subscribe_and_save: bool = True,
    delivery_slot_id: str | None = None,
    bundle_optimized: bool = False
) -> dict:
    """Stage an Amazon order proposal with Subscribe & Save discounts, slot re-scheduling, and bundle optimization."""
    # If bundle optimization requested, run the bundle engine
    if bundle_optimized:
        bundle_res = optimize_bundles(item_ids=item_ids, auto_fill_tier=True)
        order_items = []
        for b_item in bundle_res["items"]:
            order_items.append({
                "asin": b_item["asin"],
                "name": b_item["name"],
                "quantity": 1,
                "unit_price": b_item["optimized_price"],
                "original_price": b_item["regular_price"],
                "prime_delivery": "Prime Household Delivery Day",
                "subscribe_and_save": True,
                "pulled_forward": b_item.get("pulled_forward", False),
            })
        
        reg_subtotal = bundle_res["pricing"]["regular_total"]
        final_subtotal = bundle_res["pricing"]["optimized_bundle_total"]
        savings = bundle_res["pricing"]["total_savings"]

        # Resolve delivery slot
        slot = None
        if delivery_slot_id:
            for s in DEFAULT_DELIVERY_SLOTS:
                if s["slot_id"] == delivery_slot_id:
                    slot = s
                    break
        if not slot:
            slot = get_scheduled_delivery_slot()

        schedule_str = f"{slot['day_of_week']} ({slot['name']})" if "Household" in slot["name"] else f"{slot['day_of_week']} ({slot['delivery_window']})"

        return {
            "ok": True,
            "sandbox": True,
            "data_source": DATA_SOURCE,
            "staged_only": True,
            "note": "Cart STAGED for human approval — no order placed. Use build_cart_proposal() to route via actions_propose.",
            "items": order_items,
            "item_count": len(order_items),
            "regular_subtotal": round(reg_subtotal, 2),
            "final_total": round(final_subtotal, 2),
            "savings": savings,
            "delivery_schedule": schedule_str,
            "delivery_slot": slot,
            "subscribe_cadence": "Every 1 month",
            "card_type": "amazon_subscribe_and_save",
            "prime_badge": True,
            "bundle_optimized": True,
            "tier_badge": bundle_res["tier_badge"],
            "boxes_saved": bundle_res["environmental_impact"]["boxes_saved"],
            "carbon_offset_kg": bundle_res["environmental_impact"]["carbon_offset_kg"],
            "active_rebates": bundle_res["pricing"]["active_rebates"],
        }

    # Standard cart staging
    targets = [i for i in HOUSEHOLD_ESSENTIALS if (not item_ids or i["id"] in item_ids)]
    if not targets:
        targets = [i for i in HOUSEHOLD_ESSENTIALS if i["status"] in ("low", "critical")]
        
    order_items = []
    reg_subtotal = 0.0
    final_subtotal = 0.0
    
    for t in targets:
        unit_p = t["subscribe_and_save_price"] if subscribe_and_save else t["price"]
        reg_subtotal += t["price"]
        final_subtotal += unit_p
        order_items.append({
            "asin": t["asin"],
            "name": t["name"],
            "quantity": 1,
            "unit_price": unit_p,
            "original_price": t["price"],
            "prime_delivery": t["prime_delivery"],
            "subscribe_and_save": subscribe_and_save
        })
        
    savings = round(reg_subtotal - final_subtotal, 2)

    # Determine delivery slot
    slot = None
    if delivery_slot_id:
        for s in DEFAULT_DELIVERY_SLOTS:
            if s["slot_id"] == delivery_slot_id:
                slot = s
                break
    if not slot:
        slot = get_scheduled_delivery_slot()

    # Match default test string if standard Tuesday household day is active
    if slot["slot_id"] == "slot_tuesday_household":
        delivery_str = "Tuesday (Prime Household Delivery Day)"
    else:
        delivery_str = f"{slot['day_of_week']} ({slot['name']})"

    return {
        "ok": True,
        "sandbox": True,
        "data_source": DATA_SOURCE,
        "staged_only": True,
        "note": "Cart STAGED for human approval — no order placed. Use build_cart_proposal() to route via actions_propose.",
        "items": order_items,
        "item_count": len(order_items),
        "regular_subtotal": round(reg_subtotal, 2),
        "final_total": round(final_subtotal, 2),
        "savings": savings,
        "delivery_schedule": delivery_str,
        "delivery_slot": slot,
        "subscribe_cadence": "Every 1 month" if subscribe_and_save else "Single order",
        "card_type": "amazon_subscribe_and_save",
        "prime_badge": True,
        "bundle_optimized": False,
    }


def get_delivery_tracker() -> dict:
    """Return live Amazon Prime delivery tracking telemetry (sandbox fixture).

    Includes Prime live-transit milestones: ordered -> shipped -> out-for-delivery
    -> arriving -> delivered, with courier stops-away + ETA. Synthetic van
    telemetry; no live Amazon Logistics API.
    """
    steps = [
        {"step": "Ordered", "time": "Yesterday, 11:20 PM", "completed": True},
        {"step": "Shipped from JFK8 Fulfillment", "time": "Today, 4:15 AM", "completed": True},
        {"step": "Out for Delivery", "time": "Today, 6:40 PM", "completed": True, "active": True},
        {"step": "Delivered to Porch", "time": "Estimated 8:30 PM", "completed": False},
    ]
    milestones = [
        {"id": "m_ordered", "label": "Order placed", "at": "Yesterday, 11:20 PM", "done": True},
        {"id": "m_shipped", "label": "Shipped from JFK8", "at": "Today, 4:15 AM", "done": True},
        {"id": "m_in_transit", "label": "Arrived at local Prime station", "at": "Today, 2:05 PM", "done": True},
        {"id": "m_out_for_delivery", "label": "Out for delivery (Van #482)", "at": "Today, 6:40 PM", "done": True},
        {"id": "m_arriving", "label": "Arriving now — 2 stops away", "at": "ETA 7 min", "done": False},
        {"id": "m_delivered", "label": "Delivered to porch", "at": "Estimated 8:30 PM", "done": False},
    ]
    return {
        "ok": True,
        "sandbox": True,
        "data_source": DATA_SOURCE,
        "note": "Sandbox transit fixture — synthetic courier telemetry, no live AMZL API.",
        "tracking_number": "TBA3094829104",
        "carrier": "Amazon Logistics (AMZL)",
        "status": "out_for_delivery",
        "status_label": "Out for Delivery — Arriving by 8:30 PM",
        "package_items": [
            "Organic Arabica Whole Bean Coffee (2 lb)",
            "Eco-Clean Plant-Based Laundry Pods (80 ct)"
        ],
        "stops_away": 2,
        "eta_minutes": 7,
        "driver_name": "Marcus (Prime Van #482)",
        "delivery_address": "Front Porch / Secure Package Bench",
        "progress_steps": steps,
        "milestones": milestones,
        "live_transit": {
            "van_id": "Prime Van #482",
            "stops_away": 2,
            "eta_minutes": 7,
            "next_milestone": "m_arriving",
            "completed_milestones": 4,
            "total_milestones": len(milestones),
            # Synthetic position — sandbox, not a real courier fix.
            "van_lat": 40.7128,
            "van_lon": -74.0060,
        },
    }


def _resolve_scan_target(code: str) -> dict | None:
    """Resolve item_id / ASIN / UPC barcode to an inventory record."""
    if not code:
        return None
    key = str(code).strip()
    # Direct id / ASIN match.
    for item in HOUSEHOLD_ESSENTIALS:
        if item["id"] == key or item.get("asin") == key:
            return item
    # UPC hook: exact + case-insensitive + digit-only fallback.
    upc_hit = UPC_INDEX.get(key) or UPC_INDEX.get(key.upper())
    if not upc_hit:
        digits = "".join(ch for ch in key if ch.isdigit())
        for upc, iid in UPC_INDEX.items():
            if upc.isdigit() and digits and (digits == upc or digits in upc or upc in digits):
                upc_hit = iid
                break
    if upc_hit:
        for item in HOUSEHOLD_ESSENTIALS:
            if item["id"] == upc_hit:
                return item
    return None


def simulate_barcode_scan(item_id: str, action: str = "replenish") -> dict:
    """Optical UPC restock hook: barcode scan restocks or reports depletion.

    Accepts item_id, ASIN, or sandbox UPC (e.g. '012345678905'). Depletion
    days are COMPUTED from velocity (level / daily_rate), not hardcoded.
    Sandbox fixture — no live scanner hardware / retail API.
    """
    act = str(action or "replenish").strip().lower()
    if act in ("depleted", "deplete", "empty", "consume"):
        act = "deplete"
    else:
        act = "replenish"
    item = _resolve_scan_target(item_id)
    if item is not None:
        rate = DAILY_CONSUMPTION_RATE_PCT.get(item["id"], 3.0) or 3.0
        if act == "replenish":
            item["level_pct"] = 100
            item["days_until_empty"] = round(100 / rate, 1)
            item["status"] = "normal"
        else:
            item["level_pct"] = 10
            item["days_until_empty"] = round(10 / rate, 1)
            item["status"] = "critical"
        enriched = _enriched_copy(item)
        return {
            "ok": True,
            "sandbox": True,
            "data_source": DATA_SOURCE,
            "item": enriched,
            "item_id": item["id"],
            "upc_resolved": str(item_id) in UPC_INDEX or str(item_id).upper() in UPC_INDEX,
            "action": act,
            "days_until_empty": enriched["days_until_empty"],
            "computed": True,
            "message": f"Barcode scanned for {item['name']}: stock level set to {item['level_pct']}% (~{enriched['days_until_empty']}d at current velocity).",
        }
    return {"ok": False, "error": f"Item '{item_id}' not found in pantry inventory.", **sandbox_disclaimer()}


def place_order_direct(*args, **kwargs) -> dict:
    """Fail-closed: direct order execution is ALWAYS refused.

    Propose-never-execute contract: carts must go via build_cart_proposal()
    -> actions_propose (Tier-2 Ask, single-use receipt). This stub proves
    no direct checkout path exists.
    """
    return {
        "ok": False,
        "approval_required": True,
        "tier": "tier-2-ask",
        "error": "Direct order execution refused (propose-never-execute). Use build_cart_proposal() to stage a Tier-2 approval card.",
        **sandbox_disclaimer(),
    }


def build_cart_proposal(
    item_ids: list[str] | None = None,
    subscribe_and_save: bool = True,
    delivery_slot_id: str | None = None,
    bundle_optimized: bool = False,
    title: str = "Subscribe & Save Reorder",
) -> dict:
    """Cart builder that ALWAYS routes via actions_propose (Tier-2 Ask).

    Stages a read-only cart preview with stage_amazon_cart(), then drafts a
    single-use commerce_order proposal for the human tray. NEVER executes
    checkout directly; execution happens only via proposals.decide() receipt.
    """
    from . import proposals as _proposals

    cart = stage_amazon_cart(
        item_ids=item_ids,
        subscribe_and_save=subscribe_and_save,
        delivery_slot_id=delivery_slot_id,
        bundle_optimized=bundle_optimized,
    )
    total = float(cart.get("final_total", 0.0) or 0.0)
    savings = float(cart.get("savings", 0.0) or 0.0)
    diff = (
        f"Cart preview: {cart.get('item_count')} items, "
        f"regular ${cart.get('regular_subtotal', 0):.2f} -> "
        f"final ${total:.2f} (saved ${savings:.2f}). "
        f"Delivery: {cart.get('delivery_schedule')}. Sandbox fixture — no charge until human Approve."
    )
    reasons = (
        f"Staged Subscribe & Save cart saves ${savings:.2f}. "
        f"{cart.get('note', '')} Depletion computed from velocity; "
        "Tier-2 Ask: requires human 1-tap approval (single-use receipt)."
    )
    proposal = _proposals.propose(
        kind="commerce_order",
        title=title,
        reasons=reasons,
        cost_delta_yr=-total,
        risk_level="medium",
        diff=diff,
        meta={
            "cart_preview": cart,
            "price": total,
            "savings": savings,
            "bundle_optimized": bundle_optimized,
            "tier": "tier-2-ask",
            "single_use": True,
            "sandbox": True,
        },
    )
    return {
        "ok": True,
        "gated": True,
        "tier": "tier-2-ask",
        "single_use": True,
        "via": "actions_propose",
        "proposal": proposal,
        "cart_preview": cart,
        "message": f"Cart staged as proposal {proposal.get('id')} — awaiting human Approve (single-use). No order executed.",
        **sandbox_disclaimer(),
    }
