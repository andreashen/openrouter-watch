"""Tests for openrouter_watch.deriver."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from openrouter_watch.deriver import (
    merge_benchmark_fields,
    merge_derived_rows,
    to_row,
    write_csv,
    write_json,
)
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
        "officially_removed",
        "latest_alias_target",
        "fetched_at",
    }
    assert set(row.keys()) == expected_keys
    assert row["officially_removed"] is False
    assert row["latest_alias_target"] is None


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


def test_merge_benchmark_fields_current_wins() -> None:
    current = {"intelligence_index": 80.0, "coding_index": None, "agentic_index": 50.0}
    previous = {"intelligence_index": 70.0, "coding_index": 60.0, "agentic_index": 40.0}
    merged = merge_benchmark_fields(current, previous)
    assert merged["intelligence_index"] == 80.0
    assert merged["coding_index"] == 60.0
    assert merged["agentic_index"] == 50.0


def test_merge_benchmark_fields_both_blank() -> None:
    current = {"intelligence_index": None, "coding_index": None, "agentic_index": None}
    previous = {"intelligence_index": None, "coding_index": None, "agentic_index": None}
    merged = merge_benchmark_fields(current, previous)
    assert merged["intelligence_index"] is None
    assert merged["coding_index"] is None
    assert merged["agentic_index"] is None


def test_merge_derived_rows_marks_removed_models() -> None:
    current = [
        {
            "model_id": "alpha/model",
            "vendor_name": "Alpha",
            "officially_removed": False,
            "intelligence_index": None,
            "coding_index": None,
            "agentic_index": None,
        }
    ]
    previous = {
        "alpha/model": {
            "model_id": "alpha/model",
            "vendor_name": "Alpha",
            "officially_removed": False,
            "intelligence_index": 1.0,
            "coding_index": 2.0,
            "agentic_index": 3.0,
        },
        "gone/model": {
            "model_id": "gone/model",
            "vendor_name": "Gone",
            "officially_removed": False,
            "intelligence_index": 9.0,
            "coding_index": 8.0,
            "agentic_index": 7.0,
        },
    }
    merged = merge_derived_rows(current, previous)
    by_id = {row["model_id"]: row for row in merged}
    assert by_id["alpha/model"]["officially_removed"] is False
    assert by_id["gone/model"]["officially_removed"] is True
    assert by_id["gone/model"]["intelligence_index"] == 9.0


def test_merge_derived_rows_reappeared_model() -> None:
    current = [
        {
            "model_id": "back/model",
            "vendor_name": "Back",
            "name": "Back: New",
            "officially_removed": False,
            "intelligence_index": 50.0,
            "coding_index": None,
            "agentic_index": None,
        }
    ]
    previous = {
        "back/model": {
            "model_id": "back/model",
            "vendor_name": "Back",
            "name": "Back: Old",
            "officially_removed": True,
            "intelligence_index": 70.0,
            "coding_index": 60.0,
            "agentic_index": 55.0,
        }
    }
    merged = merge_derived_rows(current, previous)
    row = merged[0]
    assert row["officially_removed"] is False
    assert row["name"] == "Back: New"
    assert row["intelligence_index"] == 50.0
    assert row["coding_index"] == 60.0


def test_merge_derived_rows_keeps_previous_latest_alias_target_when_current_missing() -> None:
    current = [
        {
            "model_id": "~openai/gpt-latest",
            "vendor_name": "~openai",
            "officially_removed": False,
            "latest_alias_target": None,
            "intelligence_index": None,
            "coding_index": None,
            "agentic_index": None,
        }
    ]
    previous = {
        "~openai/gpt-latest": {
            "model_id": "~openai/gpt-latest",
            "vendor_name": "~openai",
            "officially_removed": False,
            "latest_alias_target": "openai/gpt-5.5",
            "intelligence_index": 60.2,
            "coding_index": 59.1,
            "agentic_index": 74.1,
        }
    }
    merged = merge_derived_rows(current, previous)
    row = merged[0]
    assert row["latest_alias_target"] == "openai/gpt-5.5"


def test_write_json_fields_complete(rows) -> None:
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)
    write_json(rows, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    row = data[0]
    assert row["model_id"] == "openai/gpt-4o"
    assert row["vendor_name"] == "OpenAI"
    assert row["fetched_at"] == "2026-04-17T00:00:00Z"
