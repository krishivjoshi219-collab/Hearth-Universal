# Security Audit: Findings, Triage, SBOM

> Generated artifacts: `bandit.json` (82 findings), `pip-audit.json`,
> `sbom.cyclonedx.json` (213 components). Rerun:
> `python3 -m bandit -r src mcp-server -f json -o docs/security/bandit.json`
> and `python3 -m pip_audit --desc --format=json --output docs/security/pip-audit.json`.
> Scanned 2026-10-03. CI runs the same tools (non-blocking until judging ends).

## Dependency audit: 0 vulnerabilities in project deps

`pip-audit` reports 112 vulns across the 22-package *system* environment,
but **all 16 shipped project dependencies are clean**:

| package | version | vulns |
|---|---|---|
| mcp | 1.30.0 | 0 |
| fastapi / starlette / uvicorn / sse-starlette | 0.141.1 / 1.6.0 / 0.53.0 / 3.4.11 | 0 |
| pydantic / httpx / httpx-sse / anyio / pyyaml | 2.13.5 / 0.28.1 / 0.4.3 / 4.15.1 / 6.0.1 | 0 |
| numpy | 2.5.3 | 0 |
| pytest / pytest-asyncio / pytest-cov / bandit / ruff | 9.1.1 / 1.4.0 / 7.1.0 / 1.9.4 / 0.16.7 | 0 |

Remaining 96 findings belong to host-system packages never shipped in
`infra/Dockerfile` (`python:3.12-slim` + `pip install .`). SBOM:
`sbom.cyclonedx.json`.

## Bandit triage: 0 HIGH, 9 MEDIUM (all intended-design)

| ID | Location | Verdict |
|---|---|---|
| B104 bind 0.0.0.0 | `mcp-server/server.py:212` | Intended: container listen; TLS terminates at proxy/frigate per `config.example.yaml`. |
| B310 `urlopen` | `brains.py:148`, `model_mesh.py:138`, `webtools.py:67,98` | User-configured endpoints only; provider registration is SSRF-guarded (`_host_allowed`, private/metadata nets blocked); `webtools` blocks redirects. |
| B102 `exec` ×2 | `meta_skill.py:198,304` | The synthesizer's core: AST-validated code only, executed with stripped builtins (`abs/min/max/round/sum/len/dict/list/float/int/bool/str`), Sentinel-pattern sweep, sandboxed smoke test. See `sandbox_smoke()`. |
| B108/B603/B404 subprocess | `sandbox.py:9,142,145` | Allowlisted binaries, `shell=False`, jailed `cwd`, capped env/timeout/output, every call audited. This *is* the sandbox. |
| B105/B107 "passwords" (LOW) | `real_mode.py`, `alexa.py`, `alexaplus_addon.py` | Vault placeholders (`{{vault:...}}`), `"Bearer"` prefixes, redaction masks (`••••`) — no real secrets. Gitleaks clean. |

LOW B110/B311/B112/B101 (try/except logging, `random` for Monte Carlo/synthesis
seeds — never cryptographic, `secrets` used for tokens): accepted,
fail-safe defaults by design.

## Secrets posture

- No secrets in repo (`.gitignore` + `.dockerignore` exclude `.vault.env`,
  `config.yaml`, `.env*`); `vault.resolve` fail-closes to `""`.
- Demo fallbacks (`hearth-demo-audit-key-v1`, static salt) refuse production
  when `HEARTH_REQUIRE_AUDIT_KEY=1` / `HEARTH_ENV=production` (Copilot gate).
- OAuth: single-use codes, rotating refresh, HMAC-compared PKCE verifiers.
