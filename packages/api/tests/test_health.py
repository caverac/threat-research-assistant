"""Tests for the /health route."""

from fastapi.testclient import TestClient


class TestHealthRoute:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Verify health endpoint returns healthy status with component details."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert "vector_store" in data["components"]
        assert data["components"]["vector_store"]["status"] == "ok"
        assert data["components"]["vector_store"]["document_count"] == 5
