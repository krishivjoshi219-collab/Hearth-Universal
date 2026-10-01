# Hearth Universal 🏠⚡
### The Open Glass-Box Household Operations Agent for Amazon Alexa+
**Built for the "Build, Ship, Shape: Amazon Developer Hackathon" (Devpost 2026)**

[![MCP Spec](https://img.shields.io/badge/MCP%20Spec-2025--11--25-blue)](https://modelcontextprotocol.io)
[![Transport](https://img.shields.io/badge/Transport-Streamable%20HTTP-00d2ff)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 54 Passed](https://img.shields.io/badge/Tests-54%20Passed-emerald)](tests/)
[![Execution Time](https://img.shields.io/badge/Suite%20Speed-9.03s-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue)](pyproject.toml)

> **Hearth Universal** is an open-source, proactive personal agent for Alexa+ that orchestrates household finances, automated replenishment, and smart home digital twins under an uncompromising **propose-never-execute** safety contract. It features an **Apple Intelligence meets Echo Show 15/21 Ambient Smart Canvas** (Dual-Mode Canvas vs Ops Cockpit), an interactive **2.5D Architectural Spatial Floorplan** with dynamic ambient lighting pools, a **Glass-Box Time Machine** for predictive future scrubbing, a **Family Arbiter** for multi-resident conflict resolution and peak-tariff load shifting, an **Amazon Prime Live Delivery Tracker & Barcode Scanner**, interactive **MCP Apps** (Lighting Designer, Subscription ROI, Pantry Restock), a **Ring Doorbell & 1080p Camera simulator** with Infrared Night Vision, **Amazon Subscribe & Save Depletion Radar**, native **Alexa Smart Home v3 Directive Adapter**, and multi-persona child safety guardrails. Works out-of-the-box with zero-config local intelligence, with live support for **Amazon Bedrock (Claude 3.5 Sonnet / Amazon Nova)**, OpenAI, or local Ollama.

---

## 🏆 Hackathon Tracks & Challenges

- **Primary Track: Alexa+ ($25,000 Prize)**
  - Self-hosted MCP server implementing **MCP Spec version 2025-11-25** over Streamable HTTP (`/mcp`).
  - Native **Amazon Alexa Smart Home Skills API v3 Directive Adapter** (`/api/alexa/directive`) for `Alexa.Discovery`, `Alexa.PowerController`, `Alexa.ThermostatController`, and `Alexa.LockController`.
  - Drop-in **Agent Skill package** (`skill/SKILL.md`) with **20 tools**, 4 resources, and 3 prompt templates, plus `skill/skill.json` ASK manifest and `skill/apl_smart_canvas.json` APL Echo Show 15/21 template.
  - Multi-modal simulated Alexa+ experience featuring voice recognition, Alexa speech synthesis, interactive ReAct/DAG visualizer, and rich action cards.
- **Mini Challenge: AWS Builder ($5,000 Prize)**
  - Full **Amazon Bedrock Converse API** integration (`src/hearth/brains.py`) supporting **Claude 3.5 Sonnet** and **Amazon Nova Pro** (`us.amazon.nova-pro-v1:0`) via cross-region inference profiles, with botocore adaptive retries, proper `system=[]` isolation, and Bedrock-native `metrics.latencyMs` telemetry.
  - Dockerized runtime for AWS App Runner / ECS / EC2 (`infra/Dockerfile` · `infra/apprunner.yaml` · `infra/iam-bedrock-policy.json`), runs as non-root `hearth` user on port 8787 with persistent `/data` volume.
- **Mini Challenge: Open Source ($5,000 Prize)**
  - Clean, permissive MIT open-source repository with comprehensive documentation, **64 automated unit & smoke tests** (3 covering Amazon Bedrock Converse API schema & model routing), GitHub Actions CI, `Makefile`, and Sentinel security guardrails.

---

## 🏗️ Architecture

```mermaid
flowchart TD
    User(["🗣️ User Voice / Web Surface\n(Alexa+ Echo Show Simulator)"])
    
    subgraph Hearth_Core ["Hearth Universal MCP Core (:8787)"]
        Server["Streamable HTTP MCP Server\n(Spec 2025-11-25)"]
        Planner["Autonomous DAG Planner\n(Intent & Multi-Tool ReAct)"]
        Sentinel{"Sentinel Guardrails\n(Allow / Ask / Deny)"}
        Vault["Secret Vault\n({{vault:NAME}} + Redaction)"]
        
        subgraph Brains ["Universal Brain Adapters"]
            Bedrock["AWS Bedrock\n(Claude 3.5 Sonnet / Nova)"]
            LocalAgent["Intelligent Local Engine\n(Zero-Config Offline)"]
            OpenAI["OpenAI / Ollama\n(Compatible Endpoint)"]
        end
        
        subgraph Subsystems ["Household Subsystems"]
            Twin["Smart Home Digital Twin\n(Multi-Room, Climate, Lock)"]
            Commerce["Household Commerce\n(Subscriptions & Replenishment)"]
            Memory[("SQLite Memory\n(Facts & Goals)")]
            Ledger[("SHA-256 Merkle Ledger\n(audit.jsonl)")]
        end
        
        Tray["📥 Glass-Box Approval Tray\n(Propose-Never-Execute)"]
    end
    
    User -->|Voice / JSON-RPC| Server
    Server --> Planner
    Planner --> Brains
    Planner --> Sentinel
    Sentinel -->|Safe Read-Only| Subsystems
    Sentinel -->|Consequential| Tray
    Sentinel -->|Adversarial Command| Ledger
    Tray -->|Human 1-Tap Tap| Subsystems
    Subsystems --> Ledger
    Server -->|TTS Audio + Rich Cards| User
```

---

## ⚡ 60-Second Quickstart (Zero Configuration Needed)

No external API keys, credit cards, or physical devices required. The project includes an intelligent local agent engine so judges can test immediately.

```bash
# 1. Clone repository
git clone https://github.com/krishivjoshi219-collab/Hearth-Universal.git
cd hearth-universal

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Launch server (starts MCP + REST + Alexa+ Simulator on port 8787)
python mcp-server/server.py
```

Open your browser to:
👉 **`http://localhost:8787`**

### Live MCP Protocol Verification:
```bash
# Handshake with MCP 2025-11-25 Streamable HTTP endpoint
curl -s http://localhost:8787/mcp -H 'Content-Type: application/json' \
 -H 'Accept: application/json, text/event-stream' \
 -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'
```
*Expected response contains `"protocolVersion": "2025-11-25"`.*

### Run Automated Tests:
```bash
pytest -v
```

---

## ☁️ Optional: Live AWS Bedrock & Cloud Brains

To connect to live cloud models, set standard environment variables:

```bash
# Option A: Amazon Bedrock (AWS Builder Challenge)
export AWS_BEDROCK_ENABLED=1
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_BEDROCK_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0

# Option B: OpenAI / OpenRouter / Together
export VAULT_MODEL_KEY=sk-your-key
export HEARTH_BASE_URL=https://api.openai.com/v1
export HEARTH_MODEL=gpt-4o-mini

# Option C: Self-Hosted Ollama
export HEARTH_BASE_URL=http://localhost:11434/v1
export HEARTH_MODEL=llama3
```

### ⚙️ Product operations (no code changes needed)
```bash
cp config.example.yaml config.yaml  # file-based brain/port config (env vars still win)
HEARTH_SCHEDULER=1 python mcp-server/server.py  # background thread advances active goals hourly
```
State is crash-safe (file locks + atomic writes) and survives restarts (`state/`); chat history is capped at 500 turns; `/api/chat` is rate-limited (30/min/IP, `HEARTH_CHAT_RPM`); proposals are single-use with execution receipts.

---

## 🌟 Key Capabilities & Differentiators

| Feature | Obvious Implementation (Chatbot) | Hearth Universal (Agentic Alexa+) |
| :--- | :--- | :--- |
| **Interface & Form Factor** | Basic chat window | **Echo Show 15/21 Dual Canvas**: Glanceable ambient countertop mode + deep Glass-Box operations console. |
| **Safety Model** | Blindly runs actions or refuses | **Propose-Never-Execute**: Proactive drafts, transparent cost delta, 1-tap human approval tray with single-use receipts. |
| **Spatial Awareness** | Static device list | **2.5D Architectural Spatial Floorplan**: Live vector blueprint with dynamic ambient light radiance, micro-climate zoning, and family occupancy dots. |
| **Predictive Simulation** | Reactive only | **Glass-Box Time Machine**: Scrub future states (Bedtime, Deep Night, Morning Wake) to project solar battery shifts, infrared night vision, and morning replenishment. |
| **Conflict Resolution** | Rigid rules or fails | **Family Arbiter Engine**: Multi-party Pareto-optimal negotiation for competing resident climate setpoints and peak-tariff load shifting. |
| **Package & Delivery Ops** | Mock tracking | **Amazon Prime Live Transit Tracker & Barcode Scanner**: Live AMZL delivery milestones, courier stops away, and optical UPC pantry restock. |
| **Interactive MCP Apps** | Static text outputs | **Client Micro-Apps**: Dynamic CCT/RGB Lighting Designer, Subscription ROI simulator, Amazon Cart Builder. |
| **Commerce & Purchasing** | "Go buy coffee" text advice | **Amazon Subscribe & Save Radar**: Consumable depletion velocity (`days_until_empty`), 15% bundle deal matching, 1-click checkout. |
| **Perimeter Security** | Text notification | **Ring Camera Simulator & Directives**: Live video stream canvas, simulated doorbell chime, 1-tap visitor access pass. |
| **Multi-Persona Profiles** | Single generic profile | **Role-Based Biometrics**: Admin (Krishiv), Partner (Sarah), and Child (`Leo`) with automatic child safety guardrails. |
| **Subscription Hygiene** | Lists advice in chat | **Automated ROI Audit**: Scans 5 active services, detects dormancy, calculates **$803.76/yr** savings, and drafts cancellations. |
| **Voice & Acoustics** | Speech synthesis only | **Authentic Alexa Light Wave & Echo Chimes**: Fluid canvas sound wave visualizer + procedural Web Audio acoustic chimes. |
| **Security & Auditing** | None | **Cryptographic SHA-256 Ledger**: Immutable append-only Merkle trail verifying every agent and human action. |

---

## 🛠️ MCP Tool Registry (Spec 2025-11-25)

1. `memory_query`: Query persistent household preferences, dietary rules, and budgets.
2. `memory_remember`: Securely persist household facts into SQLite with Vault secret redaction.
3. `goals_create` & `goals_advance`: Manage long-running asynchronous household milestones.
4. `home_get_state`: Inspect multi-room lighting, climate, locks, media, and solar/energy draw.
5. `home_set_scene`: Apply coordinated presets (`evening-calm`, `movie-night`, `away`, `wake`, `energy-saver`). *(Gated)*
6. `home_routine`: Execute multi-step household routines with timers and audio queues. *(Gated)*
7. `home_toggle_lock`: Actuate front door smart lock. *(Gated)*
8. `inbox_scan`: Audit recurring subscriptions and dormant services to recover wasted spend.
9. `commerce_list_inventory`: Monitor consumable pantry levels (coffee, detergent, air filters).
10. `commerce_scan_deals`: Match household essentials with active Subscribe & Save bundle discounts.
11. `actions_propose`: Stage structured action cards in the Approval Tray.
12. `actions_list_proposals`: Retrieve current status of proposed household actions.
13. `actions_decide`: Record human approval or rejection (Human-surface only).
14. `planner_orchestrate`: Decompose high-level goals into multi-tool execution DAGs.
15. `audit_verify`: Cryptographically verify the integrity of the SHA-256 hash chain.

---

## 🔒 Sentinel Safety & Security Matrix

Sentinel enforces a strict 3-tier policy engine:
- **Tier 1 (Autonomous / Allow)**: Reads, lighting, climate, scenes, engaging locks, goals. Executes immediately — comfort should never wait for approval.
- **Tier 2 (Consequential / Ask)**: Moving money, cancelling services, ordering items, or UNLOCKING physical doors. Fail-closed: direct calls return `approval_required` and stage a tray proposal; approval executes once (replay refused, execution receipt stored).
- **Tier 3 (Dangerous / Deny)**: Shell code execution (`rm -rf /`, `mkfs`), raw credential access (`{{vault:...}}`), and unapproved wire transfers are hard-blocked and logged to the cryptographic ledger.

### ✅ Claim map (what's real vs simulated — verify it yourself)
| Claim | Status | Proof |
|---|---|---|
| MCP 2025-11-25 Streamable HTTP, stateless | Real | `curl .../mcp initialize` → `protocolVersion`, or `pytest tests/test_mcp_http.py` (live server, 4 checks) |
| Unlock gating over bare MCP | Real, fail-closed | smoke test asserts `approval_required`, door stays locked |
| Approval executes + single-use | Real | `test_decide_single_use`; receipts in `state/proposals.json` |
| Home persists across restart | Real | kill + restart server, scene/lock intact (`state/home.json`) |
| Bedrock/OpenAI/Ollama brains | Real code path, needs your key/creds | `src/hearth/brains.py`; without creds the local offline engine answers |
| Subscriptions, pantry, home devices | Fixture data (sandbox has no bank/Hue APIs) | `src/hearth/commerce.py`, `home_mock.py` — stated openly, numbers computed not hardcoded |
| Alexa+ on-device rendering | Simulated web UI | visual twin of the MCP loop for judges without devices |
| Trip research, rulebook lookup, code execution | Real tools, live data | `web_search` (fallback chain, ads filtered), `web_fetch` (SSRF-blocked), jailed `workspace_exec/write` — try "plan a trip", "check the rules", "run ..." |
| General agency beyond scripted intents | Real for live brains | ReAct JSON loop (`tests/test_hearth.py::test_react_loop_gates_and_grounds`); offline engine stays deterministic and exact |

---

## 👥 Hackathon Reviewer Setup (Private GitHub Repos)

If reviewing as part of the official Amazon judging panel, add the following GitHub accounts as collaborators in **Settings > Collaborators > Add people**:
- `chris-trag`
- `knmeiss`
- `giolaq`
- `anishamalde`
- `mosesroth`
- `emersonsklar`

---

## 📜 Documentation Index

- [Product Feedback (Mandatory Hackathon Questions)](docs/product_feedback.md)
- [Friction Logs (10% Bonus Points Submission)](docs/friction_logs.md)
- [AWS Builder Integration Guide](docs/aws_builder_integration.md)
- [Demo Video Storyboard (<3 Minutes)](docs/demo_video_script.md)
- [Devpost Final Submission Text](docs/devpost_submission.md)

---

## 📄 License

Licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
