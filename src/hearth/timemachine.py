"""Glass-Box Temporal Time Machine for Hearth Universal.
Allows users to scrub through simulated future states (Bedtime, Deep Night, Morning Wake)
to see predictive energy flows, climate shifts, security postures, and replenishment alerts.
"""
from __future__ import annotations
import time
from typing import Any

TIMELINE_PRESETS = {
    "now": {
        "label": "Now (Evening Calm)",
        "time_str": "8:50 PM",
        "sun_phase": "Dusk / Sunset",
        "solar_kw": 0.85,
        "grid_draw_kw": 0.35,
        "battery_pct": 94,
        "outdoor_temp": 19.2,
        "indoor_temp": 21.0,
        "lighting_summary": "Living Room 55% Amber (2700K) | Kitchen 40%",
        "security_posture": "Perimeter Locked | Front Porch Camera Active",
        "ring_cam_mode": "Color Daylight HDR",
        "pantry_alert": "Coffee Beans low (2.5 days remaining)",
        "occupancy": "Alex (Living Room), Sarah (Kitchen), Leo (Bedroom)",
        "narrative": "Current active evening state: Living room in warm calm lighting. Household drawing 0.35 kW with 94% battery reserve.",
    },
    "bedtime": {
        "label": "Bedtime Routine (11:00 PM)",
        "time_str": "11:00 PM",
        "sun_phase": "Night",
        "solar_kw": 0.0,
        "grid_draw_kw": 0.22,
        "battery_pct": 89,
        "outdoor_temp": 16.0,
        "indoor_temp": 19.5,
        "lighting_summary": "Living Room OFF (0%) | Bedroom 15% Deep Amber (2000K)",
        "security_posture": "Perimeter Armed / Deadbolts Latch Verified",
        "ring_cam_mode": "Infrared Night Vision (0 Lux)",
        "pantry_alert": "Dishwasher pods depleted by late cycle",
        "occupancy": "All family members in sleep zones",
        "narrative": "Projected Bedtime State: Living room extinguished, bedroom shifted to deep sleep amber (2000K). Perimeter deadbolts verified locked. Front porch camera switched to 850nm Infrared Night Vision.",
    },
    "night": {
        "label": "Deep Night (3:00 AM)",
        "time_str": "3:00 AM",
        "sun_phase": "Deep Night",
        "solar_kw": 0.0,
        "grid_draw_kw": 0.18,
        "battery_pct": 81,
        "outdoor_temp": 13.5,
        "indoor_temp": 19.0,
        "lighting_summary": "All interior lights 0% | Hallway Path Light 5%",
        "security_posture": "High Security Sentinel Armed",
        "ring_cam_mode": "Infrared Night Vision (Motion Sentinel)",
        "pantry_alert": "Overnight restock staging in progress",
        "occupancy": "Deep sleep telemetry active",
        "narrative": "Projected Deep Night State: Minimal phantom base load (180W). House powered cleanly by battery storage with 81% remaining. Zero light pollution.",
    },
    "morning": {
        "label": "Morning Wake (7:30 AM)",
        "time_str": "7:30 AM",
        "sun_phase": "Sunrise",
        "solar_kw": 1.65,
        "grid_draw_kw": 0.0,
        "battery_pct": 78,
        "outdoor_temp": 15.2,
        "indoor_temp": 21.5,
        "lighting_summary": "Kitchen 70% Daylight (4500K) | Living Room 50%",
        "security_posture": "Morning Disarm / Porch Motion Active",
        "ring_cam_mode": "Morning Color Stream",
        "pantry_alert": "Coffee Depleted! Amazon Prime Delivery Van approaching (Stop #2)",
        "occupancy": "Alex & Sarah (Kitchen), Leo (Waking)",
        "narrative": "Projected Morning State: Solar roof generating 1.65 kW (100% net self-sufficient). Kitchen illuminated with energizing 4500K daylight. Amazon Prime delivery van approaching porch with Coffee & Pods.",
    }
}


def get_timeline_presets() -> list[dict]:
    """Return available temporal forecast presets."""
    return [
        {"id": k, "label": v["label"], "time_str": v["time_str"]}
        for k, v in TIMELINE_PRESETS.items()
    ]


def simulate_timeline(preset: str = "now") -> dict:
    """Project smart home telemetry and status for a chosen time."""
    p = preset.lower()
    if p not in TIMELINE_PRESETS:
        p = "now"
    
    data = TIMELINE_PRESETS[p]
    return {
        "ok": True,
        "preset": p,
        "forecast": data,
        "timestamp": time.strftime("%I:%M %p"),
    }
