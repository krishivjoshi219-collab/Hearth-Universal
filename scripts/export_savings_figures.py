#!/usr/bin/env python3
"""Export savings methodology figures GENERATED from live code (never hand-typed).

Writes:
  docs/savings_figures.csv  — subscription line items with evidence + savings
  docs/savings_figures.json — cart bundle math, swarm auction math, acoustic part math

The whitepaper docs/savings_methodology.md quotes these files; CI can re-run
this script and diff to prove docs == code.
"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from hearth import commerce, swarm  # noqa: E402

DOCS = os.path.join(ROOT, "docs")


def main() -> None:
    subs = commerce.scan_subscriptions()
    services = subs["subscriptions"]

    csv_path = os.path.join(DOCS, "savings_figures.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["service", "annual_cost_usd", "usage_evidence",
                    "recommendation", "savings_yr_usd"])
        for s in services:
            w.writerow([s.get("name"), f"{s.get('cost_yr', 0):.2f}",
                        s.get("usage_status"), s.get("recommendation"),
                        f"{s.get('savings_yr', 0):.2f}"])

    cart = commerce.stage_amazon_cart()
    grid = swarm.swarm_grid.coordinate_microgrid(export_kw=3.8)
    econ = grid["economic_impact"]
    fridge = None
    try:
        from hearth import acoustic
        scan = acoustic.acoustic_doctor.scan_appliance_acoustics(
            target_appliance="all", stage_remedy=False)
        fridge = next((a for a in scan["appliances"]
                       if a["id"] == "app_fridge_01"), None)
    except Exception:
        fridge = None

    figures = {
        "subscriptions": {
            "total_annual_spend_usd": round(subs["total_annual_spend"], 2),
            "potential_annual_savings_usd": round(
                subs["potential_annual_savings"], 2),
            "formula": "sum(savings_yr where recommendation in (cancel, downgrade))",
        },
        "cart_bundle": {
            "regular_subtotal_usd": round(cart.get("regular_subtotal", 0), 2),
            "final_total_usd": round(cart.get("final_total", 0), 2),
            "savings_usd": round(cart.get("savings", 0), 2),
            "item_count": cart.get("item_count"),
            "formula": "regular_subtotal - final_total at 15% Subscribe & Save tier",
        },
        "swarm_vpp": {
            "allocated_kw": grid["allocated_peer_power_kw"],
            "clearing_price_kwh": grid["cooperative_rate_kwh"],
            "utility_buyback_kwh": 0.035,
            "utility_peak_kwh": 0.485,
            "seller_gain_hr_usd": econ["seller_hourly_gain_usd"],
            "buyer_save_hr_usd": econ["buyer_hourly_savings_usd"],
            "community_dividend_hr_usd":
                econ["total_community_dividend_hourly_usd"],
            "annualized_retention_usd":
                econ["annualized_neighborhood_wealth_retention_usd"],
            "carbon_kg_hr": grid["environmental_impact"]["carbon_offset_kg_co2e_hr"],
            "formula": ("seller_gain = kW*(clearing - 0.035); "
                        "buyer_save = kW*(0.485 - clearing); "
                        "annualized = hourly_dividend * 4h/day * 365d"),
        },
        "acoustic_part": ({
            "detected_peak_hz": fridge["detected_peak_hz"],
            "failure_probability_14d": fridge["failure_probability_14d"],
            "regular_price_usd": fridge["remedy"]["regular_price"],
            "final_price_usd": fridge["remedy"]["final_price"],
            "formula": "final = regular * (1 - 0.15 Subscribe & Save)",
        } if fridge and fridge.get("remedy") else None),
        "data_source": "sandbox fixture (see commerce.sandbox_disclaimer); "
                       "arithmetic is real, inputs are declared synthetic",
    }
    json_path = os.path.join(DOCS, "savings_figures.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(figures, f, indent=2)

    print(f"wrote {csv_path} ({len(services)} services)")
    print(f"wrote {json_path}")
    print(f"headline savings: ${figures['subscriptions']['potential_annual_savings_usd']:.2f}/yr")


if __name__ == "__main__":
    main()
