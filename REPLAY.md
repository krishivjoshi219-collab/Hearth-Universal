# Deterministic Replay: Re-Run Our Numbers

> Every demo number in the video is reproducible. No keys, no network.

```bash
./replay.sh   # == python3 scripts/replay.py --seed 42
```

Output: `replay identical: seed=42 sha=<git> (6 engines, semantic outputs match golden)`.

## What it proves

`scripts/replay.py` re-executes all 6 stochastic engines with fixed seeds
(`PYTHONHASHSEED` + `random` + `numpy` + `HEARTH_SEED`) in an isolated state
dir and compares **semantic outputs** (verdicts, Nash scores, savings,
quantiles — not random IDs/timestamps) against the committed golden
`replays/golden.json`.

## Honest variance contract

- 5 engines are fully seed-invariant (parliament, forensics, acoustic,
  mediation, swarm): same outputs on any seed.
- The twin is Monte Carlo: `--seed 7` moves pantry probabilities ±1 and
  savings $106.36 → $106.05. Same hazards, same decisions. That's a real
  stochastic simulator, not a recording.
