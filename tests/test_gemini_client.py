"""
Tests for the Gemini client (Phase 7).
"""
from __future__ import annotations  # noqa: I001

from src.extraction.gemini_client import GeminiLLMClient, _BASE_URL, _DEFAULT_MODEL, inline_refs


def test_default_model_and_base_url():
    client = GeminiLLMClient(api_key="test-key")
    assert client._model == _DEFAULT_MODEL
    assert str(client._client.base_url).rstrip("/") == _BASE_URL.rstrip("/")


def test_model_override_is_respected():
    client = GeminiLLMClient(api_key="test-key", model="gemini-2.5-flash")
    assert client._model == "gemini-2.5-flash"


def test_inline_refs_resolves_nested_ref_and_drops_defs():
    schema = {
        "type": "object",
        "properties": {
            "field_a": {"$ref": "#/$defs/Nested"},
        },
        "$defs": {
            "Nested": {"type": "object", "properties": {"value": {"type": "string"}}},
        },
    }
    result = inline_refs(schema)
    assert "$defs" not in result
    assert result["properties"]["field_a"] == {
        "type": "object",
        "properties": {"value": {"type": "string"}},
    }


def test_inline_refs_resolves_nested_ref_inside_a_list():
    schema = {
        "type": "object",
        "properties": {
            "items": {"type": "array", "items": {"$ref": "#/$defs/Nested"}},
        },
        "$defs": {"Nested": {"type": "object", "properties": {"value": {"type": "string"}}}},
    }
    result = inline_refs(schema)
    assert "$defs" not in result
    assert result["properties"]["items"]["items"] == {
        "type": "object",
        "properties": {"value": {"type": "string"}},
    }


def test_inline_refs_preserves_sibling_keys_alongside_a_ref():
    schema = {
        "properties": {"field_a": {"$ref": "#/$defs/Nested", "description": "the person's name"}},
        "$defs": {"Nested": {"type": "object", "properties": {"value": {"type": "string"}}}},
    }
    result = inline_refs(schema)
    assert result["properties"]["field_a"]["description"] == "the person's name"
    assert result["properties"]["field_a"]["type"] == "object"


def test_inline_refs_handles_schema_with_no_refs():
    schema = {"type": "object", "properties": {"value": {"type": "string"}}}
    assert inline_refs(schema) == schema
