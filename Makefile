.PHONY: help install test lint format type-check docs docs-serve clean cdk-synth generate-data build-index train-recommender serve docker-build docker-run upload-artifacts

help:
	@echo "Available commands:"
	@echo "  install             Install all dependencies (uv sync)"
	@echo "  test                Run all tests"
	@echo "  lint                Run linting (flake8 + pylint + pydocstyle)"
	@echo "  format              Format code (black + isort)"
	@echo "  type-check          Run type checking (mypy)"
	@echo "  docs                Build documentation"
	@echo "  docs-serve          Serve documentation locally"
	@echo "  clean               Clean build artifacts"
	@echo "  generate-data       Generate synthetic threat data"
	@echo "  build-index         Build FAISS index from data (requires Bedrock)"
	@echo "  train-recommender   Train LightGBM recommender model"
	@echo "  serve               Run API server locally"

# Development setup
install:
	uv sync --all-packages
	uv run pre-commit install
	cd packages/infra && yarn install

# Testing
test:
	uv run pytest

test-verbose:
	uv run pytest -v

# Code quality
lint:
	uv run flake8 packages/
	uv run pylint packages/
	uv run pydocstyle packages/

format:
	uv run black packages/
	uv run isort packages/

type-check:
	uv run mypy packages/core/src packages/ingestion/src packages/embeddings/src packages/retrieval/src packages/recommender/src packages/assistant/src packages/api/src

# Documentation
docs:
	cd packages/docs && uv run mkdocs build

docs-serve:
	cd packages/docs && uv run mkdocs serve --livereload --dev-addr 127.0.0.1:8080

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "cdk.out" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "site" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage

# Data & model commands
generate-data:
	uv run python -m ingestion

build-index:
	uv run python -m embeddings

train-recommender:
	uv run python -m recommender

serve:
	uv run uvicorn api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

# Docker
docker-build:
	docker build -t tra-api .

docker-run:
	docker run -p 8000:8000 -e TRA_AWS_REGION=us-east-1 tra-api

# Artifact upload
upload-artifacts:
	aws s3 sync data/faiss_index/ s3://tra-models-$$(aws sts get-caller-identity --query Account --output text)-$$(aws configure get region)/faiss_index/
	aws s3 cp models/recommender.joblib s3://tra-models-$$(aws sts get-caller-identity --query Account --output text)-$$(aws configure get region)/models/recommender.joblib

# CDK commands
cdk-synth:
	cd packages/infra && yarn cdk synth

cdk-deploy:
	cd packages/infra && yarn deploy

cdk-destroy:
	cd packages/infra && yarn destroy

cdk-diff:
	cd packages/infra && yarn diff

cdk-bootstrap:
	cd packages/infra && yarn bootstrap
