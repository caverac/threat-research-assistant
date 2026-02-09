"""Build and update the embedding index."""

from __future__ import annotations

from core.schemas import DocumentChunk
from embeddings.client import BedrockEmbeddingClient
from embeddings.store import FAISSVectorStore


class EmbeddingIndexer:
    """Build and update embedding indices from document chunks."""

    def __init__(self, client: BedrockEmbeddingClient, store: FAISSVectorStore) -> None:
        self._client = client
        self._store = store

    def index_chunks(self, chunks: list[DocumentChunk], batch_size: int = 10) -> int:
        """Generate embeddings for chunks and add to the vector store.

        Returns the number of chunks indexed.
        """
        chunks_to_embed = [c for c in chunks if c.embedding is None]
        chunks_with_embeddings = [c for c in chunks if c.embedding is not None]

        if chunks_to_embed:
            texts = [c.content for c in chunks_to_embed]
            embeddings = self._client.embed_texts(texts, batch_size)
            for chunk, embedding in zip(chunks_to_embed, embeddings):
                chunk.embedding = embedding

        all_chunks = chunks_with_embeddings + chunks_to_embed
        if all_chunks:
            self._store.add(all_chunks)
        return len(all_chunks)

    def reindex_all(self, chunks: list[DocumentChunk], batch_size: int = 10) -> int:
        """Clear the store and reindex all chunks.

        Returns the number of chunks indexed.
        """
        existing_ids = [c.id for c in chunks]
        self._store.delete(existing_ids)
        for chunk in chunks:
            chunk.embedding = None
        return self.index_chunks(chunks, batch_size)
