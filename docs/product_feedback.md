# Amazon Developer Product Feedback

Submitted for **Build, Ship, Shape: Amazon Developer Hackathon (2026)**  
Entrant: **Hearth Universal Team**  
Track: **Alexa+** | Mini-Challenges: **AWS Builder**, **Open Source**

---

### 1. Which developer tools, APIs, and SDKs did you use and for what?

1. **Model Context Protocol (MCP) Python SDK (`mcp>=1.29.1,<2`)**:
   - Implemented the official MCP specification version **2025-11-25** over Streamable HTTP (`stateless_http=True`).
   - Exposed 35 agentic tools, 4 resources (`household://profile`, `home://state`, `commerce://inventory`, `audit://chain`), and 3 prompt templates (`prepare_family_weekend`, `audit_monthly_finances`, `emergency_lockdown`).
2. **AWS Strands Agents SDK**:
   - Implemented the **Supervisor Multi-Agent Pattern** in [`src/hearth/strands_agent.py`](file:///home/k/Prototype/Amazon/src/hearth/strands_agent.py), coordinating specialized sub-agents (`ArbiterNegotiatorAgent`, `ReplenishmentDepletionAgent`, `SentinelGuardianAgent`).
   - Built the open-source bridge [`src/hearth/mcp_strands_adapter.py`](file:///home/k/Prototype/Amazon/src/hearth/mcp_strands_adapter.py) linking Strands agents to Streamable HTTP MCP tools.
3. **AWS Bedrock AgentCore Memory & Gateway**:
   - Integrated Bedrock AgentCore Memory architecture in [`src/hearth/agentcore.py`](file:///home/k/Prototype/Amazon/src/hearth/agentcore.py) for persistent conversational turns and cross-session episodic memory retrieval.
4. **Amazon Bedrock Converse API (`boto3`)**:
   - Orchestrated multi-turn agentic reasoning with **Anthropic Claude 3.5 Sonnet** (`us.anthropic.claude-3-5-sonnet-20241022-v2:0`) and **Amazon Nova Pro** (`us.amazon.nova-pro-v1:0`).
   - Implemented dynamic multi-model routing based on content hints, adaptive botocore retries, and `system=[]` prompt isolation.
5. **Alexa+ Agent Skills Runtime (`skill/agent_skills_manifest.json`)**:
   - Built the declarative manifest engine and invocation runtime in [`src/hearth/agent_skills.py`](file:///home/k/Prototype/Amazon/src/hearth/agent_skills.py) adhering to Amazon Alexa+ Agent Skills standards.
6. **Amazon Alexa Smart Home v3 API**:
   - Built directive handlers for `Alexa.Discovery`, `Alexa.PowerController`, `Alexa.ThermostatController`, `Alexa.LockController`, and camera stream controllers in [`src/hearth/alexa.py`](file:///home/k/Prototype/Amazon/src/hearth/alexa.py).
7. **FastMCP & Starlette / Uvicorn**:
   - Single-process server running on port `8787` serving MCP protocol endpoints on `/mcp`, REST APIs on `/api/*`, and the static multi-modal Alexa+ simulator on `/`.
8. **SQLite & SHA-256 Cryptographic Chain**:
   - Built an immutable, append-only hash-chained ledger (`audit.jsonl`) verifying that every AI proposal, human approval, and Sentinel block is mathematically tamper-evident.

---

### 2. What worked well? (Setup, Docs, Testing, Performance, Reliability)

- **MCP 2025-11-25 Streamable HTTP Handshake**:
  - The Streamable HTTP transport is a massive improvement over raw stdio pipes for cloud and containerized agent deployment. Being able to verify the server with a simple `curl` initialize command (`protocolVersion: 2025-11-25`) made testing and continuous integration reliable and fast.
- **FastMCP Decorator Ergonomics**:
  - `@mcp.tool()`, `@mcp.resource()`, and `@mcp.prompt()` decorators drastically simplified converting Python functions with type hints and docstrings into fully compliant MCP tool manifests.
- **Amazon Bedrock Converse API**:
  - The unified Converse API (`client.converse()`) provides a cleaner, more consistent contract across model families (Claude, Nova) compared to legacy `InvokeModel` payloads. Cross-region inference profiles (`us.*`) significantly boosted availability.
- **AWS Strands Multi-Agent Pattern**:
  - Structuring domain responsibilities into specialized sub-agents (`Arbiter`, `Replenishment`, `Guardian`) under a supervisor pattern dramatically improved plan coherence and reduced prompt token overhead.
- **Local-First Zero-Config Testing**:
  - Building an intelligent local offline fallback engine allowed our 159-test suite (`pytest`) to run in ~25 seconds without external network dependencies or API keys.

---

### 3. What needs work? (System errors, docs sections, missing features, tool limitations, workarounds)

- **Streamable HTTP `Accept` Header Enforcement**:
  - FastMCP's Streamable HTTP implementation returns HTTP 406 when the `Accept: application/json, text/event-stream` header is omitted. The SDK should default to `application/json` in stateless mode or produce a clear diagnostic message.
- **Stateless MCP Session Handling**:
  - Upstream proxies often inject synthetic `Mcp-Session-Id` headers. FastMCP in `stateless_http=True` mode initially threw session validation warnings before configuring it to cleanly accept and ignore session state.
- **Bedrock Model ID Documentation & Regional Availability**:
  - Finding active regional model IDs for newly released foundation models (e.g. Amazon Nova vs Claude 3.5 Sonnet v2) required hunting across different AWS documentation tables. A centralized discovery endpoint would streamline development.
- **Alexa+ Agent Skills Discovery & Live Debugging**:
  - The transition from traditional Alexa Skills Kit (ASK) interaction models to MCP-based Agent Skills is a huge architectural leap. Providing an interactive cloud-based Skill Inspector or emulator for testing Streamable HTTP endpoints directly from developer.amazon.com would be an enormous win for the ecosystem.

---

### 4. How was your onboarding experience (getting from zero to hello world)?

- **Total time to first working MCP call**: Under 15 minutes.
- **Path taken**:
  1. Cloned repo, created virtual environment, ran `pip install -e ".[dev]"`.
  2. Defined FastMCP server with `@mcp.tool()` and launched on `0.0.0.0:8787`.
  3. Verified `/health` and executed a curl JSON-RPC initialize payload against `/mcp`.
  4. Connected the simulated multi-modal Alexa+ client with voice recognition and digital twin sliders.
- **Zero-Friction Highlight**: Anyone inspecting the repository can run `python mcp-server/server.py` and immediately test the entire application at `http://localhost:8787` without creating accounts, configuring AWS IAM, or purchasing test devices.

---

### 5. Would you build with these devices and services again? Yes/No and please tell us why.

**YES, absolutely.**
- **Why**: The convergence of **MCP (Model Context Protocol)**, **AWS Strands Agents SDK**, **Bedrock AgentCore**, and **Amazon Alexa+** marks a genuine paradigm shift in ambient computing. We can now build assistants that proactively solve complex household problems—negotiating family climate conflicts, auditing subscriptions, restocking essentials before stockouts—while strictly guaranteeing safety through the **Propose-Never-Execute** contract and cryptographic SHA-256 Merkle audit receipts.
