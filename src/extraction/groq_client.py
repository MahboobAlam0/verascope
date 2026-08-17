"""
Groq implementation of LLMClient (Phase 7).
"""
from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from src.extraction.llm_client import LLMClient
from src.extraction.openai_client import _make_strict

_DEFAULT_MODEL = "openai/gpt-oss-120b"
_BASE_URL = "https://api.groq.com/openai/v1"


class GroqLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str | None = None):
        self._client = OpenAI(api_key=api_key, base_url=_BASE_URL)
        self._model = model or _DEFAULT_MODEL

    def extract_structured(
        self, system_prompt: str, user_prompt: str, json_schema: dict[str, Any]
    ) -> dict[str, Any]:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "extraction_result",
                    "schema": _make_strict(json_schema),
                    "strict": True,
                },
            },
        )
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("Groq response had no content.")
        return json.loads(content)
