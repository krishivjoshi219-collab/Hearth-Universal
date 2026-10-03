"""B1 DAG planner_orchestrate: multi-step DAG + cross-session state + media-card JSON.

Zero-config local fallback: file-backed sessions in HEARTH_STATE_DIR,
no keys required. Gating: unlock/order paths return approval_required
via propose-never-execute (never executes directly).
"""
from __future__ import annotations
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from . import atomic


def _state_dir() -> Path:
    return Path(os.environ.get("HEARTH_STATE_DIR", "state"))


def _sessions_file() -> Path:
    return _state_dir() / "orchestrations.json"


def _load_all() -> dict:
    p = _sessions_file()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_all(data: dict) -> None:
    d = _state_dir()
    d.mkdir(parents=True, exist_ok=True)
    with atomic.locked(_sessions_file()):
        atomic.atomic_write_text(_sessions_file(), json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# DAG decomposition (keyword router, deterministic offline)
# ---------------------------------------------------------------------------

def decompose_goal(goal: str) -> dict:
    """Decompose a goal into a multi-step DAG with explicit depends_on edges."""
    low = (goal or "").lower()
    nodes: list[dict] = []

    def add(tool: str, args: dict, deps: list[str], why: str) -> str:
        nid = f"step_{len(nodes) + 1}"
        nodes.append({"id": nid, "tool": tool, "args": args,
                      "depends_on": list(deps), "why": why, "status": "pending"})
        return nid

    if any(k in low for k in ("light", "cct", "rgb", "mood", "designer", "wheel")):
        a = add("home_get_state", {}, [], "read twin telemetry first")
        b = add("mcp_app_lighting_designer", {"room": "living_room"}, [a],
                "design lighting from live state")
        add("home_set_scene", {"name": "evening-calm"}, [b],
            "apply ambient scene after design")
        intent = "LIGHTING_DESIGN"
        media_kind = "lighting_designer"
    elif any(k in low for k in ("subscription", "roi", "save", "renew", "bill", "$", "budget")):
        a = add("memory_query", {"q": "budget"}, [], "load spend constraints")
        b = add("inbox_scan", {}, [a], "audit subscriptions")
        c = add("commerce_scan_deals", {}, [b], "match bundle discounts")
        add("mcp_app_subscription_roi", {}, [c], "render ROI optimizer card")
        intent = "SUBSCRIPTION_ROI"
        media_kind = "subscription_roi"
    elif any(k in low for k in ("checkout", "autopilot", "voice order", "buy it", "check me out", "add to tray")):
        a = add("commerce_list_inventory", {}, [], "read pantry levels")
        b = add("commerce_autopilot_checkout", {"utterance": goal, "bundle_optimized": True}, [a],
                "voice-to-tray staging only")
        add("mcp_app_pantry_restock", {}, [b], "render depletion radar + tray card")
        intent = "AUTOPILOT_CHECKOUT"
        media_kind = "pantry_restock"
    elif any(k in low for k in ("pantry", "restock", "reorder", "coffee", "detergent",
                                "cart", "groc", "subscribe", "deplet")):
        a = add("commerce_list_inventory", {}, [], "read pantry levels")
        b = add("commerce_depletion_forecast", {}, [a], "rank runout urgency")
        add("mcp_app_pantry_restock", {}, [b], "render depletion radar card")
        intent = "PANTRY_RESTOCK"
        media_kind = "pantry_restock"
    elif "unlock" in low or ("open" in low and "door" in low):
        a = add("home_get_state", {}, [], "verify lock state first")
        add("home_toggle_lock", {"door": "front_door", "locked": False}, [a],
            "unlock is GATED: stage approval, never execute")
        intent = "GATED_UNLOCK"
        media_kind = "pantry_restock"
    elif any(k in low for k in ("order", "buy")):
        a = add("commerce_list_inventory", {}, [], "read pantry levels")
        add("actions_propose", {"kind": "commerce_order", "title": "Reorder essentials",
                                "reasons": "agent-requested purchase"},
            [a], "purchases are GATED: stage approval")
        intent = "GATED_ORDER"
        media_kind = "pantry_restock"
    else:
        a = add("memory_query", {"q": ""}, [], "load household facts")
        add("home_get_state", {}, [a], "ground in live telemetry")
        intent = "GENERAL_AGENTIC"
        media_kind = "subscription_roi"

    edges = [(n["id"], d) for n in nodes for d in n["depends_on"]]
    return {"intent": intent, "nodes": nodes, "edges": edges,
            "media_kind": media_kind}


# ---------------------------------------------------------------------------
# Media-card JSON (consumable by web2/js/app.js carousel renderer)
# ---------------------------------------------------------------------------

def build_media_card(kind: str) -> dict:
    """Return {type,title,carousel{items},purchase_action,app_id} for web UI."""
    # Local imports: zero-config, no keys.
    from . import commerce, home_mock
    if kind == "lighting_designer":
        st = {}
        try:
            st = home_mock.get_state().get("living_room", {}).get("lights", {})
        except Exception:
            st = {}
        presets = [
            {"id": "warm", "name": "Warm Candlelight", "temp_k": 2200,
             "bri": 35, "color": "#ff9d42",
             "image": "https://example.com/media/lighting-warm.png"},
            {"id": "focus", "name": "Focus Daylight", "temp_k": 5000,
             "bri": 85, "color": "#f4f8ff",
             "image": "https://example.com/media/lighting-focus.png"},
            {"id": "cyber", "name": "Cyber Ambient", "temp_k": 6500,
             "bri": 60, "color": "#00f0ff",
             "image": "https://example.com/media/lighting-cyber.png"},
            {"id": "cinema", "name": "Cinema Violet", "temp_k": 3000,
             "bri": 40, "color": "#a855f7",
             "image": "https://example.com/media/lighting-cinema.png"},
        ]
        return {
            "type": "media-card",
            "app_id": "mcp_app_lighting_designer",
            "title": "Lighting Designer",
            "subtitle": f"Live: {'on' if st.get('on') else 'off'} @ {st.get('bri', 80)}%",
            "carousel": {"items": [
                {"title": p["name"], "image": p["image"],
                 "meta": f"{p['temp_k']}K · {p['bri']}%",
                 "action": {"tool": "home_set_scene", "args": {"name": "evening-calm"}}}
                for p in presets
            ]},
            "purchase_action": None,
            "hint": "Tap a preset to preview; Apply stages a scene (Tier-1).",
        }
    if kind == "subscription_roi":
        try:
            scan = commerce.scan_subscriptions()
        except Exception:
            scan = {"subscriptions": [], "total_annual_spend": 0.0,
                    "potential_annual_savings": 0.0}
        subs = scan.get("subscriptions", [])[:5]
        items = [{"title": s.get("name", "Service"),
                  "image": "https://example.com/media/sub.png",
                  "meta": f"${s.get('cost_monthly', 0)}/mo · {s.get('recommendation', '')}",
                  "action": {"tool": "actions_propose",
                             "args": {"kind": "cancel_subscription",
                                      "title": f"Cancel {s.get('name', '')}",
                                      "reasons": s.get("reason", "")}}}
                 for s in subs]
        return {
            "type": "media-card",
            "app_id": "mcp_app_subscription_roi",
            "title": "Subscription ROI",
            "subtitle": f"Save ${scan.get('potential_annual_savings', 0)}/yr",
            "carousel": {"items": items},
            "purchase_action": None,
            "hint": "Review dormant services; cancel/downgrade via Approval Tray.",
        }
    # default: pantry_restock
    try:
        forecast = commerce.get_depletion_forecast()[:5]
    except Exception:
        forecast = []
    try:
        cart = commerce.stage_amazon_cart()
    except Exception:
        cart = {"final_total": 0.0, "savings": 0.0, "items": []}
    items = [{"title": f.get("name", "Item"),
              "image": f.get("amazon_url", "https://example.com/media/pantry.png"),
              "meta": f"{f.get('level_pct', 0)}% · {f.get('days_until_empty', 0)}d left",
              "action": {"tool": "actions_propose",
                         "args": {"kind": "commerce_order",
                                  "title": f"Reorder {f.get('name', '')}",
                                  "reasons": "low stock"}}}
             for f in forecast]
    return {
        "type": "media-card",
        "app_id": "mcp_app_pantry_restock",
        "title": "Pantry Restock",
        "subtitle": f"Cart ${cart.get('final_total', 0):.2f} (save ${cart.get('savings', 0):.2f})",
        "carousel": {"items": items},
        "purchase_action": {
            "label": "Autopilot Checkout (voice-to-tray)",
            "tool": "commerce_autopilot_checkout",
            "args": {"utterance": "restock critical pantry items", "bundle_optimized": True},
            "gated": True,
            "note": "approval_required: human must approve in tray; never auto-charges",
        },
        "hint": "1-tap staging only; checkout requires Approval Tray confirm. Say 'checkout coffee and detergent'.",
    }


# ---------------------------------------------------------------------------
# Orchestrated execution with persisted session state
# ---------------------------------------------------------------------------

def _topo_order(nodes: list[dict]) -> list[dict]:
    done: set[str] = set()
    out: list[dict] = []
    remaining = list(nodes)
    guard = 0
    while remaining and guard < 100:
        guard += 1
        progressed = False
        for n in list(remaining):
            if all(d in done for d in n.get("depends_on", [])):
                out.append(n)
                done.add(n["id"])
                remaining.remove(n)
                progressed = True
        if not progressed:  # cycle fallback: append rest in order
            out.extend(remaining)
            break
    return out


def orchestrate(goal: str, session_id: str | None = None) -> dict:
    """Decompose goal -> execute DAG in topo order -> persist session.

    Gating: tools judged by sentinel; tier-2 state-changers (unlock without
    approval, orders, exec/write) return approval_required and stage a
    proposal instead of executing.
    """
    # Lazy imports to avoid circulars at module load.
    from . import planner as _planner
    from . import proposals as _proposals
    from . import sentinel as _sentinel
    from . import audit as _audit

    spec = decompose_goal(goal)
    sid = session_id or f"ses_{uuid.uuid4().hex[:8]}"
    now = time.time()
    dag_trace: list[dict] = []
    results: dict[str, Any] = {}
    gated: list[dict] = []

    for node in _topo_order(spec["nodes"]):
        tool, args = node["tool"], dict(node.get("args", {}))
        v = _sentinel.judge(tool, args)
        if v.decision == "deny":
            node["status"] = "blocked"
            node["result"] = {"ok": False, "error": v.reason}
            dag_trace.append(node)
            _audit.append("agent", tool, {"status": "blocked", "reason": v.reason})
            continue
        if v.decision == "ask" and _planner._requires_approval(tool, args):
            created = _planner._stage_gated_proposal(tool, args)
            node["status"] = "awaiting_approval"
            node["result"] = {"ok": False, "approval_required": True,
                              "proposal": created}
            gated.append(created)
            dag_trace.append(node)
            _audit.append("agent", tool, {"status": "awaiting_approval"})
            continue
        handler = _planner.TOOLS.get(tool, {}).get("handler")
        if not handler:
            node["status"] = "blocked"
            node["result"] = {"ok": False, "error": f"unknown tool {tool}"}
            dag_trace.append(node)
            continue
        try:
            res = handler(args)
        except Exception as e:
            res = {"ok": False, "error": str(e)}
        # Media-app tools: attach rich media-card JSON.
        if tool.startswith("mcp_app_") and isinstance(res, dict):
            kind = {"mcp_app_lighting_designer": "lighting_designer",
                    "mcp_app_subscription_roi": "subscription_roi",
                    "mcp_app_pantry_restock": "pantry_restock"}.get(tool)
            if kind:
                res = dict(res)
                res["media_card"] = build_media_card(kind)
        node["status"] = "completed"
        node["result"] = res
        results[node["id"]] = res
        dag_trace.append(node)
        _audit.append("agent", tool, {"status": "completed"})

    media_card = build_media_card(spec["media_kind"])
    session = {
        "session_id": sid,
        "goal": goal,
        "intent": spec["intent"],
        "dag": dag_trace,
        "edges": spec["edges"],
        "media_card": media_card,
        "gated_proposals": [g.get("id") for g in gated if isinstance(g, dict) and g.get("id")],
        "status": "awaiting_approval" if gated else "completed",
        "created_at": now,
        "updated_at": time.time(),
    }
    # Persist across sessions (merge with existing store).
    try:
        store = _load_all()
        # resume: keep prior history under session["history"]
        prev = store.get(sid, {})
        if prev:
            session["history"] = prev.get("history", []) + [
                {"goal": prev.get("goal"), "status": prev.get("status")}]
        store[sid] = session
        _save_all(store)
    except Exception:
        pass
    # Surface gated signal at top level for propose-never-execute clients.
    if gated:
        session["approval_required"] = True
        session["proposals"] = gated
    # Back-compat for planner_orchestrate clients expecting plan-shaped fields.
    session["draft"] = (f"{spec['intent']}: executed {len(dag_trace)} DAG steps; "
                        f"status={session['status']}. Media card: {media_card.get('title')}.")
    session["model"] = "hearth-dag-v1"
    session["provider"] = "local-agent"
    # Also remember last session pointer for cross-session resume.
    try:
        from . import memory as _memory
        _memory.chat_history_append("user", goal)
    except Exception:
        pass
    return session


def get_session(session_id: str) -> dict:
    store = _load_all()
    s = store.get(session_id)
    if not s:
        return {"ok": False, "error": f"session '{session_id}' not found"}
    return {"ok": True, "session": s}


def list_sessions(limit: int = 20) -> dict:
    store = _load_all()
    items = sorted(store.values(), key=lambda s: s.get("updated_at", 0),
                   reverse=True)[: max(1, limit)]
    return {"ok": True, "count": len(store),
            "sessions": [{"session_id": s.get("session_id"),
                          "goal": s.get("goal"), "intent": s.get("intent"),
                          "status": s.get("status")} for s in items]}
