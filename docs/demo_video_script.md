# Demo Video Storyboard & Script (<3:00)

**Project:** Hearth Universal — The Open Glass-Box Agent for Alexa+  
**Primary Track:** Alexa+ ($25,000 1st Place)  
**Mini-Challenges:** AWS Builder ($5,000), Open Source ($5,000)  
**Target Video Duration:** 2 minutes 45 seconds  
**Platforms to Display:** Terminal (FastMCP Handshake, Test Suite, Rubric Evaluator) + Web Browser (Echo Show 15/21 Ambient Smart Canvas & Glass-Box Ops Cockpit on `localhost:8787`).

---

### [0:00 - 0:25] The Problem & The Core Innovation
- **Visual**: Camera starts on title screen: *"Hearth Universal — The Open Glass-Box Agent for Alexa+"*. Transition to split screen showing modern home chaos: forgotten subscriptions, depleting pantry items, and "black box" AI assistants that either do nothing or risk unintended actions.
- **Narrator (Voiceover)**:
  > *"Voice assistants used to just answer trivia or set timers. With Alexa+, we can build proactive agentic workflows that solve complex household problems. But households don't want black-box agents that silently spend money, order unwanted items, or unlock doors without permission.*  
  > *Meet **Hearth Universal**: an open-source, glass-box operations agent for Alexa+ built on the new **MCP 2025-11-25 Streamable HTTP specification**. It coordinates an AWS Strands multi-agent supervisor, Bedrock AgentCore memory, and operates under an uncompromising principle: **Propose-Never-Execute**."*

---

### [0:25 - 0:50] 60-Second Setup & MCP Spec Verification
- **Visual**: Screen capture of terminal.
  - Run: `python3 mcp-server/server.py` (shows FastMCP starting on port `8787` with 50 tools).
  - Run: `curl POST /mcp` initialize request. Output displays `"protocolVersion": "2025-11-25"`.
  - Run: `pytest -q` (**222 passing tests**).
  - Run: `python3 scripts/evaluate_rubric.py` (shows 100/100 all criteria passing).
- **Narrator**:
  > *"Hearth is completely zero-friction and zero-build. It requires no closed API keys, Node.js, or cloud hardware to evaluate. Our server exposes a fully compliant MCP 2025-11-25 Streamable HTTP endpoint. As you can see, our official rubric evaluator verifies all 222 tests and protocol handshakes across Alexa+, AWS Builder, and Open Source."*

---

### [0:50 - 1:15] Echo Show 15/21 Ambient Smart Canvas & Spatial Floorplan
- **Visual**: Browser opens to `http://localhost:8787` on the **Ambient Smart Canvas** view.
  - Highlight the sleek Apple Intelligence & Echo Show 15/21 layout.
  - Show the live **Solar / Grid / Battery Energy Flow** vector diagram animating power distribution.
  - Show the **Pantry Depletion Radar**: Organic Milk (Critical - 1 day), Fair-Trade Coffee (Urgent - 2 days).
  - Show the interactive **2.5D Architectural Spatial Floorplan** with light radiance pools and real-time family occupancy dots (`Alex`, `Sarah`, `Leo`).
  - Demonstrate the **Glass-Box Time Machine**: scrub to Bedtime (11 PM) to see future energy storage and automated night scenes.
- **Narrator**:
  > *"This is the Echo Show Ambient Smart Canvas. It gives families glanceable real-time intelligence: live solar energy flows, a spatial 2.5D architectural floorplan with occupancy tracking, a predictive pantry depletion radar, and a glass-box Time Machine that previews future home states before they happen."*

---

