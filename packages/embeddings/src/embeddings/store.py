"""Vector store protocol and FAISS implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable

import faiss
import numpy as np

from core.schemas import DocumentChunk


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for vector storage backends."""

    def add(self, chunks: list[DocumentChunk]) -> None:
        """Add document chunks with embeddings to the store."""
        ...  # pylint: disable=unnecessary-ellipsis

    def search(self, query_embedding: list[float], top_k: int = 10) -> list[tuple[DocumentChunk, float]]:
        """Search for similar chunks and return (chunk, score) pairs."""
        ...  # pylint: disable=unnecessary-ellipsis

    def delete(self, chunk_ids: list[str]) -> None:
        """Delete chunks by their IDs."""
        ...  # pylint: disable=unnecessary-ellipsis

    def count(self) -> int:
        """Return the number of chunks in the store."""
        ...  # pylint: disable=unnecessary-ellipsis


class FAISSVectorStore:
    """FAISS-backed vector store for local development."""

    def __init__(self, dimension: int = 1024) -> None:
        self._dimension = dimension
        self._index = faiss.IndexFlatIP(dimension)
        self._chunks: list[DocumentChunk] = []
        self._id_to_position: dict[str, int] = {}

    def add(self, chunks: list[DocumentChunk]) -> None:
        """Add document chunks with embeddings to the FAISS index."""
        vectors = []
        for chunk in chunks:
            if chunk.embedding is None:
                raise ValueError(f"Chunk {chunk.id} has no embedding")
            vectors.append(chunk.embedding)
            self._id_to_position[chunk.id] = len(self._chunks)
            self._chunks.append(chunk)

        if vectors:
            arr = np.array(vectors, dtype=np.float32)
            faiss.normalize_L2(arr)
            self._index.add(arr)

    def search(self, query_embedding: list[float], top_k: int = 10) -> list[tuple[DocumentChunk, float]]:
        """Search the FAISS index for similar chunks."""
        if self._index.ntotal == 0:
            return []
        query = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query)
        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(query, k)
        results: list[tuple[DocumentChunk, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                results.append((self._chunks[idx], float(score)))
        return results

    def delete(self, chunk_ids: list[str]) -> None:
        """Delete chunks by ID. Rebuilds the index."""
        ids_to_remove = set(chunk_ids)
        remaining = [c for c in self._chunks if c.id not in ids_to_remove]
        self._rebuild(remaining)

    def count(self) -> int:
        """Return the number of chunks in the store."""
        return len(self._chunks)

    def save(self, path: Path) -> None:
        """Save the FAISS index and metadata to disk."""
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(path / "index.faiss"))
        metadata = [chunk.model_dump() for chunk in self._chunks]
        (path / "metadata.json").write_text(json.dumps(metadata))

    def load(self, path: Path) -> None:
        """Load the FAISS index and metadata from disk."""
        index_path = path / "index.faiss"
        metadata_path = path / "metadata.json"
        if not index_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(f"Index files not found at {path}")
        self._index = faiss.read_index(str(index_path))
        self._dimension = self._index.d
        raw_metadata = json.loads(metadata_path.read_text())
        self._chunks = [DocumentChunk.model_validate(m) for m in raw_metadata]
        self._id_to_position = {c.id: i for i, c in enumerate(self._chunks)}

    def _rebuild(self, chunks: list[DocumentChunk]) -> None:
        """Rebuild the index from a list of chunks."""
        self._index = faiss.IndexFlatIP(self._dimension)
        self._chunks = []
        self._id_to_position = {}
        if chunks:
            self.add(chunks)
