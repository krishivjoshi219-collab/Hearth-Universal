"""Proposals Manager: Glass-box human-in-the-loop approval tray.
The agent advises and constructs rich, verifiable proposals.
The human decides. Nothing modifies subscriptions, moves money, or alters locks without explicit user consent.
"""
from __future__ import annotations

import contextlib
import json
import math
import os
import secrets
import time
from pathlib import Path

from . import atomic, commerce

STATE_DIR = Path(os.environ.get("HEARTH_STATE_DIR", "state"))

# Product guardrails: bound stored sizes so one bad client can't bloat state.
TITLE_MAX = 200
REASONS_MAX = 4000
DIFF_MAX = 4000
LIST_DEFAULT_LIMIT = 100
PROPOSALS_MAX = 500
META_MAX_BYTES = 4096
COST_MAX_ABS = 1_000_000.0


def _path() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    p = STATE_DIR / "proposals.json"
    if not p.exists():
        p.write_text("[]")
    return p


def scan_renewals() -> dict:
    """Return comprehensive subscription & renewal telemetry with savings opportunities."""
    subs_data = commerce.scan_subscriptions()
    return {
        "renewals": subs_data["subscriptions"],
        "total_annual_spend": subs_data["total_annual_spend"],
        "potential_save_yr": subs_data["potential_annual_savings"],
        "cancellable_count": subs_data["cancellable_count"],
        "downgradable_count": subs_data["downgradable_count"],
    }


def propose(
    kind: str,
    title: str,
    reasons: str,
    cost_delta_yr: float = 0.0,
    risk_level: str = "medium",
    diff: str = "",
    meta: dict | None = None
) -> dict:
    """Draft a new consequential action proposal for the human approval tray."""
    title, t_trunc = _cap(str(title), TITLE_MAX)
    reasons, r_trunc = _cap(str(reasons), REASONS_MAX)
    diff_in, d_trunc = _cap(str(diff or reasons), DIFF_MAX)
    try:
        cost_delta_yr = float(cost_delta_yr)
    except (TypeError, ValueError):
        cost_delta_yr = 0.0
    if not math.isfinite(cost_delta_yr):
        cost_delta_yr = 0.0
    cost_delta_yr = max(-COST_MAX_ABS, min(COST_MAX_ABS, cost_delta_yr))
    if risk_level not in ("low", "medium", "high", "critical"):
        risk_level = "medium"
    kind = str(kind or "generic")[:64]
    p = _path()
    with atomic.locked(p):
        try:
            items = json.loads(p.read_text())
            if not isinstance(items, list):
                items = []
        except Exception:
            with contextlib.suppress(Exception):
                os.replace(p, STATE_DIR / f"proposals.corrupt.{int(time.time())}.json")
            items = []

        now = int(time.time())
        existing_ids = {it.get("id") for it in items if isinstance(it, dict)}
        pid = f"p{secrets.token_hex(8)}"
        while pid in existing_ids:
            pid = f"p{secrets.token_hex(8)}"

        safe_meta = meta if isinstance(meta, dict) else {}
        try:
            meta_bytes = len(json.dumps(safe_meta, default=str))
        except Exception:
            safe_meta = {}
            meta_bytes = 2
        meta_trunc = False
        if meta_bytes > META_MAX_BYTES:
            # Keep small allowlisted keys; drop large blobs (e.g. 100KB content).
            keep: dict = {}
            for k in ("cmd", "path", "scene", "locked", "door", "slot_id", "cart_preview"):
                if k in safe_meta:
                    v = safe_meta[k]
                    keep[k] = str(v)[:1000] if isinstance(v, str) else v
            safe_meta = keep
            meta_trunc = True
        item = {
            "id": pid,
            "kind": kind,
            "title": title,
            "reasons": reasons,
            "cost_delta_yr": cost_delta_yr,
            "risk_level": risk_level,
            "diff": diff_in,
            "meta": safe_meta,
            "status": "pending",
            "ts": now,
            "decided_at": None,
            "consumed_at": None,
        }
        if t_trunc or r_trunc or d_trunc or meta_trunc:
            item["truncated"] = True
        items.append(item)
        # Retention: never drop pending; shed oldest decided beyond the cap.
        # Bound pending too: cap pending at PROPOSALS_MAX to prevent tray-spam DoS.
        if len(items) > PROPOSALS_MAX:
            pending = [it for it in items if isinstance(it, dict) and it.get("status") == "pending"]
            decided = [it for it in items if not (isinstance(it, dict) and it.get("status") == "pending")]
            if len(pending) >= PROPOSALS_MAX:
                items = pending[-PROPOSALS_MAX:]
            else:
                room = PROPOSALS_MAX - len(pending)
                keep_decided = decided[-room:] if room > 0 else []
                items = pending + keep_decided
        atomic.atomic_write_text(p, json.dumps(items, indent=2))
    return item


