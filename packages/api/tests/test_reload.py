"""Tests for the /reload-index route and reload_index dependency."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.dependencies import reload_index
from core.config import Settings
from embeddings.store import FAISSVectorStore


class TestReloadRoute:
    """Tests for the reload-index endpoint."""

    def test_reload_returns_counts(self, client: TestClient) -> None:
        """Verify reload endpoint returns previous and current counts."""
        with patch("api.routes.reload.reload_index", return_value=(5, 10)):
            response = client.post("/reload-index")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["previous_count"] == 5
        assert data["current_count"] == 10


class TestReloadIndex:
    """Tests for the reload_index function."""

    def test_reload_replaces_store(self, tmp_path: Path) -> None:
        """Verify reload rebuilds vector store and downstream services."""
        index_dir = tmp_path / "faiss_index"
        index_dir.mkdir()

        # Create an initial store with one chunk
        old_store = FAISSVectorStore(dimension=8)
        from core.schemas import DocumentChunk  # pylint: disable=import-outside-toplevel

        rng = np.random.default_rng(0)
        old_store.add(
            [
                DocumentChunk(
                    id="old-chunk",
                    source_id="src-old",
                    source_type="advisory",
                    content="Old content",
                    metadata={},
                    embedding=rng.random(8).tolist(),
                ),
            ]
        )

        settings = Settings()
        with patch.dict("os.environ", {"TRA_FAISS_INDEX_PATH": str(index_dir)}):
            settings = Settings()

        app = FastAPI()
        app.state.settings = settings
        app.state.vector_store = old_store
        app.state.embedding_client = MagicMock()
        app.state.reranker = None
        app.state.assistant_client = MagicMock()

        with patch("api.dependencies._sync_index_from_s3"):
            prev, curr = reload_index(app)

        assert prev == 1
        assert curr == 0  # No index file downloaded, so empty store
        assert app.state.vector_store is not old_store
        assert hasattr(app.state, "research_chain")

    def test_reload_picks_up_new_index(self, tmp_path: Path) -> None:
        """Verify reload loads a new index from S3."""
        import faiss  # pylint: disable=import-outside-toplevel

        index_dir = tmp_path / "faiss_index"
        index_dir.mkdir()

        settings = Settings()
        with patch.dict("os.environ", {"TRA_FAISS_INDEX_PATH": str(index_dir), "TRA_S3_INDEX_BUCKET": "my-bucket"}):
            settings = Settings()

        old_store = FAISSVectorStore(dimension=8)

        app = FastAPI()
        app.state.settings = settings
        app.state.vector_store = old_store
        app.state.embedding_client = MagicMock()
        app.state.reranker = None
        app.state.assistant_client = MagicMock()

        def fake_sync(_s: Settings) -> None:
            idx = faiss.IndexFlatIP(8)
            faiss.write_index(idx, str(index_dir / "index.faiss"))
            (index_dir / "metadata.json").write_text("[]")

        with patch("api.dependencies._sync_index_from_s3", side_effect=fake_sync):
            prev, curr = reload_index(app)

        assert prev == 0
        assert curr == 0  # Empty but valid index
        assert app.state.vector_store is not old_store

    def test_reload_removes_local_files_before_sync(self, tmp_path: Path) -> None:
        """Verify existing local index files are deleted before re-downloading."""
        index_dir = tmp_path / "faiss_index"
        index_dir.mkdir()
        (index_dir / "index.faiss").write_text("stale")
        (index_dir / "metadata.json").write_text("stale")

        with patch.dict("os.environ", {"TRA_FAISS_INDEX_PATH": str(index_dir)}):
            settings = Settings()

        old_store = FAISSVectorStore(dimension=8)

        app = FastAPI()
        app.state.settings = settings
        app.state.vector_store = old_store
        app.state.embedding_client = MagicMock()
        app.state.reranker = None
        app.state.assistant_client = MagicMock()

        files_existed_during_sync: list[bool] = []

        def fake_sync(_s: Settings) -> None:
            files_existed_during_sync.append((index_dir / "index.faiss").exists())

        with patch("api.dependencies._sync_index_from_s3", side_effect=fake_sync):
            reload_index(app)

        assert files_existed_during_sync == [False]
