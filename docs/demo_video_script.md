# Demo Video Storyboard & Script (<3:00)

**Project:** Hearth Universal  
**Track:** Alexa+ (Primary) | **Mini-Challenges:** AWS Builder, Open Source  
**Target Video Duration:** 2 minutes 45 seconds  
**Platforms to Display:** Terminal (FastMCP Streamable HTTP Handshake) + Web Browser (Echo Show 15/21 Ambient Smart Canvas & Glass-Box Ops Cockpit on `localhost:8787`).

---

### [0:00 - 0:25] The Problem & The Core Innovation
- **Visual**: Camera starts on title screen: *"Hearth Universal — The Open Glass-Box Agent for Alexa+"*. Transition to split screen showing modern home chaos: forgotten subscriptions, depleting pantry items, and "black box" AI assistants that either do nothing or risk unintended actions.
- **Narrator (Voiceover)**:
  > *"Voice assistants used to just answer trivia or set timers. With Alexa+, we can build proactive agentic workflows that solve complex household problems. But households don't want black-box agents that silently spend money, order unwanted items, or unlock doors without permission.*  
  > *Meet **Hearth Universal**: an open-source, glass-box operations agent for Alexa+ built on the new **MCP 2025-11-25 Streamable HTTP specification**. It operates under an uncompromising principle: **Propose-Never-Execute**."*

---

### [0:25 - 0:45] 60-Second Setup & MCP Spec Verification
- **Visual**: Screen capture of terminal.
  - Run: `python mcp-server/server.py` (shows FastMCP starting on port `8787`).
  - Run: `curl POST /mcp` initialize request. Output displays `"protocolVersion": "2025-11-25"`.
  - Run: `pytest -v` (49 passing tests in ~19s).
- **Narrator**:
  > *"Hearth is completely zero-friction and zero-build. It requires no closed API keys, Node.js, or physical devices to evaluate. Our server exposes a fully compliant MCP 2025-11-25 Streamable HTTP endpoint. As you can see with this curl handshake, it validates immediately against the latest specification."*

---

### [0:45 - 1:15] Echo Show 15/21 Ambient Smart Canvas & Ring Camera
- **Visual**: Browser opens to `http://localhost:8787` on the **Ambient Smart Canvas** view.
  - Highlight the sleek Apple Intelligence & Echo Show 15/21 layout.
  - Show the live **Solar / Grid / Battery Energy Flow** vector diagram animating power distribution.
  - Show the **Pantry Depletion Radar**: Organic Milk (Critical - 1 day), Fair-Trade Coffee (Urgent - 2 days).
  - Click **"🔔 Ring Doorbell"** button on the Front Porch Camera.
    - Web Audio plays authentic dual-tone acoustic chime.
    - Simulated 1080p canvas displays visitor motion bounding box and pops the visitor alert card.
    - Alexa speaks: *"Visitor detected at front porch camera."*
- **Narrator**:
  > *"This is the Echo Show Ambient Smart Canvas. It gives families glanceable real-time intelligence: live solar energy flows, a predictive pantry depletion radar, and our native Alexa Smart Home v3 camera stream. When a visitor approaches, our Ring camera directive triggers an acoustic chime and live video feed."*

---

### [1:15 - 1:45] Autonomous Subscription Audit & Recovering $803.76/yr
- **Visual**: Switch to the **Operations Cockpit** view.
  - Click quick-prompt chip: *"💰 Save me $800 on renewals"*.
  - Show the live **Multi-Tool DAG visualizer** expanding:
    - `[1] memory_query`
    - `[2] inbox_scan`
    - `[3] commerce_scan_deals`
    - `[4] sentinel_judge`
    - `[5] actions_propose`
  - Alexa speaks response via TTS: *"I audited 5 active household subscriptions. StreamBox 4K has been dormant for 68 days..."*
  - Automatically navigates to the **Approval Tray**. Three rich proposal cards appear:
    - *Cancel StreamBox 4K* (+$239.88/yr)
    - *Downgrade Metro Fitness* (+$360.00/yr)
    - *Cancel Cloud Gaming* (+$203.88/yr)
  - Point out that **NOTHING** has been charged or cancelled yet. Click **"✓ Approve Action"** on StreamBox. The card updates to **"Approved"** with an instant cryptographic audit hash!
- **Narrator**:
  > *"Watch the autonomous DAG decompose our request. It reads memory, audits 5 subscriptions, and detects that StreamBox 4K has had zero playback in 68 days. Instead of silently acting, it stages 3 verifiable action cards in our Glass-Box Approval Tray with exact before-and-after diffs. One tap approves it."*

---

### [1:45 - 2:10] Interactive MCP Apps: Lighting Designer & Amazon Restock
- **Visual**: 
  - Click prompt chip: *"🎨 Launch Lighting Designer"*.
  - An interactive **Lighting Designer MCP App** mounts in chat: show the HTML5 color wheel canvas. Drag the pointer to Amber 2700K; the Living Room lights react instantly.
  - Click prompt chip: *"🛒 Restock Coffee & Milk"*.
  - A rich **Amazon Subscribe & Save Cart Card** renders:
    - Fair-Trade Coffee Beans: $22.87 ($26.90 with 15% discount applied).
    - Prime Delivery Slot: *Tomorrow, 8 AM - 11 AM*.
    - One-tap "Approve Amazon Order" stages into the Approval Tray.
- **Narrator**:
  > *"Hearth Universal pioneers interactive MCP Apps. Tools don't just return plain text—they render micro-UIs directly in the interface. Here, our Lighting Designer lets users visually fine-tune color temperatures, while our Amazon Subscribe & Save card automatically calculates 15% bulk discounts and secures Prime delivery windows."*

---

### [2:10 - 2:30] Persona Safety Matrix: Child Guardrails
- **Visual**:
  - In the header, change the Persona selector from **Alex (Adult / Owner)** to **Leo (Child / Age 9)**.
  - The UI updates with a playful avatar and blue badge: *"Child Persona Active"*.
  - Attempt to approve an Amazon order or unlock the front door.
  - A modal / warning toast immediately fires:
    - *"🛡️ Child Safety Policy: Persona 'Leo' is not authorized to execute financial orders or perimeter door unlocks."*
- **Narrator**:
  > *"Safety is context-aware. When our 9-year-old son Leo interacts with Alexa, the Sentinel Persona Matrix automatically restricts financial orders and perimeter unlocks, while still allowing safe bedtime comfort controls."*

---

### [2:30 - 2:45] Cryptographic Audit Ledger & Conclusion
- **Visual**: Click the **"🛡️ Audit Chain"** button in the header.
  - The SHA-256 Merkle Ledger dialog opens.
  - Show the table of events with timestamps, actors (`agent`, `human`, `sentinel`), and verifiable SHA-256 hashes.
  - Point to the badge: *"Integrity: 100% VALID"*.
  - Display the GitHub repo URL and MIT license on screen.
- **Narrator**:
  > *"Every proposal, approval, and Sentinel decision is cryptographically hash-chained in an immutable SHA-256 ledger. Hearth Universal brings transparent, verifiable, and safe agency to Amazon Alexa+.*  
  > *Clone the MIT repo today and run it in 60 seconds. Thank you!"*
