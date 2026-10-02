"""Neighborhood Swarm Grid & Decentralized Virtual Power Plant (VPP) for Amazon Alexa+.

Federates neighboring Hearth Universal nodes over FastMCP Streamable HTTP protocol.
Allows households to pool solar generation, battery storage, and EV charge schedules
into a hyper-local microgrid cooperative, arbitraging energy peer-to-peer at fair rates
($0.18/kWh) instead of selling surplus to utility monopolies for pennies ($0.03/kWh).
"""
from __future__ import annotations
import secrets
import time
from typing import Any, Dict, List
from . import audit, home_mock, proposals


class NeighborhoodSwarmGrid:
    """Decentralized municipal microgrid arbitrator for federated smart homes."""

    def __init__(self) -> None:
        self._last_dispatch: Dict[str, Any] | None = None

    def coordinate_microgrid(
        self,
        export_kw: float = 3.8,
        custom_peers: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """Arbitrate peer-to-peer energy trades across neighborhood nodes."""
        trade_id = f"vpp_{secrets.token_hex(6)}"
        now = int(time.time())

        # Participating neighborhood nodes
        nodes = custom_peers or [
            {
                "node_id": "hearth-node-local",
                "name": "Oak Lane Resident (Local Hub)",
                "role": "SURPLUS_EXPORTER",
                "solar_generation_kw": 6.2,
                "home_consumption_kw": 2.4,
                "net_available_kw": export_kw,
                "battery_soc_pct": 94,
                "utility_feedin_tariff_kwh": 0.035,  # Utility pays pathetic $0.035
            },
            {
                "node_id": "hearth-node-02",
                "name": "104 Maple Drive (EV Charging)",
                "role": "DEFICIT_CONSUMER",
                "demand_type": "Tesla Model Y Scheduled Charge",
                "required_kw": 4.5,
                "battery_soc_pct": 28,
                "utility_peak_tariff_kwh": 0.485,  # Utility charges predatory $0.485
            },
            {
                "node_id": "hearth-node-03",
                "name": "212 Cedar Court (Heat Pump Surge)",
                "role": "PEAK_SHEDDER",
                "demand_type": "Geothermal Heat Pump Pre-Cool",
                "required_kw": 2.1,
                "battery_soc_pct": 65,
                "utility_peak_tariff_kwh": 0.485,
            },
        ]

        # P2P Cooperative settlement rate
        coop_rate_kwh = 0.18  # Fair price for both buyer and seller!
        allocated_kw = min(export_kw, 3.8)

        # Economic delta calculation
        seller_revenue_utility = allocated_kw * 0.035
        seller_revenue_coop = allocated_kw * coop_rate_kwh
        seller_net_gain = seller_revenue_coop - seller_revenue_utility

        buyer_cost_utility = allocated_kw * 0.485
        buyer_cost_coop = allocated_kw * coop_rate_kwh
        buyer_net_savings = buyer_cost_utility - buyer_cost_coop

        total_community_dividend_hr = seller_net_gain + buyer_net_savings
        carbon_offset_kg_hr = round(allocated_kw * 0.85, 2)

        transfers = [
            {
                "trade_tx": f"tx_{secrets.token_hex(4)}",
                "from_node": "Oak Lane Resident",
                "to_node": "104 Maple Drive",
                "power_kw": allocated_kw,
                "settlement_rate_kwh": coop_rate_kwh,
                "duration_minutes": 60,
                "seller_dividend_hr": round(seller_net_gain, 3),
                "buyer_savings_hr": round(buyer_net_savings, 3),
                "grid_congestion_relief": "High (Feeder Transformer Sub-Load Reduced)",
            }
        ]

        result = {
            "dispatch_id": trade_id,
            "timestamp": now,
            "swarm_status": "OPTIMAL_COOPERATIVE_DISPATCH",
            "active_nodes_count": len(nodes),
            "allocated_peer_power_kw": allocated_kw,
            "cooperative_rate_kwh": coop_rate_kwh,
            "economic_impact": {
                "seller_hourly_gain_usd": round(seller_net_gain, 2),
                "buyer_hourly_savings_usd": round(buyer_net_savings, 2),
                "total_community_dividend_hourly_usd": round(total_community_dividend_hr, 2),
                "annualized_neighborhood_wealth_retention_usd": round(total_community_dividend_hr * 4 * 365, 2),
            },
            "environmental_impact": {
                "carbon_offset_kg_co2e_hr": carbon_offset_kg_hr,
                "avoided_fossil_peaker_dispatch": True,
            },
            "p2p_transactions": transfers,
            "nodes": nodes,
            "voice_summary": (
                f"Neighborhood Swarm Grid dispatch active. Routing {allocated_kw} kW of surplus solar to 104 Maple Drive "
                f"at 18 cents per kilowatt hour. You earn 55 cents more per hour than utility buyback, while saving your neighbor "
                f"over one dollar per hour in peak tariffs."
            ),
        }

        audit.append(
            "swarm_grid",
            "microgrid_dispatch_settled",
            {
                "trade_id": trade_id,
                "allocated_kw": allocated_kw,
                "community_dividend": total_community_dividend_hr,
            },
        )
        self._last_dispatch = result
        return result

    def get_latest_dispatch(self) -> Dict[str, Any]:
        """Retrieve recent dispatch or compute nominal swarm."""
        if self._last_dispatch:
            return self._last_dispatch
        return self.coordinate_microgrid()


swarm_grid = NeighborhoodSwarmGrid()
