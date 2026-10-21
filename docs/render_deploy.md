# Deploy Hearth to Render

The repo ships a `render.yaml` blueprint. The live surface is the same one the
film shows: `/` landing, `/echo` cockpit, `/mcp` (55 tools), `/demo_film/…`.

## One-click blueprint

Render Dashboard → **New** → **Blueprint** → pick this repo → **Apply**.
The blueprint sets the build, start command, health check, and `autoDeploy: false`.

## Manual service (if the service already exists)

- **Runtime**: Python 3.12
- **Build command**: `pip install -e .`
- **Start command**:
  ```
  mkdir -p state/synthesized_skills && cp -n seed/synthesized_skills/*.json state/synthesized_skills/ 2>/dev/null; python3 mcp-server/server.py
  ```
- **Health check path**: `/health`
- The server binds `0.0.0.0:$PORT` automatically.

## Environment (Dashboard → Environment)

| Key | Value |
| --- | --- |
| `OPENAI_API_KEY` | the Groq key (`gsk_…`) — **secret**, never commit |
| `HEARTH_BRAIN_PROVIDER` | `groq` |
| `HEARTH_BASE_URL` | `https://api.groq.com/openai/v1` |
| `HEARTH_MODEL` | `llama-3.3-70b-versatile` |
| `HEARTH_CHAT_RPM` | `20` |
| `PYTHON_VERSION` | `3.12` |

No key? The app still runs: chat falls back to the local engine (fast,
deterministic, no cloud). The cockpit, film, Forge, and MCP surface are
unaffected.

Never upload or commit `state/brain_config.json` — keys live only in Render's
environment.

## Verify (from outside)

```bash
U=https://YOUR-APP.onrender.com
curl -s $U/health
curl -s $U/api/forge/tools | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['tools_count'], len(d['tools']))"   # 55 4
curl -s -X POST $U/api/chat -H 'content-type: application/json' \
  -d '{"message":"say ready in 3 words"}' | grep -o '"provider":"[^"]*"'   # "provider":"groq"
curl -s -o /dev/null -w '%{http_code} %{size_download}\n' -H 'Range: bytes=0-1023' $U/demo_film/HEARTH_DEMO_FINAL.mp4  # 206 1024
```

Then open `$U/` on a phone and `$U/echo`, and play the film from the landing.

## Keep it awake for judging (Nov 9–20)

Render free instances sleep after ~15 idle minutes. Ping `/health` every 10:

```bash
nohup scripts/render_keepalive.sh https://YOUR-APP.onrender.com \
  >> /tmp/opencode/render_keepalive.log 2>&1 &
```

The machine has to stay on. The reboot-proof variant is a GitHub Actions
workflow with `schedule: cron: '*/10 * * * *'` curling `/health`.

## Freeze

`autoDeploy` is off in the blueprint. After the first successful deploy, make
sure the dashboard also has Auto-Deploy off, so a late push cannot change the
judged URL's behavior.
