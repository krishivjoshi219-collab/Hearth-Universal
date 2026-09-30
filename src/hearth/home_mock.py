"""Mock Smart Home Digital Twin for Alexa+ simulated environment.
Provides full multi-room simulation: living room, master bedroom, kitchen, entryway.
Features lighting controls, HVAC climate, smart lock, ambient media, and real-time energy telemetry.
"""
from __future__ import annotations
import copy
import time

DEFAULT_STATE = {
    "living_room": {
        "lights": {
            "on": True,
            "bri": 80,
            "color_temp": "warm",
            "hex": "#ffb366"
        },
        "climate": {
            "current_c": 22.0,
            "target_c": 21.5,
            "mode": "auto",
            "fan": "eco"
        },
        "blinds": "open",
        "media": {
            "status": "idle",
            "title": "Acoustic Afternoon Chill",
            "artist": "Echo Ambient Lounge",
            "volume": 35,
            "playing": False
        }
    },
    "master_bedroom": {
        "lights": {
            "on": False,
            "bri": 0,
            "color_temp": "warm",
            "hex": "#ffa040"
        },
        "climate": {
            "current_c": 20.5,
            "target_c": 19.5,
            "mode": "cool",
            "fan": "silent"
        },
        "blinds": "closed"
    },
    "kitchen": {
        "lights": {
            "on": True,
            "bri": 90,
            "color_temp": "neutral",
            "hex": "#ffffff"
        },
        "appliances": {
            "coffee_maker": "standby",
            "air_purifier": "auto"
        }
    },
    "entryway": {
        "lock": {
            "front_door": "locked",
            "auto_lock_timer_min": 5,
            "last_event": "Auto-locked at 08:30 AM"
        },
        "security_mode": "armed_home"
    },
    "energy": {
        "current_draw_kw": 1.45,
        "solar_generation_kw": 0.85,
        "net_grid_kw": 0.60,
        "daily_kwh": 8.7,
        "projected_cost_monthly": 42.50,
        "eco_score": 94
    },
    "active_scene": "default"
}

SCENES = {
    "evening-calm": {
        "living_room": {
            "lights": {"on": True, "bri": 55, "color_temp": "warm", "hex": "#ff9e42"},
            "climate": {"target_c": 21.0, "mode": "eco"},
            "blinds": "closed",
            "media": {"status": "playing", "playing": True, "title": "Evening Lo-Fi Beats", "volume": 30}
        },
        "master_bedroom": {
            "lights": {"on": False, "bri": 0},
            "climate": {"target_c": 19.5, "mode": "cool"}
        },
        "entryway": {
            "lock": {"front_door": "locked"},
            "security_mode": "armed_home"
        },
        "energy": {"current_draw_kw": 0.95}
    },
    "movie-night": {
        "living_room": {
            "lights": {"on": True, "bri": 20, "color_temp": "warm", "hex": "#9933ff"},
            "climate": {"target_c": 21.5, "mode": "silent"},
            "blinds": "closed",
            "media": {"status": "playing", "playing": True, "title": "Interstellar (4K HDR)", "artist": "Fire TV Cinema", "volume": 60}
        },
        "entryway": {
            "lock": {"front_door": "locked"},
            "security_mode": "armed_home"
        },
        "energy": {"current_draw_kw": 1.10}
    },
    "away": {
        "living_room": {
            "lights": {"on": False, "bri": 0},
            "climate": {"target_c": 18.0, "mode": "eco"},
            "blinds": "closed",
            "media": {"playing": False, "status": "stopped"}
        },
        "master_bedroom": {
            "lights": {"on": False, "bri": 0},
            "climate": {"target_c": 18.0, "mode": "eco"}
        },
        "kitchen": {
            "lights": {"on": False, "bri": 0}
        },
        "entryway": {
            "lock": {"front_door": "locked", "last_event": "Locked for Away mode"},
            "security_mode": "armed_away"
        },
        "energy": {"current_draw_kw": 0.35}
    },
    "wake": {
        "living_room": {
            "lights": {"on": True, "bri": 70, "color_temp": "neutral", "hex": "#fff2e0"},
            "climate": {"target_c": 21.0, "mode": "auto"},
            "blinds": "open"
        },
        "master_bedroom": {
            "lights": {"on": True, "bri": 80, "color_temp": "cool", "hex": "#ffffff"},
            "blinds": "open"
        },
        "kitchen": {
            "lights": {"on": True, "bri": 100},
            "appliances": {"coffee_maker": "brewing"}
        },
        "energy": {"current_draw_kw": 2.20}
    },
    "energy-saver": {
        "living_room": {
            "lights": {"on": True, "bri": 40},
            "climate": {"target_c": 20.0, "mode": "eco"}
        },
        "kitchen": {"lights": {"on": False, "bri": 0}},
        "master_bedroom": {"lights": {"on": False, "bri": 0}},
        "energy": {"current_draw_kw": 0.45}
    }
}

