"""10/10 proof: every frontier engine must be input-sensitive, not fixture-pinned.

Regression guards analogous to mediation's test_mediation_is_input_sensitive:
- forensics flips verdict with intruder-like sensors
- acoustic tracks an injected fault frequency and goes healthy on override<=0
- swarm clearing price moves with buyer bids and respects feeder limit
- REST + MCP surfaces expose the same knobs
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))

import server
from starlette.testclient import TestClient

from hearth import acoustic, forensics, swarm


def test_forensics_is_input_sensitive():
    benign = forensics.forensics_engine.reconstruct_incident("perimeter_anomaly")
    assert benign["verdict"] == "BENIGN_PHYSICAL_DISPLACEMENT"

    intruder = forensics.forensics_engine.reconstruct_incident(
        "perimeter_anomaly",
        sensor_readings={
            "wind_mph": 4.0,
            "hvac_cfm": 60.0,
            "humidity_pct": 45.0,
            "torque_nm": 1.4,
            "applied_force_n": 65.0,
            "pir_delta_temp_c": 0.8,
            "intruder_biometric_confidence": 0.88,
        },
    )
    assert intruder["verdict"] == "INTRUDER_LIKELY_ENTRY", intruder["posteriors"]
    assert intruder["posteriors"]["intruder"] > benign["posteriors"]["intruder"]
    assert intruder["confidence_score"] >= 0.50


def test_acoustic_tracks_injected_fault():
    default = acoustic.acoustic_doctor.scan_appliance_acoustics(stage_remedy=False)
    fridge = next(a for a in default["appliances"] if a["id"] == "app_fridge_01")
    assert fridge["detected_peak_hz"] == 124.5

    moved = acoustic.acoustic_doctor.scan_appliance_acoustics(
        stage_remedy=False, fault_hz_override=180.0, synth_seed=42)
    fridge2 = next(a for a in moved["appliances"] if a["id"] == "app_fridge_01")
    assert abs(fridge2["detected_peak_hz"] - 180.0) < 3.0, fridge2["detected_peak_hz"]
    assert fridge2["status"] == "DEGRADED_BEARING_WEAR"

    healthy = acoustic.acoustic_doctor.scan_appliance_acoustics(
        stage_remedy=False, fault_hz_override=0)
    fridge3 = next(a for a in healthy["appliances"] if a["id"] == "app_fridge_01")
    assert fridge3["status"] == "HEALTHY"
    assert fridge3["failure_probability_14d"] < 0.30


def test_swarm_price_moves_with_bids():
    base = swarm.swarm_grid.coordinate_microgrid(export_kw=3.8)
    assert base["cooperative_rate_kwh"] == 0.18

    low_bid = swarm.swarm_grid.coordinate_microgrid(
        export_kw=3.8,
        bids=[
            {"node": "104 Maple Drive", "price": 0.12, "qty": 4.5},
            {"node": "212 Cedar Court", "price": 0.11, "qty": 2.1},
        ],
    )
    assert low_bid["cooperative_rate_kwh"] != base["cooperative_rate_kwh"], (
        base["cooperative_rate_kwh"], low_bid["cooperative_rate_kwh"])

    capped = swarm.swarm_grid.coordinate_microgrid(export_kw=3.8, feeder_limit_kw=1.0)
    assert capped["allocated_peer_power_kw"] <= 1.0 + 1e-9
    assert capped["allocated_peer_power_kw"] < base["allocated_peer_power_kw"]


def test_rest_surfaces_expose_inputs():
    client = TestClient(server.mcp.streamable_http_app())
    r = client.post("/api/forensics/reconstruct", json={
        "incident_type": "perimeter_anomaly",
        "sensor_readings": {"wind_mph": 4.0, "torque_nm": 1.4,
                            "intruder_biometric_confidence": 0.88,
                            "applied_force_n": 65.0, "hvac_cfm": 60.0},
    })
    assert r.status_code == 200
    assert r.json()["verdict"] == "INTRUDER_LIKELY_ENTRY"

    r = client.post("/api/acoustic/scan", json={"fault_hz_override": 0, "stage_remedy": False})
    assert r.status_code == 200
    fridge = next(a for a in r.json()["appliances"] if a["id"] == "app_fridge_01")
    assert fridge["status"] == "HEALTHY"

    r = client.post("/api/swarm/grid", json={"export_kw": 3.8, "buyer_peak_tariff": 0.12})
    assert r.status_code == 200
    assert r.json()["cooperative_rate_kwh"] != 0.18

    r = client.post("/api/mediation/treaty", json={
        "topic": "t1",
        "statements": {"A": "I do all kitchen cleanup", "B": "budget $500 please"},
    })
    assert r.status_code == 200
    assert r.json()["topic"] == "t1"
