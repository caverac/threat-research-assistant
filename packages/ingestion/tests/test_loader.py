"""Tests for the DataLoader."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from core.config import Settings
from ingestion.loader import DataLoader


class TestDataLoader:
    """Tests for DataLoader functionality."""

    def test_load_json_directory(self, tmp_data_dir: Path) -> None:
        """Verify loading JSON files from a valid directory."""
        settings = Settings(data_dir=tmp_data_dir)
        loader = DataLoader(settings)
        docs = loader.load_json_directory(tmp_data_dir / "advisories")
        assert len(docs) == 1
        assert docs[0]["id"] == "ICSA-2024-001"

    def test_load_json_directory_empty(self, tmp_path: Path) -> None:
        """Verify loading from an empty directory returns no documents."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        loader = DataLoader()
        docs = loader.load_json_directory(empty_dir)
        assert not docs

    def test_load_json_directory_nonexistent(self) -> None:
        """Verify loading from a nonexistent directory returns no documents."""
        loader = DataLoader()
        docs = loader.load_json_directory(Path("/nonexistent"))
        assert not docs

    def test_load_advisories(self, tmp_data_dir: Path) -> None:
        """Verify loading advisory documents from the data directory."""
        settings = Settings(data_dir=tmp_data_dir)
        loader = DataLoader(settings)
        docs = loader.load_advisories()
        assert len(docs) == 1
        assert docs[0]["id"] == "ICSA-2024-001"

    def test_load_threat_reports(self, tmp_data_dir: Path) -> None:
        """Verify loading threat report documents from the data directory."""
        settings = Settings(data_dir=tmp_data_dir)
        loader = DataLoader(settings)
        docs = loader.load_threat_reports()
        assert len(docs) == 1
        assert docs[0]["id"] == "TR-2024-001"

    def test_load_incidents(self, tmp_data_dir: Path) -> None:
        """Verify loading incident documents from the data directory."""
        settings = Settings(data_dir=tmp_data_dir)
        loader = DataLoader(settings)
        docs = loader.load_incidents()
        assert len(docs) == 1
        assert docs[0]["id"] == "INC-2024-001"

    def test_load_from_s3(self) -> None:
        """Verify loading JSON documents from an S3 bucket."""
        mock_s3 = MagicMock()
        mock_paginator = MagicMock()
        mock_s3.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {"Contents": [{"Key": "prefix/doc1.json"}]},
        ]
        mock_body = MagicMock()
        mock_body.read.return_value = b'{"id": "test-001"}'
        mock_s3.get_object.return_value = {"Body": mock_body}

        with patch("ingestion.loader.boto3.client", return_value=mock_s3):
            loader = DataLoader()
            docs = loader.load_from_s3("my-bucket", "prefix/")
            assert len(docs) == 1
            assert docs[0]["id"] == "test-001"
            mock_s3.get_paginator.assert_called_once_with("list_objects_v2")

    def test_load_from_s3_skips_non_json(self) -> None:
        """Verify that non-JSON files in S3 are skipped during loading."""
        mock_s3 = MagicMock()
        mock_paginator = MagicMock()
        mock_s3.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {"Contents": [{"Key": "prefix/readme.txt"}, {"Key": "prefix/doc.json"}]},
        ]
        mock_body = MagicMock()
        mock_body.read.return_value = b'{"id": "doc"}'
        mock_s3.get_object.return_value = {"Body": mock_body}

        with patch("ingestion.loader.boto3.client", return_value=mock_s3):
            loader = DataLoader()
            docs = loader.load_from_s3("my-bucket", "prefix/")
            assert len(docs) == 1

    def test_load_from_s3_client_error(self) -> None:
        """Verify that S3 ClientError is wrapped in a RuntimeError."""
        mock_s3 = MagicMock()
        mock_s3.get_paginator.side_effect = ClientError({"Error": {"Code": "NoSuchBucket", "Message": "Not found"}}, "ListObjectsV2")

        with patch("ingestion.loader.boto3.client", return_value=mock_s3):
            loader = DataLoader()
            with pytest.raises(RuntimeError, match="Failed to load from S3"):
                loader.load_from_s3("nonexistent-bucket", "prefix/")

    def test_load_from_s3_with_endpoint_url(self) -> None:
        """Verify that a custom endpoint URL is passed to the S3 client."""
        settings = Settings(aws_endpoint_url="http://localhost:4566")
        mock_s3 = MagicMock()
        mock_paginator = MagicMock()
        mock_s3.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Contents": []}]

        with patch("ingestion.loader.boto3.client", return_value=mock_s3) as mock_client:
            loader = DataLoader(settings)
            loader.load_from_s3("bucket", "prefix/")
            mock_client.assert_called_once_with("s3", region_name="us-east-1", endpoint_url="http://localhost:4566")
