"""Dependency injection for API services."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request

from assistant.chain import ResearchChain
from assistant.client import BedrockAssistantClient
from core.config import Settings
from embeddings.client import BedrockEmbeddingClient
from embeddings.store import FAISSVectorStore
from recommender.predictor import RecommenderPredictor
from retrieval.pipeline import RetrievalPipeline
from retrieval.reranker import LightGBMReranker
from retrieval.retriever import HybridRetriever

logger = logging.getLogger(__name__)


def _s3_client(settings: Settings) -> Any:
    """Create a boto3 S3 client from settings."""
    import boto3  # pylint: disable=import-outside-toplevel

    kwargs: dict[str, Any] = {"region_name": settings.aws_region}
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    return boto3.client("s3", **kwargs)


def _download_from_s3(bucket: str, key: str, local_path: Path, settings: Settings) -> bool:
    """Download a single file from S3 to *local_path*.

    Returns True on success, False if the object does not exist.
    """
    from botocore.exceptions import ClientError  # pylint: disable=import-outside-toplevel

    local_path.parent.mkdir(parents=True, exist_ok=True)
    client = _s3_client(settings)
    logger.info("Downloading s3://%s/%s → %s", bucket, key, local_path)
    try:
        client.download_file(bucket, key, str(local_path))
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
            logger.warning("s3://%s/%s not found, skipping", bucket, key)
            return False
        raise
    return True


def _sync_index_from_s3(settings: Settings) -> None:
    """Download FAISS index files from S3 if not already present locally."""
    if not settings.s3_index_bucket:
        return
    index_dir = settings.faiss_index_path
    for filename in ("index.faiss", "metadata.json"):
        local_file = index_dir / filename
        if not local_file.exists():
            s3_key = f"{settings.s3_index_prefix}/{filename}"
            if not _download_from_s3(settings.s3_index_bucket, s3_key, local_file, settings):
                logger.info("FAISS index not available in S3; starting with empty store")
                return


def _sync_model_from_s3(settings: Settings) -> None:
    """Download recommender model from S3 if not already present locally."""
    if not settings.s3_models_bucket:
        return
    local_path = settings.recommender_model_path
    if not local_path.exists():
        s3_key = f"{settings.s3_models_prefix}/recommender.joblib"
        if not _download_from_s3(settings.s3_models_bucket, s3_key, local_path, settings):
            logger.info("Recommender model not available in S3; skipping")
            return


def initialize_services(app: FastAPI) -> None:
    """Initialize all services and store them in app state."""
    settings = Settings()
    app.state.settings = settings

    embedding_client = BedrockEmbeddingClient(settings)
    app.state.embedding_client = embedding_client

    _sync_index_from_s3(settings)

    vector_store = FAISSVectorStore()
    if (settings.faiss_index_path / "index.faiss").exists():
        vector_store.load(settings.faiss_index_path)
    app.state.vector_store = vector_store

    _sync_model_from_s3(settings)

    retriever = HybridRetriever(embedding_client, vector_store)
    app.state.retriever = retriever

    reranker: LightGBMReranker | None = None
    if settings.recommender_model_path.exists():
        predictor = RecommenderPredictor.from_path(settings.recommender_model_path)
        reranker = LightGBMReranker(predictor)
    app.state.reranker = reranker

    pipeline = RetrievalPipeline(retriever, reranker)
    app.state.retrieval_pipeline = pipeline

    assistant_client = BedrockAssistantClient(settings)
    app.state.assistant_client = assistant_client

    chain = ResearchChain(pipeline, assistant_client)
    app.state.research_chain = chain


def shutdown_services(app: FastAPI) -> None:  # pylint: disable=unused-argument
    """Clean up services on shutdown."""


def get_settings(request: Request) -> Settings:
    """Get settings from app state."""
    return request.app.state.settings  # type: ignore[no-any-return]


def get_research_chain(request: Request) -> ResearchChain:
    """Get the research chain from app state."""
    return request.app.state.research_chain  # type: ignore[no-any-return]


def get_vector_store(request: Request) -> FAISSVectorStore:
    """Get the vector store from app state."""
    return request.app.state.vector_store  # type: ignore[no-any-return]


def get_embedding_client(request: Request) -> BedrockEmbeddingClient:
    """Get the embedding client from app state."""
    return request.app.state.embedding_client  # type: ignore[no-any-return]


def reload_index(app: FastAPI) -> tuple[int, int]:
    """Re-download the FAISS index from S3 and hot-swap the in-memory store.

    Returns (previous_count, current_count).
    """
    settings: Settings = app.state.settings
    previous_count = app.state.vector_store.count()

    # Remove local files so _sync_index_from_s3 re-downloads them
    index_dir = settings.faiss_index_path
    for filename in ("index.faiss", "metadata.json"):
        local_file = index_dir / filename
        if local_file.exists():
            local_file.unlink()

    _sync_index_from_s3(settings)

    store = FAISSVectorStore()
    if (index_dir / "index.faiss").exists():
        store.load(index_dir)
    app.state.vector_store = store

    # Rebuild retriever and downstream pipeline with the new store
    retriever = HybridRetriever(app.state.embedding_client, store)
    app.state.retriever = retriever

    pipeline = RetrievalPipeline(retriever, app.state.reranker)
    app.state.retrieval_pipeline = pipeline

    chain = ResearchChain(pipeline, app.state.assistant_client)
    app.state.research_chain = chain

    return previous_count, store.count()
