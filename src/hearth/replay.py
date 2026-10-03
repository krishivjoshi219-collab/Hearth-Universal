"""Agent time-travel debugger: read-only replay of any tray decision.

Reconstructs WHY a proposal exists, WHAT decided it, and HOW to reverse it —
from the proposal record + Merkle audit chain. Never mutates state.
"""
from __future__ import annotations
import json
from typing import Any

from . import audit, proposals


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
        trail = [{"ts": prop["ts"], "actor": "agent",
                  "action": "proposal_staged",
                  "hash": None}] + trail
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
