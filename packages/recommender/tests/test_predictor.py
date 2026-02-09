"""Tests for the RecommenderPredictor."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pytest

from recommender.predictor import RecommenderPredictor


class TestRecommenderPredictor:
    """Tests for RecommenderPredictor functionality."""

    def test_predict_scores(self, trained_model: lgb.LGBMRanker) -> None:
        """Verify that predict_scores returns an array with the correct shape."""
        predictor = RecommenderPredictor(model=trained_model)
        features = np.random.default_rng(42).random((5, 6)).astype(np.float32)
        scores = predictor.predict_scores(features)
        assert scores.shape == (5,)

    def test_predict_scores_no_model(self) -> None:
        """Verify that predict_scores raises RuntimeError when no model is loaded."""
        predictor = RecommenderPredictor()
        with pytest.raises(RuntimeError, match="No model loaded"):
            predictor.predict_scores(np.zeros((1, 6), dtype=np.float32))

    def test_rank_documents(self, trained_model: lgb.LGBMRanker) -> None:
        """Verify that rank_documents returns scored and sorted results."""
        predictor = RecommenderPredictor(model=trained_model)
        query_emb = [0.1] * 8
        candidates = [
            {
                "id": f"doc-{i}",
                "embedding": np.random.default_rng(i).random(8).tolist(),
                "published": datetime.now(tz=timezone.utc) - timedelta(days=i * 30),
                "protocols": {"modbus"},
                "asset_types": {"plc"},
                "interaction_count": i * 10,
            }
            for i in range(5)
        ]
        results = predictor.rank_documents(query_emb, candidates, top_k=3)
        assert len(results) == 3
        assert all(isinstance(r, tuple) for r in results)
        assert all(isinstance(r[1], float) for r in results)

    def test_rank_documents_empty(self, trained_model: lgb.LGBMRanker) -> None:
        """Verify that rank_documents returns an empty list for empty candidates."""
        predictor = RecommenderPredictor(model=trained_model)
        results = predictor.rank_documents([0.1] * 8, [], top_k=5)
        assert results == []

    def test_rank_documents_no_model(self) -> None:
        """Verify that rank_documents raises RuntimeError when no model is loaded."""
        predictor = RecommenderPredictor()
        with pytest.raises(RuntimeError, match="No model loaded"):
            predictor.rank_documents(
                [0.1],
                [{"embedding": [0.1], "published": datetime.now(tz=timezone.utc), "protocols": set(), "asset_types": set()}],
            )

    def test_from_path(self, trained_model: lgb.LGBMRanker, tmp_path: Path) -> None:
        """Verify that a predictor can be loaded from a saved model path."""
        model_path = tmp_path / "model.joblib"
        joblib.dump(trained_model, model_path)

        predictor = RecommenderPredictor.from_path(model_path)
        features = np.random.default_rng(42).random((3, 6)).astype(np.float32)
        scores = predictor.predict_scores(features)
        assert scores.shape == (3,)
