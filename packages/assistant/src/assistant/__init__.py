"""OT Threat Research Assistant — LLM assistant package."""

from assistant.chain import ResearchChain
from assistant.client import BedrockAssistantClient
from assistant.prompts import PromptTemplates

__all__ = ["BedrockAssistantClient", "PromptTemplates", "ResearchChain"]
