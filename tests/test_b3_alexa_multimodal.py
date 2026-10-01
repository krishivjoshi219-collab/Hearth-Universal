"""B3: voice + Alexa directives + APL multi-modal simulator tests.

Covers: Discovery returns endpoints, PowerController gated correctly,
ThermostatController round-trip + range gating, LockController round-trip
(Lock executes, Unlock is Sentinel-gated), APL template valid JSON,
TTS queue + chime + light-wave hooks, D-pad nav, ReAct visualizer events,
and the no-device voice-turn simulator.
"""
import json
import os
import tempfile

os.environ.setdefault("HEARTH_STATE_DIR", tempfile.mkdtemp())

from hearth import alexa, home_mock


def _directive(ns, name, endpoint_id="", payload=None, token="tok-test"):
    d = {"directive": {"header": {"namespace": ns, "name": name,
                                  "correlationToken": token}, "payload": payload or {}}}
    if endpoint_id:
        d["directive"]["endpoint"] = {"endpointId": endpoint_id}
    return d


def test_discovery_returns_endpoints():
    res = alexa.handle_directive(_directive("Alexa.Discovery", "Discover"))
    eps = res["event"]["payload"]["endpoints"]
    ids = {e["endpointId"] for e in eps}
    assert {"living_room_lights", "master_bedroom_lights", "home_thermostat",
            "front_door_lock", "front_doorbell_cam"} <= ids
    assert res["event"]["header"]["name"] == "Discover.Response"
    # every endpoint has at least one AlexaInterface capability
    for e in eps:
        assert any(c.get("type") == "AlexaInterface" for c in e["capabilities"])


def test_power_controller_gated_correctly():
    # Valid TurnOn round-trip
    res = alexa.handle_directive(_directive("Alexa.PowerController", "TurnOn",
                                            "living_room_lights"))
    assert res["event"]["header"]["name"] == "Response"
    assert home_mock.get_state()["living_room"]["lights"]["on"] is True
    # Valid TurnOff round-trip
    res = alexa.handle_directive(_directive("Alexa.PowerController", "TurnOff",
                                            "living_room_lights"))
    assert res["event"]["header"]["name"] == "Response"
    assert home_mock.get_state()["living_room"]["lights"]["on"] is False
    # Unknown endpoint -> NO_SUCH_ENDPOINT (must not touch real lights)
    res = alexa.handle_directive(_directive("Alexa.PowerController", "TurnOn",
                                            "toaster_oven"))
    assert res["event"]["header"]["name"] == "ErrorResponse"
    assert res["event"]["payload"]["type"] == "NO_SUCH_ENDPOINT"
    # Unknown action -> INVALID_DIRECTIVE
    res = alexa.handle_directive(_directive("Alexa.PowerController", "Blink",
                                            "living_room_lights"))
    assert res["event"]["payload"]["type"] == "INVALID_DIRECTIVE"


def test_thermostat_round_trip_and_range_gating():
    res = alexa.handle_directive(_directive(
        "Alexa.ThermostatController", "SetTargetTemperature", "home_thermostat",
        {"targetSetpoint": {"value": 22.5, "scale": "CELSIUS"}}))
    assert res["event"]["header"]["name"] == "Response"
    assert home_mock.get_state()["living_room"]["climate"]["target_c"] == 22.5
    # Out-of-range rejected, state untouched
    res = alexa.handle_directive(_directive(
        "Alexa.ThermostatController", "SetTargetTemperature", "home_thermostat",
        {"targetSetpoint": {"value": 99.0, "scale": "CELSIUS"}}))
    assert res["event"]["payload"]["type"] == "VALUE_OUT_OF_RANGE"
    assert home_mock.get_state()["living_room"]["climate"]["target_c"] == 22.5
    # Mode round-trip
    res = alexa.handle_directive(_directive(
        "Alexa.ThermostatController", "SetThermostatMode", "home_thermostat",
        {"thermostatMode": {"value": "ECO"}}))
    assert res["event"]["header"]["name"] == "Response"
    # Bad mode rejected
    res = alexa.handle_directive(_directive(
        "Alexa.ThermostatController", "SetThermostatMode", "home_thermostat",
        {"thermostatMode": {"value": "SAUNA"}}))
    assert res["event"]["payload"]["type"] == "INVALID_VALUE"
    # Unknown endpoint gated
    res = alexa.handle_directive(_directive(
        "Alexa.ThermostatController", "SetTargetTemperature", "nope",
        {"targetSetpoint": {"value": 21.0}}))
    assert res["event"]["payload"]["type"] == "NO_SUCH_ENDPOINT"


