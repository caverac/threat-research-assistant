"""Shared fixtures for assistant tests."""

import json
from unittest.mock import MagicMock

import numpy as np
import pytest

from assistant.client import BedrockAssistantClient
from core.schemas import DocumentChunk
from embeddings.client import BedrockEmbeddingClient
from embeddings.store import FAISSVectorStore
from recommender.predictor import RecommenderPredictor
from retrieval.pipeline import RetrievalPipeline
from retrieval.reranker import LightGBMReranker
from retrieval.retriever import HybridRetriever

EMBEDDING_DIM = 8


@pytest.fixture
def mock_assistant_client() -> BedrockAssistantClient:
    """Create a mocked BedrockAssistantClient with a canned JSON response."""
    client = MagicMock(spec=BedrockAssistantClient)
    client.model_id = "anthropic.claude-3-5-sonnet"
    response_data = json.dumps(
        {
            "answer": "Test answer about OT threats.",
            "cited_sources": ["src-0"],
            "confidence": 0.9,
            "related_topics": ["Modbus security"],
        }
    )
    client.generate.return_value = response_data
    client.invoke.return_value = {"content": [{"type": "text", "text": response_data}]}
    return client


@pytest.fixture
def mock_retrieval_pipeline() -> RetrievalPipeline:
    """Create a RetrievalPipeline backed by a small in-memory FAISS index."""
    mock_embedding_client = MagicMock(spec=BedrockEmbeddingClient)
    mock_embedding_client.embed_text.return_value = [0.1] * EMBEDDING_DIM

    store = FAISSVectorStore(dimension=EMBEDDING_DIM)
    rng = np.random.default_rng(42)
    chunks = [
        DocumentChunk(
            id=f"chunk-{i}",
            source_id=f"src-{i}",
            source_type="advisory",
            content=f"Advisory content about OT vulnerability {i}",
            metadata={"title": f"Advisory {i}", "severity": "critical", "protocols": ["modbus"], "published": "2024-01-15T00:00:00+00:00"},
            embedding=rng.random(EMBEDDING_DIM).tolist(),
        )
        for i in range(5)
    ]
    store.add(chunks)

    retriever = HybridRetriever(mock_embedding_client, store)

    mock_predictor = MagicMock(spec=RecommenderPredictor)
    mock_predictor.predict_scores.side_effect = lambda features: np.arange(len(features), dtype=np.float64)[::-1]
    reranker = LightGBMReranker(mock_predictor)

    return RetrievalPipeline(retriever, reranker)
