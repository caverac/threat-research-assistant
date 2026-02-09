"""Tests for application configuration via pydantic-settings."""

from pathlib import Path
from unittest.mock import patch

from core.config import Settings


class TestSettings:
    """Tests for the Settings model defaults and env overrides."""

    def test_default_settings(self) -> None:
        """Verify all default setting values."""
        settings = Settings()
        assert settings.aws_region == "us-east-1"
        assert settings.aws_endpoint_url is None
        assert settings.bedrock_embedding_model_id == "amazon.titan-embed-text-v2:0"
        assert settings.bedrock_llm_model_id == "us.anthropic.claude-opus-4-5-20251101-v1:0"
        assert settings.bedrock_max_tokens == 4096
        assert settings.vector_store_type == "faiss"
        assert settings.faiss_index_path == Path("data/faiss_index")
        assert settings.chunk_size == 512
        assert settings.chunk_overlap == 64
        assert settings.retrieval_top_k == 20
        assert settings.rerank_top_k == 5
        assert settings.api_port == 8000

    def test_s3_settings_default_to_none(self) -> None:
        """Verify S3 bucket settings default to None."""
        settings = Settings()
        assert settings.s3_index_bucket is None
        assert settings.s3_index_prefix == "faiss_index"
        assert settings.s3_models_bucket is None
        assert settings.s3_models_prefix == "models"

    def test_s3_settings_from_env(self) -> None:
        """Verify S3 settings are loaded from TRA_ environment variables."""
        with patch.dict(
            "os.environ",
            {
                "TRA_S3_INDEX_BUCKET": "my-index-bucket",
                "TRA_S3_INDEX_PREFIX": "custom/prefix",
                "TRA_S3_MODELS_BUCKET": "my-models-bucket",
                "TRA_S3_MODELS_PREFIX": "custom/models",
            },
        ):
            settings = Settings()
            assert settings.s3_index_bucket == "my-index-bucket"
            assert settings.s3_index_prefix == "custom/prefix"
            assert settings.s3_models_bucket == "my-models-bucket"
            assert settings.s3_models_prefix == "custom/models"

    def test_env_override(self) -> None:
        """Verify environment variables override defaults."""
        with patch.dict("os.environ", {"TRA_AWS_REGION": "eu-west-1", "TRA_CHUNK_SIZE": "1024"}):
            settings = Settings()
            assert settings.aws_region == "eu-west-1"
            assert settings.chunk_size == 1024

    def test_localstack_endpoint(self) -> None:
        """Verify endpoint_url is read from TRA_AWS_ENDPOINT_URL."""
        with patch.dict("os.environ", {"TRA_AWS_ENDPOINT_URL": "http://localhost:4566"}):
            settings = Settings()
            assert settings.aws_endpoint_url == "http://localhost:4566"

    def test_opensearch_settings(self) -> None:
        """Verify OpenSearch settings are loaded from environment."""
        with patch.dict("os.environ", {"TRA_VECTOR_STORE_TYPE": "opensearch", "TRA_OPENSEARCH_ENDPOINT": "https://search.example.com"}):
            settings = Settings()
            assert settings.vector_store_type == "opensearch"
            assert settings.opensearch_endpoint == "https://search.example.com"
