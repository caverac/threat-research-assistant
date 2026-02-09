"""Retrieval pipeline orchestrating search and reranking."""

from __future__ import annotations

import time

from core.schemas import DocumentChunk, QueryFilters
from retrieval.reranker import LightGBMReranker
from retrieval.retriever import HybridRetriever


class RetrievalPipeline:
    """Orchestrate the full retrieval pipeline: query → embed → search → rerank."""

    def __init__(self, retriever: HybridRetriever, reranker: LightGBMReranker | None = None) -> None:
        self._retriever = retriever
        self._reranker = reranker

    @property
    def total_documents(self) -> int:
        """Return the total number of documents in the vector store."""
        return self._retriever.document_count

    def run(
        self,
        query: str,
        top_k: int = 5,
        retrieval_k: int = 20,
        filters: QueryFilters | None = None,
    ) -> tuple[list[tuple[DocumentChunk, float]], float]:
        """Run the full retrieval pipeline.

        Returns
        -------
        tuple
            Tuple of (results, elapsed_ms) where results are (chunk, score) pairs.
        """
        start = time.monotonic()

        candidates = self._retriever.retrieve(query, top_k=retrieval_k, filters=filters)

        if self._reranker and candidates:
            query_embedding = self._retriever.embed_query(query)
            results = self._reranker.rerank(query_embedding, candidates, top_k=top_k)
        else:
            results = candidates[:top_k]

        elapsed_ms = (time.monotonic() - start) * 1000
        return results, elapsed_ms
