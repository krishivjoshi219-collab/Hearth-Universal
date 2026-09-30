# AWS Builder Integration Architecture

**Submission Track:** Mini Challenge — AWS Builder ($5,000 Prize)  
**Project:** Hearth Universal (Alexa+ MCP Core)  
**Integrated AWS Services:** Amazon Bedrock (Converse API), AWS AgentCore Runtime Pattern, Kiro Crew Tooling

---

## 1. Amazon Bedrock Converse API Integration

Hearth Universal integrates **Amazon Bedrock** as a first-class foundation model runtime in [`src/hearth/brains.py`](file:///home/k/Prototype/Amazon/src/hearth/brains.py).

### Models Supported
- **Anthropic Claude 3.5 Sonnet**: `anthropic.claude-3-5-sonnet-20241022-v2:0` (High-reasoning multi-tool DAG decomposition)
- **Amazon Nova Pro**: `amazon.nova-pro-v1:0` (Low-latency structured JSON planning)
- **Amazon Titan Text Express**: `amazon.titan-text-express-v1` (Fast intent classification)

### Code Implementation
Bedrock is invoked using the modern unified **Converse API**:

```python
import boto3

client = boto3.client("bedrock-runtime", region_name=region)
response = client.converse(
    modelId=model_id,
    messages=[
        {"role": "user", "content": [{"text": user_prompt}]}
    ],
    inferenceConfig={"maxTokens": 1200, "temperature": 0.3}
)
output_text = response["output"]["message"]["content"][0]["text"]
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
3. **Automated Verification**: Formulated the 14-test pytest suite validating sub-second offline verification.
