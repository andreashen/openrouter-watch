from __future__ import annotations

import os
import time

import httpx

MODELS_URL = "https://openrouter.ai/api/v1/models"
BENCHMARK_URL = "https://openrouter.ai/api/internal/v1/artificial-analysis-benchmarks"

_HEADERS = {"User-Agent": "Mozilla/5.0"}


def _auth_headers() -> dict[str, str]:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        return {**_HEADERS, "Authorization": f"Bearer {api_key}"}
    return _HEADERS


def fetch_models() -> dict:
    """Fetch all models from OpenRouter and return the full raw response."""
    with httpx.Client(trust_env=False) as client:
        response = client.get(MODELS_URL, headers=_auth_headers(), timeout=30)
        response.raise_for_status()
        return response.json()


def _extract_benchmark_indices(payload: dict) -> dict | None:
    if "data" not in payload:
        return payload

    records = payload.get("data")
    if not records:
        return None

    evaluations = records[0].get("benchmark_data", {}).get("evaluations", {})
    return {
        "intelligence_index": evaluations.get("artificial_analysis_intelligence_index"),
        "coding_index": evaluations.get("artificial_analysis_coding_index"),
        "agentic_index": evaluations.get("artificial_analysis_agentic_index"),
    }


def fetch_benchmark(model_id: str) -> dict | None:
    """Fetch benchmark indices for a model. Returns None on any failure."""
    time.sleep(0.5)
    try:
        with httpx.Client(trust_env=False) as client:
            response = client.get(
                BENCHMARK_URL,
                params={"slug": model_id},
                headers=_auth_headers(),
                timeout=30,
            )
            response.raise_for_status()
            return _extract_benchmark_indices(response.json())
    except Exception:
        return None
