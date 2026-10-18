"""Agent time-travel debugger: read-only replay of any tray decision.

Reconstructs WHY a proposal exists, WHAT decided it, and HOW to reverse it —
from the proposal record + Merkle audit chain. Never mutates state.

Also serves the household day-replay (Pillar 3): the last N hours rebuilt from
the ledger as hourly frames with narration, money, and jump markers.
"""
from __future__ import annotations

import json
import time
from typing import Any

from . import audit, proposals, receipts


def _audit_entries_for(pid: str, limit: int = 200) -> list[dict[str, Any]]:
    path = audit._log_path()
    if not path.exists():
        return []
    try:
        lines = path.read_text().strip().splitlines()
    except Exception:
        return []
    hits: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            e = json.loads(line)
        except Exception:
            continue
        if not isinstance(e, dict):
            continue
        blob = json.dumps(e.get("detail", {}), default=str)
        if pid in blob or pid in str(e.get("action", "")):
            hits.append({"ts": e.get("ts"), "actor": e.get("actor"),
                         "action": e.get("action"), "hash": e.get("hash")})
    return hits


def _why_context(prop: dict) -> dict[str, Any]:
    """Decode the decision-driving numbers from proposal meta per kind."""
    meta = prop.get("meta") or {}
    kind = prop.get("kind", "")
    ctx: dict[str, Any] = {"kind": kind}
    try:
        if kind == "parliament_consensus":
            pc = meta.get("pareto_compromise", {})
            ctx.update({"nash": pc.get("nash_equilibrium_score"),
                        "utilities": pc.get("utilities"),
                        "vote": "unanimous" if len(
                            pc.get("unanimous_votes", [])) == 3 else "majority"})
        elif kind == "causal_contingency":
            ctx.update({"plans": [p.get("title") for p in
                                  meta.get("contingency_plans", [])]})
        elif kind == "household_treaty_ratification":
            ctx.update({"fairness": meta.get("fairness_index"),
                        "covenants": meta.get("covenants_count")})
        elif kind == "commerce_order":
            cart = meta.get("cart_preview", {})
            ctx.update({"total": cart.get("final_total"),
                        "savings": cart.get("savings"),
                        "items": len(cart.get("items", []))})
            if prop.get("execution"):
                ctx.update({"receipt": prop["execution"].get("receipt_code")})
        elif kind in ("cancel_subscription", "downgrade_subscription"):
            ctx.update({"yearly_delta": prop.get("cost_delta_yr")})
        elif kind == "appliance_predictive_repair":
            ctx.update({"degradation": (meta.get("degradation_index"))})
    except Exception:
        pass
    return ctx


def replay_decision(pid: str) -> dict[str, Any]:
    """Read-only time-travel: full story of one proposal id."""
    prop = proposals.get_proposal(pid)
    if prop is None:
        return {"ok": False, "error": f"Proposal '{pid}' not found"}
    trail = _audit_entries_for(pid)
    if prop.get("ts"):
        trail = [{"ts": prop["ts"], "actor": "agent", "action": "proposal_staged", "hash": None}, *trail]
    status = prop.get("status")
    return {
        "ok": True,
        "proposal_id": pid,
        "status": status,
        "title": prop.get("title"),
        "kind": prop.get("kind"),
        "reasons": prop.get("reasons"),
        "cost_delta_yr": prop.get("cost_delta_yr"),
        "risk_level": prop.get("risk_level"),
        "staged_at": prop.get("ts"),
        "decided_at": prop.get("decided_at"),
        "why": _why_context(prop),
        "execution": prop.get("execution"),
        "reversal": prop.get("reversal"),
        "audit_trail": trail,
        "chain_valid": audit.verify(),
        "replay_note": ("Undone — reversal recorded" if status == "undone"
                        else "Approved — single-use receipt spent" if status == "approved"
                        else "Rejected by human" if status == "rejected"
                        else "Pending — awaiting your 1-tap decision"),
        "undo_available": status == "approved",
    }


