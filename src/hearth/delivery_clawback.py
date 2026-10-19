"""Amazon Prime late-delivery clawback: SLA-miss detection -> $5 courtesy credit.

The home that pays for itself doesn't wait for the customer to notice a missed
promise: it reads the carrier scan feed, spots Prime deliveries that landed
past their promised window, and drafts the courtesy-credit claim for one tap.

Sandbox posture (same as ``hearth.delivery``): the carrier scan feed is a
synthetic fixture — no live Amazon Logistics / billing API. The guards that
make the claim real anyway:

* deterministic detection — a promised-time miss of >= 2h qualifies;
* idempotent claims — one open claim per order, ever;
* propose-never-execute — nothing is filed without a human tap in the
  Glass-box Approval Tray (kind ``delivery_credit_claim``);
* hash-chained proof — approval mints a ``HEARTH-RC-AMZ-CREDIT-*`` receipt
  through the Proof Engine (``credit_claimed``, money in the earned column).

No new MCP tool is registered: the flow peaks through the existing tracker +
``actions_propose`` tools, so the on-camera tool count stays untouched.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from . import atomic, proposals

STATE_DIR = Path(os.environ.get("HEARTH_STATE_DIR", "state"))

# Prime promise: deliveries that miss the promised time by >= 2h qualify for a
# $5.00 courtesy credit (sandbox policy — deterministic, single tier).
CREDIT_USD = 5.00
LATE_THRESHOLD_MIN = 120
SLA_RULE = "Prime promised-time misses of 2 hours or more qualify for a $5.00 courtesy credit"

DATA_SOURCE = "sandbox-fixture: synthetic Prime carrier scan feed"

# Recent deliveries as reported by the carrier scan feed (synthetic): one
# missed promise (claimable), one on time, one still in transit — the live
# tracker's package (see commerce.get_delivery_tracker for its van telemetry).
_SCAN_FEED: list[dict] = [
    {
        "order_id": "113-8675309-2401984",
        "carrier": "Amazon Logistics (AMZL)",
        "tracking_number": "TBA3094827731",
        "promised_at": "Yesterday, 2:04 PM",
        "delivered_at": "Yesterday, 4:36 PM",
        "delay_minutes": 152,
        "items": [
            "Eco-Clean Plant-Based Laundry Pods (80 ct)",
            "Amazon Basics Paper Towels (12 rolls)",
        ],
    },
    {
        "order_id": "114-2201437-7783052",
        "carrier": "Amazon Logistics (AMZL)",
        "tracking_number": "TBA3094827018",
        "promised_at": "Yesterday, 9:00 PM",
        "delivered_at": "Yesterday, 2:15 PM",
        "delay_minutes": 0,
        "items": ["Organic Arabica Whole Bean Coffee (2 lb)"],
    },
    {
        "order_id": "112-9051749-3922417",
        "carrier": "Amazon Logistics (AMZL)",
        "tracking_number": "TBA3094829104",
        "promised_at": "Today, 8:30 PM",
        "delivered_at": None,
        "delay_minutes": 0,
        "status": "in_transit",
        "items": [
            "Organic Arabica Whole Bean Coffee (2 lb)",
            "Eco-Clean Plant-Based Laundry Pods (80 ct)",
        ],
    },
]

ACTIVE_CLAIM_STATES = ("pending", "approved")


def qualifies(delay_minutes) -> bool:
    """Prime courtesy-credit rule: a promised-time miss of >= 2h qualifies."""
    try:
        dm = int(delay_minutes)
    except (TypeError, ValueError):
        return False
    return dm >= LATE_THRESHOLD_MIN


def _delay_label(minutes: int) -> str:
    h, m = divmod(int(minutes), 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


def _claims_path() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    p = STATE_DIR / "delivery_claims.json"
    if not p.exists():
        p.write_text("[]")
    return p


def _load_claims() -> list[dict]:
    try:
        items = json.loads(_claims_path().read_text())
    except Exception:
        return []
    if not isinstance(items, list):
        return []
    return [it for it in items if isinstance(it, dict)]


def _proposal_status(pid: str) -> str:
    prop = proposals.get_proposal(str(pid or ""))
    return str((prop or {}).get("status", "missing"))


def _claim_view(record: dict) -> dict:
    """Claim record + live proposal status (status is derived, never stored twice)."""
    out = dict(record)
    out["status"] = _proposal_status(str(out.get("proposal_id", "")))
    return out


def _claim_for(order_id: str) -> dict | None:
    for c in _load_claims():
        if c.get("order_id") == order_id:
            return _claim_view(c)
    return None


def scan() -> dict:
    """Scan the carrier feed: per-delivery SLA verdict + live claim state. Pure read."""
    deliveries: list[dict] = []
    claimable: list[str] = []
    late_count = 0
    for row in _SCAN_FEED:
        d = dict(row)
        dm = int(d.get("delay_minutes", 0) or 0)
        d["delay_label"] = _delay_label(dm) if dm else ""
        d["late"] = qualifies(dm)
        d["eligible"] = d["late"]
        claim = _claim_for(str(d.get("order_id", "")))
        d["claim"] = claim
        d["claimed"] = bool(claim and claim.get("status") in ACTIVE_CLAIM_STATES)
        if d["late"]:
            late_count += 1
            if not d["claimed"]:
                claimable.append(str(d.get("order_id", "")))
        deliveries.append(d)
    return {
        "ok": True,
        "sandbox": True,
        "data_source": DATA_SOURCE,
        "sla_rule": SLA_RULE,
        "credit_usd": CREDIT_USD,
        "threshold_min": LATE_THRESHOLD_MIN,
        "deliveries": deliveries,
        "late_count": late_count,
        "claimable_order_ids": claimable,
        "claimable_count": len(claimable),
    }


def pick_claimable(scan_result: dict | None = None) -> dict | None:
    """First claimable late delivery (eligible, no active claim), else None."""
    s = scan_result if isinstance(scan_result, dict) else scan()
    for d in s.get("deliveries", []):
        if d.get("eligible") and not d.get("claimed"):
            return d
    return None


def proposal_fields(delivery: dict) -> dict:
    """Pure: carrier-feed delivery -> actions_propose fields for the $5 claim.

    The credit is a one-off (not a recurring cost change), so ``cost_delta_yr``
    stays 0.0 and the amount travels in ``meta.credit_usd``: no "/yr" suffix
    ever leaks onto a one-time credit, and the receipt renders it as money
    earned, never as an extra cost.
    """
    dm = int(delivery.get("delay_minutes", 0) or 0)
    label = str(delivery.get("delay_label") or _delay_label(dm))
    order = str(delivery.get("order_id", ""))
    return {
        "kind": "delivery_credit_claim",
        "title": f"Claim ${CREDIT_USD:.2f} courtesy credit — Prime delivery slipped {label}",
        "reasons": (
            f"Order {order} ({delivery.get('carrier', 'AMZL')} · {delivery.get('tracking_number', '')}) "
            f"was promised {delivery.get('promised_at', '?')} and arrived {delivery.get('delivered_at', '?')} — "
            f"{label} past the promised time. {SLA_RULE}. Approving files the claim; the "
            f"${CREDIT_USD:.2f} credit lands in your ledger with a hash-chained receipt. "
            f"Nothing is filed without your tap."
        ),
        "cost_delta_yr": 0.0,
        "risk_level": "low",
        "diff": (
            f"Promised {delivery.get('promised_at', '?')} -> Delivered {delivery.get('delivered_at', '?')} "
            f"({label} late) · +${CREDIT_USD:.2f} courtesy credit"
        ),
        "meta": {
            "claim_type": "prime_late_delivery_courtesy",
            "order_id": order,
            "carrier": delivery.get("carrier", ""),
            "tracking_number": delivery.get("tracking_number", ""),
            "promised_at": delivery.get("promised_at", ""),
            "delivered_at": delivery.get("delivered_at", ""),
            "delay_minutes": dm,
            "delay_label": label,
            "credit_usd": float(CREDIT_USD),
            "sla_rule": SLA_RULE,
        },
    }


def register_claim(order_id: str, proposal_id: str) -> dict:
    """Record (one per order) that ``order_id``'s claim was staged as ``proposal_id``."""
    p = _claims_path()
    with atomic.locked(p):
        claims = _load_claims()
        record = {
            "order_id": str(order_id),
            "proposal_id": str(proposal_id),
            "credit_usd": float(CREDIT_USD),
            "staged_at": int(time.time()),
        }
        claims = [c for c in claims if c.get("order_id") != record["order_id"]] + [record]
        atomic.atomic_write_text(p, json.dumps(claims, indent=2))
    return record


