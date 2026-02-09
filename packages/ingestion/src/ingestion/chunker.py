"""Text chunking with overlap for document embedding."""

from __future__ import annotations

import hashlib
from typing import Any, Literal

from core.config import Settings
from core.schemas import Advisory, DocumentChunk, Incident, ThreatReport


class TextChunker:
    """Split documents into overlapping text chunks for embedding."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._chunk_size = self._settings.chunk_size
        self._chunk_overlap = self._settings.chunk_overlap

    def chunk_text(
        self,
        text: str,
        source_id: str,
        source_type: Literal["advisory", "threat_report", "incident"],
        metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """Split text into overlapping chunks."""
        if not text.strip():
            return []
        chunks: list[DocumentChunk] = []
        words = text.split()
        start = 0
        chunk_index = 0
        while start < len(words):
            end = start + self._chunk_size
            chunk_words = words[start:end]
            content = " ".join(chunk_words)
            chunk_id = self._generate_chunk_id(source_id, chunk_index)
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    source_id=source_id,
                    source_type=source_type,
                    content=content,
                    metadata={**(metadata or {}), "chunk_index": chunk_index},
                )
            )
            chunk_index += 1
            if end >= len(words):
                break
            start = end - self._chunk_overlap
        return chunks

    def chunk_advisory(self, advisory: Advisory) -> list[DocumentChunk]:
        """Chunk an advisory into document chunks."""
        text = f"{advisory.title}\n\n{advisory.description}\n\nMitigations:\n" + "\n".join(f"- {m}" for m in advisory.mitigations)
        metadata = {
            "severity": advisory.severity.value,
            "protocols": [p.value for p in advisory.protocols],
            "cve_ids": advisory.cve_ids,
            "source": advisory.source,
            "published": advisory.published.isoformat(),
        }
        return self.chunk_text(text, advisory.id, "advisory", metadata)

    def chunk_threat_report(self, report: ThreatReport) -> list[DocumentChunk]:
        """Chunk a threat report into document chunks."""
        text = f"{report.title}\n\n{report.summary}\n\n{report.content}"
        metadata = {
            "threat_category": report.threat_category.value,
            "actor": report.actor,
            "targets": [t.value for t in report.targets],
            "protocols": [p.value for p in report.protocols],
            "ttps": report.ttps,
            "published": report.published.isoformat(),
        }
        return self.chunk_text(text, report.id, "threat_report", metadata)

    def chunk_incident(self, incident: Incident) -> list[DocumentChunk]:
        """Chunk an incident into document chunks."""
        text = f"Incident in {incident.sector} sector\n\n{incident.description}\n\nImpact: {incident.impact}"
        metadata = {
            "sector": incident.sector,
            "asset_types": [a.value for a in incident.asset_types],
            "protocols": [p.value for p in incident.protocols],
            "reported": incident.reported.isoformat(),
        }
        return self.chunk_text(text, incident.id, "incident", metadata)

    @staticmethod
    def _generate_chunk_id(source_id: str, chunk_index: int) -> str:
        """Generate a deterministic chunk ID."""
        raw = f"{source_id}::{chunk_index}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