# ---------------------------------------------------------------------------
# Pillar 3: household day replay — the last N hours as hourly frames.
# Everything is read back from the ledger (audit + receipts); nothing is
# recomputed from live state, so the replay cannot drift from history.
# ---------------------------------------------------------------------------

_HOUR = 3600

_NARRATION = {
    "microgrid_dispatch_settled": "sold stored solar into the community VPP",
    "fft_scan_completed": "swept the house for appliance signatures",
    "incident_reconstructed": "rebuilt the night's incident graph",
    "household_treaty_synthesized": "drafted a household treaty",
    "simulation_completed": "ran resilience simulations days ahead",
    "execution_applied": "executed an approved action",
    "actions_propose": "staged new proposals for approval",
    "synthesis_refused_privileged": "refused a privileged rule (Sentinel)",
    "skill_synthesized_and_mounted": "forged and mounted a new MCP tool",
    "forge_tool_applied": "applied a forged MCP tool",
    "user_account_linked_token_granted": "linked accounts",
    "inbox_scan": "scanned the inbox",
    "event_commerce": "watched order events",
}


def _narrate(hour: dict[str, Any]) -> str:
    by_action = hour["by_action"]
    money = hour["money"]
    if not by_action:
        return "All quiet — the house hummed along on autopilot."
    top = max(by_action.items(), key=lambda kv: kv[1])
    phrase = _NARRATION.get(top[0])
    if phrase:
        if top[0] == "microgrid_dispatch_settled":
            kw = hour.get("vpp_kw", 0)
            base = f"Hearth {phrase} — {kw:g} kW across {top[1]} settlements."
        else:
            base = f"Hearth {phrase}" + (f" ×{top[1]}." if top[1] > 1 else ".")
    else:
        base = f"{top[1]} × {top[0].replace('_', ' ')}."
    bits = []
    if money.get("earned_usd"):
        bits.append(f"+${money['earned_usd']:.2f} banked")
    if money.get("saved_usd"):
        bits.append(f"+${money['saved_usd']:.2f} saved")
    if money.get("spent_usd"):
        bits.append(f"−${money['spent_usd']:.2f} spent")
    if bits:
        base = base.rstrip(".") + " — " + ", ".join(bits) + "."
    return base


