"""Shared fixtures for embeddings tests."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from core.schemas import DocumentChunk
from embeddings.client import BedrockEmbeddingClient
from embeddings.store import FAISSVectorStore

EMBEDDING_DIM = 8


@pytest.fixture
def mock_bedrock_client() -> BedrockEmbeddingClient:
    """Create a mocked BedrockEmbeddingClient with deterministic embeddings."""
    client = MagicMock(spec=BedrockEmbeddingClient)
    client.embed_text.side_effect = lambda text: np.random.default_rng(hash(text) % 2**31).random(EMBEDDING_DIM).tolist()
    client.embed_texts.side_effect = lambda texts, batch_size=10: [
        np.random.default_rng(hash(t) % 2**31).random(EMBEDDING_DIM).tolist() for t in texts
    ]
    client.embed_texts_as_numpy.side_effect = lambda texts, batch_size=10: np.array(
        [np.random.default_rng(hash(t) % 2**31).random(EMBEDDING_DIM).tolist() for t in texts], dtype=np.float32
    )
    return client


@pytest.fixture
def faiss_store() -> FAISSVectorStore:
    """Create an empty FAISS vector store for testing."""
    return FAISSVectorStore(dimension=EMBEDDING_DIM)


@pytest.fixture
def sample_chunks() -> list[DocumentChunk]:
    """Create sample document chunks with random embeddings."""
    rng = np.random.default_rng(42)
    return [
        DocumentChunk(
            id=f"chunk-{i:03d}",
            source_id=f"src-{i:03d}",
            source_type="advisory",
            content=f"Sample content for chunk {i}",
            metadata={"index": i},
            embedding=rng.random(EMBEDDING_DIM).tolist(),
        )
        for i in range(5)
    ]


@pytest.fixture
def sample_chunks_no_embedding() -> list[DocumentChunk]:
    """Create sample document chunks without embeddings."""
    return [
        DocumentChunk(
            id=f"chunk-{i:03d}",
            source_id=f"src-{i:03d}",
            source_type="advisory",
            content=f"Sample content for chunk {i}",
            metadata={"index": i},
        )
        for i in range(3)
    ]
