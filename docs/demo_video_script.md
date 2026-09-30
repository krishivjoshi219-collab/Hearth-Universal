# Demo Video Storyboard & Script (<3:00)

**Project:** Hearth Universal  
**Track:** Alexa+ (Primary) | **Mini-Challenges:** AWS Builder, Open Source  
**Target Video Duration:** 2 minutes 45 seconds  
**Platforms to Display:** Terminal (FastMCP Streamable HTTP Handshake) + Web Browser (Alexa+ Multi-Modal Echo Show Simulator on `localhost:8787`).

---

### [0:00 - 0:25] The Problem & The Core Innovation
- **Visual**: Camera starts on title screen: *"Hearth Universal — The Open Glass-Box Agent for Alexa+"*. Transition to split screen showing modern home chaos: forgotten subscriptions, high utility bills, and "black box" AI assistants that either do nothing or risk unintended actions.
- **Narrator (Voiceover)**:
  > *"Voice assistants used to just answer trivia or set timers. With Alexa+, we can build real agentic workflows that solve complex household problems. But households don't want black-box agents that silently spend money or change door locks without permission.*  
  > *Meet **Hearth Universal**: an open-source, glass-box operations agent for Alexa+ built on the new **MCP 2025-11-25 Streamable HTTP specification**. It operates under an uncompromising principle: **Propose-Never-Execute**."*

---

### [0:25 - 0:50] 60-Second Setup & MCP Spec Verification
- **Visual**: Screen capture of terminal.
  - Run: `python mcp-server/server.py` (shows FastMCP starting on port `8787`).
  - Run: `curl POST /mcp` initialize request. Output displays `"protocolVersion": "2025-11-25"`.
  - Run: `pytest -v` (14 passing tests in 0.8s).
- **Narrator**:
  > *"Hearth is completely zero-friction. It requires no closed API keys or hardware to evaluate. Our server exposes a fully compliant MCP 2025-11-25 Streamable HTTP endpoint. As you can see with this curl handshake, it validates immediately against the latest specification."*

---

### [0:50 - 1:30] Live Demo: Subscription Audit & Recovering $437/yr
- **Visual**: Browser opens to `http://localhost:8787`. Point out the glowing Alexa+ acoustic orb, protocol status, and clean Echo Show glassmorphism interface.
  - Click the quick-prompt chip: *"💰 Save me $437 on renewals"*.
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
  - Point out that **NOTHING** has been modified yet. Click **"✓ Approve Action"** on StreamBox. The status turns green to **"Approved"** with an instant audit hash!
- **Narrator**:
  > *"Watch the autonomous DAG decompose the goal. It reads our memory, audits 5 subscriptions, and detects that StreamBox 4K has had zero playback in 68 days. Instead of silently cancelling, it stages 3 verifiable action cards in our Glass-Box Approval Tray with exact before-and-after diffs. One tap approves it."*

---

### [1:30 - 2:00] Smart Home Digital Twin & Ambient Actuation
- **Visual**: Click prompt chip: *"🏡 I'm home early, start evening mode"*.
  - Voice response plays. Switch to the **Smart Home Twin tab**.
  - Show interactive controls:
    - Living Room lighting dims to 55% warm amber (#ff9e42).
    - Thermostat setpoint smoothly adjusts to 21.0°C Eco mode.
    - Show the Front Door Smart Lock: status badge confirms **LOCKED** (Sentinel auto-locks perimeter).
    - Show the real-time energy telemetry: Solar output 0.85 kW, Eco score 94/100.
- **Narrator**:
  > *"Next, we tell Alexa+ we're home early. The agent coordinates our smart home digital twin: dimming lights to warm amber, shifting HVAC into eco comfort, and verifying our entryway lock remains securely engaged."*

---

### [2:00 - 2:25] Sentinel Guardrails & Multi-Brain Egress
- **Visual**: Click prompt chip: *"🚨 Test Sentinel: rm -rf / & wire $500"*.
  - The Sentinel Guard fires instantly. Red alert card appears:
    - *"⛔ Command Blocked by Sentinel Security Engine: Destructive filesystem deletion (rm -rf)"*.
  - Switch the Brain Provider dropdown from *Local Intelligent Engine* to *AWS Bedrock (Claude 3.5 Sonnet / Amazon Nova)*.
  - Show that secret tokens are redacted to `•••` in the Vault.
- **Narrator**:
  > *"Security is built into the core. If an adversarial prompt or untrusted tool tries to run 'rm -rf /' or exfiltrate credentials, Sentinel blocks it immediately. Furthermore, Hearth Universal is multi-brain: swap between our zero-config local engine, Amazon Bedrock, or OpenAI without changing your home setup."*

---

### [2:25 - 2:45] Cryptographic Audit Ledger & Conclusion
- **Visual**: Click the **"🛡️ Audit Chain"** button in the header.
  - The SHA-256 Merkle Ledger dialog opens.
  - Show the table of events with timestamps, actors (`agent`, `human`, `sentinel`), and real SHA-256 hashes.
  - Point to the badge: *"Integrity: 100% VALID"*.
  - Display the GitHub repo URL and MIT license on screen.
- **Narrator**:
  > *"Every proposal, approval, and Sentinel decision is cryptographically hash-chained in an immutable SHA-256 ledger. Hearth Universal brings transparent, verifiable, and safe agency to Amazon Alexa+.*  
  > *Clone the MIT repo today and run it in 60 seconds. Thank you!"*
