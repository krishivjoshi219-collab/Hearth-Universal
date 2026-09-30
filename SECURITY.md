# Security policy

## Report
Open a private issue or contact the maintainer listed on Devpost. Do not post live secrets. Expect a response within 7 days; fix target 30 days for high severity.

## Guarantees in this repo
- Secrets live in env (`VAULT_*`), referenced as `{{vault:NAME}}`, redacted before model output.
- Sentinel gate: deny destructive/egress-exfil patterns, ask for money/home/lock actions.
- Propose-never-execute: `actions_propose` writes to tray only; `actions_decide` is human-surface.
- Append-only hash-chained audit (`state/audit.jsonl`, verified by `/health`).
- Sandboxed demo: mock home/inbox, no real bank/mail credentials in code.

## Hardening checklist for self-hosters
- Set `HEARTH_EGRESS_STRICT=1` + `HEARTH_EGRESS_EXTRA` for your brain hosts.
- Serve behind TLS, require Bearer on `/mcp` (add reverse-proxy auth).
- Back up `state/memory.db` + `state/audit.jsonl`; rotate `VAULT_MODEL_KEY` regularly.
