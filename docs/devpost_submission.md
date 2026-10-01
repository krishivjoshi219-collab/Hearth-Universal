# Devpost Submission Form Guide & Copy

Use this document to quickly fill out the official **"Enter a Submission"** form on Devpost for the **Build, Ship, Shape: Amazon Developer Hackathon (2026)**.

---

### Project Title
**Hearth Universal — The Open Glass-Box Agent for Alexa+**

### Tagline / Short Description (1-2 Sentences)
An open-source, proactive personal operations agent for Amazon Alexa+ built on MCP 2025-11-25 Streamable HTTP. Features an Echo Show 15/21 Ambient Smart Canvas, autonomous subscription optimization, Ring doorbell vision, and Amazon Subscribe & Save replenishment under a strict propose-never-execute safety contract.

---

### Tracks & Categories Selected
- [x] **Primary Track**: **Alexa+** ($25,000 1st Place)
- [x] **Mini Challenge**: **AWS Builder** ($5,000 Prize)
- [x] **Mini Challenge**: **Open Source** ($5,000 Prize)

---

### Links & Video
- **GitHub Repository URL**: `https://github.com/krishivjoshi219-collab/Hearth-Universal`  
  *(Public repository with MIT License. Amazon Judges invited: `chris-trag`, `knmeiss`, `giolaq`, `anishamalde`, `mosesroth`, `emersonsklar`)*
- **Demo Video URL**: `<Your YouTube / Vimeo Link>` *(See `docs/demo_video_script.md` for the exact 2:45 storyboard)*

---

### Devpost Project Description (Markdown)

