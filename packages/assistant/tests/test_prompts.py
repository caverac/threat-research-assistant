"""Tests for prompt templates."""

from assistant.prompts import PromptTemplates


class TestPromptTemplates:
    """Tests for the PromptTemplates helper class."""

    def test_version(self) -> None:
        """Verify the template version string."""
        assert PromptTemplates.VERSION == "1.0"

    def test_system_prompt(self) -> None:
        """Verify the system prompt contains expected OT/ICS keywords."""
        assert "OT/ICS" in PromptTemplates.SYSTEM_PROMPT
        assert "cybersecurity" in PromptTemplates.SYSTEM_PROMPT

    def test_research_query(self) -> None:
        """Verify research_query template includes question, context, and sources."""
        prompt = PromptTemplates.research_query(
            question="What vulnerabilities affect Modbus PLCs?",
            context="Context about Modbus vulnerabilities...",
            source_ids=["ICSA-2024-001", "TR-2024-001"],
        )
        assert "What vulnerabilities affect Modbus PLCs?" in prompt
        assert "Context about Modbus vulnerabilities" in prompt
        assert "ICSA-2024-001" in prompt
        assert "TR-2024-001" in prompt
        assert "JSON" in prompt

    def test_summarize(self) -> None:
        """Verify summarize template includes title and content."""
        prompt = PromptTemplates.summarize(title="VOLTZITE Campaign", content="Detailed analysis...")
        assert "VOLTZITE Campaign" in prompt
        assert "Detailed analysis" in prompt
        assert "executive summary" in prompt

    def test_compare(self) -> None:
        """Verify compare template includes all item titles."""
        items = [
            {"title": "Advisory 1", "content": "Content 1"},
            {"title": "Advisory 2", "content": "Content 2"},
        ]
        prompt = PromptTemplates.compare(items)
        assert "Advisory 1" in prompt
        assert "Advisory 2" in prompt
        assert "patterns" in prompt
