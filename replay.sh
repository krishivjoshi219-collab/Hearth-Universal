#!/usr/bin/env bash
# Judge one-command deterministic replay (no keys, no network).
set -e
cd "$(dirname "$0")"
python3 scripts/replay.py --seed 42
