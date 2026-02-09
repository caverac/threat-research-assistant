#!/bin/bash
set -euo pipefail

# Bootstrap LocalStack for local development
LOCALSTACK_ENDPOINT="${LOCALSTACK_ENDPOINT:-http://localhost:4566}"

echo "Waiting for LocalStack to be ready..."
for i in $(seq 1 30); do
    if curl -s "${LOCALSTACK_ENDPOINT}/_localstack/health" | grep -q '"s3": "available"'; then
        echo "LocalStack is ready!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "Timed out waiting for LocalStack"
        exit 1
    fi
    sleep 1
done

echo "Creating S3 buckets..."
aws --endpoint-url="${LOCALSTACK_ENDPOINT}" s3 mb s3://tra-raw-data 2>/dev/null || true
aws --endpoint-url="${LOCALSTACK_ENDPOINT}" s3 mb s3://tra-processed 2>/dev/null || true
aws --endpoint-url="${LOCALSTACK_ENDPOINT}" s3 mb s3://tra-models 2>/dev/null || true

echo "Creating DynamoDB tables..."
aws --endpoint-url="${LOCALSTACK_ENDPOINT}" dynamodb create-table \
    --table-name tra-document-metadata \
    --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \
    --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST 2>/dev/null || true

aws --endpoint-url="${LOCALSTACK_ENDPOINT}" dynamodb create-table \
    --table-name tra-user-interactions \
    --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=timestamp,AttributeType=S \
    --key-schema AttributeName=user_id,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST 2>/dev/null || true

echo "LocalStack bootstrap complete!"
