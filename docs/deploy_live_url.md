# 🚀 Live URL in 15 Minutes (kill localhost before judging)

Judges won't clone. Ship `https://<you>/echo` that loads in <3s on a phone. The repo is already container-ready: `infra/Dockerfile` installs `.[aws]` (live Strands backend), exposes 8787, health-checks `/health`, persists `/data`.

## Option A — Fly.io (recommended, free tier)

```bash
fly launch --dockerfile infra/Dockerfile --internal-port 8787
fly volumes create hearth_data --size 1   # persists /data/state (ledger, proposals)
fly secrets set PUBLIC_BASE_URL=https://<your-app>.fly.dev
fly deploy
curl https://<your-app>.fly.dev/health   # must contain "status":"ok"
```

## Option B — AWS App Runner (matches repo config)

```bash
# infra/apprunner.yaml already defines runtime python312, port 8787, .[dev,aws]
aws apprunner create-service --cli-input-yaml file://infra/apprunner.yaml
```

## After deploy — 5 checks

1. `GET /health` → `"status":"ok"`, `"protocol":"2025-11-25"`
2. `GET /echo` → 200, hero chip "Fix groceries" visible
3. `POST /api/commerce/autopilot-checkout` `{"utterance":"we are out of everything, fix groceries","voice_confidence":0.95}` → `"gated":true`, 5 items
4. Phone test: cold load `/echo` <3s on mobile data
5. Paste URL into Devpost "Try It Out" + `docs/devpost_submission.md` Try-It-Out line

## Notes

- No secrets needed for the demo path (offline-first). Do NOT bake AWS creds into the image; Bedrock stays opt-in via env at runtime.
- Keep `./demo.sh` as the fallback judge path — README + Devpost list both.
- addon.json `runtime.endpoint` still says localhost by design (self-hosted add-on doc); the deployed URL is what judges click.
