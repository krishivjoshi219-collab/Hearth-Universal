"""Hearth Universal MCP server — spec 2025-11-25, Streamable HTTP, stateless.
Serves MCP protocol on /mcp, REST APIs for simulator on /api/*, and interactive Alexa+ UI on /.
Verifies via curl POST /mcp initialize -> protocolVersion 2025-11-25.
"""
from __future__ import annotations
import json
import os
import sys

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

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, FileResponse, PlainTextResponse

from hearth import sentinel, vault, audit, memory, home_mock, proposals, planner, commerce, brains

# Simple per-IP token bucket for the expensive chat endpoint (product abuse guard).
_RATE_BUCKETS: dict[str, list] = {}
RATE_LIMIT = int(os.environ.get("HEARTH_CHAT_RPM", "30"))


def _rate_ok(ip: str) -> bool:
    import time
    now = time.time()
    bucket = [t for t in _RATE_BUCKETS.get(ip, []) if now - t < 60]
    if not bucket:
        _RATE_BUCKETS.pop(ip, None)  # evict idle clients: no unbounded growth
    if len(bucket) >= RATE_LIMIT:
        _RATE_BUCKETS[ip] = bucket
        return False
    bucket.append(now)
    _RATE_BUCKETS[ip] = bucket
    return True

PROTOCOL = "2025-11-25"
WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")
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
def memory_remember(key: str, value: str, owner: str = "household") -> dict:
    """Remember a household fact (editable, exportable, privacy-preserving)."""
    v = sentinel.judge("memory_remember", {"key": key})
    audit.append("agent", "memory_remember", {"key": key, "verdict": v.decision})
    return memory.remember(key, vault.redact(value), owner)


@mcp.tool()
def memory_query(q: str = "") -> dict:
    """Query household memory facts and preferences."""
    return {"facts": memory.query(q)}


@mcp.tool()
def goals_create(title: str, steps: str = "") -> dict:
    """Create a long-running household goal. steps = comma-separated."""
    v = sentinel.judge("goals_create", {"title": title})
    audit.append("agent", "goals_create", {"title": title, "verdict": v.decision})
    if v.decision == "deny":
        return {"ok": False, "error": v.reason}
    step_list = [s.strip() for s in steps.split(",") if s.strip()] or ["step 1"]
    return memory.create_goal(title, step_list)


@mcp.tool()
def goals_advance(id: int) -> dict:
    """Advance a goal one step (called by background agent or scheduler)."""
    out = memory.advance_goal(id)
    audit.append("scheduler", "goals_advance", {"id": id, "out": out})
    return out


@mcp.tool()
def home_get_state() -> dict:
    """Read the complete multi-room virtual smart home digital twin state."""
    return home_mock.get_state()


@mcp.tool()
def home_set_scene(name: str) -> dict:
    """Apply a smart home scene (Tier-1 autonomous comfort: lights, climate, media)."""
    v = sentinel.judge("home_set_scene", {"name": name})
    audit.append("agent", "home_set_scene", {"name": name, "verdict": v.decision})
    if v.decision == "deny":
        return {"ok": False, "error": v.reason}
    return home_mock.set_scene(name)


@mcp.tool()
def home_routine(name: str) -> dict:
    """Execute a coordinated home routine (Tier-1 autonomous comfort)."""
    v = sentinel.judge("home_routine", {"name": name})
    audit.append("agent", "home_routine", {"name": name, "verdict": v.decision})
    if v.decision == "deny":
        return {"ok": False, "error": v.reason}
    return home_mock.routine(name)


@mcp.tool()
def home_toggle_lock(door: str = "front_door", locked: bool = True, proposal_id: str = "") -> dict:
    """Engage the smart lock directly (Tier-1). UNLOCKING is Tier-2: pass an
    approved proposal_id, or omit it to receive a staged approval proposal."""
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
    """Scan household subscriptions, renewal telemetry, and savings opportunities."""
    return proposals.scan_renewals()


@mcp.tool()
def commerce_list_inventory() -> dict:
    """List household consumable pantry stock and replenishment status."""
    return {"inventory": commerce.list_inventory(), "low_stock": commerce.get_low_stock()}


@mcp.tool()
def commerce_scan_deals() -> dict:
    """Scan active Subscribe & Save discounts and household essential bundles."""
    return {"deals": commerce.find_deals()}


@mcp.tool()
def actions_propose(kind: str, title: str, reasons: str = "", cost_delta_yr: float = 0.0) -> dict:
    """Propose a consequential action. Writes ONLY to approval tray — never auto-executes."""
    item = proposals.propose(kind=kind, title=title, reasons=reasons, cost_delta_yr=cost_delta_yr)
    audit.append("agent", "actions_propose", item)
    return item


@mcp.tool()
def actions_list_proposals(status: str = "") -> dict:
    """List items currently awaiting or reviewed in the human approval tray."""
    return {"proposals": proposals.list_proposals(status or None)}


@mcp.tool()
def actions_decide(id: str, approved: bool) -> dict:
    """Human-gated decision: approve or reject an action proposal."""
    out = proposals.decide(id, approved)
    audit.append("human", "actions_decide", {"id": id, "approved": approved, "outcome": out})
    return out