def day_frames(hours: int = 24) -> dict[str, Any]:
    """Hourly frames for the last `hours` hours, oldest first.

    Each frame: event mix, per-hour money from receipts, a deterministic
    narration line, plus jump markers for safety refusals, the night
    reconstruction, forged tools, and the best hour.
    """
    hours = max(6, min(72, int(hours)))
    now = int(time.time())
    end = (now // _HOUR) * _HOUR
    start = end - (hours - 1) * _HOUR

    buckets: dict[int, dict[str, Any]] = {}
    for i in range(hours):
        ts = start + i * _HOUR
        buckets[ts] = {"ts": ts, "by_action": {}, "events": 0, "vpp_kw": 0.0,
                       "money": {"earned_usd": 0.0, "saved_usd": 0.0, "spent_usd": 0.0}}

    def _bucket(ts: int) -> dict[str, Any] | None:
        return buckets.get((ts // _HOUR) * _HOUR)

    path = audit._log_path()
    marker_sources: list[tuple[int, str, dict]] = []
    if path.exists():
        try:
            lines = path.read_text().splitlines()
        except Exception:
            lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            if not isinstance(e, dict):
                continue
            ts = int(e.get("ts", 0) or 0)
            action = str(e.get("action", ""))
            if ts < start:
                continue
            b = _bucket(ts)
            if b is None:
                continue
            b["events"] += 1
            b["by_action"][action] = b["by_action"].get(action, 0) + 1
            detail = e.get("detail") or {}
            if action == "microgrid_dispatch_settled":
                try:
                    b["vpp_kw"] += float(detail.get("allocated_kw", 0) or 0)
                except Exception:
                    pass
            if action in ("synthesis_refused_privileged", "skill_synthesized_and_mounted",
                          "incident_reconstructed", "forge_tool_applied"):
                marker_sources.append((ts, action, detail))

    # Money per hour from receipts (the same ledger the Proof Engine verifies).
    try:
        for r in receipts._load():
            ts = int(r.get("ts", 0) or 0)
            b = _bucket(ts) if ts else None
            if b is None or ts < start:
                continue
            m = r.get("money") or {}
            for key in ("earned_usd", "saved_usd", "spent_usd"):
                try:
                    b["money"][key] = round(b["money"][key] + float(m.get(key, 0) or 0), 2)
                except Exception:
                    pass
    except Exception:
        pass

    frames = []
    for i in range(hours):
        ts = start + i * _HOUR
        b = buckets[ts]
        frames.append({
            "ts": ts,
            "label": time.strftime("%H:%M", time.localtime(ts)),
            "day": time.strftime("%b %d", time.localtime(ts)),
            "events": b["events"],
            "by_action": dict(sorted(b["by_action"].items(), key=lambda kv: -kv[1])),
            "money": b["money"],
            "narration": _narrate(b),
        })

    # Jump markers: the moments worth scrubbing back to.
    markers: list[dict[str, Any]] = []

    def _frame_idx(ts: int) -> int:
        return max(0, min(hours - 1, (ts - start) // _HOUR))

    marker_sources.sort(key=lambda t: t[0])
    first_refusal = next(((ts, d) for ts, a, d in marker_sources
                          if a == "synthesis_refused_privileged"), None)
    if first_refusal:
        ts, d = first_refusal
        markers.append({"ts": ts, "frame": _frame_idx(ts), "icon": "⚠", "kind": "safety",
                        "label": f"Sentinel refused: {str(d.get('reason') or 'privileged rule')[:64]}"})

    recon = [ts for ts, a, _d in marker_sources if a == "incident_reconstructed"]
    if recon:
        pick = min(recon, key=lambda ts: abs(time.localtime(ts).tm_hour - 3))
        markers.append({"ts": pick, "frame": _frame_idx(pick), "icon": "🔍", "kind": "forensics",
                        "label": f"Reconstruct {time.strftime('%H:%M', time.localtime(pick))} — "
                                 f"rebuilt the night, hypotheses tested"})

    forged = [(ts, d) for ts, a, d in marker_sources if a == "skill_synthesized_and_mounted"]
    if forged:
        ts, d = forged[-1]
        tools = d.get("tools") if isinstance(d.get("tools"), list) else []
        name = tools[0] if tools else str(d.get("name", "tool"))[:48]
        markers.append({"ts": ts, "frame": _frame_idx(ts), "icon": "⚒", "kind": "forge",
                        "label": f"Forged & mounted {name}"})

    best_i, best_v = 0, 0.0
    for i, f in enumerate(frames):
        v = f["money"]["earned_usd"] + f["money"]["saved_usd"]
        if v > best_v:
            best_i, best_v = i, v
    if best_v > 0:
        markers.append({"ts": frames[best_i]["ts"], "frame": best_i, "icon": "💰", "kind": "money",
                        "label": f"Best hour: +${best_v:.2f} banked & saved"})

    totals = {
        "events": sum(f["events"] for f in frames),
        "earned_usd": round(sum(f["money"]["earned_usd"] for f in frames), 2),
        "saved_usd": round(sum(f["money"]["saved_usd"] for f in frames), 2),
        "spent_usd": round(sum(f["money"]["spent_usd"] for f in frames), 2),
    }
    return {
        "hours": hours,
        "generated_at": now,
        "window": {"start_ts": start, "end_ts": end},
        "frames": frames,
        "markers": markers,
        "total": totals,
    }
