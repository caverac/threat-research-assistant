"""Versioned prompt templates for the research assistant."""

from __future__ import annotations


class PromptTemplates:
    """Collection of versioned prompt templates for the OT research assistant."""

    VERSION = "1.0"

    SYSTEM_PROMPT = (
        "You are an expert OT/ICS cybersecurity research assistant. "
        "You help security analysts understand threats to industrial control systems, "
        "operational technology, and critical infrastructure. "
        "Always cite your sources using [SOURCE_ID] notation. "
        "Provide actionable recommendations when relevant. "
        "Focus on accuracy and do not speculate beyond the provided context."
    )

    @staticmethod
    def research_query(question: str, context: str, source_ids: list[str]) -> str:
        """Build a prompt for answering analyst questions with citations."""
        sources_list = "\n".join(f"- {sid}" for sid in source_ids)
        return (
            f"Answer the following OT/ICS security research question using ONLY the provided context.\n\n"
            f"## Question\n{question}\n\n"
            f"## Context\n{context}\n\n"
            f"## Available Sources\n{sources_list}\n\n"
            f"## Instructions\n"
            f"1. Answer the question thoroughly based on the context\n"
            f"2. Cite sources using [SOURCE_ID] notation\n"
            f"3. If the context doesn't contain enough information, say so\n"
            f"4. Suggest related topics the analyst might want to explore\n\n"
            f'Respond in JSON format with keys: "answer" (string), "cited_sources" (list of source IDs used), '
            f'"confidence" (float 0-1), "related_topics" (list of strings)'
        )

    @staticmethod
    def summarize(title: str, content: str) -> str:
        """Build a prompt for summarizing a threat report."""
        return (
            f"Summarize the following OT/ICS threat intelligence report.\n\n"
            f"## Title\n{title}\n\n"
            f"## Content\n{content}\n\n"
            f"## Instructions\n"
            f"Provide a concise executive summary covering:\n"
            f"1. Key findings\n"
            f"2. Affected systems and protocols\n"
            f"3. Threat actor (if known)\n"
            f"4. Recommended mitigations\n\n"
            f'Respond in JSON format with keys: "summary" (string), "key_findings" (list), '
            f'"affected_systems" (list), "mitigations" (list)'
        )

    @staticmethod
    def compare(items: list[dict[str, str]]) -> str:
        """Build a prompt for comparing incidents or advisories."""
        items_text = "\n\n".join(f"### {item['title']}\n{item['content']}" for item in items)
        return (
            f"Compare the following OT/ICS security items and identify patterns.\n\n"
            f"## Items\n{items_text}\n\n"
            f"## Instructions\n"
            f"1. Identify common themes and patterns\n"
            f"2. Note differences in severity, scope, and impact\n"
            f"3. Suggest connections between the items\n"
            f"4. Provide an overall assessment\n\n"
            f'Respond in JSON format with keys: "patterns" (list), "differences" (list), '
            f'"connections" (list), "assessment" (string)'
        )
