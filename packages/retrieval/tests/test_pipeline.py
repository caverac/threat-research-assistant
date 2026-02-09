"""Tests for the RetrievalPipeline."""

from embeddings.client import BedrockEmbeddingClient
from embeddings.store import FAISSVectorStore
from recommender.predictor import RecommenderPredictor
from retrieval.pipeline import RetrievalPipeline
from retrieval.reranker import LightGBMReranker
from retrieval.retriever import HybridRetriever


class TestRetrievalPipeline:
    """Tests for RetrievalPipeline functionality."""

    def test_run_without_reranker(self, mock_embedding_client: BedrockEmbeddingClient, populated_store: FAISSVectorStore) -> None:
        """Verify pipeline returns results and positive elapsed time without a reranker."""
        retriever = HybridRetriever(mock_embedding_client, populated_store)
        pipeline = RetrievalPipeline(retriever)
        results, elapsed = pipeline.run("test query", top_k=3)
        assert len(results) == 3
        assert elapsed > 0

    def test_run_with_reranker(
        self, mock_embedding_client: BedrockEmbeddingClient, populated_store: FAISSVectorStore, mock_predictor: RecommenderPredictor
    ) -> None:
        """Verify pipeline returns reranked results and positive elapsed time."""
        retriever = HybridRetriever(mock_embedding_client, populated_store)
        reranker = LightGBMReranker(mock_predictor)
        pipeline = RetrievalPipeline(retriever, reranker)
        results, elapsed = pipeline.run("test query", top_k=3, retrieval_k=6)
        assert len(results) == 3
        assert elapsed > 0

    def test_run_empty_store(self, mock_embedding_client: BedrockEmbeddingClient) -> None:
        """Verify pipeline returns an empty list when the store has no documents."""
        empty_store = FAISSVectorStore(dimension=8)
        retriever = HybridRetriever(mock_embedding_client, empty_store)
        pipeline = RetrievalPipeline(retriever)
        results, elapsed = pipeline.run("test query", top_k=5)
        assert results == []
        assert elapsed > 0
