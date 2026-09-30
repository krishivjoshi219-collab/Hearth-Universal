"""Household memory: SQLite, editable, exportable, multi-turn history.
Maintains persistent facts, long-running household goals, and conversation context.
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
"""

# Product guardrails: bound stored sizes and history length.
KEY_MAX = 128
VALUE_MAX = 8000
GOAL_TITLE_MAX = 200
GOAL_STEPS_MAX = 20
CHAT_HISTORY_MAX = 500


def _cap(text: str, maximum: int) -> tuple[str, bool]:
    if len(text) <= maximum:
        return text, False
    return text[:maximum], True


DEFAULT_FACTS = [
    ("dietary_preference", "Gluten-free dinners on weekdays; kid loves oatmeal and berries", "household"),
    ("budget_entertainment_limit", "$200/month across streaming, games, and dining out", "household"),
    ("night_climate_setpoint", "19.5°C in master bedroom with silent eco-fan", "household"),
    ("preferred_coffee_roast", "Organic Arabica whole bean medium roast", "household"),
    ("emergency_contact", "Dr. Sarah Miller (555-0192)", "household"),
]


def _db() -> sqlite3.Connection:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    db_path = STATE_DIR / "memory.db"
    try:
        con = sqlite3.connect(db_path, timeout=30)
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(SCHEMA)
    except sqlite3.DatabaseError:
        # Corrupt database: quarantine it and start fresh instead of
        # failing every request until someone SSHes in.
        try:
            os.replace(db_path, STATE_DIR / f"memory.corrupt.{int(time.time())}.db")
        except Exception:
            pass
        con = sqlite3.connect(db_path, timeout=30)
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(SCHEMA)
    
    # Auto-migrate older schemas
    try:
        con.execute("ALTER TABLE facts ADD COLUMN updated_at INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
        
    try:
        con.execute("ALTER TABLE goals ADD COLUMN created_at INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Populate defaults if facts table has no rows
    count = con.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    now = int(time.time())
    if count == 0:
        for k, v, o in DEFAULT_FACTS:
            con.execute("INSERT OR IGNORE INTO facts(key, value, owner, updated_at) VALUES (?, ?, ?, ?)", (k, v, o, now))

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
            "INSERT OR IGNORE INTO goals(id, title, steps, status, progress, created_at) VALUES (1, ?, ?, 'active', 1, ?)",
            ("Cut Monthly Household Utility & Subscription Spend by 20%", initial_steps, now)
        )
    con.commit()
    return con


def remember(key: str, value: str, owner: str = "household") -> dict:
    """Store or update a household fact (length-capped)."""
    key, k_trunc = _cap(str(key), KEY_MAX)
    value, v_trunc = _cap(str(value), VALUE_MAX)
    con = _db()
    now = int(time.time())
    con.execute("INSERT OR REPLACE INTO facts(key, value, owner, updated_at) VALUES(?, ?, ?, ?)", (key, value, owner, now))
    con.commit()
    con.close()
    out = {"ok": True, "key": key, "value": value, "owner": owner}
    if k_trunc or v_trunc:
        out["truncated"] = True
    return out


def query(q: str = "") -> list[dict]:
    """Query stored household facts (% and _ treated literally, not as wildcards)."""
    con = _db()
    if q:
        q_esc = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{q_esc}%"
        rows = con.execute(
            "SELECT key, value, owner FROM facts WHERE key LIKE ? ESCAPE '\\' OR value LIKE ? ESCAPE '\\'",
            (like, like)).fetchall()
    else:
        rows = con.execute("SELECT key, value, owner FROM facts ORDER BY updated_at DESC").fetchall()
    con.close()
    return [{"key": k, "value": v, "owner": o} for k, v, o in rows]


def delete(key: str) -> dict:
    """Remove a fact from household memory."""
    con = _db()
    cur = con.execute("DELETE FROM facts WHERE key=?", (key,))
    con.commit()
    affected = cur.rowcount
    con.close()
    return {"ok": affected > 0, "key": key}


def create_goal(title: str, steps: list[str]) -> dict:
    """Create a multi-step household goal (title/steps capped)."""
    title, _ = _cap(str(title), GOAL_TITLE_MAX)
    steps = [s for s in steps][:GOAL_STEPS_MAX] or ["step 1"]
    con = _db()
    now = int(time.time())
    cur = con.execute("INSERT INTO goals(title, steps, status, progress, created_at) VALUES(?, ?, 'active', 0, ?)", (title, json.dumps(steps), now))
    con.commit()
    gid = cur.lastrowid
    con.close()
    return {"ok": True, "id": gid, "title": title, "steps": steps, "progress": 0, "status": "active"}


def advance_goal(gid: int) -> dict:
    """Advance progress on an active goal."""
    con = _db()
    row = con.execute("SELECT title, steps, progress, status FROM goals WHERE id=?", (gid,)).fetchone()
    if not row:
        con.close()
        return {"ok": False, "error": f"Goal ID {gid} not found"}
    title, steps_json, progress, status = row
    steps = json.loads(steps_json)
    progress = min(progress + 1, len(steps))
    done = progress >= len(steps)
    con.execute("UPDATE goals SET progress=?, status=? WHERE id=?", (progress, "done" if done else "active", gid))
    con.commit()
    con.close()
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


def list_goals() -> list[dict]:
    """Retrieve all household goals."""
    con = _db()
    rows = con.execute("SELECT id, title, steps, status, progress, created_at FROM goals ORDER BY id ASC").fetchall()
    con.close()
    res = []
    for r in rows:
        gid, title, steps_json, status, progress, cat = r
        try:
            steps = json.loads(steps_json)
        except Exception:
            steps = []
        res.append({
            "id": gid,
            "title": title,
            "steps": steps,
            "status": status,
            "progress": progress,
            "created_at": cat
        })
    return res


def chat_history_append(role: str, content: str, model: str = "") -> None:
    """Record a chat turn; prune beyond CHAT_HISTORY_MAX to bound growth."""
    con = _db()
    con.execute("INSERT INTO chat_history(role, content, model, ts) VALUES(?, ?, ?, ?)", (role, content, model, int(time.time())))
    con.execute(
        "DELETE FROM chat_history WHERE id NOT IN (SELECT id FROM chat_history ORDER BY id DESC LIMIT ?)",
        (CHAT_HISTORY_MAX,),
    )
    con.commit()
    con.close()


def chat_history_get(limit: int = 10) -> list[dict]:
    """Fetch recent chat messages for conversational grounding."""
    con = _db()
    rows = con.execute("SELECT role, content, model, ts FROM chat_history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    con.close()
    return [{"role": r[0], "content": r[1], "model": r[2], "ts": r[3]} for r in reversed(rows)]
