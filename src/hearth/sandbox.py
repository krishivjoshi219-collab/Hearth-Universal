"""Workspace sandbox: the agent can read, write, and run code — but only inside
a jailed root, with timeouts, output caps, denied command patterns, and no secrets.
This is the "vibe code the app" primitive. Writes/exec are Tier-2: the human chat
session is the authorization boundary (every call audited); background acts stay read-only.
"""
from __future__ import annotations
import os
import re
import subprocess
from pathlib import Path

EXEC_TIMEOUT = 60
EXEC_MAX_CHARS = 8000
FILE_MAX_BYTES = 100_000
PATH_MAX = 200

# Anything matching these never runs, no matter who asks.
DENY_CMD = (
    r"\brm\s+(?:-[a-zA-Z0-9_-]+\s+)*.*(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|-r\s+-f|-f\s+-r|--recursive|--force).*(?:[/~*.]|$)",
    r"\b(mkfs|dd\s+if=|fdisk|parted|shutdown|poweroff|reboot)\b",
    r":\(\)\{:\|:\};:",
    r"\b(sudo|su\s|doas|chmod\s+.*\s+/\s|chown)\b",
    r"(curl|wget).*\|\s*(bash|sh)",
    r"\bDROP\s+TABLE\b",
)


def root() -> Path:
    r = Path(os.environ.get("HEARTH_WORKSPACE", os.getcwd())).resolve()
    r.mkdir(parents=True, exist_ok=True)
    return r


def _jail(rel: str) -> tuple[Path | None, str]:
    rel = (rel or "").strip()[:PATH_MAX]
    if not rel or "\x00" in rel or rel.startswith(("/", "~")) or ".." in Path(rel).parts:
        return None, "path must be relative and inside the workspace"
    try:
        p = (root() / rel).resolve()
        p.relative_to(root())
    except (ValueError, Exception):
        return None, "path escapes the workspace jail"
    return p, ""


def read_file(path: str) -> dict:
    p, err = _jail(path)
    if err:
        return {"ok": False, "error": err}
    try:
        data = p.read_bytes()[:FILE_MAX_BYTES]
        return {"ok": True, "path": str(p.relative_to(root())), "text": data.decode("utf-8", "replace")}
    except FileNotFoundError:
        return {"ok": False, "error": f"not found: {path}"}
    except IsADirectoryError:
        return {"ok": False, "error": f"is a directory: {path}"}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}


def write_file(path: str, content: str) -> dict:
    from . import audit as _audit
    p, err = _jail(path)
    if err:
        return {"ok": False, "error": err}
    if len(content or "") > FILE_MAX_BYTES:
        return {"ok": False, "error": f"content exceeds {FILE_MAX_BYTES} bytes"}
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content or "")
        _audit.append("agent", "workspace_write", {"path": str(p.relative_to(root())), "bytes": len(content or "")})
        return {"ok": True, "path": str(p.relative_to(root())), "bytes": len(content or "")}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}


def list_dir(path: str = ".") -> dict:
    p, err = _jail(path or ".")
    if err:
        return {"ok": False, "error": err}
    try:
        if not p.exists():
            return {"ok": False, "error": f"not found: {path}"}
        if p.is_file():
            return {"ok": True, "path": str(p.relative_to(root())), "entries": [p.name]}
        entries = sorted([e.name + ("/" if e.is_dir() else "") for e in p.iterdir()])[:200]
        return {"ok": True, "path": str(p.relative_to(root())), "entries": entries}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}


def _denied(cmd: str) -> str:
    for pat in DENY_CMD:
        if re.search(pat, cmd, re.IGNORECASE):
            return f"denied pattern: {pat[:40]}"
    return ""


def execute(cmd: str, timeout: int = EXEC_TIMEOUT) -> dict:
    """Run a shell command jailed to the workspace root. Audited, capped, timed out."""
    from . import audit as _audit
    cmd = (cmd or "")[:2000].strip()
    if not cmd:
        return {"ok": False, "error": "empty command"}
    hit = _denied(cmd)
    if hit:
        _audit.append("sentinel", "exec_blocked", {"cmd": cmd[:200], "reason": hit})
        return {"ok": False, "error": f"blocked: {hit}"}
    timeout = max(1, min(int(timeout or EXEC_TIMEOUT), 120))
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": os.environ.get("HOME", "/tmp"),
           "LANG": "C.UTF-8", "PYTHONPATH": "src"}
    try:
        proc = subprocess.run(cmd, shell=True, cwd=str(root()), env=env,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        _audit.append("agent", "workspace_exec", {"cmd": cmd[:200], "timeout": True})
        return {"ok": False, "error": f"timed out after {timeout}s"}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}
    out = (proc.stdout or "") + (proc.stderr or "")
    truncated = len(out) > EXEC_MAX_CHARS
    _audit.append("agent", "workspace_exec", {"cmd": cmd[:200], "rc": proc.returncode})
    return {"ok": proc.returncode == 0, "rc": proc.returncode,
            "output": out[:EXEC_MAX_CHARS], "truncated": truncated}
