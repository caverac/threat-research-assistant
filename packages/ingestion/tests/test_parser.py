"""Tests for the DocumentParser."""

import pytest
from pydantic import ValidationError

from core.enums import Severity, ThreatCategory
from core.schemas import Advisory, Incident, ThreatReport
from ingestion.parser import DocumentParser


class TestDocumentParser:
    """Tests for DocumentParser functionality."""

    def test_parse_advisory(self, sample_advisory_data: dict) -> None:
        """Verify parsing a valid advisory dictionary into an Advisory model."""
        parser = DocumentParser()
        advisory = parser.parse_advisory(sample_advisory_data)
        assert isinstance(advisory, Advisory)
        assert advisory.id == "ICSA-2024-001"
        assert advisory.severity == Severity.CRITICAL

    def test_parse_advisory_invalid(self) -> None:
        """Verify that an incomplete advisory dictionary raises ValidationError."""
        parser = DocumentParser()
        with pytest.raises(ValidationError):
            parser.parse_advisory({"id": "test"})

    def test_parse_threat_report(self, sample_threat_report_data: dict) -> None:
        """Verify parsing a valid threat report dictionary into a ThreatReport model."""
        parser = DocumentParser()
        report = parser.parse_threat_report(sample_threat_report_data)
        assert isinstance(report, ThreatReport)
        assert report.id == "TR-2024-001"
        assert report.threat_category == ThreatCategory.APT

    def test_parse_threat_report_invalid(self) -> None:
        """Verify that an incomplete threat report dictionary raises ValidationError."""
        parser = DocumentParser()
        with pytest.raises(ValidationError):
            parser.parse_threat_report({"id": "test"})

    def test_parse_incident(self, sample_incident_data: dict) -> None:
        """Verify parsing a valid incident dictionary into an Incident model."""
        parser = DocumentParser()
        incident = parser.parse_incident(sample_incident_data)
        assert isinstance(incident, Incident)
        assert incident.id == "INC-2024-001"
        assert incident.sector == "energy"

    def test_parse_incident_invalid(self) -> None:
        """Verify that an incomplete incident dictionary raises ValidationError."""
        parser = DocumentParser()
        with pytest.raises(ValidationError):
            parser.parse_incident({"id": "test"})

    def test_parse_advisories_batch(self, sample_advisory_data: dict) -> None:
        """Verify parsing a batch of advisory dictionaries."""
        parser = DocumentParser()
        advisories = parser.parse_advisories([sample_advisory_data, sample_advisory_data])
        assert len(advisories) == 2
        assert all(isinstance(a, Advisory) for a in advisories)

    def test_parse_threat_reports_batch(self, sample_threat_report_data: dict) -> None:
        """Verify parsing a batch of threat report dictionaries."""
        parser = DocumentParser()
        reports = parser.parse_threat_reports([sample_threat_report_data])
        assert len(reports) == 1

    def test_parse_incidents_batch(self, sample_incident_data: dict) -> None:
        """Verify parsing a batch of incident dictionaries."""
        parser = DocumentParser()
        incidents = parser.parse_incidents([sample_incident_data])
        assert len(incidents) == 1
