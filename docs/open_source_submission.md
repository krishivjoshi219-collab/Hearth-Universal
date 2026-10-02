# Open Source Mini Challenge Submission Form Copy

Use this exact information for the **Open Source Mini Challenge** field on the Devpost submission form.

---

### 1. Contribution URL / Repository URL
`https://github.com/krishivjoshi219-collab/Hearth-Universal/tree/main/open-source-contribution/mcp-strands-adapter`

### 2. Standalone Package Name
`mcp-strands-adapter` (Version 0.1.0, Apache-2.0 License)

### 3. GitHub Username
`krishivjoshi219-collab`

---

### 4. What We Did
We created **`mcp-strands-adapter`**, a standalone, zero-dependency Python library and bridge that connects Amazon's **AWS Strands Agents SDK** with the **Model Context Protocol (MCP spec 2025-11-25)** over Streamable HTTP. It features:
- Dynamic reflection of Python type annotations and docstrings into official MCP 2025-11-25 JSON Schemas.
- Bi-directional tool conversion: exposing Strands agent functions as MCP tools and allowing Strands supervisors to invoke external MCP tools over HTTP/SSE.
- Complete standalone packaging (`pyproject.toml`, Apache 2.0 license, quickstart examples, and automated pytest suite).

---

### 5. How It Works
1. **Dynamic Parameter Reflection**: `StrandsMCPToolBridge` uses Python's standard `inspect` and `get_type_hints` to automatically synthesize MCP-compliant `inputSchema` dictionaries without third-party dependencies.
2. **Schema Registry**: Registers tool callable references with namespace prefixes (e.g. `strands_pareto_comfort`).
3. **Execution Dispatch**: When an incoming MCP JSON-RPC `tools/call` request arrives over Streamable HTTP, the bridge validates arguments against the registered signature and dispatches to the underlying Strands agent function, returning structured JSON results.

```python
from mcp_strands_adapter import StrandsMCPToolBridge

bridge = StrandsMCPToolBridge(name_prefix="strands_")
schema = bridge.register_strands_tool("tariff_shift", simulate_tariff_shift)
result = bridge.invoke_from_mcp("strands_tariff_shift", {"device": "Dishwasher", "hours_delay": 2})
```

---

### 6. Why It Matters to the Amazon & Alexa+ Community
During the **Build, Ship, Shape: Amazon Developer Hackathon (2026)**, developers building for **Alexa+** are tasked with building MCP servers conforming to spec version 2025-11-25, while developers building for **AWS Builder** are encouraged to adopt the **AWS Strands Agents SDK**.

Until now, these two ecosystems lived in separate silos:
- AWS Strands agents operated within their own execution harness.
- Alexa+ MCP servers required manual tool declarations and boilerplate handlers.

`mcp-strands-adapter` bridges this exact gap: it allows any developer in the AWS or Alexa+ ecosystem to immediately expose their AWS Strands multi-agent tools over FastMCP with zero friction, fostering interoperability across Amazon's agentic tooling.
