"""Pydantic models for OT threat intelligence domain objects."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from core.enums import AssetType, Protocol, Severity, ThreatCategory


class AffectedProduct(BaseModel):
    """A product affected by an advisory."""

    vendor: str
    product: str
    version: str | None = None


class Advisory(BaseModel):
    """ICS-CERT-style security advisory."""

    id: str
    title: str
    published: datetime
    severity: Severity
    affected_products: list[AffectedProduct]
    protocols: list[Protocol]
    cve_ids: list[str]
    description: str
    mitigations: list[str]
    source: str = "ICS-CERT"


class ThreatReport(BaseModel):
    """Threat intelligence report."""

    id: str
    title: str
    published: datetime
    threat_category: ThreatCategory
    actor: str | None = None
    targets: list[AssetType]
    protocols: list[Protocol]
    ttps: list[str] = Field(default_factory=list, description="MITRE ATT&CK technique IDs")
    summary: str
    content: str
    iocs: list[str] = Field(default_factory=list, description="Indicators of compromise")


class Incident(BaseModel):
    """OT security incident record."""

    id: str
    reported: datetime
    sector: str
    asset_types: list[AssetType]
    protocols: list[Protocol]
    description: str
    impact: str
    related_advisory_ids: list[str] = Field(default_factory=list)


class DocumentChunk(BaseModel):
    """A chunk of a source document with optional embedding."""

    id: str
    source_id: str
    source_type: Literal["advisory", "threat_report", "incident"]
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None


class QueryFilters(BaseModel):
    """Optional filters for narrowing search results."""

    severity: list[Severity] | None = None
    protocols: list[Protocol] | None = None
    asset_types: list[AssetType] | None = None
    threat_categories: list[ThreatCategory] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class QueryRequest(BaseModel):
    """Analyst query to the research assistant."""

    question: str
    filters: QueryFilters | None = None
    max_results: int = Field(default=10, ge=1, le=50)


class Citation(BaseModel):
    """A citation linking an answer to a source document."""

    source_id: str
    source_type: Literal["advisory", "threat_report", "incident"]
    title: str
    excerpt: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class Recommendation(BaseModel):
    """A recommended document from the recommender system."""

    source_id: str
    source_type: Literal["advisory", "threat_report", "incident"]
    title: str
    reason: str
    score: float = Field(ge=0.0, le=1.0)


class ResponseMetadata(BaseModel):
    """Metadata about the assistant response."""

    model_id: str
    retrieval_time_ms: float
    generation_time_ms: float
    total_chunks_searched: int
    total_chunks_used: int


class QueryResponse(BaseModel):
    """Structured response from the research assistant."""

    answer: str
    citations: list[Citation]
    recommendations: list[Recommendation]
    metadata: ResponseMetadata
