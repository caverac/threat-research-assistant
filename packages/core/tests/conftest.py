"""Shared fixtures for core tests."""

from datetime import datetime, timezone

import pytest

from core.enums import AssetType, Protocol, Severity, ThreatCategory
from core.schemas import Advisory, AffectedProduct, DocumentChunk, Incident, ThreatReport


@pytest.fixture
def sample_advisory() -> Advisory:
    """Create a sample advisory for testing."""
    return Advisory(
        id="ICSA-2024-001",
        title="Siemens SIMATIC S7-1500 Buffer Overflow",
        published=datetime(2024, 1, 15, tzinfo=timezone.utc),
        severity=Severity.CRITICAL,
        affected_products=[AffectedProduct(vendor="Siemens", product="SIMATIC S7-1500", version="<3.0.1")],
        protocols=[Protocol.PROFINET, Protocol.OPCUA],
        cve_ids=["CVE-2024-0001"],
        description="A buffer overflow vulnerability in Siemens SIMATIC S7-1500 PLCs allows remote code execution via crafted PROFINET packets.",
        mitigations=["Update to firmware version 3.0.1 or later", "Restrict network access to affected devices"],
        source="ICS-CERT",
    )


@pytest.fixture
def sample_threat_report() -> ThreatReport:
    """Create a sample threat report for testing."""
    return ThreatReport(
        id="TR-2024-001",
        title="VOLTZITE Campaign Targeting Energy Sector PLCs",
        published=datetime(2024, 3, 1, tzinfo=timezone.utc),
        threat_category=ThreatCategory.APT,
        actor="VOLTZITE",
        targets=[AssetType.PLC, AssetType.SCADA],
        protocols=[Protocol.MODBUS, Protocol.DNP3],
        ttps=["T0800", "T0831", "T0855"],
        summary="VOLTZITE has been observed targeting energy sector PLCs via spear-phishing and lateral movement to OT networks.",
        content="Detailed analysis of the VOLTZITE campaign targeting energy sector infrastructure...",
        iocs=["192.168.1.100", "evil.example.com", "abc123hash"],
    )


@pytest.fixture
def sample_incident() -> Incident:
    """Create a sample incident for testing."""
    return Incident(
        id="INC-2024-001",
        reported=datetime(2024, 2, 20, tzinfo=timezone.utc),
        sector="energy",
        asset_types=[AssetType.PLC, AssetType.HMI],
        protocols=[Protocol.MODBUS],
        description="Unauthorized modification of PLC logic detected in power generation facility.",
        impact="Temporary shutdown of turbine control system for 4 hours.",
        related_advisory_ids=["ICSA-2024-001"],
    )


@pytest.fixture
def sample_chunk(sample_advisory: Advisory) -> DocumentChunk:  # pylint: disable=redefined-outer-name
    """Create a sample document chunk derived from the sample advisory."""
    return DocumentChunk(
        id="chunk-001",
        source_id=sample_advisory.id,
        source_type="advisory",
        content=sample_advisory.description,
        metadata={"severity": sample_advisory.severity.value, "protocols": [p.value for p in sample_advisory.protocols]},
    )
