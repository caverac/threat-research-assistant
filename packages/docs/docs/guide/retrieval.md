# Retrieval Pipeline

The retrieval pipeline combines vector similarity search with metadata filtering and ML reranking.

## Pipeline Stages

```mermaid
flowchart TD
    Q([Query]) --> E[1. Query Embedding<br/>Bedrock Titan]
    E --> S[2. Vector Search<br/>FAISS top-k]
    S --> F[3. Metadata Filtering<br/>severity, protocols, asset types]
    F --> R[4. ML Reranking<br/>LightGBM L2R]
    R --> K([5. Return Top-K])
```

## Usage

```python
from core.enums import Protocol
from core.schemas import QueryFilters
from retrieval.pipeline import RetrievalPipeline

results, elapsed_ms = pipeline.run(
    query="Modbus PLC vulnerabilities",
    top_k=5,
    retrieval_k=20,
    filters=QueryFilters(protocols=[Protocol.MODBUS]),
)
```
