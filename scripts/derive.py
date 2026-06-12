"""Derive final CSV/JSON products from normalized data + benchmarks."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from openrouter_watch.deriver import (
    load_previous_models,
    merge_derived_rows,
    to_row,
    write_csv,
    write_json,
)
from openrouter_watch.fetcher import BenchmarkDetails, fetch_benchmark_details
from openrouter_watch.schema import NormalizedModel

NORM_DIR = Path(__file__).parent.parent / "data" / "normalized"
DERIVED_DIR = Path(__file__).parent.parent / "data" / "derived"


def latest_normalized_file() -> Path:
    files = sorted(NORM_DIR.glob("*_models.json"))
    if not files:
        raise FileNotFoundError(f"No normalized model files found in {NORM_DIR}")
    return files[-1]


def _build_model_indexes(models: list[NormalizedModel]) -> tuple[set[str], dict[str, str]]:
    concrete_ids: set[str] = set()
    canonical_to_model_id: dict[str, str] = {}
    for model in models:
        if model.model_id.startswith("~"):
            continue
        concrete_ids.add(model.model_id)
        if model.canonical_slug:
            canonical_to_model_id[model.canonical_slug] = model.model_id
    return concrete_ids, canonical_to_model_id


def _resolve_latest_alias_target(
    model: NormalizedModel,
    benchmark_details: BenchmarkDetails | None,
    concrete_ids: set[str],
    canonical_to_model_id: dict[str, str],
) -> str | None:
    if not model.model_id.startswith("~") or benchmark_details is None:
        return None

    for candidate in (
        benchmark_details.get("heuristic_openrouter_slug"),
        benchmark_details.get("permaslug"),
    ):
        if not isinstance(candidate, str) or not candidate:
            continue
        if candidate in concrete_ids:
            return candidate
        mapped_model_id = canonical_to_model_id.get(candidate)
        if mapped_model_id:
            return mapped_model_id
    return None


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    norm_path = latest_normalized_file()
    print(f"Reading normalized file: {norm_path}")

    with open(norm_path, encoding="utf-8") as f:
        records = json.load(f)

    models = [NormalizedModel.model_validate(r) for r in records]
    concrete_ids, canonical_to_model_id = _build_model_indexes(models)
    rows: list[dict] = []

    for i, model in enumerate(models):
        print(f"[{i + 1}/{len(models)}] Fetching benchmark for {model.model_id}...")
        benchmark_details = fetch_benchmark_details(
            model.model_id,
            canonical_slug=model.canonical_slug,
        )
        benchmark = benchmark_details["indices"] if benchmark_details else None
        latest_alias_target = _resolve_latest_alias_target(
            model,
            benchmark_details,
            concrete_ids,
            canonical_to_model_id,
        )
        rows.append(to_row(model, benchmark, latest_alias_target=latest_alias_target))

    latest_path = DERIVED_DIR / "models_latest.json"
    previous_map = load_previous_models(latest_path)
    rows = merge_derived_rows(rows, previous_map)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    csv_path = DERIVED_DIR / f"models_{ts}.csv"
    json_path = DERIVED_DIR / f"models_{ts}.json"

    write_csv(rows, csv_path)
    write_json(rows, json_path)

    if latest_path.exists() or latest_path.is_symlink():
        latest_path.unlink()
    latest_path.symlink_to(json_path.name)

    print(f"Wrote {len(rows)} rows → {csv_path}")
    print(f"Wrote {len(rows)} rows → {json_path}")
    print(f"Wrote latest symlink → {latest_path} -> {json_path.name}")


if __name__ == "__main__":
    main()
