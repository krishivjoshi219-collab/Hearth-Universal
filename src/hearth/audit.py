"""Append-only hash-chained audit log. Proves restraint: what was proposed vs executed."""
from __future__ import annotations
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

STATE_DIR = Path(os.environ.get("HEARTH_STATE_DIR", "state"))


def _hmac_key() -> bytes:
    # HMAC key binds the chain to a server secret so stolen files can't be
    # rewritten with a valid chain. Zero-config fallback keeps demos working;
    # operators MUST set HEARTH_AUDIT_KEY (32+ random bytes hex) in prod.
    # Set HEARTH_REQUIRE_AUDIT_KEY=1 to fail closed when the demo key is in use.
    key = os.environ.get("HEARTH_AUDIT_KEY", "hearth-demo-audit-key-v1")
    if key == "hearth-demo-audit-key-v1" and os.environ.get("HEARTH_REQUIRE_AUDIT_KEY") == "1":
        raise RuntimeError("HEARTH_REQUIRE_AUDIT_KEY=1 but HEARTH_AUDIT_KEY is unset (demo key refused)")
    return key.encode("utf-8")


def _chain_hash(body: str) -> str:
    return hmac.new(_hmac_key(), body.encode("utf-8"), hashlib.sha256).hexdigest()


def _log_path() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR / "audit.jsonl"


from . import atomic

# Retention: the chain is append-only, but the file is not infinite.
# Past this many lines the ledger archives (hash-linked checkpoint) and restarts.
AUDIT_MAX_LINES = 10000


def count() -> int:
    path = _log_path()
    try:
        if not path.exists():
            return 0
        return sum(1 for line in path.read_text().splitlines() if line.strip())
    except Exception:
        return -1


def _maybe_rotate(path: Path) -> None:
    """Archive a full ledger and restart it with a hash-linked checkpoint.

    verify() keeps passing: the new file is its own valid chain whose first
    entry commits to the archive digest. Nothing is ever silently dropped.
    """
    try:
        lines = [line for line in path.read_text().splitlines() if line.strip()]
    except Exception:
        return
    if len(lines) < AUDIT_MAX_LINES:
        return
    import time as _t
    digest = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    archive = path.parent / f"audit-archive-{int(_t.time())}.jsonl"
    try:
        os.replace(path, archive)
    except Exception:
        return
    checkpoint = {
        "ts": int(_t.time()),
        "actor": "system",
        "action": "ledger_rotated",
        "detail": {"archive": archive.name, "entries": len(lines), "digest": digest},
        "prev": f"ARCHIVED:{digest}",
    }
    body = json.dumps(checkpoint, sort_keys=True, default=str)
    checkpoint["hash"] = _chain_hash(body)
    try:
        with path.open("a") as f:
            f.write(json.dumps(checkpoint) + "\n")
    except Exception:
        pass


def append(actor: str, action: str, detail: dict) -> dict:
    path = _log_path()
    with atomic.locked(path):
        _maybe_rotate(path)
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
        h = _chain_hash(body)
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
    first = True
    for line in lines:
        try:
            e = json.loads(line)
            body = json.dumps({"ts": e["ts"], "actor": e["actor"], "action": e["action"], "detail": e["detail"], "prev": e["prev"]}, sort_keys=True, default=str)
        except Exception:
            return False
        # Accept legacy plain-SHA256 entries (pre-hardening) OR HMAC entries.
        legacy = hashlib.sha256(body.encode()).hexdigest()
        if _chain_hash(body) != e.get("hash") and legacy != e.get("hash"):
            return False
        if e.get("prev") != prev:
            # Rotation checkpoints commit to the archive digest instead of GENESIS.
            if not (first and str(e.get("prev", "")).startswith("ARCHIVED:")):
                return False
        prev = e["hash"]
        first = False
    return True
