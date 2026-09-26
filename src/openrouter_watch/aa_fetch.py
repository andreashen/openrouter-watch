"""Fetch one Artificial Analysis language-model list and enforce page stability."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import httpx

from .aa_version import canonical_major_minor

FREE_MODELS_URL = "https://artificialanalysis.ai/api/v2/language/models/free"
INDEX_FIELDS = {
    "intelligence_index": "artificial_analysis_intelligence_index",
    "coding_index": "artificial_analysis_coding_index",
    "agentic_index": "artificial_analysis_agentic_index",
}
_HTTP_FAILURES = frozenset({401, 403, 429})
_MAX_PAGES = 100


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _number_or_null(value: object) -> bool:
    if value is None:
        return True
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def parse_response_page(
    body: dict,
    *,
    requested_page: int,
    request_started_at: str,
    request_ended_at: str,
) -> dict:
    """Copy one API page into the capture shape the invariants check."""
    pagination = body.get("pagination") if isinstance(body, dict) else None
    if not isinstance(pagination, dict):
        pagination = {}
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, list):
        data = []
    models: list[dict] = []
    uuids: list[str] = []
    for item in data:
        if not isinstance(item, dict):
            models.append({"id": None, "evaluations_missing": True})
            continue
        model_id = item.get("id")
        uuids.append(model_id if isinstance(model_id, str) else "")
        evaluations = item.get("evaluations")
        model = {
            "id": model_id if isinstance(model_id, str) else None,
            "slug": item.get("slug"),
            "evaluations": evaluations if isinstance(evaluations, dict) else None,
        }
        if "openrouter_api_id" in item:
            model["openrouter_api_id"] = item.get("openrouter_api_id")
        models.append(model)
    return {
        "requested_page": requested_page,
        "page": pagination.get("page"),
        "total_pages": pagination.get("total_pages"),
        "has_more": pagination.get("has_more"),
        "tier": body.get("tier") if isinstance(body, dict) else None,
        "intelligence_index_version": body.get("intelligence_index_version")
        if isinstance(body, dict)
        else None,
        "aa_uuids": uuids,
        "models": models,
        "request_started_at": request_started_at,
        "request_ended_at": request_ended_at,
    }


def page_failures(pages: list[dict]) -> list[str]:
    """Return F-* codes that failed. Empty means the capture is one stable snapshot."""
    failures: list[str] = []
    if not pages:
        return ["F-COMPLETE"]

    def _fail(code: str) -> None:
        if code not in failures:
            failures.append(code)

    total_values = [page.get("total_pages") for page in pages]
    locked = total_values[0]
    if not isinstance(locked, int) or isinstance(locked, bool) or locked < 1:
        _fail("F-T")
        locked_t: int | None = None
    else:
        locked_t = locked
    if any(value != locked for value in total_values):
        _fail("F-T")

    for index, page in enumerate(pages, start=1):
        if page.get("page") != index or page.get("requested_page") != index:
            _fail("F-PAGE")
        has_more = page.get("has_more")
        if locked_t is None or not isinstance(has_more, bool) or has_more != (index < locked_t):
            _fail("F-MORE")
        uuids = page.get("aa_uuids")
        duplicate = not isinstance(uuids, list) or len(uuids) != len(set(uuids))
        blank = isinstance(uuids, list) and any(not uid for uid in uuids)
        if duplicate or blank:
            _fail("F-UUID")

    if locked_t is not None and len(pages) != locked_t:
        _fail("F-COMPLETE")
    elif locked_t is not None and [page.get("requested_page") for page in pages] != list(
        range(1, locked_t + 1)
    ):
        _fail("F-COMPLETE")

    seen: list[str] = []
    for page in pages:
        uuids = page.get("aa_uuids")
        if isinstance(uuids, list):
            seen.extend(uid for uid in uuids if isinstance(uid, str))
    if len(seen) != len(set(seen)):
        _fail("F-UUID")

    tiers = [page.get("tier") for page in pages]
    versions = [canonical_major_minor(page.get("intelligence_index_version")) for page in pages]
    if any(tier is None or tier == "" for tier in tiers) or len(set(tiers)) != 1:
        _fail("F-ENVELOPE")
    if any(version is None for version in versions) or len(set(versions)) != 1:
        _fail("F-ENVELOPE")
    for page in pages:
        for model in page.get("models") or []:
            evaluations = model.get("evaluations") if isinstance(model, dict) else None
            if not isinstance(evaluations, dict):
                _fail("F-ENVELOPE")
                continue
            for wire_name in INDEX_FIELDS.values():
                if wire_name not in evaluations or not _number_or_null(evaluations.get(wire_name)):
                    _fail("F-ENVELOPE")
    return failures


def advance_success_streak(streak: int, fetch_ok: bool) -> int:
    """G1 counts only captures that passed every F-* check."""
    if fetch_ok:
        return streak + 1
    return 0


def _clock() -> Callable[[], str]:
    return _utc_now


def fetch_language_models(
    client: httpx.Client,
    *,
    api_key: str,
    url: str = FREE_MODELS_URL,
    now: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Pull every page. F-* failure discards the capture and does not build a snapshot."""
    stamp = now or _clock()
    pages: list[dict] = []
    http_error: int | None = None
    for requested in range(1, _MAX_PAGES + 1):
        started = stamp()
        response = client.get(
            url,
            params={"page": requested},
            headers={"x-api-key": api_key},
            timeout=60,
        )
        ended = stamp()
        if response.status_code in _HTTP_FAILURES:
            http_error = response.status_code
            break
        response.raise_for_status()
        pages.append(
            parse_response_page(
                response.json(),
                requested_page=requested,
                request_started_at=started,
                request_ended_at=ended,
            )
        )
        has_more = pages[-1].get("has_more")
        if has_more is False:
            break
        if has_more is not True:
            break
    failures = ["F-COMPLETE"] if http_error is not None or not pages else page_failures(pages)
    ok = http_error is None and not failures
    return {
        "ok": ok,
        "http_error": http_error,
        "failures": [] if ok else failures,
        "pages": [] if not ok else pages,
    }
