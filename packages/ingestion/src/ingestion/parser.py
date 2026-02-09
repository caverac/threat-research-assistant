"""Parse raw data dictionaries into domain models."""

from __future__ import annotations

from typing import Any

from core.schemas import Advisory, Incident, ThreatReport


class DocumentParser:
    """Parse raw JSON data into typed domain models."""

    @staticmethod
    def parse_advisory(data: dict[str, Any]) -> Advisory:
        """Parse raw data into an Advisory model."""
        return Advisory.model_validate(data)

    @staticmethod
    def parse_threat_report(data: dict[str, Any]) -> ThreatReport:
        """Parse raw data into a ThreatReport model."""
        return ThreatReport.model_validate(data)

    @staticmethod
    def parse_incident(data: dict[str, Any]) -> Incident:
        """Parse raw data into an Incident model."""
        return Incident.model_validate(data)

    def parse_advisories(self, data_list: list[dict[str, Any]]) -> list[Advisory]:
        """Parse a list of raw advisory data."""
        return [self.parse_advisory(d) for d in data_list]

    def parse_threat_reports(self, data_list: list[dict[str, Any]]) -> list[ThreatReport]:
        """Parse a list of raw threat report data."""
        return [self.parse_threat_report(d) for d in data_list]

    def parse_incidents(self, data_list: list[dict[str, Any]]) -> list[Incident]:
        """Parse a list of raw incident data."""
        return [self.parse_incident(d) for d in data_list]
