"""Tests for the BedrockEmbeddingClient."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from botocore.exceptions import ClientError

from core.config import Settings
from embeddings.client import BedrockEmbeddingClient


class TestBedrockEmbeddingClient:
    """Tests for BedrockEmbeddingClient methods."""

    def test_embed_text(self) -> None:
        """Verify embed_text returns the embedding from the model response."""
        mock_client = MagicMock()
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({"embedding": [0.1, 0.2, 0.3]}).encode()
        mock_client.invoke_model.return_value = {"body": mock_body}

        with patch("embeddings.client.boto3.client", return_value=mock_client):
            client = BedrockEmbeddingClient()
            embedding = client.embed_text("test text")
            assert embedding == [0.1, 0.2, 0.3]
            mock_client.invoke_model.assert_called_once()

    def test_embed_text_failure(self) -> None:
        """Verify ClientError is wrapped in RuntimeError."""
        mock_client = MagicMock()
        mock_client.invoke_model.side_effect = ClientError({"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}}, "InvokeModel")

        with patch("embeddings.client.boto3.client", return_value=mock_client):
            client = BedrockEmbeddingClient()
            with pytest.raises(RuntimeError, match="Bedrock embedding request failed"):
                client.embed_text("test text")

    def test_embed_texts(self) -> None:
        """Verify embed_texts returns one embedding per input text."""
        mock_client = MagicMock()
        call_count = 0

        def mock_invoke(**_kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            mock_body = MagicMock()
            mock_body.read.return_value = json.dumps({"embedding": [float(call_count)] * 3}).encode()
            return {"body": mock_body}

        mock_client.invoke_model.side_effect = mock_invoke

        with patch("embeddings.client.boto3.client", return_value=mock_client):
            client = BedrockEmbeddingClient()
            embeddings = client.embed_texts(["text1", "text2"])
            assert len(embeddings) == 2
            assert embeddings[0] == [1.0, 1.0, 1.0]
            assert embeddings[1] == [2.0, 2.0, 2.0]

    def test_embed_texts_as_numpy(self) -> None:
        """Verify embed_texts_as_numpy returns a float32 numpy array."""
        mock_client = MagicMock()
        call_count = 0

        def mock_invoke(**_kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            mock_body = MagicMock()
            mock_body.read.return_value = json.dumps({"embedding": [float(call_count)] * 3}).encode()
            return {"body": mock_body}

        mock_client.invoke_model.side_effect = mock_invoke

        with patch("embeddings.client.boto3.client", return_value=mock_client):
            client = BedrockEmbeddingClient()
            result = client.embed_texts_as_numpy(["text1", "text2"])
            assert isinstance(result, np.ndarray)
            assert result.shape == (2, 3)
            assert result.dtype == np.float32

    def test_client_with_endpoint_url(self) -> None:
        """Verify endpoint_url is forwarded to boto3 when configured."""
        settings = Settings(aws_endpoint_url="http://localhost:4566")
        with patch("embeddings.client.boto3.client") as mock_boto:
            BedrockEmbeddingClient(settings)
            mock_boto.assert_called_once_with("bedrock-runtime", region_name="us-east-1", endpoint_url="http://localhost:4566")
