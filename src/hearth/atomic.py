"""Crash-safe file primitives: inter-process locking + atomic writes.
State files (proposals, home twin, audit chain) stay consistent even if two
requests — or two server processes — write at the same moment.
"""
from __future__ import annotations
import fcntl
import os
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def locked(path: Path):
    """Hold an exclusive advisory lock while mutating a state file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path) + ".lock", "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def atomic_write_text(path: Path, text: str) -> None:
    """Write crash-safely: temp file + rename, never a half-written state file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, path)
