"""Tests for core domain schemas."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from core.enums import AssetType, Protocol, Severity, ThreatCategory
from core.schemas import (
    Advisory,
    AffectedProduct,
    Citation,
    DocumentChunk,
    Incident,
    QueryFilters,
    QueryRequest,
    QueryResponse,
    Recommendation,
    ResponseMetadata,
    ThreatReport,
)


class TestAdvisory:
    """Tests for the Advisory schema."""

    def test_valid_advisory(self, sample_advisory: Advisory) -> None:
        """Verify advisory fields are parsed correctly."""
        assert sample_advisory.id == "ICSA-2024-001"
        assert sample_advisory.severity == Severity.CRITICAL
        assert len(sample_advisory.affected_products) == 1
        assert sample_advisory.affected_products[0].vendor == "Siemens"

    def test_advisory_serialization(self, sample_advisory: Advisory) -> None:
        """Verify model_dump round-trip preserves data."""
        data = sample_advisory.model_dump()
        assert data["id"] == "ICSA-2024-001"
        assert data["severity"] == "critical"
        reconstructed = Advisory.model_validate(data)
        assert reconstructed == sample_advisory

    def test_advisory_json_round_trip(self, sample_advisory: Advisory) -> None:
        """Verify JSON serialization round-trip preserves data."""
        json_str = sample_advisory.model_dump_json()
        reconstructed = Advisory.model_validate_json(json_str)
        assert reconstructed == sample_advisory

    def test_advisory_default_source(self) -> None:
        """Verify source defaults to ICS-CERT."""
        advisory = Advisory(
            id="test",
            title="Test",
            published=datetime(2024, 1, 1, tzinfo=timezone.utc),
            severity=Severity.LOW,
            affected_products=[],
            protocols=[],
            cve_ids=[],
            description="test",
            mitigations=[],
        )
        assert advisory.source == "ICS-CERT"


class TestThreatReport:
    """Tests for the ThreatReport schema."""

    def test_valid_threat_report(self, sample_threat_report: ThreatReport) -> None:
        """Verify threat report fields are parsed correctly."""
        assert sample_threat_report.id == "TR-2024-001"
        assert sample_threat_report.threat_category == ThreatCategory.APT
        assert sample_threat_report.actor == "VOLTZITE"
        assert AssetType.PLC in sample_threat_report.targets

    def test_threat_report_optional_actor(self) -> None:
        """Verify actor, ttps, and iocs default correctly when omitted."""
        report = ThreatReport(
            id="TR-test",
            title="Test",
            published=datetime(2024, 1, 1, tzinfo=timezone.utc),
            threat_category=ThreatCategory.RANSOMWARE,
            targets=[AssetType.HMI],
            protocols=[],
            summary="Test",
            content="Test content",
        )
        assert report.actor is None
        assert report.ttps == []
        assert report.iocs == []

    def test_threat_report_serialization(self, sample_threat_report: ThreatReport) -> None:
        """Verify model_dump round-trip preserves data."""
        data = sample_threat_report.model_dump()
        reconstructed = ThreatReport.model_validate(data)
        assert reconstructed == sample_threat_report


class TestIncident:
    """Tests for the Incident schema."""

    def test_valid_incident(self, sample_incident: Incident) -> None:
        """Verify incident fields are parsed correctly."""
        assert sample_incident.id == "INC-2024-001"
        assert sample_incident.sector == "energy"
        assert len(sample_incident.related_advisory_ids) == 1

    def test_incident_default_related_ids(self) -> None:
        """Verify related_advisory_ids defaults to empty list."""
        incident = Incident(
            id="test",
            reported=datetime(2024, 1, 1, tzinfo=timezone.utc),
            sector="water",
            asset_types=[AssetType.RTU],
            protocols=[Protocol.DNP3],
            description="Test",
            impact="None",
        )
        assert incident.related_advisory_ids == []

    def test_incident_serialization(self, sample_incident: Incident) -> None:
        """Verify model_dump round-trip preserves data."""
        data = sample_incident.model_dump()
        reconstructed = Incident.model_validate(data)
        assert reconstructed == sample_incident


class TestDocumentChunk:
    """Tests for the DocumentChunk schema."""

    def test_valid_chunk(self, sample_chunk: DocumentChunk) -> None:
        """Verify chunk fields are parsed correctly."""
        assert sample_chunk.id == "chunk-001"
        assert sample_chunk.source_type == "advisory"
        assert sample_chunk.embedding is None

    def test_chunk_with_embedding(self, sample_chunk: DocumentChunk) -> None:
        """Verify embedding can be set on a chunk."""
        sample_chunk.embedding = [0.1, 0.2, 0.3]
        assert sample_chunk.embedding == [0.1, 0.2, 0.3]

    def test_chunk_invalid_source_type(self) -> None:
        """Verify invalid source_type raises ValidationError."""
        with pytest.raises(ValidationError):
            DocumentChunk(id="test", source_id="test", source_type="invalid", content="test")  # type: ignore[arg-type]

    def test_chunk_default_metadata(self) -> None:
        """Verify metadata defaults to empty dict."""
        chunk = DocumentChunk(id="test", source_id="test", source_type="advisory", content="test")
        assert chunk.metadata == {}


class TestQueryRequest:
    """Tests for the QueryRequest schema."""

    def test_valid_query(self) -> None:
        """Verify default max_results and filters."""
        query = QueryRequest(question="What vulnerabilities affect Modbus PLCs?")
        assert query.max_results == 10
        assert query.filters is None

    def test_query_with_filters(self) -> None:
        """Verify filters are attached to the request."""
        filters = QueryFilters(severity=[Severity.CRITICAL, Severity.HIGH], protocols=[Protocol.MODBUS])
        query = QueryRequest(question="Test", filters=filters, max_results=5)
        assert query.filters is not None
        assert len(query.filters.severity) == 2  # type: ignore[arg-type]

    def test_query_max_results_bounds(self) -> None:
        """Verify max_results rejects out-of-range values."""
        with pytest.raises(ValidationError):
            QueryRequest(question="Test", max_results=0)
        with pytest.raises(ValidationError):
            QueryRequest(question="Test", max_results=51)


class TestQueryResponse:
    """Tests for the QueryResponse schema."""

    def test_valid_response(self) -> None:
        """Verify a fully populated QueryResponse is accepted."""
        response = QueryResponse(
            answer="Based on analysis...",
            citations=[
                Citation(
                    source_id="ICSA-2024-001",
                    source_type="advisory",
                    title="Test Advisory",
                    excerpt="Relevant excerpt",
                    relevance_score=0.95,
                )
            ],
            recommendations=[
                Recommendation(
                    source_id="TR-2024-001",
                    source_type="threat_report",
                    title="Related Report",
                    reason="Similar threat actor",
                    score=0.8,
                )
            ],
            metadata=ResponseMetadata(
                model_id="anthropic.claude-3-5-sonnet",
                retrieval_time_ms=120.5,
                generation_time_ms=2500.0,
                total_chunks_searched=100,
                total_chunks_used=5,
            ),
        )
        assert len(response.citations) == 1
        assert len(response.recommendations) == 1
        assert response.metadata.total_chunks_used == 5

    def test_citation_score_bounds(self) -> None:
        """Verify relevance_score rejects out-of-range values."""
        with pytest.raises(ValidationError):
            Citation(source_id="test", source_type="advisory", title="Test", excerpt="Test", relevance_score=1.5)
        with pytest.raises(ValidationError):
            Citation(source_id="test", source_type="advisory", title="Test", excerpt="Test", relevance_score=-0.1)


class TestAffectedProduct:
    """Tests for the AffectedProduct schema."""

    def test_with_version(self) -> None:
        """Verify version field is stored."""
        product = AffectedProduct(vendor="Siemens", product="S7-1500", version="<3.0")
        assert product.version == "<3.0"

    def test_without_version(self) -> None:
        """Verify version defaults to None."""
        product = AffectedProduct(vendor="Schneider", product="Modicon M340")
        assert product.version is None


class TestQueryFilters:
    """Tests for the QueryFilters schema."""

    def test_empty_filters(self) -> None:
        """Verify all filter fields default to None."""
        filters = QueryFilters()
        assert filters.severity is None
        assert filters.protocols is None
        assert filters.asset_types is None
        assert filters.threat_categories is None
        assert filters.date_from is None
        assert filters.date_to is None

    def test_partial_filters(self) -> None:
        """Verify a subset of filter fields can be provided."""
        filters = QueryFilters(severity=[Severity.CRITICAL], asset_types=[AssetType.PLC, AssetType.RTU])
        assert len(filters.severity) == 1  # type: ignore[arg-type]
        assert len(filters.asset_types) == 2  # type: ignore[arg-type]
