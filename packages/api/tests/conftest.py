"""Shared fixtures for API tests."""

import json
from contextlib import asynccontextmanager
from typing import AsyncIterator
from unittest.mock import MagicMock

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import health, ingest, query, recommend, reload
from assistant.chain import ResearchChain
from assistant.client import BedrockAssistantClient
from core.config import Settings
from core.schemas import DocumentChunk
from embeddings.client import BedrockEmbeddingClient
from embeddings.store import FAISSVectorStore
from recommender.predictor import RecommenderPredictor
from retrieval.pipeline import RetrievalPipeline
from retrieval.reranker import LightGBMReranker
from retrieval.retriever import HybridRetriever

EMBEDDING_DIM = 8


@pytest.fixture
def test_app() -> FastAPI:
    """Create a test FastAPI app with mocked dependencies injected directly."""
    mock_emb_client = MagicMock(spec=BedrockEmbeddingClient)
    mock_emb_client.embed_text.return_value = [0.1] * EMBEDDING_DIM

    store = FAISSVectorStore(dimension=EMBEDDING_DIM)
    rng = np.random.default_rng(42)
    chunks = [
        DocumentChunk(
            id=f"chunk-{i}",
            source_id=f"src-{i}",
            source_type="advisory",
            content=f"Content about OT vulnerability {i}",
            metadata={"title": f"Advisory {i}", "severity": "critical", "protocols": ["modbus"], "published": "2024-01-15T00:00:00+00:00"},
            embedding=rng.random(EMBEDDING_DIM).tolist(),
        )
        for i in range(5)
    ]
    store.add(chunks)

    retriever = HybridRetriever(mock_emb_client, store)

    mock_predictor = MagicMock(spec=RecommenderPredictor)
    mock_predictor.predict_scores.side_effect = lambda features: np.arange(len(features), dtype=np.float64)[::-1]
    reranker = LightGBMReranker(mock_predictor)

    pipeline = RetrievalPipeline(retriever, reranker)

    mock_asst_client = MagicMock(spec=BedrockAssistantClient)
    mock_asst_client.model_id = "test-model"
    response_data = json.dumps({"answer": "Test answer", "cited_sources": ["src-0"], "confidence": 0.9, "related_topics": []})
    mock_asst_client.generate.return_value = response_data

    chain = ResearchChain(pipeline, mock_asst_client)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = Settings()
        app.state.embedding_client = mock_emb_client
        app.state.vector_store = store
        app.state.retriever = retriever
        app.state.reranker = reranker
        app.state.retrieval_pipeline = pipeline
        app.state.assistant_client = mock_asst_client
        app.state.research_chain = chain
        yield

    app = FastAPI(title="Test", lifespan=lifespan)
    app.include_router(health.router, tags=["health"])
    app.include_router(query.router, prefix="/query", tags=["query"])
    app.include_router(recommend.router, prefix="/recommendations", tags=["recommendations"])
    app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
    app.include_router(reload.router, prefix="/reload-index", tags=["reload"])

    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:  # type: ignore[misc]  # pylint: disable=redefined-outer-name
    """Provide a TestClient bound to the test app."""
    with TestClient(test_app) as c:
        yield c  # type: ignore[misc]
