"""Amazon Alexa Smart Home Skills API v3 Directive Adapter.
Provides native compliance with the Alexa Smart Home API:
- Alexa.Discovery (Discover appliances, endpoints, and capabilities)
- Alexa (ReportState for device state queries)
- Alexa.PowerController (TurnOn, TurnOff for lighting & appliances)
- Alexa.BrightnessController (SetBrightness, AdjustBrightness)
- Alexa.ThermostatController (SetTargetTemperature, AdjustTargetTemperature, SetThermostatMode)
- Alexa.LockController (Lock [Tier-1], Unlock [Tier-2 Sentinel Gated])
- Alexa.CameraStreamController (InitializeCameraStreams for RTSP/HLS live feeds)
- Alexa.DoorbellEventSource & Alexa.MotionSensor (DoorbellPress and Motion event notifications)

Enables zero-friction integration with Alexa Voice Service (AVS) and Alexa Skills Kit (ASK).
"""
from __future__ import annotations
import time
import uuid
from typing import Any

from . import home_mock, proposals, audit


def _make_header(namespace: str, name: str, correlation_token: str = "") -> dict[str, Any]:
    header = {
        "namespace": namespace,
        "name": name,
        "payloadVersion": "3",
        "messageId": str(uuid.uuid4())
    }
    header["correlationToken"] = correlation_token
    return header


def handle_directive(directive_payload: dict[str, Any]) -> dict[str, Any]:
    """Parse and dispatch an incoming Alexa Smart Home v3 directive."""
    directive = directive_payload.get("directive", directive_payload)
    header = directive.get("header", {})
    endpoint = directive.get("endpoint", {})
    payload = directive.get("payload", {})

    namespace = header.get("namespace", "")
    name = header.get("name", "")
    correlation_token = header.get("correlationToken", "")
    endpoint_id = endpoint.get("endpointId", "")

    # 1. Alexa.Discovery
    if namespace == "Alexa.Discovery" and name == "Discover":
        return _handle_discovery(correlation_token)

    # 2. Alexa (State query: ReportState)
    if namespace == "Alexa" and name == "ReportState":
        return _handle_report_state(endpoint_id, correlation_token)

    # 3. Alexa.PowerController (TurnOn / TurnOff)
    if namespace == "Alexa.PowerController":
        return _handle_power_controller(name, endpoint_id, correlation_token)

    # 4. Alexa.BrightnessController (SetBrightness / AdjustBrightness)
    if namespace == "Alexa.BrightnessController":
        return _handle_brightness_controller(name, endpoint_id, payload, correlation_token)

    # 5. Alexa.ThermostatController (SetTargetTemperature / AdjustTargetTemperature / SetThermostatMode)
    if namespace == "Alexa.ThermostatController":
        return _handle_thermostat_controller(name, endpoint_id, payload, correlation_token)

    # 6. Alexa.LockController (Lock / Unlock)
    if namespace == "Alexa.LockController":
        return _handle_lock_controller(name, endpoint_id, correlation_token)

    # 7. Alexa.CameraStreamController (InitializeCameraStreams)
    if namespace == "Alexa.CameraStreamController":
        return _handle_camera_stream_controller(name, endpoint_id, payload, correlation_token)

    # Default fallback / Unsupported
    return {
        "event": {
            "header": _make_header("Alexa", "ErrorResponse", correlation_token),
            "endpoint": {"endpointId": endpoint_id},
            "payload": {
                "type": "INVALID_DIRECTIVE",
                "message": f"Unsupported directive: {namespace}.{name}"
            }
        }
    }


def _get_endpoint_properties(endpoint_id: str) -> list[dict[str, Any]]:
    """Retrieve current state properties for an endpoint formatted for Alexa v3 context."""
    st = home_mock.get_state()
    sample_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    props = []

    if endpoint_id in ("living_room_lights", "master_bedroom_lights"):
        room = "master_bedroom" if "bedroom" in endpoint_id else "living_room"
        lights = st.get(room, {}).get("lights", {})
        props.append({
            "namespace": "Alexa.PowerController",
            "name": "powerState",
            "value": "ON" if lights.get("on") else "OFF",
            "timeOfSample": sample_time,
            "uncertaintyInMilliseconds": 50
        })
        props.append({
            "namespace": "Alexa.BrightnessController",
            "name": "brightness",
            "value": int(lights.get("bri", 0)),
            "timeOfSample": sample_time,
            "uncertaintyInMilliseconds": 50
        })
    elif endpoint_id == "home_thermostat":
        climate = st.get("living_room", {}).get("climate", {})
        props.append({
            "namespace": "Alexa.ThermostatController",
            "name": "targetSetpoint",
            "value": {"value": float(climate.get("target_c", 21.5)), "scale": "CELSIUS"},
            "timeOfSample": sample_time,
            "uncertaintyInMilliseconds": 50
        })
        props.append({
            "namespace": "Alexa.ThermostatController",
            "name": "thermostatMode",
            "value": str(climate.get("mode", "auto")).upper(),
            "timeOfSample": sample_time,
            "uncertaintyInMilliseconds": 50
        })
        props.append({
            "namespace": "Alexa.TemperatureSensor",
            "name": "temperature",
            "value": {"value": float(climate.get("current_c", 22.0)), "scale": "CELSIUS"},
            "timeOfSample": sample_time,
            "uncertaintyInMilliseconds": 50
        })
    elif endpoint_id == "front_door_lock":
        lock_info = st.get("entryway", {}).get("lock", {})
        is_locked = lock_info.get("front_door") == "locked"
        props.append({
            "namespace": "Alexa.LockController",
            "name": "lockState",
            "value": "LOCKED" if is_locked else "UNLOCKED",
            "timeOfSample": sample_time,
            "uncertaintyInMilliseconds": 50
        })
    elif endpoint_id == "front_doorbell_cam":
        props.append({
            "namespace": "Alexa.MotionSensor",
            "name": "detectionState",
            "value": "NOT_DETECTED",
            "timeOfSample": sample_time,
            "uncertaintyInMilliseconds": 50
        })

    return props