### [1:15 - 1:40] Autonomous Subscription Audit & Recovering $803.76/yr
- **Visual**: Switch to the **Operations Cockpit** view.
  - Click quick-prompt chip: *"💰 Save me $800 on renewals"*.
  - Show the live **Multi-Tool DAG visualizer** expanding:
    - `[1] memory_query`
    - `[2] inbox_scan`
    - `[3] commerce_scan_deals`
    - `[4] actions_propose` (×3, one per savings card)
  - Alexa speaks response via TTS: *"I audited 5 active household subscriptions. StreamBox 4K has been dormant for 68 days..."*
  - Automatically navigates to the **Approval Tray**. Three rich proposal cards appear:
    - *Cancel StreamBox 4K* (+$239.88/yr)
    - *Downgrade Metro Fitness* (+$360.00/yr)
    - *Cancel Cloud Gaming* (+$203.88/yr)
  - Point out that **NOTHING** has been charged or cancelled yet. Click **"✓ Approve Action"** on StreamBox. The card updates to **"Approved"** with an instant cryptographic audit hash!
- **Narrator**:
  > *"Watch our autonomous DAG decompose our request. It audits 5 household subscriptions and detects StreamBox 4K has had zero playback in 68 days. Instead of silently acting, it stages 3 verifiable action cards in our Glass-Box Approval Tray with exact before-and-after diffs. One tap approves it."*

---

### [1:40 - 2:05] AWS Strands Multi-Agent Supervisor & 15% Subscribe & Save
- **Visual**:
  - Click prompt chip: *"🛒 Restock Coffee & Milk"*.
  - Terminal/Log shows **AWS Strands Agents SDK** routing to `ReplenishmentDepletionAgent`:
    - Linear consumption velocity analysis (`days_until_empty <= 3`).
    - Automated Subscribe & Save 15% bulk discount calculation ($4.03 discount applied).
    - Prime Delivery scheduled: *Tomorrow by 8 AM - 11 AM*.
  - A rich **Amazon Subscribe & Save Cart Card** renders with interactive item controls.
  - Show the live **Amazon Prime Transit Tracker** showing delivery van approaching (2 stops away).
- **Narrator**:
  > *"Under the hood, Amazon's AWS Strands Agents SDK coordinates specialized sub-agents. Our Replenishment Agent evaluates pantry depletion velocity, applies a 15% Subscribe & Save bulk discount, and schedules guaranteed Prime delivery slots—staging a 1-tap cart approval."*

---

### [2:05 - 2:25] Persona Safety Matrix: Child Guardrails & Family Arbiter
- **Visual**:
  - In the header, change the Persona selector from **Alex (Adult / Owner)** to **Leo (Child / Age 9)**.
  - The UI updates with a playful avatar and blue badge: *"Child Persona Active"*.
  - Attempt to approve an Amazon order or unlock the front door.
  - A modal / warning toast immediately fires:
    - *"🛡️ Child Safety Policy: Persona 'Leo' is restricted to safe ambient comfort actions. Ask an adult to authorize financial or physical security changes."*
  - Switch back to Alex. Trigger a climate dispute: Alex wants 68°F during a peak $0.48/kWh tariff window.
  - The **Arbiter Negotiator Agent** computes a Pareto-optimal compromise (71°F with fan) and shifts high-draw laundry off-peak.
- **Narrator**:
  > *"Safety is context-aware. When our 9-year-old son Leo interacts with Alexa, the Sentinel Persona Matrix automatically blocks financial purchases and lock commands. Meanwhile, our Arbiter Negotiator uses game theory to resolve climate disputes fairly while shifting energy loads off peak tariffs."*

---

### [2:25 - 2:45] Open Source Adapter, SHA-256 Ledger & Conclusion
- **Visual**:
  - Show the standalone `open-source-contribution/mcp-strands-adapter` folder:
    - Display `pyproject.toml`, Apache 2.0 license, and dynamic JSON schema reflection tests.
  - Open **Settings** on the UI and click **"Verify now"** next to Ledger.
    - Status reads: *"Chain intact · N sealed events"* (SHA-256 Merkle chain verified live).
  - Display the GitHub repo URL and invite links on screen.
- **Narrator**:
  > *"To give back to the Amazon developer community, we published **`mcp-strands-adapter`**—an open-source library bridging AWS Strands Agents SDK to FastMCP 2025-11-25. Every decision is cryptographically anchored in an immutable SHA-256 ledger.*  
  > *Hearth Universal delivers transparent, verifiable, and safe ambient intelligence to Alexa+. Clone the repo and run it today. Thank you!"*
