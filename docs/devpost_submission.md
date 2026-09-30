# Devpost Submission Form Guide & Copy

Use this document to quickly fill out the official **"Enter a Submission"** form on Devpost for the **Build, Ship, Shape: Amazon Developer Hackathon**.

---

### Project Title
**Hearth Universal — The Open Glass-Box Agent for Alexa+**

### Tagline / Short Description (1-2 Sentences)
An open-source, proactive personal operations agent for Amazon Alexa+ built on MCP 2025-11-25 Streamable HTTP. Manages subscriptions, pantry replenishment, and smart homes under a strict propose-never-execute safety contract.

---

### Tracks & Categories Selected
- [x] **Primary Track**: **Alexa+** ($25,000 1st Place)
- [x] **Mini Challenge**: **AWS Builder** ($5,000 Prize)
- [x] **Mini Challenge**: **Open Source** ($5,000 Prize)

---

### Links & Video
- **GitHub Repository URL**: `https://github.com/krishivjoshi219-collab/Hearth-Universal`  
  *(Make sure repo is Public with MIT License, OR if private, add the 6 Amazon judges as collaborators: `chris-trag`, `knmeiss`, `giolaq`, `anishamalde`, `mosesroth`, `emersonsklar`)*
- **Demo Video URL**: `<Your YouTube / Vimeo Link>` *(See `docs/demo_video_script.md` for the exact 2:45 storyboard)*

---

### Devpost Project Description (Markdown)

```markdown
## 💡 Inspiration
Today's voice assistants are often trapped in two extremes: either they are basic trivia bots that execute single-turn commands, or they are closed "black-box" agents that lack transparent safety boundaries. Households want an assistant that proactively solves real problems—like auditing forgotten recurring subscriptions, restocking essentials before they run out, and preparing the house when someone arrives home early. But nobody wants an autonomous agent that silently charges their card or unlocks doors without clear, transparent verification.

We built **Hearth Universal** to deliver the next generation of ambient intelligence for **Amazon Alexa+**: an autonomous, multi-tool operations agent built on the official **Model Context Protocol (MCP 2025-11-25)** that operates under an uncompromising principle: **Propose-Never-Execute**.

---

## 🛠️ What Hearth Universal Does

1. **Autonomous Subscription & Financial Hygiene (Saves $803.76/yr)**:
   - Scans 5 active household subscriptions and analyzes usage telemetry.
   - Detects dormant services (e.g. StreamBox 4K unused for 68 days) and low-utilization gym plans.
   - Calculates **$803.76/yr in actionable annual savings** and stages 1-tap cancellation/downgrade cards in the user's **Approval Tray**. Nothing moves money until tapped.

2. **Smart Home Digital Twin & Ambient Actuation**:
   - Maintains a live multi-room digital twin (Living Room, Bedroom, Kitchen, Entryway).
   - Coordinates multi-device scenes (`evening-calm`, `movie-night`, `away`, `wake`, `energy-saver`) adjusting dimmable warm/cool lighting, HVAC thermostat setpoints, and smart locks.
   - Displays real-time energy telemetry (current draw, solar generation, and eco-score).

3. **Household Commerce & Consumable Replenishment**:
   - Tracks consumable pantry levels (Coffee 15%, Laundry Pods 10%, Air Filters 20%).
   - Discovers active Subscribe & Save bundle deals that save $7.50 on essential replenishment.
   - Stages checkout cards in the approval tray with transparent pricing diffs.

4. **Multi-Tool ReAct / DAG Orchestrator with Live Visualizer**:
   - Decomposes high-level natural language requests into parallel dependency graphs (`memory_query` -> `inbox_scan` -> `sentinel_judge` -> `actions_propose`).
   - Renders animated execution steps directly inside the simulated Alexa+ interface.

5. **Multi-Brain Egress & Sentinel Safety Matrix**:
   - Enforces a 3-tier security gate: Tier-1 (Safe read-only), Tier-2 (Consequential actions routed to human tray), and Tier-3 (Hard-blocked destructive commands like `rm -rf /` or credential exfiltration).
   - Swappable brain backends: **Amazon Bedrock (Claude 3.5 Sonnet / Amazon Nova)**, OpenAI, or local Ollama, with an intelligent zero-config offline engine so anyone can test in seconds.

6. **Cryptographic SHA-256 Audit Ledger**:
   - Immutably records every AI proposal, human approval, and Sentinel block in an append-only hash chain (`audit.jsonl`), verifiable with 1 click in the UI.

---

## ⚙️ How We Built It

- **MCP Server Core (`mcp>=1.29.1`)**: Implemented FastMCP over **Streamable HTTP** with specification version **2025-11-25** on port `8787`. Exposes 15 tools, 4 resources, and 3 prompt templates.
- **Agent Skill (`skill/SKILL.md`)**: Engineered a standardized skill specification for Alexa+ orchestrators detailing tool contracts and safety guardrails.
- **Amazon Bedrock Integration (`src/hearth/brains.py`)**: Wired the standardized AWS Bedrock Converse API (`client.converse()`) for Claude 3.5 Sonnet and Amazon Nova.
- **Frontend / Simulated Alexa+ Experience (`web/`)**: Built a zero-build, responsive ambient Echo Show dashboard featuring the glowing Alexa+ acoustic orb, two-way Web Speech Synthesis & Recognition, live DAG flow rendering, and digital twin controls.
- **Persistence & Cryptography**: SQLite for persistent facts and goals; SHA-256 Merkle chain for tamper-evident auditing.

---

## 🚧 Challenges We Ran Into

- **Streamable HTTP Header Negotiation**: Handshaking over Streamable HTTP required precise handling of `Accept: application/json, text/event-stream` headers to avoid 406 responses.
- **Stateless Session Affinity**: Routing traffic behind cloud proxies while maintaining FastMCP's stateless execution required custom middleware to ignore synthetic session IDs.
- **Balancing Agency with Human Control**: Creating a system that feels truly autonomous (proactive multi-step audits) without feeling risky required inventing the Glass-Box Proposal Tray where every action has an explicit cost delta and before/after diff.

---

## 🏆 Accomplishments We're Proud Of

- **100% Zero-Config Experience**: Judges and developers can clone the repo and run `python mcp-server/server.py` to experience the full multi-modal application with zero setup, no credit cards, and no device dependencies.
- **Sub-Second Test Suite**: 14 automated unit/integration tests running in under 0.9 seconds.
- **Cryptographic Trust**: Verifiable mathematical proof that the AI agent never executes without human authorization.

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
