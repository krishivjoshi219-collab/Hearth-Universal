#!/usr/bin/env python3
"""Quickstart: expose AWS Strands agents to an MCP host.

Run without Strands installed to see the plain-callable path:

    python examples/quickstart.py

Run with the extra to also exercise the real Strands path:

    pip install "mcp-strands-adapter[strands]"
    python examples/quickstart.py
"""
import json

from mcp_strands_adapter import MCPServerBridge, strands_available, to_mcp_tool


def simulate_tariff_shift(device: str, hours_delay: int, peak_rate: float = 0.48) -> dict:
    """Calculate savings from shifting an appliance cycle off-peak.

    Args:
        device: appliance to schedule
        hours_delay: how long to defer the cycle
        peak_rate: current peak price per kWh
    """
    savings = (peak_rate - 0.12) * 2.2  # ~2.2 kWh cycle
    return {
        "device": device,
        "delayed_by_hours": hours_delay,
        "projected_savings_usd": round(savings, 2),
        "status": "scheduled_off_peak",
    }


def main() -> None:
    print(f"strands-agents installed: {strands_available()}\n")

    print("--- 1. Plain callable -> MCP tool definition ---")
    definition = to_mcp_tool(simulate_tariff_shift, prefix="strands_")
    print(json.dumps(definition, indent=2))

    print("\n--- 2. Invocation via an MCP tools/call payload ---")
    bridge = MCPServerBridge(prefix="strands_")
    bridge.add(simulate_tariff_shift)
    print(json.dumps(
        bridge.call("strands_simulate_tariff_shift",
                    {"device": "Bosch 800 Dishwasher", "hours_delay": 3, "peak_rate": 0.52}),
        indent=2,
    ))

    print("\n--- 3. Mounting on a FastMCP server (Streamable HTTP) ---")
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("hearth-demo")
    MCPServerBridge(prefix="hearth_").register_all(mcp, [simulate_tariff_shift])
    for t in mcp._tool_manager.list_tools():
        print(f"  mounted: {t.name}  schema={json.dumps(t.parameters)}")

    if strands_available():
        print("\n--- 4. Real Strands @tool -> MCP tool definition ---")
        from strands import tool

        @tool
        def verify_audit_chain() -> dict:
            """Verify the tamper-evident household audit ledger.

            Returns:
                dict: chain integrity status
            """
            return {"chain_intact": True, "entries": 128}

        strands_def = to_mcp_tool(verify_audit_chain, prefix="hearth_")
        print(json.dumps(strands_def, indent=2))
        print("note: schema came from the SDK's own tool_spec (inputSchema.json "
              "reshaped to MCP's flat inputSchema), not from local reflection.")
        b2 = MCPServerBridge()
        b2.add(verify_audit_chain)
        print("invocation:", b2.call("verify_audit_chain", {}))


if __name__ == "__main__":
    main()