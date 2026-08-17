"""
Anthropic implementation of LLMClient (Phase 7).
"""
from __future__ import annotations

from typing import Any

import anthropic

from config.settings import settings
from src.extraction.llm_client import LLMClient

_DEFAULT_MODEL = "claude-sonnet-5"


class AnthropicLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str | None = None):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model or _DEFAULT_MODEL

    def extract_structured(
        self, system_prompt: str, user_prompt: str, json_schema: dict[str, Any]
    ) -> dict[str, Any]:
        tool_name = "extract"
        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[
                {
                    "name": tool_name,
                    "description": "Extract structured data matching the required schema.",
                    "input_schema": json_schema,
                }
            ],
            tool_choice={"type": "tool", "name": tool_name},
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                return block.input  # already a dict matching json_schema

        raise RuntimeError(
            "Anthropic response did not contain the expected tool_use block. "
            "This should not happen with tool_choice forced - check API version compatibility."
        )
