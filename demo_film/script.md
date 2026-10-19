# HEARTH — The Film (as shot)
### Alexa+ Hackathon submission · live-navigated product demo · 1920×1080 @ 30 fps · **2:58** (178.2 s)

**Logline.** A small servant for the whole household. It finds the money, food and energy a
family leaks, stages exactly what to do about it — writes the tool when nobody coded it,
proves every step — and never acts without you.

**What is real on screen.**
- A real server (`mcp-server/server.py`), a real Chrome, the shipped app surfaces (`/`, `/echo`, `/web2/`).
- The money question is answered live by **Google Gemini 3.8 Flash** (`gemini-3.8-flash`); the answer
  card shows the brain chip *“Gemini · gemini-3.8-flash”* on camera.
- The forge scene mints a new tool **live**: catalog goes 54 → 55 while the camera watches, and the
  new ability is invoked for real (`applied_hour: 16`, `savings_usd: 0.7`).
- Nothing is composited; the UI in frame is the UI that ships.

**Narrative arc:** leak → conversation → cockpit → the line it never crosses → the story behind
every action → insight → **THE FORGE** → proof → close.

**Voice.** Calm documentary narrator (edge-tts `en-US-AndrewMultilingualNeural`, rate −4%).
Music: an original synthesized room-tone bed, mixed at 0.55, `loudnorm I=-16:TP=-1.5:LRA=11`.
No third-party audio, no Amazon/Alexa marks.

---

## s01 — Cold open · Landing · 16.70 s
**VO.** “Every home runs on guesswork. Forgotten subscriptions. Energy burned at the wrong hour.
Money that quietly leaks away. Hearth is not an agent. It's a small servant for your household —
and it never acts without asking.”

| t | Beat |
|---|---|
| 0.0 | `/` fades in on the hero: **Tell Alexa, “Save me $800.”** |
| ~2.7 | Glide to the stats band — `$803.76 · 15% · 96% · $0.18 · 0` |
| ~5.2–7.4 | The leak: “Every household leaks — quietly” (subscriptions · the 9 p.m. pantry panic · oversold trust) |
| ~9.9 | What it does: “One small servant for the whole household” + the conversation strip |
| ~12.7 | The promises: “No commands to memorize” + “It asks before it acts” cards |
| 15.0 | Settle low, hold the line — fade to black (0.7 s). |

## s02 — “Save me $800.” · Echo surface · 24.28 s
**VO.** “Just talk to it. Save me eight hundred dollars. Hearth understands the whole home —
energy, pantry, comfort, and every subscription that quietly renews. The answer comes back inline,
full screen, structured with live data, and voice only. One question. Four ways to see it.”

| t | Beat |
|---|---|
| 1.9 | Cursor eases to the composer, clicks in. |
| 2.7 | Types `Save me $800.` (voice says it with him). |
| ~5.8 | Sends. The question stages; the live brain thinks on camera. |
| ~11 | **The answer lands**: count-up to **$803.76** — “$803.76/yr in projected savings has been
identified across your subscriptions.” Three proposals staged (StreamBox 4K, Ultra Cloud Gaming,
Metro Fitness), receipts rail at $810.54, trust strip ***Gemini · gemini-3.8-flash*** / Checked for
safety / receipt issued when it happens. |
| ~13 | Opens **Display & AI**; tours the four modes — **Full screen → Structured → Voice only →
Inline** — brain row reads *Google Gemini*. |
| ~21 | Closes the sheet; the answer + pending Approve/Decline stay on screen. |

## s03 — The cockpit · 17.75 s
**VO.** “Behind the conversation sits a cockpit for the household. What is happening. What it costs.
What Hearth recommends next. Scenarios you can rehearse before your home ever feels them.
Your home, rendered as a system, not a list of gadgets.”

| t | Beat |
|---|---|
| 3.0–7.4 | Hover the three live tiles — weather/energy, **locked** state, load |
| 9.2 | Scroll to the intent feed: what the house noticed, what it staged |
| 12.8 | Park on the **rehearsal scenarios** — spike at 4 p.m., coffee down to two pods, motion at night |
| 14.4 | Ride back up to the top tiles. |

## s04 — The line Hearth never crosses · Approvals · 18.60 s
**VO.** “Here is the line Hearth never crosses. It proposes. It never executes. Every action waits
for you: what will happen, what it saves, why it matters. Approve once — and Hearth carries it out.
Trust is built in the pauses.”

| t | Beat |
|---|---|
| 3.4 | Open **Approvals**: three staged intents with exact savings ($239.88 · $203.88 · $360.00). |
| 5.8–8.6 | Glide down the first card: what will happen, what it saves, why it matters. |
| 11.0 | **Approve** the downgrade — one tap; the card resolves in place. |
| 14.0 | The counter (`#apprCount`) ticks down; the pause is the point. |

