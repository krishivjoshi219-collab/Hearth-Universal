# HEARTH — The Film
### Alexa+ Hackathon submission · cinematic demo · 1920×1080 · ~3:00

**Logline.** A household agent that runs a real home, tells you the truth about it, and when it meets a need nobody coded — it writes the tool itself, proves every step, and never acts without you.

**Narrative arc (trustworthy autonomy):** leak → conversation → cockpit → the line it never crosses → the story behind every action → insight → **THE FORGE** → proof → close.

**Voice.** Calm, warm, confident documentary narrator. Rate −4%. No hype, no exclamation. The product is the excitement.

**Direction principles.**
- Real product, real server, live actions. Nothing staged, nothing faked.
- The cursor is a character: deliberate moves, pauses that let numbers land.
- Every scene = one idea. Forge is the climax; everything before it earns the right to it.
- Fades between scenes; silence is allowed to breathe under the final line.

---

## Scene s01 — Cold open · Landing *(~13s)*
**VO:** "Every home runs on guesswork. Forgotten subscriptions. Energy burned at the wrong hour. Money that quietly leaks away. Hearth is one calm agent that stops the leak — and shows you how."

| t | Action |
|---|---|
| 0.0 | `/` loads. Fade in from black. |
| 0.8 | Slow gliding mouse move across hero headline. |
| D−6 | Wheel-scroll down ~2 viewports in 5 gentle steps, revealing the $800-leak section, the "What Hearth does" cards, the conversation strip. |
| D−1.5 | Settle. Hold on the "Stop paying for what you forgot." line. |

**On screen copy:** "Tell Alexa, …" / "The quiet $800 leak in every household" / "One calm agent for the whole household".

---

## Scene s02 — "Save me $800." · Echo surface *(~22s)*
**VO:** "Just talk to it. 'Save me eight hundred dollars.' Hearth understands the whole home — energy, pantry, water, comfort. Answer: inline, fullscreen, hydrated with live data, voice-only. One question. Four ways to see it. No apps to learn. No dashboards to decode."

| t | Action |
|---|---|
| 0.0 | `/echo` loads (landing-styled surface). |
| 1.2 | Click `#askText`; type `Save me $800.` at ~60ms/char (human cadence, includes the period). |
| 4.0 | Click `#askSend`. Hearth "thinks" (ring/typing). |
| 6.5 | Answer card appears → pause 1.5s to read. |
| 9.0 | Click mode chip `[data-mode="fullscreen"]` → fullscreen answer. Hold 2s. |
| 12.0 | Click `[data-mode="hydrated"]` → live data woven in. Hold 2s. |
| 15.0 | Click `[data-mode="voice-only"]` → answer speaks. Hold. |
| 18.5 | Return to `[data-mode="inline"]`. |

*Backup if a chip fails: proceed — never retry on camera.*

---

## Scene s03 — The cockpit *(~16s)*
**VO:** "Behind the conversation sits a cockpit for the household. What is happening. What it costs. What Hearth recommends next. Scenarios you can rehearse before your home ever feels them. Your home, rendered as a system — not a list of gadgets."

| t | Action |
|---|---|
| 0.0 | `/` loads. Auto-staging ribbon plays (~2s). |
| 2.5 | Mouse glides across the stat tiles: **tools live**, **intents staged**, **ledger state**. Small hover pauses. |
| 7.0 | Slow scroll to the simulator section; park the cursor on the scenario controls. |
| 12.0 | Scroll back up to the top tiles. |

---

## Scene s04 — The line Hearth never crosses · Approvals *(~21s)*
**VO:** "Here is the line Hearth never crosses. It proposes. It never executes. Every action waits for you — what will happen, what it saves, why it matters. Approve once, and Hearth carries it out. Then it records exactly what it did. Trust is built in the pauses."

| t | Action |
|---|---|
| 0.0 | Cockpit → click tab `[data-view="approvals"]` (`.tab`). |
| 1.2 | Hover the first intent card (`.intent`); hold so projected savings are readable. |
| 4.0 | Small scroll within list to show a second proposal. |
| 8.5 | Click **Proceed** (`.intent .btn-primary`). |
| 9.5 | Card resolves (executes) — hold. Small settle mouse move. |
| D−3 | Park cursor mid-list; hold the moment. |

**On camera numbers:** projected savings visible; count in `#apprCount` ticks down after approval.

---

## Scene s05 — "Why this happened" · Activity *(~14s)*
**VO:** "Every action leaves a story. Tap any event, and ask the only question that matters — why this happened. Evidence, reasoning, outcome, in plain language. No black boxes. No 'the algorithm decided.'"

| t | Action |
|---|---|
| 0.0 | Click tab `[data-view="activity"]`. |
| 1.0 | Click the first `#timeline .event summary` → expands "Why this happened" with causal chain. |
| 4.0 | Hover successive evidence lines slowly. Hold. |
| D−2 | Second event summary hover (do not open). |

---

