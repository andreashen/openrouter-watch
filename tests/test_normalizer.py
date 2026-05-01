"""Tests for openrouter_watch.normalizer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openrouter_watch.normalizer import normalize_model
from openrouter_watch.schema import NormalizedModel

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def models_data() -> list[dict]:
    payload = json.loads((FIXTURES / "models_sample.json").read_text())
    return payload["data"]


def get_model(models_data: list[dict], model_id: str) -> dict:
    return next(m for m in models_data if m["id"] == model_id)


def test_returns_normalized_model_instance(models_data: list[dict]) -> None:
    raw = get_model(models_data, "openai/gpt-4o")
    result = normalize_model(raw)
    assert isinstance(result, NormalizedModel)


def test_author_slug_split(models_data: list[dict]) -> None:
    raw = get_model(models_data, "openai/gpt-4o")
    result = normalize_model(raw)
    assert result.author == "openai"
    assert result.slug == "gpt-4o"


def test_vendor_name_uses_name_prefix(models_data: list[dict]) -> None:
    raw = get_model(models_data, "openai/gpt-4o")
    result = normalize_model(raw)
    assert result.vendor_name == "OpenAI"


def test_vendor_name_falls_back_to_author(models_data: list[dict]) -> None:
    raw = get_model(models_data, "noslash-model")
    result = normalize_model(raw)
    assert result.vendor_name == ""


def test_no_slash_model_id(models_data: list[dict]) -> None:
    raw = get_model(models_data, "noslash-model")
    result = normalize_model(raw)
    assert result.author == ""
    assert result.slug == "noslash-model"


def test_price_conversion(models_data: list[dict]) -> None:
    raw = get_model(models_data, "openai/gpt-4o")
    result = normalize_model(raw)
    # prompt: 0.0000025 * 1_000_000 = 2.5
    assert result.input_price_usd_per_1m == pytest.approx(2.5)
    # completion: 0.00001 * 1_000_000 = 10.0
    assert result.output_price_usd_per_1m == pytest.approx(10.0)


def test_price_conversion_rounds_to_six_decimals() -> None:
    raw = {
        "id": "openai/gpt-4o",
        "name": "OpenAI: GPT-4o",
        "pricing": {"prompt": "0.000000123456789", "completion": ""},
    }
    result = normalize_model(raw)
    assert result.input_price_usd_per_1m == pytest.approx(0.123457)
    assert result.output_price_usd_per_1m is None


def test_free_model_price_is_zero(models_data: list[dict]) -> None:
    raw = get_model(models_data, "noslash-model")
    result = normalize_model(raw)
    assert result.input_price_usd_per_1m == pytest.approx(0.0)
    assert result.output_price_usd_per_1m == pytest.approx(0.0)


def test_supports_tools_true(models_data: list[dict]) -> None:
    raw = get_model(models_data, "openai/gpt-4o")
    result = normalize_model(raw)
    assert result.supports_tools is True


def test_supports_reasoning_true(models_data: list[dict]) -> None:
    raw = get_model(models_data, "anthropic/claude-3-5-sonnet")
    result = normalize_model(raw)
    assert result.supports_reasoning is True


def test_supports_reasoning_false(models_data: list[dict]) -> None:
    raw = get_model(models_data, "openai/gpt-4o")
    result = normalize_model(raw)
    assert result.supports_reasoning is False


def test_supports_vision_true_when_image_in_modality(models_data: list[dict]) -> None:
    raw = get_model(models_data, "openai/gpt-4o")
    result = normalize_model(raw)
    assert result.supports_vision is True


def test_supports_vision_false_when_text_only(models_data: list[dict]) -> None:
    raw = get_model(models_data, "google/gemini-2-0-flash")
    result = normalize_model(raw)
    assert result.supports_vision is False


def test_supports_vision_false_when_no_architecture(models_data: list[dict]) -> None:
    raw = get_model(models_data, "noslash-model")
    result = normalize_model(raw)
    assert result.supports_vision is False


def test_fetched_at_preserved(models_data: list[dict]) -> None:
    raw = get_model(models_data, "openai/gpt-4o")
    result = normalize_model(raw, fetched_at="2026-04-17T00:00:00Z")
    assert result.fetched_at == "2026-04-17T00:00:00Z"
