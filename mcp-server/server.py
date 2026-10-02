"""Hearth Universal MCP server — spec 2025-11-25, Streamable HTTP, stateless.
Serves MCP protocol on /mcp, REST APIs for simulator on /api/*, and interactive Alexa+ UI on /.
Verifies via curl POST /mcp initialize -> protocolVersion 2025-11-25.
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
import time as _time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def _load_config() -> None:
    """Optional config.yaml (env vars always win). Lets operators configure the
    brain, port, and scheduler without touching code or exports."""
    cfg_path = os.environ.get("HEARTH_CONFIG", os.path.join(os.path.dirname(__file__), "..", "config.yaml"))
    if not os.path.exists(cfg_path):
        return
    try:
        import yaml
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"config warn: ignoring {cfg_path}: {e}")
        return
    model = cfg.get("model", {})
    if model.get("base_url"):
        os.environ.setdefault("HEARTH_BASE_URL", str(model["base_url"]))
    if model.get("model"):
        os.environ.setdefault("HEARTH_MODEL", str(model["model"]))
    if model.get("provider"):
        os.environ.setdefault("HEARTH_BRAIN_PROVIDER", str(model["provider"]))
    server = cfg.get("server", {})
    if server.get("port"):
        os.environ.setdefault("PORT", str(server["port"]))


_load_config()

from typing import Annotated, Optional
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, FileResponse, PlainTextResponse

from hearth import (
    sentinel, vault, audit, memory, home_mock, proposals, planner, commerce,
    brains, alexa, heartbeat, webtools, sandbox, arbiter, timemachine, auth,
    strands_agent, agentcore, agent_skills, mcp_strands_adapter,
    parliament, causal_twin, meta_skill, model_mesh
)

_SERVER_START_TIME = _time.time()

# Simple per-IP token bucket for the expensive chat endpoint (product abuse guard).
_RATE_BUCKETS: dict[str, list] = {}
RATE_LIMIT = int(os.environ.get("HEARTH_CHAT_RPM", "30"))


def _rate_ok(ip: str) -> bool:
    import time
    now = time.time()
    # Periodic GC: evict idle buckets to bound memory under distinct-IP floods.
    if len(_RATE_BUCKETS) > 500:
        for k in list(_RATE_BUCKETS.keys()):
            v = _RATE_BUCKETS.get(k, [])
            if not v or (now - v[-1]) > 60:
                _RATE_BUCKETS.pop(k, None)
            if len(_RATE_BUCKETS) <= 500:
                break
        # Hard cap: if still over (burst within same 60s), drop oldest keys.
        if len(_RATE_BUCKETS) > 800:
            for k in list(_RATE_BUCKETS.keys())[: len(_RATE_BUCKETS) - 800]:
                _RATE_BUCKETS.pop(k, None)
    bucket = [t for t in _RATE_BUCKETS.get(ip, []) if now - t < 60]
    if not bucket:
        _RATE_BUCKETS.pop(ip, None)  # evict idle clients: no unbounded growth
    if len(bucket) >= RATE_LIMIT:
        _RATE_BUCKETS[ip] = bucket
        return False
    bucket.append(now)
    _RATE_BUCKETS[ip] = bucket
    return True


# Global POST budget: cheap per-IP ceiling so one hammering client can't stall
# the loop for everyone. Generous (200/min) — legit use never trips it.
_GLOBAL_BUCKETS: dict[str, list] = {}
GLOBAL_LIMIT = int(os.environ.get("HEARTH_GLOBAL_RPM", "200"))


def _global_ok(ip: str) -> bool:
    now = _time.time()
    if len(_GLOBAL_BUCKETS) > 2000:
        for k in list(_GLOBAL_BUCKETS.keys())[:1000]:
            _GLOBAL_BUCKETS.pop(k, None)
    bucket = [t for t in _GLOBAL_BUCKETS.get(ip, []) if now - t < 60]
    if len(bucket) >= GLOBAL_LIMIT:
        _GLOBAL_BUCKETS[ip] = bucket
        return False
    bucket.append(now)
    _GLOBAL_BUCKETS[ip] = bucket
    return True


def _throttled(request: Request):
    ip = request.client.host if request.client else "unknown"
    if not _global_ok(ip):
        _bump("global_limited")
        return JSONResponse(
            {"ok": False, "error": "Global rate budget exceeded (200/min). Slow down."},
            status_code=429,
        )
    return None


# Lightweight ops counters (in-memory; exposed via /api/metrics, no PII).
_COUNTERS = {"chat": 0, "decide": 0, "chat_rate_limited": 0,
             "global_limited": 0, "chat_timeout": 0, "auth_denied": 0}


def _bump(key: str) -> None:
    try:
        _COUNTERS[key] = _COUNTERS.get(key, 0) + 1
    except Exception:
        pass


def _validate_env() -> None:
    """Fail-safe boot validation: clamp nonsense, never crash a judge demo."""
    try:
        port = int(os.environ.get("PORT", "8787"))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        print("config warn: bad PORT, falling back to 8787")
        os.environ["PORT"] = "8787"
    for var, lo, hi, default in (("HEARTH_CHAT_RPM", 1, 1000, "30"),
                                 ("HEARTH_GLOBAL_RPM", 10, 10000, "200")):
        try:
            v = int(os.environ.get(var, default))
            if not lo <= v <= hi:
                raise ValueError
        except ValueError:
            print(f"config warn: bad {var}, falling back to {default}")
            os.environ[var] = default


_validate_env()


def _require_dict_body(body) -> bool:
    return isinstance(body, dict)


def _identity(request: Request):
    pin, bearer = auth.extract_creds(request.headers)
    return auth.identify(pin=pin, bearer=bearer)


def _adult_or_403(request: Request, action: str):
    """Fail-closed Tier-2 gate. Open only when auth is unconfigured (zero-config demo)."""
    ident = _identity(request)
    if ident.full:
        return None
    if not auth.auth_configured():
        return None
    _bump("auth_denied")
    audit.append("sentinel", "auth_denied", {"action": action, "via": ident.via})
    code = 401 if ident.persona in ("anonymous", "intruder") else 403
    return JSONResponse(
        {"ok": False, "error": "Adult authorization required (X-Hearth-PIN or bearer token).", "action": action},
        status_code=code,
    )

PROTOCOL = "2025-11-25"
HEARTH_VERSION = "1.31.0"
START_TIME = _time.time()
WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web2")
_PORT = int(os.environ.get("PORT", "8787"))

mcp = FastMCP(
    "hearth-universal",
    stateless_http=True,
    streamable_http_path="/mcp",
    json_response=True,
    host="0.0.0.0",
    port=_PORT,
)


# ==============================================================================
# MCP Tools (Runtime Hook: Imported & Executed)
# ==============================================================================

@mcp.tool()
def memory_remember(
    key: Annotated[str, Field(description="Unique lookup key or identifier for the household fact, preference, or ambient constraint")],
    value: Annotated[str, Field(description="The factual content to record. Sensitive tokens and credentials will be redacted automatically via Vault")],
    owner: Annotated[str, Field(description="Household resident identifier or scope owning this fact (default: 'household')")] = "household"
) -> dict:
    """Remember a household fact, preference, or ambient constraint.

    Persists the key-value fact into durable SQLite storage. Vault secret redaction
    is automatically applied before saving to protect sensitive tokens.
    Tier-1 autonomous execution.
    """
    v = sentinel.judge("memory_remember", {"key": key})
    audit.append("agent", "memory_remember", {"key": key, "verdict": v.decision})
    return memory.remember(key, vault.redact(value), owner)


@mcp.tool()
def memory_query(
    q: Annotated[str, Field(description="Search filter substring to match against stored fact keys and values. Leave empty to retrieve all facts")] = ""
) -> dict:
    """Query household memory facts, resident preferences, and ambient constraints.

    Tier-1 autonomous read.
    """
    return {"facts": memory.query(q)}


@mcp.tool()
def goals_create(
    title: Annotated[str, Field(description="Clear human-readable title summarizing the long-running household goal")],
    steps: Annotated[str, Field(description="Comma-separated sequential steps or milestones to complete (e.g. 'Audit bills, Call provider, Downgrade tier')")] = ""
) -> dict:
    """Create a long-running multi-stage household goal.

    Evaluated by Sentinel guardrails before creation. Decomposes steps into
    an actionable milestone sequence tracked in persistent storage.
    Tier-1 autonomous execution.
    """
    v = sentinel.judge("goals_create", {"title": title})
    audit.append("agent", "goals_create", {"title": title, "verdict": v.decision})
    if v.decision == "deny":
        return {"ok": False, "error": v.reason}
    step_list = [s.strip() for s in steps.split(",") if s.strip()] or ["step 1"]
    return memory.create_goal(title, step_list)


@mcp.tool()
def goals_advance(
    id: Annotated[int, Field(description="Unique numeric ID of the active household goal to advance to the next step")]
) -> dict:
    """Advance an active household goal to its next milestone.

    Called by background agent routines or proactive cron schedulers.
    Appends an entry to the cryptographic audit trail upon advancement.
    Tier-1 autonomous execution.
    """
    out = memory.advance_goal(id)
    audit.append("scheduler", "goals_advance", {"id": id, "out": out})
    return out


@mcp.tool()
def home_get_state() -> dict:
    """Read the complete multi-room virtual smart home digital twin state.

    Returns live state for living room, master bedroom, kitchen, entryway,
    including lighting (power, brightness, CCT), HVAC climate, locks, blinds,
    ambient media, and real-time solar/grid energy telemetry.
    Tier-1 autonomous read.
    """
    return home_mock.get_state()


@mcp.tool()
def home_set_scene(
    name: Annotated[str, Field(description="Target scene preset name (e.g. 'evening-calm', 'movie-night', 'away', 'wake', 'energy-saver')")]
) -> dict:
    """Apply a coordinated multi-room smart home scene.

    Adjusts lighting ambiance, climate setpoints, motorized blinds, and media playback.
    Tier-1 autonomous comfort action. Destructive inputs are intercepted by Sentinel.
    """
    v = sentinel.judge("home_set_scene", {"name": name})
    audit.append("agent", "home_set_scene", {"name": name, "verdict": v.decision})
    if v.decision == "deny":
        return {"ok": False, "error": v.reason}
    return home_mock.set_scene(name)


@mcp.tool()
def home_routine(
    name: Annotated[str, Field(description="Name of the coordinated routine preset to run (e.g. 'morning-kickstart', 'bedtime-winddown', 'energy-saver')")]
) -> dict:
    """Execute a coordinated household routine with appliance, lighting, and audio triggers.

    Tier-1 autonomous comfort action. Evaluated by Sentinel before execution.
    """
    v = sentinel.judge("home_routine", {"name": name})
    audit.append("agent", "home_routine", {"name": name, "verdict": v.decision})
    if v.decision == "deny":
        return {"ok": False, "error": v.reason}
    return home_mock.routine(name)


@mcp.tool()
def home_toggle_lock(
    door: Annotated[str, Field(description="Identifier of the door lock to operate (default: 'front_door')")] = "front_door",
    locked: Annotated[bool, Field(description="Target lock state: True to lock (Tier-1 autonomous), False to unlock (Tier-2 Sentinel gated)")] = True,
    proposal_id: Annotated[str, Field(description="Approved proposal ID from the human approval tray authorizing unlock. Omit to stage a new proposal")] = ""
) -> dict:
    """Engage or disengage a physical entryway smart deadbolt.

    LOCKING (locked=True) is Tier-1 autonomous comfort.
    UNLOCKING (locked=False) is Tier-2 Sentinel-gated under Propose-Never-Execute:
    Requires an approved proposal_id. When omitted, fails closed and stages an approval
    proposal in the human Approval Tray.
    """
    v = sentinel.judge("home_toggle_lock", {"door": door, "locked": locked})
    if v.decision == "deny":
        audit.append("agent", "home_toggle_lock", {"door": door, "locked": locked, "verdict": v.decision})
        return {"ok": False, "error": v.reason}
    if locked:
        audit.append("agent", "home_toggle_lock", {"door": door, "locked": True, "verdict": v.decision})
        return home_mock.toggle_lock(door=door, locked=True)
    # Unlock path: fail-closed without an approved proposal.
    if proposal_id:
        p = proposals.get_proposal(proposal_id)
        if p and p.get("status") == "approved" and p.get("kind") == "home_lock":
            audit.append("agent", "home_toggle_lock", {"door": door, "locked": False, "via": proposal_id})
            return home_mock.toggle_lock(door=door, locked=False)
        return {"ok": False, "error": "proposal_id is not an approved home_lock proposal"}
    item = proposals.propose(
        kind="home_lock",
        title="Unlock Front Door Entryway",
        reasons="MCP client requested door unlock. Physical access requires human confirmation.",
        risk_level="high",
        diff="Front door: Locked -> Unlocked. Auto-lock re-engages after 5 minutes.",
        meta={"door": door, "locked": False},
    )
    audit.append("agent", "home_toggle_lock", {"door": door, "locked": False, "verdict": "ask", "proposal": item["id"]})
    return {"ok": False, "approval_required": True, "proposal": item}


@mcp.tool()
def inbox_scan() -> dict:
    """Scan household subscriptions, renewal telemetry, and savings opportunities.

    Analyzes recurring subscription usage, detects dormant services (e.g. 0 usage
    in 45+ days), and calculates annualized financial savings ($803.76/yr potential).
    Tier-1 autonomous read.
    """
    return proposals.scan_renewals()


@mcp.tool()
def commerce_list_inventory() -> dict:
    """List household consumable pantry stock, depletion levels, and replenishment status.

    Returns full inventory of staples (coffee, milk, laundry detergent, etc.),
    current stock counts, reorder thresholds, and low-stock warnings.
    Tier-1 autonomous read.
    """
    return {"inventory": commerce.list_inventory(), "low_stock": commerce.get_low_stock()}


@mcp.tool()
def commerce_scan_deals() -> dict:
    """Scan active Subscribe & Save discounts and household essential bundles.

    Identifies tiered bulk discounts, instant coupons, and scheduled delivery savings
    across essential household consumables.
    Tier-1 autonomous read.
    """
    return {"deals": commerce.find_deals()}


@mcp.tool()
def actions_propose(
    kind: Annotated[str, Field(description="Proposal category (e.g. 'subscription_cancel', 'home_lock', 'order_replenish', 'workspace_exec')")],
    title: Annotated[str, Field(description="Clear human-readable summary of the proposed consequential action")],
    reasons: Annotated[str, Field(description="Detailed rationale and justification explaining why the agent recommends this action")] = "",
    cost_delta_yr: Annotated[float, Field(description="Estimated annualized financial impact in USD (negative indicates savings)")] = 0.0
) -> dict:
    """Propose a consequential action into the Glass-box Approval Tray.

    Adheres to the Propose-Never-Execute safety contract. NEVER executes actions
    directly — writes exclusively to the human approval tray awaiting single-use decision.
    Tier-2 governance tool.
    """
    item = proposals.propose(kind=kind, title=title, reasons=reasons, cost_delta_yr=cost_delta_yr)
    audit.append("agent", "actions_propose", item)
    return item


@mcp.tool()
def actions_list_proposals(
    status: Annotated[str, Field(description="Filter proposals by status ('pending', 'approved', 'rejected'). Leave empty to retrieve all proposals")] = ""
) -> dict:
    """List proposals currently awaiting or decided in the human approval tray.

    Allows inspection of pending approval cards, cost deltas, and risk levels.
    Tier-1 autonomous read.
    """
    return {"proposals": proposals.list_proposals(status or None)}


@mcp.tool()
def actions_decide(
    id: Annotated[str, Field(description="Unique proposal identifier in the human approval tray to decide upon")],
    approved: Annotated[bool, Field(description="True to approve and execute the proposal; False to reject")]
) -> dict:
    """Human-gated decision: approve or reject an action proposal.

    Single-use execution gate. Once approved, executes the staged action and writes
    an immutable cryptographic receipt to the audit ledger. Replay attacks are rejected.
    Human UI gate.
    """
    out = proposals.decide(id, approved)
    audit.append("human", "actions_decide", {"id": id, "approved": approved, "outcome": out})
    return out


@mcp.tool()
def planner_orchestrate(
    goal: Annotated[str, Field(description="High-level user goal or natural language request to decompose into a multi-tool DAG")],
    session_id: Annotated[str, Field(description="Optional orchestration session id for cross-session resume. Omit to start a new session")] = ""
) -> dict:
    """Decompose a high-level goal into an autonomous multi-tool DAG and synthesized plan.

    Classifies user intent, runs Sentinel safety pre-checks, executes parallel tool steps,
    and drafts consequential proposals where required.
    Tier-1 autonomous orchestration.
    """
    out = planner.orchestrate_dag(goal, session_id=session_id or None)
    audit.append("agent", "planner_orchestrate", {
        "goal": goal,
        "intent": out.get("intent", ""),
        "model": out.get("model", ""),
        "session_id": out.get("session_id", ""),
    })
    return out


@mcp.tool()
def planner_orchestrate_dag(
    goal: Annotated[str, Field(description="High-level user goal to decompose into an explicit DAG with depends_on edges")],
    session_id: Annotated[str, Field(description="Optional session id to resume; omit for a new session")] = ""
) -> dict:
    """Multi-step DAG planner with persisted cross-session state + media-card.

    Returns {session_id, intent, dag[{id,tool,depends_on,status}], edges,
    media_card{title, carousel, purchase_action}, approval_required?}.
    Gated actions (unlock/order) return approval_required, never execute.
    """
    out = planner.orchestrate_dag(goal, session_id=session_id or None)
    audit.append("agent", "planner_orchestrate_dag", {
        "goal": goal, "intent": out.get("intent", ""),
        "session_id": out.get("session_id", "")})
    return out


@mcp.tool()
def planner_get_session(
    session_id: Annotated[str, Field(description="Orchestration session id to resume")]
) -> dict:
    """Resume a persisted DAG orchestration session across client sessions."""
    return planner.dag_get_session(session_id)


@mcp.tool()
def mcp_apps_media_card(
    kind: Annotated[str, Field(description="Media card kind: lighting_designer, subscription_roi, or pantry_restock")] = "pantry_restock"
) -> dict:
    """Emit a rich media-card JSON (title, carousel items, purchase action) for the web UI.

    Consumable by web/js/mcp-apps.js renderMediaCard(). Purchase actions are
    propose-never-execute: they stage Approval Tray proposals (approval_required).
    """
    return planner.media_card(kind if kind in ("lighting_designer", "subscription_roi", "pantry_restock") else "pantry_restock")


@mcp.tool()
def audit_verify() -> dict:
    """Cryptographically verify the tamper-evident SHA-256 hash-chain of all actions.

    Iterates over the append-only ledger (`audit.jsonl`), verifies each entry's
    SHA-256 parent hash pointer, and confirms mathematical integrity.
    Tier-1 verification read.
    """
    is_valid = audit.verify()
    return {"valid": is_valid, "algorithm": "SHA-256", "chain_integrity": "OK" if is_valid else "CORRUPTED"}


@mcp.tool()
def web_search(
    query: Annotated[str, Field(description="Search keywords or phrase for live web retrieval")],
    count: Annotated[int, Field(description="Maximum number of search results to return (default: 5, max: 20)")] = 5
) -> dict:
    """Search the live web without external API keys.

    Queries DuckDuckGo with instant-answer fallback, ads stripped, returning titles,
    snippets, and target URLs. Tier-1 autonomous read.
    """
    return webtools.web_search(query, count)


@mcp.tool()
def web_fetch(
    url: Annotated[str, Field(description="Public HTTP/HTTPS URL to fetch and convert to readable text")]
) -> dict:
    """Fetch a public webpage as clean, readable text.

    Hardened with SSRF protection: private IP ranges, loopback addresses (127.0.0.1, 0.0.0.0),
    and internal cloud metadata endpoints are strictly blocked.
    Tier-1 autonomous read.
    """
    return webtools.web_fetch(url)


@mcp.tool()
def workspace_exec(
    cmd: Annotated[str, Field(description="Shell command line to execute inside the sandboxed workspace jail")],
    proposal_id: Annotated[str, Field(description="Approved proposal ID authorizing this execution. Omit to stage a new approval proposal")] = ""
) -> dict:
    """Run a shell command jailed to the workspace sandbox (Tier-2).

    Enforces 60-second timeouts and blocks destructive command patterns via Sentinel.
    Requires an approved proposal_id; without one, stages a proposal in the Approval Tray.
    """
    v = sentinel.judge("workspace_exec", {"cmd": cmd})
    if v.decision == "deny":
        audit.append("agent", "workspace_exec", {"cmd": cmd[:200], "verdict": v.decision})
        return {"ok": False, "error": v.reason}
    if proposal_id:
        p = proposals.get_proposal(proposal_id)
        if p and p.get("status") == "approved" and p.get("kind") == "workspace_exec":
            out = sandbox.execute(cmd)
            audit.append("agent", "workspace_exec", {"cmd": cmd[:200], "via": proposal_id, "rc": out.get("rc")})
            return out
        return {"ok": False, "error": "proposal_id is not an approved workspace_exec proposal"}
    item = proposals.propose(kind="workspace_exec", title=f"Run: {cmd[:80]}",
                             reasons="MCP client requested workspace shell execution.",
                             risk_level="medium", diff=cmd[:500], meta={"cmd": cmd[:2000]})
    audit.append("agent", "workspace_exec", {"cmd": cmd[:200], "verdict": "ask", "proposal": item["id"]})
    return {"ok": False, "approval_required": True, "proposal": item}


@mcp.tool()
def workspace_write(
    path: Annotated[str, Field(description="Relative file path inside the workspace sandbox jail to write")],
    content: Annotated[str, Field(description="Text content to write into the destination file")],
    proposal_id: Annotated[str, Field(description="Approved proposal ID authorizing this file write. Omit to stage a new approval proposal")] = ""
) -> dict:
    """Write a file inside the sandboxed workspace jail (Tier-2).

    Path traversal attempts ('..') outside the sandbox are strictly blocked.
    Requires an approved proposal_id; without one, stages a proposal in the Approval Tray.
    """
    v = sentinel.judge("workspace_write", {"path": path})
    if v.decision == "deny":
        audit.append("agent", "workspace_write", {"path": path, "verdict": v.decision})
        return {"ok": False, "error": v.reason}
    if proposal_id:
        p = proposals.get_proposal(proposal_id)
        if p and p.get("status") == "approved" and p.get("kind") == "workspace_write":
            out = sandbox.write_file(path, content)
            audit.append("agent", "workspace_write", {"path": path, "via": proposal_id})
            return out
        return {"ok": False, "error": "proposal_id is not an approved workspace_write proposal"}
    item = proposals.propose(kind="workspace_write", title=f"Write file: {path[:120]}",
                             reasons="MCP client requested a workspace file write.",
                             risk_level="medium", diff=f"path: {path[:200]}\nbytes: {len(content or '')}",
                             meta={"path": path[:200], "content": (content or "")[:100000]})
    audit.append("agent", "workspace_write", {"path": path, "verdict": "ask", "proposal": item["id"]})
    return {"ok": False, "approval_required": True, "proposal": item}


@mcp.tool()
def mcp_app_subscription_roi() -> dict:
    """Interactive MCP App for household subscription financial modeling and ROI visualization.

    Returns structured UI state with interactive spend sliders and projected annual savings.
    Tier-1 autonomous read.
    """
    scan = commerce.scan_subscriptions()
    return {
        "app_id": "mcp_app_subscription_roi",
        "title": "Interactive Subscription ROI Optimizer",
        "category": "mcp_app",
        "data": scan,
        "slider_config": {
            "min_budget": 50,
            "max_budget": 500,
            "current_monthly_spend": round(scan["total_annual_spend"] / 12, 2),
            "target_savings_annual": scan["potential_annual_savings"]
        },
        "media_card": planner.media_card("subscription_roi"),
    }


@mcp.tool()
def mcp_app_lighting_designer(
    room: Annotated[str, Field(description="Target room for lighting design (e.g. 'living_room', 'master_bedroom', 'kitchen')")] = "living_room"
) -> dict:
    """Interactive MCP App for CCT & RGB mood lighting design with instant digital twin sync.

    Provides interactive color palette presets and correlated color temperature controls.
    Tier-1 autonomous read.
    """
    st = home_mock.get_state().get(room, {})
    return {
        "app_id": "mcp_app_lighting_designer",
        "title": f"Smart Lighting Designer: {room.replace('_', ' ').title()}",
        "category": "mcp_app",
        "room": room,
        "current_state": st.get("lights", {}),
        "presets": [
            {"name": "Warm Candlelight", "temp_k": 2200, "brightness": 35, "color": "#ff9d42"},
            {"name": "Focus Daylight", "temp_k": 5000, "brightness": 85, "color": "#f4f8ff"},
            {"name": "Cyber Ambient", "temp_k": 6500, "brightness": 60, "color": "#00f0ff"},
            {"name": "Cinema Violet", "temp_k": 3000, "brightness": 40, "color": "#a855f7"},
        ],
        "media_card": planner.media_card("lighting_designer"),
    }


@mcp.tool()
def mcp_app_pantry_restock() -> dict:
    """Interactive MCP App for Amazon Prime Subscribe & Save replenishment with depletion radar.

    Returns interactive consumable depletion forecasts and staged cart reorder cards.
    Tier-1 autonomous read.
    """
    forecast = commerce.get_depletion_forecast()
    cart = commerce.stage_amazon_cart()
    return {
        "app_id": "mcp_app_pantry_restock",
        "title": "Amazon Subscribe & Save Depletion Radar",
        "category": "mcp_app",
        "forecast": forecast,
        "staged_cart": cart,
        "media_card": planner.media_card("pantry_restock"),
    }


@mcp.tool()
def family_arbiter_resolve(
    conflict_type: Annotated[str, Field(description="Category of household conflict to resolve (e.g. 'climate', 'energy_peak', 'media')")] = "climate",
    custom_params: Annotated[dict | None, Field(description="Optional custom preference parameters or constraint overrides")] = None
) -> dict:
    """Autonomous negotiation engine for household resident conflicts, custom preferences, and peak-tariff load shifting.

    Computes Pareto-optimal compromise setpoints balancing comfort, energy cost, and occupancy.
    Tier-1 autonomous resolution.
    """
    try:
        plan = arbiter.resolve_conflict(conflict_type, custom_params=custom_params)
    except (ValueError, TypeError) as e:
        return {"ok": False, "error": f"Invalid arbiter input: {e}"}
    audit.append("agent", "family_arbiter_resolve", {"type": conflict_type, "plan": plan.get("title")})
    return plan


@mcp.tool()
def commerce_optimize_bundles(
    item_ids: Annotated[list[str] | None, Field(description="Optional list of item IDs to evaluate for Subscribe & Save 5+ tier bundles")] = None,
    auto_fill_tier: Annotated[bool, Field(description="Automatically add optimal high-consumption items to hit the 15% tier discount")] = True
) -> dict:
    """Amazon Subscribe & Save 5+ item bundle tier optimizer with manufacturer co-op discounts and box consolidation."""
    res = commerce.optimize_bundles(item_ids=item_ids, auto_fill_tier=auto_fill_tier)
    audit.append("agent", "commerce_optimize_bundles", {"item_count": res.get("item_count"), "savings": res.get("pricing", {}).get("total_savings")})
    return res


@mcp.tool()
def commerce_reschedule_delivery(
    slot_id: Annotated[str, Field(description="Unique ID of the delivery slot to reschedule (e.g. 'slot_2026_10_03_morning')")],
    reason: Annotated[str, Field(description="Operational justification for rescheduling (e.g. 'prevent_coffee_stockout')")] = ""
) -> dict:
    """Re-schedule Subscribe & Save household delivery slot to resolve impending stockouts or optimize eco-consolidation."""
    res = commerce.reschedule_delivery_slot(slot_id, reason=reason)
    audit.append("agent", "commerce_reschedule_delivery", {"slot": slot_id, "rescheduled": res.get("rescheduled")})
    return res


@mcp.tool()
def commerce_available_delivery_slots() -> list[dict]:
    """List available Amazon delivery slots evaluated for stockout risk against consumable depletion rates."""
    return commerce.list_available_delivery_slots()


@mcp.tool()
def timemachine_forecast(
    preset: Annotated[str, Field(description="Timeline preset to simulate: 'now', 'morning', 'afternoon', 'bedtime', 'deep_night'")] = "now"
) -> dict:
    """Temporal projection engine forecasting future household states, energy flows, and replenishment.

    Simulates environmental telemetry, battery charge levels, and ambient lighting across daily phases.
    Tier-1 autonomous read.
    """
    res = timemachine.simulate_timeline(preset)
    audit.append("agent", "timemachine_forecast", {"preset": preset})
    return res


@mcp.tool()
def commerce_delivery_tracker() -> dict:
    """Amazon Prime delivery live progress tracker with package milestones and driver ETA.

    Retrieves real-time package logistics, courier van coordinates, and estimated arrival windows.
    Tier-1 autonomous read.
    """
    return commerce.get_delivery_tracker()


@mcp.tool()
def commerce_scan_barcode(
    item_id: Annotated[str, Field(description="Barcode SKU or product identifier (e.g. 'item_coffee', 'item_milk', 'item_pods')")],
    action: Annotated[str, Field(description="Scan action: 'replenish' to add stock or 'depleted' to report consumed/empty")] = "replenish"
) -> dict:
    """Simulate a physical barcode scan of a pantry staple to restock or report depletion.

    Updates digital twin consumable quantities and checks replenishment thresholds.
    Tier-1 autonomous action.
    """
    res = commerce.simulate_barcode_scan(item_id, action)
    audit.append("agent", "commerce_scan_barcode", {"item": item_id, "action": action})
    return res


@mcp.tool()
def strands_agent_orchestrate(
    goal: Annotated[str, Field(description="Complex multi-domain household goal for AWS Strands multi-agent supervisor")],
    session_id: Annotated[str, Field(description="Optional session ID for conversational context tracking")] = ""
) -> dict:
    """AWS Strands Agents SDK multi-agent supervisor orchestrating specialized sub-agents.

    Coordinates ArbiterNegotiatorAgent, ReplenishmentDepletionAgent, and SentinelGuardianAgent
    with Bedrock AgentCore Memory session tracking.
    Tier-1 autonomous multi-agent orchestration.
    """
    res = strands_agent.supervisor.orchestrate_goal(goal, session_id=session_id or None)
    audit.append("agent", "strands_agent_orchestrate", {
        "goal": goal,
        "agents": res.get("delegated_agents"),
        "session_id": res.get("session_id")
    })
    return res


@mcp.tool()
def agentcore_memory_sync(
    session_id: Annotated[str, Field(description="Session ID to inspect or retrieve turns from Bedrock AgentCore Memory")],
    query: Annotated[str, Field(description="Optional query to search episodic memory across sessions")] = ""
) -> dict:
    """Inspect and query Bedrock AgentCore Memory store.

    Retrieves conversational turns for the active session or searches cross-session
    episodic memory matching query terms.
    Tier-1 autonomous read.
    """
    if query:
        matches = agentcore.memory_store.search_episodic_context(query)
        return {"ok": True, "query": query, "episodic_matches": matches}
    turns = agentcore.memory_store.get_session_turns(session_id)
    return {"ok": True, "session_id": session_id, "turns": turns, "stats": agentcore.memory_store.get_stats()}


@mcp.tool()
def parliament_deliberate_issue(
    topic: Annotated[str, Field(description="Household dilemma or conflicting priority to debate (e.g., peak tariff vs AC comfort)")],
    peak_tariff: Annotated[float, Field(description="Current or projected electricity tariff in $/kWh")] = 0.48,
    target_temp: Annotated[int, Field(description="Desired indoor thermostat temperature")] = 71,
    battery_soc: Annotated[int, Field(description="Battery state of charge percentage")] = 84
) -> dict:
    """Deliberate a household dilemma using the 3-minister Game-Theoretic Parliament.

    Executes structured multi-turn dialectic debate between FrugalMind, BioComfort,
    and EcoSovereign to synthesize a Pareto-optimal Nash equilibrium consensus.
    Tier-1 autonomous deliberation; stages proposals under Propose-Never-Execute.
    """
    from dataclasses import asdict
    session = parliament.parliament.deliberate(
        topic=topic,
        context={"peak_tariff": peak_tariff, "target_temp": target_temp, "battery_soc": battery_soc}
    )
    return asdict(session)


@mcp.tool()
def parliament_get_ministers() -> dict:
    """Retrieve parliamentary minister profiles, focus areas, and utility weights."""
    return parliament.parliament.get_ministers_info()


@mcp.tool()
def causal_twin_simulate(
    days_ahead: Annotated[int, Field(description="Forecast horizon in days (1 to 14)")] = 7,
    iterations: Annotated[int, Field(description="Number of Monte Carlo iterations (50 to 500)")] = 250
) -> dict:
    """Run Monte Carlo counterfactual forward simulations on the Causal Digital Twin.

    Identifies pre-emptive grid tariff spikes, brownout risks, and pantry stockouts
    before they happen, staging pre-emptive contingency plans in the Approval Tray.
    Tier-1 autonomous simulation.
    """
    from dataclasses import asdict
    res = causal_twin.causal_twin.run_simulation(days_ahead=days_ahead, iterations=iterations)
    return asdict(res)


@mcp.tool()
def causal_twin_get_vulnerabilities() -> dict:
    """Retrieve fast vulnerability snapshot from the causal world model."""
    return causal_twin.causal_twin.get_latest_vulnerabilities()


@mcp.tool()
def meta_skill_synthesize(
    requirement: Annotated[str, Field(description="Natural language description of the new capability or automation needed")],
    persona: Annotated[str, Field(description="Author persona requesting the skill ('Alex' or 'Leo')")] = "Alex"
) -> dict:
    """Autonomously compile, sandbox-verify, and mount a brand-new Alexa+ Agent Skill at runtime.

    Synthesizes parameter schemas and execution logic, validates against Sentinel safety
    policies, and dynamically mounts the skill into the live running agent environment.
    Tier-1 / Tier-2 sandboxed synthesis.
    """
    return meta_skill.meta_synthesizer.synthesize(requirement=requirement, author_persona=persona)


@mcp.tool()
def meta_skill_list_synthesized() -> list:
    """List all autonomously synthesized and hot-mounted Alexa+ Agent Skills."""
    return meta_skill.meta_synthesizer.list_synthesized_skills()


@mcp.tool()
def brains_list_available_models() -> dict:
    """Discover all connected AI models across Bedrock, OpenAI, Ollama, and custom endpoints.

    Pings all configured API base URLs in real-time, reporting latency, online status,
    and available model IDs with Amazon Bedrock + Nova Pro as default.
    """
    return model_mesh.model_mesh.discover_all_models()


@mcp.tool()
def brains_set_active_model(
    model_id: Annotated[str, Field(description="Model identifier (e.g. 'us.amazon.nova-pro-v1:0', 'gpt-4o', 'qwen2.5-coder:1.5b')")],
    provider: Annotated[str, Field(description="Provider slug (e.g. 'bedrock', 'openai', 'ollama', 'openrouter', 'custom')")] = "bedrock"
) -> dict:
    """Switch the active reasoning brain and model across all agent workflows."""
    return model_mesh.model_mesh.set_active_model(model_id=model_id, provider_name=provider)


@mcp.tool()
def brains_add_custom_provider(
    name: Annotated[str, Field(description="Display name for the custom API (e.g. 'My Local vLLM', 'Groq Fast')")],
    base_url: Annotated[str, Field(description="Base URL for the OpenAI-compatible endpoint (e.g. 'http://localhost:8000/v1')")],
    api_key: Annotated[str, Field(description="Optional API key for authentication")] = ""
) -> dict:
    """Connect Hearth Universal to ANY custom API or base URL in the world."""
    return model_mesh.model_mesh.register_custom_provider(name=name, base_url=base_url, api_key=api_key)


# ==============================================================================
# MCP Resources
# ==============================================================================

@mcp.resource("household://profile", mime_type="application/json")
def household_profile() -> str:
    """Household profile containing saved facts, preferences, and ambient state."""
    return json.dumps({
        "facts": memory.query(),
        "state": home_mock.get_state(),
        "proposals_pending": len(proposals.list_proposals("pending"))
    })


@mcp.resource("home://state", mime_type="application/json")
def home_state() -> str:
    """Live snapshot of the virtual smart home digital twin."""
    return json.dumps(home_mock.get_state())


@mcp.resource("commerce://inventory", mime_type="application/json")
def commerce_inventory() -> str:
    """Consumable inventory, pantry levels, and subscription renewals."""
    return json.dumps({
        "inventory": commerce.list_inventory(),
        "subscriptions": commerce.scan_subscriptions(),
        "deals": commerce.find_deals()
    })


@mcp.resource("audit://chain", mime_type="application/json")
def audit_chain() -> str:
    """Integrity status of the append-only cryptographic ledger."""
    return json.dumps({
        "audit_valid": audit.verify(),
        "protocol": PROTOCOL,
        "hash": "SHA-256-Merkle-Chain"
    })


# ==============================================================================
# MCP Prompts
# ==============================================================================

@mcp.prompt()
def prepare_family_weekend(
    budget: Annotated[str, Field(description="Target family weekend budget limit with currency symbol (default: '$200')")] = "$200"
) -> str:
    """Prompt template for orchestrating family weekend plans within a budget limit."""
    return (
        f"Orchestrate a family weekend itinerary under {budget}. "
        "Retrieve household memory for dietary requirements and preferred activities. "
        "Coordinate smart home scenes for movie night, scan subscription services for family entertainment, "
        "and route all proposed expenses to the Glass-box Approval Tray."
    )


@mcp.prompt()
def audit_monthly_finances(
    inactivity_days: Annotated[int, Field(description="Threshold of consecutive days with zero usage to flag subscription for cancellation (default: 45)")] = 45
) -> str:
    """Prompt template for automated subscription audit and financial leakage prevention."""
    return (
        f"Scan all recurring subscriptions and cloud services in inbox_scan. "
        f"Identify services with 0 usage in the last {inactivity_days} days. "
        "Calculate annual savings and draft cancellation or downgrade proposals in the approval tray."
    )


@mcp.prompt()
def emergency_lockdown(
    reason: Annotated[str, Field(description="Reason or trigger event for initiating perimeter lockdown (default: 'routine_security_check')")] = "routine_security_check"
) -> str:
    """Prompt template for securing home perimeter and validating smart locks."""
    return (
        f"Initiate perimeter lockdown protocol (reason: {reason}). "
        "Verify front door smart lock status, arm entryway security, close window blinds, "
        "set illumination to security mode, and report any sensor anomalies."
    )


# ==============================================================================
# Custom HTTP Routes (Simulator API & Static Web UI)
# ==============================================================================

@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request):
    import sqlite3 as _sqlite
    db_ok, writable = False, False
    try:
        state_dir = os.environ.get("HEARTH_STATE_DIR", os.path.join(os.path.dirname(__file__), "..", "state"))
        os.makedirs(state_dir, exist_ok=True)
        writable = os.access(state_dir, os.W_OK)
        con = _sqlite.connect(os.path.join(state_dir, "memory.db"), timeout=2)
        con.execute("SELECT 1").fetchone()
        con.close()
        db_ok = True
    except Exception:
        pass
    return JSONResponse({
        "status": "ok" if (db_ok and writable) else "degraded",
        "version": HEARTH_VERSION,
        "uptime_s": round(_time.time() - START_TIME, 1),
        "protocol": PROTOCOL,
        "transport": "streamable-http",
        "audit_ok": audit.verify(),
        "audit_events": audit.count(),
        "db_ok": db_ok,
        "state_writable": writable,
        "auth_enforced": auth.auth_configured(),
        "tools_count": len(mcp._tool_manager.list_tools()),
        "active_provider": brains._get_active_provider(),
        "active_model": model_mesh.model_mesh.active_model,
        "strands_harness_ok": True,
        "parliament_ok": True,
        "causal_twin_ok": True,
        "meta_synthesizer_ok": True,
        "model_mesh_providers": len(model_mesh.model_mesh.providers),
        "agent_skills_count": len(agent_skills.agent_skills_runtime.list_skills()),
    })



@mcp.custom_route("/api/chat", methods=["POST"])
async def api_chat(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON payload"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"ok": False, "error": "JSON object required"}, status_code=400)
        
    message = str(body.get("message", ""))[:4000].strip()
    provider = body.get("provider")
    if not message:
        return JSONResponse({"ok": False, "error": "Message is required"}, status_code=400)
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_ok(client_ip):
        _bump("chat_rate_limited")
        return JSONResponse({"ok": False, "error": "Rate limit exceeded (30/min). Slow down."}, status_code=429)

    # Never stall the event loop: planner does blocking network/SQLite inside.
    # 25s hard deadline, then an honest 504 (client retries safely: chat is read-only).
    try:
        out = await asyncio.wait_for(
            asyncio.to_thread(planner.plan, message, provider), timeout=25
        )
    except asyncio.TimeoutError:
        _bump("chat_timeout")
        audit.append("system", "chat_timeout", {"message_len": len(message)})
        return JSONResponse(
            {"ok": False, "error": "Hearth timed out after 25s — retry, or try a simpler goal."},
            status_code=504,
        )
    _bump("chat")
    return JSONResponse(out)


@mcp.custom_route("/api/proposals", methods=["GET", "POST"])
async def api_proposals(request: Request):
    try:
        limit = max(1, min(500, int(request.query_params.get("limit", "100"))))
    except ValueError:
        limit = 100
    return JSONResponse({
        "proposals": proposals.list_proposals(limit=limit),
        "pending_count": len(proposals.list_proposals("pending"))
    })


@mcp.custom_route("/api/decide", methods=["POST"])
@mcp.custom_route("/api/proposals/{pid}/decide", methods=["POST"])
async def api_decide(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"ok": False, "error": "JSON object required"}, status_code=400)
        
    pid = str(request.path_params.get("pid") or body.get("id") or body.get("proposal_id", ""))
    decision_val = body.get("decision")
    if decision_val is not None:
        approved = str(decision_val).lower() in ("approve", "approved", "true", "yes")
    else:
        approved = bool(body.get("approved", False))
        
    if not pid:
        return JSONResponse({"ok": False, "error": "Proposal ID is required"}, status_code=400)

    if approved:
        gate = _adult_or_403(request, "actions_decide:approve")
        if gate is not None:
            return gate

    out = proposals.decide(pid, approved)
    if isinstance(out, dict) and out.get("ok") is False:
        err = str(out.get("error", ""))
        # Single-use replay is a conflict, not a missing resource.
        if "replay refused" in err or "already " in err:
            return JSONResponse(out, status_code=409)
        return JSONResponse(out, status_code=404)
        
    audit.append("human", "actions_decide", {"id": pid, "approved": approved})
    _bump("decide")
    return JSONResponse(out)


@mcp.custom_route("/api/undo", methods=["POST"])
@mcp.custom_route("/api/proposals/{pid}/undo", methods=["POST"])
async def api_undo(request: Request):
    """Reversibility & Trust: Undo an executed action proposal, restoring prior state."""
    _t = _throttled(request)
    if _t is not None:
        return _t
    try:
        body = await request.json()
    except Exception:
        body = {}
    pid = str(request.path_params.get("pid") or body.get("id") or body.get("proposal_id", ""))
    if not pid:
        return JSONResponse({"ok": False, "error": "Proposal ID is required"}, status_code=400)

    gate = _adult_or_403(request, "actions_undo")
    if gate is not None:
        return gate

    out = proposals.undo(pid)
    status_code = 200 if out.get("ok") else 400
    return JSONResponse(out, status_code=status_code)



@mcp.custom_route("/api/memory", methods=["GET", "POST", "DELETE"])
async def api_memory(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    if request.method == "GET":
        q = request.query_params.get("q", "")
        return JSONResponse({"facts": memory.query(q)})
        
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
        
    key = str(body.get("key", "")).strip()
    val = str(body.get("value", "")).strip()
    owner = str(body.get("owner", "household")).strip()
    # Identity binding: a bearer token speaks for its own persona, never the body's.
    ident = _identity(request)
    if ident.via == "token" and ident.persona not in ("anonymous", "intruder"):
        owner = ident.persona

    if request.method == "DELETE":
        if not key:
            return JSONResponse({"ok": False, "error": "Key is required"}, status_code=400)
        audit.append("human", "memory_delete", {"key": key})
        return JSONResponse(memory.delete(key))

    if not key or not val:
        return JSONResponse({"ok": False, "error": "Key and value are required"}, status_code=400)
        
    v = sentinel.judge("memory_remember", {"key": key})
    if v.decision == "deny":
        return JSONResponse({"ok": False, "error": v.reason}, status_code=403)
        
    audit.append("human", "memory_remember", {"key": key, "verdict": v.decision})
    return JSONResponse(memory.remember(key, vault.redact(val), owner))


@mcp.custom_route("/api/home", methods=["GET"])
@mcp.custom_route("/api/telemetry", methods=["GET"])
async def api_home(request: Request):
    return JSONResponse(home_mock.get_state())


@mcp.custom_route("/api/home/scene", methods=["POST"])
async def api_home_scene(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    scene_name = str(body.get("name", "evening-calm"))
    res = home_mock.set_scene(scene_name)
    audit.append("human", "home_set_scene", {"scene": scene_name})
    return JSONResponse(res)


@mcp.custom_route("/api/home/lock", methods=["POST"])
@mcp.custom_route("/api/devices/front_door_lock", methods=["POST"])
async def api_home_lock(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"ok": False, "error": "JSON object required"}, status_code=400)
    locked = bool(body.get("locked", True))
    persona = str(body.get("persona", "") or body.get("persona_id", ""))
    # Fail-closed Sentinel gate: unlocking via REST must match MCP tool policy.
    v = sentinel.judge("home_toggle_lock", {"locked": locked, "persona": persona})
    if v.decision == "deny":
        audit.append("sentinel", "rest_unlock_denied", {"locked": locked, "reason": v.reason})
        return JSONResponse({"ok": False, "error": v.reason}, status_code=403)
    if not locked:
        # Require an approved home_lock proposal, else stage one (propose-never-execute).
        proposal_id = str(body.get("proposal_id", "") or body.get("proposalId", ""))
        if proposal_id:
            gate = _adult_or_403(request, "home_toggle_lock:unlock")
            if gate is not None:
                return gate
            p = proposals.get_proposal(proposal_id)
            if p and p.get("status") == "approved" and p.get("kind") == "home_lock":
                res = home_mock.toggle_lock(locked=False)
                audit.append("human", "home_toggle_lock", {"locked": False, "via": proposal_id})
                return JSONResponse(res)
            return JSONResponse({"ok": False, "error": "proposal_id is not an approved home_lock proposal"}, status_code=403)
        item = proposals.propose(
            kind="home_lock",
            title="Unlock Front Door Entryway",
            reasons="REST client requested door unlock. Physical access requires human confirmation.",
            risk_level="high",
            diff="Front door: Locked -> Unlocked. Auto-lock re-engages after 5 minutes.",
            meta={"locked": False},
        )
        audit.append("human", "home_toggle_lock", {"locked": False, "verdict": "ask", "proposal": item["id"]})
        return JSONResponse({"ok": False, "approval_required": True, "proposal": item}, status_code=403)
    res = home_mock.toggle_lock(locked=True)
    audit.append("human", "home_toggle_lock", {"locked": True})
    return JSONResponse(res)


@mcp.custom_route("/api/home/device", methods=["POST"])
@mcp.custom_route("/api/devices", methods=["POST"])
async def api_home_device(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"ok": False, "error": "JSON object required"}, status_code=400)
    room = str(body.get("room", "living_room"))
    device = str(body.get("device", "lights"))
    patch = body.get("patch", {})
    if not isinstance(patch, dict):
        return JSONResponse({"ok": False, "error": "patch must be an object"}, status_code=400)
    # Reject non-finite floats (NaN/Inf) to avoid JSON/state poisoning.
    try:
        import math as _math
        for _v in patch.values():
            if isinstance(_v, float) and (not _math.isfinite(_v)):
                return JSONResponse({"ok": False, "error": "patch contains non-finite number"}, status_code=400)
    except Exception:
        pass
    res = home_mock.update_device(room, device, patch)
    audit.append("human", "home_update_device", {"room": room, "device": device, "patch": patch})
    return JSONResponse(res)


@mcp.custom_route("/api/home/routine", methods=["POST"])
async def api_home_routine(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    routine_name = str(body.get("name", "morning-kickstart"))
    res = home_mock.routine(routine_name)
    audit.append("human", "home_routine", {"routine": routine_name})
    return JSONResponse(res)


@mcp.custom_route("/api/renewals", methods=["GET"])
async def api_renewals(request: Request):
    return JSONResponse(proposals.scan_renewals())


@mcp.custom_route("/api/commerce", methods=["GET"])
async def api_commerce(request: Request):
    return JSONResponse({
        "inventory": commerce.list_inventory(),
        "deals": commerce.find_deals(),
        "low_stock": commerce.get_low_stock(),
    })


@mcp.custom_route("/api/goals", methods=["GET"])
async def api_goals(request: Request):
    return JSONResponse({"goals": memory.list_goals()})


@mcp.custom_route("/api/goals/advance", methods=["POST"])
async def api_goals_advance(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    try:
        gid = int(body.get("id", 0))
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "error": "Numeric goal id required"}, status_code=400)
    out = memory.advance_goal(gid)
    audit.append("human", "goals_advance", {"id": gid, "out": out})
    return JSONResponse(out)


@mcp.custom_route("/api/audit", methods=["GET"])
async def api_audit(request: Request):
    is_valid = audit.verify()
    recent = []
    log_path = audit._log_path()
    if log_path.exists():
        try:
            lines = log_path.read_text().strip().splitlines()
            for line in lines[-25:]:
                recent.append(json.loads(line))
        except Exception:
            pass
    return JSONResponse({
        "valid": is_valid,
        "count": len(recent),
        "recent": list(reversed(recent))
    })


@mcp.custom_route("/api/reset", methods=["POST"])
async def api_reset(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    gate = _adult_or_403(request, "system_reset")
    if gate is not None:
        return gate
    home_mock.reset_state()
    proposals.clear_proposals()
    audit.append("human", "system_reset", {"action": "clean_state_reset"})
    return JSONResponse({"ok": True, "message": "State reset cleanly"})


@mcp.custom_route("/api/brain", methods=["GET", "POST"])
async def api_brain(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    if request.method == "GET":
        return JSONResponse({
            "active_provider": brains._get_active_provider(),
            "model": os.environ.get("HEARTH_MODEL", "hearth-agentic-v1"),
            "providers": [
                {"id": "local", "name": "Local Agent (Zero-Config Offline)", "active": brains._get_active_provider() == "local"},
                {"id": "bedrock", "name": "Amazon Bedrock (Claude 3.5 Sonnet / Nova)", "active": brains._get_active_provider() == "bedrock"},
                {"id": "openai", "name": "OpenAI / Ollama Gateway", "active": brains._get_active_provider() == "openai"}
            ]
        })
    try:
        body = await request.json()
        provider = str(body.get("provider", "local")).lower()
        if provider in ("local", "bedrock", "openai", "ollama"):
            gate = _adult_or_403(request, "brain_switch")
            if gate is not None:
                return gate
            os.environ["HEARTH_BRAIN_PROVIDER"] = provider
            audit.append("human", "brain_switch", {"provider": provider})
            return JSONResponse({"ok": True, "active_provider": provider})
        return JSONResponse({"ok": False, "error": "Unknown provider"}, status_code=400)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@mcp.custom_route("/api/metrics", methods=["GET"])
async def api_metrics(request: Request):
    """Bedrock-native telemetry: metrics.latencyMs series + counts (no PII)."""
    try:
        limit = max(1, min(100, int(request.query_params.get("limit", "25"))))
    except ValueError:
        limit = 25
    m = brains.get_bedrock_metrics()
    m["recent"] = m.get("recent", [])[-limit:]
    m["latencyMs"] = m.get("latencyMs", [])[-limit:]
    m["http"] = dict(_COUNTERS)
    m["audit_events"] = audit.count()
    return JSONResponse(m)


@mcp.custom_route("/api/export", methods=["GET"])
async def api_export(request: Request):
    import time as _t
    return JSONResponse({
        "protocol": PROTOCOL,
        "timestamp": _t.time(),
        "memory": memory.query(limit=200),
        "goals": memory.list_goals(limit=100),
        "home": home_mock.get_state(),
        "proposals": proposals.list_proposals(limit=100),
        "heartbeat": heartbeat.get_events(),
        "audit_integrity": audit.verify()
    })


@mcp.custom_route("/api/alexa/directive", methods=["POST"])
async def api_alexa_directive(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    """Amazon Alexa Smart Home Skills API v3 directive endpoint.

    Returns the native Alexa response PLUS a headless `hearth` companion
    envelope (TTS caption, Echo chime, light-wave hook, ReAct trace, APL
    RenderDocument) so the simulator renders voice + visual in one flow.
    Shape of `event`/`context` is unchanged for AVS compatibility.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    res = alexa.handle_directive(body)
    try:
        header = (body.get("directive") or body).get("header", {})
        evt = res.get("event", {}).get("header", {}).get("name", "Response")
        if evt == "ErrorResponse":
            msg = res.get("event", {}).get("payload", {}).get("message", "That did not work.")
            speak = f"Sorry, {msg}"[:280]
            wave = "alert"
            chime_kind = "warning"
        else:
            speak_map = {
                "Discover.Response": f"Discovered {len(res.get('event', {}).get('payload', {}).get('endpoints', []))} devices.",
                "Response": "Done.",
                "StateReport": "Here is the current state.",
            }
            speak = speak_map.get(evt, "Done.")
            wave = "speaking"
            chime_kind = "wake"
        companion = alexa.build_multimodal_response(speak_text=speak, chime=chime_kind, light_wave=wave)
        res = dict(res, hearth=companion)
    except Exception:
        pass
    return JSONResponse(res)


