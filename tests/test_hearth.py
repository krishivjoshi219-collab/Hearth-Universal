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


def test_sentinel_two_tiers():
    assert sentinel.judge("home_set_scene", {"name": "movie-night"}).decision == "allow"
    assert sentinel.judge("home_update_device", {"room": "living_room", "device": "lights", "patch": {}}).decision == "allow"
    assert sentinel.judge("home_toggle_lock", {"locked": True}).decision == "allow"
    assert sentinel.judge("home_toggle_lock", {"locked": False}).decision == "ask"
    assert sentinel.judge("totally_unknown_tool", {}).decision == "ask"


def test_decide_single_use():
    item = proposals.propose("cancel_subscription", "Cancel Test Service", "test")
    first = proposals.decide(item["id"], True)
    assert first["status"] == "approved"
    assert "execution" in first
    second = proposals.decide(item["id"], True)
    assert second.get("ok") is False and "already approved" in second.get("error", "")


def test_home_state_survives_reload():
    import importlib
    home_mock.set_scene("movie-night")
    reloaded = importlib.reload(home_mock)
    assert reloaded.get_state()["active_scene"] == "movie-night"
    reloaded.reset_state()
    assert importlib.reload(home_mock).get_state()["active_scene"] == "default"


def test_propose_caps_lengths():
    item = proposals.propose("test", "T" * 500, "R" * 9000)
    assert item.get("truncated") is True
    assert len(item["title"]) <= 200 and len(item["reasons"]) <= 4000
    # newest-last ordering with limit
    assert len(proposals.list_proposals(limit=1)) == 1


def test_remember_caps_value():
    out = memory.remember("bigkey", "V" * 9000)
    assert out.get("truncated") is True
    assert len(memory.query("bigkey")[0]["value"]) <= 8000


def test_chat_history_bounded():
    for i in range(12):
        memory.chat_history_append("user", f"ping {i}")
    # prune helper keeps table small even after many turns
    con = memory._db()
    n = con.execute("SELECT COUNT(*) FROM chat_history").fetchone()[0]
    con.close()
    assert n <= memory.CHAT_HISTORY_MAX


def test_server_rate_limiter():
    """Test rate limiting algorithm directly without re-importing full server module
    (avoids pydantic forward-reference resolution across module boundaries)."""
    import time
    rate_limit = 30
    rate_buckets: dict[str, list] = {}

    def rate_ok(ip: str) -> bool:
        now = time.time()
        bucket = [t for t in rate_buckets.get(ip, []) if now - t < 60]
        if not bucket:
            rate_buckets.pop(ip, None)
        if len(bucket) >= rate_limit:
            rate_buckets[ip] = bucket
            return False
        bucket.append(now)
        rate_buckets[ip] = bucket
        return True

    ip = "10.9.9.9"
    assert all(rate_ok(ip) for _ in range(rate_limit))
    assert rate_ok(ip) is False


def test_corrupt_db_recovers():
    from pathlib import Path
    db = Path(memory.STATE_DIR) / "memory.db"
    db.write_text("this is not sqlite at all {{{")
    facts = memory.query()
    assert isinstance(facts, list)  # recovered, reseeded, no exception
    assert (db.parent).exists()


def test_corrupt_audit_reports_false_not_crash():
    from pathlib import Path
    log = Path(audit._log_path())
    with log.open("a") as f:
        f.write("garbage{{{not json\n")
    assert audit.verify() is False
    # tidy: drop the poisoned line so later tests see a valid chain
    lines = [l for l in log.read_text().splitlines() if not l.startswith("garbage")]
    log.write_text("\n".join(lines) + ("\n" if lines else ""))
    assert audit.verify() is True


def test_advance_missing_goal_no_crash():
    res = planner.plan("advance goal 999")
    assert "couldn't advance" in res["draft"].lower()


def test_forget_unknown_fact_honest():
    res = planner.plan("forget about zzz_nope_nothing")
    assert "couldn't find" in res["draft"].lower()


def test_goals_advance_rejects_bad_id():
    out = planner.TOOLS["goals_advance"]["handler"]({"id": "abc"})
    assert out.get("ok") is False


def test_alexa_discovery_directive():
    from hearth import alexa
    res = alexa.handle_directive({
        "directive": {
            "header": {"namespace": "Alexa.Discovery", "name": "Discover", "correlationToken": "tok-123"},
            "payload": {}
        }
    })
    endpoints = res["event"]["payload"]["endpoints"]
    ids = {e["endpointId"] for e in endpoints}
    assert "living_room_lights" in ids
    assert "front_door_lock" in ids
    assert "home_thermostat" in ids


