"""Autonomous Household Heartbeat & Proactive Event Stream.
Maintains a rolling stream of autonomous background events (solar optimization,
climate eco-pulses, subscription reorders, perimeter integrity checks) that give
Hearth Universal its living, proactive intelligence.
"""
from __future__ import annotations
import copy
import json
import os
import time
from pathlib import Path
from typing import Any

from . import home_mock, proposals, commerce, audit

STATE_DIR = Path(os.environ.get("HEARTH_STATE_DIR", "state"))

DEFAULT_EVENTS = [
    {
        "id": "hb-001",
        "timestamp": time.time() - 3600 * 3,
        "time_str": "04:15 PM",
        "type": "energy",
        "icon": "☀️",
        "title": "Solar Generation Surge",
        "detail": "Solar array generated +1.8 kW. Home diverted surplus to battery reserve.",
        "status": "active"
    },
    {
        "id": "hb-002",
        "timestamp": time.time() - 3600 * 2,
        "time_str": "05:30 PM",
        "type": "security",
        "icon": "🔒",
        "title": "Auto-Lock Verified",
        "detail": "Front door deadbolt auto-locked 5 minutes after closure. Perimeter armed.",
        "status": "resolved"
    },
    {
        "id": "hb-003",
        "timestamp": time.time() - 1800,
        "time_str": "06:45 PM",
        "type": "climate",
        "icon": "🌱",
        "title": "Eco-Comfort Pulse",
        "detail": "Living room thermostat optimized to 21.5°C to avoid peak tariff rate.",
        "status": "resolved"
    },
    {
        "id": "hb-004",
        "timestamp": time.time() - 300,
        "time_str": "07:12 PM",
        "type": "commerce",
        "icon": "📦",
        "title": "Pantry Low-Stock Scan",
        "detail": "Arabica Coffee (15%) and Laundry Pods (10%) flagged for bulk replenishment.",
        "status": "active"
    }
]

_events: list[dict[str, Any]] = copy.deepcopy(DEFAULT_EVENTS)


def _path() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR / "heartbeat.json"


def _save() -> None:
    try:
        from . import atomic
        atomic.atomic_write_text(_path(), json.dumps(_events[-30:]))
    except Exception:
        pass


def _load() -> None:
    global _events
    try:
        p = _path()
        if p.exists():
            data = json.loads(p.read_text())
            if isinstance(data, list) and data:
                _events = data
    except Exception:
        pass


_load()


def get_events(limit: int = 15) -> list[dict[str, Any]]:
    """Return the most recent heartbeat events."""
    return sorted(_events, key=lambda e: e.get("timestamp", 0), reverse=True)[:limit]


def emit_event(event_type: str, icon: str, title: str, detail: str, status: str = "active") -> dict[str, Any]:
    """Emit an autonomous household heartbeat event."""
    now = time.time()
    evt = {
        "id": f"hb-{int(now * 1000) % 1000000}",
        "timestamp": now,
        "time_str": time.strftime("%I:%M %p"),
        "type": str(event_type)[:64],
        "icon": str(icon)[:8],
        "title": str(title)[:200],
        "detail": str(detail)[:2000],
        "status": str(status)[:32],
    }
    _events.append(evt)
    # Bound in-process RAM: keep last 200 only (file keeps last 30).
    del _events[:-200]
    _save()
    audit.append("heartbeat", f"event_{event_type}", {"title": str(title)[:200]})
    return evt


def _autopilot_due() -> bool:
    """True when any consumable has <=3 days left and no pending commerce_order exists."""
    try:
        forecast = commerce.get_depletion_forecast()
    except Exception:
        return False
    urgent = any(float(it.get("days_until_empty", 99) or 99) <= 3.0 for it in forecast)
    if not urgent:
        return False
    try:
        pending = proposals.list_proposals("pending")
    except Exception:
        return True
    return not any(p.get("kind") == "commerce_order" for p in pending if isinstance(p, dict))


