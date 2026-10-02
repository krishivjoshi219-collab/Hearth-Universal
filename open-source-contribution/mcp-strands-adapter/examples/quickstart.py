#!/usr/bin/env python3
"""Quickstart example demonstrating mcp-strands-adapter."""

from mcp_strands_adapter import StrandsMCPToolBridge


def simulate_tariff_shift(device: str, hours_delay: int, peak_rate: float = 0.48) -> dict:
    """Calculates cost savings achieved by shifting an appliance cycle off-peak."""
    savings = (peak_rate - 0.12) * 2.2 * 1.0  # estimate 2.2 kWh cycle
    return {
        "device": device,
        "delayed_by_hours": hours_delay,
        "projected_savings_usd": round(savings, 2),
        "status": "scheduled_off_peak",
    }


def main():
    bridge = StrandsMCPToolBridge(name_prefix="strands_")
    schema = bridge.register_strands_tool("simulate_tariff_shift", simulate_tariff_shift)

    print("--- 1. Generated MCP 2025-11-25 Schema ---")
    import json
    print(json.dumps(schema, indent=2))

    print("\n--- 2. Invocation via MCP Payload ---")
    response = bridge.invoke_from_mcp(
        "strands_simulate_tariff_shift",
        {"device": "Bosch 800 Dishwasher", "hours_delay": 3, "peak_rate": 0.52},
    )
    print("Execution output:", response)


if __name__ == "__main__":
    main()