def _handle_discovery(correlation_token: str) -> dict[str, Any]:
    """Return discovered smart home endpoints formatted for Alexa Smart Home v3."""
    endpoints = [
        {
            "endpointId": "living_room_lights",
            "manufacturerName": "Hearth Universal",
            "friendlyName": "Living Room Ceiling Lights",
            "description": "Ambient warm dimmable illumination",
            "displayCategories": ["LIGHT"],
            "cookie": {},
            "capabilities": [
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa",
                    "version": "3"
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.PowerController",
                    "version": "3",
                    "properties": {
                        "supported": [{"name": "powerState"}],
                        "proactivelyReported": True,
                        "retrievable": True
                    }
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.BrightnessController",
                    "version": "3",
                    "properties": {
                        "supported": [{"name": "brightness"}],
                        "proactivelyReported": True,
                        "retrievable": True
                    }
                }
            ]
        },
        {
            "endpointId": "master_bedroom_lights",
            "manufacturerName": "Hearth Universal",
            "friendlyName": "Master Bedroom Lights",
            "description": "Recessed bedroom lighting",
            "displayCategories": ["LIGHT"],
            "cookie": {},
            "capabilities": [
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa",
                    "version": "3"
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.PowerController",
                    "version": "3",
                    "properties": {
                        "supported": [{"name": "powerState"}],
                        "proactivelyReported": True,
                        "retrievable": True
                    }
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.BrightnessController",
                    "version": "3",
                    "properties": {
                        "supported": [{"name": "brightness"}],
                        "proactivelyReported": True,
                        "retrievable": True
                    }
                }
            ]
        },
        {
            "endpointId": "home_thermostat",
            "manufacturerName": "Hearth Universal",
            "friendlyName": "Smart HVAC Climate Thermostat",
            "description": "Multi-zone smart home thermostat",
            "displayCategories": ["THERMOSTAT"],
            "cookie": {},
            "capabilities": [
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa",
                    "version": "3"
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.ThermostatController",
                    "version": "3",
                    "properties": {
                        "supported": [{"name": "targetSetpoint"}, {"name": "thermostatMode"}],
                        "proactivelyReported": True,
                        "retrievable": True
                    }
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.TemperatureSensor",
                    "version": "3",
                    "properties": {
                        "supported": [{"name": "temperature"}],
                        "proactivelyReported": True,
                        "retrievable": True
                    }
                }
            ]
        },
        {
            "endpointId": "front_door_lock",
            "manufacturerName": "Hearth Universal",
            "friendlyName": "Entryway Deadbolt Smart Lock",
            "description": "Motorized smart deadbolt with Sentinel Propose-Never-Execute safety",
            "displayCategories": ["SMARTLOCK"],
            "cookie": {},
            "capabilities": [
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa",
                    "version": "3"
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.LockController",
                    "version": "3",
                    "properties": {
                        "supported": [{"name": "lockState"}],
                        "proactivelyReported": True,
                        "retrievable": True
                    }
                }
            ]
        },
        {
            "endpointId": "front_doorbell_cam",
            "manufacturerName": "Ring",
            "friendlyName": "Front Porch Ring Video Doorbell",
            "description": "1080p HD Video Doorbell with Motion Detection & Live Stream",
            "displayCategories": ["DOORBELL", "CAMERA"],
            "cookie": {},
            "capabilities": [
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa",
                    "version": "3"
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.DoorbellEventSource",
                    "version": "3",
                    "properties": {
                        "supported": [{"name": "doorbellPress"}],
                        "proactivelyReported": True
                    }
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.MotionSensor",
                    "version": "3",
                    "properties": {
                        "supported": [{"name": "detectionState"}],
                        "proactivelyReported": True,
                        "retrievable": True
                    }
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.CameraStreamController",
                    "version": "3",
                    "cameraStreamConfigurations": [
                        {
                            "protocols": ["RTSP", "HLS"],
                            "resolutions": [{"width": 1920, "height": 1080}],
                            "authorizationTypes": ["NONE"],
                            "videoCodecs": ["H264"],
                            "audioCodecs": ["AAC"]
                        }
                    ]
                }
            ]
        }
    ]

    return {
        "event": {
            "header": _make_header("Alexa.Discovery", "Discover.Response", correlation_token),
            "payload": {"endpoints": endpoints}
        }
    }


