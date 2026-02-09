"""Tests for the TextChunker."""

from core.config import Settings
from core.schemas import Advisory, DocumentChunk, Incident, ThreatReport
from ingestion.chunker import TextChunker


class TestTextChunker:
    """Tests for TextChunker functionality."""

    def test_chunk_short_text(self) -> None:
        """Verify that short text produces a single chunk."""
        settings = Settings(chunk_size=10, chunk_overlap=2)
        chunker = TextChunker(settings)
        chunks = chunker.chunk_text("Hello world", "src-1", "advisory")
        assert len(chunks) == 1
        assert chunks[0].content == "Hello world"
        assert chunks[0].source_id == "src-1"
        assert chunks[0].source_type == "advisory"

    def test_chunk_long_text_with_overlap(self) -> None:
        """Verify that long text is split into overlapping chunks."""
        settings = Settings(chunk_size=5, chunk_overlap=2)
        chunker = TextChunker(settings)
        text = " ".join(f"word{i}" for i in range(12))
        chunks = chunker.chunk_text(text, "src-1", "threat_report")
        assert len(chunks) == 4
        # First chunk: word0..word4
        assert "word0" in chunks[0].content
        assert "word4" in chunks[0].content
        # Second chunk starts at 5-2=3: word3..word7
        assert "word3" in chunks[1].content
        assert "word7" in chunks[1].content
        # Third chunk starts at 8-2=6: word6..word10
        assert "word6" in chunks[2].content
        assert "word10" in chunks[2].content
        # Fourth chunk starts at 11-2=9: word9..word11
        assert "word9" in chunks[3].content
        assert "word11" in chunks[3].content

    def test_chunk_empty_text(self) -> None:
        """Verify that empty text produces no chunks."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("", "src-1", "advisory")
        assert not chunks

    def test_chunk_whitespace_only(self) -> None:
        """Verify that whitespace-only text produces no chunks."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("   \n  \t  ", "src-1", "advisory")
        assert not chunks

    def test_chunk_metadata_propagated(self) -> None:
        """Verify that metadata is propagated to generated chunks."""
        settings = Settings(chunk_size=100, chunk_overlap=10)
        chunker = TextChunker(settings)
        metadata = {"severity": "critical", "protocols": ["modbus"]}
        chunks = chunker.chunk_text("Test content here", "src-1", "advisory", metadata)
        assert len(chunks) == 1
        assert chunks[0].metadata["severity"] == "critical"
        assert chunks[0].metadata["chunk_index"] == 0

    def test_chunk_ids_deterministic(self) -> None:
        """Verify that chunk IDs are deterministic for identical inputs."""
        chunker = TextChunker()
        chunks1 = chunker.chunk_text("Some text", "src-1", "advisory")
        chunks2 = chunker.chunk_text("Some text", "src-1", "advisory")
        assert chunks1[0].id == chunks2[0].id

    def test_chunk_ids_unique_across_sources(self) -> None:
        """Verify that chunk IDs differ for different source IDs."""
        chunker = TextChunker()
        chunks1 = chunker.chunk_text("Some text", "src-1", "advisory")
        chunks2 = chunker.chunk_text("Some text", "src-2", "advisory")
        assert chunks1[0].id != chunks2[0].id

    def test_chunk_advisory(self, sample_advisory: Advisory) -> None:
        """Verify chunking an Advisory model instance."""
        settings = Settings(chunk_size=50, chunk_overlap=5)
        chunker = TextChunker(settings)
        chunks = chunker.chunk_advisory(sample_advisory)
        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert all(c.source_type == "advisory" for c in chunks)
        assert all(c.source_id == sample_advisory.id for c in chunks)
        assert chunks[0].metadata["severity"] == "critical"

    def test_chunk_threat_report(self, sample_threat_report: ThreatReport) -> None:
        """Verify chunking a ThreatReport model instance."""
        settings = Settings(chunk_size=50, chunk_overlap=5)
        chunker = TextChunker(settings)
        chunks = chunker.chunk_threat_report(sample_threat_report)
        assert len(chunks) >= 1
        assert all(c.source_type == "threat_report" for c in chunks)
        assert chunks[0].metadata["threat_category"] == "apt"

    def test_chunk_incident(self, sample_incident: Incident) -> None:
        """Verify chunking an Incident model instance."""
        settings = Settings(chunk_size=50, chunk_overlap=5)
        chunker = TextChunker(settings)
        chunks = chunker.chunk_incident(sample_incident)
        assert len(chunks) >= 1
        assert all(c.source_type == "incident" for c in chunks)
        assert chunks[0].metadata["sector"] == "energy"
