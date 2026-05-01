"""Normalize the latest raw snapshot and save to data/normalized/."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from openrouter_watch.normalizer import normalize_model

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
NORM_DIR = Path(__file__).parent.parent / "data" / "normalized"


def latest_raw_file() -> Path:
    files = sorted(RAW_DIR.glob("*_models.json"))
    if not files:
        raise FileNotFoundError(f"No raw model files found in {RAW_DIR}")
    return files[-1]


def main() -> None:
    NORM_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = latest_raw_file()
    print(f"Reading raw file: {raw_path}")

    with open(raw_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    fetched_at = raw_data.get("fetched_at") or datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    normalized = [normalize_model(m, fetched_at=fetched_at).model_dump() for m in raw_data["data"]]

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = NORM_DIR / f"{ts}_models.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    print(f"Normalized {len(normalized)} models → {out_path}")


if __name__ == "__main__":
    main()
