"""Tests for the LightGBMReranker."""

import numpy as np

from core.schemas import DocumentChunk
from recommender.predictor import RecommenderPredictor
from retrieval.reranker import LightGBMReranker, Reranker


class TestLightGBMReranker:
    """Tests for LightGBMReranker functionality."""

    def test_implements_protocol(self, mock_predictor: RecommenderPredictor) -> None:
        """Verify LightGBMReranker satisfies the Reranker protocol."""
        reranker = LightGBMReranker(mock_predictor)
        assert isinstance(reranker, Reranker)

    def test_rerank(self, mock_predictor: RecommenderPredictor) -> None:
        """Verify reranking returns the requested number of scored results."""
        reranker = LightGBMReranker(mock_predictor)
        rng = np.random.default_rng(42)
        candidates = [
            (
                DocumentChunk(
                    id=f"chunk-{i}",
                    source_id=f"src-{i}",
                    source_type="advisory",
                    content=f"Content {i}",
                    metadata={"published": "2024-01-15T00:00:00+00:00", "protocols": ["modbus"]},
                    embedding=rng.random(8).tolist(),
                ),
                float(i) * 0.1,
            )
            for i in range(5)
        ]

        query_emb = rng.random(8).tolist()
        results = reranker.rerank(query_emb, candidates, top_k=3)
        assert len(results) == 3
        assert all(isinstance(r[1], float) for r in results)

    def test_rerank_empty(self, mock_predictor: RecommenderPredictor) -> None:
        """Verify reranking an empty candidate list returns an empty list."""
        reranker = LightGBMReranker(mock_predictor)
        results = reranker.rerank([0.1] * 8, [], top_k=5)
        assert results == []

    def test_rerank_without_published(self, mock_predictor: RecommenderPredictor) -> None:
        """Verify reranking handles chunks missing the published metadata field."""
        reranker = LightGBMReranker(mock_predictor)
        candidates = [
            (
                DocumentChunk(
                    id="chunk-0",
                    source_id="src-0",
                    source_type="advisory",
                    content="Content",
                    metadata={},
                    embedding=[0.1] * 8,
                ),
                0.9,
            )
        ]
        results = reranker.rerank([0.1] * 8, candidates, top_k=1)
        assert len(results) == 1

    def test_rerank_without_embedding(self, mock_predictor: RecommenderPredictor) -> None:
        """Verify reranking handles chunks without an embedding vector."""
        reranker = LightGBMReranker(mock_predictor)
        candidates = [
            (
                DocumentChunk(
                    id="chunk-0",
                    source_id="src-0",
                    source_type="advisory",
                    content="Content",
                    metadata={"published": "2024-01-15T00:00:00+00:00"},
                ),
                0.9,
            )
        ]
        results = reranker.rerank([0.1] * 8, candidates, top_k=1)
        assert len(results) == 1