def _handle_report_state(endpoint_id: str, correlation_token: str) -> dict[str, Any]:
    props = _get_endpoint_properties(endpoint_id)
    audit.append("alexa_directive", "Alexa.ReportState", {"endpoint": endpoint_id})
    return {
        "context": {
            "properties": props
        },
        "event": {
            "header": _make_header("Alexa", "StateReport", correlation_token),
            "endpoint": {"endpointId": endpoint_id},
            "payload": {}
        }
    }


KNOWN_LIGHT_ENDPOINTS = {"living_room_lights", "master_bedroom_lights"}
KNOWN_THERMOSTAT_ENDPOINTS = {"home_thermostat"}
KNOWN_LOCK_ENDPOINTS = {"front_door_lock"}


def _err(endpoint_id: str, correlation_token: str, err_type: str, message: str) -> dict[str, Any]:
    return {
        "event": {
            "header": _make_header("Alexa", "ErrorResponse", correlation_token),
            "endpoint": {"endpointId": endpoint_id},
            "payload": {"type": err_type, "message": message},
        }
    }


def _handle_power_controller(name: str, endpoint_id: str, correlation_token: str) -> dict[str, Any]:
    if endpoint_id not in KNOWN_LIGHT_ENDPOINTS:
        return _err(endpoint_id, correlation_token, "NO_SUCH_ENDPOINT",
                    f"Unknown light endpoint '{endpoint_id}'. Discover first via Alexa.Discovery.")
    if name not in ("TurnOn", "TurnOff"):
        return _err(endpoint_id, correlation_token, "INVALID_DIRECTIVE",
                    f"Unsupported PowerController directive '{name}'. Use TurnOn/TurnOff.")
    _emit_react("action", f"PowerController.{name} -> {endpoint_id}",
                {"endpoint": endpoint_id, "power": name})
    turn_on = (name == "TurnOn")
    room = "master_bedroom" if "bedroom" in endpoint_id else "living_room"

    home_mock.update_device(room, "lights", {"on": turn_on, "bri": 80 if turn_on else 0})
    audit.append("alexa_directive", "Alexa.PowerController", {"endpoint": endpoint_id, "action": name})

    sample_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.PowerController",
                    "name": "powerState",
                    "value": "ON" if turn_on else "OFF",
                    "timeOfSample": sample_time,
                    "uncertaintyInMilliseconds": 50
                },
                {
                    "namespace": "Alexa.BrightnessController",
                    "name": "brightness",
                    "value": 80 if turn_on else 0,
                    "timeOfSample": sample_time,
                    "uncertaintyInMilliseconds": 50
                }
            ]
        },
        "event": {
            "header": _make_header("Alexa", "Response", correlation_token),
            "endpoint": {"endpointId": endpoint_id},
            "payload": {}
        }
    }


def _handle_brightness_controller(name: str, endpoint_id: str, payload: dict, correlation_token: str) -> dict[str, Any]:
    if endpoint_id not in KNOWN_LIGHT_ENDPOINTS:
        return _err(endpoint_id, correlation_token, "NO_SUCH_ENDPOINT",
                    f"Unknown light endpoint '{endpoint_id}'.")
    if name not in ("SetBrightness", "AdjustBrightness"):
        return _err(endpoint_id, correlation_token, "INVALID_DIRECTIVE",
                    f"Unsupported BrightnessController directive '{name}'.")
    _emit_react("action", f"BrightnessController.{name} -> {endpoint_id}",
                {"endpoint": endpoint_id, "payload": payload})
    room = "master_bedroom" if "bedroom" in endpoint_id else "living_room"
    st = home_mock.get_state()
    curr_bri = st.get(room, {}).get("lights", {}).get("bri", 80)

    if name == "SetBrightness":
        bri = max(0, min(100, int(payload.get("brightness", curr_bri))))
    elif name == "AdjustBrightness":
        delta = int(payload.get("brightnessDelta", 0))
        bri = max(0, min(100, curr_bri + delta))
    else:
        bri = curr_bri

    turn_on = bri > 0
    home_mock.update_device(room, "lights", {"bri": bri, "on": turn_on})
    audit.append("alexa_directive", "Alexa.BrightnessController", {"endpoint": endpoint_id, "action": name, "brightness": bri})

    sample_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.BrightnessController",
                    "name": "brightness",
                    "value": bri,
                    "timeOfSample": sample_time,
                    "uncertaintyInMilliseconds": 50
                },
                {
                    "namespace": "Alexa.PowerController",
                    "name": "powerState",
                    "value": "ON" if turn_on else "OFF",
                    "timeOfSample": sample_time,
                    "uncertaintyInMilliseconds": 50
                }
            ]
        },
        "event": {
            "header": _make_header("Alexa", "Response", correlation_token),
            "endpoint": {"endpointId": endpoint_id},
            "payload": {}
        }
    }


THERMOSTAT_MODES = {"AUTO", "COOL", "HEAT", "ECO", "OFF", "FAN_ONLY", "DRY", "SLEEP"}
TEMP_MIN_C, TEMP_MAX_C = 10.0, 32.0


