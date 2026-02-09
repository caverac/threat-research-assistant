"""Application settings via pydantic-settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="TRA_", env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AWS
    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = Field(default=None, description="LocalStack endpoint override")

    # Bedrock
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v2:0"
    bedrock_llm_model_id: str = "us.anthropic.claude-opus-4-5-20251101-v1:0"
    bedrock_max_tokens: int = 4096

    # Vector store
    vector_store_type: str = Field(default="faiss", description="faiss or opensearch")
    faiss_index_path: Path = Path("data/faiss_index")
    opensearch_endpoint: str | None = None
    opensearch_index_name: str = "threat-documents"

    # Data
    data_dir: Path = Path("data")

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Retrieval
    retrieval_top_k: int = 20
    rerank_top_k: int = 5

    # S3 sync (production — download index/models from S3 at startup)
    s3_index_bucket: str | None = None
    s3_index_prefix: str = "faiss_index"
    s3_models_bucket: str | None = None
    s3_models_prefix: str = "models"

    # Recommender
    recommender_model_path: Path = Path("models/recommender.joblib")

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