def tick_proactive(scenario: str = "auto") -> dict[str, Any]:
    """Simulate a proactive autonomous household event."""
    now_str = time.strftime("%I:%M %p")
    proposals_created = []

    if scenario in ("autopilot_checkout", "checkout", "voice_tray") or (scenario == "auto" and _autopilot_due()):
        # Bundle-aware autopilot: stage S&S cart once (idempotent via build_autopilot_checkout)
        try:
            urgent_ids = [it.get("id") for it in commerce.get_depletion_forecast()
                          if float(it.get("days_until_empty", 99) or 99) <= 3.0 and it.get("id")]
        except Exception:
            urgent_ids = []
        res = commerce.build_autopilot_checkout(utterance="proactive restock of critical pantry items",
                                                item_ids=urgent_ids or None,
                                                bundle_optimized=True)
        if res.get("clarification_required"):
            evt = emit_event("commerce", "🛒", "Autopilot Checkout Watch",
                             f"Pantry low at {now_str} but request ambiguous — awaiting voice clarification.",
                             "active")
            return {"ok": True, "event": evt, "proposals": []}
        p = res.get("proposal", {})
        if p:
            proposals_created.append(p)
        cart = res.get("cart_preview", {})
        evt = emit_event(
            "commerce",
            "🛒",
            "Autopilot Checkout Staged",
            f"Tray card #{p.get('id', '?')}: {cart.get('item_count', '?')} items "
            f"${cart.get('final_total', 0):.2f} (save ${cart.get('savings', 0):.2f}) — tap Approve. Undo anytime."
            + (" (already pending — no duplicate)" if res.get("deduplicated") else ""),
            "active"
        )
        return {"ok": True, "event": evt, "proposals": proposals_created,
                "receipt_preview": {"proposal_id": p.get("id"), "cart_preview": cart}}

    if scenario in ("energy_peak", "energy") or (scenario == "auto" and len(_events) % 3 == 0):
        # Peak tariff detected
        home_mock.update_device("living_room", "climate", {"target_c": 21.0})
        evt = emit_event(
            "energy",
            "⚡",
            "Peak Tariff Mitigation",
            f"Grid power jumped to 38¢/kWh at {now_str}. Thermostat dialed -0.5°C; solar inverter engaged.",
            "resolved"
        )
        return {"ok": True, "event": evt, "proposals": []}

    elif scenario in ("pantry_alert", "pantry", "commerce") or (scenario == "auto" and len(_events) % 3 == 1):
        # Low consumables -> drafts proposal in Approval Tray
        deals = commerce.find_deals()
        deal = deals[0] if deals else None
        deal_price = deal["bundle_price"] if deal else 32.99

        p = proposals.propose(
            kind="commerce_order",
            title="Autonomous Reorder: Coffee & Cleaning Bundle",
            reasons="Pantry inventory monitor detected Organic Arabica Coffee at 15% and Laundry Pods at 10%.",
            cost_delta_yr=-deal_price,
            risk_level="medium",
            diff=f"Cart bundle total: ${deal_price:.2f} (Subscribe & Save discount applied).",
            meta={"deal_id": deal["id"] if deal else "bundle_standard"}
        )
        proposals_created.append(p)
        evt = emit_event(
            "commerce",
            "📦",
            "Consumables Threshold Alert",
            f"Stock below 15%. Drafted approval card #{p['id']} for Subscribe & Save replenishment.",
            "active"
        )
        return {"ok": True, "event": evt, "proposals": proposals_created}

    else:
        # Perimeter integrity verification
        st = home_mock.get_state()
        is_locked = st.get("entryway", {}).get("lock", {}).get("front_door") == "locked"
        evt = emit_event(
            "security",
            "🛡️",
            "Perimeter Sweep Complete",
            f"All 4 door and window sensors verified. Master deadbolt is { 'SECURE' if is_locked else 'UNLOCKED' }.",
            "resolved" if is_locked else "active"
        )
        return {"ok": True, "event": evt, "proposals": []}
