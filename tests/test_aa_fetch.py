"""Page stability for one AA list capture."""

from __future__ import annotations

import json

import httpx
from pytest_httpx import HTTPXMock

import scripts.fetch_aa as fetch_aa_script
from openrouter_watch.aa_fetch import (
    FREE_MODELS_URL,
    advance_success_streak,
    fetch_language_models,
    page_failures,
    parse_response_page,
)
from openrouter_watch.aa_snapshot import build_snapshot, store_snapshot

AA = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
BB = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def _body(
    *,
    page: int,
    total_pages: int,
    has_more: bool,
    ids: list[str],
    version: float = 4.3,
    tier: str = "free",
    drop_evaluations: bool = False,
) -> dict:
    data = []
    for model_id in ids:
        item = {
            "id": model_id,
            "slug": "model",
            "evaluations": {
                "artificial_analysis_intelligence_index": 10,
                "artificial_analysis_coding_index": 9,
                "artificial_analysis_agentic_index": None,
            },
        }
        if drop_evaluations:
            del item["evaluations"]
        data.append(item)
    return {
        "tier": tier,
        "intelligence_index_version": version,
        "pagination": {
            "page": page,
            "page_size": 200,
            "total_pages": total_pages,
            "has_more": has_more,
        },
        "data": data,
    }


def _capture(body: dict, requested: int) -> dict:
    return parse_response_page(
        body,
        requested_page=requested,
        request_started_at="2026-09-11T12:00:00.000Z",
        request_ended_at="2026-09-11T12:00:01.000Z",
    )


def _pages(*specs: tuple[int, int, bool, list[str]]) -> list[dict]:
    pages = []
    for index, (page, total, has_more, ids) in enumerate(specs, start=1):
        body = _body(page=page, total_pages=total, has_more=has_more, ids=ids)
        pages.append(_capture(body, index))
    return pages


def test_total_pages_change_discards_the_capture() -> None:
    pages = _pages((1, 3, True, [AA]), (2, 2, False, [BB]))
    assert "F-T" in page_failures(pages)
    assert build_snapshot(pages, fetched_at="2026-09-11T12:00:00.000Z") is None
    assert advance_success_streak(2, False) == 0


def test_has_more_and_page_number_and_duplicate_uuid_fail() -> None:
    assert "F-MORE" in page_failures(_pages((1, 3, False, [AA])))
    bad_page = _pages((1, 1, False, [AA]))
    bad_page[0]["page"] = 2
    assert "F-PAGE" in page_failures(bad_page)
    assert "F-UUID" in page_failures(_pages((1, 2, True, [AA]), (2, 2, False, [AA])))
    assert "F-UUID" in page_failures(_pages((1, 1, False, [AA, AA])))
    assert "F-MORE" in page_failures(_pages((1, 1, True, [AA])))


def test_stable_two_page_capture_writes_a_snapshot_and_increments_streak() -> None:
    pages = _pages((1, 2, True, [AA]), (2, 2, False, [BB]))
    assert page_failures(pages) == []
    snapshot = build_snapshot(pages, fetched_at="2026-09-11T12:00:00.000Z")
    assert snapshot is not None
    assert snapshot["intelligence_index_version"] == "4.3"
    assert snapshot["pages_fetched"] == 2
    assert {model["id"] for model in snapshot["models"]} == {AA, BB}
    assert advance_success_streak(2, True) == 3


def test_missing_evaluations_key_fails_the_envelope() -> None:
    body = _body(page=1, total_pages=1, has_more=False, ids=[AA], drop_evaluations=True)
    assert "F-ENVELOPE" in page_failures([_capture(body, 1)])


