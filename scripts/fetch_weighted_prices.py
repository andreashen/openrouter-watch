"""Fetch Weighted Avg Input Price into data/derived sidecar files.

Does NOT modify models_latest.json. Intended for an independent weekly schedule.
"""

from __future__ import annotations

import json
from pathlib import Path

from openrouter_watch.weighted_prices import (
    collect_weighted_prices,
    load_weighted_rows,
    write_weighted_meta,
    write_weighted_prices,
)

DERIVED_DIR = Path(__file__).parent.parent / "data" / "derived"
MODELS_LATEST = DERIVED_DIR / "models_latest.json"
WEIGHTED_LATEST = DERIVED_DIR / "weighted_prices_latest.json"
WEIGHTED_META = DERIVED_DIR / "weighted_prices_meta.json"


def load_model_ids(path: Path) -> list[str]:
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        raise ValueError(f"{path} must contain a JSON array")
    model_ids: list[str] = []
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("model_id"), str):
            model_ids.append(row["model_id"])
    # Preserve stable unique order
    seen: set[str] = set()
    ordered: list[str] = []
    for model_id in model_ids:
        if model_id in seen:
            continue
        seen.add(model_id)
        ordered.append(model_id)
    return ordered


def main() -> None:
    if not MODELS_LATEST.exists():
        raise FileNotFoundError(f"Missing {MODELS_LATEST}; run the main derive pipeline first.")

    model_ids = load_model_ids(MODELS_LATEST)
    print(f"Loaded {len(model_ids)} model_id(s) from {MODELS_LATEST}")

    previous = load_weighted_rows(WEIGHTED_LATEST)
    print(f"Previous sidecar rows: {len(previous)}")

    rows, stats = collect_weighted_prices(model_ids, previous_map=previous)
    write_weighted_prices(rows, WEIGHTED_LATEST)
    write_weighted_meta(stats, WEIGHTED_META)

    print(
        "Done: "
        f"ok={stats['fetched_ok']} failed={stats['fetched_failed']} "
        f"missing_permaslug={stats['missing_permaslug']} non_null={stats['non_null']}"
    )
    print(f"Wrote {len(rows)} rows → {WEIGHTED_LATEST}")
    print(f"Wrote meta → {WEIGHTED_META}")


if __name__ == "__main__":
    main()
