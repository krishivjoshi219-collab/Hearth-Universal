# 🏆 Hearth Universal — Devpost Submission Copy (v2 Grand Prize Edition)
*Optimized for the Build, Ship, Shape: Amazon Developer Hackathon 2026*

---

### Project Title
**Hearth Universal**  
*Display title: A Small Servant for Alexa+ That Finds $800 in Waste, Proposes, and Never Spends Without You*

### Tagline / Short Description (≤140 characters)
**Tell Alexa "Save me $800." She finds $803.76/yr waste, proposes, you tap once — never spends $1 without you. Reverses in 1 tap.**

---

### Tracks & Categories Selected
- [x] **Primary Track**: **Alexa+ Track ($25,000 1st Place Cash + $15,000 AWS Credits)**
- [x] **Mini Challenge**: **AWS Builder ($5,000 Cash + $5,000 AWS Credits)**
- [x] **Mini Challenge**: **Open Source ($5,000 Cash + $5,000 AWS Credits)**

---

### Official Links
- **Public GitHub Repository**: [https://github.com/krishivjoshi219-collab/Hearth-Universal](https://github.com/krishivjoshi219-collab/Hearth-Universal)  
  *(Open Source with MIT License. Amazon Reviewers invited: `chris-trag`, `knmeiss`, `giolaq`, `anishamalde`, `mosesroth`, `emersonsklar`)*
- **Demo Video URL**: `<Your YouTube Public Link>` *(Exact 2:57 Human Win Cut — 177.04s, 1080p @ 30fps, captions on)*
- **Live Cloud App URL**: _(Render deploy in progress — paste the final `https://…onrender.com` URL here before submitting)_ *(Fallback: `http://localhost:8787/echo` via `./demo.sh`)*
- **Built With Tags**: `alexa-plus`, `mcp`, `streamable-http`, `aws-app-runner`, `strands-agents`, `amazon-bedrock`, `agentcore`, `subscribe-and-save`, `fastmcp`, `python`, `echo-show`

---

## ⏱️ 60-Second Judge Tour (Test it in 1 Click)

1. Open our live cloud URL: **`/echo`**
2. Tap the first hero chip: **"Save me $800"** &rarr; Hearth scans 5 household subscriptions, detects $803.76/yr waste, and stages 3 cancellation cards in your Approval Tray.
3. Tap **Approve** &rarr; A cryptographic SHA-256 receipt seals instantly.
4. Tap **Undo** &rarr; The action reverses in one tap! *"She proposes. You tap once. Nothing runs without you, and everything undoes in one tap."*
5. Tap **"Fix groceries"** &rarr; Depletion radar analyzes pantry stock, staging a 5-item Amazon Subscribe & Save cart with **15% bulk discount ($35.32 saved)** and guaranteed Prime delivery slot.
6. Switch persona to **Leo (Age 9)** &rarr; Try ordering Robux or unlocking the front door. Both are hard-blocked by the Sentinel safety contract with a friendly child card.

---

## 💡 Inspiration: The $803 Bill Every Family Pays

Every household knows this bill: $239 for StreamBox nobody opened in 68 days. $30/month for a gym nobody visits. A 9-year-old shouting *"Alexa, buy 5,000 Robux!"* at 9 PM. And black-box AI agents that either do nothing—or silently charge your credit card and unlock your front door.

We built **Hearth Universal** for **Alexa+** around one rule families instantly trust:  
**Propose-Never-Execute. Nothing moves money or locks doors without your tap. Every action undoes in one tap.**

Say *"Alexa, save me $800 on renewals"* &rarr; she audits household subscriptions, identifies **$803.76/yr** in dormant waste, stages 3 proposal cards with exact before-and-after diffs &rarr; you tap once &rarr; SHA-256 receipt sealed. Say *"restock coffee"* &rarr; 15% Subscribe & Save bulk discount calculated, Prime delivery slot booked, still nothing charged until you tap. Switch to Leo (9) &rarr; orders and door locks hard-blocked with a kind *"ask a grown-up"* card.

Under that human magic is real Alexa+ technology: **FastMCP 2025-11-25 over Streamable HTTP (55 tools live)**, AWS Strands multi-agent supervisor, Bedrock AgentCore memory, and MCP Apps cards.

---

## 🛠️ What Hearth Universal Does

### 1. Echo Show 15/21 Ambient Smart Canvas (`/echo`)
- Designed specifically for wall-mounted ambient living: real-time household telemetry, quick scenario triggers, dynamic micro-climate status, and the **Pantry Depletion Radar**.
- **Responsive Echo Show Surface**: Built with responsive layouts adapting fluidly from Echo Show 8 (1280x800) to Echo Show 15/21 (1080p).
- Zero-config offline simulation with optional **🧠 Connect AI** header chip allowing judges to test their own model keys (Google Gemini 3.8 Flash, Amazon Bedrock, OpenAI, Claude).

### 2. AWS Multi-Service Pipeline: Strands Agents SDK & Bedrock AgentCore
- **AWS Strands Multi-Agent Supervisor**: Genuine `strands.Agent` objects composed with the SDK's `Agent.as_tool()` agents-as-tools pattern:
  - `ArbiterNegotiatorAgent`: Resolves resident preference disputes with Pareto efficiency and shifts high-draw loads off peak energy tariffs.
  - `ReplenishmentDepletionAgent`: Evaluates consumable depletion velocities and maximizes 15% Subscribe & Save discounts.
  - `SentinelGuardianAgent`: Enforces 3-tier risk gating, child guardrails, and cryptographic audits.
- **AWS Bedrock AgentCore Memory**: Persistent session turns and episodic retrieval across household conversations.
- **Amazon Bedrock Converse Multi-Model Router**: Dynamic routing between **Claude 3.5 Sonnet** (deep reasoning) and **Amazon Nova Pro** (fast planning) with honest simulated offline fallbacks.

### 3. Amazon Retail & Alexa+ Flywheel: Subscribe & Save Restock
- Models linear consumption velocity across household staples (milk, fair-trade coffee, dishwasher pods).
- Stages 1-tap **Amazon Subscribe & Save Cart Cards** with automated **15% bulk discount calculations** ($35.32 saved across 5 items) and Prime delivery slots.
- Live **Amazon Prime Transit Stepper**: Tracks delivery from fulfillment center to Prime Van #482 (2 stops away).

### 4. Multi-Persona Sentinel Safety Matrix (Adult vs. Child Guardrails)
- 3-tier security gate: Tier-1 (Safe comfort actions), Tier-2 (Consequential financial actions routed to human approval tray), and Tier-3 (Hard-blocked destructive commands).
- **Persona Context Awareness**: Switching to `Leo` (Child / Age 9) automatically activates child guardrails—blocking financial orders and perimeter door unlocks while permitting safe entertainment.

### 5. Hearth Forge: Runtime MCP Tool Synthesis (Agent Skills / Shape Theme)
- When your home needs a capability it has never seen, Hearth dynamically synthesizes, AST-validates, sandbox smoke-tests, and hot-mounts a brand-new MCP tool in seconds without restarting the server (demonstrated live on camera: 54 &rarr; 55 live tools).

### 6. Standalone Open-Source Contribution: `mcp-strands-adapter`
- Exposes AWS Strands agents and tools *as* MCP 2025-11-25 tools over Streamable HTTP—the direction the official Strands SDK does not cover.
- Published with 15 passing tests under Apache-2.0 in `open-source-contribution/mcp-strands-adapter/`.

---

## 🔬 How We Built It & Architectural Rigor
- **FastMCP 2025-11-25**: Implements the newest MCP specification over Streamable HTTP (`POST /mcp`), RFC 9728 Protected Resource Metadata, and OAuth 2.1 with PKCE S256.
- **362 Automated Tests**: 100% passing test suite across contracts, tools, safety guardrails, and simulated Alexa+ surfaces.
- **Mathematical Integrity**: Real algorithms under the hood—constrained Nash bargaining (`parliament.py`), 1R1C thermal dynamics (`causal_twin.py`), and log-odds Bayesian hypothesis testing (`forensics.py`).

---

## 🎬 2:57 Video Walkthrough Breakdown
- **[0:00–0:17] The Hook**: Live count-up of $803.76 waste; "Every home runs on guesswork."
- **[0:17–0:59] The Core**: "Save me $800" → $803.76 found → 3 cards staged → cockpit reads the house.
- **[0:59–1:16] The Trust Moat**: One-tap Approve, one-tap Undo → receipt written, nothing rogue.
- **[1:16–1:33] The Prime Clawback**: $5 late-delivery refund staged and signed.
- **[1:33–1:48] Amazon Flywheel**: Pantry depletion → 5-item Subscribe & Save cart at bulk pricing.
- **[1:48–2:01] Child Safety**: Leo (Age 9) asks for Robux and the front door → both hard-blocked.
- **[2:01–2:20] Hearth Forge**: Live runtime synthesis of tool #55 (54 → 55) with safety checks.
- **[2:20–2:57] Proof + Close**: 3 AM forensic walk (98% confidence, second-by-second timeline), then 362 tests / 55 tools / "Not an agent. A servant."

---

## 🧰 Friction Log (Optional — up to +10%)

*Format: task attempted · steps · expected vs. actual · severity · workaround · actionable suggestion.*

### 1. Keeping internal tools off the public MCP surface
- **Task**: Ship a 55-tool product surface plus a private agent-to-agent bus.
- **Steps**: Registered the bus handlers with the same FastMCP `@mcp.tool()` decorator as product tools, then called `tools/list`.
- **Expected**: Internal helpers stay internal; `tools/list` returns 55.
- **Actual**: 57. The decorator publishes to every client, so "internal" tooling silently joined the judge-facing contract and broke a frame-locked count.
- **Severity**: Important — caught by a regression test, not by the framework.
- **Workaround**: Re-registered the bus as plain HTTP routes (`/api/warroom/*`), removed the decorators, and added a test asserting exactly 55 tools.
- **Suggestion**: Support `internal=True` (or registration-time namespaces/policies) so one server can host public and private tools without a second transport.

### 2. No Echo Show preview for a web-based Alexa+ surface
- **Task**: Verify the `/echo` ambient canvas at Echo Show 8/15/21 sizes, including touch targets.
- **Steps**: Built responsive CSS; drove Playwright at 1280×800, 1920×1080, and 390×844; audited tap targets and horizontal overflow.
- **Expected**: A browser preview with Echo Show device metrics and touch events.
- **Actual**: No device or browser emulator was available to us; behavior was inferred from docs and screenshots. On a 390 px phone the fixed 1280×800 canvas scales down, so text is small until the judge rotates or zooms.
- **Severity**: Nice-to-have — a workaround exists, but it is the first thing a phone judge sees.
- **Workaround**: An explicit "Experience it on Echo Show" affordance, responsive layout, and viewport checks in CI.
- **Suggestion**: Publish Echo Show viewport presets (DPR, safe areas, touch) for Chrome DevTools/Playwright and a "send to device" preview for Alexa+ web experiences.

### 3. Silent brain fallback is invisible to the judge
- **Task**: Confirm the public URL answers with the configured cloud brain.
- **Steps**: `POST /api/chat`, then inspect the `provider` field and server logs.
- **Expected**: `provider: gemini`/`groq` with cloud latency.
- **Actual**: HTTP 200 with a polished answer but `provider: local-fallback` — the app degraded silently instead of surfacing the failed provider. A judge cannot tell, and neither could we without reading logs.
- **Severity**: Important — the demo stays up, but the "real model" claim becomes unverifiable.
- **Workaround**: Pin an allowlisted OpenAI-compatible host (Groq), read the active provider from `/api/diagnostics`, and treat a non-cloud provider as a deployment failure.
- **Suggestion**: Return `degraded: true` with a reason code, expose it in diagnostics, and show a small "local engine" badge in the UI so the state is never hidden.

### 4. Validating an Alexa+ MCP server without an Alexa+ client
- **Task**: Self-host an MCP 2025-11-25 Streamable HTTP endpoint and prove compatibility.
- **Steps**: Implemented stateless `POST /mcp`, RFC 9728 protected-resource metadata, and OAuth 2.1 + PKCE S256; exercised `initialize`, `tools/list`, and `tools/call` with generic MCP clients and curl.
- **Expected**: A conformance harness that signs in the way Alexa+ does and calls the server.
- **Actual**: No Alexa+ client was reachable from our environment, so conformance had to be inferred from the spec and generic clients.
- **Severity**: Important — the integration is the submission's core claim.
- **Workaround**: Protocol-level contract tests, a public `tools/list` count, and a documented auth flow.
- **Suggestion**: Ship an "Alexa+ MCP conformance" CLI (auth discovery, initialize, tools/list, tools/call, error shapes) that runs in CI, with Alexa+ policy checks on top of the generic MCP inspector.
