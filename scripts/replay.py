#!/usr/bin/env python3
"""Deterministic replay: re-run every demo number with fixed seeds.

Wrapper-only: seeds are set at the entrypoint (PYTHONHASHSEED, random,
numpy, HEARTH_SEED). Engine physics are never touched. IDs/timestamps are
stripped from compared values — only semantic outputs must match.

Usage:
  python3 scripts/replay.py --seed 42                  # run + compare golden
  python3 scripts/replay.py --seed 42 --update-golden  # refresh golden
  ./replay.sh                                          # judge one-command
"""
import argparse
import json
import os
import random
import subprocess
import sys
import tempfile

SEED_DEFAULT = 42

os.environ["PYTHONHASHSEED"] = str(SEED_DEFAULT)
os.environ["HEARTH_SEED"] = str(SEED_DEFAULT)
os.environ["HEARTH_STATE_DIR"] = tempfile.mkdtemp(prefix="hearth-replay-")
random.seed(SEED_DEFAULT)
try:
    import numpy as _np
    _np.random.seed(SEED_DEFAULT)
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from hearth import (  # noqa: E402
    acoustic, causal_twin, forensics, mediation, parliament, proposals, swarm,
)


def collect(seed):
    proposals.clear_proposals()
    out = {}

    s = parliament.parliament.deliberate(
        "Severe heatwave during $0.52/kWh peak tariff with low solar yield",
        {"peak_tariff": 0.52, "target_temp": 70, "battery_soc": 88})
    out["parliament"] = {
        "speeches": len(s.speeches), "vote": s.vote,
        "nash": s.nash_equilibrium_score,
        "utilities": s.pareto_compromise["utilities"],
        "candidates": s.candidate_count,
        "frontier_size": len(s.pareto_frontier),
    }

    twin = causal_twin.CausalDigitalTwinEngine(seed=seed)
    sim = twin.run_simulation(days_ahead=7, iterations=150)
    out["causal_twin"] = {
        "days": sim.days_ahead, "iterations": sim.monte_carlo_iterations,
        "vulns": [[v.hazard_type, v.probability_pct] for v in sim.vulnerabilities],
        "savings": sim.expected_savings_usd,
        "resilience": sim.grid_resilience_score,
        "p50": sim.quantiles["baseline"]["p50"],
        "cvar95": sim.quantiles["baseline"]["cvar95"],
    }

    rec = forensics.forensics_engine.reconstruct_incident("perimeter_anomaly")
    out["forensics"] = {"verdict": rec["verdict"],
                        "confidence": rec["confidence_score"],
                        "posteriors": rec["posteriors"],
                        "timeline_len": len(rec["timeline"])}

    scan = acoustic.acoustic_doctor.scan_appliance_acoustics(stage_remedy=False)
    fridge = next(a for a in scan["appliances"] if a["id"] == "app_fridge_01")
    out["acoustic"] = {
        "peak_hz": fridge["detected_peak_hz"], "status": fridge["status"],
        "health": fridge["health_score"], "p14": fridge["failure_probability_14d"],
        "rul": fridge["projected_failure_days"],
        "degradation": fridge["diagnostics"]["degradation_index"]}

    treaty = mediation.family_mediator.draft_household_treaty(
        topic="monthly_household_equilibrium")
    out["mediation"] = {
        "fairness": treaty["fairness_index_out_of_10"],
        "covenants": len(treaty["covenants"]),
        "nash": treaty["nash_product"], "envy_gap": treaty["envy_gap"],
        "savings_mo": treaty["projected_monthly_savings_usd"]}

    grid = swarm.swarm_grid.coordinate_microgrid(export_kw=3.8)
    out["swarm"] = {
        "price": grid["cooperative_rate_kwh"],
        "cleared": grid["allocated_peer_power_kw"],
        "econ": grid["economic_impact"],
        "carbon": grid["environmental_impact"]["carbon_offset_kg_co2e_hr"]}

    return out


def git_sha():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            text=True).strip()
    except Exception:
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED_DEFAULT)
    ap.add_argument("--update-golden", action="store_true")
    args = ap.parse_args()

    os.environ["HEARTH_SEED"] = str(args.seed)
    random.seed(args.seed)

    values = collect(args.seed)
    golden_path = os.path.join(ROOT, "replays", "golden.json")
    manifest = {"seed": args.seed, "git_sha": git_sha(),
                "protocol": "2025-11-25", "values": values}

    if args.update_golden:
        os.makedirs(os.path.dirname(golden_path), exist_ok=True)
        with open(golden_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
        print(f"golden updated: {golden_path}")
        return

    with open(golden_path, encoding="utf-8") as f:
        golden = json.load(f)
    if golden["values"] != values:
        print("REPLAY MISMATCH vs", golden_path)
        for k in values:
            if golden["values"].get(k) != values[k]:
                print(f"  [{k}] golden={golden['values'].get(k)}")
                print(f"  [{k}] actual={values[k]}")
        sys.exit(1)
    print(f"replay identical: seed={args.seed} sha={manifest['git_sha']} "
          f"({len(values)} engines, semantic outputs match golden)")


if __name__ == "__main__":
    main()
