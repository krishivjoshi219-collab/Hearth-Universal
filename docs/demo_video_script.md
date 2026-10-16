# Demo Video — THE 10/10 CUT (2:30, hard-stop 3:00)

**Project:** Hearth Universal — Tell Alexa "Save Me $800." She Proposes. You Tap Once.
**Track:** Alexa+ ($25k) · **Minis:** AWS Builder, Open Source
**Film mode:** `http://<host>:8787/echo?tour=1` — autopilot captions drive the hero flow. You only film.
**Rules (from Devpost + AWS winners research):** human pain in first 10s · product functioning on screen by 0:15 · screencast-with-narration, not marketing · one workflow, one proof, one URL · <3 min or judges stop watching · Public + "Not for Kids".

---

## VO SCRIPT — read exactly this (271 words ≈ 2:10 at 130 wpm, leaves 20s for Alexa TTS + taps)

### [0:00–0:12] HOOK — the bill + the kid (Impact + Idea)
> "Every family pays for subscriptions nobody uses. And every parent fears an AI that orders — or unlocks — without asking. Hearth is the Alexa+ agent that found eight hundred dollars of waste in our home — and cannot spend one dollar until you tap once."
**On screen:** phone-bill close-up (StreamBox $239.88/yr, 0 plays in 68 days) → kid voice "Alexa, buy 5,000 Robux!" → title card: *"What if Alexa could save you $800 — but never spend $1 without you?"*

### [0:12–1:05] DEMO 1 — "Save me $800" → Stage → Approve → Undo (Tech + Design)
**On screen:** `/echo?tour=1` fullscreen, sound on. Tour captions do the narrating — you stay silent and let Alexa speak.
> "Watch. Alexa, ask Hearth to save me $800. She audits five subscriptions live — StreamBox dormant sixty-eight days, Metro Fitness one visit in forty-five, Cloud Gaming untouched. Three cards: eight hundred three dollars and seventy-six cents a year. I stage one — nothing is cancelled. I tap Approve — sealed receipt. I tap Undo — money back. Nothing moved until I tapped. Everything undoes. Fifty-one MCP tools behind three cards."
**Must-show:** finger/cursor tap on Stage → toast → tray → Approve → SHA-256 receipt → Undo. B-roll 3s (corner, muted): `curl initialize → protocolVersion 2025-11-25` + rubric 100/100.

### [1:05–1:35] DEMO 2 — "Fix groceries" (Impact — the commercial sentence)
> "Same contract for groceries. We're out of everything — fix groceries. Coffee empties in two days. Five items, fifteen percent Subscribe and Save, Prime slot tomorrow eight to eleven. Still nothing ordered. One tap approves. One tap undoes. This maps straight onto Alexa+ checkout and Subscribe and Save — that's who pays beyond the hackathon."
**On screen:** cart card → tray Approve → Undo.

### [1:35–2:05] SAFETY — Leo blocked + 3am intruder disproved (Idea — the moat)
**On screen:** ops cockpit `/web2`, Persona Alex → **Leo (9)**. Type "buy Robux" → denial card. Type "unlock front door" → denial, lock stays. Back to Alex. Night-mode CSI card: wind 24mph + pressure drop + zero thermal signatures.
> "Leo can't spend or unlock — by design, not by prompt. And at 3am Hearth doesn't scream 'sensor open' — it proves why. Wind, pressure drop, zero thermal signatures. Intruder disproved, proof sealed. That's the glass-box difference."

### [2:05–2:30] PROOF + CLOSE (Tech — credentials in 15s, then one URL)
**On screen:** 5 flashcards, 3s each: Strands supervisor → Bedrock memory → MCP Apps card → ledger Verify → open-source adapter + Apache-2.0. End card holds 5s: GitHub URL only.
> "Real Strands Agents SDK. Bedrock AgentCore memory. Fifty-one MCP tools over Streamable HTTP. Agent Skills. And our open-source Strands-to-MCP adapter. Clone, one script, no keys, no device. Hearth: Alexa that saves you eight hundred dollars — and never spends one without you. Thank you."

---

## Why this wins (evidence, not hope)
1. **Cold open on money + fear** — Devpost: elevator pitch in first seconds or judges drift. Every losing film opens on logo/architecture; every winner opens on human stakes.
2. **Functioning product by 0:15** — rules require footage of the Project functioning on its platform; judges score Tech on what they SEE run, not what you claim.
3. **One workflow, twice** (save → groceries) — AWS Bedrock guide: "a single feature that works cleanly beats two half-broken." Same muscle shown twice = design coherence.
4. **Tap + Undo = the memorable image** — judges watch dozens of films; the finger-tap on Approve and the reversal is the one frame they keep. No other entrant shows reversibility.
5. **Leo denial is the moat in 20s** — "Creative, not obvious" is the explicit Idea criterion; obvious = single-turn Q&A bot. A 9-year-old blocked live is un-fakeable differentiation.
6. **Credentials montage, 15s, no pytest fullscreen** — Tech Implementation needs Strands/Bedrock/MCP proof; a wall of terminal loses Design. Flashcards + unlisted backup link in README splits the audience correctly.
7. **One URL, 5s hold, spoken once** — films with three CTAs convert to zero. One repo URL.
8. **Friction logs = +10% bonus** — say "friction logs filed" on camera is optional; FILING them in Devpost is mandatory. They are scored in Stage 1 downselection.

## Shoot checklist (1 hour, solo, phone)
- [ ] `make clean && ./demo.sh` first — pristine tray (test proposals pollute `state/`, gitignored).
- [ ] Serve on laptop, open `/echo?tour=1` fullscreen (Chrome, clean profile, bookmarks hidden). Crop/hide the URL bar — never show `localhost`.
- [ ] Phone on tripod/stack of books, landscape 1080p, mic close to YOU for VO; Alexa TTS comes through laptop speakers at 60%.
- [ ] Record VO in closet/car with wired earbuds FIRST, then cut picture to VO. Never narrate over Alexa — duck or pause.
- [ ] Pre-record each Alexa turn twice; use the clean take. If Wi-Fi flakes, hotspot the laptop to the phone.
- [ ] Taps: slow cursor, 150% zoom on click targets, 4s dwell per UI state. No static screen >4s without motion.
- [ ] Music: one bed, YouTube Audio Library (attribution-free), at 15–20% under VO. Save license.
- [ ] Captions: correct the auto-SRT by hand ("Alexa" commands verbatim) + `[Alexa chime]` cues. Test muted — story must parse with sound off.
- [ ] Thumbnail: Echo screen mid-response + 3 words ("Never Spends Without You") + contrast arrow on the Approve button. 1280×720.
- [ ] Upload 3h early: YouTube Public (never Private) + "Not for Kids" + paste link into Devpost + `docs/devpost_submission.md:25`. Uploads can take hours.
- [ ] Raw 3-min terminal proof (`pytest` 288 + rubric 100/100) as UNLISTED backup link in README — not in the main film.
