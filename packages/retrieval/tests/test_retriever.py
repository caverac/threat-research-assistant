"""Tests for the HybridRetriever."""

from core.enums import AssetType, Protocol, Severity, ThreatCategory
from core.schemas import QueryFilters
from embeddings.client import BedrockEmbeddingClient
from embeddings.store import FAISSVectorStore
from retrieval.retriever import HybridRetriever


class TestHybridRetriever:
    """Tests for HybridRetriever functionality."""

    def test_retrieve(self, mock_embedding_client: BedrockEmbeddingClient, populated_store: FAISSVectorStore) -> None:
        """Verify basic retrieval returns the requested number of scored results."""
        retriever = HybridRetriever(mock_embedding_client, populated_store)
        results = retriever.retrieve("test query", top_k=3)
        assert len(results) == 3
        assert all(isinstance(r[1], float) for r in results)

    def test_retrieve_with_severity_filter(self, mock_embedding_client: BedrockEmbeddingClient, populated_store: FAISSVectorStore) -> None:
        """Verify retrieval filtered by severity returns only matching chunks."""
        retriever = HybridRetriever(mock_embedding_client, populated_store)
        filters = QueryFilters(severity=[Severity.CRITICAL])
        results = retriever.retrieve("test query", top_k=10, filters=filters)
        for chunk, _ in results:
            assert chunk.metadata.get("severity") == "critical"

    def test_retrieve_with_protocol_filter(self, mock_embedding_client: BedrockEmbeddingClient, populated_store: FAISSVectorStore) -> None:
        """Verify retrieval filtered by protocol returns only matching chunks."""
        retriever = HybridRetriever(mock_embedding_client, populated_store)
        filters = QueryFilters(protocols=[Protocol.MODBUS])
        results = retriever.retrieve("test query", top_k=10, filters=filters)
        for chunk, _ in results:
            assert "modbus" in chunk.metadata.get("protocols", [])

    def test_retrieve_with_threat_category_filter(self, mock_embedding_client: BedrockEmbeddingClient, populated_store: FAISSVectorStore) -> None:
        """Verify retrieval filtered by threat category returns only matching chunks."""
        retriever = HybridRetriever(mock_embedding_client, populated_store)
        filters = QueryFilters(threat_categories=[ThreatCategory.APT])
        results = retriever.retrieve("test query", top_k=10, filters=filters)
        for chunk, _ in results:
            assert chunk.metadata.get("threat_category") == "apt"

    def test_retrieve_with_asset_type_filter(self, mock_embedding_client: BedrockEmbeddingClient, populated_store: FAISSVectorStore) -> None:
        """Verify retrieval filtered by asset type returns only matching chunks."""
        retriever = HybridRetriever(mock_embedding_client, populated_store)
        filters = QueryFilters(asset_types=[AssetType.PLC])
        results = retriever.retrieve("test query", top_k=10, filters=filters)
        for chunk, _ in results:
            assert "plc" in chunk.metadata.get("asset_types", [])

    def test_retrieve_no_results(self, mock_embedding_client: BedrockEmbeddingClient) -> None:
        """Verify retrieval from an empty store returns an empty list."""
        empty_store = FAISSVectorStore(dimension=8)
        retriever = HybridRetriever(mock_embedding_client, empty_store)
        results = retriever.retrieve("test query", top_k=5)
        assert results == []
