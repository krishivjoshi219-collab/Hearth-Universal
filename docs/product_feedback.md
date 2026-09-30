# Amazon Developer Product Feedback

Submitted for **Build, Ship, Shape: Amazon Developer Hackathon (2026)**  
Entrant: **Hearth Universal Team**  
Track: **Alexa+** | Mini-Challenges: **AWS Builder**, **Open Source**

---

### 1. Which developer tools, APIs, and SDKs did you use and for what?

1. **Model Context Protocol (MCP) Python SDK (`mcp>=1.29.1`)**:
   - Implemented the official MCP specification version **2025-11-25** over Streamable HTTP (`stateless_http=True`).
   - Exposed 15 agentic tools (`memory_query`, `home_get_state`, `inbox_scan`, `actions_propose`, etc.), 4 resources (`household://profile`, `home://state`, `commerce://inventory`, `audit://chain`), and 3 prompt templates (`prepare_family_weekend`, `audit_monthly_finances`, `emergency_lockdown`).
2. **Amazon Bedrock Converse API (AWS SDK / `boto3`)**:
   - Orchestrated multi-turn agentic reasoning with **Anthropic Claude 3.5 Sonnet** (`anthropic.claude-3-5-sonnet-20241022-v2:0`) and **Amazon Nova Pro** (`amazon.nova-pro-v1:0`).
   - Used the standardized Converse API interface for structured intent classification, DAG decomposition, and token telemetry tracking.
3. **Alexa+ Agent Skills Architecture (`SKILL.md`)**:
   - Packaged Hearth Universal's tool schemas, safety guardrails, and propose-never-execute triggers into an interoperable skill package for Alexa+ orchestrators.
4. **FastMCP & Starlette / Uvicorn**:
   - Single-process server running on port `8787` serving MCP protocol endpoints on `/mcp`, REST APIs for the simulated client on `/api/*`, and the static multi-modal Alexa+ simulator on `/`.
5. **Web Speech Synthesis & Web Speech Recognition APIs**:
   - Integrated full two-way voice capabilities into the web simulator: voice dictation input and Alexa voice text-to-speech audio feedback.
6. **SQLite & SHA-256 Cryptographic Chain**:
   - Built an immutable, append-only hash-chained ledger (`audit.jsonl`) verifying that every AI proposal and human approval is mathematically tamper-evident.

---

### 2. What worked well? (Setup, Docs, Testing, Performance, Reliability)

- **MCP 2025-11-25 Streamable HTTP Handshake**:
  - The Streamable HTTP transport is a massive improvement over raw stdio pipes for cloud and containerized agent deployment. Being able to verify the server with a simple `curl` initialize command (`protocolVersion: 2025-11-25`) made testing and continuous integration reliable and fast.
- **FastMCP Decorator Ergonomics**:
  - `@mcp.tool()`, `@mcp.resource()`, and `@mcp.prompt()` decorators drastically simplified converting Python functions with type hints and docstrings into fully compliant MCP tool manifests.
- **Amazon Bedrock Converse API**:
  - The unified Converse API (`client.converse()`) provides a cleaner, more consistent contract across model families (Claude, Nova, Mistral, Llama) compared to legacy `InvokeModel` payloads with vendor-specific JSON formats.
- **Local-First Zero-Config Testing**:
  - Building an intelligent local offline fallback engine allowed automated test suites (`pytest`) to run in sub-second time without flaky external cloud network dependencies or credential hurdles.

---

### 3. What needs work? (System errors, docs sections, missing features, tool limitations, workarounds)

- **Streamable HTTP `Accept` Header Enforcement**:
  - In initial testing with FastMCP's Streamable HTTP implementation, omitting the `Accept: application/json, text/event-stream` header caused ambiguous 406 Not Acceptable errors or hung connections. The SDK should either default to JSON in stateless mode or produce a clear, human-readable error diagnosing the missing header.
- **Stateless MCP Session Handling**:
  - When deploying behind cloud load balancers or proxy runtimes (such as AWS AgentCore or ALB), requests often arrive with ephemeral or auto-generated `Mcp-Session-Id` headers. FastMCP in `stateless_http=True` mode initially threw session validation warnings before configuring it to cleanly accept and ignore session state.
- **Bedrock Model ID Documentation & Regional Availability**:
  - Locating active regional model IDs for newly released foundation models (e.g. Amazon Nova variants vs Claude 3.5 Sonnet v2) required hunting across different AWS documentation tables. A single centralized CLI command or auto-discovery endpoint in the Bedrock SDK for "list-available-chat-models-in-region" would save developers significant setup time.
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
- **Why**: The convergence of **MCP (Model Context Protocol)** and **Amazon Alexa+** is the exact inflection point personal voice assistants have needed for a decade. Moving away from rigid, brittle custom voice intents toward generalized tool execution and agentic DAG planning allows assistants to solve real, consequential household problems (e.g., proactive subscription auditing, pantry replenishment, multi-room comfort orchestration) while preserving human agency through glass-box approval trays.
- The developer experience of writing self-hosted Python MCP servers and dropping an Agent Skill into an orchestrator is vastly superior to maintaining legacy bespoke webhooks. We plan to actively maintain and deploy Hearth Universal as a production personal agent on Fire OS and Echo Show devices.
