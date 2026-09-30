"""Household Commerce & Subscription Management module for Alexa+.
Handles reordering essentials, finding subscription deals, and proposing cart checkouts.
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
        "status": "low",
        "last_ordered": "38 days ago",
        "price": 21.99,
        "subscribe_discount_pct": 10,
        "recommended_action": "reorder",
    },
    {
        "id": "item_detergent",
        "name": "Eco-Clean Plant-Based Laundry Pods (80 ct)",
        "category": "Cleaning",
        "level_pct": 10,
        "status": "critical",
        "last_ordered": "55 days ago",
        "price": 18.50,
        "subscribe_discount_pct": 15,
        "recommended_action": "reorder",
    },
    {
        "id": "item_filters",
        "name": "HEPA Air Purifier Replacement Filters (2-pk)",
        "category": "Home Health",
        "level_pct": 20,
        "status": "low",
        "last_ordered": "170 days ago",
        "price": 34.00,
        "subscribe_discount_pct": 5,
        "recommended_action": "reorder",
    },
    {
        "id": "item_paper",
        "name": "Bamboo Ultra-Soft Bath Tissue (24 Mega Rolls)",
        "category": "Paper Goods",
        "level_pct": 65,
        "status": "good",
        "last_ordered": "14 days ago",
        "price": 26.99,
        "subscribe_discount_pct": 10,
        "recommended_action": "monitor",
    }
]

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


def list_inventory() -> list[dict]:
    """Return household replenishment inventory."""
    return HOUSEHOLD_ESSENTIALS


def get_low_stock() -> list[dict]:
    """Return inventory items that need reordering."""
    return [i for i in HOUSEHOLD_ESSENTIALS if i["status"] in ("low", "critical")]


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
        }
    ]
