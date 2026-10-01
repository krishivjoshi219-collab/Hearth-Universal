"""Family Arbiter v2: per-resident Pareto negotiation + peak-tariff load shifting.

Builds on :mod:`hearth.arbiter` (pure Pareto math) and :mod:`hearth.memory`
(per-resident profiles + child guardrails):

- Resident-aware climate negotiation: pulls default setpoints/weights from
  memory profiles (Admin / Partner / Child Leo), caps the child weight so Leo
  can nudge but never override adults, clamps the outcome to a child-safe band.
- Peak-tariff load shifting: off-peak scheduling with deadline awareness,
  persisted as a memory fact for context continuity.
- Child guardrails: requests issued *as* Leo are restricted to safe comfort
  outcomes; financial/physical-security overrides are denied with a clear
  error instead of an arbitration.
- Propose-never-execute: every outcome is a staged compromise + proposed_action,
  never a direct device actuation.

Zero-config, no external keys.
"""
from __future__ import annotations
import time

from . import arbiter, memory

# Child-safe climate band (°C). Outcomes are clamped into this range when a
# child participates, and child-issued requests can never push outside it.
CHILD_SAFE_MIN_C = 19.0
CHILD_SAFE_MAX_C = 24.0
# A child resident may influence the Pareto blend but never dominate it.
CHILD_MAX_WEIGHT = 0.8

# Peak-tariff window model (zero-config defaults; override via custom_params).
PEAK_START_HOUR = 16      # 4 PM
PEAK_END_HOUR = 21        # 9 PM
PEAK_RATE_DEFAULT = 0.48  # $/kWh
OFFPEAK_RATE_DEFAULT = 0.12


def resident_profiles() -> dict:
    """Return canonical per-resident profiles (Admin/Partner/Child Leo)."""
    return {k: dict(v) for k, v in memory.RESIDENT_PROFILES.items()}


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def negotiate_climate(parties: list[dict] | None = None,
                      requester: str = "household",
                      custom_params: dict | None = None) -> dict:
    """Pareto-optimal setpoint negotiation across residents.

    ``parties`` entries support ``name/resident``, ``requested_setpoint``,
    ``weight``, ``tolerance``. Missing parties fall back to memory profiles
    (Admin 21.5°C, Partner 23.0°C, Leo 21.0°C). Child weight is capped at
    :data:`CHILD_MAX_WEIGHT` and the final setpoint is clamped to the
    child-safe band whenever Leo participates.
    """
    params = dict(custom_params or {})
    profiles = memory.RESIDENT_PROFILES
    who = memory.canonical_resident(requester)

    if not parties:
        parties = [
            {"name": "Admin", "resident": "admin",
             "requested_setpoint": profiles["admin"]["default_setpoint"],
             "weight": profiles["admin"]["weight"],
             "tolerance": profiles["admin"]["tolerance"]},
            {"name": "Partner", "resident": "partner",
             "requested_setpoint": profiles["partner"]["default_setpoint"],
             "weight": profiles["partner"]["weight"],
             "tolerance": profiles["partner"]["tolerance"]},
            {"name": "Leo", "resident": "child",
             "requested_setpoint": profiles["child"]["default_setpoint"],
             "weight": profiles["child"]["weight"],
             "tolerance": profiles["child"]["tolerance"]},
        ]

    norm: list[dict] = []
    child_involved = False
    for p in parties:
        resident = memory.canonical_resident(p.get("resident", p.get("name", "household")))
        if resident == "child":
            child_involved = True
        prof = profiles.get(resident, profiles["household"])
        try:
            sp = float(p.get("requested_setpoint", p.get("setpoint", prof["default_setpoint"])))
        except (TypeError, ValueError):
            sp = float(prof["default_setpoint"])
        # Clamp raw requests to a sane HVAC envelope before blending.
        sp = _clamp(sp, 16.0, 27.0)
        try:
            w = float(p.get("weight", prof.get("weight", 1.0)))
        except (TypeError, ValueError):
            w = 1.0
        if resident == "child":
            w = min(w, CHILD_MAX_WEIGHT)
        try:
            tol = float(p.get("tolerance", prof.get("tolerance", 1.5)))
        except (TypeError, ValueError):
            tol = 1.5
        name = str(p.get("name", prof.get("display_name", resident.title())))
        norm.append({"name": name, "resident": resident, "requested_setpoint": sp,
                     "weight": max(0.1, w), "tolerance": max(0.5, tol),
                     "preference": str(p.get("preference", f"{sp:.1f}°C"))})

    result = arbiter.arbitrate_multi_resident_climate(norm, params)
    if child_involved:
        try:
            sp0 = float(result["compromise"]["target_setpoint"])
            sp1 = round(_clamp(sp0, CHILD_SAFE_MIN_C, CHILD_SAFE_MAX_C), 1)
            result["compromise"]["target_setpoint"] = sp1
            result["proposed_action"]["setpoint"] = sp1
            result["compromise"]["child_safe_band"] = f"{CHILD_SAFE_MIN_C:.1f}–{CHILD_SAFE_MAX_C:.1f}°C enforced"
        except (KeyError, TypeError, ValueError):
            pass
    result["requested_by"] = who
    result["child_guardrails"] = child_involved
    # Persist the outcome for context continuity (best-effort, never fatal).
    try:
        memory.remember(
            f"arbiter_climate_last",
            f"{result['compromise'].get('target_setpoint')}°C via {result.get('resolution_badge', 'Pareto')} "
            f"({', '.join(p['name'] for p in norm)})",
            owner="household",
        )
    except Exception:
        pass
    return result


