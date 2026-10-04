# Open Source Mini Challenge Submission Form Copy

Use this exact information for the **Open Source Mini Challenge** field on the Devpost submission form.

---

### 1. Contribution URL / Repository URL

**Repository URL:** `https://github.com/krishivjoshi219-collab/Hearth-Universal`

**Contribution URL (the library):**
`https://github.com/krishivjoshi219-collab/Hearth-Universal/tree/main/open-source-contribution/mcp-strands-adapter`

### 2. Standalone Package Name

`mcp-strands-adapter` (Version 0.2.0, Apache-2.0 License)

### 3. GitHub Username

`krishivjoshi219-collab`

---

### 4. What We Did

We built **`mcp-strands-adapter`**, a small Python library that lets an MCP host such as
Alexa+ call AWS Strands agents and tools. It is a **new standalone open-source project**
(Apache-2.0), published inside the Hearth Universal hackathon repository.

The Strands Agents SDK ships tooling to *consume* MCP servers. It does not ship a
straightforward way to *expose* Strands agents to an MCP host. This library covers that
direction — **Strands → MCP** — so a Strands multi-agent system can be driven by an
Alexa+ add-on over Streamable HTTP.

What it actually does:

- **Reuses the SDK's own schemas.** Hand it a `@tool`-decorated function and it reads the
  SDK's `tool_spec` rather than re-deriving one. The SDK already does this correctly, with
  Pydantic and `docstring_parser`, so duplicating it would only be worse.
- **Reshapes the one thing that differs.** Strands nests its JSON Schema at
  `inputSchema.json`; MCP expects it flat at `inputSchema`. That transformation is the
  core of the library.
- **Exports whole agents.** A bare `strands.Agent` is adapted through `Agent.as_tool()`.
  Because that result exposes an async `stream()` rather than `__call__`, the adapter
  drains it on a private event loop and returns the final text payload, because MCP
  `tools/call` is synchronous. An SDK-declared error is raised, not swallowed.
- **Keeps mounted schemas honest.** Parameter defaults, `int` vs `number` fidelity, and
  docstring `Args:` descriptions survive the round trip to FastMCP, so the schema a host
  sees matches the definition the bridge reports.
- **Fails loudly.** Unknown tool names and unexpected arguments raise rather than being
  silently dropped.

Also included: standalone packaging, an Apache-2.0 license, a runnable quickstart that
works with or without the optional dependency, and **15 unit tests**.

### 5. How It Works

1. **Normalize** — accept a `@tool` function, a `strands.Agent`, or a plain callable.
   Strands tools are recognised by duck-typing on `tool_spec`, so the library does not
   pin itself to private SDK classes across point releases.
2. **Reshape the schema** — lift `inputSchema.json` out to MCP's flat `inputSchema`.
   Plain callables fall back to signature reflection, with descriptions parsed from the
   docstring instead of emitted as `Parameter x` placeholders.
3. **Register and mount** — `register_all(mcp, tools)` binds each tool onto a FastMCP
   server with a rebuilt signature, so FastMCP's own Pydantic-derived schema matches the
   advertised definition, defaults included.
4. **Dispatch** — `bridge.call(name, arguments)` is what an MCP `tools/call` maps onto:
   it coerces JSON scalars to the annotated types and forwards to the handler.

```python
from mcp.server.fastmcp import FastMCP
from strands import Agent, tool
from mcp_strands_adapter import MCPServerBridge

@tool
def tariff_shift(kwh: float, hours: int = 2) -> dict:
    """Shift load off the peak tariff window.

    Args:
        kwh: energy to shift
        hours: how long to defer
    """
    return {"shifted_kwh": kwh, "hours": hours}

mcp = FastMCP("household")
MCPServerBridge(prefix="hearth_").register_all(mcp, [tariff_shift])
# serve with: mcp.run(transport="streamable-http")
```

Dispatch can also be exercised directly, without a server:

```python
bridge = MCPServerBridge(prefix="hearth_")
bridge.add(tariff_shift)
bridge.list_tools()                                    # -> MCP tools/list definitions
bridge.call("hearth_tariff_shift", {"kwh": 3.0, "hours": 3})
```

`StrandsMCPToolBridge` remains as a backwards-compatible alias for `MCPServerBridge`.

### 6. Dependencies

Honest about what it needs, rather than claiming zero:

| Extra | Installs | When to use |
|---|---|---|
| *(core)* | `mcp>=1.23.0,<2.2` | mounting on a FastMCP server |
| `strands` | `strands-agents>=1.57.0,<2` | exporting real Strands tools/agents |
| `aws` | `strands-agents` + `boto3` | live Bedrock inference |

The Strands-specific tests skip automatically when the extra is absent, so the suite is
green either way — verified in both environments.

### 7. Why It Matters to the Amazon & Alexa+ Community

In the **Build, Ship, Shape: Amazon Developer Hackathon (2026)**, Alexa+ developers are
asked to build MCP servers conforming to spec 2025-11-25, while AWS Builder developers are
pointed at the Strands Agents SDK. Both tracks get a real toolchain; neither ships the
seam between them in this direction.

For an Alexa+ developer who already has Strands agents, this is the missing five lines
between "I have a multi-agent system" and "a resident can ask Alexa to run it." For a
Strands developer publishing an agent library, it is the difference between "reachable
only from Python" and "discoverable by any MCP host."

It is deliberately narrow. It does one direction, does the schema reshaping correctly,
and refuses to reimplement what the SDK already does well. In Hearth Universal it backs a
real deployment: a Strands supervisor (`ArbiterNegotiatorAgent`, `ReplenishmentDepletionAgent`,
`SentinelGuardianAgent`) reachable as MCP tools over the same `:8787/mcp` endpoint that
serves all 51 tools.

### 8. Verification

```bash
pip install -e ".[dev]"
pytest tests/ -v          # 15 tests
python examples/quickstart.py
```