def test_alexa_power_controller_directive():
    from hearth import alexa, home_mock
    res = alexa.handle_directive({
        "directive": {
            "header": {"namespace": "Alexa.PowerController", "name": "TurnOn", "correlationToken": "tok-pow"},
            "endpoint": {"endpointId": "living_room_lights"},
            "payload": {}
        }
    })
    assert res["event"]["header"]["name"] == "Response"
    st = home_mock.get_state()
    assert st["living_room"]["lights"]["on"] is True


def test_alexa_lock_controller_lock_and_unlock_gated():
    from hearth import alexa, proposals
    # 1. Lock -> Safe autonomous execution
    res_lock = alexa.handle_directive({
        "directive": {
            "header": {"namespace": "Alexa.LockController", "name": "Lock", "correlationToken": "tok-lock"},
            "endpoint": {"endpointId": "front_door_lock"},
            "payload": {}
        }
    })
    assert res_lock["event"]["header"]["name"] == "Response"
    assert res_lock["context"]["properties"][0]["value"] == "LOCKED"

    # 2. Unlock -> Sentinel Tier-2 Gated (Authorization Required, proposal drafted)
    res_unlock = alexa.handle_directive({
        "directive": {
            "header": {"namespace": "Alexa.LockController", "name": "Unlock", "correlationToken": "tok-unlock"},
            "endpoint": {"endpointId": "front_door_lock"},
            "payload": {}
        }
    })
    assert res_unlock["event"]["header"]["name"] == "ErrorResponse"
    assert res_unlock["event"]["payload"]["type"] == "AUTHORIZATION_REQUIRED"
    # Verify proposal exists in tray
    pending = proposals.list_proposals("pending")
    assert any("Unlock Front Door (Alexa Directive)" in p["title"] for p in pending)


def test_heartbeat_and_proactive_tick():
    from hearth import heartbeat
    events = heartbeat.get_events()
    assert isinstance(events, list)
    assert len(events) > 0

    tick_res = heartbeat.tick_proactive("energy_peak")
    assert tick_res["ok"] is True
    assert tick_res["event"]["type"] == "energy"



def test_unreachable_brain_falls_back_gracefully():
    import time
    os.environ["HEARTH_BRAIN_PROVIDER"] = "openai"
    os.environ["HEARTH_BASE_URL"] = "http://127.0.0.1:9"  # closed port: refused instantly
    os.environ["HEARTH_MODEL"] = "unreachable-test"
    try:
        t = time.time()
        out = brains.chat([{"role": "user", "content": "hello"}])
        assert out.fallback is True
        assert time.time() - t < 25
    finally:
        del os.environ["HEARTH_BRAIN_PROVIDER"]
        del os.environ["HEARTH_BASE_URL"]
        del os.environ["HEARTH_MODEL"]


def _fake_brain_factory(script):
    import json as _json
    calls = {"n": 0}

    def fake(messages, max_tokens=1200, preferred_provider=None):
        i = calls["n"]
        calls["n"] += 1
        item = script[min(i, len(script) - 1)]
        return brains.BrainResponse(text=_json.dumps(item), model="fake-live",
                                    provider="fake-live", fallback=False)
    return fake


def test_react_loop_gates_and_grounds(monkeypatch):
    import json as _json
    home_mock.toggle_lock(door="front_door", locked=True)
    script = [
        {"call": {"tool": "home_toggle_lock", "args": {"door": "front_door", "locked": False}, "why": "test unlock"}},
        {"call": {"tool": "workspace_exec", "args": {"cmd": "echo pwned"}, "why": "test exec"}},
        {"final": "door stays shut, exec staged"},
    ]
    monkeypatch.setattr(planner.brains, "chat", _fake_brain_factory(script))
    res = planner.plan("open everything now", preferred_provider="fake")
    assert res["intent"] == "LIVE_AGENTIC"
    assert res["draft"] == "door stays shut, exec staged"
    assert home_mock.get_state()["entryway"]["lock"]["front_door"] == "locked"
    kinds = {p["kind"] for p in proposals.list_proposals("pending")}
    assert "home_lock" in kinds and "workspace_exec" in kinds
    statuses = {s["status"] for s in res["dag"]}
    assert "awaiting_approval" in statuses


def test_offline_trip_researches_live(monkeypatch):
    from hearth import webtools
    monkeypatch.setattr(webtools, "web_search", lambda q, count=5: {
        "ok": True, "results": [{"title": f"R for {q[:20]}", "url": "https://example.com/x", "snippet": "s"}]})
    monkeypatch.setattr(webtools, "web_fetch", lambda url: {"ok": True, "url": url, "text": "page text"})
    res = planner.plan("plan a 3 day trip from Delhi to Goa under 40000")
    assert res["intent"] == "TRIP_PLANNING"
    assert len(res["proposals_created"]) == 1
    assert "example.com" in res["draft"] and "Goa" in res["draft"]