def stage_claim(order_id: str | None = None) -> dict:
    """Stage (idempotently) the $5 courtesy-credit claim for a late delivery.

    One open claim per order, ever: a pending/approved claim is returned as
    ``already`` instead of staging a second. This is the direct API path (used
    by the landing simulator); the planner path stages through
    ``actions_propose`` so the Sentinel child guardrail applies to it.
    """
    s = scan()
    if order_id:
        target = next((d for d in s["deliveries"] if d.get("order_id") == order_id), None)
        if target is None:
            return {"ok": False, "error": f"Order '{order_id}' is not in the carrier scan feed."}
        if target["claimed"]:
            claim = target["claim"] or {}
            return {
                "ok": True, "already": True, "delivery": target,
                "proposal": proposals.get_proposal(str(claim.get("proposal_id", ""))),
                "claim": claim,
            }
        if not target["eligible"]:
            error = ("That delivery is still in transit — nothing to claim yet."
                     if target.get("status") == "in_transit"
                     else "That delivery landed on time — nothing to claim.")
            return {"ok": False, "delivery": target, "error": error}
    else:
        target = pick_claimable(s)
        if target is None:
            existing = next((d for d in s["deliveries"] if d.get("claimed") and d.get("claim")), None)
            if existing:
                claim = existing["claim"] or {}
                return {
                    "ok": True, "already": True, "delivery": existing,
                    "proposal": proposals.get_proposal(str(claim.get("proposal_id", ""))),
                    "claim": claim,
                }
            return {"ok": False, "error": "No late Prime deliveries in the scan window — nothing to claim."}

    p = _claims_path()
    with atomic.locked(p):
        claims = _load_claims()
        active = next(
            (c for c in claims
             if c.get("order_id") == str(target["order_id"])
             and _proposal_status(c.get("proposal_id", "")) in ACTIVE_CLAIM_STATES),
            None,
        )
        if active:
            return {
                "ok": True, "already": True, "delivery": target,
                "proposal": proposals.get_proposal(str(active.get("proposal_id", ""))),
                "claim": _claim_view(active),
            }
        prop = proposals.propose(**proposal_fields(target))
        record = {
            "order_id": str(target["order_id"]),
            "proposal_id": str(prop.get("id", "")),
            "credit_usd": float(CREDIT_USD),
            "staged_at": int(time.time()),
        }
        claims = [c for c in claims if c.get("order_id") != record["order_id"]] + [record]
        atomic.atomic_write_text(p, json.dumps(claims, indent=2))
    return {"ok": True, "already": False, "delivery": target, "proposal": prop, "claim": _claim_view(record)}


def list_claims() -> list[dict]:
    """All claim records with live proposal status (oldest first)."""
    return [_claim_view(c) for c in _load_claims()]


def clear_claims() -> dict:
    """Wipe the claims ledger (demo reset). Proposals are cleared separately."""
    p = _claims_path()
    with atomic.locked(p):
        atomic.atomic_write_text(p, "[]")
    return {"ok": True, "cleared": True}
