from __future__ import annotations

import csv
import json
from pathlib import Path

from .schema import NormalizedModel

_FIELDS = [
    "model_id",
    "author",
    "slug",
    "vendor_name",
    "name",
    "openrouter_model_url",
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
    "fetched_at",
    "updated_at",
]

BENCHMARK_FIELDS = ("intelligence_index", "coding_index", "agentic_index")
EXCLUDED_UPDATE_FIELDS = {"fetched_at", "updated_at"}


def _is_valid_benchmark(value: object) -> bool:
    return value is not None


def to_row(model: NormalizedModel, benchmark: dict | None = None) -> dict:
    row = model.model_dump()
    if benchmark:
        row["intelligence_index"] = benchmark.get("intelligence_index")
        row["coding_index"] = benchmark.get("coding_index")
        row["agentic_index"] = benchmark.get("agentic_index")
    row["officially_removed"] = False
    row["updated_at"] = None
    return {k: row.get(k) for k in _FIELDS}


def merge_benchmark_fields(current: dict, previous: dict | None) -> dict:
    """Merge benchmark fields: new value wins; blank current inherits previous."""
    if previous is None:
        return current
    merged = dict(current)
    for field in BENCHMARK_FIELDS:
        current_val = merged.get(field)
        previous_val = previous.get(field)
        if _is_valid_benchmark(current_val):
            continue
        if _is_valid_benchmark(previous_val):
            merged[field] = previous_val
        else:
            merged[field] = None
    return merged


def load_previous_models(latest_path: Path | str) -> dict[str, dict]:
    """Load previous derived rows indexed by model_id; empty if no prior run."""
    latest_path = Path(latest_path)
    if not latest_path.exists():
        return {}
    with open(latest_path, encoding="utf-8") as f:
        rows = json.load(f)
    previous_map: dict[str, dict] = {}
    for row in rows:
        model_id = row["model_id"]
        if "officially_removed" not in row:
            row = {**row, "officially_removed": False}
        previous_map[model_id] = row
    return previous_map


def _normalize_row(row: dict) -> dict:
    return {k: row.get(k) for k in _FIELDS}


def _tracked_row_for_update(row: dict) -> dict:
    return {k: row.get(k) for k in _FIELDS if k not in EXCLUDED_UPDATE_FIELDS}


def _resolve_updated_at(current_row: dict, previous_row: dict | None, refreshed_at: str) -> str:
    if previous_row is None:
        return refreshed_at

    normalized_previous = _normalize_row(previous_row)
    if _tracked_row_for_update(current_row) != _tracked_row_for_update(normalized_previous):
        return refreshed_at

    return (
        normalized_previous.get("updated_at")
        or normalized_previous.get("fetched_at")
        or refreshed_at
    )


def merge_derived_rows(
    current_rows: list[dict], previous_map: dict[str, dict], refreshed_at: str
) -> list[dict]:
    """Union current and previous models with removal flags and benchmark backfill."""
    current_map = {row["model_id"]: row for row in current_rows}
    merged: list[dict] = []

    for model_id, current_row in current_map.items():
        previous_row = previous_map.get(model_id)
        row = _normalize_row(current_row)
        row["officially_removed"] = False
        row = merge_benchmark_fields(row, previous_row)
        row["updated_at"] = _resolve_updated_at(row, previous_row, refreshed_at)
        merged.append(row)

    for model_id, previous_row in previous_map.items():
        if model_id in current_map:
            continue
        row = _normalize_row(previous_row)
        row["officially_removed"] = True
        row["updated_at"] = _resolve_updated_at(row, previous_row, refreshed_at)
        merged.append(row)

    merged.sort(key=lambda row: (row["vendor_name"], row["model_id"]))
    return merged


def write_csv(rows: list[dict], path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows: list[dict], path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
