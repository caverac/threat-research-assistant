"""Tests for synthetic data generation."""

from pathlib import Path

from core.schemas import Advisory, Incident, ThreatReport
from ingestion.synthetic import generate_advisories, generate_all, generate_incidents, generate_threat_reports


class TestSyntheticGeneration:
    """Tests for synthetic data generators."""

    def test_generate_advisories(self) -> None:
        """Verify generating a batch of advisory objects."""
        advisories = generate_advisories(10)
        assert len(advisories) == 10
        assert all(isinstance(a, Advisory) for a in advisories)
        assert all(a.id.startswith("ICSA-") for a in advisories)
        assert all(len(a.cve_ids) >= 1 for a in advisories)
        assert all(len(a.protocols) >= 1 for a in advisories)

    def test_generate_threat_reports(self) -> None:
        """Verify generating a batch of threat report objects."""
        reports = generate_threat_reports(5)
        assert len(reports) == 5
        assert all(isinstance(r, ThreatReport) for r in reports)
        assert all(r.id.startswith("TR-") for r in reports)
        assert all(len(r.ttps) >= 2 for r in reports)

    def test_generate_incidents(self) -> None:
        """Verify generating a batch of incident objects."""
        incidents = generate_incidents(5)
        assert len(incidents) == 5
        assert all(isinstance(i, Incident) for i in incidents)
        assert all(i.id.startswith("INC-") for i in incidents)

    def test_generate_incidents_with_advisory_ids(self) -> None:
        """Verify incidents reference only the provided advisory IDs."""
        advisory_ids = ["ICSA-2024-001", "ICSA-2024-002"]
        incidents = generate_incidents(5, advisory_ids)
        assert len(incidents) == 5
        for incident in incidents:
            for related_id in incident.related_advisory_ids:
                assert related_id in advisory_ids

    def test_generate_all(self, tmp_path: Path) -> None:
        """Verify generating all document types and writing them to disk."""
        generate_all(tmp_path)
        advisory_files = list((tmp_path / "advisories").glob("*.json"))
        report_files = list((tmp_path / "threat_reports").glob("*.json"))
        incident_files = list((tmp_path / "incidents").glob("*.json"))
        assert len(advisory_files) == 50
        assert len(report_files) == 30
        assert len(incident_files) == 20
