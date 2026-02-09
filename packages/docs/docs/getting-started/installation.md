# Installation

## Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/) package manager
- AWS account with Bedrock model access enabled (see below)
- Node.js + Yarn (for CDK infrastructure only)

## AWS Bedrock Access

The API requires access to two Bedrock models. **You do not need to deploy the CDK stacks** — Bedrock is a managed API service that only requires model access to be enabled in your AWS account.

1. Sign in to the [AWS Console](https://console.aws.amazon.com/)
2. Navigate to **Amazon Bedrock** > **Model access**
3. Request access to:
    - **Amazon Titan Embed Text v2** (`amazon.titan-embed-text-v2:0`) — used for generating embeddings
    - **Anthropic Claude Opus 4.5** (`us.anthropic.claude-opus-4-5-20251101-v1:0`) — used for research answers
4. Configure your local AWS credentials:

```bash
aws configure
# Or export directly:
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
```

!!! note "CDK stacks are for production only"
    The `packages/infra` CDK stacks deploy production infrastructure (ECS Fargate, OpenSearch, S3). For local development, the API uses FAISS for vector search and calls Bedrock directly via boto3 — no infrastructure deployment required.

## Install

```bash
# Clone the repository
git clone https://github.com/caverac/threat-research-assistant.git
cd threat-research-assistant

# Install all packages, pre-commit hooks, and CDK dependencies
make install
```

This runs `uv sync` to install all workspace packages, sets up pre-commit hooks, and installs CDK Node.js dependencies.

## Development Setup

```bash
# Generate synthetic threat data
make generate-data

# Train the recommender model
make train-recommender

# Verify everything works
make test
```
