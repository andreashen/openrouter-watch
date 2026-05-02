"""Optional live HTTP tests against OpenRouter (off by default).

Run with: RUN_LIVE_API=1 pytest tests/test_live_api.py -v
"""

from __future__ import annotations

import os

import pytest

if os.environ.get("RUN_LIVE_API") != "1":
    pytest.skip("Set RUN_LIVE_API=1 to run live OpenRouter API tests", allow_module_level=True)

from openrouter_watch.fetcher import fetch_benchmark, fetch_models


@pytest.mark.live
def test_live_fetch_models_returns_data() -> None:
    payload = fetch_models()
    assert isinstance(payload.get("data"), list)
    assert len(payload["data"]) > 0
    first = payload["data"][0]
    assert "id" in first


@pytest.mark.live
def test_live_fetch_benchmark_accepts_known_model() -> None:
    payload = fetch_models()
    model_id = payload["data"][0]["id"]
    result = fetch_benchmark(model_id)
    assert result is None or isinstance(result, dict)
