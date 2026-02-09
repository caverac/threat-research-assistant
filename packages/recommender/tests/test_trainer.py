"""Tests for the RecommenderTrainer."""

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pytest

from recommender.data import FEATURE_NAMES
from recommender.trainer import RecommenderTrainer


class TestRecommenderTrainer:
    """Tests for RecommenderTrainer functionality."""

    def test_train(self, training_data: tuple[np.ndarray, np.ndarray, np.ndarray]) -> None:
        """Verify that training produces a valid LGBMRanker model."""
        features, labels, groups = training_data
        trainer = RecommenderTrainer(n_estimators=10)
        model = trainer.train(features, labels, groups)
        assert isinstance(model, lgb.LGBMRanker)
        assert trainer.model is not None

    def test_train_from_synthetic(self) -> None:
        """Verify that training from synthetic data produces a valid model."""
        trainer = RecommenderTrainer(n_estimators=10)
        model = trainer.train_from_synthetic(n_queries=5, docs_per_query=5)
        assert isinstance(model, lgb.LGBMRanker)

    def test_get_feature_importance(self, training_data: tuple[np.ndarray, np.ndarray, np.ndarray]) -> None:
        """Verify that feature importance returns all expected feature names."""
        features, labels, groups = training_data
        trainer = RecommenderTrainer(n_estimators=10)
        trainer.train(features, labels, groups)
        importance = trainer.get_feature_importance()
        assert set(importance.keys()) == set(FEATURE_NAMES)
        assert all(isinstance(v, float) for v in importance.values())

    def test_get_feature_importance_untrained(self) -> None:
        """Verify that getting importance from an untrained model raises RuntimeError."""
        trainer = RecommenderTrainer()
        with pytest.raises(RuntimeError, match="Model not trained"):
            trainer.get_feature_importance()

    def test_save(self, training_data: tuple[np.ndarray, np.ndarray, np.ndarray], tmp_path: Path) -> None:
        """Verify that a trained model can be saved to disk."""
        features, labels, groups = training_data
        trainer = RecommenderTrainer(n_estimators=10)
        trainer.train(features, labels, groups)
        model_path = tmp_path / "model.joblib"
        trainer.save(model_path)
        assert model_path.exists()

    def test_save_untrained(self, tmp_path: Path) -> None:
        """Verify that saving an untrained model raises RuntimeError."""
        trainer = RecommenderTrainer()
        with pytest.raises(RuntimeError, match="Model not trained"):
            trainer.save(tmp_path / "model.joblib")

    def test_save_creates_parent_dirs(self, training_data: tuple[np.ndarray, np.ndarray, np.ndarray], tmp_path: Path) -> None:
        """Verify that saving creates parent directories if they do not exist."""
        features, labels, groups = training_data
        trainer = RecommenderTrainer(n_estimators=10)
        trainer.train(features, labels, groups)
        model_path = tmp_path / "subdir" / "model.joblib"
        trainer.save(model_path)
        assert model_path.exists()
