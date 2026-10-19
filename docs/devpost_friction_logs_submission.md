# 📝 Official Friction Logs Submission Packet (+10% Judging Bonus)
*Copy and paste the text below directly into the Devpost "Friction Logs" submission field.*

---

### Friction Log 1: FastMCP 2025-11-25 Streamable HTTP Session Negotiation
* **Task Attempted:** Implementing self-hosted FastMCP over Streamable HTTP transport conforming to protocol version 2025-11-25.
* **Steps Taken:** Connected client to `POST /mcp` using SSE streamable headers (`Accept: text/event-stream`). Sent initialize request with protocol version handshake.
* **Expected Result:** Server establishes persistent bidirectional streamable channel without dropped frames.
* **Actual Result:** Client-side connection resets occurred when intermediate proxies stripped chunked transfer encoding, causing header mismatch between standard HTTP response and event stream.
* **Severity:** Medium.
* **Workaround Used:** Implemented an adaptive transport negotiator supporting both standard chunked transfer encoding and buffered JSON-RPC framing fallback.
* **Actionable Suggestion for Amazon SDK:** Provide an official reference middleware in the Amazon Devices Builder Tools that standardizes Streamable HTTP headers and connection keep-alives across diverse hosting environments.

---

### Friction Log 2: AWS Strands Agents SDK Tool Spec Mapping to MCP
* **Task Attempted:** Exposing AWS Strands Agents tools as standard MCP 2025-11-25 tools over Streamable HTTP.
* **Steps Taken:** Decorated Python functions with `@tool` from `strands.Agent`, inspected the generated `tool_spec`, and attempted to serialize for MCP tool registration.
* **Expected Result:** Direct serialization between Strands `tool_spec` and MCP tool schemas.
* **Actual Result:** Strands embeds JSON Schema inside an `inputSchema.json` nested dictionary, whereas MCP 2025-11-25 expects a flat `inputSchema` object. Direct passing caused MCP client validation errors.
* **Severity:** High.
* **Workaround Used:** Authored `mcp-strands-adapter`, a standalone schema flattener that reshapes Strands `tool_spec` into standard MCP format and maps `AgentTool.stream()` to synchronous `tools/call`.
* **Actionable Suggestion for Amazon SDK:** Include an official `@strands.mcp` exporter in the Strands Agents SDK to natively bridge Strands agents into MCP servers.

---

### Friction Log 3: Bedrock AgentCore Memory Local Serialization
* **Task Attempted:** Persisting household conversational turns and episodic memories across sessions using AgentCore Memory primitives.
* **Steps Taken:** Configured `AgentCoreMemory` client with local file storage for zero-key evaluation.
* **Expected Result:** Seamless fallback to local JSON/SQLite serialization when AWS credentials are not present.
* **Actual Result:** The standard AgentCore client threw unhandled authentication exceptions during offline test runs, halting execution.
* **Severity:** Medium.
* **Workaround Used:** Built a decoupled local memory provider that conforms to AgentCore Memory schema contracts, enabling seamless offline judge evaluation while maintaining live cloud sync capability when AWS credentials exist.
* **Actionable Suggestion for Amazon SDK:** Ship a zero-config local emulator package for Bedrock AgentCore Memory in PyPI (`bedrock-agentcore-emulator`) for local development and CI testing.

---

### Friction Log 4: Alexa+ Add-on Manifest (`addon.json`) Schema Validation
* **Task Attempted:** Authoring a declarative skill discovery manifest conforming to the Alexa+ Add-on specification.
* **Steps Taken:** Drafted `addon.json` defining namespace `hearth.operations`, capability declarations, and OAuth scopes.
* **Expected Result:** CLI validator confirms schema compliance with descriptive feedback.
* **Actual Result:** Minor typographical errors in scope arrays produced silent discovery failures rather than descriptive validation warnings.
* **Severity:** Low.
* **Workaround Used:** Built custom JSON Schema test (`tests/test_alexaplus_addon_compliance.py`) asserting schema keys, capability handshakes, and RFC 9728 metadata.
* **Actionable Suggestion for Amazon SDK:** Provide a standalone CLI linting tool (`alexa-addon lint addon.json`) with detailed error messages.

---

### Friction Log 5: Amazon Subscribe & Save Multi-Item Bulk Discount Precision
* **Task Attempted:** Calculating 15% bulk discount thresholds across disparate pantry replenishment consumables.
* **Steps Taken:** Aggregated 5 household low-stock items into an automated checkout staging cart.
* **Expected Result:** Dynamic tier qualification matching Amazon Retail bulk rules (e.g. 5 items = 15% discount).
* **Actual Result:** Rounding discrepancies occurred across fractional unit quantities, causing edge-case threshold miscalculations.
* **Severity:** Low.
* **Workaround Used:** Standardized all pricing math to fixed-point integer cents with deterministic tier evaluation rules.
* **Actionable Suggestion for Amazon SDK:** Publish an official Amazon Retail Subscribe & Save calculation helper in the Alexa+ SDK.

---

### Friction Log 6: Echo Show 15 Smart Canvas Viewport Scalability
* **Task Attempted:** Rendering the ambient household dashboard fluidly across Echo Show 8 (1280x800) and Echo Show 15/21 (1920x1080).
* **Steps Taken:** Built responsive CSS grid layout for the Smart Canvas surface.
* **Expected Result:** Touch targets and telemetry widgets scale gracefully across varying device aspect ratios.
* **Actual Result:** 64dp touch targets overlapped with quick-scene widgets when viewing on smaller 8-inch viewports.
* **Severity:** Medium.
* **Workaround Used:** Implemented container queries (`@container`) and dynamic viewport units to decouple widget geometry from global screen width.
* **Actionable Suggestion for Amazon SDK:** Provide pre-built Echo Show design system web components that guarantee WCAG AAA touch targets across all Echo Show screen sizes.
