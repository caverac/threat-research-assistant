"""Research chain: retrieval → LLM → structured output."""

from __future__ import annotations

import json
import time

from assistant.client import BedrockAssistantClient
from assistant.prompts import PromptTemplates
from core.schemas import Citation, DocumentChunk, QueryRequest, QueryResponse, Recommendation, ResponseMetadata
from retrieval.pipeline import RetrievalPipeline


class ResearchChain:
    """Full pipeline: parse query → retrieve context → build prompt → call LLM → parse structured output."""

    def __init__(self, retrieval_pipeline: RetrievalPipeline, assistant_client: BedrockAssistantClient) -> None:
        self._retrieval = retrieval_pipeline
        self._assistant = assistant_client

    def run(self, request: QueryRequest) -> QueryResponse:
        """Execute the full research chain."""
        retrieval_results, retrieval_time = self._retrieval.run(
            query=request.question,
            top_k=request.max_results,
            filters=request.filters,
        )

        context = self._build_context(retrieval_results)
        source_ids = [chunk.source_id for chunk, _ in retrieval_results]

        prompt = PromptTemplates.research_query(request.question, context, source_ids)

        gen_start = time.monotonic()
        raw_response = self._assistant.generate(prompt, system=PromptTemplates.SYSTEM_PROMPT)
        gen_time = (time.monotonic() - gen_start) * 1000

        answer, cited_sources = self._parse_response(raw_response)
        citations = self._build_citations(retrieval_results, cited_sources)
        recommendations = self._build_recommendations(retrieval_results)

        return QueryResponse(
            answer=answer,
            citations=citations,
            recommendations=recommendations,
            metadata=ResponseMetadata(
                model_id=self._assistant.model_id,
                retrieval_time_ms=retrieval_time,
                generation_time_ms=gen_time,
                total_chunks_searched=self._retrieval.total_documents,
                total_chunks_used=len(retrieval_results),
            ),
        )

    @staticmethod
    def _build_context(results: list[tuple[DocumentChunk, float]]) -> str:
        """Build context string from retrieval results."""
        parts: list[str] = []
        for chunk, score in results:
            parts.append(f"[{chunk.source_id}] (relevance: {score:.3f})\n{chunk.content}")
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _parse_response(raw: str) -> tuple[str, list[str]]:
        """Parse the LLM response to extract answer and cited sources."""
        try:
            data = json.loads(raw)
            answer = data.get("answer", raw)
            cited = data.get("cited_sources", [])
        except (json.JSONDecodeError, TypeError):
            answer = raw
            cited = []
        return answer, cited

    @staticmethod
    def _build_citations(
        results: list[tuple[DocumentChunk, float]],
        cited_sources: list[str],
    ) -> list[Citation]:
        """Build citation objects from retrieval results."""
        citations: list[Citation] = []
        seen: set[str] = set()
        cited_set = set(cited_sources)
        for chunk, score in results:
            if chunk.source_id in seen:
                continue
            if cited_set and chunk.source_id not in cited_set:
                continue
            seen.add(chunk.source_id)
            citations.append(
                Citation(
                    source_id=chunk.source_id,
                    source_type=chunk.source_type,
                    title=chunk.metadata.get("title", chunk.source_id),
                    excerpt=chunk.content[:200],
                    relevance_score=min(1.0, max(0.0, score)),
                )
            )
        return citations

    @staticmethod
    def _build_recommendations(results: list[tuple[DocumentChunk, float]]) -> list[Recommendation]:
        """Build recommendation objects from retrieval results."""
        recommendations: list[Recommendation] = []
        seen: set[str] = set()
        for chunk, score in results:
            if chunk.source_id in seen:
                continue
            seen.add(chunk.source_id)
            recommendations.append(
                Recommendation(
                    source_id=chunk.source_id,
                    source_type=chunk.source_type,
                    title=chunk.metadata.get("title", chunk.source_id),
                    reason=f"Relevant to query with score {score:.3f}",
                    score=min(1.0, max(0.0, score)),
                )
            )
        return recommendations
