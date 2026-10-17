# ❓ Judge FAQ (every answer runnable in 60s)

1. **Does it really use MCP 2025-11-25?** Yes — `curl -X POST localhost:8787/mcp -H "Accept: application/json, text/event-stream"` with an `initialize` body returns `"protocolVersion":"2025-11-25"`. 51 `@mcp.tool` in `mcp-server/server.py`.
2. **Does it really use Strands, not just name it?** Yes — `strands_sdk_status` shows genuine `strands.Agent` objects with SDK-derived tools (`aws-strands-sdk-no-inference` here; `pattern-fallback` only when the SDK is absent). Install `.[aws]` for the live path.
3. **Does it spend real money in the demo?** No — and that's the point. Every consequential action stages a Tier-2 tray card; nothing executes until a human taps Approve (single-use receipt), and every approval undoes in one tap.
4. **What happens on vague input?** It clarifies instead of guessing: "order something nice" → `clarification_required:true`, nothing staged. "Out of everything" → resolves to measured low-stock items, still staged not charged.
5. **Can a kid buy things?** No — Leo (child persona) gets tier-3 `deny` on orders and unlocks (`child_safety_policy`), while safe comfort actions stay allowed. Switch persona in the header and try.
6. **How is it more than a Q&A bot?** One utterance chains memory → inbox audit → bundle optimizer → cart proposal → tray → receipt → ledger across sessions — agentic workflow with state, purchasing, and MCP Apps cards.
7. **Where's the open-source contribution?** `open-source-contribution/mcp-strands-adapter/` (Apache-2.0, 15 tests): exposes Strands agents *as* MCP tools, reusing the SDK's own `tool_spec`.
8. **What AWS services?** Bedrock Converse (Nova Pro/Claude router, opt-in), AgentCore-compatible memory with live-sync, Strands multi-agent supervisor. `/api/diagnostics` reports exactly which backend ran.
9. **Reproducibility?** `./demo.sh` cold-start → rubric 100/100 → 309 tests green. `./replay.sh` replays decisions deterministically.
10. **Do I need an API key?** No — the 1-click demo runs fully offline. If you *want* free-form answers on your own model, click **🧠 Connect AI** in `/echo` and paste a key (OpenAI, Groq, OpenRouter, Ollama, any OpenAI-compatible base URL, or Bedrock). It is stored at `state/brain_config.json` (0600, gitignored) and never leaves the machine except to the provider you chose.
11. **Beyond the hackathon, who pays?** Grocers/retailers (S&S attach + fewer stockouts), property managers (sub-$200 fix flow), care orgs (adherence proof) — anywhere trust blocks autonomous purchase.
