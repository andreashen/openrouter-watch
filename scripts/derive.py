"""Derive final CSV/JSON products from normalized data + benchmarks."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from openrouter_watch.deriver import to_row, write_csv, write_json
from openrouter_watch.fetcher import fetch_benchmark
from openrouter_watch.schema import NormalizedModel

NORM_DIR = Path(__file__).parent.parent / "data" / "normalized"
DERIVED_DIR = Path(__file__).parent.parent / "data" / "derived"


def latest_normalized_file() -> Path:
    files = sorted(NORM_DIR.glob("*_models.json"))
    if not files:
        raise FileNotFoundError(f"No normalized model files found in {NORM_DIR}")
    return files[-1]


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    norm_path = latest_normalized_file()
    print(f"Reading normalized file: {norm_path}")

    with open(norm_path, encoding="utf-8") as f:
        records = json.load(f)

    models = [NormalizedModel.model_validate(r) for r in records]
    rows: list[dict] = []

    for i, model in enumerate(models):
        print(f"[{i + 1}/{len(models)}] Fetching benchmark for {model.model_id}...")
        benchmark = fetch_benchmark(model.model_id)
        rows.append(to_row(model, benchmark))

    rows.sort(key=lambda row: (row["vendor_name"], row["model_id"]))

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    csv_path = DERIVED_DIR / f"models_{ts}.csv"
    json_path = DERIVED_DIR / f"models_{ts}.json"
    latest_path = DERIVED_DIR / "models_latest.json"

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
