# Critic Brief — HEARTH demo film

You are reviewing a **hackathon demo film** for the **Alexa+ track** (Amazon hackathon, 60k+ participants).

## The product (all real, running live in the film)
Hearth is a household agent that:
- Audits subscriptions and finds household money leaks (real numeric engine: "Save me $800" → $803.76/yr found, itemized).
- Proposes but **never executes** — every action waits in an Approval Tray ("propose-never-execute" is the core trust promise).
- Shows an agent timeline (actor → action → reasoning) for every event.
- Insights: money recovered, pantry depletion, Household Parliament (game-theoretic), Causal Digital Twin (Monte Carlo 7-day forecast).
- **Hearth Forge (the wedge)**: when it meets a rule nobody coded (e.g. "Charge the EV with at least 8 kWh after 10pm, never pay above $0.28/kWh"), it writes a **real MCP tool at runtime**: intent → schema → Sentinel safety gate → AST check → sandboxed smoke test → live MCP mount (51 → 52 tools, verified). Forged tool is executed live via `call_tool` (applied_hour 22, savings_usd 3.2).
- Black Box forensics: "Reconstruct 3 AM" → Bayesian incident reconstruction "Intruder hypothesis disproven" sealed with a SHA-256 Merkle proof.
- 314 automated tests; hash-chained audit ledger; ARIA-clean UI.

## The film
- File: `HEARTH_DEMO_FINAL.mp4` (3:06, 1920×1080, narrated with an AI voiceover).
- Structure: landing → echo (4 display modes) → cockpit → approvals → activity timeline → insights → **Forge climax** → forensics proof → endcard.
- Everything on screen was recorded live from the running product (no mockups, no fake data).
- Script/direction: `script.md`. Contact sheet: `contact.png`. Key frames: `s01_landing.png`, `s02_answer.png`, `s04_approvals.png`, `s07_forge.png`, `s08_dialog.png`, `s09_endcard.png`.

## Your task
Watch/read carefully, then deliver a sharp, honest critique:
1. **Top 3 strengths** (what would score points with judges).
2. **Top 3 weaknesses** (what loses points; be specific about moments in the film).
3. **3 concrete improvements** (feasible edits, not rewrites).
4. **Scores /10**: (a) demo-film craft, (b) innovation credibility, (c) would this plausibly win the Alexa+ track? One paragraph justifying.
Be a tough critic; vague praise is useless. If you can read the mp4, watch it; otherwise judge from the contact sheet + key frames + script.
