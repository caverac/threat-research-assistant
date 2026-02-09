"""LightGBM model inference for document ranking."""

from __future__ import annotations

from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

from recommender.data import FEATURE_NAMES
from recommender.features import FeatureExtractor


class RecommenderPredictor:
    """Score and rank candidate documents using the trained LightGBM model."""

    def __init__(self, model: lgb.LGBMRanker | None = None) -> None:
        self._model = model
        self._extractor = FeatureExtractor()

    @classmethod
    def from_path(cls, model_path: Path) -> RecommenderPredictor:
        """Load a predictor from a saved model file."""
        model = joblib.load(model_path)
        return cls(model=model)

    def predict_scores(self, features: np.ndarray) -> np.ndarray:
        """Predict relevance scores for feature matrix."""
        if self._model is None:
            raise RuntimeError("No model loaded")
        df = pd.DataFrame(features, columns=FEATURE_NAMES)
        scores: np.ndarray = self._model.predict(df)
        return scores

    def rank_documents(
        self,
        query_embedding: list[float],
        candidates: list[dict],
        top_k: int = 10,
    ) -> list[tuple[dict, float]]:
        """Rank candidate documents by predicted relevance.

        Each candidate dict should have:
            - embedding: list[float]
            - published: datetime
            - protocols: set[str]
            - asset_types: set[str]
            - interaction_count: int (optional)
        """
        if self._model is None:
            raise RuntimeError("No model loaded")

        if not candidates:
            return []

        features_list: list[list[float]] = []
        query_protocols: set[str] = set()
        query_assets: set[str] = set()

        for candidate in candidates:
            features = self._extractor.extract_features(
                query_embedding=query_embedding,
                doc_embedding=candidate["embedding"],
                doc_published=candidate["published"],
                query_protocols=query_protocols,
                doc_protocols=set(candidate.get("protocols", [])),
                query_asset_types=query_assets,
                doc_asset_types=set(candidate.get("asset_types", [])),
                interaction_count=candidate.get("interaction_count", 0),
            )
            features_list.append(features)

        features_array = np.array(features_list, dtype=np.float32)
        scores = self.predict_scores(features_array)

        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return [(doc, float(score)) for doc, score in ranked[:top_k]]
