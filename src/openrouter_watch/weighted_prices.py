"""Fetch and merge OpenRouter Weighted Avg Input Price into a sidecar dataset.

Data source (non-official frontend API used by the model page Effective Pricing UI):
  GET https://openrouter.ai/api/frontend/v1/stats/effective-pricing?permaslug=...

Permaslugs are resolved via:
  GET https://openrouter.ai/api/frontend/v1/catalog/models
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httpx

CATALOG_URL = "https://openrouter.ai/api/frontend/v1/catalog/models"
EFFECTIVE_PRICING_URL = "https://openrouter.ai/api/frontend/v1/stats/effective-pricing"

WEIGHTED_PRICE_SOURCE = "openrouter_frontend_effective_pricing"
WEIGHTED_FIELDS = (
    "model_id",
    "weighted_avg_input_price_usd_per_1m",
    "weighted_price_fetched_at",
    "weighted_price_source",
    "permaslug",
)

# Persist at most 4 decimal places (matches table display).
_PRICE_QUANT = Decimal("0.0001")
# Skip rewrite when relative change < 1% AND absolute change < $0.001 / 1M.
_EPS_REL = 0.01
_EPS_ABS = 0.001

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; openrouter-watch/0.1; +https://github.com/andreashen/openrouter-watch)"
    ),
    "Accept": "application/json",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def round_price(value: float | None) -> float | None:
    if value is None:
        return None
    try:
        quantized = Decimal(str(value)).quantize(_PRICE_QUANT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return None
    return float(quantized)


def normalize_weighted_input(raw: Any) -> float | None:
    """Treat missing / non-positive API values as unavailable."""
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return round_price(value)


def price_changed(
    previous: float | None,
    current: float | None,
    *,
    rel: float = _EPS_REL,
    abs_eps: float = _EPS_ABS,
) -> bool:
    if previous is None and current is None:
        return False
    if previous is None or current is None:
        return True
    delta = abs(current - previous)
    if delta < abs_eps:
        return False
    scale = max(abs(previous), abs(current), 1e-12)
    return (delta / scale) >= rel


def fetch_catalog_permaslugs(client: httpx.Client | None = None) -> dict[str, str]:
    """Return mapping model slug (model_id) → versioned permaslug."""
    owns_client = client is None
    if client is None:
        client = httpx.Client(headers=_HEADERS, timeout=60.0, trust_env=False)
    try:
        response = client.get(CATALOG_URL)
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("data") if isinstance(payload, dict) else payload
        mapping: dict[str, str] = {}
        if not isinstance(rows, list):
            return mapping
        for row in rows:
            if not isinstance(row, dict):
                continue
            slug = row.get("slug")
            permaslug = row.get("permaslug") or slug
            if isinstance(slug, str) and slug and isinstance(permaslug, str) and permaslug:
                mapping[slug] = permaslug
        return mapping
    finally:
        if owns_client:
            client.close()


def fetch_weighted_input_price(
    permaslug: str,
    client: httpx.Client | None = None,
) -> float | None:
    owns_client = client is None
    if client is None:
        client = httpx.Client(headers=_HEADERS, timeout=30.0, trust_env=False)
    try:
        response = client.get(EFFECTIVE_PRICING_URL, params={"permaslug": permaslug})
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            return None
        return normalize_weighted_input(data.get("weightedInputPrice"))
    finally:
        if owns_client:
            client.close()


def load_weighted_rows(path: Path | str) -> dict[str, dict]:
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        return {}
    out: dict[str, dict] = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("model_id"), str):
            out[row["model_id"]] = _normalize_row(row)
    return out


def _normalize_row(row: dict) -> dict:
    return {
        "model_id": row["model_id"],
        "weighted_avg_input_price_usd_per_1m": normalize_weighted_input(
            row.get("weighted_avg_input_price_usd_per_1m")
        ),
        "weighted_price_fetched_at": row.get("weighted_price_fetched_at"),
        "weighted_price_source": row.get("weighted_price_source") or WEIGHTED_PRICE_SOURCE,
        "permaslug": row.get("permaslug"),
    }


def merge_weighted_row(
    *,
    model_id: str,
    current_price: float | None,
    permaslug: str | None,
    previous: dict | None,
    fetched_at: str,
    fetch_failed: bool = False,
) -> dict:
    """Merge one model row with epsilon / failure inheritance."""
    previous = _normalize_row(previous) if previous else None
    if fetch_failed:
        if previous is not None:
            return previous
        return {
            "model_id": model_id,
            "weighted_avg_input_price_usd_per_1m": None,
            "weighted_price_fetched_at": fetched_at,
            "weighted_price_source": WEIGHTED_PRICE_SOURCE,
            "permaslug": permaslug,
        }

    current_price = normalize_weighted_input(current_price)
    if previous is not None and not price_changed(
        previous.get("weighted_avg_input_price_usd_per_1m"),
        current_price,
    ):
        # Keep previous timestamps when value is effectively unchanged.
        return {
            **previous,
            "permaslug": permaslug or previous.get("permaslug"),
            "weighted_price_source": WEIGHTED_PRICE_SOURCE,
        }

    return {
        "model_id": model_id,
        "weighted_avg_input_price_usd_per_1m": current_price,
        "weighted_price_fetched_at": fetched_at,
        "weighted_price_source": WEIGHTED_PRICE_SOURCE,
        "permaslug": permaslug,
    }


def collect_weighted_prices(
    model_ids: list[str],
    *,
    previous_map: dict[str, dict] | None = None,
    permaslug_by_model: dict[str, str] | None = None,
    sleep_s: float = 0.15,
    client: httpx.Client | None = None,
    progress_every: int = 25,
) -> tuple[list[dict], dict]:
    """Fetch weighted input prices for all model_ids and merge with previous sidecar."""
    previous_map = previous_map or {}
    owns_client = client is None
    if client is None:
        client = httpx.Client(headers=_HEADERS, timeout=30.0, trust_env=False)

    fetched_at = _now_utc()
    stats = {
        "requested": len(model_ids),
        "fetched_ok": 0,
        "fetched_failed": 0,
        "missing_permaslug": 0,
        "non_null": 0,
        "refreshed_at": fetched_at,
    }

    try:
        if permaslug_by_model is None:
            permaslug_by_model = fetch_catalog_permaslugs(client)

        rows: list[dict] = []
        for index, model_id in enumerate(model_ids, start=1):
            permaslug = permaslug_by_model.get(model_id)
            previous = previous_map.get(model_id)
            if not permaslug:
                stats["missing_permaslug"] += 1
                rows.append(
                    merge_weighted_row(
                        model_id=model_id,
                        current_price=None,
                        permaslug=None,
                        previous=previous,
                        fetched_at=fetched_at,
                        fetch_failed=True,
                    )
                )
            else:
                try:
                    price = fetch_weighted_input_price(permaslug, client=client)
                    stats["fetched_ok"] += 1
                    row = merge_weighted_row(
                        model_id=model_id,
                        current_price=price,
                        permaslug=permaslug,
                        previous=previous,
                        fetched_at=fetched_at,
                        fetch_failed=False,
                    )
                except Exception:
                    stats["fetched_failed"] += 1
                    row = merge_weighted_row(
                        model_id=model_id,
                        current_price=None,
                        permaslug=permaslug,
                        previous=previous,
                        fetched_at=fetched_at,
                        fetch_failed=True,
                    )
                rows.append(row)

            if row.get("weighted_avg_input_price_usd_per_1m") is not None:
                stats["non_null"] += 1

            if progress_every and index % progress_every == 0:
                print(f"  … {index}/{len(model_ids)} models processed")

            if sleep_s > 0 and index < len(model_ids):
                time.sleep(sleep_s)

        rows.sort(key=lambda row: row["model_id"])
        return rows, stats
    finally:
        if owns_client:
            client.close()


def write_weighted_prices(rows: list[dict], path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [_normalize_row(row) for row in rows]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)


def write_weighted_meta(meta: dict, path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
