"""Tests for the FeatureExtractor."""

from datetime import datetime, timedelta, timezone

import pytest

from recommender.features import FeatureExtractor


class TestFeatureExtractor:
    """Tests for FeatureExtractor functionality."""

    def test_embedding_similarity_identical(self) -> None:
        """Verify that identical vectors produce a similarity of 1.0."""
        extractor = FeatureExtractor()
        vec = [1.0, 0.0, 0.0]
        assert extractor.embedding_similarity(vec, vec) == pytest.approx(1.0)

    def test_embedding_similarity_orthogonal(self) -> None:
        """Verify that orthogonal vectors produce a similarity of 0.0."""
        extractor = FeatureExtractor()
        assert extractor.embedding_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0, abs=1e-6)

    def test_embedding_similarity_zero_vector(self) -> None:
        """Verify that a zero vector produces a similarity of 0.0."""
        extractor = FeatureExtractor()
        assert extractor.embedding_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0

    def test_temporal_decay_recent(self) -> None:
        """Verify that a recent date produces a decay close to 1.0."""
        extractor = FeatureExtractor()
        now = datetime.now(tz=timezone.utc)
        score = extractor.temporal_decay(now)
        assert score == pytest.approx(1.0, abs=0.01)

    def test_temporal_decay_old(self) -> None:
        """Verify that a date older than the half-life decays below 0.5."""
        extractor = FeatureExtractor()
        old_date = datetime.now(tz=timezone.utc) - timedelta(days=365)
        score = extractor.temporal_decay(old_date, half_life_days=180)
        assert 0 < score < 0.5

    def test_temporal_decay_future(self) -> None:
        """Verify that a future date is clamped to a decay of 1.0."""
        extractor = FeatureExtractor()
        future = datetime.now(tz=timezone.utc) + timedelta(days=10)
        assert extractor.temporal_decay(future) == 1.0

    def test_metadata_match_identical(self) -> None:
        """Verify that identical metadata sets produce a match score of 1.0."""
        extractor = FeatureExtractor()
        vals = {"modbus", "dnp3"}
        assert extractor.metadata_match(vals, vals) == 1.0

    def test_metadata_match_no_overlap(self) -> None:
        """Verify that disjoint metadata sets produce a match score of 0.0."""
        extractor = FeatureExtractor()
        assert extractor.metadata_match({"modbus"}, {"dnp3"}) == 0.0

    def test_metadata_match_partial(self) -> None:
        """Verify that partially overlapping sets produce the expected Jaccard score."""
        extractor = FeatureExtractor()
        score = extractor.metadata_match({"modbus", "dnp3"}, {"modbus", "opc-ua"})
        assert score == pytest.approx(1 / 3)

    def test_metadata_match_empty(self) -> None:
        """Verify that empty metadata sets produce a match score of 0.0."""
        extractor = FeatureExtractor()
        assert extractor.metadata_match(set(), set()) == 0.0
        assert extractor.metadata_match({"modbus"}, set()) == 0.0

    def test_popularity_score_zero(self) -> None:
        """Verify that zero interactions produce a popularity score of 0.0."""
        extractor = FeatureExtractor()
        assert extractor.popularity_score(0) == 0.0

    def test_popularity_score_max(self) -> None:
        """Verify that max interactions produce a popularity score of 1.0."""
        extractor = FeatureExtractor()
        score = extractor.popularity_score(100, max_interactions=100)
        assert score == pytest.approx(1.0)

    def test_popularity_score_mid(self) -> None:
        """Verify that a mid-range interaction count produces a score between 0 and 1."""
        extractor = FeatureExtractor()
        score = extractor.popularity_score(10, max_interactions=100)
        assert 0 < score < 1

    def test_recency_boost_new(self) -> None:
        """Verify that a very recent date receives a boost close to 1.0."""
        extractor = FeatureExtractor()
        now = datetime.now(tz=timezone.utc)
        assert extractor.recency_boost(now) == pytest.approx(1.0, abs=0.05)

    def test_recency_boost_old(self) -> None:
        """Verify that a date beyond the boost window receives no boost."""
        extractor = FeatureExtractor()
        old = datetime.now(tz=timezone.utc) - timedelta(days=60)
        assert extractor.recency_boost(old, boost_days=30) == 0.0

    def test_recency_boost_future(self) -> None:
        """Verify that a future date receives the maximum boost of 1.0."""
        extractor = FeatureExtractor()
        future = datetime.now(tz=timezone.utc) + timedelta(days=5)
        assert extractor.recency_boost(future) == 1.0

    def test_extract_features_length(self) -> None:
        """Verify that extract_features returns exactly 6 float values."""
        extractor = FeatureExtractor()
        features = extractor.extract_features(
            query_embedding=[0.1, 0.2],
            doc_embedding=[0.3, 0.4],
            doc_published=datetime.now(tz=timezone.utc),
            query_protocols={"modbus"},
            doc_protocols={"modbus", "dnp3"},
            query_asset_types={"plc"},
            doc_asset_types={"plc"},
            interaction_count=5,
        )
        assert len(features) == 6
        assert all(isinstance(f, float) for f in features)
