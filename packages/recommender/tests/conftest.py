"""Shared fixtures for recommender tests."""

import lightgbm as lgb
import numpy as np
import pytest

from recommender.data import TrainingDataGenerator
from recommender.trainer import RecommenderTrainer


@pytest.fixture
def training_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate synthetic training data for recommender tests."""
    generator = TrainingDataGenerator(seed=42)
    return generator.generate(n_queries=10, docs_per_query=10)


@pytest.fixture
def trained_model(training_data: tuple[np.ndarray, np.ndarray, np.ndarray]) -> lgb.LGBMRanker:  # pylint: disable=redefined-outer-name
    """Train and return a lightweight LGBMRanker model for testing."""
    features, labels, groups = training_data
    trainer = RecommenderTrainer(n_estimators=10)
    trainer.train(features, labels, groups)
    assert trainer.model is not None
    return trainer.model
