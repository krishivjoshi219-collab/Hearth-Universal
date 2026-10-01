#!/usr/bin/env bash
# One-command brain switching for Hearth Universal.
# Usage:
#   scripts/use-brain.sh local              # zero-config offline engine (default, judge-safe)
#   scripts/use-brain.sh ollama [model]     # real local LLM, no accounts/keys (needs `ollama serve`)
#   scripts/use-brain.sh openai             # cloud key (needs VAULT_MODEL_KEY, see docs/cloud-brains.md)
#   scripts/use-brain.sh bedrock            # AWS Bedrock (needs boto3 + AWS creds, see docs/cloud-brains.md)
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-local}"

# Never leak harness/CI keys into a local Ollama run; explicit keys still win.
unset OPENAI_API_KEY VAULT_MODEL_KEY 2>/dev/null || true
if [ -n "${USER_VAULT_KEY:-}" ]; then export VAULT_MODEL_KEY="$USER_VAULT_KEY"; fi

case "$MODE" in
  local)
    echo "brain=local (deterministic offline engine, exact numbers)"
    exec python3 mcp-server/server.py
    ;;
  ollama)
    MODEL="${2:-qwen2.5-coder:1.5b}"
    curl -s --max-time 5 http://localhost:11434/api/tags >/dev/null \
      || { echo "ERROR: ollama not running. Start it first:  ollama serve"; exit 1; }
    /home/k/bin/ollama list 2>/dev/null | grep -q "${MODEL%%:*}" \
      || { echo "ERROR: model '$MODEL' not downloaded. Run:  ollama pull $MODEL"; exit 1; }
    echo "brain=ollama ($MODEL, genuine local LLM — may paraphrase telemetry on small models)"
    export HEARTH_BRAIN_PROVIDER=openai HEARTH_BASE_URL=http://localhost:11434/v1 HEARTH_MODEL="$MODEL"
    exec python3 mcp-server/server.py
    ;;
  openai)
    [ -n "${VAULT_MODEL_KEY:-}" ] \
      || { echo "ERROR: set VAULT_MODEL_KEY first (see docs/cloud-brains.md for free keys)"; exit 1; }
    export HEARTH_BRAIN_PROVIDER=openai
    export HEARTH_BASE_URL="${HEARTH_BASE_URL:-https://api.openai.com/v1}"
    export HEARTH_MODEL="${HEARTH_MODEL:-gpt-4o-mini}"
    echo "brain=openai-compatible ($HEARTH_BASE_URL model=$HEARTH_MODEL)"
    exec python3 mcp-server/server.py
    ;;
  bedrock)
    python3 -c "import boto3" 2>/dev/null \
      || { echo "ERROR: boto3 missing. Run:  pip install boto3"; exit 1; }
    [ -n "${AWS_ACCESS_KEY_ID:-}" ] \
      || { echo "ERROR: AWS creds missing (AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY). See docs/cloud-brains.md"; exit 1; }
    export AWS_BEDROCK_ENABLED=1
    echo "brain=bedrock (model=${AWS_BEDROCK_MODEL:-default})"
    exec python3 mcp-server/server.py
    ;;
  *)
    echo "unknown mode: $MODE (local|ollama|openai|bedrock)"; exit 1
    ;;
esac
