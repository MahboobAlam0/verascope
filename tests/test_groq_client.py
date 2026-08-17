"""
Sanity checks for the Groq client (Phase 7).
"""
from __future__ import annotations  # noqa: I001

from src.extraction.groq_client import GroqLLMClient, _BASE_URL, _DEFAULT_MODEL


def test_default_model_and_base_url():
    client = GroqLLMClient(api_key="test-key")
    assert client._model == _DEFAULT_MODEL
    assert str(client._client.base_url).rstrip("/") == _BASE_URL


def test_model_override_is_respected():
    client = GroqLLMClient(api_key="test-key", model="llama-3.1-8b-instant")
    assert client._model == "llama-3.1-8b-instant"