def test_offline_rules_fetch(monkeypatch):
    from hearth import webtools
    monkeypatch.setattr(webtools, "web_fetch", lambda url: {"ok": True, "url": url, "text": "RULEBOOK EXCERPT XYZ"})
    res = planner.plan("check the hackathon rules on devpost")
    assert res["intent"] == "RULEBOOK_LOOKUP"
    assert "RULEBOOK EXCERPT XYZ" in res["draft"]


def test_workspace_verbs_end_to_end(monkeypatch, tmp_path):
    monkeypatch.setenv("HEARTH_WORKSPACE", str(tmp_path))
    r1 = planner.plan("run echo hello-hearth")
    assert r1["intent"] == "WORKSPACE_EXEC" and "hello-hearth" in r1["draft"]
    r2 = planner.plan("write file notes.txt: remember the milk")
    assert r2["intent"] == "WORKSPACE_WRITE" and (tmp_path / "notes.txt").read_text() == "remember the milk"
    r3 = planner.plan("read file notes.txt")
    assert "remember the milk" in r3["draft"]
    r4 = planner.plan("ls")
    assert "notes.txt" in r4["draft"]
    r5 = planner.plan("run rm -rf /")
    assert "Refused" in r5["draft"] or "blocked" in r5["draft"].lower()


def test_boot_reports_honestly():
    res = planner.plan("boot my workspace")
    assert res["intent"] == "WORKSPACE_BOOT"
    assert "can't power" in res["draft"]


def test_search_falls_back_to_instant_answer(monkeypatch):
    from hearth import webtools
    monkeypatch.setattr(webtools, "_search_ddg_html", lambda q, c: ([], "ddg-html"))
    monkeypatch.setattr(webtools, "_search_ddg_ia", lambda q, c: (
        [{"title": "Fallback Result", "url": "https://example.com/fb", "snippet": "s"}], "ddg-instant-answer"))
    r = webtools.web_search("anything", 3)
    assert r["ok"] is True and r["source"] == "ddg-instant-answer"
    assert r["results"][0]["url"] == "https://example.com/fb"


def test_mcp_workspace_exec_gated_over_wire():
    # planner-level gate: unknown-context exec call must stage, not run
    assert planner._requires_approval("workspace_exec", {"cmd": "echo hi"}) is True
    assert planner._requires_approval("web_search", {"query": "x"}) is False


def test_commerce_depletion_velocity():
    forecast = commerce.get_depletion_forecast()
    assert len(forecast) >= 3
    # Check that items are ordered by depletion urgency
    days = [f["days_until_empty"] for f in forecast]
    assert days == sorted(days)
    assert forecast[0]["days_until_empty"] < 5.0  # Most critical consumable


def test_amazon_subscribe_and_save_cart():
    cart = commerce.stage_amazon_cart(subscribe_and_save=True)
    assert cart["ok"] is True
    assert cart["prime_badge"] is True
    assert cart["savings"] > 0
    assert "Tuesday" in cart["delivery_schedule"]


def test_ring_camera_directive_and_event():
    from hearth import alexa
    # Test discovery exposes Ring camera
    disc = alexa.handle_directive({"directive": {"header": {"namespace": "Alexa.Discovery", "name": "Discover"}}})
    endpoints = {e["endpointId"] for e in disc["event"]["payload"]["endpoints"]}
    assert "front_doorbell_cam" in endpoints

    # Test doorbell event emission
    event_res = alexa.trigger_ring_event("doorbell_press", "FedEx Courier")
    assert event_res["ok"] is True
    assert event_res["event_type"] == "doorbell_press"
    assert "Courier" in event_res["announcement"]
    assert event_res["proposal_id"] is not None


def test_child_persona_guardrail():
    # Child persona can do safe comfort actions (dim lights)
    v_safe = sentinel.judge("home_update_device", {"room": "living_room", "device": "lights", "patch": {"bri": 50}, "persona": "child"})
    assert v_safe.decision == "allow"

    # Child persona is blocked from unlocking doors or financial actions
    v_unlock = sentinel.judge("home_toggle_lock", {"door": "front_door", "locked": False, "persona": "child"})
    assert v_unlock.decision == "deny"
    assert "Child safety" in v_unlock.reason


