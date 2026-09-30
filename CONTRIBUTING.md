# Contributing to Hearth Universal

MIT open source. PRs welcome — especially new skills, home adapters, and red-team tests.

## Quick start
```bash
pip install -e ".[dev]"
python mcp-server/server.py  # :8787, MCP at /mcp, simulator at /
PYTHONPATH=src python -m pytest -q
```

## Adding a skill
1. Add tools in `mcp-server/server.py` with `@mcp.tool()` (typed args, docstring).
2. Gate consequential actions: `sentinel.judge(...)` + write to `proposals.py` tray, never execute directly.
3. Document in `skill/SKILL.md` (when to call, guardrails, example).
4. Add a test in `tests/test_hearth.py` (allow/ask/deny + happy path).
5. Update README tool list + demo script if user-visible.

## Rules
- Secrets only via `{{vault:NAME}}`; run `vault.redact()` on model-visible text.
- Every consequential action appends to `audit.py` log; keep `audit.verify()` green.
- Keep the simulator zero-build (static HTML/JS) so judges run with pip + python only.
- Small PRs, signed commits preferred, no secrets in diffs.
