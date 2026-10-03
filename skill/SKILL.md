# Hearth Universal — Agent Skill Package for Alexa+ Orchestrators
Drop this package into any Alexa+ Agent Skills runtime or MCP-compatible orchestrator.
Target endpoint: `/mcp` (Streamable HTTP, MCP Protocol 2025-11-25).

## Overview
Hearth Universal transforms Alexa+ into an autonomous, proactive household operations agent that manages subscriptions, pantry replenishment, and smart home digital twins under an uncompromising **propose-never-execute** safety contract.

## When to Activate
- User articulates multi-domain household requests ("Save me $800", "I'm heading home early", "Reorder coffee and pantry essentials", "Plan family weekend under $150").
- Background proactive schedules (nightly subscription telemetry audit, consumable stock reorder alerts, energy conservation routines).
- Physical access or home actuation (lock, lights, climate) requiring explicit human confirmation.

## Registered MCP Tools (Streamable HTTP 2025-11-25)

### 1. Household Memory & Goals
- `memory_query(q)`: Retrieve persistent household facts, dietary requirements, and preferences.
- `memory_remember(key, value, owner)`: Store verified facts into SQLite memory (redacted via Vault).
- `goals_create(title, steps)`: Schedule long-running multi-stage household initiatives.
- `goals_advance(id)`: Advance goal state and report progress.

### 2. Smart Home Digital Twin
- `home_get_state()`: Inspect multi-room lighting, climate, locks, media, and energy draw in real time.
- `home_set_scene(name)`: Apply coordinated lighting/HVAC scenes (`evening-calm`, `movie-night`, `away`, `wake`, `energy-saver`). Tier-1 autonomous comfort.
- `home_routine(name)`: Execute sequenced routines with appliance triggers and audio queues. Tier-1 autonomous comfort.
- `home_toggle_lock(door, locked)`: Locking is autonomous; UNLOCKING is [GATED] — needs an approved `home_lock` proposal.

### 3. Financial Intelligence & Commerce
- `inbox_scan()`: Analyze subscription usage, dormant billing, and annual savings potential ($803.76/yr).
- `commerce_list_inventory()`: Monitor pantry consumables (coffee, detergent, filters) and depletion percentages.
- `commerce_scan_deals()`: Match household essentials to active Subscribe & Save bundle discounts.

### 4. Glass-Box Action Tray & Governance
- `actions_propose(kind, title, reasons, cost_delta_yr)`: Stage structured proposals for human review. Never auto-executes consequential actions.
- `actions_list_proposals(status)`: Inspect pending, approved, or rejected proposals.
- `actions_decide(id, approved)`: Record human decision (Human UI surface only).
- `planner_orchestrate(goal)`: Decompose goals into dynamic multi-tool DAGs with parallel execution.
- `audit_verify()`: Cryptographically verify the SHA-256 tamper-evident execution ledger.

### 5. Live Web & Workspace Agency (real tools, zero fixture data)
- `web_search(query, count)`: Keyless live search (DDG html → Instant Answer fallback, ads filtered).
- `web_fetch(url)`: Public pages as readable text; loopback/private IPs hard-blocked (SSRF-proof).
- `workspace_exec(cmd, proposal_id)`: Shell jailed to workspace, 60s timeout, destructive patterns blocked. [GATED] without an approved proposal.
- `workspace_write(path, content, proposal_id)`: Jailed file writes. [GATED] without an approved proposal.
- Live brains drive a general ReAct loop (`{"call"|"final"}` JSON); offline engine stays deterministic and exact.

## MCP Resources
- `household://profile`: Complete household profile, persistent facts, and pending proposal counts.
- `home://state`: Multi-room digital twin device states, locks, and live energy telemetry.
- `commerce://inventory`: Pantry consumable levels and active bundle discounts.
- `audit://chain`: Verification state of the SHA-256 cryptographic audit trail.

## MCP Prompts
- `prepare_family_weekend(budget)`: Orchestrate weekend itinerary balancing dietary constraints, media, and budget.
- `audit_monthly_finances()`: Run automated subscription hygiene and flag zero-usage waste.
- `emergency_lockdown()`: Rapidly verify perimeter locks, secure illumination, and report anomalies.

## Guardrail Architecture (Sentinel)
Two tiers, enforced in code (not just documented):
- **Tier-1 autonomous comfort** (lights, climate, scenes, engaging locks, reads, goals): executes immediately. Proven by `test_sentinel_two_tiers`.
- **Tier-2 gated consequences** (UNLOCKING doors, spending, orders, cancellations): the agent MUST call `actions_propose` and NEVER execute directly. Direct gated calls fail closed with `approval_required`. Decisions are single-use (replay refused). Proven by `test_planner_gates_unlock` + HTTP smoke test.
1. **Propose-Never-Execute (tier-2)**: Any action that spends money, cancels services, or UNLOCKS physical locks MUST be a structured proposal with cost delta and diff; approval executes it and writes an execution receipt.
2. **Vault Secret Redaction**: Secrets (`{{vault:NAME}}`, API tokens, OTP codes) are replaced with `•••` before model context ingestion.
3. **Strict Egress Validation**: Models and tool requests must communicate only with allowlisted endpoints (`*.amazonaws.com`, `api.openai.com`, `localhost`).
4. **Adversarial Interception**: Shell injection (`rm -rf`, `mkfs`), SQL injections, and system prompt override attempts are hard-denied and audited.

## B1: DAG Orchestration + MCP Apps Media Cards
- `planner_orchestrate(goal, session_id?)` / `planner_orchestrate_dag(goal, session_id?)`: decomposes goals into an explicit multi-step DAG (`dag[{id,tool,depends_on,status}]` + `edges`), executes Tier-1 steps, persists `session_id` state to `state/orchestrations.json` for cross-session resume via `planner_get_session(session_id)`.
- `mcp_apps_media_card(kind)`: emits rich `media-card` JSON `{type:"media-card", title, carousel:{items[{title,image,meta,action}]}, purchase_action{label,tool,args,gated}}` for kinds `lighting_designer`, `subscription_roi`, `pantry_restock`. Render with `web2/js/app.js` carousel renderer.
- Gating intact: `unlock` / `order` DAG nodes return `approval_required` + staged proposal; never auto-execute. `purchase_action.gated=true` always routes to the Approval Tray.