## s05 — Every action leaves a story · Activity · 18.80 s
**VO.** “Every action leaves a story. The timeline names every actor — acoustic doctor, family
mediator, forensic investigator — and exactly what each one did. Every entry carries its reasoning.
No black boxes. No silent decisions.”

| t | Beat |
|---|---|
| 3.4 | Open **Activity** — the actor-stamped timeline. |
| 5.6 | Expand the newest event: it opens with *why*, not just what. |
| 8.2–13.0 | Scroll the evidence; hover the next event. |

## s06 — Insight, not noise · Insights · 15.25 s
**VO.** “Insights turn a month of noise into a signal. Money recovered. What's actually in your
pantry. How sunlight and load shift through the day. Even a digital twin that rehearses tomorrow
before your home lives it.”

| t | Beat |
|---|---|
| 2.9 | Open **Insights**. |
| 4.8–9.9 | Wheel-scroll: money recovered → pantry reality → sunlight/load curve. |
| 11 | The **causal twin** box slides into centre — tomorrow, rehearsed tonight. |

## s07 — THE FORGE · 31.59 s — the moment
**VO.** “And when Hearth meets a need nobody coded — a new rate plan, a rule that only your
household has — it doesn't wait for an update. It writes the tool itself. Watch. Intent understood.
Schema compiled. A safety gate. Source verified. Sandboxed. Smoke tested. Then mounted, live — as
tool fifty five. Nothing was shipped. Nothing was hand coded. And every step is on the record.”

| t | Beat |
|---|---|
| 2.6 | Home tab → the **Teach Hearth a new habit** panel scrolls in. Rule on screen:
*“Pre-cool the living room to 70F before the 4pm peak tariff.”* |
| 11.9 | **Teach it.** The pipeline lights up: Understanding → Writing the plan → Checking safety
→ Double-checking → Trying it out. |
| 12.8–20 | Drift down the evidence: the synthesized skill `hearth_forge_precool_the_living_r_5adf51`,
safety **PASSED (Sentinel tier-2 + AST + smoke)**, dry run passed, source on the record. |
| 20.9 | **Try it right now** — the forged tool is invoked for real:
`{"status": "scheduled", "applied_hour": 16, "eco_mode": true, "savings_usd": 0.7}`. |
| 24.3 | The catalog pill: **55 abilities · 4 learned here** — 54 before the take, 55 after. |
| 27.0 | Settle on the audited trail; every step sealed. |

## s08 — Proof, not promises · Black-box forensics · 18.59 s
**VO.** “Trust isn't a promise. It's a proof. Reconstruct three A M: every sensor, every decision,
replayed and sealed into a hash-chained Merkle record. The intruder hypothesis? Disproven in
seconds, with evidence.”

| t | Beat |
|---|---|
| 3.2 | Insights → scroll to **Black Box forensics**. |
| 7.4 | **Reconstruct 3 AM** — the scan runs on camera. |
| ~9 | The dialog opens: *Intruder hypothesis — disproven*, 96% physical certainty, every evidence
line named, SHA-256 Merkle proof at the bottom. |
| 15–17.4 | Scroll the proof; hold. |

## s09 — Close · Endcard · 16.54 s
**VO.** “Hearth. Three hundred forty three tests. Fifty five tools — one of them forged, live, on
camera. A home that finally understands itself. And never acts without you. Not an agent. A servant.”

| t | Beat |
|---|---|
| 0.3 | `endcard.html` fades in: flame, **HEARTH**, *a small servant for the whole household*. |
| 4–6 | Stats settle: **362 tests passing · 55 tools live · 1 forged on camera · 100% actions audited**. |
| ~9 | *“Not an agent. A servant.”* — hold to the final fade. |

---

## Timing model (as shipped)
- Scene length = VO length + tail (1.5–4 s); VO starts at **+0.42 s** inside each scene.
- Per scene: trim to length, 30 fps, fade-in 0.35 s / fade-out 0.7 s; recorder keeps a ~3.2 s
  encoder cushion past the target so the tail is never clipped.
- Mix: VO + original synth bed (0.55) → `loudnorm I=-16:TP=-1.5:LRA=11` → AAC 192 k.
- Totals: **178.2 s** (limit 180) · H.264 CRF 18 · `demo_film/HEARTH_DEMO_FINAL.mp4`.

## Numbers on camera
| Number | Meaning |
|---|---|
| **$803.76/yr** | projected savings identified across subscriptions (goal: 800) |
| $239.88 · $360.00 · $203.88 | StreamBox 4K · Metro Fitness · Ultra Cloud Gaming |
| $1547.52/yr | total household subscription spend audited |
| **54 → 55** | tools before/after the live forge |
| `applied_hour: 16` · `savings_usd: 0.7` | real result of invoking the forged skill |
| 362 / 100% | tests passing · actions audited |
