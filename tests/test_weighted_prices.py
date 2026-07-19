"""Tests for weighted avg input price sidecar helpers."""

from __future__ import annotations

import re
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from openrouter_watch.weighted_prices import (
    CATALOG_URL,
    collect_weighted_prices,
    fetch_catalog_permaslugs,
    fetch_weighted_input_price,
    merge_weighted_row,
    normalize_weighted_input,
    price_changed,
    round_price,
)

_EFFECTIVE_URL_RE = re.compile(r".*/api/frontend/v1/stats/effective-pricing(?:\?.*)?$")


def test_round_price_quantizes_to_four_decimals() -> None:
    assert round_price(1.725584671) == 1.7256
    assert round_price(0.169783) == 0.1698


def test_normalize_weighted_input_treats_non_positive_as_null() -> None:
    assert normalize_weighted_input(0) is None
    assert normalize_weighted_input(-1) is None
    assert normalize_weighted_input(None) is None
    assert normalize_weighted_input(1.23456) == 1.2346


def test_price_changed_epsilon() -> None:
    assert price_changed(1.0, 1.0005) is False  # abs < 0.001
    assert price_changed(1.0, 1.02) is True
    assert price_changed(None, 1.0) is True
    assert price_changed(None, None) is False


def test_merge_inherits_on_fetch_failure() -> None:
    previous = {
        "model_id": "openai/gpt-5.4",
        "weighted_avg_input_price_usd_per_1m": 1.5,
        "weighted_price_fetched_at": "2026-07-01T00:00:00Z",
        "weighted_price_source": "openrouter_frontend_effective_pricing",
        "permaslug": "openai/gpt-5.4-20260305",
    }
    merged = merge_weighted_row(
        model_id="openai/gpt-5.4",
        current_price=None,
        permaslug="openai/gpt-5.4-20260305",
        previous=previous,
        fetched_at="2026-07-19T00:00:00Z",
        fetch_failed=True,
    )
    assert merged["weighted_avg_input_price_usd_per_1m"] == 1.5
    assert merged["weighted_price_fetched_at"] == "2026-07-01T00:00:00Z"


def test_merge_skips_tiny_jitter() -> None:
    previous = {
        "model_id": "openai/gpt-5.4",
        "weighted_avg_input_price_usd_per_1m": 1.7256,
        "weighted_price_fetched_at": "2026-07-01T00:00:00Z",
        "weighted_price_source": "openrouter_frontend_effective_pricing",
        "permaslug": "openai/gpt-5.4-20260305",
    }
    merged = merge_weighted_row(
        model_id="openai/gpt-5.4",
        current_price=1.7259,  # tiny abs delta after rounding path
        permaslug="openai/gpt-5.4-20260305",
        previous=previous,
        fetched_at="2026-07-19T00:00:00Z",
        fetch_failed=False,
    )
    assert merged["weighted_price_fetched_at"] == "2026-07-01T00:00:00Z"
    assert merged["weighted_avg_input_price_usd_per_1m"] == 1.7256


def test_fetch_catalog_permaslugs(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=CATALOG_URL,
        json={
            "data": [
                {"slug": "openai/gpt-5.4", "permaslug": "openai/gpt-5.4-20260305"},
                {"slug": "z-ai/glm-5.2", "permaslug": "z-ai/glm-5.2-20260616"},
            ]
        },
    )
    mapping = fetch_catalog_permaslugs()
    assert mapping == {
        "openai/gpt-5.4": "openai/gpt-5.4-20260305",
        "z-ai/glm-5.2": "z-ai/glm-5.2-20260616",
    }


def test_fetch_weighted_input_price(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=_EFFECTIVE_URL_RE,
        json={"data": {"weightedInputPrice": 1.7255846710618987}},
    )
    assert fetch_weighted_input_price("openai/gpt-5.4-20260305") == 1.7256


def test_fetch_weighted_input_price_zero_is_null(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=_EFFECTIVE_URL_RE,
        json={"data": {"weightedInputPrice": 0, "providerSummaries": []}},
    )
    assert fetch_weighted_input_price("openrouter/auto-beta") is None


def test_collect_weighted_prices_merges(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=CATALOG_URL,
        json={
            "data": [
                {"slug": "openai/gpt-5.4", "permaslug": "openai/gpt-5.4-20260305"},
                {"slug": "missing/model", "permaslug": "missing/model"},
            ]
        },
    )
    httpx_mock.add_response(
        url=_EFFECTIVE_URL_RE,
        json={"data": {"weightedInputPrice": 1.5}},
    )
    httpx_mock.add_response(
        url=_EFFECTIVE_URL_RE,
        status_code=500,
    )

    previous = {
        "missing/model": {
            "model_id": "missing/model",
            "weighted_avg_input_price_usd_per_1m": 0.42,
            "weighted_price_fetched_at": "2026-07-01T00:00:00Z",
            "weighted_price_source": "openrouter_frontend_effective_pricing",
            "permaslug": "missing/model",
        }
    }
    rows, stats = collect_weighted_prices(
        ["openai/gpt-5.4", "missing/model", "unknown/slug"],
        previous_map=previous,
        sleep_s=0,
        progress_every=0,
    )
    by_id = {row["model_id"]: row for row in rows}
    assert by_id["openai/gpt-5.4"]["weighted_avg_input_price_usd_per_1m"] == 1.5
    assert by_id["missing/model"]["weighted_avg_input_price_usd_per_1m"] == 0.42
    assert by_id["unknown/slug"]["weighted_avg_input_price_usd_per_1m"] is None
    assert stats["fetched_ok"] == 1
    assert stats["fetched_failed"] == 1
    assert stats["missing_permaslug"] == 1


def test_collect_raises_on_catalog_http_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CATALOG_URL, status_code=403)
    with pytest.raises(httpx.HTTPStatusError):
        collect_weighted_prices(["openai/gpt-5.4"], sleep_s=0, progress_every=0)


def test_weighted_price_refresh_workflow_is_independent() -> None:
    workflow = Path(".github/workflows/weighted-price-refresh.yml").read_text(encoding="utf-8")
    assert "fetch_weighted_prices.py" in workflow
    assert "models_latest.json" in workflow
    assert "weighted_prices_latest.json" in workflow
    assert "17 1 * * 1" in workflow
    # Must not run the daily models pipeline scripts
    assert "scripts/fetch.py" not in workflow
    assert "scripts/derive.py" not in workflow
