"""Crash-safe file primitives: inter-process locking + atomic writes.
State files (proposals, home twin, audit chain) stay consistent even if two
requests — or two server processes — write at the same moment.
"""
from __future__ import annotations

import fcntl
import os
import threading
import uuid
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any

_HELD_LOCKS: dict[tuple[int, str], int] = {}
_LOCK = threading.Lock()


@contextmanager
def locked(path: Path):
    """Hold an exclusive advisory lock while mutating a state file.

    Reentrant within the same thread (nested calls do not self-deadlock);
    other threads in this process still block on the flock, so mutual
    exclusion holds across threads and processes.
    """
    path = Path(path).resolve()
    key = (threading.get_ident(), str(path))
    with _LOCK:
        if _HELD_LOCKS.get(key, 0) > 0:
            _HELD_LOCKS[key] += 1
            is_reentrant = True
        else:
            _HELD_LOCKS[key] = 1
            is_reentrant = False

    if is_reentrant:
        try:
            yield
        finally:
            with _LOCK:
                _HELD_LOCKS[key] -= 1
                if _HELD_LOCKS[key] <= 0:
                    _HELD_LOCKS.pop(key, None)
        return

    lf = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        lf = open(str(path) + ".lock", "w")  # noqa: SIM115 — held open across the yield
        fcntl.flock(lf, fcntl.LOCK_EX)
    except BaseException:
        # Acquisition failed: roll the refcount back so the next call takes a
        # real lock instead of believing it is reentrant (adversarial pass, P2#11).
        if lf is not None:
            with suppress(Exception):
                lf.close()
        with _LOCK:
            _HELD_LOCKS[key] -= 1
            if _HELD_LOCKS[key] <= 0:
                _HELD_LOCKS.pop(key, None)
        raise
    try:
        yield
    finally:
        try:
            fcntl.flock(lf, fcntl.LOCK_UN)
        finally:
            lf.close()
            with _LOCK:
                _HELD_LOCKS[key] -= 1
                if _HELD_LOCKS[key] <= 0:
                    _HELD_LOCKS.pop(key, None)


def atomic_write_text(path: Path, text: str) -> None:
    """Write crash-safely: temp file + rename, never a half-written state file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + f".tmp.{os.getpid()}.{uuid.uuid4().hex[:8]}"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON data crash-safely via atomic rename."""
    import json
    atomic_write_text(path, json.dumps(data, indent=2))


