"""Tests for API application factory and service initialization."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import faiss
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import get_embedding_client, get_research_chain, get_settings, get_vector_store, initialize_services, shutdown_services


class TestCreateApp:
    """Tests for the create_app factory function."""

    def test_create_app_returns_fastapi(self) -> None:
        """Verify create_app returns a FastAPI instance with correct title."""
        with patch("api.dependencies.BedrockEmbeddingClient"), patch("api.dependencies.BedrockAssistantClient"):
            app = create_app()
            assert isinstance(app, FastAPI)
            assert app.title == "OT Threat Research Assistant"

    def test_create_app_lifespan(self) -> None:
        """Verify lifespan initializes services and health endpoint works."""
        with patch("api.dependencies.BedrockEmbeddingClient"), patch("api.dependencies.BedrockAssistantClient"):
            app = create_app()
            with TestClient(app) as client:
                response = client.get("/health")
                assert response.status_code == 200


class TestInitializeServices:
    """Tests for the initialize_services function."""

    def test_initialize_services(self) -> None:
        """Verify all expected services are attached to app state."""
        with patch("api.dependencies.BedrockEmbeddingClient") as mock_emb_cls, patch("api.dependencies.BedrockAssistantClient") as mock_asst_cls:
            app = FastAPI()
            initialize_services(app)
            assert hasattr(app.state, "settings")
            assert hasattr(app.state, "embedding_client")
            assert hasattr(app.state, "vector_store")
            assert hasattr(app.state, "retriever")
            assert hasattr(app.state, "retrieval_pipeline")
            assert hasattr(app.state, "assistant_client")
            assert hasattr(app.state, "research_chain")
            mock_emb_cls.assert_called_once()
            mock_asst_cls.assert_called_once()

    def test_initialize_services_with_existing_index(self, tmp_path: Path) -> None:
        """Verify services load existing FAISS index and recommender model."""
        from recommender.trainer import RecommenderTrainer  # pylint: disable=import-outside-toplevel

        index_path = tmp_path / "faiss_index"
        index_path.mkdir()
        index = faiss.IndexFlatIP(8)
        faiss.write_index(index, str(index_path / "index.faiss"))
        (index_path / "metadata.json").write_text(json.dumps([]))

        model_path = tmp_path / "recommender.joblib"
        trainer = RecommenderTrainer(n_estimators=5)
        trainer.train_from_synthetic(n_queries=3, docs_per_query=3)
        trainer.save(model_path)

        with (
            patch("api.dependencies.BedrockEmbeddingClient"),
            patch("api.dependencies.BedrockAssistantClient"),
            patch.dict(
                "os.environ",
                {
                    "TRA_FAISS_INDEX_PATH": str(index_path),
                    "TRA_RECOMMENDER_MODEL_PATH": str(model_path),
                },
            ),
        ):
            app = FastAPI()
            initialize_services(app)
            assert app.state.reranker is not None

    def test_shutdown_services(self) -> None:
        """Verify shutdown_services runs without error."""
        app = FastAPI()
        shutdown_services(app)


class TestDependencyGetters:
    """Tests for FastAPI dependency getter functions."""

    def test_get_settings(self) -> None:
        """Verify get_settings returns settings from app state."""
        mock_request = MagicMock()
        mock_request.app.state.settings = "test_settings"
        assert get_settings(mock_request) == "test_settings"

    def test_get_research_chain(self) -> None:
        """Verify get_research_chain returns chain from app state."""
        mock_request = MagicMock()
        mock_request.app.state.research_chain = "test_chain"
        assert get_research_chain(mock_request) == "test_chain"

    def test_get_vector_store(self) -> None:
        """Verify get_vector_store returns store from app state."""
        mock_request = MagicMock()
        mock_request.app.state.vector_store = "test_store"
        assert get_vector_store(mock_request) == "test_store"

    def test_get_embedding_client(self) -> None:
        """Verify get_embedding_client returns client from app state."""
        mock_request = MagicMock()
        mock_request.app.state.embedding_client = "test_client"
        assert get_embedding_client(mock_request) == "test_client"
