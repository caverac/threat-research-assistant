# Quick Start

!!! warning "Requires AWS Bedrock access"
    Make sure you have [configured AWS credentials with Bedrock model access](installation.md#aws-bedrock-access) before running `build-index` or starting the API server.

## 1. Generate Synthetic Data

```bash
make generate-data
```

This creates ~100 JSON documents (advisories, threat reports, incidents) in the `data/` directory.

## 2. Build the FAISS Index

```bash
make build-index
```

This loads the generated data, chunks it, calls Bedrock Titan to generate embeddings, and saves the FAISS index to `data/faiss_index/`.

## 3. Train the Recommender

```bash
make train-recommender
```

This trains the LightGBM learning-to-rank model on synthetic query-document pairs and saves it to `models/recommender.joblib`.

## 4. Start the API Server

```bash
make serve
```

## 5. Ask a Question

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What vulnerabilities affect Modbus PLCs?", "max_results": 5}'
```

## 6. View the Response

The API returns structured JSON with:

- `answer`: The assistant's response with citations
- `citations`: Source documents referenced
- `recommendations`: Related documents to explore
- `metadata`: Performance metrics and model info
