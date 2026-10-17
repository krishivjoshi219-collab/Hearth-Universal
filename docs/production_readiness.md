# Production readiness

**Verdict:** Hearth is production-grade for what it is designed to be — a
**single-node household deployment** (one family, one server, one state
directory). It is not, and does not claim to be, a multi-tenant SaaS. This
document states exactly what is enforced, how to run it, and where the honest
limits are.

---

## 1. At a glance

| Area | Status | Evidence |
|---|---|---|
| Fail-fast production config | ✅ enforced | `_validate_env()` refuses to boot `HEARTH_ENV=production` without PIN, auth salt, audit HMAC key and an `https://` base URL |
| Auth on mutating actions | ✅ enforced | Adult PIN gates approvals/insights; `auth_enforced` surfaced in `/health` |
| Tamper-evident audit | ✅ enforced | Hash-chained `state/audit.jsonl` (HMAC-bound), `audit_ok` in `/health` |
| Rate limiting | ✅ enforced | 30 req/min/IP on `/api/chat`; 200 req/min/IP global POST budget on every mutating route |
| Request timeouts | ✅ enforced | 25 s chat deadline → honest `504`, client-safe retry |
| Non-leaky errors | ✅ enforced | `http_hardening.RequestHardeningMiddleware` converts uncaught exceptions to JSON 500 with `X-Request-Id`; tracebacks stay in server logs |
| Security headers + CSP | ✅ enforced | `script-src 'self'` (no inline JS), `frame-ancestors 'none'`, nosniff, referrer policy |
| BYO API key at rest | ✅ enforced | `state/brain_config.json`, `chmod 0600`, atomic write, masked hints only, wiped by `make clean` |
| Health & metrics | ✅ present | `/health` (state writable, DB ok, audit chain ok), `/api/metrics` counters |
| Cache correctness | ✅ present | Static assets revalidate (`no-cache` + ETag/304); `/api/*` is `no-store` |
| Graceful shutdown | ✅ present | Uvicorn drain + `tini` as PID 1 in the container |
| Container hygiene | ✅ present | Non-root user, slim pinned base, `HEALTHCHECK`, no dev deps in image |
| CI gates | ✅ enforced | Ruff, compileall, `node --check`, pytest on Python 3.11 + 3.12 with coverage |
| Accessibility basics | ✅ present | ARIA tablist/tabpanel wiring, visible focus rings, `prefers-reduced-motion`, keyboard-operable dialogs |

Advisory scanners (bandit, pip-audit, gitleaks) run in CI but do not block yet —
see §9.

---

## 2. Runtime modes

### Demo (default)

```bash
make run            # http://localhost:8787
```

Zero config. Auth is relaxed, synthetic household data is enabled, and the
cockpit auto-stages proposals so the product is explorable immediately.

### Production

```bash
export HEARTH_ENV=production
export HEARTH_ADULT_PIN='<6+ digit pin>'
export HEARTH_AUTH_SALT='<32+ random chars>'
export HEARTH_AUDIT_KEY='<32+ random chars>'
export PUBLIC_BASE_URL='https://hearth.example.com'
export PORT=8787
make run
```

Boot **fails loudly** if any of the four production secrets/URLs are missing or
malformed. Generate values with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 3. Deploy runbook (single node)

```bash
make docker-build
docker run -d --name hearth \
  --restart unless-stopped \
  -p 127.0.0.1:8787:8787 \
  -v "$PWD/state:/app/state" \
  -e HEARTH_ENV=production \
  -e HEARTH_ADULT_PIN -e HEARTH_AUTH_SALT -e HEARTH_AUDIT_KEY \
  -e PUBLIC_BASE_URL \
  hearth-universal:latest
```

Terminate TLS in front of the container (Caddy/nginx/ALB) and forward
`X-Forwarded-For` so per-IP limits see real clients. Keep the container port
bound to loopback. `docker inspect --format '{{.State.Health.Status}}' hearth`
should report `healthy`.

### Backup and restore

```bash
make backup                                  # tar of state/ → backups/state-<utc>.tgz
tar -xzf backups/state-<utc>.tgz -C .        # restore (stop the server first)
```

