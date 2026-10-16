# 🏈 Fire TV Flank: CoachTelestrator (second submission, same backend)

**Pick:** youth-sports telestrator. Kid's game paused on TV, coach draws with D-pad + Alexa voice, Hearth explains kid-simple + saves drills. Zero overlap with the Alexa+ saver entry. All endpoints below verified present in `mcp-server/server.py`.

**Starter:** `github.com/amazon-fire-tv-samples/react-native-multi-tv-app-sample` (RN + Leanback, Fire OS + Vega OS). Fork to `flank-firetv-telestrator/`. TV app = thin client on `http://<host>:8787`; all smarts server-side (already built):

1. `POST /api/alexa/voice-turn` — "pause and show where the zone broke"
2. `POST /api/alexa/dpad` — telestration strokes
3. `POST /api/chat` → planner — kid-words fix
4. `GET+POST /api/memory` — per-kid playbook persistence
5. `POST /api/meta-skills/synthesize` — live drill skill
6. `GET /api/diagnostics` — tech-montage proof

**9 days:** 10/14 fork + D-pad overlay in Vega sim → 10/15 voice/chat → 10/16 memory/synthesize → 10/17 Leanback polish → 10/18 point at live URL (`docs/deploy_live_url.md`) → 10/19 shoot (kid+coach, frozen game, voice gap-draw, D-pad circle, saved drill) → 10/20 Devpost + Appstore text → 10/21 hallway test → 10/22-23 submit.

**Why it wins:** no streaming grid (dodges Obvious); pause → telestrate → explain → persist → synthesize is 10-foot D-pad + voice native. Impact: $0 assistant coach for youth leagues, Vega/Fire OS sports retention.
