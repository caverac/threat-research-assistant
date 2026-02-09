"""Shared fixtures for retrieval tests."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from core.schemas import DocumentChunk
from embeddings.client import BedrockEmbeddingClient
from embeddings.store import FAISSVectorStore
from recommender.predictor import RecommenderPredictor

EMBEDDING_DIM = 8


@pytest.fixture
def mock_embedding_client() -> BedrockEmbeddingClient:
    """Return a mocked BedrockEmbeddingClient with a fixed random embedding."""
    client = MagicMock(spec=BedrockEmbeddingClient)
    client.embed_text.return_value = np.random.default_rng(0).random(EMBEDDING_DIM).tolist()
    return client


@pytest.fixture
def populated_store() -> FAISSVectorStore:
    """Return a FAISSVectorStore pre-populated with six document chunks."""
    store = FAISSVectorStore(dimension=EMBEDDING_DIM)
    rng = np.random.default_rng(42)
    chunks = [
        DocumentChunk(
            id=f"chunk-{i}",
            source_id=f"src-{i}",
            source_type="advisory" if i < 3 else "threat_report",
            content=f"Content for chunk {i}",
            metadata={
                "severity": "critical" if i % 2 == 0 else "high",
                "protocols": ["modbus"] if i < 3 else ["dnp3"],
                "asset_types": ["plc"] if i < 3 else ["hmi"],
                "threat_category": "apt" if i >= 3 else None,
                "published": "2024-01-15T00:00:00+00:00",
            },
            embedding=rng.random(EMBEDDING_DIM).tolist(),
        )
        for i in range(6)
    ]
    store.add(chunks)
    return store


@pytest.fixture
def mock_predictor() -> RecommenderPredictor:
    """Return a mocked RecommenderPredictor that returns descending scores."""
    predictor = MagicMock(spec=RecommenderPredictor)
    predictor.predict_scores.side_effect = lambda features: np.arange(len(features), dtype=np.float64)[::-1]
    return predictor