Back up `state/` on a schedule — it holds proposals, the audit ledger, the
household SQLite memory, and the BYO-key config. `make clean` refuses to run
when `HEARTH_ENV=production`.

---

## 4. Observability

`GET /health` returns the operational truth used by the container healthcheck:

- `status`, `version`, `uptime_s`, protocol/transport
- `tools` count, `state_writable`, `db_ok`, `audit_ok`, `auth_enforced`,
  `brain.configured` (never the key itself)

`GET /api/metrics` exposes in-memory counters (`chat`, `decide`,
`chat_rate_limited`, `global_limited`, `chat_timeout`, `auth_denied`) for
dashboards and alerting. Counters reset on restart by design — they are for
rate/error trends, not billing.

Every HTTP response carries `X-Request-Id`; API 500s include the same id in the
JSON body, so a user report can be matched to a server traceback.

Suggested alerts: `status != ok` for 2 min; `audit_ok == false` (page
immediately); `chat_timeout` rate > 5%; 429 rate > 10% sustained (limit tuning
or abuse); disk > 85%.

---

## 5. Limits & SLOs

| Control | Value | Where |
|---|---|---|
| Chat request deadline | 25 s → `504` | `/api/chat` |
| Chat rate limit | 30 / min / IP | `HEARTH_CHAT_RPM` |
| Global mutating budget | 200 / min / IP | `HEARTH_GLOBAL_RPM` |
| Proposals retained | 100 (oldest trimmed) | `proposals` store |
| Audit ledger retention | 10 000 lines, then hash-linked archive | `audit.AUDIT_MAX_LINES` |
| Static assets | revalidate each load, `304` when unchanged | `FileResponse` + ETag |
| API responses | `Cache-Control: no-store` | hardening middleware |

---

## 6. Privacy & secrets

- A household-supplied model key lives only in `state/brain_config.json`
  (`0600`), is never returned by any endpoint (masked last-4 hint only), and is
  never logged.
- Vault redaction runs on memory writes and audit payloads.
- No analytics, no third-party calls except the model endpoint the household
  itself configures (or the offline local reasoner).
- `docs/SECURITY.md` holds the disclosure policy; rotate `HEARTH_AUTH_SALT`,
  `HEARTH_AUDIT_KEY` and the model key on personnel change.

---

## 7. CI gates (every push / PR)

| Gate | Blocking? |
|---|---|
| `ruff check src mcp-server tests` | ✅ yes |
| `python -m compileall src mcp-server` | ✅ yes |
| `node --check web2/js/*.js` | ✅ yes |
| `pytest` on Python 3.11 and 3.12 with coverage | ✅ yes |
| bandit (SAST) | advisory |
| pip-audit (dependencies) | advisory |
| gitleaks (secret scan) | advisory |

The advisory scanners are intentionally non-blocking until their findings are
triaged into a baseline; the lint, syntax and test gates are hard and currently
clean.

---

## 8. Known limits (honest)

- **Single node.** JSON/SQLite state and in-memory rate counters do not
  replicate. Horizontal scaling needs an external store and a shared limiter.
- **One shared household PIN**, not per-user accounts/OIDC. Sufficient for a
  family deployment; multi-tenant use needs an identity provider.
- **Synchronous JSON state reads** inside async routes. Files are small and
  requests are cheap; at high concurrency move state I/O to a thread pool/DB.
- **No built-in TLS.** Terminate at a reverse proxy; `PUBLIC_BASE_URL` must be
  `https://` in production.
- **Rate limits reset on restart.** Fine for abuse control; not a billing-grade
  quota.
- **No APM/exporter.** `/api/metrics` + request ids are scrape-friendly; add an
  OpenTelemetry exporter for fleet operations.

---

## 9. Release checklist

- [ ] `ruff check src mcp-server tests` → clean
- [ ] `for f in web2/js/*.js; do node --check "$f"; done` → clean
- [ ] `pytest` → all green
- [ ] Boot with `HEARTH_ENV=production` and verify `/health` reports
      `auth_enforced: true`, `audit_ok: true`, `state_writable: true`
- [ ] `make backup` succeeds and the archive restores into a scratch dir
- [ ] TLS proxy in front, `PUBLIC_BASE_URL` matches, port bound to loopback
- [ ] Rotate secrets if anyone with access left the project