def _handle_thermostat_controller(name: str, endpoint_id: str, payload: dict, correlation_token: str) -> dict[str, Any]:
    if endpoint_id not in KNOWN_THERMOSTAT_ENDPOINTS:
        return _err(endpoint_id, correlation_token, "NO_SUCH_ENDPOINT",
                    f"Unknown thermostat endpoint '{endpoint_id}'.")
    if name not in ("SetTargetTemperature", "AdjustTargetTemperature", "SetThermostatMode"):
        return _err(endpoint_id, correlation_token, "INVALID_DIRECTIVE",
                    f"Unsupported ThermostatController directive '{name}'.")
    _emit_react("action", f"ThermostatController.{name} -> {endpoint_id}",
                {"endpoint": endpoint_id, "payload": payload})
    st = home_mock.get_state()
    curr_target = st.get("living_room", {}).get("climate", {}).get("target_c", 21.5)
    curr_mode = st.get("living_room", {}).get("climate", {}).get("mode", "auto")

    patch = {}
    if name == "SetTargetTemperature":
        try:
            target = float(payload.get("targetSetpoint", {}).get("value", curr_target))
        except (TypeError, ValueError):
            return _err(endpoint_id, correlation_token, "INVALID_VALUE",
                        "targetSetpoint.value must be numeric Celsius.")
        if not (TEMP_MIN_C <= target <= TEMP_MAX_C):
            return _err(endpoint_id, correlation_token, "VALUE_OUT_OF_RANGE",
                        f"Target {target}C outside {TEMP_MIN_C}-{TEMP_MAX_C}C comfort band.")
        patch["target_c"] = target
    elif name == "AdjustTargetTemperature":
        try:
            delta = float(payload.get("targetSetpointDelta", {}).get("value", 0.0))
        except (TypeError, ValueError):
            return _err(endpoint_id, correlation_token, "INVALID_VALUE",
                        "targetSetpointDelta.value must be numeric Celsius.")
        target = round(curr_target + delta, 1)
        if not (TEMP_MIN_C <= target <= TEMP_MAX_C):
            return _err(endpoint_id, correlation_token, "VALUE_OUT_OF_RANGE",
                        f"Adjusted target {target}C outside {TEMP_MIN_C}-{TEMP_MAX_C}C band.")
        patch["target_c"] = target
    elif name == "SetThermostatMode":
        target = curr_target
        mode_val = payload.get("thermostatMode", {}).get("value", curr_mode)
        mode_up = str(mode_val).upper()
        if mode_up not in THERMOSTAT_MODES:
            return _err(endpoint_id, correlation_token, "INVALID_VALUE",
                        f"Unknown thermostatMode '{mode_val}'. Supported: {sorted(THERMOSTAT_MODES)}.")
        curr_mode = str(mode_val).lower()
        patch["mode"] = curr_mode
    else:
        target = curr_target

    if patch:
        home_mock.update_device("living_room", "climate", patch)
    audit.append("alexa_directive", "Alexa.ThermostatController", {"target_c": target, "action": name, "mode": curr_mode})

    sample_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.ThermostatController",
                    "name": "targetSetpoint",
                    "value": {"value": target, "scale": "CELSIUS"},
                    "timeOfSample": sample_time,
                    "uncertaintyInMilliseconds": 50
                },
                {
                    "namespace": "Alexa.ThermostatController",
                    "name": "thermostatMode",
                    "value": curr_mode.upper(),
                    "timeOfSample": sample_time,
                    "uncertaintyInMilliseconds": 50
                }
            ]
        },
        "event": {
            "header": _make_header("Alexa", "Response", correlation_token),
            "endpoint": {"endpointId": endpoint_id},
            "payload": {}
        }
    }


def _handle_lock_controller(name: str, endpoint_id: str, correlation_token: str) -> dict[str, Any]:
    if endpoint_id not in KNOWN_LOCK_ENDPOINTS:
        return _err(endpoint_id, correlation_token, "NO_SUCH_ENDPOINT",
                    f"Unknown lock endpoint '{endpoint_id}'.")
    if name not in ("Lock", "Unlock"):
        return _err(endpoint_id, correlation_token, "INVALID_DIRECTIVE",
                    f"Unsupported LockController directive '{name}'. Use Lock/Unlock.")
    _emit_react("action", f"LockController.{name} -> {endpoint_id}",
                {"endpoint": endpoint_id})
    # 1. Lock command -> Safe Tier-1 Autonomous
    if name == "Lock":
        home_mock.toggle_lock(door="front_door", locked=True)
        audit.append("alexa_directive", "Alexa.LockController", {"action": "Lock", "status": "locked"})
        return {
            "context": {
                "properties": [
                    {
                        "namespace": "Alexa.LockController",
                        "name": "lockState",
                        "value": "LOCKED",
                        "timeOfSample": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "uncertaintyInMilliseconds": 50
                    }
                ]
            },
            "event": {
                "header": _make_header("Alexa", "Response", correlation_token),
                "endpoint": {"endpointId": endpoint_id},
                "payload": {}
            }
        }

    # 2. Unlock command -> GATED Tier-2 (Propose-Never-Execute Contract)
    # Physical entryway unlock requires human approval! We draft a proposal in the Approval Tray.
    item = proposals.propose(
        kind="home_lock",
        title="Unlock Front Door (Alexa Directive)",
        reasons="Alexa Smart Home v3 Unlock directive received. Physical security requires human approval.",
        risk_level="high",
        diff="Front door deadbolt: LOCKED -> UNLOCKED (Auto-lock timer 5m).",
        meta={"door": "front_door", "locked": False, "source": "alexa_skill"}
    )
    audit.append("alexa_directive", "Alexa.LockController", {
        "action": "Unlock",
        "verdict": "ask",
        "proposal": item["id"]
    })

    # Return Alexa ErrorResponse: AUTHORIZATION_REQUIRED
    return {
        "event": {
            "header": _make_header("Alexa", "ErrorResponse", correlation_token),
            "endpoint": {"endpointId": endpoint_id},
            "payload": {
                "type": "AUTHORIZATION_REQUIRED",
                "message": f"Door unlock is gated by Hearth Sentinel policy. Approval card #{item['id']} staged in Glass-box Approval Tray."
            }
        }
    }


