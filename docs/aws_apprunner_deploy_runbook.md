# 🚀 Hearth Universal — Cloud Deployment Runbook
*Target: Live HTTPS URL on AWS App Runner (or Fly.io fallback) for Devpost Submission*

---

## 🅰️ Option 1: AWS App Runner Deployment (Recommended for AWS Hackathon)

Deploying directly to AWS App Runner (`*.awsapprunner.com`) maximizes scoring in both the **Alexa+ Track** and the **AWS Builder Mini Challenge ($5,000 Cash + $5,000 AWS Credits)**.

### Step 1: Login to AWS via CLI
Make sure you have the AWS CLI configured with your credentials:
```bash
aws sts get-caller-identity
```

### Step 2: Build & Push Image to Amazon ECR
```bash
# 1. Create an ECR repository
aws ecr create-repository --repository-name hearth-universal --region us-east-1

# 2. Authenticate Docker with Amazon ECR
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# 3. Build the production container
docker build -t hearth-universal:latest -f infra/Dockerfile .

# 4. Tag and push to ECR
docker tag hearth-universal:latest ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/hearth-universal:latest
docker push ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/hearth-universal:latest
```

### Step 3: Create App Runner Service
Create an App Runner service pointing to your ECR image:
```bash
aws apprunner create-service \
  --service-name hearth-universal \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "'"${ACCOUNT_ID}"'.dkr.ecr.us-east-1.amazonaws.com/hearth-universal:latest",
      "ImageConfiguration": {
        "Port": "8787",
        "RuntimeEnvironmentVariables": {
          "PORT": "8787",
          "HEARTH_BRAIN_PROVIDER": "local",
          "AWS_BEDROCK_ENABLED": "1",
          "AWS_REGION": "us-east-1"
        }
      },
      "ImageRepositoryType": "ECR"
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }' \
  --region us-east-1
```

### Step 4: Verify Deployment
Once created, App Runner provides a live public domain:
```
https://<service-id>.us-east-1.awsapprunner.com/health
https://<service-id>.us-east-1.awsapprunner.com/echo
```
Test on your phone over mobile 5G.

---

## 🅱️ Option 2: Fly.io Deployment (Fast 5-Minute Fallback)

If AWS credentials are not readily available in your local shell, Fly.io deploys directly from `infra/Dockerfile`:

```bash
# 1. Install and authenticate flyctl (if not already installed)
curl -L https://fly.io/install.sh | sh
fly auth login

# 2. Launch using our multi-stage Dockerfile
fly launch --dockerfile infra/Dockerfile --internal-port 8787 --no-deploy

# 3. Create persistent volume for state
fly volumes create hearth_data --size 1 --region iad

# 4. Deploy
fly deploy
```

Once deployed, your live URL will be:
```
https://hearth-universal.fly.dev/echo
```

---

## 📋 Devpost Insertion
Once your live URL is active, update **Line 28** in `docs/devpost_submission_v2.md`:
```markdown
- **Live Cloud App URL**: https://<your-service>.awsapprunner.com/echo
```
