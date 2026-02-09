"""Tests for FAISSVectorStore and EmbeddingIndexer."""

from pathlib import Path

import pytest

from core.schemas import DocumentChunk
from embeddings.client import BedrockEmbeddingClient
from embeddings.index import EmbeddingIndexer
from embeddings.store import FAISSVectorStore, VectorStore


class TestFAISSVectorStore:
    """Tests for the FAISS-backed vector store."""

    def test_implements_protocol(self, faiss_store: FAISSVectorStore) -> None:
        """Verify FAISSVectorStore satisfies the VectorStore protocol."""
        assert isinstance(faiss_store, VectorStore)

    def test_add_and_count(self, faiss_store: FAISSVectorStore, sample_chunks: list[DocumentChunk]) -> None:
        """Verify chunks are added and count reflects them."""
        faiss_store.add(sample_chunks)
        assert faiss_store.count() == 5

    def test_add_no_embedding_raises(self, faiss_store: FAISSVectorStore) -> None:
        """Verify adding a chunk without embedding raises ValueError."""
        chunk = DocumentChunk(id="test", source_id="src", source_type="advisory", content="text")
        with pytest.raises(ValueError, match="has no embedding"):
            faiss_store.add([chunk])

    def test_search(self, faiss_store: FAISSVectorStore, sample_chunks: list[DocumentChunk]) -> None:
        """Verify search returns ranked results with scores."""
        faiss_store.add(sample_chunks)
        query = sample_chunks[0].embedding
        assert query is not None
        results = faiss_store.search(query, top_k=3)
        assert len(results) == 3
        assert all(isinstance(r, tuple) for r in results)
        assert all(isinstance(r[0], DocumentChunk) for r in results)
        assert all(isinstance(r[1], float) for r in results)
        # First result should be the query itself (highest similarity)
        assert results[0][0].id == sample_chunks[0].id

    def test_search_empty_store(self, faiss_store: FAISSVectorStore) -> None:
        """Verify search on empty store returns empty list."""
        query = [0.1] * 8
        results = faiss_store.search(query, top_k=5)
        assert results == []

    def test_search_top_k_larger_than_store(self, faiss_store: FAISSVectorStore, sample_chunks: list[DocumentChunk]) -> None:
        """Verify search returns all available when top_k exceeds count."""
        faiss_store.add(sample_chunks[:2])
        query = sample_chunks[0].embedding
        assert query is not None
        results = faiss_store.search(query, top_k=10)
        assert len(results) == 2

    def test_delete(self, faiss_store: FAISSVectorStore, sample_chunks: list[DocumentChunk]) -> None:
        """Verify delete removes specified chunks."""
        faiss_store.add(sample_chunks)
        assert faiss_store.count() == 5
        faiss_store.delete(["chunk-000", "chunk-001"])
        assert faiss_store.count() == 3

    def test_delete_nonexistent(self, faiss_store: FAISSVectorStore, sample_chunks: list[DocumentChunk]) -> None:
        """Verify deleting nonexistent IDs is a no-op."""
        faiss_store.add(sample_chunks)
        faiss_store.delete(["nonexistent"])
        assert faiss_store.count() == 5

    def test_save_and_load(self, faiss_store: FAISSVectorStore, sample_chunks: list[DocumentChunk], tmp_path: Path) -> None:
        """Verify index can be saved and loaded from disk."""
        faiss_store.add(sample_chunks)
        save_path = tmp_path / "faiss_index"
        faiss_store.save(save_path)

        new_store = FAISSVectorStore(dimension=8)
        new_store.load(save_path)
        assert new_store.count() == 5

        query = sample_chunks[0].embedding
        assert query is not None
        results = new_store.search(query, top_k=1)
        assert results[0][0].id == sample_chunks[0].id

    def test_load_nonexistent(self, faiss_store: FAISSVectorStore, tmp_path: Path) -> None:
        """Verify loading from nonexistent path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            faiss_store.load(tmp_path / "nonexistent")


class TestEmbeddingIndexer:
    """Tests for the EmbeddingIndexer."""

    def test_index_chunks_with_embeddings(
        self, mock_bedrock_client: BedrockEmbeddingClient, faiss_store: FAISSVectorStore, sample_chunks: list[DocumentChunk]
    ) -> None:
        """Verify indexing pre-embedded chunks skips embed_texts call."""
        indexer = EmbeddingIndexer(mock_bedrock_client, faiss_store)
        count = indexer.index_chunks(sample_chunks)
        assert count == 5
        assert faiss_store.count() == 5
        mock_bedrock_client.embed_texts.assert_not_called()  # type: ignore[attr-defined]

    def test_index_chunks_without_embeddings(
        self, mock_bedrock_client: BedrockEmbeddingClient, faiss_store: FAISSVectorStore, sample_chunks_no_embedding: list[DocumentChunk]
    ) -> None:
        """Verify indexing chunks without embeddings calls embed_texts."""
        indexer = EmbeddingIndexer(mock_bedrock_client, faiss_store)
        count = indexer.index_chunks(sample_chunks_no_embedding)
        assert count == 3
        assert faiss_store.count() == 3
        mock_bedrock_client.embed_texts.assert_called_once()  # type: ignore[attr-defined]

    def test_index_mixed_chunks(
        self,
        mock_bedrock_client: BedrockEmbeddingClient,
        faiss_store: FAISSVectorStore,
        sample_chunks: list[DocumentChunk],
        sample_chunks_no_embedding: list[DocumentChunk],
    ) -> None:
        """Verify indexing a mix of embedded and unembedded chunks."""
        mixed = sample_chunks[:2] + sample_chunks_no_embedding[:1]
        indexer = EmbeddingIndexer(mock_bedrock_client, faiss_store)
        count = indexer.index_chunks(mixed)
        assert count == 3

    def test_reindex_all(
        self, mock_bedrock_client: BedrockEmbeddingClient, faiss_store: FAISSVectorStore, sample_chunks: list[DocumentChunk]
    ) -> None:
        """Verify reindex_all clears the store and re-indexes."""
        indexer = EmbeddingIndexer(mock_bedrock_client, faiss_store)
        indexer.index_chunks(sample_chunks)
        assert faiss_store.count() == 5
        count = indexer.reindex_all(sample_chunks)
        assert count == 5
