from __future__ import annotations

import os

import httpx

MODELS_URL = "https://openrouter.ai/api/v1/models"

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


def extract_benchmark_from_raw(raw: dict) -> dict | None:
    """Extract AA benchmark indices embedded in a /api/v1/models item."""
    aa = (raw.get("benchmarks") or {}).get("artificial_analysis")
    if not aa:
        return None

    result = {
        "intelligence_index": aa.get("intelligence_index"),
        "coding_index": aa.get("coding_index"),
        "agentic_index": aa.get("agentic_index"),
    }
    if all(value is None for value in result.values()):
        return None
    return result