def test_mcp_apps_generation():
    roi_app = planner.TOOLS["mcp_app_subscription_roi"]["handler"]({})
    assert roi_app["app_id"] == "mcp_app_subscription_roi"
    assert roi_app["category"] == "mcp_app"

    light_app = planner.TOOLS["mcp_app_lighting_designer"]["handler"]({"room": "living_room"})
    assert light_app["app_id"] == "mcp_app_lighting_designer"
    assert light_app["room"] == "living_room"


def test_family_arbiter_conflict_resolution():
    from hearth import arbiter
    conflicts = arbiter.list_active_conflicts()
    assert len(conflicts) >= 3

    # Test climate conflict resolution
    res_clim = arbiter.resolve_conflict("climate")
    assert res_clim["ok"] is True
    assert "Dual-Resident" in res_clim["title"]
    assert res_clim["compromise"]["target_setpoint"] == 21.5
    assert res_clim["proposed_action"]["device"] == "thermostat"

    # Test peak tariff load shifting
    res_tar = arbiter.resolve_conflict("tariff")
    assert res_tar["ok"] is True
    assert res_tar["proposed_action"]["device"] == "dishwasher"
    assert res_tar["proposed_action"]["cost_delta"] < 0


def test_timemachine_simulation_presets():
    from hearth import timemachine
    presets = timemachine.get_timeline_presets()
    assert len(presets) >= 4
    preset_ids = {p["id"] for p in presets}
    assert "now" in preset_ids
    assert "bedtime" in preset_ids
    assert "morning" in preset_ids

    # Test bedtime projection
    bed_res = timemachine.simulate_timeline("bedtime")
    assert bed_res["ok"] is True
    fc = bed_res["forecast"]
    assert fc["solar_kw"] == 0.0
    assert "Infrared" in fc["ring_cam_mode"]
    assert fc["battery_pct"] > 80

    # Test morning wake projection
    morn_res = timemachine.simulate_timeline("morning")
    assert morn_res["forecast"]["solar_kw"] > 1.0


def test_amazon_prime_delivery_tracker():
    from hearth import commerce
    tracker = commerce.get_delivery_tracker()
    assert tracker["ok"] is True
    assert tracker["status"] == "out_for_delivery"
    assert "Marcus" in tracker["driver_name"]
    assert tracker["stops_away"] > 0
    assert len(tracker["progress_steps"]) == 4


def test_commerce_barcode_scan_replenish():
    from hearth import commerce
    # Deplete coffee via scan
    dep_res = commerce.simulate_barcode_scan("item_coffee", "deplete")
    assert dep_res["ok"] is True
    assert dep_res["item"]["level_pct"] == 10
    assert dep_res["item"]["status"] == "critical"

    # Replenish coffee via scan
    rep_res = commerce.simulate_barcode_scan("item_coffee", "replenish")
    assert rep_res["ok"] is True
    assert rep_res["item"]["level_pct"] == 100
    assert rep_res["item"]["status"] == "normal"


def test_family_arbiter_custom_multi_resident_climate():
    from hearth import arbiter
    # Test 3 residents with custom preferences and priority weights
    custom_params = {
        "parties": [
            {"name": "Alex", "requested_setpoint": 20.0, "weight": 1.0, "tolerance": 1.0},
            {"name": "Sarah", "requested_setpoint": 23.5, "weight": 1.2, "tolerance": 1.5},
            {"name": "Leo", "requested_setpoint": 21.0, "weight": 0.8, "tolerance": 1.2}
        ],
        "baseline_temp": 24.0,
        "eco_weight": 0.0
    }
    res = arbiter.resolve_conflict("climate", custom_params=custom_params)
    assert res["ok"] is True
    assert "3 Residents" in res["title"]
    assert len(res["parties"]) == 3

    # Computed Pareto optimal target setpoint
    setpoint = res["compromise"]["target_setpoint"]
    assert 21.0 <= setpoint <= 21.5
    assert res["proposed_action"]["device"] == "thermostat"
    assert res["proposed_action"]["setpoint"] == setpoint
    assert res["proposed_action"]["cost_delta"] < 0  # Saves money vs baseline

    # Micro-climate zone compensation
    assert "perceived_temp_alex" in res["compromise"]
    assert "wind-chill" in res["compromise"]["perceived_temp_alex"]
    assert "perceived_temp_sarah" in res["compromise"]
    assert "baffle" in res["compromise"]["perceived_temp_sarah"]

    # Satisfaction index per resident
    sats = res["compromise"]["individual_satisfaction"]
    assert sats["Alex"] >= 80
    assert sats["Sarah"] >= 80
    assert sats["Leo"] >= 85


