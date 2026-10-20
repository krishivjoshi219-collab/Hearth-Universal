# Devpost Submission Form Guide & Copy

Use this document to quickly fill out the official **"Enter a Submission"** form on Devpost for the **Build, Ship, Shape: Amazon Developer Hackathon (2026)**.

---

### Project Title
**Hearth Universal — Tell Alexa "Save Me $800." She Proposes. You Tap Once. She Never Spends Without You.**

### Tagline / Short Description (1-2 Sentences, keep Devpost tagline field ≤140 chars)
Tell Alexa "Save Me $800." She finds $803.76/yr waste, proposes, you tap once — never spends $1 without you.

Full short description: proactive agentic workflows (audit → propose → 1-tap approve → 1-tap undo) on MCP 2025-11-25 Streamable HTTP, with Strands multi-agent + Bedrock memory + MCP Apps cards under a Propose-Never-Execute safety contract.

---

### Tracks & Categories Selected
- [x] **Primary Track**: **Alexa+** ($25,000 1st Place)
- [x] **Mini Challenge**: **AWS Builder** ($5,000 Prize + $5,000 AWS Credits)
- [x] **Mini Challenge**: **Open Source** ($5,000 Prize + $5,000 AWS Credits)

---

### Links & Video
- **GitHub Repository URL**: `https://github.com/krishivjoshi219-collab/Hearth-Universal`  
  *(Public repository with MIT License. Amazon Reviewers invited: `chris-trag`, `knmeiss`, `giolaq`, `anishamalde`, `mosesroth`, `emersonsklar` — add Oct 22, invites expire in 7 days)*
- **Demo Video URL**: `<Your YouTube / Vimeo Link>` *(the finished film is `demo_film/HEARTH_DEMO_FINAL.mp4` — 2:58, the as-shot script is `demo_film/script.md`. Must be Public + "Not for Kids", <3:00.)*
- **Try It Out URL**: `<deployed /echo URL — see battleplan>` *(fallback: clone + `./demo.sh`)*
- **Built With tags**: `alexa-plus`, `mcp`, `streamable-http`, `strands-agents`, `bedrock`, `agentcore`, `nova`, `google-gemini`, `mcp-apps`, `agent-skills`, `oauth-2.1`, `fastapi`, `python`, `subscribe-and-save`, `echo-show`
- **Thumbnail**: 3:2 JPG/PNG/GIF ≤5MB — Echo Show tray card with "$803.76/yr found" + big Approve button, not the logo.

---

### Devpost Project Description (Markdown)

