"""Long-running household goals (memory v2 wrapper).

Thin, stable API over :mod:`hearth.memory` goals storage with an hourly
scheduler hook compatible with ``HEARTH_SCHEDULER=1``.

Example goal flow::

    from hearth import goals
    g = goals.create_goal(
        "Cut utility spend by 20%",
        ["Audit subscriptions", "Shift dishwasher off-peak", "Review kW telemetry"],
        owner="household",
    )
    goals.advance_goal(g["id"])   # progress 1/3 ...
    goals.scheduler_tick()        # hourly hook: advances oldest due active goal
"""
from __future__ import annotations
import os
import time

from . import memory

SCHEDULER_ENV = "HEARTH_SCHEDULER"
SCHEDULER_INTERVAL_ENV = "HEARTH_SCHEDULER_MINUTES"
DEFAULT_INTERVAL_S = 3600


def create_goal(title: str, steps: list[str], owner: str = "household",
                priority: str = "normal", deadline: str = "") -> dict:
    """Create a long-running multi-stage household goal (persisted in SQLite)."""
    return memory.create_goal(title, steps, owner=owner, priority=priority, deadline=deadline)


def advance_goal(gid: int) -> dict:
    """Advance a goal one milestone (crash-safe, atomic)."""
    return memory.advance_goal(int(gid))


def list_goals(status: str | None = None) -> list[dict]:
    """List goals, optionally filtered to ``active`` / ``done``."""
    return memory.list_goals(status)


def get_goal(gid: int) -> dict | None:
    """Fetch a single goal by id (None when missing)."""
    for g in memory.list_goals():
        if g.get("id") == int(gid):
            return g
    return None


def scheduler_tick(now: float | None = None, min_interval_s: int = DEFAULT_INTERVAL_S) -> dict:
    """Hourly scheduler hook: advance the oldest due active goal.

    The ``HEARTH_SCHEDULER=1`` server loop calls the equivalent primitive
    every ``HEARTH_SCHEDULER_MINUTES`` (default 60). Safe to call frequently:
    per-goal rate-limiting via ``last_advanced_at`` means at most one
    advancement per ``min_interval_s``.
    """
    return memory.scheduler_tick(now=now, min_interval_s=min_interval_s)


def scheduler_enabled() -> bool:
    return os.environ.get(SCHEDULER_ENV) == "1"


def scheduler_interval_s() -> int:
    try:
        return int(float(os.environ.get(SCHEDULER_INTERVAL_ENV, "60")) * 60)
    except (TypeError, ValueError):
        return DEFAULT_INTERVAL_S


def run_scheduler_once(now: float | None = None) -> dict:
    """Single scheduler iteration used by the background loop and tests."""
    ts = now if now is not None else time.time()
    out = scheduler_tick(now=ts)
    out["scheduler"] = "on" if scheduler_enabled() else "off"
    return out
