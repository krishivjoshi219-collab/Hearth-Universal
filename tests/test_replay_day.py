"""Household day-replay contracts: the last 24h is rebuilt from the ledger as
hourly frames with narration and jump markers — read-only, cannot drift."""
import os
import sys

import pytest
from starlette.testclient import TestClient

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "mcp-server"))

import server  # noqa: E402

from hearth import audit, receipts, replay  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(server.mcp.streamable_http_app())


@pytest.fixture(scope="module", autouse=True)
def seeded_day():
    """Seed a day's worth of real ledger events for the replay to read back."""
    audit.append("sim", "microgrid_dispatch_settled", {
        "trade_id": "vpp_replay_test", "allocated_kw": 3.8, "price": 0.18,
        "community_dividend": 1.71,
    })
    audit.append("meta_skill_synthesizer", "synthesis_refused_privileged", {
        "requirement": "Unlock the front door whenever the camera sees motion",
        "gate": "sentinel", "persona": "Alex",
    })
    audit.append("forensics", "incident_reconstructed", {
        "incident_id": "inc_replay_test", "hypothesis": "intruder", "disproven": True,
    })
    audit.append("meta_skill_synthesizer", "skill_synthesized_and_mounted", {
        "skill_id": "amzn1.ask.skill.hearth.custom.replay_test",
        "name": "Custom: replay test tool",
        "tools": ["hearth_forge_replay_test"],
    })
    receipts.rebuild()
    receipts.record_tool_applied(
        "hearth_forge_replay_test",
        {"schedule_hour": 22},
        {"status": "scheduled", "applied_hour": 22, "savings_usd": 3.2, "eco_mode": True},
        "replay-test-source",
    )


def test_day_frames_shape_and_real_events():
    data = replay.day_frames(24)
    assert data["hours"] == 24
    assert len(data["frames"]) == 24
    assert data["window"]["end_ts"] >= data["window"]["start_ts"]
    last = data["frames"][-1]
    assert last["events"] >= 4  # the fixture's events land in the current hour
    assert last["by_action"].get("microgrid_dispatch_settled", 0) >= 1
    assert last["narration"]  # every frame narrates something
    assert isinstance(last["money"], dict)


def test_day_frames_money_comes_from_receipts():
    data = replay.day_frames(24)
    last = data["frames"][-1]
    assert last["money"]["earned_usd"] >= 1.71
    assert last["money"]["saved_usd"] >= 3.2
    total = data["total"]
    assert total["earned_usd"] >= last["money"]["earned_usd"]
    assert total["events"] >= last["events"]


def test_day_frames_markers_cover_the_moments():
    data = replay.day_frames(24)
    kinds = {m["kind"] for m in data["markers"]}
    assert "safety" in kinds      # the Sentinel refusal
    assert "forensics" in kinds   # the night reconstruction
    assert "forge" in kinds       # the mounted tool
    for m in data["markers"]:
        assert 0 <= m["frame"] <= 23
        assert m["icon"] and m["label"]


def test_http_replay_day_endpoint(client):
    res = client.get("/api/replay/day?hours=24")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["ok"] is True
    assert len(data["frames"]) == 24
    assert data["markers"]
    assert data["total"]["events"] >= 4
    # window bound: 6..72
    small = client.get("/api/replay/day?hours=2").json()
    assert small["hours"] == 6
    big = client.get("/api/replay/day?hours=999").json()
    assert big["hours"] == 72