_state = copy.deepcopy(DEFAULT_STATE)


def get_state() -> dict:
    """Return an isolated copy of current smart home state."""
    # Ensure backward compatibility with original minimal keys
    res = copy.deepcopy(_state)
    res["living"] = {
        "lights": {
            "on": res["living_room"]["lights"]["on"],
            "bri": res["living_room"]["lights"]["bri"],
            "ct": res["living_room"]["lights"]["color_temp"]
        },
        "temp_c": res["living_room"]["climate"]["current_c"]
    }
    res["bedroom"] = {
        "lights": {
            "on": res["master_bedroom"]["lights"]["on"],
            "bri": res["master_bedroom"]["lights"]["bri"],
            "ct": res["master_bedroom"]["lights"]["color_temp"]
        },
        "temp_c": res["master_bedroom"]["climate"]["current_c"]
    }
    res["lock"] = {"front_door": res["entryway"]["lock"]["front_door"]}
    res["media"] = {"queue": [res["living_room"]["media"]["title"]]}
    return res


def update_device(room: str, device: str, patch: dict) -> dict:
    """Update a specific room device patch."""
    if room not in _state:
        return {"ok": False, "error": f"Unknown room '{room}'"}
    if device not in _state[room]:
        _state[room][device] = patch
    elif isinstance(_state[room][device], dict) and isinstance(patch, dict):
        _state[room][device].update(patch)
    else:
        _state[room][device] = patch
    return {"ok": True, "state": get_state()}


def toggle_lock(door: str = "front_door", locked: bool = True) -> dict:
    """Lock or unlock entryway."""
    status = "locked" if locked else "unlocked"
    _state["entryway"]["lock"]["front_door"] = status
    _state["entryway"]["lock"]["last_event"] = f"Manual {status} via Alexa+ UI at {time.strftime('%I:%M %p')}"
    return {"ok": True, "door": door, "status": status, "state": get_state()}


def set_scene(name: str) -> dict:
    """Apply a named scene to all rooms."""
    if name not in SCENES:
        return {"ok": False, "error": f"unknown scene {name}", "scenes": sorted(SCENES)}
    patch_data = SCENES[name]
    for section, val in patch_data.items():
        if section in _state:
            if isinstance(val, dict) and isinstance(_state[section], dict):
                for k, v in val.items():
                    if isinstance(v, dict) and isinstance(_state[section].get(k), dict):
                        _state[section][k].update(v)
                    else:
                        _state[section][k] = v
            else:
                _state[section] = val
        else:
            _state[section] = val
    _state["active_scene"] = name
    return {"ok": True, "scene": name, "state": get_state()}


def routine(name: str) -> dict:
    """Execute a coordinated routine (scene + smart appliances + audio)."""
    r = set_scene(name)
    timers = {
        "movie-night": [{"action": "dim_cinema_lighting", "in_sec": 0}, {"action": "dim_hallway", "in_sec": 120}],
        "wake": [{"action": "brew_espresso", "in_sec": 0}, {"action": "morning_news_briefing", "in_sec": 300}],
        "evening-calm": [{"action": "engage_night_thermostat", "in_sec": 1800}],
    }.get(name, [])
    return {"ok": r["ok"], "routine": name, "timers": timers, "state": get_state()}


def reset_state() -> dict:
    """Reset to clean default state."""
    global _state
    _state = copy.deepcopy(DEFAULT_STATE)
    return {"ok": True, "state": get_state()}
