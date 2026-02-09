"""Tests for the BedrockAssistantClient."""

import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from assistant.client import BedrockAssistantClient
from core.config import Settings


class TestBedrockAssistantClient:
    """Tests for BedrockAssistantClient methods."""

    def test_invoke(self) -> None:
        """Verify invoke sends messages and returns parsed response."""
        mock_client = MagicMock()
        mock_body = MagicMock()
        response_data = {"content": [{"type": "text", "text": "Hello"}], "stop_reason": "end_turn"}
        mock_body.read.return_value = json.dumps(response_data).encode()
        mock_client.invoke_model.return_value = {"body": mock_body}

        with patch("assistant.client.boto3.client", return_value=mock_client):
            client = BedrockAssistantClient()
            result = client.invoke([{"role": "user", "content": "test"}])
            assert result["content"][0]["text"] == "Hello"

    def test_invoke_with_system(self) -> None:
        """Verify system prompt is included in the request body."""
        mock_client = MagicMock()
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({"content": [{"type": "text", "text": "ok"}]}).encode()
        mock_client.invoke_model.return_value = {"body": mock_body}

        with patch("assistant.client.boto3.client", return_value=mock_client):
            client = BedrockAssistantClient()
            client.invoke([{"role": "user", "content": "test"}], system="You are helpful.")
            call_body = json.loads(mock_client.invoke_model.call_args[1]["body"])
            assert call_body["system"] == "You are helpful."

    def test_invoke_with_tools(self) -> None:
        """Verify tools are included in the request body."""
        mock_client = MagicMock()
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({"content": [{"type": "text", "text": "ok"}]}).encode()
        mock_client.invoke_model.return_value = {"body": mock_body}

        tools = [{"name": "test_tool", "description": "A test", "input_schema": {"type": "object", "properties": {}}}]
        with patch("assistant.client.boto3.client", return_value=mock_client):
            client = BedrockAssistantClient()
            client.invoke([{"role": "user", "content": "test"}], tools=tools)
            call_body = json.loads(mock_client.invoke_model.call_args[1]["body"])
            assert "tools" in call_body

    def test_invoke_failure(self) -> None:
        """Verify ClientError is wrapped in RuntimeError."""
        mock_client = MagicMock()
        mock_client.invoke_model.side_effect = ClientError({"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}}, "InvokeModel")

        with patch("assistant.client.boto3.client", return_value=mock_client):
            client = BedrockAssistantClient()
            with pytest.raises(RuntimeError, match="Bedrock assistant request failed"):
                client.invoke([{"role": "user", "content": "test"}])

    def test_generate(self) -> None:
        """Verify generate returns extracted text from model response."""
        mock_client = MagicMock()
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({"content": [{"type": "text", "text": "Generated response"}]}).encode()
        mock_client.invoke_model.return_value = {"body": mock_body}

        with patch("assistant.client.boto3.client", return_value=mock_client):
            client = BedrockAssistantClient()
            result = client.generate("What is Modbus?")
            assert result == "Generated response"

    def test_generate_empty_content(self) -> None:
        """Verify generate returns empty string for empty content list."""
        mock_client = MagicMock()
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({"content": []}).encode()
        mock_client.invoke_model.return_value = {"body": mock_body}

        with patch("assistant.client.boto3.client", return_value=mock_client):
            client = BedrockAssistantClient()
            result = client.generate("test")
            assert result == ""

    def test_invoke_with_tools_method(self) -> None:
        """Verify invoke_with_tools passes tools through to the model."""
        mock_client = MagicMock()
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({"content": [{"type": "text", "text": "ok"}]}).encode()
        mock_client.invoke_model.return_value = {"body": mock_body}

        tools = [{"name": "search", "description": "Search", "input_schema": {"type": "object", "properties": {}}}]
        with patch("assistant.client.boto3.client", return_value=mock_client):
            client = BedrockAssistantClient()
            result = client.invoke_with_tools([{"role": "user", "content": "test"}], tools=tools)
            assert "content" in result

    def test_model_id_property(self) -> None:
        """Verify model_id returns the configured model identifier."""
        with patch("assistant.client.boto3.client"):
            client = BedrockAssistantClient()
            assert client.model_id == "us.anthropic.claude-opus-4-5-20251101-v1:0"

    def test_client_with_endpoint_url(self) -> None:
        """Verify endpoint_url is forwarded to boto3 when configured."""
        settings = Settings(aws_endpoint_url="http://localhost:4566")
        with patch("assistant.client.boto3.client") as mock_boto:
            BedrockAssistantClient(settings)
            mock_boto.assert_called_once_with("bedrock-runtime", region_name="us-east-1", endpoint_url="http://localhost:4566")
