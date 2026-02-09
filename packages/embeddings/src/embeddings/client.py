"""Bedrock Titan embedding client."""

from __future__ import annotations

import json
from typing import Any

import boto3
import numpy as np
from botocore.exceptions import ClientError

from core.config import Settings


class BedrockEmbeddingClient:
    """Generate embeddings using AWS Bedrock Titan Embeddings model."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._model_id = self._settings.bedrock_embedding_model_id
        self._client = self._create_client()

    def _create_client(self) -> Any:
        kwargs: dict[str, Any] = {"region_name": self._settings.aws_region}
        if self._settings.aws_endpoint_url:
            kwargs["endpoint_url"] = self._settings.aws_endpoint_url
        return boto3.client("bedrock-runtime", **kwargs)

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text string."""
        body = json.dumps({"inputText": text})
        try:
            response = self._client.invoke_model(modelId=self._model_id, body=body, contentType="application/json", accept="application/json")
            response_body = json.loads(response["body"].read())
            embedding: list[float] = response_body["embedding"]
            return embedding
        except ClientError as e:
            raise RuntimeError(f"Bedrock embedding request failed: {e}") from e

    def embed_texts(self, texts: list[str], batch_size: int = 10) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            for text in batch:
                embeddings.append(self.embed_text(text))
        return embeddings

    def embed_texts_as_numpy(self, texts: list[str], batch_size: int = 10) -> np.ndarray:
        """Generate embeddings and return as numpy array."""
        embeddings = self.embed_texts(texts, batch_size)
        return np.array(embeddings, dtype=np.float32)
