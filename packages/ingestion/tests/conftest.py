"""Shared fixtures for ingestion tests."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.enums import AssetType, Protocol, Severity, ThreatCategory
from core.schemas import Advisory, AffectedProduct, Incident, ThreatReport


@pytest.fixture
def sample_advisory_data() -> dict:
    """Return a sample advisory data dictionary."""
    return {
        "id": "ICSA-2024-001",
        "title": "Siemens SIMATIC S7-1500 Buffer Overflow",
        "published": "2024-01-15T00:00:00Z",
        "severity": "critical",
        "affected_products": [{"vendor": "Siemens", "product": "SIMATIC S7-1500", "version": "<3.0.1"}],
        "protocols": ["profinet", "opc-ua"],
        "cve_ids": ["CVE-2024-0001"],
        "description": "A buffer overflow vulnerability in Siemens SIMATIC S7-1500 PLCs.",
        "mitigations": ["Update firmware", "Restrict access"],
        "source": "ICS-CERT",
    }


@pytest.fixture
def sample_threat_report_data() -> dict:
    """Return a sample threat report data dictionary."""
    return {
        "id": "TR-2024-001",
        "title": "VOLTZITE Campaign",
        "published": "2024-03-01T00:00:00Z",
        "threat_category": "apt",
        "actor": "VOLTZITE",
        "targets": ["plc", "scada"],
        "protocols": ["modbus"],
        "ttps": ["T0800"],
        "summary": "APT campaign targeting energy sector.",
        "content": "Detailed analysis of the VOLTZITE campaign.",
        "iocs": ["192.168.1.100"],
    }


@pytest.fixture
def sample_incident_data() -> dict:
    """Return a sample incident data dictionary."""
    return {
        "id": "INC-2024-001",
        "reported": "2024-02-20T00:00:00Z",
        "sector": "energy",
        "asset_types": ["plc", "hmi"],
        "protocols": ["modbus"],
        "description": "Unauthorized modification of PLC logic.",
        "impact": "Temporary shutdown for 4 hours.",
        "related_advisory_ids": ["ICSA-2024-001"],
    }


@pytest.fixture
def tmp_data_dir(  # pylint: disable=redefined-outer-name
    tmp_path: Path,
    sample_advisory_data: dict,
    sample_threat_report_data: dict,
    sample_incident_data: dict,
) -> Path:
    """Create a temporary data directory populated with sample JSON files."""
    advisory_dir = tmp_path / "advisories"
    advisory_dir.mkdir()
    (advisory_dir / "ICSA-2024-001.json").write_text(json.dumps(sample_advisory_data))

    report_dir = tmp_path / "threat_reports"
    report_dir.mkdir()
    (report_dir / "TR-2024-001.json").write_text(json.dumps(sample_threat_report_data))

    incident_dir = tmp_path / "incidents"
    incident_dir.mkdir()
    (incident_dir / "INC-2024-001.json").write_text(json.dumps(sample_incident_data))

    return tmp_path


@pytest.fixture
def sample_advisory() -> Advisory:
    """Return a sample Advisory model instance."""
    return Advisory(
        id="ICSA-2024-001",
        title="Siemens SIMATIC S7-1500 Buffer Overflow",
        published=datetime(2024, 1, 15, tzinfo=timezone.utc),
        severity=Severity.CRITICAL,
        affected_products=[AffectedProduct(vendor="Siemens", product="SIMATIC S7-1500", version="<3.0.1")],
        protocols=[Protocol.PROFINET, Protocol.OPCUA],
        cve_ids=["CVE-2024-0001"],
        description="A buffer overflow vulnerability in Siemens SIMATIC S7-1500 PLCs.",
        mitigations=["Update firmware", "Restrict access"],
        source="ICS-CERT",
    )


@pytest.fixture
def sample_threat_report() -> ThreatReport:
    """Return a sample ThreatReport model instance."""
    return ThreatReport(
        id="TR-2024-001",
        title="VOLTZITE Campaign",
        published=datetime(2024, 3, 1, tzinfo=timezone.utc),
        threat_category=ThreatCategory.APT,
        actor="VOLTZITE",
        targets=[AssetType.PLC, AssetType.SCADA],
        protocols=[Protocol.MODBUS],
        ttps=["T0800"],
        summary="APT campaign targeting energy sector.",
        content="Detailed analysis of the VOLTZITE campaign.",
        iocs=["192.168.1.100"],
    )


@pytest.fixture
def sample_incident() -> Incident:
    """Return a sample Incident model instance."""
    return Incident(
        id="INC-2024-001",
        reported=datetime(2024, 2, 20, tzinfo=timezone.utc),
        sector="energy",
        asset_types=[AssetType.PLC, AssetType.HMI],
        protocols=[Protocol.MODBUS],
        description="Unauthorized modification of PLC logic.",
        impact="Temporary shutdown for 4 hours.",
        related_advisory_ids=["ICSA-2024-001"],
    )
