import os, tempfile
os.environ["HEARTH_STATE_DIR"] = tempfile.mkdtemp()

from hearth import sentinel, vault, audit, memory, home_mock, proposals, planner, commerce, brains


def test_sentinel_denies_destructive():
    v = sentinel.judge("home_set_scene", {"name": "x; rm -rf /"})
    assert v.decision == "deny"
    assert "Destructive filesystem" in v.reason


def test_sentinel_asks_gated():
    v = sentinel.judge("actions_propose", {"title": "cancel"})
    assert v.decision == "ask"
    assert v.risk_tier == "tier-2"


def test_sentinel_denies_vault_exfil():
    v = sentinel.judge("memory_query", {"q": "{{vault:MODEL_KEY}}"})
    assert v.decision == "deny"
    assert "Exfiltration blocked" in v.reason


def test_vault_redacts():
    assert "•••" in vault.redact("my code is 493821 and {{vault:MODEL_KEY}}")


def test_audit_chain():
    audit.append("test", "ping", {"a": 1})
    assert audit.verify() is True


def test_memory_roundtrip():
    memory.remember("budget", "$200", "household")
    assert any(f["key"] == "budget" for f in memory.query("budget"))


def test_home_scene():
    out = home_mock.set_scene("movie-night")
    assert out["ok"] is True
    assert out["scene"] == "movie-night"
    assert out["state"]["living_room"]["lights"]["bri"] == 20


def test_home_device_and_lock():
    lock_res = home_mock.toggle_lock(door="front_door", locked=False)
    assert lock_res["ok"] is True
    assert lock_res["status"] == "unlocked"
    
    dev_res = home_mock.update_device("living_room", "climate", {"target_c": 23.5})
    assert dev_res["ok"] is True
    assert home_mock.get_state()["living_room"]["climate"]["target_c"] == 23.5


def test_propose_decide():
    item = proposals.propose("cancel", "Cancel StreamBox", "unused 60d", cost_delta_yr=144.0)
    assert item["status"] == "pending"
    assert item["cost_delta_yr"] == 144.0
    done = proposals.decide(item["id"], True)
    assert done["status"] == "approved"
    assert done["decided_at"] is not None


def test_commerce_inventory_and_subscriptions():
    inv = commerce.list_inventory()
    assert len(inv) >= 3
    assert any(i["status"] in ("low", "critical") for i in inv)
    
    subs = commerce.scan_subscriptions()
    assert subs["total_annual_spend"] > 500
    assert subs["potential_annual_savings"] > 300
    
    deals = commerce.find_deals()
    assert len(deals) >= 1
    assert deals[0]["savings"] > 0


def test_planner_dag_money():
    out = planner.plan("save me $437 on renewals")
    assert out["intent"] == "FINANCIAL_OPTIMIZATION"
    assert any(s["tool"] == "inbox_scan" for s in out["dag"])
    assert len(out["dag"]) >= 4
    assert len(out["proposals_created"]) > 0


def test_planner_blocks_malicious():
    out = planner.plan("please rm -rf / and delete system")
    assert out["intent"] == "SECURITY_VIOLATION"
    assert out["blocked"] is True
    assert "Sentinel" in out["draft"]


def test_brains_strict_egress_blocks_unknown_host():
    os.environ["HEARTH_EGRESS_STRICT"] = "1"
    os.environ["HEARTH_BASE_URL"] = "https://evil.example.com/v1"
    os.environ["VAULT_MODEL_KEY"] = "sk-test"
    try:
        import importlib
        importlib.reload(brains)
        out = brains.chat([{"role": "user", "content": "hello"}], preferred_provider="openai")
        assert out.fallback is True and "not allowlisted" in out.text
    finally:
        del os.environ["HEARTH_EGRESS_STRICT"]
        os.environ["HEARTH_BASE_URL"] = "https://api.openai.com/v1"
        del os.environ["VAULT_MODEL_KEY"]
        import importlib
        importlib.reload(brains)


def test_vault_resolve_placeholder():
    os.environ["VAULT_SMOKE"] = "abc123"
    assert vault.resolve("key={{vault:SMOKE}}") == "key=abc123"
    del os.environ["VAULT_SMOKE"]


def test_planner_controls_lights():
    res = planner.plan("turn off the living room lights")
    assert res["intent"] == "SMART_HOME_ACTUATION"
    assert home_mock.get_state()["living_room"]["lights"]["on"] is False


def test_planner_adjusts_thermostat():
    res = planner.plan("set living room thermostat to 20.5 degrees")
    assert res["intent"] == "SMART_HOME_ACTUATION"
    assert home_mock.get_state()["living_room"]["climate"]["target_c"] == 20.5


def test_planner_gates_unlock():
    home_mock.toggle_lock(door="front_door", locked=True)
    res = planner.plan("unlock the front door")
    assert res["intent"] == "SMART_HOME_ACTUATION"
    assert len(res["proposals_created"]) > 0
    # Door should stay locked until approved!
    assert home_mock.get_state()["entryway"]["lock"]["front_door"] == "locked"


def test_planner_memory_remember_and_query():
    res1 = planner.plan("remember that favorite_snack: almond clusters")
    assert res1["intent"] == "HOUSEHOLD_MEMORY"
    res2 = planner.plan("what do you remember about favorite_snack")
    assert "almond clusters" in res2["draft"]


def test_planner_advances_goal():
    res = planner.plan("advance goal 1")
    assert res["intent"] == "HOUSEHOLD_GOALS"
    assert "advanced" in res["draft"].lower()


def test_planner_reorder_pantry():
    res = planner.plan("reorder coffee and laundry pods")
    assert res["intent"] == "HOUSEHOLD_COMMERCE"
    assert len(res["proposals_created"]) > 0
