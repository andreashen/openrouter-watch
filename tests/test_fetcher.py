"""Tests for openrouter_watch.fetcher (all HTTP mocked)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from openrouter_watch.fetcher import MODELS_URL, fetch_benchmark, fetch_models

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def models_payload() -> dict:
    return json.loads((FIXTURES / "models_sample.json").read_text())


@pytest.fixture()
def benchmark_payload() -> dict:
    return json.loads((FIXTURES / "benchmark_sample.json").read_text())


def test_fetch_models_returns_full_payload(httpx_mock: HTTPXMock, models_payload: dict) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=models_payload)
    result = fetch_models()
    assert result == models_payload
    assert result["data"][0]["id"] == "openai/gpt-4o"


def test_fetch_models_raises_on_http_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, status_code=403)
    with pytest.raises(httpx.HTTPStatusError):
        fetch_models()


def test_fetch_benchmark_returns_dict(httpx_mock: HTTPXMock, benchmark_payload: dict) -> None:
    # URL includes query param slug=openai%2Fgpt-4o; match any request
    httpx_mock.add_response(json=benchmark_payload)
    result = fetch_benchmark("openai/gpt-4o")
    assert result is not None
    assert result["intelligence_index"] == 72.5
    assert result["coding_index"] == 68.3
    assert result["agentic_index"] == 55.1


def test_fetch_benchmark_accepts_legacy_flat_payload(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        json={
            "intelligence_index": 1.0,
            "coding_index": 2.0,
            "agentic_index": 3.0,
        }
    )
    result = fetch_benchmark("openai/gpt-4o")
    assert result == {
        "intelligence_index": 1.0,
        "coding_index": 2.0,
        "agentic_index": 3.0,
    }


def test_fetch_benchmark_returns_none_on_empty_data(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json={"data": []})
    result = fetch_benchmark("openai/gpt-4o")
    assert result is None


def test_fetch_benchmark_returns_none_on_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=500)
    result = fetch_benchmark("openai/gpt-4o")
    assert result is None


def test_fetch_benchmark_returns_none_on_network_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ConnectError("timeout"))
    result = fetch_benchmark("openai/gpt-4o")
    assert result is None


def test_fetch_benchmark_returns_none_on_timeout(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ReadTimeout("timed out"))
    result = fetch_benchmark("openai/gpt-4o")
    assert result is None


def test_fetch_benchmark_returns_none_on_invalid_json(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(text="not json {")
    result = fetch_benchmark("openai/gpt-4o")
    assert result is None
