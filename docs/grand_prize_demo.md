# Grand-Prize Demo Runbook (3 minutes)

**Thesis in one line:** every other agent demo shows what the AI *can do* — Hearth shows what it can do **and prove it was allowed to**. Autonomy you can trust, that grows its own capability.

---

## The 3-minute live script (exact clicks)

**0:00 — Landing (`/`)** *(5s)*
"There's an Alexa+ add-on that turns a household into an autonomous operator — with a hard rule: it proposes, never executes. And every decision lands in a tamper-evident ledger. Watch."

**0:05 — Echo (`/echo`)** *(40s)*
- Say/type the headline ask: **"Save me $800."** → show the plan + cost deltas.
- Point at the **Auto · Reversible** contract strip: "Nothing moves without a tap."
- Flip one display mode chip (Inline Card → Voice-Only) — shows native Alexa+ Add-on display compliance.

**0:45 — Cockpit (`/web2`)** *(60s)*
- Home: stat tiles + "Next up" — one household, four live systems.
- **Approvals**: click one `✓ Proceed` → item executes and expires. "It works once, then it's dead."
- **Activity**: open one *Why this happened* → the reasoning, in public.
- **Insights**: money recovered + causal twin risk.

**1:45 — 🔨 Hearth Forge (scroll to the panel)** *(50s)* — **THE MOMENT**
- Input is pre-filled: *"Pre-cool the living room to 70F before the 4pm peak tariff."*
- Click **Forge tool**. Six chips light green: Intent → Schema → Sentinel → AST → Smoke → MCP mount.
- Generated source appears. Say: *"Sentinel's policy gate, an AST scan, and a sandbox smoke test all ran before it was allowed to exist."*
- Point at **52 MCP tools live** (was 51). Click **Call it now** → `applied_hour: 22, savings_usd: 3.2`.
- "Five seconds ago this tool did not exist. Now any MCP client on the planet can call it. And if you restart the server — **it's still there**."

**2:35 — Close** *(25s)*
"51 tools, 314 tests, zero console errors. It's not a chatbot — it's a household OS that compounds: safer with every approval, and smarter with every rule you teach it."

---

## Proof commands (if a judge doubts you)

```bash
curl -s localhost:8787/health | python3 -m json.tool   # tools_count, audit_ok, auth_enforced
curl -s localhost:8787/api/forge/tools                  # forged-tool catalog
curl -s -X POST localhost:8787/api/forge/synthesize \
  -H 'content-type: application/json' \
  -d '{"requirement":"Pre-cool the living room to 70F before the 4pm peak tariff"}'
```

## Pre-flight (10 minutes before judging)

1. `make clean` is **not** needed — the auto-staged proposals are the demo.
2. Clear the forge catalog so the 51→52 moment lands live: `rm -f state/synthesized_skills/*.json`, restart the server, confirm `/health` shows `tools_count: 51`.
3. **Warm the server** (startup compiles grammars, can take ~30 s) — never cold-start in front of judges.
4. Open three tabs in order: `/`, `/echo`, `/web2` (cockpit scrolled to Hearth Forge).
5. Hard-refresh once so the browser has the latest CSS/JS (the server sends `no-cache` + ETags, so a normal reload is enough).

## Live-demo fallbacks

| If this breaks | Do this |
|---|---|
| Forge is slow (>5 s) | Keep talking through the chips — they animate while it runs; it's usually <1 s warm. |
| Forge misfires | Stop, reload: any previously forged tool **rehydrates on boot** — show the catalog instead. |
| Network dies | Everything degrades to the offline local engine by design; `/echo` still answers. |
| Judge asks "is this an Echo?" | "The Echo Show surface is the product; this browser runs the identical MCP server the device talks to." |

## The two things only you can do (and they matter more than any code)

1. **Re-film the 2:30 video** — the existing one predates every rebuild. Judges watch the video first; a stale video loses before the repo is opened. Shot list = the 3-minute script above, condensed.
2. **Deploy the live URL** — `infra/Dockerfile` + `docs/production_readiness.md` §3 (TLS proxy, secrets, healthcheck). A live link converts skeptics.

One-line fix: `web2/landing.html` still says "292 passing tests" — it's **314** now.
