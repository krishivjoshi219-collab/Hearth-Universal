"""B2: context-aware memory v2 + Family Arbiter + goals tests (zero-config)."""
import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture()
def iso(tmp_path, monkeypatch):
    """Isolated STATE_DIR with freshly reloaded hearth modules."""
    monkeypatch.setenv("HEARTH_STATE_DIR", str(tmp_path))
    import hearth.memory as memory
    import hearth.goals as goals
    import hearth.family as family
    importlib.reload(memory)
    importlib.reload(goals)
    importlib.reload(family)
    assert str(memory.STATE_DIR) == str(tmp_path)
    yield types(memory, goals, family)
    # restore default state dir binding for other test modules
    monkeypatch.delenv("HEARTH_STATE_DIR", raising=False)
    for mod in (memory, goals, family):
        try:
            importlib.reload(mod)
        except Exception:
            pass


class types:
    def __init__(self, memory, goals, family):
        self.memory = memory
        self.goals = goals
        self.family = family


def test_resident_profiles_seeded(iso):
    residents = iso.memory.list_residents()
    profiles = {r["profile"] for r in residents}
    assert {"admin", "partner", "child"} <= profiles
    assert iso.memory.canonical_resident("Leo") == "child"
    assert iso.memory.canonical_resident("Sarah Miller") == "partner"
    assert iso.memory.canonical_resident("Krishiv") == "admin"
    assert iso.memory.canonical_resident("???") == "household"


def test_child_guardrail_blocks_sensitive_remember(iso):
    denied = iso.memory.remember("wifi_password", "hunter2-secret", owner="Leo")
    assert denied.get("ok") is False
    assert "Child safety" in denied.get("error", "")

    # no privilege escalation via owner spoofing
    spoof = iso.memory.remember("bedtime_story", "dragons", owner="Leo")
    # comfort facts are fine for Leo ...
    assert spoof.get("ok") is True
    assert spoof.get("owner") == "child"

    # ... but nothing sensitive landed in storage
    assert not any(f["key"] == "wifi_password" for f in iso.memory.query("", requester="household"))


def test_child_query_filters_sensitive_admin_facts(iso):
    iso.memory.remember("admin_bank_note", "payment card 4111", owner="admin")
    iso.memory.remember("movie_night", "Friday popcorn", owner="household")
    as_admin = {f["key"] for f in iso.memory.query("", requester="admin")}
    as_child = {f["key"] for f in iso.memory.query("", requester="Leo")}
    assert "admin_bank_note" in as_admin
    assert "admin_bank_note" not in as_child
    assert "movie_night" in as_child
    ctx = iso.memory.get_resident_context("Leo")
    assert ctx["child_guardrails"] is True
    assert ctx["resident"] == "child"


def test_pareto_climate_negotiation_and_child_safe_band(iso):
    res = iso.family.negotiate_climate([
        {"name": "Admin", "resident": "admin", "requested_setpoint": 20.0, "weight": 1.2},
        {"name": "Partner", "resident": "partner", "requested_setpoint": 23.0, "weight": 1.0},
        {"name": "Leo", "resident": "child", "requested_setpoint": 26.0, "weight": 5.0},
    ], requester="household")
    assert res["ok"] is True
    sp = res["compromise"]["target_setpoint"]
    assert 19.0 <= sp <= 24.0  # child-safe clamp despite Leo asking 26 with weight 5
    assert res["proposed_action"]["device"] == "thermostat"
    assert res["proposed_action"]["cost_delta"] < 0
    # persisted for context continuity
    assert any(f["key"] == "arbiter_climate_last" for f in iso.memory.query("arbiter"))


def test_peak_tariff_shift_and_child_ev_guardrail(iso):
    ok = iso.family.shift_load("dishwasher", requester="partner",
                               custom_params={"delay_minutes": 75})
    assert ok["ok"] is True
    assert ok["proposed_action"]["device"] == "dishwasher"
    assert ok["proposed_action"]["cost_delta"] < 0

    denied = iso.family.shift_load("ev_charger", requester="Leo")
    assert denied.get("ok") is False
    assert "Child safety" in denied.get("error", "")

    uni = iso.family.resolve("bedtime", requester="Leo",
                             custom_params={"resident": "Leo", "fade_minutes": 15})
    assert uni["ok"] is True
    assert uni["proposed_action"]["duration_minutes"] == 15


def test_goal_flow_scheduler_and_persistence(iso, tmp_path):
    # Drain seeded goals so the hourly hook is deterministic for our goal.
    for g0 in iso.goals.list_goals("active"):
        for _ in range(len(g0["steps"]) + 1):
            iso.goals.advance_goal(g0["id"])
    assert iso.goals.list_goals("active") == []

    g = iso.goals.create_goal("B2 demo goal", ["step one", "step two", "step three"],
                              owner="partner", priority="high", deadline="Sunday")
    assert g["ok"] is True and g["owner"] == "partner"
    gid = g["id"]

    a1 = iso.goals.advance_goal(gid)
    assert a1["ok"] is True and a1["progress"] == 1 and a1["status"] == "active"

    # hourly hook is rate-limited right after a manual advance ...
    tick_fast = iso.goals.scheduler_tick()
    assert tick_fast["advanced"] is False

    # ... but advances once an hour has elapsed (simulated clock).
    import time as _t
    tick_due = iso.goals.scheduler_tick(now=_t.time() + 7200)
    assert tick_due["advanced"] is True
    assert tick_due["progress"] == 2

    # persistence across "restart": same STATE_DIR, fresh connections see data.
    iso.memory.remember("restart_probe", "survives-reload", owner="household")
    import hearth.memory as fresh
    importlib.reload(fresh)
    assert any(f["key"] == "restart_probe" for f in fresh.query())
    goals_seen = [x for x in fresh.list_goals() if x["id"] == gid]
    assert goals_seen and goals_seen[0]["progress"] == 2

    # legacy MCP call shapes still work (extend, don't break).
    legacy = iso.memory.create_goal("legacy title", ["a", "b"])
    assert legacy["ok"] is True
    assert iso.memory.advance_goal(legacy["id"])["ok"] is True
    assert iso.memory.remember("k", "v")["ok"] is True
    assert isinstance(iso.memory.query("k"), list)
