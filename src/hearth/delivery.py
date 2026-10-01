"""Prime delivery tracker + UPC restock hook (B5 scope: subscriptions/delivery).

Sandbox fixture module — no live Amazon Logistics API. All telemetry is
synthetic. Cart checkout ALWAYS routes via actions_propose (Tier-2 Ask,
single-use receipt); direct execution is refused.
"""
from __future__ import annotations

from . import commerce as _commerce


def get_live_transit() -> dict:
    """Prime live transit tracker: milestones + courier ETA (sandbox)."""
    tracker = _commerce.get_delivery_tracker()
    # Expose a flat milestone checklist for UI cards.
    tracker["milestone_checklist"] = [
        {"label": m["label"], "done": m["done"]} for m in tracker.get("milestones", [])
    ]
    return tracker


def list_slots(item_ids: list[str] | None = None) -> dict:
    """Available delivery slots with computed stockout risk (sandbox)."""
    return {
        "ok": True,
        "slots": _commerce.list_available_delivery_slots(item_ids=item_ids),
        "active_slot": _commerce.get_scheduled_delivery_slot(),
        "sandbox": True,
        "data_source": _commerce.DATA_SOURCE,
    }


def reschedule(slot_id: str, reason: str = "") -> dict:
    """Reschedule household delivery slot (sandbox persistence)."""
    out = _commerce.reschedule_delivery_slot(slot_id, reason=reason)
    out.setdefault("sandbox", True)
    return out


def restock_via_upc(upc: str, action: str = "replenish") -> dict:
    """Barcode UPC restock hook: optical scan -> velocity recompute (sandbox)."""
    return _commerce.simulate_barcode_scan(upc, action)


def build_cart_proposal(**kwargs) -> dict:
    """Cart builder — ALWAYS via actions_propose (Tier-2 Ask, single-use)."""
    return _commerce.build_cart_proposal(**kwargs)


def place_order_direct(*args, **kwargs) -> dict:
    """Fail-closed: direct checkout refused, must propose first."""
    return _commerce.place_order_direct(*args, **kwargs)