## Scene s06 — Insight, not noise · Insights *(~16s)*
**VO:** "Insights turn a month of noise into a signal. Money recovered. What is actually in your pantry. How sunlight and load shift through the day. Even a digital twin that rehearses tomorrow before your home lives it."

| t | Action |
|---|---|
| 0.0 | Click tab `[data-view="insights"]`. |
| 1.2 | Wheel-scroll slowly (~900px over 8s): **money recovered** → **pantry** → **sunlight/load** → **causal twin**. Park 1.2s on each. |
| D−2 | Stop on the causal-twin visualization; small settle. |

---

## Scene s07 — THE FORGE *(~33s)* — the moment
**VO:** "And when Hearth meets a need nobody coded — a new rate plan, an EV tariff, a rule that only your household has — it doesn't wait for an update. It writes the tool itself. Watch. Intent understood. Schema compiled. A safety gate. Source verified. Sandboxed. Smoke-tested. Then mounted — live — as tool fifty five. Nothing was shipped. Nothing was hand-coded. And every step is on the record."

| t | Action |
|---|---|
| 0.0 | Home tab → `scrollIntoView` `#forgePanel` (smooth). |
| 1.5 | Pause: the panel is already showing the EV rule intent. Hover the input so its text reads on camera. |
| 4.0 | Click `#forgeGo`. **The Forge sequence animates** (`#forgeSteps`, `#forgeCode`, `#forgeSafety`, `#forgeSmoke`). |
| — | Wait for `#forgeOut` to become visible (≤60s). As each step lights up, glide the cursor down the checklist — do not rush. |
| +1.5 | When result shows → hold 2s (tool name + summary). |
| +4.5 | Click `#forgeCall` → live MCP `call_tool` on the forged tool. |
| +7.5 | `#forgeResult` shows execution output (`applied_hour: 22`, `savings_usd: 3.2`) → hold 2.5s. Cursor rests on the number. |
| +11 | Small scroll to `#forgeCatalog` — the new tool listed among live tools (`#forgeCount`: 55 / 25 cap). |

*Pre-shoot: forge catalog starts 0 (pristine 51 tools). If `#forgeGo` errors — stop-take, clean `state/synthesized_skills/*.json`, restart, re-warm.*

---

## Scene s08 — Proof, not promises · Black box forensics *(~15s)*
**VO:** "Trust isn't a promise. It's a proof. Reconstruct three A M — every sensor, every decision, every deduction, replayed and sealed in a hash-chained Merkle proof. The intruder hypothesis? Disproven in seconds — with evidence."

| t | Action |
|---|---|
| 0.0 | Insights view → scroll to `#forensicsBox` (Black Box). |
| 1.5 | Click `#forensicsScanBtn` ("Reconstruct 3 AM") → button switches to "Reconstructing…". |
| — | Wait for `#dialog` to open (`.open` class / visible). |
| +2 | `#dlgBody` visible: "✓ Intruder Hypothesis Disproven — 96% physical certainty", SHA-256 Merkle proof. |
| +6 | Slow scroll inside the dialog timeline. Hold on the proof line. |
| D−2 | Hold. Do not close (next scene fades). |

---

## Scene s09 — Close · Endcard *(~15s)*
**VO:** "Hearth. Three hundred forty three tests. Fifty four live tools — and the power to forge the next one. A home that finally understands itself, and never acts without you. Alexa plus: one calm agent, for your whole household."

| t | Action |
|---|---|
| 0.0 | `demo_film/endcard.html` loads (file://). |
| 1.0 | Logo flame ignites (CSS animation), headline fades up. |
| 4.0 | Stat row counts up: **314 tests · 51 tools + 1 forged · 0 unverified actions**. |
| 9.0 | Tagline fades: "Proposes. Never executes." |
| D−2 | Slow fade to black (built into the endcard CSS). |

**Endcard copy:**
- HEARTH — *one calm agent for the whole household*
- 343 tests passing · 55 tools live (54 + 1 forged on camera) · hash-chained audit
- "Proposes. Never executes."
- Built for the Alexa+ Hackathon · Oct 2026

---

## Timing model
- Every scene: `duration = VO_duration + tail` (tail 2.2s; s07 tail 3.5s).
- Video: 30 fps, 1920×1080. Per-scene fade-in 0.35s / fade-out 0.5s.
- Audio: VO +0.35s offset, soft pink-noise room tone at −42 dB, music bed optional (credits permitting).
- Final: `HEARTH_DEMO_FINAL.mp4` — H.264 high profile + AAC 192k.

## Shoot checklist
1. Server warm (startup 15–40s; verify `curl /api/forge/tools` → `tools_count: 54`).
2. Forge catalog empty: `rm -f state/synthesized_skills/*.json` + restart + warm.
3. Hard-refresh surfaces once (`no-cache` + ETag already shipped).
4. Record 9 scenes → `demo_film/raw/s01…s09/*.webm`.
5. Mux + concat + mix → final. Extract contact sheet + key frames.
6. Reviewers: Gemini (agy CLI) + Muse Spark (opencode subagent) over script + frames.
