"""
LLM client abstraction (Phase 7).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from config.settings import settings


class LLMConfigurationError(RuntimeError):
    """Raised when no LLM provider is configured or the configured one is missing its key."""


class LLMClient(ABC):
    @abstractmethod
    def extract_structured(
        self, system_prompt: str, user_prompt: str, json_schema: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError


def get_llm_client() -> LLMClient:
    
    provider = (settings.llm_provider or "").strip().lower()

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise LLMConfigurationError(
                "LLM_PROVIDER is set to 'anthropic' but ANTHROPIC_API_KEY is not "
                "set in your .env file. Add your API key and try again."
            )
        from src.extraction.anthropic_client import AnthropicLLMClient

        return AnthropicLLMClient(api_key=settings.anthropic_api_key, model=settings.anthropic_model)

    if provider == "openai":
        if not settings.openai_api_key:
            raise LLMConfigurationError(
                "LLM_PROVIDER is set to 'openai' but OPENAI_API_KEY is not set "
                "in your .env file. Add your API key and try again."
            )
        from src.extraction.openai_client import OpenAILLMClient

        return OpenAILLMClient(api_key=settings.openai_api_key, model=settings.openai_model)

    if provider == "groq":
        if not settings.groq_api_key:
            raise LLMConfigurationError(
                "LLM_PROVIDER is set to 'groq' but GROQ_API_KEY is not set "
                "in your .env file. Add your API key and try again."
            )
        from src.extraction.groq_client import GroqLLMClient

        return GroqLLMClient(api_key=settings.groq_api_key, model=settings.groq_model)

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise LLMConfigurationError(
                "LLM_PROVIDER is set to 'gemini' but GEMINI_API_KEY is not "
                "set in your .env file. Add your API key and try again."
            )
        from src.extraction.gemini_client import GeminiLLMClient

        return GeminiLLMClient(api_key=settings.gemini_api_key, model=settings.gemini_model)

    raise LLMConfigurationError(
        "No LLM provider configured. Set LLM_PROVIDER to 'anthropic', "
        "'openai', 'groq', or 'gemini' in your .env file, along with the "
        "matching API key. See .env.example."
    )
