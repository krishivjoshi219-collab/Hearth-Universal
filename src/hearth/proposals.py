"""Proposals Manager: Glass-box human-in-the-loop approval tray.
The agent advises and constructs rich, verifiable proposals.
The human decides. Nothing modifies subscriptions, moves money, or alters locks without explicit user consent.
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path
from . import commerce

STATE_DIR = Path(os.environ.get("HEARTH_STATE_DIR", "state"))


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
    p = _path()
    try:
        items = json.loads(p.read_text())
    except Exception:
        items = []

    now = int(time.time())
    pid = f"p{now % 1000000}_{len(items) + 1}"
    item = {
        "id": pid,
        "kind": kind,
        "title": title,
        "reasons": reasons,
        "cost_delta_yr": cost_delta_yr,
        "risk_level": risk_level,
        "diff": diff or reasons,
        "meta": meta or {},
        "status": "pending",
        "ts": now,
        "decided_at": None,
    }
    items.append(item)
    p.write_text(json.dumps(items, indent=2))
    return item


def list_proposals(status: str | None = None) -> list[dict]:
    """Retrieve proposals from persistent state, optionally filtered by status."""
    try:
        items = json.loads(_path().read_text())
        if status:
            return [it for it in items if it.get("status") == status]
        return items
    except Exception:
        return []


def get_proposal(pid: str) -> dict | None:
    """Get a single proposal by ID."""
    items = list_proposals()
    for it in items:
        if it["id"] == pid:
            return it
    return None


def decide(pid: str, approved: bool) -> dict:
    """Record human approval or rejection of an action proposal.
    Executes post-approval side effect if approved.
    """
    p = _path()
    try:
        items = json.loads(p.read_text())
    except Exception:
        items = []

    for it in items:
        if it["id"] == pid:
            it["status"] = "approved" if approved else "rejected"
            it["decided_at"] = int(time.time())
            p.write_text(json.dumps(items, indent=2))
            
            # Post-decision execution triggers
            if approved:
                _execute_approved_action(it)
            return it
            
    return {"ok": False, "error": f"Proposal '{pid}' not found"}


def _execute_approved_action(proposal: dict) -> None:
    """Execute authorized action after human green-light."""
    kind = proposal.get("kind", "")
    meta = proposal.get("meta", {})
    if kind == "home_scene":
        from . import home_mock
        scene_name = meta.get("scene", "evening-calm")
        home_mock.set_scene(scene_name)
    elif kind == "home_lock":
        from . import home_mock
        lock_status = meta.get("locked", True)
        home_mock.toggle_lock(door="front_door", locked=lock_status)


def clear_proposals() -> dict:
    """Clear proposal list for fresh testing."""
    p = _path()
    p.write_text("[]")
    return {"ok": True}