def test_lock_round_trip_unlock_gated():
    home_mock.toggle_lock(locked=True)
    res = alexa.handle_directive(_directive("Alexa.LockController", "Lock",
                                            "front_door_lock"))
    assert res["event"]["header"]["name"] == "Response"
    assert res["context"]["properties"][0]["value"] == "LOCKED"
    # Unlock must NOT execute: Sentinel Tier-2 gate
    res = alexa.handle_directive(_directive("Alexa.LockController", "Unlock",
                                            "front_door_lock"))
    assert res["event"]["header"]["name"] == "ErrorResponse"
    assert res["event"]["payload"]["type"] == "AUTHORIZATION_REQUIRED"
    assert home_mock.get_state()["entryway"]["lock"]["front_door"] == "locked"
    # Unknown lock endpoint gated
    res = alexa.handle_directive(_directive("Alexa.LockController", "Lock",
                                            "garage_door"))
    assert res["event"]["payload"]["type"] == "NO_SUCH_ENDPOINT"


def test_apl_template_valid_json():
    import pathlib
    p = pathlib.Path(__file__).resolve().parent.parent / "skill" / "apl_smart_canvas.json"
    tpl = json.loads(p.read_text())
    assert tpl["type"] == "APL"
    assert tpl["version"] == "2024.1"
    items = tpl["mainTemplate"]["items"]
    assert len(items) >= 1
    blob = json.dumps(tpl)
    # Back-compat bindings + new multimodal bindings must exist
    for key in ("payload.sentinel_status", "payload.solar_kw", "payload.deadbolt_status",
                "payload.pending_proposals_count", "payload.ttsCaption", "payload.cards",
                "payload.reactSteps", "payload.focusIndex"):
        assert key in blob, f"missing APL binding {key}"
    # D-pad SendEvent hooks
    assert "SendEvent" in blob and "select_card" in blob and "open_approval_tray" in blob


def test_tts_chime_lightwave_hooks():
    alexa.clear_tts_queue()
    alexa.clear_react_events()
    t = alexa.enqueue_tts("Lights updated.")
    assert t["ok"] is True and t["text"] == "Lights updated."
    assert any(e["text"] == "Lights updated." for e in alexa.get_tts_queue())
    chime = alexa.emit_chime("wake")
    assert chime["kind"] == "wake" and "tones" in chime["spec"]
    wave = alexa.emit_light_wave("speaking")
    assert wave["mode"] == "speaking"
    assert alexa.get_light_wave()["mode"] == "speaking"
    phases = {e["phase"] for e in alexa.get_react_events(20)}
    assert {"speak", "chime", "light-wave"} <= phases
    alexa.clear_tts_queue()
    assert alexa.get_tts_queue() == []


def test_dpad_keyboard_single_flow():
    cards = [{"id": "a", "title": "A", "action": "a"},
             {"id": "b", "title": "B", "action": "b"},
             {"id": "c", "title": "C", "action": "c"}]
    r = alexa.handle_dpad_input("Right", focus_index=0, cards=cards)
    assert r["ok"] is True and r["focus_index"] == 1
    r = alexa.handle_dpad_input("Right", focus_index=2, cards=cards)
    assert r["focus_index"] == 0  # wraps
    r = alexa.handle_dpad_input("Select", focus_index=1, cards=cards)
    assert r["selected"]["id"] == "b"
    r = alexa.handle_dpad_input("Diagonal", cards=cards)
    assert r["ok"] is False
    # Multimodal envelope keeps voice + cards + hooks + D-pad hint in ONE flow
    mm = alexa.build_multimodal_response(speak_text="Hello.", cards=cards)
    assert mm["speak_text"] == "Hello."
    assert mm["apl_directive"]["type"] == "Alexa.Presentation.APL.RenderDocument"
    assert len(mm["apl_payload"]["cards"]) == 3
    assert "D-pad" in mm["dpad_hint"] or "arrows" in mm["dpad_hint"].lower()


def test_voice_turn_simulator_no_device():
    alexa.clear_tts_queue()
    out = alexa.simulate_voice_turn("turn on the living room lights")
    assert out["ok"] is True
    assert out["directive_response"]["event"]["header"]["name"] == "Response"
    assert out["multimodal"]["speak_text"]
    assert out["multimodal"]["apl_directive"]["type"].endswith("RenderDocument")
    phases = {e["phase"] for e in out["react"]}
    assert {"thought", "action", "observation", "speak", "show"} <= phases
    # Gated unlock turn stays locked but still returns a speak + APL turn
    home_mock.toggle_lock(locked=True)
    out = alexa.simulate_voice_turn("unlock the front door")
    assert out["directive_response"]["event"]["payload"]["type"] == "AUTHORIZATION_REQUIRED"
    assert home_mock.get_state()["entryway"]["lock"]["front_door"] == "locked"
    assert "approval" in out["multimodal"]["speak_text"].lower()


def test_skill_manifest_keeps_smarthome_handshake():
    import pathlib
    p = pathlib.Path(__file__).resolve().parent.parent / "skill" / "skill.json"
    man = json.loads(p.read_text())["manifest"]
    assert man["apis"]["smartHome"]["protocolVersion"] == "3"
    assert man["manifestVersion"] == "1.0"
    assert man["hearth"]["aplTemplate"] == "skill/apl_smart_canvas.json"
    assert man["hearth"]["simulator"]["noDeviceRequired"] is True
