"""Amazon Alexa Smart Home Skills API v3 Directive Adapter.
Provides native compliance with the Alexa Smart Home API:
- Alexa.Discovery (Discover appliances, endpoints, and capabilities)
- Alexa.PowerController (TurnOn, TurnOff for lighting & appliances)
- Alexa.ThermostatController (SetTargetTemperature, AdjustTargetTemperature)
- Alexa.LockController (Lock [Tier-1], Unlock [Tier-2 Sentinel Gated])

Enables zero-friction integration with Alexa Voice Service (AVS) and Alexa Skills Kit (ASK).
"""
from __future__ import annotations
import json
import time
import uuid
from typing import Any

from . import home_mock, sentinel, proposals, audit


def _make_header(namespace: str, name: str, correlation_token: str = "") -> dict[str, Any]:
    return {
        "namespace": namespace,
        "name": name,
        "payloadVersion": "3",
        "messageId": str(uuid.uuid4()),
        "correlationToken": correlation_token
    }


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

    # 2. Alexa.PowerController (TurnOn / TurnOff)
    if namespace == "Alexa.PowerController":
        return _handle_power_controller(name, endpoint_id, correlation_token)

    # 3. Alexa.ThermostatController (SetTargetTemperature / AdjustTargetTemperature)
    if namespace == "Alexa.ThermostatController":
        return _handle_thermostat_controller(name, endpoint_id, payload, correlation_token)

    # 4. Alexa.LockController (Lock / Unlock)
    if namespace == "Alexa.LockController":
        return _handle_lock_controller(name, endpoint_id, correlation_token)

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


def _handle_discovery(correlation_token: str) -> dict[str, Any]:
    """Return discovered smart home endpoints formatted for Alexa Smart Home v3."""
    endpoints = [
        {
            "endpointId": "living_room_lights",
            "manufacturerName": "Hearth Universal",
            "friendlyName": "Living Room Ceiling Lights",
            "description": "Ambient warm dimmable illumination",
            "displayCategories": ["LIGHT"],
            "capabilities": [
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
            "capabilities": [
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.PowerController",
                    "version": "3",
                    "properties": {
                        "supported": [{"name": "powerState"}],
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
            "capabilities": [
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.ThermostatController",
                    "version": "3",
                    "properties": {
                        "supported": [{"name": "targetSetpoint"}, {"name": "thermostatMode"}],
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
            "capabilities": [
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
        }
    ]

    return {
        "event": {
            "header": _make_header("Alexa.Discovery", "Discover.Response", correlation_token),
            "payload": {"endpoints": endpoints}
        }
    }


def _handle_power_controller(name: str, endpoint_id: str, correlation_token: str) -> dict[str, Any]:
    turn_on = (name == "TurnOn")
    room = "master_bedroom" if "bedroom" in endpoint_id else "living_room"
    
    home_mock.update_device(room, "lights", {"on": turn_on, "bri": 80 if turn_on else 0})
    audit.append("alexa_directive", "Alexa.PowerController", {"endpoint": endpoint_id, "action": name})

    return {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.PowerController",
                    "name": "powerState",
                    "value": "ON" if turn_on else "OFF",
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


def _handle_thermostat_controller(name: str, endpoint_id: str, payload: dict, correlation_token: str) -> dict[str, Any]:
    st = home_mock.get_state()
    curr_target = st.get("living_room", {}).get("climate", {}).get("target_c", 21.5)
    
    if name == "SetTargetTemperature":
        target = float(payload.get("targetSetpoint", {}).get("value", curr_target))
    elif name == "AdjustTargetTemperature":
        delta = float(payload.get("targetSetpointDelta", {}).get("value", 0.0))
        target = round(curr_target + delta, 1)
    else:
        target = curr_target

    home_mock.update_device("living_room", "climate", {"target_c": target})
    audit.append("alexa_directive", "Alexa.ThermostatController", {"target_c": target})

    return {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.ThermostatController",
                    "name": "targetSetpoint",
                    "value": {"value": target, "scale": "CELSIUS"},
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


def _handle_lock_controller(name: str, endpoint_id: str, correlation_token: str) -> dict[str, Any]:
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