```markdown
## 💡 Inspiration
Today's voice assistants are often trapped in two extremes: either they are basic trivia bots that execute single-turn commands, or they are closed "black-box" agents that lack transparent safety boundaries. Households want an assistant that proactively solves real problems—auditing forgotten recurring subscriptions, restocking essentials before they run out, adjusting home climate when someone arrives early, and monitoring the front porch. But nobody wants an autonomous agent that silently charges their card, orders unwanted items, or unlocks doors without clear, transparent verification.

We built **Hearth Universal** to deliver the next generation of ambient intelligence for **Amazon Alexa+**: an autonomous, multi-tool operations agent built on the official **Model Context Protocol (MCP 2025-11-25)** that operates under an uncompromising principle: **Propose-Never-Execute**.

---

## 🛠️ What Hearth Universal Does

### 1. Dual-Mode Ambient OS: Echo Show 15/21 Smart Canvas & Ops Cockpit
- **Echo Show 15/21 Smart Canvas**: A high-design ambient wall display featuring real-time solar/battery energy flow vector diagrams, a live Ring doorbell HUD, quick scene triggers, an autonomous heartbeat ticker, and the **Pantry Depletion Radar**.
- **Interactive 2.5D Architectural Spatial Floorplan**: Vector architectural blueprint with dynamic ambient light radiance pools, micro-climate zoning, and real-time family occupancy dots (`Alex`, `Sarah`, `Leo`).
- **Glass-Box Time Machine**: Scrub future states (Bedtime 11 PM, Deep Night 3 AM, Morning Wake 7:30 AM) to simulate future solar battery levels, Infrared Night Vision on porch cams, and coffee replenishment alerts.
- **Glass-Box Ops Cockpit**: A deep-inspection desktop/tablet view showing multi-turn voice chat, DAG ReAct execution graphs, the Proposal Approval Tray, and the multi-room Digital Twin.

### 2. Autonomous Subscription & Financial Hygiene (Saves $803.76/yr)
- Scans 5 active household subscriptions and analyzes real usage telemetry.
- Detects dormant services (e.g. StreamBox 4K unused for 68 days) and low-utilization gym memberships.
- Calculates **$803.76/yr in actionable annual savings** and stages 1-tap cancellation/downgrade cards in the user's **Approval Tray**. Nothing moves money until tapped.

### 3. Family Arbiter & Conflict Negotiation Engine
- Autonomous Pareto-optimal conflict resolution for competing resident climate setpoints (e.g. Alex 20.0°C vs Sarah 23.0°C -> 21.5°C with eco airflow, saving $24.80/mo).
- Automatically shifts high-draw appliance loads (dishwasher, EV charging) out of peak tariff windows ($0.48/kWh down to $0.12/kWh).

### 4. Predictive Pantry Depletion, Amazon Prime Live Transit & Barcode Restock
- Models linear consumption velocity (`days_until_empty`) across household staples (Organic Whole Milk, Fair-Trade Coffee Beans, Dishwasher Pods).
- Live **Amazon Prime Transit Tracker**: Stepper tracking package progress from JFK8 fulfillment to Prime Van #482 (Driver Marcus, 2 stops away).
- Interactive **Pantry Barcode Scanner**: Simulated optical UPC barcode scanner that instantly scans items to replenish or flag depletion.
- Stages 1-tap **Amazon Subscribe & Save Cart Cards** with automated **15% bulk discount calculations** ($4.03 savings on coffee) and guaranteed Prime delivery slots (e.g. *Tomorrow, 8 AM - 11 AM*).

### 5. Interactive MCP Apps (Rich Media & Micro-UIs)
- Exposes interactive mini-applications directly inside tool execution payloads:
  - **Lighting Designer App**: Interactive HTML5 color wheel canvas with live CCT (2700K - 6500K) and RGB gamut picker.
  - **Subscription ROI Simulator**: Dynamic budget slider recalculating 1-year and 3-year compound savings in real time.
  - **Amazon Restock Cart**: Interactive item selector with automated coupon and quantity adjustment.

### 6. Ring Doorbell & Camera Stream Controller (`Alexa.DoorbellEventSource`)
- Full compliance with the **Alexa Smart Home v3 API** for video doorbells and security cameras.
- Features a procedural **1080p Porch Camera Canvas Simulator** with scanlines, live timestamp, motion box detection, visitor snapshot capture, and authentic **Infrared Night Vision**.
- Responds to `Alexa.DoorbellEventSource` directives: plays an authentic dual-tone acoustic chime (Web Audio C5/E5), pops a visitor card, and offers a 1-tap porch light safety trigger.

### 7. Multi-Persona Sentinel Safety Matrix (Adult vs. Child Guardrails)
- 3-tier security gate: Tier-1 (Safe read-only), Tier-2 (Consequential actions routed to human tray), and Tier-3 (Hard-blocked destructive commands).
- **Persona Context Awareness**: Switching from `Alex` (Adult Owner) to `Leo` (Child / Age 9) automatically activates child safety guardrails—blocking all credit card transactions, financial orders, and perimeter door unlocks while permitting safe comfort actions (nightlight, bedtime stories).

### 8. Multi-Brain Orchestrator & Cryptographic SHA-256 Ledger
- Swappable brain backends: **Amazon Bedrock (Claude 3.5 Sonnet / Amazon Nova)**, OpenAI, or local Ollama, backed by a zero-config offline ReAct engine.
- Immutably records every AI proposal, human approval, and Sentinel block in an append-only SHA-256 hash chain (`audit.jsonl`).
- 1-tap **Cryptographic Inspection Modal** verifies mathematical tamper-evidence, dependency traces, and rollback states.

---

## ⚙️ How We Built It

- **MCP Server Core (`mcp>=1.29.1,<2`)**: Implemented FastMCP over **Streamable HTTP** with specification version **2025-11-25** on port `8787`. Exposes 33 tools, 4 resources, and 3 prompt templates.
- **Amazon Alexa Smart Home v3 Adapter (`src/hearth/alexa.py`)**: Built standard directive handlers for `Alexa.Discovery`, `Alexa.PowerController`, `Alexa.ThermostatController`, `Alexa.LockController`, `Alexa.DoorbellEventSource`, and `Alexa.CameraStreamController`.
- **Commerce & Depletion Engine (`src/hearth/commerce.py`)**: Designed consumption forecasting models, Prime delivery window allocation, and Subscribe & Save tiered discount logic.
- **Family Arbiter (`src/hearth/arbiter.py`)**: Multi-resident Pareto-optimal conflict negotiation engine with peak-tariff shaving.
- **Glass-Box Time Machine (`src/hearth/timemachine.py`)**: Predictive temporal simulation engine scrubbing future states.
- **Sentinel Safety Matrix (`src/hearth/sentinel.py`)**: Engineered persona-aware policy gating, regex threat interception (`rm -rf`, token leaks), and single-use approval receipt validation.
- **Amazon Bedrock Integration (`src/hearth/brains.py`)**: Wired the standardized AWS Bedrock Converse API (`client.converse()`) for Claude 3.5 Sonnet and Amazon Nova Pro with token telemetry tracking.
- **Modular Zero-Build Frontend (`web/`)**: Built a zero-build, responsive PWA using clean ES6+ modules (`voice.js`, `twin.js`, `mcp-apps.js`, `proposals.js`, `app.js`) and modular CSS (`main.css`, `canvas.css`, `cards.css`, `modal.css`). Runs instantly in any browser without Node, npm, or bundlers.
- **Testing & Verification**: 141 automated unit, regression, contract, auth, and over-the-wire smoke tests. 100% pass rate in ~25s.

---

## 🚧 Challenges We Ran Into

- **Streamable HTTP Header Negotiation**: Handshaking over Streamable HTTP required strict handling of `Accept: application/json, text/event-stream` headers to avoid 406 responses when communicating with cloud or curl clients.
- **Stateless Session Affinity**: Routing traffic behind AWS proxies while maintaining FastMCP's stateless execution required custom middleware to safely ignore synthetic session headers.
- **FastMCP Static File Routing**: Serving modular client assets (`/css/*`, `/js/*`) alongside Streamable HTTP `/mcp` endpoints required configuring custom Starlette sub-mounts on the underlying ASGI application.
- **Balancing Agency with Human Control**: Creating a system that feels truly autonomous (proactive multi-step audits) without feeling risky required inventing the Glass-Box Proposal Tray where every action has an explicit cost delta, child safety check, and before/after diff.

---

## 🏆 Accomplishments We're Proud Of

- **100% Zero-Config, Zero-Build Experience**: Judges and developers can clone the repo and run `python mcp-server/server.py` to experience the full multi-modal application with zero setup, no credit cards, and no device dependencies.
- **141 Automated Tests**: Unit, regression, auth-fortress, reliability, contract, and over-the-wire smoke tests running in ~25 seconds.
- **Cryptographic Trust**: Verifiable mathematical proof that the AI agent never executes financial or security actions without human authorization.
- **Rich Media & Interactive MCP Apps**: Setting a new benchmark for Alexa+ multimodal UI by delivering interactive color wheels, ROI sliders, and cart carousels directly from tool invocations.

---

## 🔮 What's Next for Hearth Universal

- Direct integration with real Matter / Home Assistant hubs over local network websockets.
- Multi-user biometric voice profiles on Echo Show devices so only authorized adults can approve financial proposals.
- Real-time Fire TV companion card rendering for big-screen household dashboards.
```

---

### Mandatory Devpost Questions: Product Feedback & Friction Logs
- **Product Feedback**: Copy the contents of [`docs/product_feedback.md`](file:///home/k/Prototype/Amazon/docs/product_feedback.md) into the Product Feedback field.
- **Friction Logs**: Copy the contents of [`docs/friction_logs.md`](file:///home/k/Prototype/Amazon/docs/friction_logs.md) into the Friction Log field (for **up to 10% bonus points**!).
