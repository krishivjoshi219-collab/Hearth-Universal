# Developer Friction Log

**Competition:** Build, Ship, Shape: Amazon Developer Hackathon (2026)  
**Track:** Alexa+ | **Mini-Challenges:** AWS Builder, Open Source  
**Evaluation Category:** Friction Log Submission (Eligible for **up to 10% Bonus Points**)

---

### Friction Entry 1: Streamable HTTP `Accept` Header Negotiation in MCP Server

- **Specific Task Attempted**:  
  Perform standard `initialize` handshake with the FastMCP Streamable HTTP server via `curl` and automated HTTP client libraries.
- **Steps Taken**:  
  1. Configured FastMCP with `stateless_http=True` and `streamable_http_path="/mcp"`.
  2. Executed `curl -X POST http://localhost:8787/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0",...}'`.
- **Expected Result**:  
  Server returns standard JSON-RPC response with server capabilities and protocol version `2025-11-25`.
- **Actual Result**:  
  Server rejected the request with HTTP `406 Not Acceptable` or streamed raw unparsed Server-Sent Event (SSE) frames without terminating.
- **Severity Rating**: **Important**
- **Workaround Used**:  
  Explicitly passed both content types in headers: `-H "Accept: application/json, text/event-stream"`.
- **Actionable Suggestion for Developer Relations / SDK Team**:  
  When `json_response=True` is enabled on the server, the SDK should default to `application/json` even if the client's `Accept` header is omitted or `*/*`. Additionally, if rejecting on `Accept`, return a structured JSON error explaining the required MIME types.

---

### Friction Entry 2: Stateless MCP Header Stripping & `Mcp-Session-Id` Injection

- **Specific Task Attempted**:  
  Deploy the MCP server behind a standard reverse proxy (AWS ALB / CloudFront) to simulate an Alexa+ cloud orchestrator connection.
- **Steps Taken**:  
  1. Started FastMCP server with `stateless_http=True`.
  2. Routed HTTP POST traffic from proxy.
  3. Upstream proxy injected a synthetic `Mcp-Session-Id` header for connection tracking.
- **Expected Result**:  
  Stateless server ignores any injected session headers and treats each HTTP POST independently.
- **Actual Result**:  
  Server logged warnings and occasionally returned session mismatch errors (`Session ID not recognized`).
- **Severity Rating**: **Critical**
- **Workaround Used**:  
  Overrode session verification middleware to permit arbitrary session identifiers when `stateless_http=True` is set.
- **Actionable Suggestion for Developer Relations / SDK Team**:  
  Document the exact session affinity contract for stateless MCP servers in the Alexa+ developer portal, and ensure the SDK does not validate session IDs when explicitly configured in stateless mode.

---

### Friction Entry 3: Schema Generation for Optional Dictionary Arguments in FastMCP Tools

- **Specific Task Attempted**:  
  Expose the `actions_propose` and `home_update_device` MCP tools with optional metadata dictionaries (`meta: dict | None = None`).
- **Steps Taken**:  
  1. Annotated function signature with `meta: dict | None = None`.
  2. Called `tools/list` over MCP JSON-RPC.
- **Expected Result**:  
  The tool manifest in `tools/list` exposes `meta` as an optional object property with `{ type: "object" }`.
- **Actual Result**:  
  Pydantic type reflection in older FastMCP builds omitted the property description or threw a schema generation warning for unstructured dictionary types.
- **Severity Rating**: **Important**
- **Workaround Used**:  
  Explicitly typed parameters using primitive fallback strings or serialized JSON strings (`meta: str = ""`) in the outer tool interface, parsing internally.
- **Actionable Suggestion for Developer Relations / SDK Team**:  
  Provide a standardized guide on Pydantic v2 type mapping for FastMCP tools, including examples for nested dictionaries, lists, and enums.

---

### Friction Entry 4: Amazon Bedrock Converse API Regional Model ID Discovery

- **Specific Task Attempted**:  
  Dynamically invoke Amazon Bedrock models (`Claude 3.5 Sonnet` and `Amazon Nova Pro`) across different AWS regions (`us-east-1`, `us-west-2`, `eu-west-1`).
- **Steps Taken**:  
  1. Initialized `boto3.client("bedrock-runtime", region_name=region)`.
  2. Passed model ID string `anthropic.claude-3-5-sonnet-20241022-v2:0` to `client.converse()`.
- **Expected Result**:  
  Consistent execution across supported regions.
- **Actual Result**:  
  Model IDs have subtle syntax variations across versions (`:0` suffix vs raw name), and cross-region inference profiles require prepending `us.` or `eu.` prefixes (e.g. `us.anthropic.claude-3-5-sonnet-20241022-v2:0`). When a developer inputs a standard model ID in a region using cross-region routing, Bedrock returns a `ValidationException`.
- **Severity Rating**: **Important**
- **Workaround Used**:  
  Created an internal provider normalization map in `src/hearth/brains.py` with automatic region prefixing and graceful failover to offline simulation.
- **Actionable Suggestion for Developer Relations / SDK Team**:  
  Update the AWS Bedrock documentation to highlight cross-region inference profile IDs upfront in the Converse API getting-started tutorials.

---

### Friction Entry 5: Web Speech Synthesis Inconsistency Across Embedded Device WebViews

- **Specific Task Attempted**:  
  Enable Alexa voice text-to-speech audio playback in the simulated Alexa+ interface when tested inside tablet/embedded browsers (Fire OS / Android WebViews).
- **Steps Taken**:  
  1. Called `window.speechSynthesis.speak(utterance)` upon receiving the agent's plan.
- **Expected Result**:  
  Natural voice playback begins immediately.
- **Actual Result**:  
  Browsers require a prior user interaction (click/tap) before allowing audio playback. On initial load, voice synthesis was silently muted without throwing an exception.
- **Severity Rating**: **Nice-to-have**
- **Workaround Used**:  
  Added a visible "🔊 Voice: ON/OFF" control in the simulator header and tied the audio activation to the first "Send" or prompt chip interaction.
- **Actionable Suggestion for Developer Relations / SDK Team**:  
  When providing templates for simulated web experiences, include a pre-flight audio unlock pattern in the sample starter kit.
