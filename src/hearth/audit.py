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


def append(actor: str, action: str, detail: dict) -> dict:
    path = _log_path()
    prev = "GENESIS"
    if path.exists():
        try:
            last = path.read_text().strip().splitlines()[-1]
            prev = json.loads(last).get("hash", "GENESIS")
        except Exception:
            prev = "GENESIS"
    ts = int(time.time())
    body = json.dumps({"ts": ts, "actor": actor, "action": action, "detail": detail, "prev": prev}, sort_keys=True)
    h = hashlib.sha256(body.encode()).hexdigest()
    entry = {"ts": ts, "actor": actor, "action": action, "detail": detail, "prev": prev, "hash": h}
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def verify() -> bool:
    path = _log_path()
    if not path.exists():
        return True
    prev = "GENESIS"
    for line in path.read_text().splitlines():
        e = json.loads(line)
        body = json.dumps({"ts": e["ts"], "actor": e["actor"], "action": e["action"], "detail": e["detail"], "prev": e["prev"]}, sort_keys=True)
        if hashlib.sha256(body.encode()).hexdigest() != e["hash"]:
            return False
        if e["prev"] != prev:
            return False
        prev = e["hash"]
    return True
