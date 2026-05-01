"""Tests for openrouter_watch.deriver."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from openrouter_watch.deriver import to_row, write_csv, write_json
from openrouter_watch.normalizer import normalize_model

FIXTURES = Path(__file__).parent / "fixtures"

_MODELS_PAYLOAD = json.loads((FIXTURES / "models_sample.json").read_text())
_BENCHMARK_RESULT = {
    "intelligence_index": 72.5,
    "coding_index": 68.3,
    "agentic_index": 55.1,
}


@pytest.fixture()
def normalized_models():
    return [normalize_model(m, fetched_at="2026-04-17T00:00:00Z") for m in _MODELS_PAYLOAD["data"]]


@pytest.fixture()
def rows(normalized_models):
    return [to_row(m) for m in normalized_models]


def test_to_row_has_all_fields(normalized_models) -> None:
    row = to_row(normalized_models[0])
    expected_keys = {
        "model_id",
        "author",
        "slug",
        "vendor_name",
        "name",
        "context_length",
        "max_completion_tokens",
        "input_price_usd_per_1m",
        "output_price_usd_per_1m",
        "supports_reasoning",
        "supports_tools",
        "supports_vision",
        "intelligence_index",
        "coding_index",
        "agentic_index",
        "fetched_at",
    }
    assert set(row.keys()) == expected_keys


def test_to_row_includes_vendor_name(normalized_models) -> None:
    row = to_row(normalized_models[0])
    assert row["vendor_name"] == "OpenAI"


def test_to_row_with_benchmark(normalized_models) -> None:
    row = to_row(normalized_models[0], benchmark=_BENCHMARK_RESULT)
    assert row["intelligence_index"] == 72.5
    assert row["coding_index"] == 68.3
    assert row["agentic_index"] == 55.1


def test_to_row_without_benchmark_has_none_indices(normalized_models) -> None:
    row = to_row(normalized_models[0])
    assert row["intelligence_index"] is None
    assert row["coding_index"] is None
    assert row["agentic_index"] is None


def test_write_csv_correct_row_count(rows) -> None:
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = Path(f.name)
    write_csv(rows, path)
    df = pd.read_csv(path, encoding="utf-8-sig")
    assert len(df) == len(rows)


def test_write_csv_has_all_columns(rows) -> None:
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = Path(f.name)
    write_csv(rows, path)
    df = pd.read_csv(path, encoding="utf-8-sig")
    assert "model_id" in df.columns
    assert "vendor_name" in df.columns
    assert "input_price_usd_per_1m" in df.columns
    assert "supports_vision" in df.columns
    assert "intelligence_index" in df.columns


def test_write_json_correct_count(rows) -> None:
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)
    write_json(rows, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) == len(rows)


def test_write_json_fields_complete(rows) -> None:
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)
    write_json(rows, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    row = data[0]
    assert row["model_id"] == "openai/gpt-4o"
    assert row["vendor_name"] == "OpenAI"
    assert row["fetched_at"] == "2026-04-17T00:00:00Z"
