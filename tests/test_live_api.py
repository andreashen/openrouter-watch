"""Optional live HTTP tests against OpenRouter (off by default).

Run with: RUN_LIVE_API=1 pytest tests/test_live_api.py -v
"""

from __future__ import annotations

import os

import pytest

if os.environ.get("RUN_LIVE_API") != "1":
    pytest.skip("Set RUN_LIVE_API=1 to run live OpenRouter API tests", allow_module_level=True)

from openrouter_watch.fetcher import extract_benchmark_from_raw, fetch_models


@pytest.mark.live
def test_live_fetch_models_returns_data() -> None:
    payload = fetch_models()
    assert isinstance(payload.get("data"), list)
    assert len(payload["data"]) > 0
    first = payload["data"][0]
    assert "id" in first


@pytest.mark.live
def test_live_models_embed_artificial_analysis_for_opus_4_8() -> None:
    payload = fetch_models()
    opus = next(m for m in payload["data"] if m["id"] == "anthropic/claude-opus-4.8")
    benchmark = extract_benchmark_from_raw(opus)
    assert benchmark is not None
    assert benchmark["intelligence_index"] is not None
    assert benchmark["coding_index"] is not None
    assert benchmark["agentic_index"] is not None
