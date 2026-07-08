"""Tests for openrouter_watch.fetcher (all HTTP mocked)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from openrouter_watch.fetcher import MODELS_URL, extract_benchmark_from_raw, fetch_models

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def models_payload() -> dict:
    return json.loads((FIXTURES / "models_sample.json").read_text())


def test_fetch_models_returns_full_payload(httpx_mock: HTTPXMock, models_payload: dict) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=models_payload)
    result = fetch_models()
    assert result == models_payload
    assert result["data"][0]["id"] == "openai/gpt-4o"


def test_fetch_models_raises_on_http_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, status_code=403)
    with pytest.raises(httpx.HTTPStatusError):
        fetch_models()


def test_extract_benchmark_from_raw_returns_indices() -> None:
    raw = {
        "id": "anthropic/claude-opus-4.8",
        "benchmarks": {
            "artificial_analysis": {
                "intelligence_index": 55.7,
                "coding_index": 74.3,
                "agentic_index": 47.2,
            }
        },
    }
    result = extract_benchmark_from_raw(raw)
    assert result == {
        "intelligence_index": 55.7,
        "coding_index": 74.3,
        "agentic_index": 47.2,
    }


def test_extract_benchmark_from_raw_returns_none_when_missing() -> None:
    assert extract_benchmark_from_raw({"id": "openai/gpt-4o"}) is None
    assert extract_benchmark_from_raw({"id": "openai/gpt-4o", "benchmarks": None}) is None
    assert extract_benchmark_from_raw(
        {"id": "openai/gpt-4o", "benchmarks": {"artificial_analysis": None}}
    ) is None


def test_extract_benchmark_from_raw_returns_none_when_all_blank() -> None:
    raw = {
        "id": "anthropic/claude-opus-4.8-fast",
        "benchmarks": {
            "artificial_analysis": {
                "intelligence_index": None,
                "coding_index": None,
                "agentic_index": None,
            }
        },
    }
    assert extract_benchmark_from_raw(raw) is None