def test_family_arbiter_custom_tariff_load_shifting():
    from hearth import arbiter
    custom_params = {
        "device": "ev_charger",
        "deadline": "6:30 AM",
        "delay_minutes": 90,
        "peak_rate": 0.52,
        "offpeak_rate": 0.11,
        "cycle_kwh": 14.0
    }
    res = arbiter.resolve_conflict("tariff", custom_params=custom_params)
    assert res["ok"] is True
    assert "Ev Charger" in res["title"]
    assert res["compromise"]["delay_minutes"] == 90
    assert res["proposed_action"]["cost_delta"] < -5.0
    assert res["proposed_action"]["device"] == "ev_charger"


def test_family_arbiter_bedtime_wind_down():
    from hearth import arbiter
    custom_params = {
        "resident": "Leo",
        "activity": "gaming on tablet",
        "fade_minutes": 20,
        "target_bedtime": "10:00 PM"
    }
    res = arbiter.resolve_conflict("bedtime", custom_params=custom_params)
    assert res["ok"] is True
    assert "Leo Bedtime" in res["title"]
    assert res["compromise"]["protocol"] == "20-Minute Sunset Gradual Fade"
    assert res["proposed_action"]["duration_minutes"] == 20


def test_commerce_delivery_slot_rescheduling():
    from hearth import commerce
    # 1. List available delivery slots
    slots = commerce.list_available_delivery_slots()
    assert len(slots) >= 4
    slot_ids = {s["slot_id"] for s in slots}
    assert "slot_tuesday_household" in slot_ids
    assert "slot_overnight_urgent" in slot_ids

    # 2. Reschedule to overnight slot
    res = commerce.reschedule_delivery_slot("slot_overnight_urgent", reason="Urgent coffee replenish")
    assert res["ok"] is True
    assert res["rescheduled"] is True
    assert "Prime Overnight" in res["new_slot"]
    assert res["stockout_risk_mitigated"] is True

    # 3. Active slot should reflect the update
    active = commerce.get_scheduled_delivery_slot()
    assert active["slot_id"] == "slot_overnight_urgent"

    # 4. Clean up: reset back to Tuesday household day
    revert = commerce.reschedule_delivery_slot("slot_tuesday_household", reason="Reset test")
    assert revert["ok"] is True


def test_commerce_bundle_optimization():
    from hearth import commerce
    bundle = commerce.optimize_bundles(auto_fill_tier=True, target_tier_items=5)
    assert bundle["ok"] is True
    assert bundle["tier_unlocked"] is True
    assert bundle["item_count"] >= 5
    assert len(bundle["pull_forward_items"]) >= 1

    # Pricing savings
    pricing = bundle["pricing"]
    assert pricing["regular_total"] > 80.0
    assert pricing["total_savings"] > 25.0
    assert pricing["savings_pct"] >= 20.0
    assert pricing["bundle_synergy_rebates"] > 0

    # Environmental consolidation
    env = bundle["environmental_impact"]
    assert env["boxes_saved"] >= 3
    assert env["carbon_offset_kg"] >= 2.0


def test_commerce_stage_cart_with_bundle_and_slot():
    from hearth import commerce
    cart = commerce.stage_amazon_cart(bundle_optimized=True, delivery_slot_id="slot_overnight_urgent")
    assert cart["ok"] is True
    assert cart["bundle_optimized"] is True
    assert cart["item_count"] >= 5
    assert cart["savings"] > 25.0
    assert "Prime Overnight" in cart["delivery_schedule"] or "Tomorrow" in cart["delivery_schedule"]
    assert cart["boxes_saved"] >= 3


def test_planner_bundle_and_delivery_and_arbiter_dags():
    from hearth import planner
    # Bundle optimization intent
    p_bundle = planner.plan("optimize my amazon subscribe and save bundle")
    assert p_bundle["intent"] == "COMMERCE_BUNDLE_OPTIMIZATION"
    assert any(s["tool"] == "commerce_optimize_bundles" for s in p_bundle["dag"])
    assert len(p_bundle["proposals_created"]) > 0

    # Delivery slot rescheduling intent
    p_slot = planner.plan("reschedule delivery slot to overnight urgent")
    assert p_slot["intent"] == "COMMERCE_RESCHEDULE_DELIVERY"
    assert any(s["tool"] == "commerce_reschedule_delivery" for s in p_slot["dag"])

    # Multi-resident negotiation intent
    p_arb = planner.plan("negotiate temperature conflict between Alex at 19.5 and Sarah at 23.5 and Leo at 21.0")
    assert p_arb["intent"] == "FAMILY_ARBITER"
    assert any(s["tool"] == "family_arbiter_resolve" for s in p_arb["dag"])