```markdown
## ⏱️ If you have 60 seconds (the whole product)
Tap **"Save me $800"** → 3 waste cards ($803.76/yr in our demo household) → **Stage** → **Approve** → sealed receipt → **Undo**. Then tap **"Fix groceries"** → 5-item Subscribe & Save cart → Approve → Undo. Switch to Leo (9) → orders + unlocks blocked. Everything below is the engine room behind those 60 seconds.

## 💡 Inspiration — the $803 bill every family pays

Every family knows this bill: $239 for StreamBox nobody opened in 68 days. $30/mo for a gym nobody visits. A 9-year-old yelling "Alexa, buy Robux!" at 9pm. And black-box agents that either do nothing — or silently charge your card and unlock your door.

We built **Hearth Universal** for **Alexa+** around one rule families instantly trust: **Propose-Never-Execute. Nothing moves money or locks without your tap. Every action undoes in one tap.**

Say *"Alexa, save me $800 on renewals"* → she audits 5 subscriptions, finds **$803.76/yr** waste, stages 3 cards with exact before/after diffs → you tap once → SHA-256 receipt sealed. Say *"restock coffee"* → 15% Subscribe & Save cart staged, Prime slot booked, still nothing ordered until you tap. Switch to Leo (9) → orders + unlocks hard-blocked with a kind "ask a grown-up" card.

Under that 60-second magic is real Alexa+ tech: self-hosted MCP 2025-11-25 Streamable HTTP (51 hand-built tools — 54 live once forged skills are mounted), Strands multi-agent supervisor, Bedrock memory, MCP Apps cards, Agent Skills — all offline-first so a judge can run it with zero keys. Bring your own key in the preview (🧠 Connect AI) and free-form questions route through **your** provider — Google Gemini (the film runs live on Gemini 3.8 Flash), OpenAI, Groq, OpenRouter, Ollama, any OpenAI-compatible endpoint, or Bedrock — with the key stored server-side only.

---

## 🛠️ What Hearth Universal Does

### 1. Dual-Mode Ambient OS: Echo Show 15/21 Smart Canvas & Ops Cockpit
- **Echo Show 15/21 Smart Canvas**: A high-design ambient wall display featuring real-time solar/battery energy flow vector diagrams, quick scene triggers, an autonomous heartbeat ticker, and the **Pantry Depletion Radar**.
- **Interactive 2.5D Architectural Spatial Floorplan**: Vector architectural blueprint with dynamic ambient light radiance pools, micro-climate zoning, and real-time family occupancy dots (`Alex`, `Sarah`, `Leo`).
- **Glass-Box Time Machine**: Scrub future states (Bedtime 11 PM, Deep Night 3 AM, Morning Wake 7:30 AM) to simulate future solar battery levels, lighting scenes, and replenishment alerts.
- **Glass-Box Ops Cockpit**: A deep-inspection desktop/tablet view showing multi-turn voice chat, DAG ReAct execution graphs, the Proposal Approval Tray, and the multi-room Digital Twin.

### 2. AWS Builder Multi-Service Pipeline: Strands Agents SDK & Bedrock AgentCore
- **AWS Strands Multi-Agent Supervisor**: Genuine `strands.Agent` objects, tools declared with the SDK's `@tool` decorator, sub-agents composed with the SDK's `Agent.as_tool()` agents-as-tools pattern. `strands_backend` reports which path ran (`aws-strands-sdk` / `aws-strands-sdk-no-inference` / `pattern-fallback`) and is never guessed. Coordinates:
  - `ArbiterNegotiatorAgent`: Resolves resident preference disputes with Pareto efficiency and shifts high-draw loads off peak energy tariffs.
  - `ReplenishmentDepletionAgent`: Evaluates consumable depletion velocities and maximizes 15% Subscribe & Save discounts.
  - `SentinelGuardianAgent`: Enforces 3-tier risk gating, child guardrails, and cryptographic audits.
- **AWS Bedrock AgentCore Memory**: An AgentCore-Memory-compatible store for persistent session turns and cross-session episodic retrieval. `get_stats()` reports its backend precisely (`bedrock-agentcore-memory-compatible`, `implementation: local-json-store`) and sets `live_sync` only when `AWS_AGENTCORE_MEMORY_ID` and credentials are present.
- **Amazon Bedrock Converse Multi-Model Router (optional, emulated by default)**: Dynamic routing between **Claude 3.5 Sonnet** (deep reasoning) and **Amazon Nova Pro** (structured fast planning) with adaptive retries and `system=[]` prompt isolation when `AWS_BEDROCK_ENABLED=1`; honest `aws-bedrock-simulated` offline fallback otherwise.

### 3. Autonomous Subscription & Financial Hygiene (Saves $803.76/yr)
- Scans active household subscriptions and analyzes real usage telemetry.
- Detects dormant services (e.g. StreamBox 4K unused for 68 days) and low-utilization memberships.
- Calculates **$803.76/yr in actionable annual savings** and stages 1-tap cancellation/downgrade cards in the user's **Approval Tray**. Nothing moves money until tapped.

### 4. Predictive Pantry Depletion, Amazon Prime Live Transit & Barcode Restock
- Models linear consumption velocity (`days_until_empty`) across household staples (Organic Whole Milk, Fair-Trade Coffee Beans, Dishwasher Pods).
- Live **Amazon Prime Transit Tracker**: Stepper tracking package progress from JFK8 fulfillment to Prime Van #482 (Driver Marcus, 2 stops away).
- Interactive **Pantry Barcode Scanner**: Simulated optical UPC barcode scanner that instantly scans items to replenish or flag depletion.
- Stages 1-tap **Amazon Subscribe & Save Cart Cards** with automated **15% bulk discount calculations** ($4.03 savings on coffee) and guaranteed Prime delivery slots (e.g. *Tomorrow, 8 AM - 11 AM*).

### 5. Interactive MCP Apps (Rich Media Micro-UIs)
- Exposes interactive mini-applications directly inside tool execution payloads:
  - **Lighting Designer App**: Interactive HTML5 color wheel canvas with live CCT (2700K - 6500K) and RGB gamut picker.
  - **Subscription ROI Simulator**: Dynamic budget slider recalculating 1-year and 3-year compound savings in real time.
  - **Amazon Restock Cart**: Interactive item selector with automated coupon and quantity adjustment.

### 6. Multi-Persona Sentinel Safety Matrix (Adult vs. Child Guardrails)
- 3-tier security gate: Tier-1 (Safe comfort actions), Tier-2 (Consequential actions routed to human tray), and Tier-3 (Hard-blocked destructive commands).
- **Persona Context Awareness**: Switching from `Alex` (Adult Owner) to `Leo` (Child / Age 9) automatically activates child safety guardrails—blocking financial orders and perimeter door unlocks while permitting safe comfort actions.

### 7. Cryptographic SHA-256 Ledger & Alexa+ Agent Skills
- Immutably records every AI proposal, human approval, and Sentinel block in an append-only SHA-256 hash chain (`audit.jsonl`).
- Implements the official **Alexa+ Agent Skills** specification (`skill/agent_skills_manifest.json`) for declarative skill discovery and capability handshakes.
- Publishes **[`mcp-strands-adapter`](open-source-contribution/mcp-strands-adapter/)**: a standalone Apache-2.0 library exposing AWS Strands agents and tools *as* MCP 2025-11-25 tools over Streamable HTTP — the direction the Strands SDK does not cover. Reuses the SDK's `tool_spec`, reshapes `inputSchema.json` into MCP's flat `inputSchema`, and adapts `AgentTool.stream()` to synchronous `tools/call`.

### 8. Modular Home Resilience & Extension Engines (Appendix)
Beyond financial waste auditing and Subscribe & Save replenishments, Hearth provides modular resilience extensions operating under the same Propose-Never-Execute safety contract:
- **Acoustic Mechanical Doctor**: Echo ambient FFT vibration diagnostics detecting refrigerator bearing wear and staging replacement parts before breakdown (`acoustic.py`).
- **Black Box Forensic Reconstruction (Home CSI)**: Reverse causal physical walk disproving perimeter break-in false alarms from sensor telemetry (`forensics.py`).
- **Household Parliament (Dialectic Deliberation)**: Cooperative Nash bargaining resolving multi-resident comfort vs. peak energy tariff conflicts (`parliament.py`).
- **Causal Digital Twin (7-Day Stochastic Forecast)**: 150-iteration forward Monte Carlo thermal dynamics simulation anticipating grid vulnerabilities (`causal_twin.py`).
- **Confidential Family Mediation**: Zero-knowledge domestic treaty synthesizer with salted covenants for domestic harmony (`mediation.py`).
- **Neighborhood Swarm Grid (VPP)**: Localized solar peer-to-peer trading at $0.18/kWh over Streamable HTTP (`swarm.py`).
- **Autopilot Checkout & Time-Travel Debugger**: Voice-to-tray staging with Merkle receipts, 1-tap undo, and non-mutating decision replay (`replay.py`).

---

## ⚙️ How We Built It

- **MCP Server Core (`mcp>=1.29.1,<2`)**: Implemented FastMCP over **Streamable HTTP** with specification version **2025-11-25** on port `8787`. Exposes 51 hand-built tools (54 served live with forged skills mounted — the demo film mints another on camera: 54 → 55), 8 resources, and 3 prompt templates (counts verified live over the wire).
- **AWS Strands Agents SDK (`src/hearth/strands_agent.py`)**: Real `strands-agents` integration (`pip install -e ".[aws]"`). Three sub-agents built as `strands.Agent` objects with SDK-derived tool schemas, composed via `Agent.as_tool()`; every schema reported by `strands_sdk_status()` is produced by the SDK. A deterministic router remains the offline path so tests need no credentials.
- **Bedrock AgentCore (`src/hearth/agentcore.py`)**: Persistent session turns and cross-session episodic context retrieval.
- **Alexa Smart Home v3 Adapter (`src/hearth/alexa.py`)**: Standard directive handlers for `Alexa.Discovery`, `Alexa.PowerController`, `Alexa.ThermostatController`, `Alexa.LockController`, and camera stream controllers.
- **Official Rubric Evaluator (`scripts/evaluate_rubric.py`)**: 1-second automated verification across all competition rubrics.
- **Testing & Verification**: 305 automated unit, regression, contract, auth, UI-contract, and smoke tests passing (+15 open-source adapter tests = 320 total, 100% pass rate).

---

## 🏆 Accomplishments We're Proud Of

- **100% Zero-Config, Zero-Build Experience**: Judges and developers can clone the repo and run `python3 mcp-server/server.py` to experience the full multi-modal application with zero setup, no credit cards, and no device dependencies.
- **365 Automated Tests**: 100% pass rate with high test coverage across unit, regression, contract, auth, UI-contract, delivery clawback, and warroom IPC suites.
- **AWS Builder Champion**: Elevating AWS Builder from a single Bedrock call into a multi-service pipeline uniting Bedrock Converse, AgentCore Memory, and Strands Agents SDK.
- **Cryptographic Trust**: Verifiable mathematical proof that the AI agent never executes financial or security actions without human authorization.
- **Open Source Contribution**: `mcp-strands-adapter` covers the direction the SDK does not ship — exposing Strands agents *as* MCP tools, reusing the SDK's own `tool_spec` rather than re-deriving schemas. Apache-2.0, 15 standalone tests, real `mcp` and `strands-agents` dependencies declared honestly.

---

## 🚧 Challenges we ran into

- **Stateless session headers**: FastMCP in `stateless_http` mode tripped on proxy-injected `Mcp-Session-Id` — fixed with a session-tolerant middleware (see friction log #2, +10% bonus filed).
- **Bedrock region IDs**: cross-region inference needs `us.`-prefixed model IDs that docs bury — normalized with automatic prefixing + offline fallback (friction log #3).
- **Draft honesty**: our narrator once claimed "staged" for actions the guardrail blocked. Fixed at all 8 propose sites + locked with `test_child_persona_draft_never_claims_staged` — denials now read as denials.

---

## 🔮 What's next (beyond the hackathon)

1. **Live pilot**: 50-home beta on the deployed URL measuring $ saved, tap-to-approve rate, and undo rate.
2. **UCP checkout**: graduate the tray from staged proposals to Alexa+ Universal Commerce Protocol checkout sessions with dual-wallet.
3. **Utility + insurer channels**: peak-tariff shifting (TOU) and verified benign-alarm proofs as paid APIs — the trust layer makes autonomy sellable.
```

---

### Mandatory Devpost Fields

#### 1. Open Source Mini Challenge Submission
Copy the contents of [`docs/open_source_submission.md`](docs/open_source_submission.md) into the Open Source Mini Challenge section.

#### 2. Product Feedback & Friction Logs
- **Product Feedback**: Copy the contents of [`docs/product_feedback.md`](docs/product_feedback.md) into the Product Feedback field.
- **Friction Logs**: Copy the contents of [`docs/friction_logs.md`](docs/friction_logs.md) into the Friction Log field (for **up to 10% bonus points**!).
