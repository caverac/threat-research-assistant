"""Tests for the /query route."""

from fastapi.testclient import TestClient


class TestQueryRoute:
    """Tests for query endpoint."""

    def test_query(self, client: TestClient) -> None:
        """Verify a basic query returns expected response structure."""
        response = client.post("/query", json={"question": "What Modbus vulnerabilities exist?", "max_results": 3})
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "citations" in data
        assert "recommendations" in data
        assert "metadata" in data

    def test_query_with_filters(self, client: TestClient) -> None:
        """Verify query with filters returns 200."""
        response = client.post(
            "/query",
            json={
                "question": "Critical PLC vulnerabilities",
                "filters": {"severity": ["critical"], "protocols": ["modbus"]},
                "max_results": 5,
            },
        )
        assert response.status_code == 200

    def test_query_invalid_max_results(self, client: TestClient) -> None:
        """Verify query with invalid max_results returns 422."""
        response = client.post("/query", json={"question": "test", "max_results": 0})
        assert response.status_code == 422