def _handle_camera_stream_controller(name: str, endpoint_id: str, payload: dict, correlation_token: str) -> dict[str, Any]:
    audit.append("alexa_directive", "Alexa.CameraStreamController", {"endpoint": endpoint_id, "action": name})
    exp_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 3600))
    return {
        "context": {},
        "event": {
            "header": _make_header("Alexa.CameraStreamController", "Response", correlation_token),
            "endpoint": {"endpointId": endpoint_id},
            "payload": {
                "cameraStream": {
                    "uri": "https://stream.hearth.universal/live/front_doorbell.m3u8",
                    "expirationTime": exp_time,
                    "idleTimeoutInSeconds": 300,
                    "protocol": "HLS",
                    "resolution": {"width": 1920, "height": 1080},
                    "audioCodec": "AAC",
                    "videoCodec": "H264"
                }
            }
        }
    }


def trigger_ring_event(event_type: str = "doorbell_press", visitor_label: str = "Delivery Courier") -> dict[str, Any]:
    """Simulate a Ring Doorbell or Motion sensor event, emitting an Alexa announcement directive and v3 event."""
    from . import heartbeat
    t_str = time.strftime("%I:%M %p")
    iso_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if event_type == "doorbell_press":
        heartbeat.tick_proactive("ring_doorbell")

        item = proposals.propose(
            kind="home_lock",
            title=f"Grant Temporary Entry: {visitor_label}",
            reasons=f"Ring Doorbell chime detected at {t_str}. Verify video feed before granting entry.",
            risk_level="high",
            diff="Front Door Deadbolt: 1-Time 3-Minute Unlock for Package Delivery.",
            meta={"door": "front_door", "locked": False, "source": "ring_doorbell"}
        )
        audit.append("ring_security", "doorbell_press", {
            "visitor": visitor_label,
            "proposal": item["id"],
            "timestamp": t_str
        })
        alexa_event = {
            "event": {
                "header": {
                    "namespace": "Alexa.DoorbellEventSource",
                    "name": "DoorbellPress",
                    "payloadVersion": "3",
                    "messageId": str(uuid.uuid4())
                },
                "endpoint": {
                    "endpointId": "front_doorbell_cam"
                },
                "payload": {
                    "cause": {
                        "type": "PHYSICAL_INTERACTION"
                    },
                    "timestamp": iso_time
                }
            }
        }
        return {
            "ok": True,
            "event_type": "doorbell_press",
            "visitor": visitor_label,
            "announcement": f"Someone is at your front door: {visitor_label}.",
            "proposal_id": item["id"],
            "timestamp": t_str,
            "video_feed_url": "/api/ring/preview?cam=front_door",
            "camera_state": "streaming",
            "alexa_event": alexa_event
        }
    else:
        audit.append("ring_security", "motion_detected", {"zone": "Perimeter Porch", "timestamp": t_str})
        alexa_event = {
            "context": {
                "properties": [
                    {
                        "namespace": "Alexa.MotionSensor",
                        "name": "detectionState",
                        "value": "DETECTED",
                        "timeOfSample": iso_time,
                        "uncertaintyInMilliseconds": 50
                    }
                ]
            },
            "event": {
                "header": {
                    "namespace": "Alexa",
                    "name": "ChangeReport",
                    "payloadVersion": "3",
                    "messageId": str(uuid.uuid4())
                },
                "endpoint": {
                    "endpointId": "front_doorbell_cam"
                },
                "payload": {
                    "change": {
                        "cause": {
                            "type": "PHYSICAL_INTERACTION"
                        },
                        "properties": [
                            {
                                "namespace": "Alexa.MotionSensor",
                                "name": "detectionState",
                                "value": "DETECTED",
                                "timeOfSample": iso_time,
                                "uncertaintyInMilliseconds": 50
                            }
                        ]
                    }
                }
            }
        }
        return {
            "ok": True,
            "event_type": "motion_detected",
            "zone": "Front Porch Perimeter",
            "announcement": "Motion detected at Front Porch.",
            "timestamp": t_str,
            "camera_state": "motion_alert",
            "alexa_event": alexa_event
        }


# ==============================================================================
# Alexa+ Multi-Modal Simulator (B3): TTS queue + Echo chime + light-wave + ReAct
# Runs fully headless (no device, no AVS credentials). All state is in-memory
# so the simulator is safe to import from tests and the /api/alexa/* routes.
# ==============================================================================

_TTS_QUEUE: list[dict[str, Any]] = []
_CHIME_LOG: list[dict[str, Any]] = []
_REACT_LOG: list[dict[str, Any]] = []
_LIGHT_WAVE_STATE: dict[str, Any] = {"mode": "idle", "updated_at": ""}
_TTS_SEQ = 0
_REACT_SEQ = 0

