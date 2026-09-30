# Hearth Universal — Agent Skill Package for Alexa+ Orchestrators
Drop this package into any Alexa+ Agent Skills runtime or MCP-compatible orchestrator.
Target endpoint: `/mcp` (Streamable HTTP, MCP Protocol 2025-11-25).

## Overview
Hearth Universal transforms Alexa+ into an autonomous, proactive household operations agent that manages subscriptions, pantry replenishment, and smart home digital twins under an uncompromising **propose-never-execute** safety contract.

## When to Activate
- User articulates multi-domain household requests ("Save me $437", "I'm heading home early", "Reorder coffee and pantry essentials", "Plan family weekend under $150").
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
- `home_set_scene(name)`: Apply coordinated lighting/HVAC scenes (`evening-calm`, `movie-night`, `away`, `wake`, `energy-saver`). [GATED]
- `home_routine(name)`: Execute sequenced routines with appliance triggers and audio queues. [GATED]
- `home_toggle_lock(door, locked)`: Actuate smart entryway lock. [GATED]

### 3. Financial Intelligence & Commerce
- `inbox_scan()`: Analyze subscription usage, dormant billing, and annual savings potential ($437/yr).
- `commerce_list_inventory()`: Monitor pantry consumables (coffee, detergent, filters) and depletion percentages.
- `commerce_scan_deals()`: Match household essentials to active Subscribe & Save bundle discounts.

### 4. Glass-Box Action Tray & Governance
- `actions_propose(kind, title, reasons, cost_delta_yr)`: Stage structured proposals for human review. Never auto-executes consequential actions.
- `actions_list_proposals(status)`: Inspect pending, approved, or rejected proposals.
- `actions_decide(id, approved)`: Record human decision (Human UI surface only).
- `planner_orchestrate(goal)`: Decompose goals into dynamic multi-tool DAGs with parallel execution.
- `audit_verify()`: Cryptographically verify the SHA-256 tamper-evident execution ledger.

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
1. **Propose-Never-Execute**: Any action that spends money, cancels services, or changes physical locks MUST be formatted as a structured proposal with cost delta and diff.
2. **Vault Secret Redaction**: Secrets (`{{vault:NAME}}`, API tokens, OTP codes) are replaced with `•••` before model context ingestion.
3. **Strict Egress Validation**: Models and tool requests must communicate only with allowlisted endpoints (`*.amazonaws.com`, `api.openai.com`, `localhost`).
4. **Adversarial Interception**: Shell injection (`rm -rf`, `mkfs`), SQL injections, and system prompt override attempts are hard-denied and audited.
