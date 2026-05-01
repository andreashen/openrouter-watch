"""Fetch raw model data from OpenRouter and save to data/raw/."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from openrouter_watch.fetcher import fetch_models

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
DEBUG_MAINSTREAM_ENV = "OPENROUTER_DEBUG_MAINSTREAM_20"
MAINSTREAM_MODEL_IDS = [
    "qwen/qwen3.6-35b-a3b",
    "qwen/qwen3.6-27b",
    "openai/gpt-5.5",
    "deepseek/deepseek-v4-pro",
    "deepseek/deepseek-v4-flash",
    "moonshotai/kimi-k2.6",
    "anthropic/claude-opus-4.7",
    "z-ai/glm-5.1",
    "z-ai/glm-5v-turbo",
    "openai/gpt-5.4-nano",
    "openai/gpt-5.4-mini",
    "z-ai/glm-5-turbo",
    "openai/gpt-5.4",
    "google/gemini-3.1-flash-lite-preview",
    "qwen/qwen3.5-35b-a3b",
    "qwen/qwen3.5-27b",
    "qwen/qwen3.5-122b-a10b",
    "openai/gpt-5.3-codex",
    "google/gemini-3.1-pro-preview",
    "anthropic/claude-sonnet-4.6",
]


def _debug_mainstream_enabled() -> bool:
    return os.environ.get(DEBUG_MAINSTREAM_ENV, "").lower() in {"1", "true", "yes", "on"}


def _filter_mainstream_models(payload: dict) -> dict:
    models_by_id = {model.get("id"): model for model in payload["data"]}
    selected = [
        models_by_id[model_id] for model_id in MAINSTREAM_MODEL_IDS if model_id in models_by_id
    ]
    return {**payload, "data": selected}


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_path = RAW_DIR / f"{ts}_models.json"

    print("Fetching models from OpenRouter...")
    payload = fetch_models()
    if _debug_mainstream_enabled():
        payload = _filter_mainstream_models(payload)
        print(
            f"Debug mode {DEBUG_MAINSTREAM_ENV}=1: kept {len(payload['data'])} mainstream models."
        )
    print(f"Fetched {len(payload['data'])} models.")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({**payload, "fetched_at": fetched_at}, f, ensure_ascii=False, indent=2)

    print(f"Saved raw snapshot → {out_path}")


if __name__ == "__main__":
    main()