CHIME_SPECS: dict[str, dict[str, Any]] = {
    # Procedural Echo activation ping: C5 -> E5 dual-tone (matches web/js/voice.js).
    "wake": {"kind": "wake", "tones": [{"freq": 523.25, "at": 0.0}, {"freq": 659.25, "at": 0.12}],
             "duration_s": 0.45, "gain": 0.2, "wave": "sine"},
    "success": {"kind": "success", "tones": [{"freq": 587.33, "at": 0.0}, {"freq": 783.99, "at": 0.08},
                                            {"freq": 1046.50, "at": 0.16}],
                "duration_s": 0.5, "gain": 0.18, "wave": "sine"},
    "warning": {"kind": "warning", "tones": [{"freq": 180, "at": 0.0, "slide_to": 140}],
                "duration_s": 0.3, "gain": 0.15, "wave": "sawtooth"},
    "scan": {"kind": "scan", "tones": [{"freq": 2200, "at": 0.0}],
             "duration_s": 0.09, "gain": 0.15, "wave": "sine"},
}

LIGHT_WAVE_MODES = ("idle", "listening", "thinking", "speaking", "alert")

LIGHT_WAVE_SPECS: dict[str, dict[str, Any]] = {
    "idle": {"mode": "idle", "amplitude": 0.05, "colors": ["#06b6d4"],
             "hint": "ambient sensing"},
    "listening": {"mode": "listening", "amplitude": 0.9,
                  "colors": ["#ff3366", "#ff88a3"], "hint": "awaiting speech"},
    "thinking": {"mode": "thinking", "amplitude": 0.5,
                 "colors": ["#a855f7", "#06b6d4"], "hint": "orchestrating DAG"},
    "speaking": {"mode": "speaking", "amplitude": 0.8,
                 "colors": ["#06b6d4", "#3b82f6", "#a855f7"], "hint": "audio response"},
    "alert": {"mode": "alert", "amplitude": 1.0,
              "colors": ["#ef4444", "#ff3366"], "hint": "sentinel gated / doorbell"},
}

_DPAD_ACTIONS = ("Up", "Down", "Left", "Right", "Select", "Back")


