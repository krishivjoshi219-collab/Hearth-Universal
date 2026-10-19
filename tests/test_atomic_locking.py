"""Regression tests for hearth.atomic locking: reentrancy + cross-thread exclusion."""
from __future__ import annotations

import threading
import time

from hearth import atomic


def test_locked_is_reentrant_within_one_thread(tmp_path):
    """Nested locked() calls in the same thread must not self-deadlock."""
    p = tmp_path / "state.json"
    with atomic.locked(p):  # noqa: SIM117 — deliberate nested reentrancy test
        with atomic.locked(p):
            atomic.atomic_write_text(p, "ok")
    assert p.read_text(encoding="utf-8") == "ok"
    assert not atomic._HELD_LOCKS, "lock refcounts must be cleaned up"


def test_locked_serializes_across_threads(tmp_path):
    """Two threads must never sit inside the same critical section at once,
    and a read-modify-write under the lock must not lose updates."""
    p = tmp_path / "counter.txt"
    atomic.atomic_write_text(p, "0")
    inside = {"now": 0, "max": 0}
    guard = threading.Lock()

    def worker():
        for _ in range(15):
            with atomic.locked(p):
                with guard:
                    inside["now"] += 1
                    inside["max"] = max(inside["max"], inside["now"])
                val = int(p.read_text(encoding="utf-8"))
                time.sleep(0.001)
                atomic.atomic_write_text(p, str(val + 1))
                with guard:
                    inside["now"] -= 1

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert inside["max"] == 1, "two threads were inside the lock at the same time"
    assert int(p.read_text(encoding="utf-8")) == 60, "increments were lost to a race"
    assert not atomic._HELD_LOCKS, "lock refcounts must be cleaned up"


def test_lock_acquisition_failure_does_not_leak_refcount(tmp_path):
    """A failed flock acquisition must roll back the reentrancy refcount;
    otherwise the next locked() call in this thread silently skips locking."""
    p = tmp_path / "guarded.txt"
    blocker = tmp_path / "guarded.txt.lock"
    blocker.mkdir()
    try:
        with atomic.locked(p):
            raise AssertionError("expected the lock acquisition to fail")
    except OSError:
        pass
    assert not atomic._HELD_LOCKS, "failed acquisition leaked a refcount"
    blocker.rmdir()
    with atomic.locked(p):
        atomic.atomic_write_text(p, "ok")
    assert p.read_text(encoding="utf-8") == "ok"
    assert not atomic._HELD_LOCKS