def shift_load(device: str = "dishwasher", requester: str = "household",
               custom_params: dict | None = None) -> dict:
    """Peak-tariff load shifting: delay heavy loads to the off-peak window.

    Child-issued requests may *view* the shift plan but cannot schedule
    high-draw devices (EV charger) — denied with a guardrail error.
    """
    params = dict(custom_params or {})
    who = memory.canonical_resident(requester)
    dev = str(device or params.get("device", "dishwasher")).lower()
    params.setdefault("device", dev)
    params.setdefault("peak_rate", PEAK_RATE_DEFAULT)
    params.setdefault("offpeak_rate", OFFPEAK_RATE_DEFAULT)

    if who == "child" and ("ev" in dev or "charger" in dev):
        return {
            "ok": False,
            "error": "Child safety guardrail: profile 'Leo' cannot schedule high-draw devices. Ask an adult.",
            "conflict_type": "tariff",
            "device": dev,
        }
    result = arbiter.arbitrate_tariff_load_shifting(params)
    result["requested_by"] = who
    try:
        memory.remember(
            "arbiter_tariff_last",
            f"{dev} delayed {result['compromise'].get('delay_minutes')}min "
            f"saves ${-float(result['proposed_action'].get('cost_delta', 0)):.2f}",
            owner="household",
        )
    except Exception:
        pass
    return result


def bedtime_protocol(resident: str = "Leo", custom_params: dict | None = None) -> dict:
    """Sunset wind-down protocol (always child-safe, gradual, non-jarring)."""
    params = dict(custom_params or {})
    params.setdefault("resident", resident)
    return arbiter.arbitrate_bedtime_protocol(params)


def resolve(conflict_type: str = "climate", parties: list[dict] | None = None,
            requester: str = "household", custom_params: dict | None = None) -> dict:
    """Unified Family Arbiter entry point (MCP ``family_arbiter_resolve`` shape).

    Routes to climate negotiation / tariff shifting / bedtime protocol with
    resident context + child guardrails applied. Unknown types fall back to the
    generic Pareto solver. Never executes — returns a staged compromise.
    """
    ctype = str(conflict_type or "climate").lower()
    params = dict(custom_params or {})
    if parties is not None and "parties" not in params:
        params["parties"] = parties
    if ctype in ("climate", "temperature", "setpoint", "energy_peak"):
        return negotiate_climate(parties or params.get("parties"), requester, params)
    if ctype in ("tariff", "load", "peak", "dishwasher", "ev", "ev_charger"):
        return shift_load(params.get("device", "dishwasher"), requester, params)
    if ctype in ("bedtime", "wind-down", "wind_down", "sleep"):
        return bedtime_protocol(params.get("resident", "Leo"), params)
    # Generic fallback with guardrailed parties.
    plist = params.get("parties") or parties or [{"name": requester}]
    result = arbiter.arbitrate_generic(ctype, plist, params)
    result["requested_by"] = memory.canonical_resident(requester)
    result["timestamp"] = time.strftime("%I:%M %p")
    return result
