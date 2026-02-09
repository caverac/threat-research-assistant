"""Tests for the ResearchChain orchestration class."""

import json

from assistant.chain import ResearchChain
from assistant.client import BedrockAssistantClient
from core.schemas import DocumentChunk, QueryRequest, QueryResponse
from retrieval.pipeline import RetrievalPipeline


class TestResearchChain:
    """Tests for ResearchChain.run and its helper methods."""

    def test_run(self, mock_retrieval_pipeline: RetrievalPipeline, mock_assistant_client: BedrockAssistantClient) -> None:
        """Verify run returns a well-formed QueryResponse."""
        chain = ResearchChain(mock_retrieval_pipeline, mock_assistant_client)
        request = QueryRequest(question="What Modbus vulnerabilities exist?", max_results=3)
        response = chain.run(request)

        assert isinstance(response, QueryResponse)
        assert "OT threats" in response.answer
        assert len(response.citations) > 0
        assert len(response.recommendations) > 0
        assert response.metadata.model_id == "anthropic.claude-3-5-sonnet"
        assert response.metadata.retrieval_time_ms > 0
        assert response.metadata.generation_time_ms > 0

    def test_run_with_unparseable_response(self, mock_retrieval_pipeline: RetrievalPipeline, mock_assistant_client: BedrockAssistantClient) -> None:
        """Verify run gracefully handles non-JSON LLM responses."""
        mock_assistant_client.generate.return_value = "Plain text response without JSON"  # type: ignore[attr-defined]
        chain = ResearchChain(mock_retrieval_pipeline, mock_assistant_client)
        request = QueryRequest(question="Test query")
        response = chain.run(request)
        assert response.answer == "Plain text response without JSON"

    def test_build_context(self) -> None:
        """Verify _build_context formats results with source IDs and scores."""
        results = [
            (DocumentChunk(id="c1", source_id="src-1", source_type="advisory", content="Content 1"), 0.95),
            (DocumentChunk(id="c2", source_id="src-2", source_type="threat_report", content="Content 2"), 0.80),
        ]
        context = ResearchChain._build_context(results)  # pylint: disable=protected-access
        assert "[src-1]" in context
        assert "[src-2]" in context
        assert "0.950" in context

    def test_parse_response_valid_json(self) -> None:
        """Verify _parse_response extracts answer and cited_sources from JSON."""
        raw = json.dumps({"answer": "The answer", "cited_sources": ["src-1"]})
        answer, cited = ResearchChain._parse_response(raw)  # pylint: disable=protected-access
        assert answer == "The answer"
        assert cited == ["src-1"]

    def test_parse_response_invalid_json(self) -> None:
        """Verify _parse_response returns raw text when JSON parsing fails."""
        answer, cited = ResearchChain._parse_response("Not JSON")  # pylint: disable=protected-access
        assert answer == "Not JSON"
        assert cited == []

    def test_build_citations_deduplicates(self) -> None:
        """Verify _build_citations deduplicates by source_id."""
        results = [
            (DocumentChunk(id="c1", source_id="src-1", source_type="advisory", content="Content", metadata={"title": "Adv1"}), 0.9),
            (DocumentChunk(id="c2", source_id="src-1", source_type="advisory", content="Content 2", metadata={"title": "Adv1"}), 0.8),
        ]
        citations = ResearchChain._build_citations(results, ["src-1"])  # pylint: disable=protected-access
        assert len(citations) == 1

    def test_build_recommendations_deduplicates(self) -> None:
        """Verify _build_recommendations deduplicates by source_id."""
        results = [
            (DocumentChunk(id="c1", source_id="src-1", source_type="advisory", content="Content", metadata={"title": "Adv1"}), 0.9),
            (DocumentChunk(id="c2", source_id="src-1", source_type="advisory", content="Content 2", metadata={"title": "Adv1"}), 0.8),
        ]
        recommendations = ResearchChain._build_recommendations(results)  # pylint: disable=protected-access
        assert len(recommendations) == 1

    def test_build_recommendations(self) -> None:
        """Verify _build_recommendations returns one entry per unique source."""
        results = [
            (DocumentChunk(id="c1", source_id="src-1", source_type="advisory", content="Content", metadata={"title": "Adv1"}), 0.9),
            (DocumentChunk(id="c2", source_id="src-2", source_type="threat_report", content="Content 2", metadata={"title": "Report1"}), 0.7),
        ]
        recommendations = ResearchChain._build_recommendations(results)  # pylint: disable=protected-access
        assert len(recommendations) == 2
        assert recommendations[0].source_id == "src-1"