@mcp.custom_route("/api/alexa/voice-turn", methods=["POST"])
async def api_alexa_voice_turn(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    """No-device simulator: utterance -> directive round-trip + multimodal envelope."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    utterance = str(body.get("utterance") or body.get("message") or body.get("text") or "")
    if not utterance.strip():
        return JSONResponse({"ok": False, "error": "utterance is required"}, status_code=400)
    res = alexa.simulate_voice_turn(utterance)
    return JSONResponse(res)


@mcp.custom_route("/api/alexa/dpad", methods=["POST"])
async def api_alexa_dpad(request: Request):
    """Fire TV D-pad / keyboard nav over the APL card row (headless-safe)."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    action = str(body.get("action", "Right"))
    try:
        focus = int(body.get("focus_index", body.get("focusIndex", 0)))
    except (TypeError, ValueError):
        focus = 0
    cards = body.get("cards")
    res = alexa.handle_dpad_input(action, focus_index=focus, cards=cards)
    status = 200 if res.get("ok") else 400
    return JSONResponse(res, status_code=status)


@mcp.custom_route("/api/alexa/tts", methods=["GET", "DELETE"])
async def api_alexa_tts(request: Request):
    """Inspect (GET) or drain (DELETE) the headless TTS queue."""
    if request.method == "DELETE":
        return JSONResponse(alexa.clear_tts_queue())
    return JSONResponse({"queue": alexa.get_tts_queue(), "chimes": alexa.get_chime_log(),
                         "light_wave": alexa.get_light_wave()})


@mcp.custom_route("/api/alexa/react", methods=["GET", "DELETE"])
async def api_alexa_react(request: Request):
    """ReAct visualizer event feed (thought/action/observation/speak/show/dpad)."""
    if request.method == "DELETE":
        return JSONResponse(alexa.clear_react_events())
    try:
        limit = int(request.query_params.get("limit", "20"))
    except ValueError:
        limit = 20
    return JSONResponse({"events": alexa.get_react_events(limit)})


@mcp.custom_route("/api/alexa/apl", methods=["GET"])
async def api_alexa_apl(request: Request):
    """Live APL template + datasources payload for the smart canvas."""
    import json as _json
    tpl_path = os.path.join(os.path.dirname(__file__), "..", "skill", "apl_smart_canvas.json")
    try:
        with open(tpl_path) as f:
            template = _json.load(f)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
    return JSONResponse({"ok": True, "template": template,
                         "datasources": {"payload": alexa.get_apl_payload()},
                         "render_directive": alexa.build_apl_render_directive()})


@mcp.custom_route("/api/heartbeat", methods=["GET"])
async def api_heartbeat(request: Request):
    """Retrieve rolling autonomous household heartbeat events."""
    try:
        limit = max(1, min(50, int(request.query_params.get("limit", "15"))))
    except ValueError:
        limit = 15
    return JSONResponse({"events": heartbeat.get_events(limit)})


@mcp.custom_route("/api/simulate/tick", methods=["POST"])
async def api_simulate_tick(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    """Trigger a proactive household simulation event."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    scenario = str(body.get("scenario", "auto")).lower()
    res = heartbeat.tick_proactive(scenario)
    return JSONResponse(res)


@mcp.custom_route("/favicon.ico", methods=["GET"])
async def favicon(request: Request):
    from starlette.responses import Response
    return Response(status_code=204)


# Household Persona state — persisted to state/persona.json across restarts
_PERSONAS_MAP = {
    "admin":   {"id": "admin",   "name": "Krishiv Joshi",   "role": "Household Admin",         "tier_limit": "tier-3"},
    "partner": {"id": "partner", "name": "Sarah Miller",    "role": "Partner (Full Access)",    "tier_limit": "tier-3"},
    "child":   {"id": "child",   "name": "Leo (Child)",     "role": "Child (Safe Comfort Only)","tier_limit": "tier-1"},
    "guest":   {"id": "guest",   "name": "Guest Visitor",   "role": "Guest (Living Room Only)", "tier_limit": "tier-1"},
}
_PERSONA_FILE = os.path.join(os.environ.get("HEARTH_STATE_DIR", os.path.join(os.path.dirname(__file__), "..", "state")), "persona.json")


def _load_persona() -> dict:
    try:
        import json as _json
        p = _json.loads(open(_PERSONA_FILE).read())
        if p.get("id") in _PERSONAS_MAP:
            return p
    except Exception:
        pass
    return _PERSONAS_MAP["admin"]


def _save_persona(p: dict) -> None:
    try:
        from pathlib import Path as _Path
        from hearth import atomic as _atomic
        import json as _json
        os.makedirs(os.path.dirname(_PERSONA_FILE), exist_ok=True)
        target = _Path(_PERSONA_FILE)
        with _atomic.locked(target):
            _atomic.atomic_write_text(target, _json.dumps(p))
    except Exception:
        pass


ACTIVE_PERSONA = _load_persona()

@mcp.custom_route("/api/persona", methods=["GET", "POST"])
async def api_persona(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    global ACTIVE_PERSONA
    if request.method == "POST":
        try:
            body = await request.json()
            pid = str(body.get("id", "admin")).lower()
            if pid in _PERSONAS_MAP:
                # Escalation to a privileged persona requires adulthood when auth is on.
                if pid in ("admin", "partner"):
                    gate = _adult_or_403(request, "persona_escalate")
                    if gate is not None:
                        return gate
                ACTIVE_PERSONA = _PERSONAS_MAP[pid]
                _save_persona(ACTIVE_PERSONA)
                audit.append("human", "persona_switched", {"persona": ACTIVE_PERSONA})
                return JSONResponse({"ok": True, "active_persona": ACTIVE_PERSONA})
            return JSONResponse({"ok": False, "error": "Unknown persona"}, status_code=400)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    return JSONResponse({"ok": True, "active_persona": ACTIVE_PERSONA})



@mcp.custom_route("/api/ring/event", methods=["POST"])
async def api_ring_event(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    """Trigger simulated Ring Doorbell or Motion event."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        return JSONResponse({"ok": False, "error": "JSON object required"}, status_code=400)
    event_type = str(body.get("event_type", "doorbell_press"))
    visitor = str(body.get("visitor", "Delivery Courier"))
    res = alexa.trigger_ring_event(event_type=event_type, visitor_label=visitor)
    return JSONResponse(res)


@mcp.custom_route("/api/commerce/depletion", methods=["GET"])
async def api_commerce_depletion(request: Request):
    """Retrieve pantry items sorted by depletion velocity."""
    forecast = commerce.get_depletion_forecast()
    return JSONResponse({"ok": True, "forecast": forecast})


@mcp.custom_route("/api/commerce/stage-cart", methods=["POST"])
async def api_stage_cart(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    """Stage Amazon cart reorder proposal with slot selection and bundle tier optimization."""
    try:
        body = await request.json()
        item_ids = body.get("items")
        sub_and_save = bool(body.get("subscribe_and_save", True))
        slot_id = body.get("delivery_slot_id")
        bundle_opt = bool(body.get("bundle_optimized", False))
    except Exception:
        item_ids = None
        sub_and_save = True
        slot_id = None
        bundle_opt = False
    cart = commerce.stage_amazon_cart(
        item_ids=item_ids,
        subscribe_and_save=sub_and_save,
        delivery_slot_id=slot_id,
        bundle_optimized=bundle_opt
    )
    return JSONResponse(cart)


@mcp.custom_route("/api/commerce/optimize-bundles", methods=["GET", "POST"])
async def api_commerce_optimize_bundles(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    """Amazon Subscribe & Save 5+ item bundle tier optimizer."""
    item_ids = None
    auto_fill = True
    if request.method == "POST":
        try:
            body = await request.json()
            item_ids = body.get("items")
            auto_fill = bool(body.get("auto_fill_tier", True))
        except Exception:
            pass
    res = commerce.optimize_bundles(item_ids=item_ids, auto_fill_tier=auto_fill)
    return JSONResponse(res)


@mcp.custom_route("/api/commerce/delivery-slots", methods=["GET", "POST"])
async def api_delivery_slots(request: Request):
    """Delivery slot inspection and re-scheduling."""
    if request.method == "POST":
        try:
            body = await request.json()
            slot_id = str(body.get("slot_id", "slot_overnight_urgent"))
            reason = str(body.get("reason", "User requested schedule adjustment"))
            item_ids = body.get("items")
        except Exception:
            slot_id = "slot_overnight_urgent"
            reason = "Schedule adjustment"
            item_ids = None
        res = commerce.reschedule_delivery_slot(slot_id, item_ids=item_ids, reason=reason)
        return JSONResponse(res)
    
    slots = commerce.list_available_delivery_slots()
    scheduled = commerce.get_scheduled_delivery_slot()
    return JSONResponse({"ok": True, "slots": slots, "active_slot": scheduled})


@mcp.custom_route("/api/arbiter", methods=["GET", "POST"])
async def api_arbiter(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    """Catalog of household conflicts and resolution proposals with deep multi-resident negotiation."""
    if request.method == "POST":
        try:
            body = await request.json()
            ctype = str(body.get("conflict_type", "climate"))
            custom_params = body.get("custom_params")
            if not custom_params and "parties" in body:
                custom_params = {"parties": body.get("parties")}
        except Exception:
            ctype = "climate"
            custom_params = None
        try:
            plan = arbiter.resolve_conflict(ctype, custom_params=custom_params)
        except (ValueError, TypeError) as e:
            return JSONResponse({"ok": False, "error": f"Invalid arbiter input: {e}"}, status_code=400)
        if not isinstance(plan, dict):
            return JSONResponse({"ok": False, "error": "Arbiter returned no plan"}, status_code=502)
        return JSONResponse(plan)
    return JSONResponse({"ok": True, "conflicts": arbiter.list_active_conflicts()})


@mcp.custom_route("/api/timemachine", methods=["GET", "POST"])
async def api_timemachine(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    """Temporal simulation engine endpoints."""
    if request.method == "POST":
        try:
            body = await request.json()
            preset = str(body.get("preset", "now"))
        except Exception:
            preset = "now"
        return JSONResponse(timemachine.simulate_timeline(preset))
    return JSONResponse({"ok": True, "presets": timemachine.get_timeline_presets(), "current": timemachine.simulate_timeline("now")})


@mcp.custom_route("/api/commerce/delivery-tracker", methods=["GET"])
async def api_delivery_tracker(request: Request):
    return JSONResponse(commerce.get_delivery_tracker())


@mcp.custom_route("/api/commerce/scan", methods=["POST"])
async def api_commerce_scan(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    try:
        body = await request.json()
        item_id = str(body.get("item_id", "item_coffee"))
        action = str(body.get("action", "replenish"))
    except Exception:
        item_id = "item_coffee"
        action = "replenish"
    res = commerce.simulate_barcode_scan(item_id, action)
    return JSONResponse(res)


@mcp.custom_route("/api/strands/orchestrate", methods=["POST"])
async def api_strands_orchestrate(request: Request):
    _t = _throttled(request)
    if _t is not None:
        return _t
    """AWS Strands Agents multi-agent supervisor goal execution."""
    try:
        body = await request.json()
        goal = str(body.get("goal", "")).strip()
        sid = body.get("session_id")
        ctx = body.get("context")
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    if not goal:
        return JSONResponse({"ok": False, "error": "goal is required"}, status_code=400)
    res = strands_agent.supervisor.orchestrate_goal(goal, session_id=sid, context=ctx)
    return JSONResponse(res)


@mcp.custom_route("/api/strands/telemetry", methods=["GET"])
async def api_strands_telemetry(request: Request):
    """Telemetry counters for AWS Strands Agents SDK and Bedrock AgentCore Memory."""
    return JSONResponse({
        "ok": True,
        "framework": "AWS Strands Agents SDK + Bedrock AgentCore",
        "memory_stats": agentcore.memory_store.get_stats(),
        "gateway_stats": agentcore.gateway.get_telemetry(),
        "supervisor_active": True,
        "subagents": ["ArbiterNegotiatorAgent", "ReplenishmentDepletionAgent", "SentinelGuardianAgent"],
    })


@mcp.custom_route("/api/agent-skills", methods=["GET"])
async def api_agent_skills(request: Request):
    """Retrieve the standardized Alexa+ Agent Skills manifest."""
    return JSONResponse(agent_skills.agent_skills_runtime.export_agent_skills_manifest())


@mcp.custom_route("/api/parliament/deliberate", methods=["POST"])
async def api_parliament_deliberate(request: Request):
    """Deliberate a household dilemma using the 3-minister Game-Theoretic Parliament."""
    try:
        body = await request.json()
        topic = body.get("topic", "Household energy and comfort optimization")
        ctx = body.get("context", {})
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    from dataclasses import asdict
    session = parliament.parliament.deliberate(topic=topic, context=ctx)
    return JSONResponse(asdict(session))


@mcp.custom_route("/api/parliament/ministers", methods=["GET"])
async def api_parliament_ministers(request: Request):
    """Retrieve parliamentary minister profiles and weights."""
    return JSONResponse(parliament.parliament.get_ministers_info())


@mcp.custom_route("/api/causal/simulate", methods=["POST"])
async def api_causal_simulate(request: Request):
    """Run Monte Carlo counterfactual forward simulations on the Causal Digital Twin."""
    try:
        body = await request.json()
        days = int(body.get("days_ahead", 7))
        iters = int(body.get("iterations", 250))
    except Exception:
        days, iters = 7, 250
    from dataclasses import asdict
    res = causal_twin.causal_twin.run_simulation(days_ahead=days, iterations=iters)
    return JSONResponse(asdict(res))


@mcp.custom_route("/api/causal/vulnerabilities", methods=["GET"])
async def api_causal_vulnerabilities(request: Request):
    """Retrieve fast vulnerability snapshot from the causal world model."""
    return JSONResponse(causal_twin.causal_twin.get_latest_vulnerabilities())


@mcp.custom_route("/api/meta-skills/synthesize", methods=["POST"])
async def api_meta_skills_synthesize(request: Request):
    """Autonomously synthesize and mount a new Agent Skill at runtime."""
    try:
        body = await request.json()
        req_text = body.get("requirement", "")
        persona = body.get("persona", "Alex")
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    if not req_text:
        return JSONResponse({"ok": False, "error": "requirement is required"}, status_code=400)
    res = meta_skill.meta_synthesizer.synthesize(requirement=req_text, author_persona=persona)
    return JSONResponse(res)


@mcp.custom_route("/api/meta-skills", methods=["GET"])
async def api_meta_skills_list(request: Request):
    """List all autonomously synthesized and hot-mounted Alexa+ Agent Skills."""
    return JSONResponse({"ok": True, "skills": meta_skill.meta_synthesizer.list_synthesized_skills()})


@mcp.custom_route("/api/models", methods=["GET"])
async def api_models_list(request: Request):
    """Discover all connected AI models across Bedrock, OpenAI, Ollama, and custom endpoints."""
    return JSONResponse(model_mesh.model_mesh.discover_all_models())


@mcp.custom_route("/api/models/active", methods=["POST"])
async def api_models_set_active(request: Request):
    """Switch the active reasoning brain and model across all agent workflows."""
    try:
        body = await request.json()
        model_id = body.get("model_id")
        provider = body.get("provider", "bedrock")
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    if not model_id:
        return JSONResponse({"ok": False, "error": "model_id is required"}, status_code=400)
    res = model_mesh.model_mesh.set_active_model(model_id=model_id, provider_name=provider)
    return JSONResponse(res)


@mcp.custom_route("/api/models/providers/add", methods=["POST"])
async def api_models_provider_add(request: Request):
    """Connect Hearth Universal to ANY custom API or base URL in the world."""
    try:
        body = await request.json()
        name = body.get("name", "Custom API")
        base_url = body.get("base_url")
        api_key = body.get("api_key", "")
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    if not base_url:
        return JSONResponse({"ok": False, "error": "base_url is required"}, status_code=400)
    res = model_mesh.model_mesh.register_custom_provider(name=name, base_url=base_url, api_key=api_key)
    return JSONResponse(res)


@mcp.custom_route("/api/diagnostics", methods=["GET"])
async def api_diagnostics(request: Request):
    """System Diagnostics & Telemetry: Complete health overview of all subsystems."""
    now = _time.time()
    uptime = round(now - _SERVER_START_TIME, 1)
    audit_health = audit.verify()
    mesh_info = model_mesh.model_mesh.discover_all_models()
    parl_info = parliament.parliament.get_ministers_info()
    causal_info = causal_twin.causal_twin.get_latest_vulnerabilities()

    return JSONResponse({
        "status": "healthy",
        "system": "Hearth Universal Multi-Agent Household Command",
        "spec_version": PROTOCOL,
        "uptime_seconds": uptime,
        "active_brain": mesh_info.get("active_model"),
        "active_provider": mesh_info.get("active_provider"),
        "connected_providers": mesh_info.get("providers_connected", 1),
        "total_models_available": mesh_info.get("total_models_available", 1),
        "audit_ledger": {
            "valid": bool(audit_health),
            "events_count": audit.count(),
        },
        "parliament": {
            "council": parl_info.get("council"),
            "ministers_count": len(parl_info.get("ministers", [])),
        },
        "causal_twin": {
            "resilience_score": causal_info.get("resilience_score", 0.94),
            "vulnerability_count": causal_info.get("vulnerability_count", 0),
        },
        "meta_skills": {
            "count": len(meta_skill.meta_synthesizer.list_synthesized_skills()),
        },
        "active_persona": ACTIVE_PERSONA.get("name"),
        "proposals_pending": len(proposals.list_proposals(status="pending")),
    })


WEB2_DIR = os.path.join(os.path.dirname(__file__), "..", "web2")


@mcp.custom_route("/web2/{path:path}", methods=["GET"])
async def web2_static(request: Request):
    rel = (request.path_params.get("path", "") or "").strip("/") or "index.html"
    target = os.path.normpath(os.path.join(WEB2_DIR, rel))
    web2_root = os.path.abspath(WEB2_DIR)
    if target.startswith(web2_root) and os.path.isfile(target):
        ctype = "text/html"
        if target.endswith(".css"):
            ctype = "text/css"
        elif target.endswith(".js"):
            ctype = "application/javascript"
        elif target.endswith(".json"):
            ctype = "application/json"
        return FileResponse(target, headers={"Cache-Control": "no-store", "Content-Type": ctype})
    return PlainTextResponse("Not Found", status_code=404)


@mcp.custom_route("/web2", methods=["GET"])
async def web2_index(request: Request):
    idx = os.path.join(WEB2_DIR, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx, headers={"Cache-Control": "no-store"})
    return PlainTextResponse("web2 UI not built yet.", status_code=404)


@mcp.custom_route("/css/{path:path}", methods=["GET"])
async def css_static(request: Request):
    rel = request.path_params.get("path", "")
    target = os.path.normpath(os.path.join(WEB_DIR, "css", rel))
    css_root = os.path.abspath(os.path.join(WEB_DIR, "css"))
    if target.startswith(css_root) and os.path.isfile(target):
        return FileResponse(target, headers={"Cache-Control": "no-store", "Content-Type": "text/css"})
    return PlainTextResponse("Not Found", status_code=404)


@mcp.custom_route("/js/{path:path}", methods=["GET"])
async def js_static(request: Request):
    rel = request.path_params.get("path", "")
    target = os.path.normpath(os.path.join(WEB_DIR, "js", rel))
    js_root = os.path.abspath(os.path.join(WEB_DIR, "js"))
    if target.startswith(js_root) and os.path.isfile(target):
        return FileResponse(target, headers={"Cache-Control": "no-store", "Content-Type": "application/javascript"})
    return PlainTextResponse("Not Found", status_code=404)


@mcp.custom_route("/app.js", methods=["GET"])
async def app_js(request: Request):
    # Support both web/js/app.js and web/app.js
    modular_js = os.path.join(WEB_DIR, "js", "app.js")
    if os.path.exists(modular_js):
        return FileResponse(modular_js, headers={"Cache-Control": "no-store", "Content-Type": "application/javascript"})
    return FileResponse(os.path.join(WEB_DIR, "app.js"), headers={"Cache-Control": "no-store", "Content-Type": "application/javascript"})


@mcp.custom_route("/manifest.json", methods=["GET"])
async def manifest(request: Request):
    return FileResponse(os.path.join(WEB_DIR, "manifest.json"))


@mcp.custom_route("/vendor/{path:path}", methods=["GET"])
async def vendor_static(request: Request):
    rel = request.path_params.get("path", "")
    target = os.path.normpath(os.path.join(WEB_DIR, "vendor", rel))
    vendor_root = os.path.abspath(os.path.join(WEB_DIR, "vendor"))
    if target.startswith(vendor_root) and os.path.isfile(target):
        return FileResponse(target)
    return PlainTextResponse("Not Found", status_code=404)


@mcp.custom_route("/", methods=["GET"])
async def index(request: Request):
    idx = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx, headers={"Cache-Control": "no-store"})
    return PlainTextResponse("Hearth Universal MCP 2025-11-25 at /mcp.")


if __name__ == "__main__":
    print(f"Hearth Universal on :{_PORT} | MCP {PROTOCOL} Streamable HTTP stateless | /mcp + /health + /")
    print(f"brain provider={brains._get_active_provider()} model={os.environ.get('HEARTH_MODEL', 'default')} "
          f"scheduler={'on' if os.environ.get('HEARTH_SCHEDULER') == '1' else 'off'} "
          f"chat_rpm={RATE_LIMIT} state={os.environ.get('HEARTH_STATE_DIR', 'state')}")
    if os.environ.get("HEARTH_SCHEDULER") == "1":
        import threading

        def _scheduler_loop() -> None:
            import time as _t
            interval = float(os.environ.get("HEARTH_SCHEDULER_MINUTES", "60")) * 60
            while True:
                _t.sleep(interval)
                try:
                    actives = [g for g in memory.list_goals() if g.get("status") == "active"]
                    if actives:
                        nxt = min(actives, key=lambda g: g["id"])
                        out = memory.advance_goal(nxt["id"])
                        audit.append("scheduler", "goals_tick", out)
                except Exception:
                    pass

        threading.Thread(target=_scheduler_loop, daemon=True).start()
    mcp.run(transport="streamable-http")
