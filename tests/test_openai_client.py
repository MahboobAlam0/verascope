"""
Regression test for the OpenAI strict-json_schema adapter (Phase 7).
"""
from __future__ import annotations

from typing import Any

from src.extraction.openai_client import _make_strict
from src.extraction.schema import (
    BufferAndWaivers,
    Demographics,
    Hospitalization,
    InfertilityAndAmbulance,
    InsurerAndTPA,
    Maternity,
    OtherBenefits,
    PolicyStructure,
    PreviousPolicy,
    WaitingPeriods,
)


def _assert_strict(node: Any, path: str = "root") -> None:
    if isinstance(node, dict):
        if node.get("type") == "object" and "properties" in node:
            props = set(node["properties"].keys())
            required = set(node.get("required", []))
            assert node.get("additionalProperties") is False, (
                f"{path}: additionalProperties must be False"
            )
            assert required == props, (
                f"{path}: required {required} must equal properties {props}"
            )
        assert "default" not in node, f"{path}: OpenAI strict mode rejects 'default'"
        for key, value in node.items():
            _assert_strict(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _assert_strict(item, f"{path}[{index}]")


STAGE_MODELS = [
    InsurerAndTPA,
    PreviousPolicy,
    PolicyStructure,
    Demographics,
    Hospitalization,
    Maternity,
    WaitingPeriods,
    OtherBenefits,
    InfertilityAndAmbulance,
    BufferAndWaivers,
]


def test_make_strict_satisfies_openai_requirements_for_every_stage_model():
    for model in STAGE_MODELS:
        strict_schema = _make_strict(model.model_json_schema())
        _assert_strict(strict_schema)


def test_make_strict_does_not_mutate_input():
    original = InsurerAndTPA.model_json_schema()
    import copy

    before = copy.deepcopy(original)
    _make_strict(original)
    assert original == before
