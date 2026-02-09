"""Bedrock Claude assistant client for research queries."""

from __future__ import annotations

import json
from typing import Any

import boto3
from botocore.exceptions import ClientError

from core.config import Settings


class BedrockAssistantClient:
    """Interact with Bedrock Claude for research assistance."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._model_id = self._settings.bedrock_llm_model_id
        self._max_tokens = self._settings.bedrock_max_tokens
        self._client = self._create_client()

    def _create_client(self) -> Any:
        kwargs: dict[str, Any] = {"region_name": self._settings.aws_region}
        if self._settings.aws_endpoint_url:
            kwargs["endpoint_url"] = self._settings.aws_endpoint_url
        return boto3.client("bedrock-runtime", **kwargs)

    def invoke(self, messages: list[dict[str, str]], system: str | None = None, tools: list[dict] | None = None) -> dict[str, Any]:
        """Invoke Bedrock Claude with messages."""
        body: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self._max_tokens,
            "messages": messages,
        }
        if system:
            body["system"] = system
        if tools:
            body["tools"] = tools

        try:
            response = self._client.invoke_model(
                modelId=self._model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            response_body: dict[str, Any] = json.loads(response["body"].read())
            return response_body
        except ClientError as e:
            raise RuntimeError(f"Bedrock assistant request failed: {e}") from e

    def generate(self, prompt: str, system: str | None = None) -> str:
        """Generate a text response from a simple prompt."""
        messages = [{"role": "user", "content": prompt}]
        response = self.invoke(messages, system=system)
        content = response.get("content", [])
        text_parts = [block["text"] for block in content if block.get("type") == "text"]
        return "\n".join(text_parts)

    @property
    def model_id(self) -> str:
        """Return the Bedrock model ID."""
        return self._model_id

    def invoke_with_tools(self, messages: list[dict[str, str]], system: str | None = None, tools: list[dict] | None = None) -> dict[str, Any]:
        """Invoke Claude with tool-calling support and return the full response."""
        return self.invoke(messages, system=system, tools=tools)
