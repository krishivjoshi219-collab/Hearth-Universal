"""Append-only hash-chained audit log. Proves restraint: what was proposed vs executed."""
from __future__ import annotations
import hashlib
import json
import os
import time
from pathlib import Path

STATE_DIR = Path(os.environ.get("HEARTH_STATE_DIR", "state"))


def _log_path() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR / "audit.jsonl"


from . import atomic


def append(actor: str, action: str, detail: dict) -> dict:
    path = _log_path()
    with atomic.locked(path):
        prev = "GENESIS"
        if path.exists():
            try:
                lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
                for line in reversed(lines):
                    try:
                        e = json.loads(line)
                        if isinstance(e, dict) and "hash" in e:
                            prev = e["hash"]
                            break
                    except Exception:
                        continue
            except Exception:
                prev = "GENESIS"
        ts = int(time.time())
        try:
            body = json.dumps({"ts": ts, "actor": str(actor), "action": str(action), "detail": detail, "prev": prev}, sort_keys=True, default=str)
            safe_detail = json.loads(json.dumps(detail, default=str))
        except Exception:
            safe_detail = {"value": str(detail)}
            body = json.dumps({"ts": ts, "actor": str(actor), "action": str(action), "detail": safe_detail, "prev": prev}, sort_keys=True, default=str)
        h = hashlib.sha256(body.encode()).hexdigest()
        entry = {"ts": ts, "actor": str(actor), "action": str(action), "detail": safe_detail, "prev": prev, "hash": h}
        with path.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    return entry


def verify() -> bool:
    path = _log_path()
    if not path.exists():
        return True
    try:
        lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    except Exception:
        return False
    if not lines:
        return True
    prev = "GENESIS"
    for line in lines:
        try:
            e = json.loads(line)
            body = json.dumps({"ts": e["ts"], "actor": e["actor"], "action": e["action"], "detail": e["detail"], "prev": e["prev"]}, sort_keys=True, default=str)
        except Exception:
            return False
        if hashlib.sha256(body.encode()).hexdigest() != e.get("hash"):
            return False
        if e.get("prev") != prev:
            return False
        prev = e["hash"]
    return True
