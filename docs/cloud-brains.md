# Cloud brains: what I set up vs what needs your hands

Done automatically: **Ollama live-LLM mode** — `scripts/use-brain.sh ollama` runs the
full agent on a genuine local model (`qwen2.5-coder:1.5b`, already on disk, no keys,
no accounts, no bills). Verified end-to-end: real model synthesis from live tool data.

Honest tradeoff I measured: tiny local models reason genuinely but can paraphrase
telemetry (e.g. converting °C→°F unprompted). The default `local` engine stays
deterministic and numerically exact — keep it for the judged video; use Ollama or
cloud for the "real LLM" story.

## Paths that need YOU in a browser (I cannot sign you up)

### A. Free cloud key, no card (recommended, ~5 min)
1. **Google AI Studio:** https://aistudio.google.com → Get API key (free tier, no card).
   ```bash
   export VAULT_MODEL_KEY=<your-key>
   export HEARTH_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
   export HEARTH_MODEL=gemini-2.0-flash
   scripts/use-brain.sh openai
   ```
2. **Alternative — OpenRouter:** https://openrouter.ai/keys → create key; free models end in
   `:free` (e.g. `meta-llama/llama-3.1-8b-instruct:free`). Same exports with
   `HEARTH_BASE_URL=https://openrouter.ai/api/v1`.

### B. AWS Bedrock + $150 hackathon credits (needs a card for the AWS account)
1. Create an AWS account, then request credits via the hackathon form
   (`https://forms.gle/5hyhr1u6x3fuV2aW7`) before Oct 21, 12pm PT.
2. ```bash
   pip install boto3
   export AWS_BEDROCK_ENABLED=1 AWS_REGION=us-east-1
   export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...
   export AWS_BEDROCK_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
   scripts/use-brain.sh bedrock
   ```

### Judge-safe default
Ship and demo on `local` (exact numbers, zero setup). Mention Ollama/cloud as
supported brains with proof in `docs/product_feedback.md` — optionality scores
without risking a live-key failure on stage.