@mcp.tool()
def planner_orchestrate(goal: str) -> dict:
    """Decompose a high-level goal into an autonomous multi-tool DAG + synthesized plan."""
    out = planner.plan(goal)
    audit.append("agent", "planner_orchestrate", {
        "goal": goal,
        "intent": out.get("intent", ""),
        "model": out.get("model", "")
    })
    return out


@mcp.tool()
def audit_verify() -> dict:
    """Cryptographically verify the tamper-evident SHA-256 hash-chain of all actions."""
    is_valid = audit.verify()
    return {"valid": is_valid, "algorithm": "SHA-256", "chain_integrity": "OK" if is_valid else "CORRUPTED"}


# ==============================================================================
# MCP Resources
# ==============================================================================

@mcp.resource("household://profile")
def household_profile() -> str:
    """Household profile containing saved facts, preferences, and ambient state."""
    return json.dumps({
        "facts": memory.query(),
        "state": home_mock.get_state(),
        "proposals_pending": len(proposals.list_proposals("pending"))
    })


@mcp.resource("home://state")
def home_state() -> str:
    """Live snapshot of the virtual smart home digital twin."""
    return json.dumps(home_mock.get_state())


@mcp.resource("commerce://inventory")
def commerce_inventory() -> str:
    """Consumable inventory, pantry levels, and subscription renewals."""
    return json.dumps({
        "inventory": commerce.list_inventory(),
        "subscriptions": commerce.scan_subscriptions(),
        "deals": commerce.find_deals()
    })


@mcp.resource("audit://chain")
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
def prepare_family_weekend(budget: str = "$200") -> str:
    """Prompt template for orchestrating family weekend plans within a budget limit."""
    return (
        f"Orchestrate a family weekend itinerary under {budget}. "
        "Retrieve household memory for dietary requirements and preferred activities. "
        "Coordinate smart home scenes for movie night, scan subscription services for family entertainment, "
        "and route all proposed expenses to the Glass-box Approval Tray."
    )


@mcp.prompt()
def audit_monthly_finances() -> str:
    """Prompt template for automated subscription audit and financial leakage prevention."""
    return (
        "Scan all recurring subscriptions and cloud services in inbox_scan. "
        "Identify services with 0 usage in the last 45 days. "
        "Calculate annual savings and draft cancellation or downgrade proposals in the approval tray."
    )


@mcp.prompt()
def emergency_lockdown() -> str:
    """Prompt template for securing home perimeter and validating smart locks."""
    return (
        "Verify front door smart lock status, arm entryway security, close window blinds, "
        "set illumination to security mode, and report any sensor anomalies."
    )


# ==============================================================================
# Custom HTTP Routes (Simulator API & Static Web UI)
# ==============================================================================

@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request):
    return JSONResponse({
        "status": "ok",
        "protocol": PROTOCOL,
        "transport": "streamable-http",
        "audit_ok": audit.verify(),
        "tools_count": 16,
        "active_provider": brains._get_active_provider(),
    })


@mcp.custom_route("/api/chat", methods=["POST"])
async def api_chat(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON payload"}, status_code=400)
        
    message = str(body.get("message", ""))[:4000].strip()
    provider = body.get("provider")
    if not message:
        return JSONResponse({"ok": False, "error": "Message is required"}, status_code=400)
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_ok(client_ip):
        return JSONResponse({"ok": False, "error": "Rate limit exceeded (30/min). Slow down."}, status_code=429)

    out = planner.plan(message, preferred_provider=provider)
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
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
        
    pid = str(request.path_params.get("pid") or body.get("id") or body.get("proposal_id", ""))
    decision_val = body.get("decision")
    if decision_val is not None:
        approved = str(decision_val).lower() in ("approve", "approved", "true", "yes")
    else:
        approved = bool(body.get("approved", False))
        
    if not pid:
        return JSONResponse({"ok": False, "error": "Proposal ID is required"}, status_code=400)
        
    out = proposals.decide(pid, approved)
    if isinstance(out, dict) and out.get("ok") is False:
        return JSONResponse(out, status_code=404)
        
    audit.append("human", "actions_decide", {"id": pid, "approved": approved})
    return JSONResponse(out)


@mcp.custom_route("/api/memory", methods=["GET", "POST", "DELETE"])
async def api_memory(request: Request):
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
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    locked = bool(body.get("locked", True))
    res = home_mock.toggle_lock(locked=locked)
    audit.append("human", "home_toggle_lock", {"locked": locked})
    return JSONResponse(res)


@mcp.custom_route("/api/home/device", methods=["POST"])
@mcp.custom_route("/api/devices", methods=["POST"])
async def api_home_device(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    room = str(body.get("room", "living_room"))
    device = str(body.get("device", "lights"))
    patch = body.get("patch", {})
    res = home_mock.update_device(room, device, patch)
    audit.append("human", "home_update_device", {"room": room, "device": device, "patch": patch})
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
    home_mock.reset_state()
    proposals.clear_proposals()
    audit.append("human", "system_reset", {"action": "clean_state_reset"})
    return JSONResponse({"ok": True, "message": "State reset cleanly"})


@mcp.custom_route("/favicon.ico", methods=["GET"])
async def favicon(request: Request):
    from starlette.responses import Response
    return Response(status_code=204)


@mcp.custom_route("/app.js", methods=["GET"])
async def app_js(request: Request):
    return FileResponse(os.path.join(WEB_DIR, "app.js"))


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
        return FileResponse(idx)
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
