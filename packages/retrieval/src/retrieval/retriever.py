"""Hybrid retrieval combining vector search with metadata filtering."""

from __future__ import annotations

from core.schemas import DocumentChunk, QueryFilters
from embeddings.client import BedrockEmbeddingClient
from embeddings.store import FAISSVectorStore


class HybridRetriever:
    """Combine vector similarity search with keyword/metadata filtering."""

    def __init__(self, embedding_client: BedrockEmbeddingClient, vector_store: FAISSVectorStore) -> None:
        self._embedding_client = embedding_client
        self._vector_store = vector_store

    @property
    def document_count(self) -> int:
        """Return the total number of documents in the vector store."""
        return self._vector_store.count()

    def embed_query(self, query: str) -> list[float]:
        """Generate an embedding for the given query text."""
        return self._embedding_client.embed_text(query)

    def retrieve(self, query: str, top_k: int = 20, filters: QueryFilters | None = None) -> list[tuple[DocumentChunk, float]]:
        """Retrieve relevant document chunks via vector search + optional metadata filtering."""
        query_embedding = self._embedding_client.embed_text(query)
        candidates = self._vector_store.search(query_embedding, top_k=top_k * 2)

        if filters:
            candidates = self._apply_filters(candidates, filters)

        return candidates[:top_k]

    @staticmethod
    def _apply_filters(candidates: list[tuple[DocumentChunk, float]], filters: QueryFilters) -> list[tuple[DocumentChunk, float]]:
        """Apply metadata filters to candidate results."""
        filtered: list[tuple[DocumentChunk, float]] = []
        for chunk, score in candidates:
            if filters.severity and chunk.metadata.get("severity"):
                if chunk.metadata["severity"] not in [s.value for s in filters.severity]:
                    continue

            if filters.protocols and chunk.metadata.get("protocols"):
                doc_protocols = set(chunk.metadata["protocols"])
                filter_protocols = {p.value for p in filters.protocols}
                if not doc_protocols & filter_protocols:
                    continue

            if filters.asset_types and chunk.metadata.get("asset_types"):
                doc_assets = set(chunk.metadata["asset_types"])
                filter_assets = {a.value for a in filters.asset_types}
                if not doc_assets & filter_assets:
                    continue

            if filters.threat_categories:
                doc_category = chunk.metadata.get("threat_category")
                if not doc_category or doc_category not in [c.value for c in filters.threat_categories]:
                    continue

            filtered.append((chunk, score))
        return filtered
