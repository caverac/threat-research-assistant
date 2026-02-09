"""Load threat intelligence data from JSON files or S3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError

from core.config import Settings


class DataLoader:
    """Load threat intelligence data from local filesystem or S3."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()

    def load_json_directory(self, directory: Path) -> list[dict[str, Any]]:
        """Load all JSON files from a directory."""
        documents: list[dict[str, Any]] = []
        if not directory.exists():
            return documents
        for path in sorted(directory.glob("*.json")):
            documents.append(self._load_json_file(path))
        return documents

    def load_advisories(self) -> list[dict[str, Any]]:
        """Load advisory documents from the data directory."""
        return self.load_json_directory(self._settings.data_dir / "advisories")

    def load_threat_reports(self) -> list[dict[str, Any]]:
        """Load threat report documents from the data directory."""
        return self.load_json_directory(self._settings.data_dir / "threat_reports")

    def load_incidents(self) -> list[dict[str, Any]]:
        """Load incident documents from the data directory."""
        return self.load_json_directory(self._settings.data_dir / "incidents")

    def load_from_s3(self, bucket: str, prefix: str) -> list[dict[str, Any]]:
        """Load JSON documents from an S3 bucket."""
        client_kwargs: dict[str, Any] = {"region_name": self._settings.aws_region}
        if self._settings.aws_endpoint_url:
            client_kwargs["endpoint_url"] = self._settings.aws_endpoint_url
        s3 = boto3.client("s3", **client_kwargs)
        documents: list[dict[str, Any]] = []
        try:
            paginator = s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    if obj["Key"].endswith(".json"):
                        response = s3.get_object(Bucket=bucket, Key=obj["Key"])
                        body = response["Body"].read().decode("utf-8")
                        documents.append(json.loads(body))
        except ClientError as e:
            raise RuntimeError(f"Failed to load from S3 s3://{bucket}/{prefix}: {e}") from e
        return documents

    @staticmethod
    def _load_json_file(path: Path) -> dict[str, Any]:
        """Load and parse a single JSON file."""
        with open(path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        return data