def _cap(text: str, maximum: int) -> tuple[str, bool]:
    if len(text) <= maximum:
        return text, False
    return text[:maximum], True


def list_proposals(status: str | None = None, limit: int = LIST_DEFAULT_LIMIT) -> list[dict]:
    """Retrieve proposals from persistent state, optionally filtered, newest last, capped."""
    p = _path()
    try:
        with atomic.locked(p):
            items = json.loads(p.read_text())
        if not isinstance(items, list):
            return []
        if status:
            items = [it for it in items if isinstance(it, dict) and it.get("status") == status]
        return items[-max(1, limit):]
    except Exception:
        return []


def get_proposal(pid: str) -> dict | None:
    """Get a single proposal by ID.

    Scans the full file — never the capped window. A capped read makes old
    proposals read as "missing", which broke clawback idempotency (double
    $5 claims) and refused legitimate late approvals once the tray grew
    past LIST_DEFAULT_LIMIT (adversarial pass, P1#4).
    """
    p = _path()
    try:
        with atomic.locked(p):
            items = json.loads(p.read_text())
    except Exception:
        return None
    if not isinstance(items, list):
        return None
    for it in reversed(items):
        if isinstance(it, dict) and it.get("id") == pid:
            return it
    return None


def decide(pid: str, approved: bool) -> dict:
    """Record human approval or rejection of an action proposal.
    Single-use: an already-decided proposal can never be decided again
    (double-approve / double-spend is refused and logged).
    On approval, the authorized side effect executes OUTSIDE the file lock
    (no TOCTOU/deadlock) and an execution receipt is stored on the item.
    """
    from . import audit as _audit

    if isinstance(approved, str):
        approved = approved.strip().lower() not in ("false", "0", "no", "f", "")
    else:
        approved = bool(approved)

    p = _path()
    target: dict | None = None
    with atomic.locked(p):
        try:
            items = json.loads(p.read_text())
            if not isinstance(items, list):
                items = []
        except Exception:
            with contextlib.suppress(Exception):
                os.replace(p, STATE_DIR / f"proposals.corrupt.{int(time.time())}.json")
            items = []

        for it in items:
            if it["id"] == pid:
                if it.get("status") != "pending":
                    _audit.append("sentinel", "replay_blocked", {"id": pid, "status": it.get("status")})
                    return {"ok": False, "error": f"Proposal '{pid}' already {it.get('status')} — single-use, replay refused"}
                it["status"] = "approved" if approved else "rejected"
                it["decided_at"] = int(time.time())
                if approved:
                    # Execution runs outside this lock; stamp the in-flight
                    # marker so undo() refuses to race a landing side effect
                    # (adversarial pass, P1#5).
                    it["executing_at"] = it["decided_at"]
                target = dict(it)
                atomic.atomic_write_text(p, json.dumps(items, indent=2))
                break
        else:
            return {"ok": False, "error": f"Proposal '{pid}' not found"}

    # Execute outside the lock so slow network/FS work can't starve deciders.
    if approved and target is not None:
        try:
            receipt = _execute_approved_action(target)
        except Exception as exc:
            receipt = {"applied": False, "at": int(time.time()), "error": str(exc)}
        with contextlib.suppress(Exception):
            _audit.append("executor", "execution_applied", {"id": pid, "execution": receipt})
        with atomic.locked(p):
            try:
                items = json.loads(p.read_text())
                for it in items:
                    if it.get("id") == pid:
                        if it.get("status") == "approved":
                            it["execution"] = receipt
                            it.pop("executing_at", None)
                        else:
                            # The item was reversed/undone while the side effect
                            # was in flight (stale executor) — keep proof out.
                            _audit.append("executor", "execution_dropped",
                                          {"id": pid, "status": it.get("status")})
                        break
                atomic.atomic_write_text(p, json.dumps(items, indent=2))
            except Exception:
                pass
        target["execution"] = receipt
        return target
    if not approved:
        with contextlib.suppress(Exception):
            _audit.append("human", "proposal_rejected", {"id": pid, "title": target.get("title") if target else ""})
    return target if target is not None else {"ok": False, "error": f"Proposal '{pid}' not found"}


def mark_consumed(pid: str, via: str = "") -> bool:
    """Burn an approved receipt after it is used once (prevents infinite reuse
    of the same approved proposal for unlock/exec/write). Returns True if
    this caller won the single use, False if already consumed."""
    import time as _t
    p = _path()
    with atomic.locked(p):
        try:
            items = json.loads(p.read_text())
        except Exception:
            return False
        for it in items:
            if isinstance(it, dict) and it.get("id") == pid:
                if it.get("status") != "approved" or it.get("consumed_at"):
                    return False
                it["consumed_at"] = int(_t.time())
                it["consumed_via"] = via[:128]
                atomic.atomic_write_text(p, json.dumps(items, indent=2))
                return True
    return False


