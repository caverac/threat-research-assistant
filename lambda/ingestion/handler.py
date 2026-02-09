"""AWS Lambda handler for S3-triggered threat document ingestion.

Handles both EventBridge S3 events and native S3 notification events.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import boto3

from core.config import Settings
from embeddings.client import BedrockEmbeddingClient
from embeddings.index import EmbeddingIndexer
from embeddings.store import FAISSVectorStore
from ingestion.chunker import TextChunker
from ingestion.parser import DocumentParser

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SOURCE_TYPE_MAP: dict[str, str] = {
    "advisories": "advisory",
    "threat_reports": "threat_report",
    "incidents": "incident",
}


def _detect_source_type(key: str) -> str:
    """Determine source type from S3 key prefix."""
    for prefix, source_type in SOURCE_TYPE_MAP.items():
        if key.startswith(f"{prefix}/"):
            return source_type
    raise ValueError(f"Cannot determine source_type from S3 key: {key}")


def _extract_bucket_key_pairs(event: dict[str, Any]) -> list[tuple[str, str]]:
    """Extract (bucket, key) pairs from either EventBridge or S3 notification events."""
    pairs: list[tuple[str, str]] = []

    if "detail" in event and event.get("source") == "aws.s3":
        # EventBridge S3 event format
        detail = event["detail"]
        bucket = detail["bucket"]["name"]
        key = detail["object"]["key"]
        pairs.append((bucket, key))
    else:
        # Native S3 notification format
        for record in event.get("Records", []):
            bucket = record["s3"]["bucket"]["name"]
            key = record["s3"]["object"]["key"]
            pairs.append((bucket, key))

    return pairs


def main(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda entry point — process S3 events.

    Parameters
    ----------
    event : dict
        EventBridge or S3 event notification payload.
    context : Any
        Lambda context (unused).

    Returns
    -------
    dict
        Status and number of chunks added.
    """
    settings = _build_settings()
    s3_client = boto3.client("s3", region_name=settings.aws_region)
    parser = DocumentParser()
    chunker = TextChunker(settings)
    embedding_client = BedrockEmbeddingClient(settings)

    models_bucket = os.environ.get("TRA_S3_MODELS_BUCKET", "")
    models_prefix = os.environ.get("TRA_S3_MODELS_PREFIX", "faiss_index")

    total_chunks_added = 0

    for source_bucket, source_key in _extract_bucket_key_pairs(event):
        logger.info("Processing s3://%s/%s", source_bucket, source_key)

        source_type = _detect_source_type(source_key)

        obj = s3_client.get_object(Bucket=source_bucket, Key=source_key)
        data = json.loads(obj["Body"].read().decode("utf-8"))

        if source_type == "advisory":
            advisory = parser.parse_advisory(data)
            chunks = chunker.chunk_advisory(advisory)
        elif source_type == "threat_report":
            report = parser.parse_threat_report(data)
            chunks = chunker.chunk_threat_report(report)
        else:
            incident = parser.parse_incident(data)
            chunks = chunker.chunk_incident(incident)

        if not chunks:
            logger.warning("No chunks produced for %s", source_key)
            continue

        with tempfile.TemporaryDirectory() as tmpdir:
            index_dir = Path(tmpdir) / "faiss_index"
            index_dir.mkdir()
            store = FAISSVectorStore()

            try:
                s3_client.download_file(models_bucket, f"{models_prefix}/index.faiss", str(index_dir / "index.faiss"))
                s3_client.download_file(models_bucket, f"{models_prefix}/metadata.json", str(index_dir / "metadata.json"))
                store.load(index_dir)
                logger.info("Loaded existing index with %d chunks", store.count())
            except Exception:  # pylint: disable=broad-exception-caught
                logger.info("No existing index found — starting fresh")

            indexer = EmbeddingIndexer(embedding_client, store)
            indexed = indexer.index_chunks(chunks)
            total_chunks_added += indexed

            store.save(index_dir)
            s3_client.upload_file(str(index_dir / "index.faiss"), models_bucket, f"{models_prefix}/index.faiss")
            s3_client.upload_file(str(index_dir / "metadata.json"), models_bucket, f"{models_prefix}/metadata.json")
            logger.info("Uploaded updated index (%d total chunks)", store.count())

    return {"status": "ok", "chunks_added": total_chunks_added}


def _build_settings() -> Settings:
    """Build Settings from Lambda environment variables."""
    return Settings()
