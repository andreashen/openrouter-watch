from __future__ import annotations

import os
import time
from typing import TypedDict

import httpx

MODELS_URL = "https://openrouter.ai/api/v1/models"
BENCHMARK_URL = "https://openrouter.ai/api/internal/v1/artificial-analysis-benchmarks"

_HEADERS = {"User-Agent": "Mozilla/5.0"}


class BenchmarkDetails(TypedDict):
    indices: dict[str, float | None]
    query_slug: str
    heuristic_openrouter_slug: str | None
    permaslug: str | None


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


def _extract_indices_from_evaluations(evaluations: dict) -> dict[str, float | None]:
    return {
        "intelligence_index": evaluations.get("artificial_analysis_intelligence_index"),
        "coding_index": evaluations.get("artificial_analysis_coding_index"),
        "agentic_index": evaluations.get("artificial_analysis_agentic_index"),
    }


def _intelligence_score(record: dict) -> float:
    evaluations = record.get("benchmark_data", {}).get("evaluations", {})
    value = evaluations.get("artificial_analysis_intelligence_index")
    if isinstance(value, (int, float)):
        return float(value)
    return float("-inf")


def _extract_benchmark_details(payload: dict, query_slug: str) -> BenchmarkDetails | None:
    if "data" not in payload:
        return {
            "indices": {
                "intelligence_index": payload.get("intelligence_index"),
                "coding_index": payload.get("coding_index"),
                "agentic_index": payload.get("agentic_index"),
            },
            "query_slug": query_slug,
            "heuristic_openrouter_slug": None,
            "permaslug": None,
        }

    records = payload.get("data")
    if not records:
        return None

    best_record = max(records, key=_intelligence_score)
    evaluations = best_record.get("benchmark_data", {}).get("evaluations", {})
    return {
        "indices": _extract_indices_from_evaluations(evaluations),
        "query_slug": query_slug,
        "heuristic_openrouter_slug": best_record.get("heuristic_openrouter_slug"),
        "permaslug": best_record.get("permaslug"),
    }


def _candidate_slugs(model_id: str, canonical_slug: str | None = None) -> list[str]:
    candidates = [model_id]
    if canonical_slug and canonical_slug not in candidates:
        candidates.append(canonical_slug)
    return candidates


def fetch_benchmark_details(model_id: str, canonical_slug: str | None = None) -> BenchmarkDetails | None:
    """Fetch benchmark details for a model; supports canonical slug fallback."""
    try:
        with httpx.Client(trust_env=False) as client:
            for slug in _candidate_slugs(model_id, canonical_slug):
                time.sleep(0.5)
                try:
                    response = client.get(
                        BENCHMARK_URL,
                        params={"slug": slug},
                        headers=_auth_headers(),
                        timeout=30,
                    )
                    response.raise_for_status()
                    details = _extract_benchmark_details(response.json(), query_slug=slug)
                    if details is not None:
                        return details
                except Exception:
                    continue
    except Exception:
        return None
    return None


def fetch_benchmark(model_id: str, canonical_slug: str | None = None) -> dict | None:
    """Fetch benchmark indices for a model. Returns None on any failure."""
    details = fetch_benchmark_details(model_id, canonical_slug=canonical_slug)
    if details is None:
        return None
    return details["indices"]
