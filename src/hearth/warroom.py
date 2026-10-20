"""Direct Inter-Agent War Room IPC & MCP Layer.

Provides structured, real-time message bus between Antigravity (Gemini)
and OpenCode (DeepSeek) via FastMCP tools, REST endpoints, and disk-backed logs.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import atomic

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
STATE_DIR = ROOT_DIR / "state"
IPC_LOG = STATE_DIR / "warroom_ipc.jsonl"
DISCUSSION_MD = ROOT_DIR / "discussion.md"

_WARROOM_LOCK = threading.Lock()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def send_message(
    sender: str,
    message: str,
    topic: str = "general",
    metadata: dict[str, Any] | None = None,
    sync_to_discussion: bool = True,
) -> dict[str, Any]:
    """Send an inter-agent message, logging to warroom_ipc.jsonl and optionally syncing to discussion.md."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    msg_id = str(uuid.uuid4())[:8]
    ts = _now_iso()

    entry = {
        "id": msg_id,
        "timestamp": ts,
        "sender": sender.strip().lower(),
        "topic": topic.strip().lower(),
        "content": message.strip(),
        "metadata": metadata or {},
    }

    # 1. Append to structured JSONL IPC log atomically
    line = json.dumps(entry) + "\n"
    with _WARROOM_LOCK, atomic.locked(str(IPC_LOG)), open(IPC_LOG, "a", encoding="utf-8") as f:
        f.write(line)

    # 2. Optionally append to discussion.md cleanly
    if sync_to_discussion and DISCUSSION_MD.exists():
        sender_title = sender.strip().capitalize()
        badge = "🤖 [MCP-BUS]"
        entry_text = (
            f"\n\n---\n\n"
            f"### {badge} {sender_title} ({topic.upper()}) · `{msg_id}`\n"
            f"**Time:** {ts} · **Via:** Direct MCP Layer\n\n"
            f"{message.strip()}\n"
        )
        try:
            with _WARROOM_LOCK, atomic.locked(str(DISCUSSION_MD)), open(DISCUSSION_MD, "a", encoding="utf-8") as f:
                f.write(entry_text)
        except Exception:
            pass

    return {"ok": True, "id": msg_id, "timestamp": ts, "delivered": True}


def get_messages(since_timestamp: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Retrieve recent inter-agent messages from the IPC log."""
    if not IPC_LOG.exists():
        return []

    messages: list[dict[str, Any]] = []
    try:
        with _WARROOM_LOCK, atomic.locked(str(IPC_LOG)):
            lines = IPC_LOG.read_text(encoding="utf-8").strip().splitlines()
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                if since_timestamp and item.get("timestamp", "") <= since_timestamp:
                    continue
                messages.append(item)
                if len(messages) >= limit:
                    break
            except Exception:
                continue
    except Exception:
        return []

    return list(reversed(messages))


def get_warroom_status() -> dict[str, Any]:
    """Return high-level status of the two-agent war room."""
    film_path = ROOT_DIR / "demo_film" / "HEARTH_DEMO_FINAL.mp4"
    film_stats = {}
    if film_path.exists():
        film_stats = {
            "exists": True,
            "size_bytes": film_path.stat().st_size,
            "size_mb": round(film_path.stat().st_size / (1024 * 1024), 2),
        }
    else:
        film_stats = {"exists": False}

    recent = get_messages(limit=5)

    return {
        "status": "active",
        "mcp_layer_version": "1.0.0",
        "timestamp": _now_iso(),
        "film": film_stats,
        "recent_messages_count": len(recent),
        "latest_message": recent[-1] if recent else None,
        "agents": {
            "antigravity": {"model": "Gemini 3.8 Flash High", "role": "Product & Presentation Lead"},
            "opencode": {"model": "DeepSeek V4.1 Flash", "role": "Backend & Security Lead"},
        },
    }
