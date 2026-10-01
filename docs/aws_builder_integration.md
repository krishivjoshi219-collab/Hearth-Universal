# AWS Builder Integration Architecture

**Submission Track:** Mini Challenge — AWS Builder ($5,000 Prize)  
**Project:** Hearth Universal (Alexa+ MCP Core)  
**Integrated AWS Services:** Amazon Bedrock (Converse API), AWS AgentCore Runtime Pattern, Kiro Crew Tooling

---

## 1. Amazon Bedrock Converse API Integration

Hearth Universal integrates **Amazon Bedrock** as a first-class foundation model runtime in [`src/hearth/brains.py`](file:///home/k/Prototype/Amazon/src/hearth/brains.py).

### Models Supported (cross-region inference profiles)
- **Anthropic Claude 3.5 Sonnet**: `us.anthropic.claude-3-5-sonnet-20241022-v2:0` (High-reasoning multi-tool DAG decomposition)
- **Amazon Nova Pro**: `us.amazon.nova-pro-v1:0` (Low-latency structured JSON planning)
- **Amazon Nova Lite / Titan Express**: `us.amazon.nova-lite-v1:0` / `amazon.titan-text-express-v1` (Fast intent classification)

### Multi-Model Router (B4 upgrade)
`select_bedrock_model()` in `src/hearth/brains.py` routes per request:
- Explicit `AWS_BEDROCK_MODEL` alias or full inference-profile ID always wins.
- `auto` (default): content hints (`json`, `classify`, `intent`, `fast`, `structured`, …) → **Nova Pro**; otherwise → **Claude 3.5 Sonnet**.
- All IDs use `us.*` cross-region inference profiles for multi-region resilience.
- Botocore client uses adaptive retries: `Config(retries={"max_attempts": AWS_BEDROCK_MAX_ATTEMPTS (default 5), "mode": "adaptive"})`.
- `system=[]` isolation: system prompts are never merged into user turns; user/assistant alternation is enforced (consecutive same-role turns merged, leading user turn guaranteed).

### Env Var Reference (zero-config offline by default — no charges unless opted in)
| Var | Default | Effect |
|---|---|---|
| `AWS_BEDROCK_ENABLED` | `0` | Set `1` to enable live Bedrock; anything else → local agent fallback, no AWS calls |
| `AWS_REGION` | `us-east-1` | Bedrock region for `bedrock-runtime` client |
| `AWS_BEDROCK_MODEL` | `auto` | `auto` (router) \| `claude-sonnet` \| `nova-pro` \| `nova-lite` \| full inference-profile ID |
| `AWS_BEDROCK_MAX_ATTEMPTS` | `5` | Botocore adaptive retry max attempts (clamped 1–10) |
| `HEARTH_BRAIN_PROVIDER` | `local` | `local` \| `bedrock` \| `openai`; `preferred_provider` arg / `/api/brain` can override |
| `HEARTH_MODEL` / `HEARTH_BASE_URL` / `OPENAI_API_KEY` | `gpt-4o-mini` / `https://api.openai.com/v1` | OpenAI-compatible path (used only when provider=openai or key present) |
| `PORT` | `8787` | HTTP port (Dockerfile `EXPOSE 8787`, non-root `hearth` user) |

### Telemetry: `GET /api/metrics`
Bedrock-native `metrics.latencyMs` series (no PII, in-memory ring of last 100 calls):
```json
{"bedrockEnabled": false, "region": "us-east-1", "count": 3, "avgLatencyMs": 210.4, "lastLatencyMs": 195.0, "latencyMs": [231.2, 204.4, 195.0], "recent": [...]}
```
Every `_call_bedrock` records `{model, provider, latencyMs, tokens, fallback}` — visible via `brains.get_bedrock_metrics()` and `GET /api/metrics?limit=25`.

### Code Implementation
Bedrock is invoked using the modern unified **Converse API**:

```python
import boto3
from botocore.config import Config

config = Config(retries={"max_attempts": 5, "mode": "adaptive"})
client = boto3.client("bedrock-runtime", region_name=region, config=config)
response = client.converse(
    modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",  # cross-region inference profile
    system=[{"text": system_prompt}],  # isolated, never merged into user turns
    messages=[
        {"role": "user", "content": [{"text": user_prompt}]}
    ],
    inferenceConfig={"maxTokens": 1200, "temperature": 0.3}
)
output_text = response["output"]["message"]["content"][0]["text"]
bedrock_latency = response.get("metrics", {}).get("latencyMs", 0.0)  # -> /api/metrics
```

### Zero-Friction Fallback
To ensure hackathon judges can test the submission immediately without providing AWS credentials or incurring charges, Hearth Universal includes an automatic failover:
- If `boto3` or AWS credentials are not detected in the environment, the system gracefully operates on the intelligent local agent engine while surfacing a clean status notification in the UI:
  `[AWS Bedrock: running on simulated agent core — configure AWS credentials to stream from live Bedrock]`

---

## 2. AWS AgentCore & Containerization

The repository includes a production-ready, multi-architecture Dockerfile targeting AWS container services (AWS App Runner, ECS Fargate, or EKS):

- **File**: [`infra/Dockerfile`](file:///home/k/Prototype/Amazon/infra/Dockerfile)
- **Base Image**: `python:3.12-slim-bookworm`
- **Exposed Port**: `8787` (MCP Streamable HTTP + REST + Static PWA)
- **Security**: Non-root container user (`hearth`), read-only root filesystem with dedicated volume for `state/`.

### Run via Docker:
```bash
docker build -t hearth-universal -f infra/Dockerfile .
docker run -p 8787:8787 -e PORT=8787 hearth-universal
```

---

## 3. Development Workflow with Kiro Crew

Per the official hackathon rules:
> *"Kiro Crew qualifies on its own as a development tool used during the hackathon — a submission does not need to also call a runtime AWS service (Bedrock, AgentCore, SageMaker, Strands SDK) to count for this mini-challenge."*

Hearth Universal was scaffolded, designed, and verified using the Kiro development workflow:
1. **Agentic Scaffolding**: Decomposed the MCP 2025-11-25 Streamable HTTP specification into modular Python components (`brains`, `planner`, `sentinel`, `vault`, `proposals`).
2. **Adversarial Red-Teaming**: Generated the regex and pattern security rules used in Sentinel to block destructive shell injection (`rm -rf /`, `mkfs`) and vault exfiltration.
3. **Automated Verification**: Formulated the 64-test pytest suite (including 3 dedicated Amazon Bedrock Converse API schema tests) validating sub-second offline verification across all core modules.

---

## 4. Deploy Verification (no live charges)

```bash
# offline zero-config (default): no AWS calls, local agent
PORT=8787 python mcp-server/server.py &
curl -s localhost:8787/health | head -c 300
curl -s localhost:8787/api/metrics  # {"bedrockEnabled": false, ...}

# live Bedrock (only when you intend spend):
export AWS_BEDROCK_ENABLED=1 AWS_REGION=us-east-1 AWS_BEDROCK_MODEL=auto
python -c "from hearth import brains; print(brains.select_bedrock_model('classify intent as json'))"
# -> us.amazon.nova-pro-v1:0
curl -s localhost:8787/api/metrics | python3 -m json.tool | head -20
```

IAM least privilege: `infra/iam-bedrock-policy.json` allows only
`bedrock:Converse/ConverseStream/InvokeModel(+WithResponseStream)` on
`foundation-model/anthropic.claude-3-5-sonnet*`, `amazon.nova*`, and `inference-profile/*`.
Docker: `infra/Dockerfile` runs as non-root `hearth`, `EXPOSE 8787`.
App Runner: `infra/apprunner.yaml` sets `AWS_BEDROCK_MODEL=auto` router + `AWS_BEDROCK_MAX_ATTEMPTS=5`.

## 5. Product Feedback (AWS Builder Mini Challenge)

> Bedrock Converse + cross-region inference profiles worked well for swapping Claude/Nova without code changes; what slowed us down was discovering at runtime that (a) `system` must be top-level (not a message role) and (b) Converse IAM needs `bedrock:Converse`, not just `InvokeModel`. A local Converse schema validator (offline, no charges) and a documented minimal IAM policy per API (`converse` vs `invoke`) would shorten every hackathon integration. The `metrics.latencyMs` field is excellent for `/api/metrics` dashboards — we kept it as our canonical latency source with local wall-clock only as fallback.

