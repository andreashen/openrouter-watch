"""Tests for openrouter_watch.deriver."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from openrouter_watch.deriver import (
    enrich_pointer_metadata,
    is_pointer_candidate,
    merge_benchmark_fields,
    merge_derived_rows,
    pointer_kind_for,
    resolve_pointer_target,
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
        "knowledge_cutoff",
        "released_at",
        "officially_removed",
        "openrouter_model_url",
        "fetched_at",
        "updated_at",
        "is_pointer",
        "pointer_target_id",
        "pointer_kind",
    }
    assert set(row.keys()) == expected_keys
    assert row["officially_removed"] is False
    assert row["is_pointer"] is False
    assert row["pointer_target_id"] is None
    assert row["pointer_kind"] is None
    assert row["knowledge_cutoff"] == "2023-10-31"
    assert row["released_at"] == "2024-05-13"


def test_to_row_includes_vendor_name(normalized_models) -> None:
    row = to_row(normalized_models[0])
    assert row["vendor_name"] == "OpenAI"


def test_to_row_includes_openrouter_model_url(normalized_models) -> None:
    row = to_row(normalized_models[0])
    assert row["openrouter_model_url"] == "https://openrouter.ai/openai/gpt-4o"


def test_to_row_with_benchmark(normalized_models) -> None:
    row = to_row(normalized_models[0], benchmark=_BENCHMARK_RESULT)
    assert row["intelligence_index"] == 72.5
    assert row["coding_index"] == 68.3
    assert row["agentic_index"] == 55.1


def test_to_row_without_benchmark_has_none_indices(normalized_models) -> None:
    row = to_row(normalized_models[1])
    assert row["intelligence_index"] is None
    assert row["coding_index"] is None
    assert row["agentic_index"] is None


def test_to_row_uses_embedded_benchmark_when_present(normalized_models) -> None:
    row = to_row(normalized_models[0])
    assert row["intelligence_index"] == 72.5
    assert row["coding_index"] == 68.3
    assert row["agentic_index"] == 55.1


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


def test_merge_derived_rows_new_model_sets_updated_at() -> None:
    current = [
        {
            "model_id": "alpha/model",
            "author": "alpha",
            "slug": "model",
            "vendor_name": "Alpha",
            "name": "Alpha: Model",
            "context_length": 8192,
            "max_completion_tokens": 4096,
            "input_price_usd_per_1m": 1.0,
            "output_price_usd_per_1m": 2.0,
            "supports_reasoning": False,
            "supports_tools": True,
            "supports_vision": False,
            "intelligence_index": None,
            "coding_index": None,
            "agentic_index": None,
            "officially_removed": False,
            "openrouter_model_url": "https://openrouter.ai/alpha/model",
            "fetched_at": "2026-01-02T03:04:05Z",
            "updated_at": None,
        }
    ]
    merged = merge_derived_rows(current, {}, refreshed_at="2026-01-02T03:04:05Z")
    assert merged[0]["updated_at"] == "2026-01-02T03:04:05Z"


def test_merge_derived_rows_unchanged_model_keeps_previous_updated_at() -> None:
    current = [
        {
            "model_id": "alpha/model",
            "author": "alpha",
            "slug": "model",
            "vendor_name": "Alpha",
            "name": "Alpha: Model",
            "context_length": 8192,
            "max_completion_tokens": 4096,
            "input_price_usd_per_1m": 1.0,
            "output_price_usd_per_1m": 2.0,
            "supports_reasoning": False,
            "supports_tools": True,
            "supports_vision": False,
            "intelligence_index": None,
            "coding_index": None,
            "agentic_index": None,
            "officially_removed": False,
            "openrouter_model_url": "https://openrouter.ai/alpha/model",
            "fetched_at": "2026-02-02T03:04:05Z",
            "updated_at": None,
        }
    ]
    previous = {
        "alpha/model": {
            "model_id": "alpha/model",
            "author": "alpha",
            "slug": "model",
            "vendor_name": "Alpha",
            "name": "Alpha: Model",
            "context_length": 8192,
            "max_completion_tokens": 4096,
            "input_price_usd_per_1m": 1.0,
            "output_price_usd_per_1m": 2.0,
            "supports_reasoning": False,
            "supports_tools": True,
            "supports_vision": False,
            "intelligence_index": None,
            "coding_index": None,
            "agentic_index": None,
            "officially_removed": False,
            "openrouter_model_url": "https://openrouter.ai/alpha/model",
            "fetched_at": "2026-01-02T03:04:05Z",
            "updated_at": "2026-01-15T00:00:00Z",
        }
    }
    merged = merge_derived_rows(current, previous, refreshed_at="2026-02-02T03:04:05Z")
    assert merged[0]["updated_at"] == "2026-01-15T00:00:00Z"


def test_merge_derived_rows_uses_previous_fetched_at_when_updated_at_missing() -> None:
    current = [
        {
            "model_id": "alpha/model",
            "author": "alpha",
            "slug": "model",
            "vendor_name": "Alpha",
            "name": "Alpha: Model",
            "context_length": 8192,
            "max_completion_tokens": 4096,
            "input_price_usd_per_1m": 1.0,
            "output_price_usd_per_1m": 2.0,
            "supports_reasoning": False,
            "supports_tools": True,
            "supports_vision": False,
            "intelligence_index": None,
            "coding_index": None,
            "agentic_index": None,
            "officially_removed": False,
            "openrouter_model_url": "https://openrouter.ai/alpha/model",
            "fetched_at": "2026-02-02T03:04:05Z",
            "updated_at": None,
        }
    ]
    previous = {
        "alpha/model": {
            "model_id": "alpha/model",
            "author": "alpha",
            "slug": "model",
            "vendor_name": "Alpha",
            "name": "Alpha: Model",
            "context_length": 8192,
            "max_completion_tokens": 4096,
            "input_price_usd_per_1m": 1.0,
            "output_price_usd_per_1m": 2.0,
            "supports_reasoning": False,
            "supports_tools": True,
            "supports_vision": False,
            "intelligence_index": None,
            "coding_index": None,
            "agentic_index": None,
            "officially_removed": False,
            "openrouter_model_url": "https://openrouter.ai/alpha/model",
            "fetched_at": "2026-01-02T03:04:05Z",
        }
    }
    merged = merge_derived_rows(current, previous, refreshed_at="2026-02-02T03:04:05Z")
    assert merged[0]["updated_at"] == "2026-01-02T03:04:05Z"


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
    merged = merge_derived_rows(current, previous, refreshed_at="2026-02-02T03:04:05Z")
    by_id = {row["model_id"]: row for row in merged}
    assert by_id["alpha/model"]["officially_removed"] is False
    assert by_id["gone/model"]["officially_removed"] is True
    assert by_id["gone/model"]["intelligence_index"] == 9.0
    assert by_id["gone/model"]["updated_at"] == "2026-02-02T03:04:05Z"


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
    merged = merge_derived_rows(current, previous, refreshed_at="2026-02-02T03:04:05Z")
    row = merged[0]
    assert row["officially_removed"] is False
    assert row["name"] == "Back: New"
    assert row["intelligence_index"] == 50.0
    assert row["coding_index"] == 60.0
    assert row["updated_at"] == "2026-02-02T03:04:05Z"


def test_write_json_fields_complete(rows) -> None:
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)
    write_json(rows, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    row = data[0]
    assert row["model_id"] == "openai/gpt-4o"
    assert row["vendor_name"] == "OpenAI"
    assert row["openrouter_model_url"] == "https://openrouter.ai/openai/gpt-4o"
    assert row["fetched_at"] == "2026-04-17T00:00:00Z"


def test_is_pointer_candidate_rules() -> None:
    assert is_pointer_candidate("~anthropic/claude-opus-latest") is True
    assert is_pointer_candidate("openai/gpt-chat-latest") is True
    assert is_pointer_candidate("openai/gpt-4o") is False
    assert is_pointer_candidate("vendor/latest-preview") is False


def test_pointer_kind_for_variants() -> None:
    assert pointer_kind_for("~anthropic/claude-opus-latest") == "tilde_latest"
    assert pointer_kind_for("openai/gpt-chat-latest") == "slug_latest"
    assert pointer_kind_for("openai/gpt-4o") is None


def test_resolve_pointer_target_from_url_canonical() -> None:
    rows = {
        "openai/gpt-chat-latest": {
            "model_id": "openai/gpt-chat-latest",
            "author": "openai",
            "openrouter_model_url": "https://openrouter.ai/openai/gpt-chat-latest-20260505",
        },
        "openai/gpt-5-chat": {
            "model_id": "openai/gpt-5-chat",
            "author": "openai",
            "openrouter_model_url": "https://openrouter.ai/openai/gpt-chat-latest-20260505",
        },
        "openai/gpt-4o": {
            "model_id": "openai/gpt-4o",
            "author": "openai",
            "openrouter_model_url": "https://openrouter.ai/openai/gpt-4o",
        },
    }
    target = resolve_pointer_target(rows["openai/gpt-chat-latest"], rows)
    assert target == "openai/gpt-5-chat"


def test_resolve_pointer_target_fuzzy_highest_version() -> None:
    rows = {
        "~anthropic/claude-opus-latest": {
            "model_id": "~anthropic/claude-opus-latest",
            "author": "~anthropic",
            "openrouter_model_url": "https://openrouter.ai/~anthropic/claude-opus-latest",
        },
        "anthropic/claude-opus-4.5": {
            "model_id": "anthropic/claude-opus-4.5",
            "author": "anthropic",
            "openrouter_model_url": "https://openrouter.ai/anthropic/claude-opus-4.5",
        },
        "anthropic/claude-opus-4.8": {
            "model_id": "anthropic/claude-opus-4.8",
            "author": "anthropic",
            "openrouter_model_url": "https://openrouter.ai/anthropic/claude-opus-4.8",
        },
        "anthropic/claude-sonnet-4.6": {
            "model_id": "anthropic/claude-sonnet-4.6",
            "author": "anthropic",
            "openrouter_model_url": "https://openrouter.ai/anthropic/claude-sonnet-4.6",
        },
    }
    target = resolve_pointer_target(rows["~anthropic/claude-opus-latest"], rows)
    assert target == "anthropic/claude-opus-4.8"


def test_resolve_pointer_target_unresolved_keeps_null() -> None:
    rows = {
        "~vendor/unknown-latest": {
            "model_id": "~vendor/unknown-latest",
            "author": "~vendor",
            "openrouter_model_url": "https://openrouter.ai/~vendor/unknown-latest",
        },
        "other/model": {
            "model_id": "other/model",
            "author": "other",
            "openrouter_model_url": "https://openrouter.ai/other/model",
        },
    }
    assert resolve_pointer_target(rows["~vendor/unknown-latest"], rows) is None


def test_enrich_pointer_metadata_sets_fields() -> None:
    rows = [
        {
            "model_id": "~anthropic/claude-opus-latest",
            "author": "~anthropic",
            "slug": "claude-opus-latest",
            "vendor_name": "Anthropic",
            "name": "Anthropic: Claude Opus Latest",
            "openrouter_model_url": "https://openrouter.ai/~anthropic/claude-opus-latest",
            "context_length": 1000000,
            "max_completion_tokens": None,
            "input_price_usd_per_1m": 1.0,
            "output_price_usd_per_1m": 2.0,
            "supports_reasoning": True,
            "supports_tools": True,
            "supports_vision": False,
            "intelligence_index": 61.4,
            "coding_index": None,
            "agentic_index": None,
            "officially_removed": False,
            "fetched_at": "2026-01-02T03:04:05Z",
            "updated_at": "2026-01-02T03:04:05Z",
        },
        {
            "model_id": "anthropic/claude-opus-4.8",
            "author": "anthropic",
            "slug": "claude-opus-4.8",
            "vendor_name": "Anthropic",
            "name": "Anthropic: Claude Opus 4.8",
            "openrouter_model_url": "https://openrouter.ai/anthropic/claude-opus-4.8",
            "context_length": 1000000,
            "max_completion_tokens": None,
            "input_price_usd_per_1m": 5.0,
            "output_price_usd_per_1m": 25.0,
            "supports_reasoning": True,
            "supports_tools": True,
            "supports_vision": True,
            "intelligence_index": 55.7,
            "coding_index": None,
            "agentic_index": None,
            "officially_removed": False,
            "fetched_at": "2026-01-02T03:04:05Z",
            "updated_at": "2026-01-02T03:04:05Z",
        },
        {
            "model_id": "openai/gpt-4o",
            "author": "openai",
            "slug": "gpt-4o",
            "vendor_name": "OpenAI",
            "name": "OpenAI: GPT-4o",
            "openrouter_model_url": "https://openrouter.ai/openai/gpt-4o",
            "context_length": 128000,
            "max_completion_tokens": None,
            "input_price_usd_per_1m": 2.5,
            "output_price_usd_per_1m": 10.0,
            "supports_reasoning": False,
            "supports_tools": True,
            "supports_vision": True,
            "intelligence_index": None,
            "coding_index": None,
            "agentic_index": None,
            "officially_removed": False,
            "fetched_at": "2026-01-02T03:04:05Z",
            "updated_at": "2026-01-02T03:04:05Z",
        },
    ]
    enriched = enrich_pointer_metadata(rows)
    by_id = {row["model_id"]: row for row in enriched}
    pointer = by_id["~anthropic/claude-opus-latest"]
    assert pointer["is_pointer"] is True
    assert pointer["pointer_kind"] == "tilde_latest"
    assert pointer["pointer_target_id"] == "anthropic/claude-opus-4.8"
    assert by_id["openai/gpt-4o"]["is_pointer"] is False
    assert by_id["openai/gpt-4o"]["pointer_target_id"] is None
    assert by_id["openai/gpt-4o"]["pointer_kind"] is None


def test_merge_derived_rows_enriches_pointer_metadata() -> None:
    current = [
        {
            "model_id": "~anthropic/claude-opus-latest",
            "author": "~anthropic",
            "slug": "claude-opus-latest",
            "vendor_name": "Anthropic",
            "name": "Anthropic: Claude Opus Latest",
            "openrouter_model_url": "https://openrouter.ai/~anthropic/claude-opus-latest",
            "context_length": 1000000,
            "max_completion_tokens": None,
            "input_price_usd_per_1m": 1.0,
            "output_price_usd_per_1m": 2.0,
            "supports_reasoning": True,
            "supports_tools": True,
            "supports_vision": False,
            "intelligence_index": None,
            "coding_index": None,
            "agentic_index": None,
            "officially_removed": False,
            "fetched_at": "2026-01-02T03:04:05Z",
            "updated_at": None,
        },
        {
            "model_id": "anthropic/claude-opus-4.8",
            "author": "anthropic",
            "slug": "claude-opus-4.8",
            "vendor_name": "Anthropic",
            "name": "Anthropic: Claude Opus 4.8",
            "openrouter_model_url": "https://openrouter.ai/anthropic/claude-opus-4.8",
            "context_length": 1000000,
            "max_completion_tokens": None,
            "input_price_usd_per_1m": 5.0,
            "output_price_usd_per_1m": 25.0,
            "supports_reasoning": True,
            "supports_tools": True,
            "supports_vision": True,
            "intelligence_index": 55.7,
            "coding_index": None,
            "agentic_index": None,
            "officially_removed": False,
            "fetched_at": "2026-01-02T03:04:05Z",
            "updated_at": None,
        },
    ]
    merged = merge_derived_rows(current, {}, refreshed_at="2026-01-02T03:04:05Z")
    by_id = {row["model_id"]: row for row in merged}
    assert by_id["~anthropic/claude-opus-latest"]["is_pointer"] is True
    assert (
        by_id["~anthropic/claude-opus-latest"]["pointer_target_id"]
        == "anthropic/claude-opus-4.8"
    )
    assert by_id["anthropic/claude-opus-4.8"]["is_pointer"] is False
