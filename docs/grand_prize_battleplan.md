# 🏆 Grand Prize Battleplan — Alexa+ $25k vs 54,999

**Deadline: Oct 23 12pm PT (Oct 24 00:30 IST). Judging Nov 9-20. Winners ~Dec 3.**
**Status Oct 14 2:40pm IST:** engineering 100/100, storytelling was losing. Fixed hook + video script today. 9 days left to ship win.

## Why you were losing (brutal)

1. **Hook was jargon.** "Glass-Box Household Operations Agent + game-theoretic" = judge skip. Winners say "$803 saved, never spends $1 without you" in 10s.
2. **No video = auto-loss.** Devpost placeholder + plan to film terminal pytest for 25s. Judges stop at 3:00, decide in 15s. Terminal kills.
3. **localhost = skip.** 80% of judges never clone among 55k. No live URL, no phone-loadable Echo demo.
4. **9 innovations = 0 memories.** Judge remembers ONE tap (Approve → Undo) + ONE block (Leo can't buy). Rest is appendix.
5. **Honest fallback scared judges.** `/api/diagnostics: pattern-fallback / simulated` reads as "fake AWS" in 60s even though real Strands.Agent + AgentCore + Bedrock Converse are wired.

## What I fixed today (Oct 14, verified, no breakage)

- `docs/devpost_submission.md`: title → *"Tell Alexa Save Me $800. She Proposes. You Tap Once."* Tagline human + tech in one line. Inspiration rewritten to bill + kid + 60-sec magic.
- `docs/demo_video_script.md`: rewrote to WIN CUT 2:30 — 0:00 bill/kid hook, 0:12 live Approve/Undo, 1:05 restock, 1:35 Leo block + CSI, 2:05 15s tech montage. Terminal cut to 3s B-roll. Shooting checklist (Public + Not for Kids, crop localhost bar, real taps).
- `README.md` hero: same hook, 60-sec judge path, commercial sentence (Alexa+ checkout + S&S pattern). Badges kept.
- Verified Stage-1 still green: `evaluate_rubric.py → 100/100`, `test_alexaplus_addon_compliance 11 passed`, 51 tools, MIT LICENSE, friction logs (6) + product feedback present.

## Shipped Oct 14 afternoon (verified, full suite green, rubric 100/100)

- `src/hearth/commerce.py` — "out of everything / fix groceries / restock week" now resolves to low-stock items and stages a Tier-2 cart (still never charges). Vague-but-clear intent works; truly ambiguous ("order something nice") still clarifies. Propose-never-execute intact.
- `mcp-server/server.py` — new `POST /api/commerce/autopilot-checkout` (utterance → staged cart JSON) so the Echo Show voice path can reach checkout.
- `web2/js/echo.js` — fixed misroute where pantry/restock voice went to the acoustic fridge scan; now stages checkout with cart renderer + voice line ("Cart staged for 5 items, saving $35.32. Nothing ordered until you tap Approve."). Fallback message updated.
- `tests/test_echo_surface.py` — new endpoint added to SHOWCASE matrix (staged proposal asserts proposal + cart_preview + message).
- Proof: "we are out of everything, fix groceries" → 5-item cart → Approve → receipt → undo, end-to-end (in-process + live HTTP over :8787: health ok, autopilot staged Tier-2, /echo 200). Full `pytest` green (284 passed), `evaluate_rubric.py` 100/100.
- `web2/echo.html` — new first-position hero chip "Fix groceries" hitting the checkout endpoint, so judges tap once instead of typing.

## Shift log — Oct 14 autonomous build (owner mode, to 8pm IST)

- 14:33–15:00 — Research: 55k-participant rules verified, 9-researcher swarm + 50-spec orchestrator. Pick: Pantry Autopilot sniper (Alexa+), WatchParty flank (Fire TV).
- 15:00–15:10 — Hero fix: everything-intent → low-stock Tier-2 cart (`commerce.py`); ambiguous still clarifies. Proven: stage → Approve → receipt → undo.
- 15:10–15:25 — Echo voice misroute fixed (pantry went to fridge scan) + new `POST /api/commerce/autopilot-checkout` + cart renderer + voice line + hero chips in `/echo` ask-row. SHOWCASE matrix extended.
- 15:25–15:45 — Submission hygiene: all test counts synced + coverage 74.65% measured; demo.sh Step 4b hero proof; feature requests; deploy guide.
- 15:45–16:00 — Found + fixed the day's biggest blocker: Echo's Approval Tray never loaded proposals (panel permanently "Nothing waiting"). Now renders pending (Approve/Reject) + decided (Undo) from `/api/proposals`, with delegated handlers + tray CSS. Added `/api/renewals/stage` so "Save me $800" stages one tap at a time from the Echo surface itself. Roundtrip test locks stage → tray → approve → undo at HTTP layer.
- ~15:30–16:00 — Adversarial review + safety: found Leo could trigger "staged" WORDS while guardrail blocked the action (draft honesty bug across all 8 propose sites in `planner.py`) — fixed so denials read as denials; Leo's drone/audit/unlock now return 0 proposals + "Blocked by the safety contract… Ask an adult". Locked with `test_child_persona_draft_never_claims_staged`. Suite 288 green, rubric 100/100.
- Winners research (Devpost official + AWS Bedrock guide + Alexa/PartyRock/Bedrock-Ber winners): distilled the winning formula — pain in 10s, product by 0:15, one workflow twice, tap+undo as the kept image, Leo denial as moat, 15s credentials, one URL. Rebuilt `docs/demo_video_script.md` as exact-read VO (252 words ≈ 116s, 34s headroom for TTS+taps) + `docs/video_shot_list.md` 1-page shoot plan. Added `?tour=1` autopilot to `/echo` (caption bar + scripted audit→stage→approve→undo→groceries→approve→undo, all real API calls) — verified live over HTTP. Full rules confirmed: <3min hard, 4 equal criteria (Tech/Design/Impact/Idea) + 10% friction-log bonus.
- 9.9 hype pass: cinematic tour splash (title beat), money count-up tick on verdicts, receipt-seal pulse on approve, hero-chip glow, tray copy as contract furniture ("Nothing has run without you… undoes in 1 tap"), index showcase reordered money-first (Save $800 ★ → S&S → Sentinel → CSI…), denial lines lead with "Leo can't spend or unlock — by design, not by prompt". **Caught live bug**: cockpit persona switch never reached `planner.plan()` (env-only read) — Leo on camera would have STAGED instead of denying. Fixed with persona bridge in `/api/chat` + `test_cockpit_persona_switch_drives_guardrail`. Suite 289, rubric 100/100.
- **FILM RENDERED**: `docs/demo_video_v1.mp4` (2:05, h264+aac, burnt captions) — real tour take + Leo denial take, ElevenLabs Rachel VO ×4 blocks + local neural safety block (quota hit zero mid-render), synth music bed, end card + `docs/thumbnail.png` + `docs/captions.srt`. Verified frame-by-frame. Only remaining: upload to YOUR YouTube (Public + Not-for-Kids) + paste link into Devpost.
- ~15:45–17:00 — Consistency sweep: hero phrases unified across `addon.json` + skill manifests + engine generator + fallback hints + Echo placeholder (v1.33.0); README demo.sh section documents Step 4b; dead video link → script link; endpoint fuzz (10 calls, zero 500s); `/echo` payload audit (~75KB, ~25ms local); Fire TV flank plan + competitor memo filed.
- Full `./demo.sh` cold-start judge path: server boot → rubric → compliance 11 → frontier 18 → hero 5 items → 287 passed → READY.

## 9-day sprint to Oct 23 (do in order)

**Oct 14-15 — Video or die**
- [ ] Shoot WIN CUT on phone — printable plan: `docs/video_shot_list.md`, full script: `docs/demo_video_script.md`. FIRST run `make clean && ./demo.sh` for a pristine tray (my test proposals pollute `state/`, which is gitignored ephemeral).
- [ ] YouTube Public + Not for Kids + captions. Paste into devpost_submission.md:25 + Devpost form. Keep raw pytest/rubric run as unlisted backup link in README.
- [ ] 3 GIFs (Approve, Undo, Leo blocked) → top of README + Devpost. No judge reads 633 lines.

**Oct 16-17 — Kill localhost**
- [ ] Deploy in 15 min: `docs/deploy_live_url.md`. Devpost hero link = live URL, not localhost. Keep `./demo.sh` as fallback.
- [ ] Shoot the video on a machine with `pip install -e ".[aws]"`: `strands_sdk_status` there reports genuine `strands.Agent` + `Agent.as_tool()` objects (`aws-strands-sdk-no-inference`), not mocks. Flash `/api/diagnostics` for 3s in the montage — that is the AWS Builder proof. Do NOT rename `pattern-fallback`/`simulated` tokens: tests + docs assert them, and honest backend reporting is the documented design.
- [ ] If no deploy: record 60s phone screen-load with voice, upload as "live demo" — still beats localhost text.
- [ ] 2 hallway tests: real mom/roommate says "finally I trust it" → quote + 15s clip in Devpost. Beats 283-test badge.

**Oct 18-19 — Devpost page polish**
- [ ] Flank decision: Fire TV telestrator plan is filed (`docs/firetv_flank_plan.md`, all endpoints verified present). Start fork only if main entry video is shot.
- [ ] Devpost description = new Inspiration (bill/kid) + 3 GIFs + 60-sec how-to-test + commercial sentence. Move 9 innovations + mermaid + RFC badges below fold.
- [ ] Stage-1 checklist: public repo + MIT visible in About, video shows functioning product, `import + called` (51 `@mcp.tool`, Strands Agent.as_tool — already true), product feedback pasted, friction logs pasted (+10%), reviewers added at submit time (chris-trag, knmeiss, giolaq, anishamalde, mosesroth, emersonsklar — invites expire in 7 days, add Oct 22).
- [ ] Minis: AWS Builder description = multi-service pipeline (Bedrock Converse + AgentCore + Strands — Creative, not single call). Open Source = mcp-strands-adapter URL + repo URL + username + what/why (meaningful feature + 15 tests — Creative, not typo).

**Oct 20-21 — Pre-mortem**
- [ ] Fresh-clone test on clean laptop: `./demo.sh` green in <3 min. Fix any pip miss.
- [ ] Judge skim test: stranger gets hook + Approve/Undo + Leo in 60s without help? If not, simplify again.
- [ ] Feature requests (optional): 1-2 with Critical/Important + why it matters.

**Oct 22-23 — Submit**
- [ ] Add reviewers, submit before Oct 23 12pm PT. Save draft early, final video swap last. Don't touch after deadline (only infringing/PII fixes allowed).

## Judge cheat-sheet (tape to monitor)

- Stage 1 pass/fail → Stage 2 four equals: Tech, Design, Impact, Idea. Tie-break in that order — Tech #1 matters most. Bonus +10% friction logs in Stage 1 → applied Stage 2.
- Alexa+ Creative (wins): agentic cross-service workflow, stateful context, purchasing, cards/carousels, MCP Apps, Agent Skills. Obvious (loses): single-turn Q&A, basic MCP wrapper.
- AWS Builder Creative: Bedrock+AgentCore+Strands pipeline. Obvious: single Bedrock call. Kiro Crew alone qualifies.
- Video <3min hard stop. Show functioning product on intended device. No trademarked music.
- One track prize + one mini max. Pick Alexa+ sharp, layer minis on same project.

## What NOT to change

Don't rewrite engines, don't add 10th innovation, don't chase live Bedrock creds at cost of offline demo. Your moat is Propose-Never-Execute + Undo + child guardrails + 100/100 reproducible proof. Win by making that *felt in 60s*, not by adding more.
