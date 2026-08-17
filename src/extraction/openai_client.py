"""
OpenAI implementation of LLMClient (Phase 7).
"""
from __future__ import annotations

import copy
import json
from typing import Any

from openai import OpenAI

from src.extraction.llm_client import LLMClient

_DEFAULT_MODEL = "gpt-4.1"


def _make_strict(schema: dict[str, Any]) -> dict[str, Any]:
    """Adapt a Pydantic-generated JSON schema for OpenAI's strict mode.
    """
    schema = copy.deepcopy(schema)

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            node.pop("default", None)
            if node.get("type") == "object" and "properties" in node:
                node["additionalProperties"] = False
                node["required"] = list(node["properties"].keys())
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(schema)
    return schema


class OpenAILLMClient(LLMClient):
    def __init__(self, api_key: str, model: str | None = None):
        self._client = OpenAI(api_key=api_key)
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
            raise RuntimeError("OpenAI response had no content.")
        return json.loads(content)
