"""Tests for the /recommendations route."""

from fastapi.testclient import TestClient


class TestRecommendRoute:
    """Tests for the recommendations endpoint."""

    def test_get_recommendations(self, client: TestClient) -> None:
        """Verify recommendations endpoint returns a list."""
        response = client.get("/recommendations/user-123")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_recommendations_with_max(self, client: TestClient) -> None:
        """Verify max_results query parameter is accepted."""
        response = client.get("/recommendations/user-123?max_results=3")
        assert response.status_code == 200
