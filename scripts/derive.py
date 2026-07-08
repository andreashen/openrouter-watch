"""Derive the committed model dataset from normalized data + benchmarks."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from openrouter_watch.deriver import (
    load_previous_models,
    merge_derived_rows,
    to_row,
    write_json,
)
from openrouter_watch.schema import NormalizedModel

NORM_DIR = Path(__file__).parent.parent / "data" / "normalized"
DERIVED_DIR = Path(__file__).parent.parent / "data" / "derived"
LATEST_JSON_NAME = "models_latest.json"
META_JSON_NAME = "models_meta.json"
LEGACY_DERIVED_PATTERNS = ("models_*.json", "models_*.csv")
PROTECTED_DERIVED_NAMES = {LATEST_JSON_NAME, META_JSON_NAME}


def latest_normalized_file() -> Path:
    files = sorted(NORM_DIR.glob("*_models.json"))
    if not files:
        raise FileNotFoundError(f"No normalized model files found in {NORM_DIR}")
    return files[-1]


def remove_legacy_derived_outputs(derived_dir: Path, *, keep_path: Path) -> list[Path]:
    removed_paths: list[Path] = []
    for pattern in LEGACY_DERIVED_PATTERNS:
        for path in derived_dir.glob(pattern):
            if path == keep_path or path.name in PROTECTED_DERIVED_NAMES:
                continue
            path.unlink()
            removed_paths.append(path)
    return removed_paths


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    latest_json_path = DERIVED_DIR / LATEST_JSON_NAME
    meta_json_path = DERIVED_DIR / META_JSON_NAME
    norm_path = latest_normalized_file()
    print(f"Reading normalized file: {norm_path}")

    with open(norm_path, encoding="utf-8") as f:
        records = json.load(f)

    models = [NormalizedModel.model_validate(r) for r in records]
    refreshed_at = models[0].fetched_at if models else _now_utc()
    rows: list[dict] = []

    for model in models:
        rows.append(to_row(model))

    previous_map = load_previous_models(latest_json_path)
    rows = merge_derived_rows(rows, previous_map, refreshed_at)

    if latest_json_path.exists() or latest_json_path.is_symlink():
        latest_json_path.unlink()
    write_json(rows, latest_json_path)
    with open(meta_json_path, "w", encoding="utf-8") as f:
        json.dump({"refreshed_at": refreshed_at}, f, ensure_ascii=False, indent=2)
    removed_paths = remove_legacy_derived_outputs(DERIVED_DIR, keep_path=latest_json_path)

    print(f"Wrote {len(rows)} rows → {latest_json_path}")
    if removed_paths:
        print(f"Removed {len(removed_paths)} legacy derived artifact(s).")


if __name__ == "__main__":
    main()
