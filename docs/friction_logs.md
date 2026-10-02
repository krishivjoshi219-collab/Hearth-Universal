# Developer Friction Log

**Competition:** Build, Ship, Shape: Amazon Developer Hackathon (2026)  
**Track:** Alexa+ | **Mini-Challenges:** AWS Builder, Open Source  
**Evaluation Category:** Friction Log Submission (Eligible for **up to 10% Bonus Points**)

---

### Friction Entry 1: Streamable HTTP `Accept` Header Negotiation in MCP Server

- **Specific Task Attempted**:  
  Perform standard `initialize` handshake with FastMCP Streamable HTTP server via `curl` and automated HTTP client libraries.
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
  Server logged warnings and returned session mismatch errors (`Session ID not recognized`).
- **Severity Rating**: **Critical**
- **Workaround Used**:  
  Overrode session verification middleware to permit arbitrary session identifiers when `stateless_http=True` is set.
- **Actionable Suggestion for Developer Relations / SDK Team**:  
  Document the exact session affinity contract for stateless MCP servers in the Alexa+ developer portal, and ensure the SDK does not validate session IDs when explicitly configured in stateless mode.

---

### Friction Entry 3: Amazon Bedrock Converse API Regional Model ID & Profile Discovery

- **Specific Task Attempted**:  
  Dynamically invoke Amazon Bedrock models (`Claude 3.5 Sonnet` and `Amazon Nova Pro`) across different AWS regions (`us-east-1`, `us-west-2`).
- **Steps Taken**:  
  1. Initialized `boto3.client("bedrock-runtime", region_name=region)`.
  2. Passed model ID string `anthropic.claude-3-5-sonnet-20241022-v2:0` to `client.converse()`.
- **Expected Result**:  
  Consistent execution across supported regions.
- **Actual Result**:  
  Cross-region inference profiles require prepending `us.` or `eu.` prefixes (e.g. `us.anthropic.claude-3-5-sonnet-20241022-v2:0`). When a developer inputs a standard model ID in a region using cross-region routing, Bedrock returns a `ValidationException`.
- **Severity Rating**: **Important**
- **Workaround Used**:  
  Created an internal provider normalization map in `src/hearth/brains.py` with automatic region prefixing and graceful failover to offline simulation.
- **Actionable Suggestion for Developer Relations / SDK Team**:  
  Update the AWS Bedrock documentation to highlight cross-region inference profile IDs upfront in the Converse API getting-started tutorials.

---

### Friction Entry 4: Alexa+ Agent Skills Manifest Tool Schema Reflection

- **Specific Task Attempted**:  
  Generate declarative Alexa+ Agent Skills manifest schemas (`skill/agent_skills_manifest.json`) from dynamically registered Python MCP tools.
- **Steps Taken**:  
  1. Inspected FastMCP tool parameters using Python's `inspect` and Pydantic field annotations.
  2. Exported tool definitions into the Alexa+ Agent Skills capability structure.
- **Expected Result**:  
  Clean reflection of input JSON schemas without requiring duplicate manual manifest definitions.
- **Actual Result**:  
  FastMCP wraps parameter definitions inside Pydantic models whose schema generation can produce `$defs` references or complex title fields that the Alexa+ Agent Skills parser rejects as non-primitive.
- **Severity Rating**: **Important**
- **Workaround Used**:  
  Built a normalized schema transformer in `src/hearth/mcp_strands_adapter.py` that strips internal `$defs` references and produces flat JSON Schema object definitions.
- **Actionable Suggestion for Developer Relations / SDK Team**:  
  Publish an official JSON Schema validator CLI for Alexa+ Agent Skills manifests to let developers lint their manifests before deploying.

---

### Friction Entry 5: Bedrock AgentCore Memory State Serialization & SQLite Concurrency Locks

- **Specific Task Attempted**:  
  Persist rapid conversational turns and episodic context in Bedrock AgentCore Memory while simultaneous background household heartbeat ticks occur.
- **Steps Taken**:  
  1. Simulated multi-threaded household ticks advancing long-running goals in parallel with chat turns.
  2. Wrote episodic memory entries to local file storage.
- **Expected Result**:  
  Non-blocking writes with atomic persistence.
- **Actual Result**:  
  Under concurrent thread access, uncoordinated file writes caused intermittent `JSONDecodeError` on subsequent reads.
- **Severity Rating**: **Important**
- **Workaround Used**:  
  Wrapped all AgentCore Memory read/write cycles in `src/hearth/agentcore.py` with atomic file locking (`src/hearth/atomic.py`) and temporary file renaming.
- **Actionable Suggestion for Developer Relations / SDK Team**:  
  Provide a reference local persistence adapter in the AWS AgentCore Python starter kit that includes atomic file lock semantics.

---

### Friction Entry 6: AWS Strands Agents SDK Sub-Agent Exception Isolation

- **Specific Task Attempted**:  
  Orchestrate parallel sub-agent calls (`ArbiterNegotiatorAgent`, `ReplenishmentDepletionAgent`) via the Strands Supervisor pattern when one sub-agent encounters missing telemetry.
- **Steps Taken**:  
  1. Invoked Strands Supervisor with a complex multi-domain goal.
  2. Simulated a transient timeout in the replenishment data provider.
- **Expected Result**:  
  The supervisor isolates the failure to the specific sub-agent, continues executing remaining sub-agents, and presents partial results.
- **Actual Result**:  
  An unhandled exception in one sub-agent halted the entire supervisor execution loop without returning partial findings.
- **Severity Rating**: **Important**
- **Workaround Used**:  
  Wrapped sub-agent execution in `src/hearth/strands_agent.py` with individual `try/except` blocks, collecting partial summaries and reporting degraded status gracefully.
- **Actionable Suggestion for Developer Relations / SDK Team**:  
  Incorporate built-in fault tolerance and partial resolution patterns directly into the AWS Strands Agents SDK supervisor harness.