def _emit_react(phase: str, summary: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    """Append a ReAct visualizer step (thought/action/observation/speak/show)."""
    global _REACT_SEQ
    _REACT_SEQ += 1
    evt = {
        "seq": _REACT_SEQ,
        "phase": phase,
        "summary": summary,
        "detail": detail or {},
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _REACT_LOG.append(evt)
    if len(_REACT_LOG) > 200:
        del _REACT_LOG[:-200]
    return evt


def get_react_events(limit: int = 50) -> list[dict[str, Any]]:
    try:
        n = max(1, min(200, int(limit)))
    except (TypeError, ValueError):
        n = 50
    return list(_REACT_LOG[-n:])


def clear_react_events() -> dict[str, Any]:
    _REACT_LOG.clear()
    return {"ok": True}


def emit_chime(kind: str = "wake") -> dict[str, Any]:
    """Record an Echo chime hook (headless: no audio playback server-side)."""
    spec = dict(CHIME_SPECS.get(kind, CHIME_SPECS["wake"]))
    entry = {"kind": spec["kind"], "spec": spec,
             "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    _CHIME_LOG.append(entry)
    if len(_CHIME_LOG) > 100:
        del _CHIME_LOG[:-100]
    _emit_react("chime", f"Echo chime: {spec['kind']}", {"spec": spec})
    return entry


def get_chime_log(limit: int = 20) -> list[dict[str, Any]]:
    return list(_CHIME_LOG[-limit:])


def emit_light_wave(mode: str = "idle") -> dict[str, Any]:
    """Set the Alexa fluid light-wave hook state (mirrors web glow bar)."""
    m = mode if mode in LIGHT_WAVE_MODES else "idle"
    _LIGHT_WAVE_STATE["mode"] = m
    _LIGHT_WAVE_STATE["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    spec = dict(LIGHT_WAVE_SPECS[m])
    _emit_react("light-wave", f"Light wave -> {m}", {"spec": spec})
    return {"mode": m, "spec": spec, "at": _LIGHT_WAVE_STATE["updated_at"]}


def get_light_wave() -> dict[str, Any]:
    return dict(_LIGHT_WAVE_STATE)


def enqueue_tts(text: str, voice: str = "alexa", lang: str = "en-US") -> dict[str, Any]:
    """Queue a TTS caption for the simulator (playback happens in web voice.js)."""
    global _TTS_SEQ
    clean = " ".join(str(text or "").split())[:2000]
    if not clean:
        return {"ok": False, "error": "empty text"}
    _TTS_SEQ += 1
    entry = {"id": f"tts-{_TTS_SEQ}", "text": clean, "voice": voice, "lang": lang,
             "status": "queued",
             "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    _TTS_QUEUE.append(entry)
    if len(_TTS_QUEUE) > 50:
        del _TTS_QUEUE[:-50]
    _emit_react("speak", clean[:120], {"tts_id": entry["id"]})
    return {"ok": True, **entry}


def get_tts_queue() -> list[dict[str, Any]]:
    return list(_TTS_QUEUE)


def clear_tts_queue() -> dict[str, Any]:
    _TTS_QUEUE.clear()
    return {"ok": True}


def get_apl_payload(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build live datasources payload matching skill/apl_smart_canvas.json bindings."""
    from . import proposals as _prop
    st = home_mock.get_state()
    lock = st.get("entryway", {}).get("lock", {}).get("front_door", "locked")
    payload: dict[str, Any] = {
        "sentinel_status": "SENTINEL ARMED",
        "solar_kw": round(float(st.get("energy", {}).get("solar_generation_kw", 0.85)), 2),
        "annual_savings": "$804/yr",
        "deadbolt_status": str(lock).upper(),
        "pending_proposals_count": len(_prop.list_proposals("pending")),
        "ttsCaption": "",
        "focusIndex": 0,
        "cards": [
            {"id": "lights", "title": "Living Room Lights",
             "subtitle": "ON" if st.get("living_room", {}).get("lights", {}).get("on") else "OFF",
             "action": "lights"},
            {"id": "climate", "title": "Thermostat",
             "subtitle": f"{st.get('living_room', {}).get('climate', {}).get('target_c', 21.5)}C",
             "action": "climate"},
            {"id": "lock", "title": "Front Door",
             "subtitle": str(lock).upper(), "action": "lock"},
        ],
        "reactSteps": [{"phase": e["phase"], "summary": e["summary"]} for e in _REACT_LOG[-6:]],
    }
    if extra:
        payload.update(extra)
    return payload


def build_apl_render_directive(token: str = "hearth-smart-canvas",
                               datasources: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return an Alexa.Presentation.APL RenderDocument directive (visual card)."""
    return {
        "type": "Alexa.Presentation.APL.RenderDocument",
        "token": token,
        "document": {"src": "skill/apl_smart_canvas.json", "version": "2024.1"},
        "datasources": datasources or {"payload": get_apl_payload()},
    }


def build_multimodal_response(speak_text: str = "",
                              apl_payload: dict[str, Any] | None = None,
                              cards: list[dict[str, Any]] | None = None,
                              chime: str = "wake",
                              light_wave: str = "speaking") -> dict[str, Any]:
    """Single-flow envelope: voice TTS + visual APL cards + D-pad focus + hooks.

    Keeps voice, D-pad/keyboard, and visual cards in ONE turn so TV + Echo
    stay in sync. All hooks are headless-safe.
    """
    payload = apl_payload or get_apl_payload()
    if cards is not None:
        payload = dict(payload, cards=cards)
    if speak_text:
        payload = dict(payload, ttsCaption=speak_text[:280])
        tts = enqueue_tts(speak_text)
    else:
        tts = None
    chime_evt = emit_chime(chime) if chime else None
    wave = emit_light_wave(light_wave) if light_wave else get_light_wave()
    react = get_react_events(12)
    apl = build_apl_render_directive(datasources={"payload": payload})
    _emit_react("show", f"APL canvas: {len(payload.get('cards', []))} cards",
                {"token": apl["token"]})
    return {
        "speak_text": speak_text,
        "tts": tts,
        "tts_queue": get_tts_queue()[-5:],
        "chime": chime_evt,
        "light_wave": wave,
        "react": react,
        "apl_payload": payload,
        "apl_directive": apl,
        "dpad_hint": "Arrows move focus, Enter selects, Esc goes back.",
    }


def handle_dpad_input(action: str, focus_index: int = 0,
                      cards: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Simulate Fire TV D-pad / keyboard nav over the APL card row."""
    items = cards if cards is not None else get_apl_payload().get("cards", [])
    n = max(1, len(items))
    if action not in _DPAD_ACTIONS:
        return {"ok": False, "error": f"Unknown D-pad action '{action}'. Use {list(_DPAD_ACTIONS)}."}
    idx = int(focus_index or 0) % n
    selected = None
    if action == "Right":
        idx = (idx + 1) % n
    elif action == "Left":
        idx = (idx - 1) % n
    elif action in ("Up", "Back"):
        idx = 0
    elif action == "Down":
        idx = min(n - 1, idx + 1)
    elif action == "Select":
        selected = items[idx] if items else None
        emit_chime("success")
    emit_light_wave("thinking" if action != "Select" else "speaking")
    _emit_react("dpad", f"D-pad {action} -> focus {idx}",
                {"focus": idx, "selected": (selected or {}).get("id") if selected else None})
    focused = items[idx] if items else None
    return {"ok": True, "action": action, "focus_index": idx, "focused": focused,
            "selected": selected, "count": n,
            "speak_hint": f"Focused {(focused or {}).get('title', 'card')}." if focused else ""}


def _parse_utterance_to_directive(utterance: str) -> dict[str, Any]:
    """Headless NLU: map a spoken phrase to an Alexa v3 directive dict."""
    import re
    u = (utterance or "").lower().strip()
    tok = str(uuid.uuid4())
    if not u or "discover" in u:
        return {"directive": {"header": {"namespace": "Alexa.Discovery", "name": "Discover",
                                        "correlationToken": tok}, "payload": {}}}
    m = re.search(r"set .*?thermostat.*?(\d+(?:\.\d+)?)", u)
    if m:
        return {"directive": {
            "header": {"namespace": "Alexa.ThermostatController", "name": "SetTargetTemperature",
                       "correlationToken": tok},
            "endpoint": {"endpointId": "home_thermostat"},
            "payload": {"targetSetpoint": {"value": float(m.group(1)), "scale": "CELSIUS"}}}}
    if "thermostat" in u and ("eco" in u or "auto" in u or "cool" in u or "heat" in u or "off" in u):
        mode = next((w.upper() for w in ("auto", "cool", "heat", "eco", "off") if w in u), "AUTO")
        return {"directive": {
            "header": {"namespace": "Alexa.ThermostatController", "name": "SetThermostatMode",
                       "correlationToken": tok},
            "endpoint": {"endpointId": "home_thermostat"},
            "payload": {"thermostatMode": {"value": mode}}}}
    m = re.search(r"(brightness|dim|brighten).*?(\d{1,3})", u)
    if m or ("brightness" in u and any(c.isdigit() for c in u)):
        val = int(m.group(2)) if m else 50
        return {"directive": {
            "header": {"namespace": "Alexa.BrightnessController", "name": "SetBrightness",
                       "correlationToken": tok},
            "endpoint": {"endpointId": "master_bedroom_lights" if "bedroom" in u else "living_room_lights"},
            "payload": {"brightness": max(0, min(100, val))}}}
    if "unlock" in u:
        return {"directive": {"header": {"namespace": "Alexa.LockController", "name": "Unlock",
                                         "correlationToken": tok},
                              "endpoint": {"endpointId": "front_door_lock"}, "payload": {}}}
    if "lock" in u:
        return {"directive": {"header": {"namespace": "Alexa.LockController", "name": "Lock",
                                         "correlationToken": tok},
                              "endpoint": {"endpointId": "front_door_lock"}, "payload": {}}}
    if "thermostat" in u or "temperature" in u:
        return {"directive": {"header": {"namespace": "Alexa", "name": "ReportState",
                                        "correlationToken": tok},
                              "endpoint": {"endpointId": "home_thermostat"}, "payload": {}}}
    if any(w in u for w in ("turn on", "switch on", "lights on", "light on")):
        return {"directive": {"header": {"namespace": "Alexa.PowerController", "name": "TurnOn",
                                        "correlationToken": tok},
                              "endpoint": {"endpointId": "master_bedroom_lights" if "bedroom" in u else "living_room_lights"},
                              "payload": {}}}
    if any(w in u for w in ("turn off", "switch off", "lights off", "light off")):
        return {"directive": {"header": {"namespace": "Alexa.PowerController", "name": "TurnOff",
                                        "correlationToken": tok},
                              "endpoint": {"endpointId": "master_bedroom_lights" if "bedroom" in u else "living_room_lights"},
                              "payload": {}}}
    return {"directive": {"header": {"namespace": "Alexa", "name": "ReportState",
                                    "correlationToken": tok},
                          "endpoint": {"endpointId": "living_room_lights"}, "payload": {}}}


def simulate_voice_turn(utterance: str, correlation_token: str = "") -> dict[str, Any]:
    """No-device simulator: voice utterance -> directive round-trip + multimodal envelope.

    Emits the full ReAct trace (thought -> action -> observation -> speak/show)
    so the web ReAct visualizer can render the turn without hardware.
    """
    emit_light_wave("listening")
    emit_chime("wake")
    _emit_react("thought", f"Heard: {utterance[:140]}", {"utterance": utterance})
    directive = _parse_utterance_to_directive(utterance)
    if correlation_token:
        try:
            directive["directive"]["header"]["correlationToken"] = correlation_token
        except (KeyError, TypeError):
            pass
    emit_light_wave("thinking")
    header = directive.get("directive", {}).get("header", {})
    _emit_react("action", f"{header.get('namespace')}.{header.get('name')}",
                {"directive": directive})
    response = handle_directive(directive)
    evt_name = response.get("event", {}).get("header", {}).get("name", "Response")
    payload = response.get("event", {}).get("payload", {})
    if evt_name == "ErrorResponse" and payload.get("type") == "AUTHORIZATION_REQUIRED":
        speak = "That needs your approval. I staged an approval card for you."
        emit_chime("warning")
        wave = "alert"
    elif evt_name == "ErrorResponse":
        speak = f"Sorry, {payload.get('message', 'that did not work.')}"
        emit_chime("warning")
        wave = "alert"
    else:
        wave = "speaking"
        ns, nm = header.get("namespace", ""), header.get("name", "")
        if ns == "Alexa.Discovery":
            n = len(response.get("event", {}).get("payload", {}).get("endpoints", []))
            speak = f"Discovered {n} devices."
        elif nm in ("TurnOn", "TurnOff"):
            speak = "Lights updated."
        elif "TargetTemperature" in nm or "ThermostatMode" in nm:
            speak = "Thermostat updated."
        elif nm in ("Lock", "Unlock"):
            speak = "Front door locked."
        else:
            speak = "Done."
    _emit_react("observation", f"{evt_name}: {speak[:120]}", {"response": evt_name})
    multimodal = build_multimodal_response(speak_text=speak, chime="", light_wave=wave)
    return {"ok": True, "utterance": utterance, "directive": directive,
            "directive_response": response, "multimodal": multimodal,
            "react": get_react_events(20)}
