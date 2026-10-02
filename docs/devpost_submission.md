# Devpost Submission Form Guide & Copy

Use this document to quickly fill out the official **"Enter a Submission"** form on Devpost for the **Build, Ship, Shape: Amazon Developer Hackathon (2026)**.

---

### Project Title
**Hearth Universal — The Open Glass-Box Agent for Alexa+**

### Tagline / Short Description (1-2 Sentences)
An open-source, proactive personal operations agent for Amazon Alexa+ built on MCP 2025-11-25 Streamable HTTP. Features an AWS Strands multi-agent supervisor, Bedrock AgentCore persistent memory, multi-room digital twin orchestration, and Subscribe & Save replenishment under a strict propose-never-execute safety contract.

---

### Tracks & Categories Selected
- [x] **Primary Track**: **Alexa+** ($25,000 1st Place)
- [x] **Mini Challenge**: **AWS Builder** ($5,000 Prize + $5,000 AWS Credits)
- [x] **Mini Challenge**: **Open Source** ($5,000 Prize + $5,000 AWS Credits)

---

### Links & Video
- **GitHub Repository URL**: `https://github.com/krishivjoshi219-collab/Hearth-Universal`  
  *(Public repository with MIT License. Amazon Reviewers invited: `chris-trag`, `knmeiss`, `giolaq`, `anishamalde`, `mosesroth`, `emersonsklar`)*
- **Demo Video URL**: `<Your YouTube / Vimeo Link>` *(See `docs/demo_video_script.md` for the exact storyboard)*

---

### Devpost Project Description (Markdown)

```markdown
## 💡 Inspiration
Today's voice assistants are often trapped in two extremes: either they are basic trivia bots that execute single-turn commands, or they are closed "black-box" agents that lack transparent safety boundaries. Households want an assistant that proactively solves real problems—auditing forgotten recurring subscriptions, restocking essentials before they run out, and adjusting home climate when someone arrives early. But nobody wants an autonomous agent that silently charges their card, orders unwanted items, or unlocks doors without clear, transparent verification.

We built **Hearth Universal** to deliver the next generation of ambient intelligence for **Amazon Alexa+**: an autonomous, multi-agent operations agent built on the official **Model Context Protocol (MCP 2025-11-25)** over Streamable HTTP that operates under an uncompromising principle: **Propose-Never-Execute**.

---

## 🛠️ What Hearth Universal Does

### 1. Dual-Mode Ambient OS: Echo Show 15/21 Smart Canvas & Ops Cockpit
- **Echo Show 15/21 Smart Canvas**: A high-design ambient wall display featuring real-time solar/battery energy flow vector diagrams, quick scene triggers, an autonomous heartbeat ticker, and the **Pantry Depletion Radar**.
- **Interactive 2.5D Architectural Spatial Floorplan**: Vector architectural blueprint with dynamic ambient light radiance pools, micro-climate zoning, and real-time family occupancy dots (`Alex`, `Sarah`, `Leo`).
- **Glass-Box Time Machine**: Scrub future states (Bedtime 11 PM, Deep Night 3 AM, Morning Wake 7:30 AM) to simulate future solar battery levels, lighting scenes, and replenishment alerts.
- **Glass-Box Ops Cockpit**: A deep-inspection desktop/tablet view showing multi-turn voice chat, DAG ReAct execution graphs, the Proposal Approval Tray, and the multi-room Digital Twin.

### 2. AWS Builder Multi-Service Pipeline: Strands Agents SDK & Bedrock AgentCore
- **AWS Strands Multi-Agent Supervisor Pattern**: Coordinates specialized domain sub-agents:
  - `ArbiterNegotiatorAgent`: Resolves resident preference disputes with Pareto efficiency and shifts high-draw loads off peak energy tariffs.
  - `ReplenishmentDepletionAgent`: Evaluates consumable depletion velocities and maximizes 15% Subscribe & Save discounts.
  - `SentinelGuardianAgent`: Enforces 3-tier risk gating, child guardrails, and cryptographic audits.
- **AWS Bedrock AgentCore Memory**: Emulates the serverless AgentCore Memory architecture for persistent session turns and cross-session episodic memory retrieval.
- **Amazon Bedrock Converse Multi-Model Router**: Dynamic routing between **Claude 3.5 Sonnet** (deep reasoning) and **Amazon Nova Pro** (structured fast planning) with adaptive retries and `system=[]` prompt isolation.

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
- Publishes **[`mcp-strands-adapter`](open-source-contribution/mcp-strands-adapter/)**: a standalone open-source library bridging AWS Strands Agents SDK to FastMCP 2025-11-25 over Streamable HTTP.

---

## ⚙️ How We Built It

- **MCP Server Core (`mcp>=1.29.1,<2`)**: Implemented FastMCP over **Streamable HTTP** with specification version **2025-11-25** on port `8787`. Exposes 35 tools, 4 resources, and 3 prompt templates.
- **AWS Strands Agents SDK (`src/hearth/strands_agent.py`)**: Multi-agent supervisor pattern delegating to Arbiter, Replenishment, and Sentinel agents.
- **Bedrock AgentCore (`src/hearth/agentcore.py`)**: Persistent session turns and cross-session episodic context retrieval.
- **Alexa Smart Home v3 Adapter (`src/hearth/alexa.py`)**: Standard directive handlers for `Alexa.Discovery`, `Alexa.PowerController`, `Alexa.ThermostatController`, `Alexa.LockController`, and camera stream controllers.
- **Official Rubric Evaluator (`scripts/evaluate_rubric.py`)**: 1-second automated verification across all competition rubrics.
- **Testing & Verification**: 159 automated unit, regression, contract, auth, and smoke tests passing in ~24s.

---

## 🏆 Accomplishments We're Proud Of

- **100% Zero-Config, Zero-Build Experience**: Judges and developers can clone the repo and run `python3 mcp-server/server.py` to experience the full multi-modal application with zero setup, no credit cards, and no device dependencies.
- **159 Automated Tests**: 100% pass rate in ~24 seconds.
- **AWS Builder Champion**: Elevating AWS Builder from a single Bedrock call into a multi-service pipeline uniting Bedrock Converse, AgentCore Memory, and Strands Agents SDK.
- **Cryptographic Trust**: Verifiable mathematical proof that the AI agent never executes financial or security actions without human authorization.
- **Open Source Contribution**: Creating the first turnkey bridge between AWS Strands and FastMCP 2025-11-25.
```

---

### Mandatory Devpost Fields

#### 1. Open Source Mini Challenge Submission
Copy the contents of [`docs/open_source_submission.md`](docs/open_source_submission.md) into the Open Source Mini Challenge section.

#### 2. Product Feedback & Friction Logs
- **Product Feedback**: Copy the contents of [`docs/product_feedback.md`](docs/product_feedback.md) into the Product Feedback field.
- **Friction Logs**: Copy the contents of [`docs/friction_logs.md`](docs/friction_logs.md) into the Friction Log field (for **up to 10% bonus points**!).
