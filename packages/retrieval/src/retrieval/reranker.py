"""Document reranking strategies."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

import numpy as np

from core.schemas import DocumentChunk
from recommender.features import FeatureExtractor
from recommender.predictor import RecommenderPredictor


@runtime_checkable
class Reranker(Protocol):
    """Protocol for document reranking strategies."""

    def rerank(
        self,
        query_embedding: list[float],
        candidates: list[tuple[DocumentChunk, float]],
        top_k: int = 5,
    ) -> list[tuple[DocumentChunk, float]]:
        """Rerank candidate chunks and return top_k results."""
        ...  # pylint: disable=unnecessary-ellipsis


class LightGBMReranker:
    """Rerank documents using the trained LightGBM L2R model."""

    def __init__(self, predictor: RecommenderPredictor) -> None:
        self._predictor = predictor
        self._extractor = FeatureExtractor()

    def rerank(
        self,
        query_embedding: list[float],
        candidates: list[tuple[DocumentChunk, float]],
        top_k: int = 5,
    ) -> list[tuple[DocumentChunk, float]]:
        """Rerank candidates using the LightGBM model."""
        if not candidates:
            return []

        features_list: list[list[float]] = []
        for chunk, _vector_score in candidates:
            doc_embedding = chunk.embedding or [0.0] * len(query_embedding)
            published_str = chunk.metadata.get("published")
            if published_str:
                published = datetime.fromisoformat(published_str)
            else:
                published = datetime(2024, 1, 1, tzinfo=timezone.utc)

            doc_protocols = set(chunk.metadata.get("protocols", []))
            doc_assets = set(chunk.metadata.get("asset_types", []))

            features = self._extractor.extract_features(
                query_embedding=query_embedding,
                doc_embedding=doc_embedding,
                doc_published=published,
                query_protocols=set(),
                doc_protocols=doc_protocols,
                query_asset_types=set(),
                doc_asset_types=doc_assets,
                interaction_count=0,
            )
            features_list.append(features)

        features_array = np.array(features_list, dtype=np.float32)
        scores = self._predictor.predict_scores(features_array)

        reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return [(chunk_score[0], float(lgbm_score)) for chunk_score, lgbm_score in reranked[:top_k]]
