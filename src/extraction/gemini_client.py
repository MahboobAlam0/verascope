"""
Gemini implementation of LLMClient (Phase 7)
"""
from __future__ import annotations

import copy
import json
from typing import Any

from openai import OpenAI

from src.extraction.llm_client import LLMClient
from src.extraction.openai_client import _make_strict


_DEFAULT_MODEL = "gemini-flash-latest"
_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def inline_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Public entry point: resolve $ref/$defs into a fully self-contained schema."""
    schema = copy.deepcopy(schema)
    defs = schema.pop("$defs", {})

    def _resolve_node(node: Any, depth: int) -> Any:
        if depth > 20:
            raise RuntimeError("Schema nesting too deep to inline for Gemini (possible $ref cycle).")
        if isinstance(node, dict):
            if "$ref" in node:
                key = node["$ref"].rsplit("/", 1)[-1]
                resolved = _resolve_node(copy.deepcopy(defs[key]), depth + 1)
                overrides = {k: v for k, v in node.items() if k != "$ref"}
                return {**resolved, **overrides}
            return {k: _resolve_node(v, depth + 1) for k, v in node.items()}
        if isinstance(node, list):
            return [_resolve_node(item, depth + 1) for item in node]
        return node

    return _resolve_node(schema, 0)


class GeminiLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str | None = None):
        self._client = OpenAI(api_key=api_key, base_url=_BASE_URL)
        self._model = model or _DEFAULT_MODEL

    def extract_structured(
        self, system_prompt: str, user_prompt: str, json_schema: dict[str, Any]
    ) -> dict[str, Any]:
        schema = inline_refs(_make_strict(json_schema))
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
                    "schema": schema,
                    "strict": True,
                },
            },
        )
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("Gemini response had no content.")
        return json.loads(content)
