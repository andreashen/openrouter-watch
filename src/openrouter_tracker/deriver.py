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
]


def to_row(model: NormalizedModel, benchmark: dict | None = None) -> dict:
    row = model.model_dump()
    row["intelligence_index"] = None
    row["coding_index"] = None
    row["agentic_index"] = None
    if benchmark:
        row["intelligence_index"] = benchmark.get("intelligence_index")
        row["coding_index"] = benchmark.get("coding_index")
        row["agentic_index"] = benchmark.get("agentic_index")
    return {k: row.get(k) for k in _FIELDS}


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
