# Implementation plan

## Goal
Win Alexa+ ($25k) with an open glass-box agent that runs on any key, plus Open Source mini. No AWS account, no devices required.

## Architecture
Single FastMCP server (stateless Streamable HTTP 2025-11-25) owns `/mcp` + custom routes (`/health`, `/api/*`, `/`). Static PWA simulator, no build. Modules: `vault`, `sentinel`, `audit`, `memory` (SQLite), `home_mock`, `proposals`, `brains` (OpenAI-compatible + mock fallback + Bedrock slot), `planner` (DAG).

## Done
- 49 MCP tools, 8 resources, 3 prompts; curl-verified initialize/tools/list/tools/call.
- Approval tray seeded by money-intent chat; scene suggestions for home intent; memory API + UI.
- 9 pytest (gate, redaction, audit chain, memory, home, proposals, planner).
- Docs: friction x5, product feedback, demo script, contributing, security.

## Next (only if time before Oct 23)
1. Record <3min video per script; capture live brain-swap + deny + refresh-persist.
2. Optional AWS Builder: implement `bedrock_chat()` + AgentCore Dockerfile run, document usage.
3. Optional second OSS contribution: fork a popular MCP client with Hearth skill example; link PR.
4. Red-team 10 more prompts; add evals file with pass/fail.

## Risks
- MCP spec drift → pinned 2025-11-25, verified live.
- Key-less judges → mock fallback keeps demo alive.
- Scope creep → freeze tools at 12; new ideas become skills post-submission.
