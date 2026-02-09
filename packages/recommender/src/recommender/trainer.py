"""LightGBM learning-to-rank trainer."""

from __future__ import annotations

from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

from recommender.data import FEATURE_NAMES, TrainingDataGenerator


class RecommenderTrainer:
    """Train a LightGBM ranker for document reranking."""

    def __init__(
        self,
        n_estimators: int = 100,
        learning_rate: float = 0.1,
        num_leaves: int = 31,
        max_depth: int = -1,
    ) -> None:
        self._n_estimators = n_estimators
        self._learning_rate = learning_rate
        self._num_leaves = num_leaves
        self._max_depth = max_depth
        self._model: lgb.LGBMRanker | None = None

    def train(self, features: np.ndarray, labels: np.ndarray, groups: np.ndarray) -> lgb.LGBMRanker:
        """Train the LightGBM ranker model."""
        self._model = lgb.LGBMRanker(
            objective="lambdarank",
            metric="ndcg",
            n_estimators=self._n_estimators,
            learning_rate=self._learning_rate,
            num_leaves=self._num_leaves,
            max_depth=self._max_depth,
            verbose=-1,
        )
        df = pd.DataFrame(features, columns=FEATURE_NAMES)
        self._model.fit(df, labels, group=groups)
        return self._model

    def train_from_synthetic(self, n_queries: int = 200, docs_per_query: int = 20, seed: int = 42) -> lgb.LGBMRanker:
        """Train the model using synthetic training data."""
        generator = TrainingDataGenerator(seed=seed)
        features, labels, groups = generator.generate(n_queries, docs_per_query)
        return self.train(features, labels, groups)

    def get_feature_importance(self) -> dict[str, float]:
        """Get feature importance scores from the trained model."""
        if self._model is None:
            raise RuntimeError("Model not trained yet")
        importances = self._model.feature_importances_
        return dict(zip(FEATURE_NAMES, [float(v) for v in importances]))

    def save(self, path: Path) -> None:
        """Save the trained model to disk."""
        if self._model is None:
            raise RuntimeError("Model not trained yet")
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._model, path)

    @property
    def model(self) -> lgb.LGBMRanker | None:
        """Return the trained LightGBM model, or None if not yet trained."""
        return self._model