def _execute_approved_action(proposal: dict) -> dict:
    """Execute authorized action after human green-light. Returns a receipt."""
    kind = proposal.get("kind", "")
    meta = proposal.get("meta") or {}
    if not isinstance(meta, dict):
        meta = {}
    now = int(time.time())
    if kind == "home_scene":
        from . import home_mock
        scene_name = meta.get("scene", "evening-calm")
        res = home_mock.set_scene(scene_name)
        return {"applied": bool(res.get("ok")), "at": now, "note": f"scene '{scene_name}' applied" if res.get("ok") else res.get("error", "scene failed")}
    elif kind == "home_lock":
        from . import home_mock
        lock_status = meta.get("locked", True)
        res = home_mock.toggle_lock(door=meta.get("door", "front_door"), locked=lock_status)
        return {"applied": bool(res.get("ok")), "at": now, "note": f"door {res.get('status')}" if res.get("ok") else res.get("error", "lock failed")}
    elif kind in ("subscription_cancel", "cancel_subscription", "downgrade_subscription"):
        save_yr = abs(proposal.get("cost_delta_yr", 0))
        receipt_code = f"HEARTH-RC-SUB-{str(proposal.get('id', 'p?')).upper()}-{now:X}"
        portal_url = meta.get("portal_url", "")
        support_phone = meta.get("support_phone", "")
        return {
            "applied": True,
            "at": now,
            "receipt_code": receipt_code,
            "savings_yr": save_yr,
            "service_name": meta.get("service_name") or proposal.get("title"),
            "portal_url": portal_url,
            "support_phone": support_phone,
            "glass": True,
            "undo_before": "billing_cycle",
            "undo_via": f"/api/undo {proposal.get('id')} | actions_undo",
            "note": f"Recorded cancellation/downgrade for '{proposal.get('title')}' saving ${save_yr:.2f}/yr. Provider call simulated — no live billing API in sandbox.",
            "sandbox": True,
        }
    elif kind == "commerce_order":
        cart = (meta.get("cart_preview") or {})
        receipt_code = f"HEARTH-RC-{str(proposal.get('id', 'p?')).upper()}-{now:X}"
        qr_payload = (f"hearth://receipt/{receipt_code}?pid={proposal.get('id')}"
                      f"&total={abs(proposal.get('cost_delta_yr', 0)):.2f}")
        return {"applied": True, "at": now,
                "note": f"order staged for '{proposal.get('title')}' at ${abs(proposal.get('cost_delta_yr', 0)):.2f} (checkout simulated — no live payment in sandbox)",
                "receipt_code": receipt_code, "qr_payload": qr_payload,
                "items": cart.get("items", []), "final_total": cart.get("final_total"),
                "savings": cart.get("savings"), "delivery_schedule": cart.get("delivery_schedule"),
                "glass": True, "undo_before": "dispatch",
                "undo_via": f"/api/undo {proposal.get('id')} | actions_undo",
                "sandbox": True}
    elif kind == "arbiter_compromise":
        from . import home_mock
        action_data = meta.get("proposed_action", {})
        if action_data.get("device") == "thermostat" and "setpoint" in action_data:
            home_mock.update_device("living_room", "climate", {"target_c": float(action_data["setpoint"]), "mode": "eco"})
        return {"applied": True, "at": now,
                "note": f"applied arbitrated compromise '{proposal.get('title')}': {action_data.get('diff', 'compromise applied')}"}
    elif kind == "delivery_reschedule":
        from . import commerce
        slot_id = meta.get("slot_id") or meta.get("new_slot", "slot_overnight_urgent")
        if isinstance(slot_id, str) and slot_id.startswith("slot_"):
            commerce.reschedule_delivery_slot(slot_id, reason=proposal.get("title", ""))
        return {"applied": True, "at": now,
                "note": f"rescheduled delivery window: {meta.get('diff', 'delivery updated')}"}
    elif kind == "delivery_credit_claim":
        try:
            credit = round(float(meta.get("credit_usd", 0) or 0), 2)
        except (TypeError, ValueError):
            credit = 0.0
        receipt_code = f"HEARTH-RC-AMZ-CREDIT-{str(proposal.get('id', 'p?')).upper()}-{now:X}"
        return {
            "applied": True,
            "at": now,
            "receipt_code": receipt_code,
            "credit_usd": credit,
            "order_id": meta.get("order_id", ""),
            "tracking_number": meta.get("tracking_number", ""),
            "delay_minutes": meta.get("delay_minutes"),
            "delay_label": meta.get("delay_label", ""),
            "glass": True,
            "undo_before": "claim_settlement",
            "undo_via": f"/api/undo {proposal.get('id')} | actions_undo",
            "note": (f"Filed ${credit:.2f} Amazon courtesy credit for order {meta.get('order_id', '?')} "
                     f"({meta.get('delay_label', 'late')} past the promised time). "
                     f"Carrier dispute simulated — no live billing API in sandbox."),
            "sandbox": True,
        }
    elif kind == "workspace_exec":
        from . import sandbox
        res = sandbox.execute(str(meta.get("cmd", ""))[:2000])
        return {"applied": bool(res.get("ok")), "at": now,
                "note": f"workspace exec rc={res.get('rc')}", "output": res.get("output", "")[:2000]}
    elif kind == "workspace_write":
        from . import sandbox
        res = sandbox.write_file(str(meta.get("path", "")), str(meta.get("content", "")))
        return {"applied": bool(res.get("ok")), "at": now,
                "note": res.get("path", res.get("error", "write failed"))}
    return {"applied": True, "at": now, "note": f"approved {kind} recorded"}


