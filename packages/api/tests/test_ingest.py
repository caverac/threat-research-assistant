"""Tests for the /ingest route."""

from fastapi.testclient import TestClient


class TestIngestRoute:
    """Tests for the ingest endpoint."""

    def test_ingest_advisory(self, client: TestClient) -> None:
        """Verify ingesting an advisory returns ok status."""
        response = client.post(
            "/ingest",
            json={
                "source_type": "advisory",
                "document": {
                    "id": "ICSA-2024-099",
                    "title": "Test Advisory",
                    "published": "2024-01-15T00:00:00Z",
                    "severity": "high",
                    "affected_products": [{"vendor": "Test", "product": "Widget"}],
                    "protocols": ["modbus"],
                    "cve_ids": ["CVE-2024-99999"],
                    "description": "Test vulnerability description.",
                    "mitigations": ["Update firmware"],
                    "source": "ICS-CERT",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["chunks_added"] >= 1
        assert data["source_id"] == "ICSA-2024-099"

    def test_ingest_threat_report(self, client: TestClient) -> None:
        """Verify ingesting a threat report returns ok status."""
        response = client.post(
            "/ingest",
            json={
                "source_type": "threat_report",
                "document": {
                    "id": "TR-2024-099",
                    "title": "Test Report",
                    "published": "2024-03-01T00:00:00Z",
                    "threat_category": "apt",
                    "actor": "TEST_ACTOR",
                    "targets": ["plc"],
                    "protocols": ["modbus"],
                    "ttps": ["T0800"],
                    "summary": "Test summary.",
                    "content": "Test content.",
                    "iocs": ["1.2.3.4"],
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["source_id"] == "TR-2024-099"

    def test_ingest_incident(self, client: TestClient) -> None:
        """Verify ingesting an incident returns ok status."""
        response = client.post(
            "/ingest",
            json={
                "source_type": "incident",
                "document": {
                    "id": "INC-2024-099",
                    "reported": "2024-02-20T00:00:00Z",
                    "sector": "energy",
                    "asset_types": ["plc"],
                    "protocols": ["modbus"],
                    "description": "Test incident.",
                    "impact": "Test impact.",
                    "related_advisory_ids": [],
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["source_id"] == "INC-2024-099"

    def test_ingest_unknown_type(self, client: TestClient) -> None:
        """Verify ingesting an unknown source type returns error status."""
        response = client.post("/ingest", json={"source_type": "unknown", "document": {"id": "test"}})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
