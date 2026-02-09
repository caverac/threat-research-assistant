# Configuration

All configuration is managed via environment variables with the `TRA_` prefix.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRA_AWS_REGION` | `us-east-1` | AWS region |
| `TRA_AWS_ENDPOINT_URL` | `None` | LocalStack endpoint override |
| `TRA_BEDROCK_EMBEDDING_MODEL_ID` | `amazon.titan-embed-text-v2:0` | Bedrock embedding model |
| `TRA_BEDROCK_LLM_MODEL_ID` | `us.anthropic.claude-opus-4-5-20251101-v1:0` | Bedrock LLM model |
| `TRA_VECTOR_STORE_TYPE` | `faiss` | Vector store backend (`faiss` or `opensearch`) |
| `TRA_CHUNK_SIZE` | `512` | Document chunk size (words) |
| `TRA_CHUNK_OVERLAP` | `64` | Chunk overlap (words) |
| `TRA_RETRIEVAL_TOP_K` | `20` | Initial retrieval candidates |
| `TRA_RERANK_TOP_K` | `5` | Final results after reranking |

## Using a `.env` File

Create a `.env` file in the project root:

```env
TRA_AWS_REGION=us-east-1
TRA_BEDROCK_LLM_MODEL_ID=us.anthropic.claude-opus-4-5-20251101-v1:0
```