def test_fetch_discards_partial_http_failure(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{FREE_MODELS_URL}?page=1", status_code=429)
    with httpx.Client(trust_env=False) as client:
        result = fetch_language_models(client, api_key="test-key")
    assert not result["ok"]
    assert result["pages"] == []
    assert result["http_error"] == 429


def test_missing_or_mistyped_data_does_not_become_an_empty_snapshot() -> None:
    missing = _body(page=1, total_pages=1, has_more=False, ids=[AA])
    del missing["data"]
    missing_pages = [_capture(missing, 1)]
    assert "F-ENVELOPE" in page_failures(missing_pages)
    assert build_snapshot(missing_pages, fetched_at="2026-09-11T12:00:00.000Z") is None

    mistyped = _body(page=1, total_pages=1, has_more=False, ids=[AA])
    mistyped["data"] = {"id": AA}
    mistyped_pages = [_capture(mistyped, 1)]
    assert "F-ENVELOPE" in page_failures(mistyped_pages)
    assert build_snapshot(mistyped_pages, fetched_at="2026-09-11T12:00:00.000Z") is None
    assert advance_success_streak(2, False) == 0


def test_transport_and_parse_failures_discard_the_capture(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{FREE_MODELS_URL}?page=1", status_code=500)
    httpx_mock.add_response(url=f"{FREE_MODELS_URL}?page=1", content=b"{", status_code=200)
    httpx_mock.add_exception(httpx.ReadTimeout("timed out"), url=f"{FREE_MODELS_URL}?page=1")
    with httpx.Client(trust_env=False) as client:
        server_error = fetch_language_models(client, api_key="test-key")
        invalid_json = fetch_language_models(client, api_key="test-key")
        timed_out = fetch_language_models(client, api_key="test-key")
    assert server_error["http_error"] == 500
    assert invalid_json["failures"] == ["F-ENVELOPE"]
    assert timed_out["failures"] == ["F-COMPLETE"]
    for result in (server_error, invalid_json, timed_out):
        assert not result["ok"]
        assert result["pages"] == []


def test_failed_fetch_zeroes_streak_and_keeps_previous_snapshot(
    tmp_path, httpx_mock: HTTPXMock
) -> None:
    previous = {
        "aa_snapshot_id": "20260911T120000.000Z_4.3",
        "aa_fetched_at": "2026-09-11T12:00:00.000Z",
        "intelligence_index_version": "4.3",
        "models": [{"id": AA, "slug": "kept", "intelligence_index": 1}],
    }
    store_snapshot(tmp_path, previous)
    fetch_aa_script.write_streak(tmp_path, 2)
    kept_bytes = (tmp_path / "snapshots" / f"{previous['aa_snapshot_id']}.json").read_bytes()
    kept_pointer = (tmp_path / "latest_snapshot.json").read_text(encoding="utf-8")

    httpx_mock.add_response(url=f"{FREE_MODELS_URL}?page=1", status_code=500)
    with httpx.Client(trust_env=False) as client:
        fetched = fetch_language_models(client, api_key="test-key")
    assert fetch_aa_script.commit_fetch(
        tmp_path,
        fetched,
        previous=2,
        fetched_at="2026-09-12T12:00:00.000Z",
    ) == 1
    assert fetch_aa_script.read_streak(tmp_path) == 0
    kept_path = tmp_path / "snapshots" / f"{previous['aa_snapshot_id']}.json"
    assert kept_path.read_bytes() == kept_bytes
    assert (tmp_path / "latest_snapshot.json").read_text(encoding="utf-8") == kept_pointer
    assert list((tmp_path / "snapshots").glob("*.json")) == [
        tmp_path / "snapshots" / f"{previous['aa_snapshot_id']}.json"
    ]


def test_each_capture_is_stored_under_its_own_id(tmp_path) -> None:
    first = build_snapshot(_pages((1, 1, False, [AA])), fetched_at="2026-09-11T12:00:00.000Z")
    second = build_snapshot(_pages((1, 1, False, [BB])), fetched_at="2026-09-12T12:00:00.000Z")
    assert first is not None and second is not None
    store_snapshot(tmp_path, first)
    first_bytes = (tmp_path / "snapshots" / f"{first['aa_snapshot_id']}.json").read_bytes()
    store_snapshot(tmp_path, second)
    assert (tmp_path / "snapshots" / f"{first['aa_snapshot_id']}.json").read_bytes() == first_bytes
    assert (tmp_path / "snapshots" / f"{second['aa_snapshot_id']}.json").is_file()
    pointer = json.loads((tmp_path / "latest_snapshot.json").read_text(encoding="utf-8"))
    assert pointer["aa_snapshot_id"] == second["aa_snapshot_id"]
    changed = dict(first)
    changed["models"] = []
    try:
        store_snapshot(tmp_path, changed)
    except FileExistsError:
        pass
    else:
        raise AssertionError("a different body reused an existing snapshot id")
    assert (tmp_path / "snapshots" / f"{first['aa_snapshot_id']}.json").read_bytes() == first_bytes
    assert json.loads((tmp_path / "latest_snapshot.json").read_text(encoding="utf-8")) == pointer


def test_fetch_keeps_a_stable_capture(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{FREE_MODELS_URL}?page=1",
        json=_body(page=1, total_pages=1, has_more=False, ids=[AA]),
    )
    with httpx.Client(trust_env=False) as client:
        result = fetch_language_models(client, api_key="test-key")
    assert result["ok"]
    assert result["failures"] == []
    assert len(result["pages"]) == 1
