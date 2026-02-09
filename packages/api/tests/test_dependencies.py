"""Tests for S3 download helpers in api.dependencies."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from api.dependencies import _download_from_s3, _s3_client, _sync_index_from_s3, _sync_model_from_s3
from core.config import Settings


class TestS3Client:
    """Tests for the _s3_client helper."""

    def test_creates_client_with_region(self) -> None:
        """Verify client is created with the configured region."""
        settings = Settings()
        with patch("boto3.client") as mock_client:
            _s3_client(settings)
        mock_client.assert_called_once_with("s3", region_name="us-east-1")

    def test_creates_client_with_endpoint_url(self) -> None:
        """Verify endpoint_url is forwarded when configured."""
        with patch.dict("os.environ", {"TRA_AWS_ENDPOINT_URL": "http://localhost:4566"}):
            settings = Settings()
        with patch("boto3.client") as mock_client:
            _s3_client(settings)
        mock_client.assert_called_once_with("s3", region_name="us-east-1", endpoint_url="http://localhost:4566")


class TestDownloadFromS3:
    """Tests for the _download_from_s3 helper."""

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        """Verify parent directories are created and download_file is called."""
        local_path = tmp_path / "subdir" / "file.bin"
        mock_client = MagicMock()
        with patch("api.dependencies._s3_client", return_value=mock_client):
            result = _download_from_s3("bucket", "key/file.bin", local_path, Settings())
        assert result is True
        assert local_path.parent.exists()
        mock_client.download_file.assert_called_once_with("bucket", "key/file.bin", str(local_path))

    def test_returns_false_on_404(self, tmp_path: Path) -> None:
        """Verify False is returned when S3 object does not exist."""
        from botocore.exceptions import ClientError  # pylint: disable=import-outside-toplevel

        local_path = tmp_path / "file.bin"
        mock_client = MagicMock()
        mock_client.download_file.side_effect = ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject")
        with patch("api.dependencies._s3_client", return_value=mock_client):
            result = _download_from_s3("bucket", "key/file.bin", local_path, Settings())
        assert result is False

    def test_raises_on_non_404_error(self, tmp_path: Path) -> None:
        """Verify non-404 ClientErrors are re-raised."""
        from botocore.exceptions import ClientError  # pylint: disable=import-outside-toplevel

        local_path = tmp_path / "file.bin"
        mock_client = MagicMock()
        mock_client.download_file.side_effect = ClientError({"Error": {"Code": "AccessDenied", "Message": "Forbidden"}}, "HeadObject")
        with patch("api.dependencies._s3_client", return_value=mock_client):
            with pytest.raises(ClientError, match="AccessDenied"):
                _download_from_s3("bucket", "key/file.bin", local_path, Settings())


class TestSyncIndexFromS3:
    """Tests for the _sync_index_from_s3 helper."""

    def test_noop_when_no_bucket_configured(self) -> None:
        """Verify no download when s3_index_bucket is None."""
        settings = Settings()
        assert settings.s3_index_bucket is None
        with patch("api.dependencies._download_from_s3") as mock_dl:
            _sync_index_from_s3(settings)
        mock_dl.assert_not_called()

    def test_downloads_when_bucket_set_and_files_missing(self, tmp_path: Path) -> None:
        """Verify both index files are downloaded when missing."""
        with patch.dict("os.environ", {"TRA_S3_INDEX_BUCKET": "my-bucket", "TRA_FAISS_INDEX_PATH": str(tmp_path / "index")}):
            settings = Settings()
        with patch("api.dependencies._download_from_s3", return_value=True) as mock_dl:
            _sync_index_from_s3(settings)
        assert mock_dl.call_count == 2
        calls = [c.args for c in mock_dl.call_args_list]
        assert calls[0][0] == "my-bucket"
        assert calls[0][1] == "faiss_index/index.faiss"
        assert calls[1][1] == "faiss_index/metadata.json"

    def test_returns_early_when_index_not_in_s3(self, tmp_path: Path) -> None:
        """Verify early return when S3 download returns False (404)."""
        with patch.dict("os.environ", {"TRA_S3_INDEX_BUCKET": "my-bucket", "TRA_FAISS_INDEX_PATH": str(tmp_path / "index")}):
            settings = Settings()
        with patch("api.dependencies._download_from_s3", return_value=False) as mock_dl:
            _sync_index_from_s3(settings)
        mock_dl.assert_called_once()

    def test_skips_existing_files(self, tmp_path: Path) -> None:
        """Verify no download when index files already exist locally."""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        (index_dir / "index.faiss").write_text("stub")
        (index_dir / "metadata.json").write_text("stub")
        with patch.dict("os.environ", {"TRA_S3_INDEX_BUCKET": "my-bucket", "TRA_FAISS_INDEX_PATH": str(index_dir)}):
            settings = Settings()
        with patch("api.dependencies._download_from_s3") as mock_dl:
            _sync_index_from_s3(settings)
        mock_dl.assert_not_called()


class TestSyncModelFromS3:
    """Tests for the _sync_model_from_s3 helper."""

    def test_noop_when_no_bucket_configured(self) -> None:
        """Verify no download when s3_models_bucket is None."""
        settings = Settings()
        assert settings.s3_models_bucket is None
        with patch("api.dependencies._download_from_s3") as mock_dl:
            _sync_model_from_s3(settings)
        mock_dl.assert_not_called()

    def test_downloads_when_bucket_set_and_model_missing(self, tmp_path: Path) -> None:
        """Verify model is downloaded when missing."""
        model_path = tmp_path / "recommender.joblib"
        with patch.dict("os.environ", {"TRA_S3_MODELS_BUCKET": "my-bucket", "TRA_RECOMMENDER_MODEL_PATH": str(model_path)}):
            settings = Settings()
        with patch("api.dependencies._download_from_s3", return_value=True) as mock_dl:
            _sync_model_from_s3(settings)
        mock_dl.assert_called_once_with("my-bucket", "models/recommender.joblib", model_path, settings)

    def test_returns_early_when_model_not_in_s3(self, tmp_path: Path) -> None:
        """Verify graceful handling when model does not exist in S3."""
        model_path = tmp_path / "recommender.joblib"
        with patch.dict("os.environ", {"TRA_S3_MODELS_BUCKET": "my-bucket", "TRA_RECOMMENDER_MODEL_PATH": str(model_path)}):
            settings = Settings()
        with patch("api.dependencies._download_from_s3", return_value=False) as mock_dl:
            _sync_model_from_s3(settings)
        mock_dl.assert_called_once()

    def test_skips_existing_model(self, tmp_path: Path) -> None:
        """Verify no download when model file already exists."""
        model_path = tmp_path / "recommender.joblib"
        model_path.write_text("stub")
        with patch.dict("os.environ", {"TRA_S3_MODELS_BUCKET": "my-bucket", "TRA_RECOMMENDER_MODEL_PATH": str(model_path)}):
            settings = Settings()
        with patch("api.dependencies._download_from_s3") as mock_dl:
            _sync_model_from_s3(settings)
        mock_dl.assert_not_called()