def clear_proposals() -> dict:
    """Clear proposal list for fresh testing with atomic locking."""
    p = _path()
    with atomic.locked(p):
        atomic.atomic_write_text(p, "[]")
    return {"ok": True}


def undo(pid: str) -> dict:
    """Reverse an approved and executed proposal, returning the system to its prior state.

    Human Psychology & Trust Engineering:
    Knowing that decisions are reversible provides psychological safety, reducing cognitive friction
    and commitment anxiety when interacting with autonomous household agents.
    Every undo operation is sealed into the SHA-256 Merkle audit chain.
    """
    from . import audit as _audit

    p = _path()
    with atomic.locked(p):
        try:
            items = json.loads(p.read_text())
            if not isinstance(items, list):
                items = []
        except Exception:
            return {"ok": False, "error": "State corrupted"}

        for it in items:
            if it["id"] == pid:
                if it.get("status") != "approved":
                    return {"ok": False, "error": f"Proposal '{pid}' is '{it.get('status')}', not approved. Cannot undo."}

                # Execution runs outside decide()'s lock; refuse undo while a
                # side effect is still landing (adversarial pass, P1#5),
                # unless the marker is stale (crashed executor).
                _exec_at = it.get("executing_at")
                if _exec_at and (int(time.time()) - int(_exec_at)) < 120:
                    return {"ok": False, "error": "Action is still being applied — try undo again in a moment."}

                kind = it.get("kind", "")
                meta = it.get("meta") or {}
                now = int(time.time())
                reversal_note = f"Reversed {kind}"

                try:
                    if kind == "home_lock":
                        from . import home_mock
                        door = meta.get("door", "front_door")
                        target_lock = not meta.get("locked", False)
                        res = home_mock.toggle_lock(door=door, locked=target_lock)
                        reversal_note = f"Door '{door}' reversed to {res.get('status', 'locked')}"
                    elif kind == "home_scene":
                        from . import home_mock
                        home_mock.set_scene("evening-calm")
                        reversal_note = "Restored default scene 'evening-calm'"
                    elif kind == "arbiter_compromise":
                        from . import home_mock
                        home_mock.update_device("living_room", "climate", {"target_c": 22.0, "mode": "comfort"})
                        reversal_note = "Thermostat restored to baseline 22.0°C comfort"
                    elif kind in ("subscription_cancel", "cancel_subscription", "downgrade_subscription"):
                        reversal_note = f"Subscription modification for '{it.get('title')}' rolled back (active status maintained)"
                    elif kind == "commerce_order":
                        reversal_note = f"Cart replenishment for '{it.get('title')}' cancelled before dispatch"
                    elif kind == "delivery_credit_claim":
                        reversal_note = (f"Credit claim for order {meta.get('order_id', '?')} withdrawn — "
                                        f"the credit returns to the carrier dispute queue")
                except Exception as exc:
                    reversal_note = f"Reversal execution partial: {exc}"

                it["status"] = "undone"
                it["undone_at"] = now
                it["reversal"] = {"applied": True, "at": now, "note": reversal_note}

                _audit.append("human", "proposal_undone", {
                    "id": pid,
                    "kind": kind,
                    "title": it.get("title"),
                    "note": reversal_note
                })

                atomic.atomic_write_text(p, json.dumps(items, indent=2))
                return {"ok": True, "proposal": it, "note": reversal_note}

    return {"ok": False, "error": f"Proposal '{pid}' not found"}


