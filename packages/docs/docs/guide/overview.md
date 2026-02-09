# Overview

The OT Threat Research Assistant is a RAG (Retrieval-Augmented Generation) system designed for ICS/OT cybersecurity analysts. It combines:

1. **Semantic Search**: Vector embeddings via AWS Bedrock Titan for finding relevant threat intelligence
2. **ML Reranking**: LightGBM learning-to-rank model that considers temporal decay, metadata overlap, and popularity
3. **LLM Generation**: AWS Bedrock Claude for generating structured research answers with citations

## Packages

| Package | Purpose |
|---------|---------|
| `core` | Shared Pydantic models, enums, configuration |
| `ingestion` | Data loading, parsing, chunking |
| `embeddings` | Bedrock Titan embeddings, FAISS vector store |
| `retrieval` | Hybrid search pipeline |
| `recommender` | LightGBM learning-to-rank |
| `assistant` | Bedrock Claude research assistant |
| `api` | FastAPI REST service |
| `infra` | AWS CDK infrastructure |
| `docs` | This documentation site |
