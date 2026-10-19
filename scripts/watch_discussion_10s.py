#!/usr/bin/env python3
"""10-Second Watcher Heartbeat for Hearth War Room (discussion.md).

Monitors discussion.md every 10 seconds continuously.
Detects modifications, logs new turns, and verifies war room momentum.
"""
import hashlib
import os
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DISCUSSION_FILE = REPO_ROOT / "discussion.md"
LOG_FILE = REPO_ROOT / ".watcher_10s.log"

def get_file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def log(msg: str):
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] [WATCHER-10S] {msg}\n"
    print(entry, end="", flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(entry)

def main():
    log("Starting 10-second discussion.md heartbeat watcher daemon.")
    last_hash = get_file_hash(DISCUSSION_FILE)
    last_size = DISCUSSION_FILE.stat().st_size if DISCUSSION_FILE.exists() else 0
    poll_count = 0

    while True:
        try:
            time.sleep(10)
            poll_count += 1
            if not DISCUSSION_FILE.exists():
                log("WARNING: discussion.md not found.")
                continue

            current_size = DISCUSSION_FILE.stat().st_size
            current_hash = get_file_hash(DISCUSSION_FILE)

            if current_hash != last_hash:
                delta = current_size - last_size
                log(f"⚡ DISCUSSION UPDATED! Delta: {delta:+d} bytes (Total: {current_size} bytes). Polling count: {poll_count}")
                # Inspect last 15 lines of discussion.md
                lines = DISCUSSION_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
                recent_snippet = "\n".join(lines[-8:]) if lines else ""
                log(f"Recent tail snippet:\n---\n{recent_snippet}\n---")
                last_hash = current_hash
                last_size = current_size
            else:
                # Heartbeat every 6 polls (1 minute) to keep logs clean but verifiable
                if poll_count % 6 == 0:
                    log(f"Heartbeat OK: discussion.md stable at {current_size} bytes (Poll #{poll_count}).")

        except Exception as e:
            log(f"Watcher error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
