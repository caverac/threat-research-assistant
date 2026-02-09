"""Generate synthetic training data for the learning-to-rank model."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import numpy as np

from recommender.features import FeatureExtractor

FEATURE_NAMES = [
    "embedding_similarity",
    "temporal_decay",
    "protocol_match",
    "asset_type_match",
    "popularity_score",
    "recency_boost",
]


class TrainingDataGenerator:
    """Generate synthetic query-document pairs with relevance labels for LTR training."""

    def __init__(self, seed: int = 42) -> None:
        self._rng = np.random.default_rng(seed)
        self._random = random.Random(seed)
        self._extractor = FeatureExtractor()

    def generate(self, n_queries: int = 100, docs_per_query: int = 20, embedding_dim: int = 8) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate synthetic training data.

        Returns
        -------
        tuple
            Tuple of (features, labels, groups) where:
            - features: (n_queries * docs_per_query, n_features) array
            - labels: (n_queries * docs_per_query,) array of relevance labels (0-4)
            - groups: (n_queries,) array of group sizes
        """
        all_features: list[list[float]] = []
        all_labels: list[int] = []
        groups: list[int] = []

        protocols = ["modbus", "dnp3", "opc-ua", "ethernet-ip", "profinet"]
        asset_types = ["plc", "rtu", "hmi", "scada", "dcs"]

        for _ in range(n_queries):
            query_emb = self._rng.random(embedding_dim).tolist()
            query_protocols = set(self._random.sample(protocols, k=self._random.randint(1, 3)))
            query_assets = set(self._random.sample(asset_types, k=self._random.randint(1, 3)))

            for _ in range(docs_per_query):
                noise = self._rng.normal(0, 0.3, embedding_dim)
                relevance_signal = self._rng.random()

                if relevance_signal > 0.7:
                    doc_emb = (np.array(query_emb) + noise * 0.2).tolist()
                    doc_protocols = query_protocols | set(self._random.sample(protocols, k=1))
                    doc_assets = query_assets
                    days_ago = self._random.randint(0, 60)
                    interactions = self._random.randint(10, 100)
                    label = self._random.choice([3, 4])
                elif relevance_signal > 0.4:
                    doc_emb = (np.array(query_emb) + noise * 0.5).tolist()
                    doc_protocols = set(self._random.sample(protocols, k=2))
                    doc_assets = set(self._random.sample(asset_types, k=2))
                    days_ago = self._random.randint(30, 365)
                    interactions = self._random.randint(1, 30)
                    label = self._random.choice([1, 2])
                else:
                    doc_emb = self._rng.random(embedding_dim).tolist()
                    doc_protocols = set(self._random.sample(protocols, k=1))
                    doc_assets = set(self._random.sample(asset_types, k=1))
                    days_ago = self._random.randint(180, 1000)
                    interactions = self._random.randint(0, 5)
                    label = 0

                published = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)

                features = self._extractor.extract_features(
                    query_embedding=query_emb,
                    doc_embedding=doc_emb,
                    doc_published=published,
                    query_protocols=query_protocols,
                    doc_protocols=doc_protocols,
                    query_asset_types=query_assets,
                    doc_asset_types=doc_assets,
                    interaction_count=interactions,
                )
                all_features.append(features)
                all_labels.append(label)

            groups.append(docs_per_query)

        return (
            np.array(all_features, dtype=np.float32),
            np.array(all_labels, dtype=np.int32),
            np.array(groups, dtype=np.int32),
        )
