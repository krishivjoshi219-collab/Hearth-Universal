#!/usr/bin/env python3
"""CLI interface for the Direct Inter-Agent War Room MCP Layer.

Usage:
  python3 scripts/warroom_cli.py --from opencode --msg "Hey Gemini, film looks clean."
  python3 scripts/warroom_cli.py --inbox
  python3 scripts/warroom_cli.py --status
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hearth import warroom  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Inter-Agent War Room CLI")
    parser.add_argument("--from", dest="sender", default="agent", help="Sender identifier (e.g. opencode, gemini)")
    parser.add_argument("--msg", dest="message", help="Message content to broadcast")
    parser.add_argument("--file", dest="file_path", help="Path to text file containing message to broadcast")
    parser.add_argument("--stdin", action="store_true", help="Read message content from stdin")
    parser.add_argument("--topic", default="general", help="Topic (e.g. film, presentation, security)")
    parser.add_argument("--inbox", action="store_true", help="View recent inbox messages")
    parser.add_argument("--status", action="store_true", help="View War Room status")
    parser.add_argument("--limit", type=int, default=10, help="Inbox message limit")
    parser.add_argument("--no-sync", action="store_true", help="Do not append to discussion.md")

    args = parser.parse_args()

    if args.status:
        st = warroom.get_warroom_status()
        print(json.dumps(st, indent=2))
        return

    if args.inbox:
        msgs = warroom.get_messages(limit=args.limit)
        print(f"=== WAR ROOM INBOX ({len(msgs)} messages) ===")
        for m in msgs:
            print(f"[{m.get('timestamp')}] <{m.get('sender')}> ({m.get('topic')}): {m.get('content')}")
        return

    msg_content = args.message
    if args.stdin:
        msg_content = sys.stdin.read().strip()
    elif args.file_path:
        msg_content = Path(args.file_path).read_text(encoding="utf-8").strip()

    if msg_content:
        res = warroom.send_message(
            sender=args.sender,
            message=msg_content,
            topic=args.topic,
            sync_to_discussion=not args.no_sync,
        )
        print(f"✓ Message delivered: ID={res.get('id')} at {res.get('timestamp')}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
