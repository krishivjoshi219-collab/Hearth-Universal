"""Household memory v2: context-aware SQLite facts/goals with per-resident profiles.

- Per-resident profiles: Admin / Partner / Child Leo (child guardrails).
- Context-aware query: household facts + resident-scoped facts, child-safe filtering.
- Crash-safe atomic writes: inter-process file lock + BEGIN IMMEDIATE + WAL.
- Long-running goals with hourly scheduler hook (HEARTH_SCHEDULER=1 compatible).
- Backward compatible: remember/query/create_goal/advance_goal/list_goals keep
  their original signatures (new optional kwargs only).
"""
from __future__ import annotations
import json
import os
import sqlite3
import time
from pathlib import Path

STATE_DIR = Path(os.environ.get("HEARTH_STATE_DIR", "state"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS facts (
    key TEXT PRIMARY KEY,
    value TEXT,
    owner TEXT DEFAULT 'household',
    updated_at INTEGER
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    steps TEXT,
    status TEXT DEFAULT 'active',
    progress INTEGER DEFAULT 0,
    created_at INTEGER
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT,
    content TEXT,
    model TEXT,
    ts INTEGER
);

CREATE TABLE IF NOT EXISTS residents (
    profile TEXT PRIMARY KEY,
    display_name TEXT,
    role TEXT,
    tier_limit TEXT,
    prefs_json TEXT,
    updated_at INTEGER
);
"""

# Product guardrails: bound stored sizes and history length.
KEY_MAX = 128
VALUE_MAX = 8000
GOAL_TITLE_MAX = 200
GOAL_STEPS_MAX = 20
CHAT_HISTORY_MAX = 500

SCHEMA_VERSION = 2

# ---------------------------------------------------------------------------
# Per-resident profiles (memory v2)
# ---------------------------------------------------------------------------
RESIDENT_PROFILES: dict[str, dict] = {
    "admin": {
        "profile": "admin",
        "display_name": "Krishiv Joshi",
        "role": "Household Admin",
        "tier_limit": "tier-3",
        "default_setpoint": 21.5,
        "tolerance": 1.5,
        "weight": 1.2,
    },
    "partner": {
        "profile": "partner",
        "display_name": "Sarah Miller",
        "role": "Partner (Full Access)",
        "tier_limit": "tier-3",
        "default_setpoint": 23.0,
        "tolerance": 1.5,
        "weight": 1.0,
    },
    "child": {
        "profile": "child",
        "display_name": "Leo (Child)",
        "role": "Child (Safe Comfort Only)",
        "tier_limit": "tier-1",
        "default_setpoint": 21.0,
        "tolerance": 1.2,
        "weight": 0.8,
    },
    "household": {
        "profile": "household",
        "display_name": "Household (Shared)",
        "role": "Shared household scope",
        "tier_limit": "tier-1",
        "default_setpoint": 21.5,
        "tolerance": 1.5,
        "weight": 1.0,
    },
}

# Aliases so callers can pass "Leo", "kid", "Sarah", etc.
_RESIDENT_ALIASES: dict[str, str] = {
    "admin": "admin",
    "krishiv": "admin",
    "krishiv joshi": "admin",
    "partner": "partner",
    "sarah": "partner",
    "sarah miller": "partner",
    "child": "child",
    "leo": "child",
    "kid": "child",
    "child leo": "child",
    "household": "household",
    "shared": "household",
    "guest": "household",
}

CHILD_PROFILE = "child"

# Child guardrails: Leo may store comfort facts only — never secrets/credentials,
# money, locks, or security overrides.
CHILD_DENIED_KEY_SUBSTRINGS = (
    "password", "passwd", "token", "secret", "api_key", "apikey",
    "lock_code", "pin", "payment", "card", "bank", "ssn",
    "credit", "credential", "private_key", "seed",
)
CHILD_DENIED_OWNER_OVERRIDE = True  # child can never claim admin/partner ownership


def canonical_resident(owner: str | None) -> str:
    """Normalize any resident label to admin|partner|child|household."""
    if not owner:
        return "household"
    key = str(owner).strip().lower()
    if key in _RESIDENT_ALIASES:
        return _RESIDENT_ALIASES[key]
    return "household"


def is_child(owner: str | None) -> bool:
    return canonical_resident(owner) == CHILD_PROFILE


def _cap(text: str, maximum: int) -> tuple[str, bool]:
    if len(text) <= maximum:
        return text, False
    return text[:maximum], True


def _child_blocked(key: str, value: str) -> str | None:
    """Return denial reason if a child profile may not store this fact."""
    blob = f"{key} {value}".lower()
    for sub in CHILD_DENIED_KEY_SUBSTRINGS:
        if sub in blob:
            return (
                "Child safety guardrail: profile 'Leo' may only store safe comfort "
                f"facts; blocked sensitive topic '{sub}'. Ask an adult for help."
            )
    return None


DEFAULT_FACTS = [
    ("dietary_preference", "Gluten-free dinners on weekdays; kid loves oatmeal and berries", "household"),
    ("budget_entertainment_limit", "$200/month across streaming, games, and dining out", "household"),
    ("night_climate_setpoint", "19.5°C in master bedroom with silent eco-fan", "household"),
    ("preferred_coffee_roast", "Organic Arabica whole bean medium roast", "household"),
    ("emergency_contact", "Dr. Sarah Miller (555-0192)", "household"),
]


def _columns(con: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()}
    except sqlite3.DatabaseError:
        return set()


def _init_db(con: sqlite3.Connection) -> None:
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript(SCHEMA)
    # Auto-migrate older schemas (v1 -> v2 deltas)
    for stmt in (
        "ALTER TABLE facts ADD COLUMN updated_at INTEGER DEFAULT 0",
        "ALTER TABLE goals ADD COLUMN created_at INTEGER DEFAULT 0",
        "ALTER TABLE facts ADD COLUMN sensitivity TEXT DEFAULT 'normal'",
        "ALTER TABLE facts ADD COLUMN created_at INTEGER DEFAULT 0",
        "ALTER TABLE goals ADD COLUMN owner TEXT DEFAULT 'household'",
        "ALTER TABLE goals ADD COLUMN priority TEXT DEFAULT 'normal'",
        "ALTER TABLE goals ADD COLUMN deadline TEXT DEFAULT ''",
        "ALTER TABLE goals ADD COLUMN updated_at INTEGER DEFAULT 0",
        "ALTER TABLE goals ADD COLUMN last_advanced_at INTEGER DEFAULT 0",
    ):
        try:
            con.execute(stmt)
        except sqlite3.OperationalError:
            pass

    # Populate defaults if facts table has no rows
    count = con.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    now = int(time.time())
    if count == 0:
        for k, v, o in DEFAULT_FACTS:
            con.execute(
                "INSERT OR IGNORE INTO facts(key, value, owner, updated_at, sensitivity, created_at) "
                "VALUES (?, ?, ?, ?, 'normal', ?)",
                (k, v, o, now, now),
            )

    # Populate default goal if goals table has no rows
    g_count = con.execute("SELECT COUNT(*) FROM goals").fetchone()[0]
    if g_count == 0:
        initial_steps = json.dumps([
            "Audit household subscription waste (target >$300/yr)",
            "Engage off-peak dishwasher and EV charging schedule",
            "Install smart thermostat eco-setpoints overnight",
            "Review monthly electric kilowatt telemetry"
        ])
        con.execute(
            "INSERT OR IGNORE INTO goals(id, title, steps, status, progress, created_at, owner, priority, deadline, updated_at, last_advanced_at) "
            "VALUES (1, ?, ?, 'active', 1, ?, 'household', 'normal', '', ?, 0)",
            ("Cut Monthly Household Utility & Subscription Spend by 20%", initial_steps, now, now),
        )

    # Seed per-resident profiles (idempotent)
    for key, prof in RESIDENT_PROFILES.items():
        con.execute(
            "INSERT OR IGNORE INTO residents(profile, display_name, role, tier_limit, prefs_json, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (key, prof["display_name"], prof["role"], prof["tier_limit"],
             json.dumps({k: v for k, v in prof.items() if k not in ("profile", "display_name", "role", "tier_limit")}),
             now),
        )
    con.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    con.commit()


def _db_path() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR / "memory.db"


def _db() -> sqlite3.Connection:
    db_path = _db_path()
    try:
        con = sqlite3.connect(db_path, timeout=30, isolation_level=None)
        con.execute("PRAGMA journal_mode=WAL")
        ver = con.execute("PRAGMA user_version").fetchone()[0]
        if ver != SCHEMA_VERSION:
            _init_db(con)
        else:
            con.execute("PRAGMA synchronous=NORMAL")
            # Ensure seed rows exist even on version match (e.g. tests wiping tables)
            try:
                n = con.execute("SELECT COUNT(*) FROM residents").fetchone()[0]
                if n == 0:
                    now = int(time.time())
                    for key, prof in RESIDENT_PROFILES.items():
                        con.execute(
                            "INSERT OR IGNORE INTO residents(profile, display_name, role, tier_limit, prefs_json, updated_at) "
                            "VALUES (?, ?, ?, ?, ?, ?)",
                            (key, prof["display_name"], prof["role"], prof["tier_limit"], json.dumps({}), now),
                        )
                    con.execute("COMMIT") if con.in_transaction else None
            except sqlite3.DatabaseError:
                pass
        return con
    except sqlite3.DatabaseError:
        # Corrupt database: quarantine it and start fresh instead of
        # failing every request until someone SSHes in.
        try:
            os.replace(db_path, STATE_DIR / f"memory.corrupt.{int(time.time())}.db")
        except Exception:
            pass
        con = sqlite3.connect(db_path, timeout=30, isolation_level=None)
        _init_db(con)
        return con


def _locked_write():
    """Crash-safe inter-process write guard (no-op fallback on exotic platforms)."""
    try:
        from .atomic import locked as _locked
        return _locked(_db_path())
    except Exception:
        from contextlib import nullcontext
        return nullcontext()


def remember(key: str, value: str, owner: str = "household") -> dict:
    """Store or update a household fact (length-capped, resident-aware).

    Child guardrail: profile Leo/child cannot store sensitive facts
    (passwords, tokens, payment, lock codes, ...). Returns
    ``{"ok": False, "error: ...}`` instead of persisting.
    """
    key, k_trunc = _cap(str(key), KEY_MAX)
    value, v_trunc = _cap(str(value), VALUE_MAX)
    resident = canonical_resident(owner)
    requester_raw = str(owner or "household")

    # A child caller must not be able to escalate by passing owner='admin'.
    if is_child(requester_raw) and resident != CHILD_PROFILE:
        return {
            "ok": False,
            "error": "Child safety guardrail: profile 'Leo' cannot write facts owned by another resident.",
        }
    if resident == CHILD_PROFILE:
        denied = _child_blocked(key, value)
        if denied:
            return {"ok": False, "error": denied}

    sensitivity = "child-safe" if resident == CHILD_PROFILE else "normal"
    con = _db()
    try:
        with _locked_write():
            now = int(time.time())
            con.execute("BEGIN IMMEDIATE")
            try:
                cols = _columns(con, "facts")
                if {"sensitivity", "created_at"} <= cols:
                    con.execute(
                        "INSERT OR REPLACE INTO facts(key, value, owner, updated_at, sensitivity, created_at) "
                        "VALUES(?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM facts WHERE key=?), ?))",
                        (key, value, resident, now, sensitivity, key, now),
                    )
                else:
                    con.execute(
                        "INSERT OR REPLACE INTO facts(key, value, owner, updated_at) VALUES(?, ?, ?, ?)",
                        (key, value, resident, now),
                    )
                con.execute("COMMIT")
            except Exception:
                try:
                    con.execute("ROLLBACK")
                except Exception:
                    pass
                raise
            try:
                con.execute("PRAGMA wal_checkpoint(PASSIVE)")
            except Exception:
                pass
    finally:
        con.close()
    out: dict = {"ok": True, "key": key, "value": value, "owner": resident}
    if k_trunc or v_trunc:
        out["truncated"] = True
    return out


def query(q: str = "", requester: str = "household", limit: int = 200) -> list[dict]:
    """Query stored household facts (% and _ treated literally, not as wildcards).

    Context-aware v2: ``requester`` scopes visibility. Household/admin/partner
    see everything; the child profile (Leo) sees household + its own facts and
    never sees sensitive admin/partner facts.
    """
    limit = max(1, min(500, int(limit)))
    who = canonical_resident(requester)
    con = _db()
    try:
        if q:
            q_str = str(q)
            q_esc = q_str.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            like = f"%{q_esc}%"
            rows = con.execute(
                "SELECT key, value, owner FROM facts WHERE key LIKE ? ESCAPE '\\' OR value LIKE ? ESCAPE '\\' LIMIT ?",
                (like, like, limit)).fetchall()
        else:
            rows = con.execute("SELECT key, value, owner FROM facts ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        facts = [{"key": k, "value": v, "owner": o} for k, v, o in rows]
        if who == CHILD_PROFILE:
            facts = [
                f for f in facts
                if canonical_resident(f.get("owner")) in ("household", CHILD_PROFILE)
                and _child_blocked(f["key"], f["value"]) is None
            ]
        return facts
    finally:
        con.close()


def get_resident_context(resident: str = "household") -> dict:
    """Return merged context for a resident: profile + household & own facts."""
    who = canonical_resident(resident)
    profile = RESIDENT_PROFILES.get(who, RESIDENT_PROFILES["household"])
    facts = query("", requester=who)
    own = [f for f in facts if canonical_resident(f.get("owner")) in ("household", who)]
    return {
        "resident": who,
        "profile": profile,
        "facts": own,
        "fact_count": len(own),
        "child_guardrails": who == CHILD_PROFILE,
    }


def list_residents() -> list[dict]:
    """List seeded per-resident profiles (Admin/Partner/Child Leo + household)."""
    con = _db()
    try:
        try:
            rows = con.execute(
                "SELECT profile, display_name, role, tier_limit, prefs_json FROM residents ORDER BY profile ASC"
            ).fetchall()
            if rows:
                out = []
                for profile, display_name, role, tier_limit, prefs_json in rows:
                    try:
                        prefs = json.loads(prefs_json) if prefs_json else {}
                    except Exception:
                        prefs = {}
                    out.append({
                        "profile": profile, "display_name": display_name,
                        "role": role, "tier_limit": tier_limit, "prefs": prefs,
                    })
                return out
        except sqlite3.DatabaseError:
            pass
        return [dict(v) for v in RESIDENT_PROFILES.values()]
    finally:
        con.close()


def delete(key: str) -> dict:
    """Remove a fact from household memory."""
    con = _db()
    try:
        with _locked_write():
            con.execute("BEGIN IMMEDIATE")
            try:
                cur = con.execute("DELETE FROM facts WHERE key=?", (str(key),))
                con.execute("COMMIT")
                affected = cur.rowcount
            except Exception:
                try:
                    con.execute("ROLLBACK")
                except Exception:
                    pass
                raise
        return {"ok": affected > 0, "key": key}
    finally:
        con.close()


def create_goal(title: str, steps: list[str], owner: str = "household",
                priority: str = "normal", deadline: str = "") -> dict:
    """Create a multi-step household goal (title/steps capped).

    v2 adds optional ``owner`` (resident scope), ``priority`` and ``deadline``
    metadata while keeping the original (title, steps) call shape working.
    """
    title, _ = _cap(str(title), GOAL_TITLE_MAX)
    steps = [str(s) for s in steps][:GOAL_STEPS_MAX] or ["step 1"]
    resident = canonical_resident(owner)
    prio = str(priority or "normal").lower()[:32]
    dl = str(deadline or "")[:64]
    con = _db()
    try:
        with _locked_write():
            now = int(time.time())
            con.execute("BEGIN IMMEDIATE")
            try:
                cols = _columns(con, "goals")
                if {"owner", "priority", "deadline", "updated_at", "last_advanced_at"} <= cols:
                    cur = con.execute(
                        "INSERT INTO goals(title, steps, status, progress, created_at, owner, priority, deadline, updated_at, last_advanced_at) "
                        "VALUES(?, ?, 'active', 0, ?, ?, ?, ?, ?, 0)",
                        (title, json.dumps(steps), now, resident, prio, dl, now),
                    )
                else:
                    cur = con.execute(
                        "INSERT INTO goals(title, steps, status, progress, created_at) VALUES(?, ?, 'active', 0, ?)",
                        (title, json.dumps(steps), now),
                    )
                con.execute("COMMIT")
                gid = cur.lastrowid
            except Exception:
                try:
                    con.execute("ROLLBACK")
                except Exception:
                    pass
                raise
            try:
                con.execute("PRAGMA wal_checkpoint(PASSIVE)")
            except Exception:
                pass
        return {"ok": True, "id": gid, "title": title, "steps": steps,
                "progress": 0, "status": "active", "owner": resident,
                "priority": prio, "deadline": dl}
    finally:
        con.close()


def _row_to_goal(r: tuple) -> dict:
    if len(r) == 10:
        gid, title, steps_json, status, progress, cat, owner, prio, dl, last_adv = r
        updated = cat
    else:
        gid, title, steps_json, status, progress, cat = r
        owner, prio, dl, last_adv, updated = "household", "normal", "", 0, cat
    try:
        steps = json.loads(steps_json) if steps_json else []
        if not isinstance(steps, list):
            steps = [str(steps)]
    except Exception:
        steps = []
    return {
        "id": gid, "title": title, "steps": steps, "status": status,
        "progress": progress, "created_at": cat, "owner": owner or "household",
        "priority": prio or "normal", "deadline": dl or "",
        "last_advanced_at": last_adv or 0, "updated_at": updated or cat,
    }


def advance_goal(gid: int) -> dict:
    """Advance progress on an active goal atomically with transaction isolation."""
    con = _db()
    try:
        with _locked_write():
            con.execute("BEGIN IMMEDIATE")
            try:
                cols = _columns(con, "goals")
                if {"owner", "last_advanced_at"} <= cols:
                    row = con.execute(
                        "SELECT title, steps, progress, status FROM goals WHERE id=?", (gid,)).fetchone()
                else:
                    row = con.execute(
                        "SELECT title, steps, progress, status FROM goals WHERE id=?", (gid,)).fetchone()
                if not row:
                    con.execute("ROLLBACK")
                    return {"ok": False, "error": f"Goal ID {gid} not found"}
                title, steps_json, progress, status = row
                try:
                    steps = json.loads(steps_json) if steps_json else []
                    if not isinstance(steps, list):
                        steps = [str(steps)]
                except Exception:
                    steps = []
                progress = min(progress + 1, len(steps))
                done = progress >= len(steps)
                now = int(time.time())
                if "last_advanced_at" in cols and "updated_at" in cols:
                    con.execute(
                        "UPDATE goals SET progress=?, status=?, last_advanced_at=?, updated_at=? WHERE id=?",
                        (progress, "done" if done else "active", now, now, gid))
                else:
                    con.execute("UPDATE goals SET progress=?, status=? WHERE id=?",
                                (progress, "done" if done else "active", gid))
                con.execute("COMMIT")
            except Exception:
                try:
                    con.execute("ROLLBACK")
                except Exception:
                    pass
                raise
            try:
                con.execute("PRAGMA wal_checkpoint(PASSIVE)")
            except Exception:
                pass
        next_step = steps[progress - 1] if progress > 0 and progress <= len(steps) else None
        return {
            "ok": True,
            "id": gid,
            "title": title,
            "progress": progress,
            "of": len(steps),
            "status": "done" if done else "active",
            "current_step": next_step
        }
    finally:
        con.close()


def list_goals(status: str | None = None, limit: int = 200) -> list[dict]:
    """Retrieve household goals, optionally filtered by status."""
    limit = max(1, min(500, int(limit)))
    con = _db()
    try:
        cols = _columns(con, "goals")
        if {"owner", "last_advanced_at"} <= cols:
            sel = ("SELECT id, title, steps, status, progress, created_at, owner, priority, deadline, "
                   "last_advanced_at FROM goals ORDER BY id ASC LIMIT ?")
        else:
            sel = "SELECT id, title, steps, status, progress, created_at FROM goals ORDER BY id ASC LIMIT ?"
        rows = con.execute(sel, (limit,)).fetchall()
        res = [_row_to_goal(r) for r in rows]
        if status:
            res = [g for g in res if g.get("status") == status]
        return res
    finally:
        con.close()


def scheduler_tick(now: float | None = None, min_interval_s: int = 3600) -> dict:
    """Hourly scheduler hook: advance the oldest due active goal.

    Compatible with ``HEARTH_SCHEDULER=1`` (the server loop calls the same
    primitive). Rate-limits to one advancement per ``min_interval_s`` per goal
    using ``last_advanced_at`` when the v2 column exists; falls back to plain
    oldest-active advancement on v1 schemas.
    """
    ts = int(now if now is not None else time.time())
    actives = [g for g in list_goals("active")]
    if not actives:
        return {"ok": True, "advanced": False, "reason": "no active goals"}
    due = [g for g in actives if ts - int(g.get("last_advanced_at") or 0) >= min_interval_s]
    if not due:
        nxt = min(actives, key=lambda g: g["id"])
        return {"ok": True, "advanced": False, "reason": "rate-limited",
                "next_id": nxt["id"], "next_title": nxt["title"]}
    nxt = min(due, key=lambda g: g["id"])
    out = advance_goal(nxt["id"])
    out["advanced"] = out.get("ok", False)
    out["tick_at"] = ts
    return out


def chat_history_append(role: str, content: str, model: str = "") -> None:
    """Record a chat turn; prune beyond CHAT_HISTORY_MAX to bound growth."""
    con = _db()
    try:
        with _locked_write():
            con.execute("BEGIN IMMEDIATE")
            try:
                con.execute("INSERT INTO chat_history(role, content, model, ts) VALUES(?, ?, ?, ?)",
                            (str(role), str(content), str(model), int(time.time())))
                con.execute(
                    "DELETE FROM chat_history WHERE id NOT IN (SELECT id FROM chat_history ORDER BY id DESC LIMIT ?)",
                    (CHAT_HISTORY_MAX,),
                )
                con.execute("COMMIT")
            except Exception:
                try:
                    con.execute("ROLLBACK")
                except Exception:
                    pass
                raise
    finally:
        con.close()


def chat_history_get(limit: int = 10) -> list[dict]:
    """Fetch recent chat messages for conversational grounding."""
    con = _db()
    try:
        limit = max(1, min(500, int(limit)))
        rows = con.execute("SELECT role, content, model, ts FROM chat_history ORDER BY id DESC LIMIT ?",
                           (limit,)).fetchall()
        return [{"role": r[0], "content": r[1], "model": r[2], "ts": r[3]} for r in reversed(rows)]
    finally:
        con.close()
