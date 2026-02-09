"""Feature engineering for the learning-to-rank model."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np


class FeatureExtractor:
    """Extract features for the learning-to-rank model."""

    @staticmethod
    def embedding_similarity(query_embedding: list[float], doc_embedding: list[float]) -> float:
        """Compute cosine similarity between query and document embeddings."""
        q = np.array(query_embedding, dtype=np.float32)
        d = np.array(doc_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        d_norm = np.linalg.norm(d)
        if q_norm == 0 or d_norm == 0:
            return 0.0
        return float(np.dot(q, d) / (q_norm * d_norm))

    @staticmethod
    def temporal_decay(published: datetime, half_life_days: float = 180.0) -> float:
        """Compute exponential decay based on document age.

        Returns a value in (0, 1] where 1 is brand new and approaches 0 for old documents.
        """
        now = datetime.now(tz=timezone.utc)
        age_days = (now - published).total_seconds() / 86400.0
        if age_days < 0:
            return 1.0
        return math.exp(-0.693 * age_days / half_life_days)

    @staticmethod
    def metadata_match(query_values: set[str], doc_values: set[str]) -> float:
        """Compute Jaccard similarity for metadata overlap (protocols, asset types)."""
        if not query_values and not doc_values:
            return 0.0
        if not query_values or not doc_values:
            return 0.0
        intersection = query_values & doc_values
        union = query_values | doc_values
        return len(intersection) / len(union)

    @staticmethod
    def popularity_score(interaction_count: int, max_interactions: int = 100) -> float:
        """Normalize interaction count to [0, 1] using log scaling."""
        if interaction_count <= 0:
            return 0.0
        return min(1.0, math.log1p(interaction_count) / math.log1p(max_interactions))

    @staticmethod
    def recency_boost(published: datetime, boost_days: float = 30.0) -> float:
        """Provide a bonus score for recently published content."""
        now = datetime.now(tz=timezone.utc)
        age_days = (now - published).total_seconds() / 86400.0
        if age_days < 0:
            return 1.0
        if age_days > boost_days:
            return 0.0
        return 1.0 - (age_days / boost_days)

    def extract_features(
        self,
        query_embedding: list[float],
        doc_embedding: list[float],
        doc_published: datetime,
        query_protocols: set[str],
        doc_protocols: set[str],
        query_asset_types: set[str],
        doc_asset_types: set[str],
        interaction_count: int = 0,
    ) -> list[float]:
        """Extract all features for a query-document pair."""
        return [
            self.embedding_similarity(query_embedding, doc_embedding),
            self.temporal_decay(doc_published),
            self.metadata_match(query_protocols, doc_protocols),
            self.metadata_match(query_asset_types, doc_asset_types),
            self.popularity_score(interaction_count),
            self.recency_boost(doc_published),
        ]
