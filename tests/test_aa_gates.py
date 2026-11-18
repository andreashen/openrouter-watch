"""Public cutover stays closed without a grant, including the committed switch."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from openrouter_watch.aa_gates import (
    cutover_allowed,
    effective_collect_openrouter_benchmark,
    effective_display_source,
    g0_problems,
    publication_problems,
    repo_publication_is_held,
    select_public_benchmark_rows,
    stop_collection_allowed,
)
from openrouter_watch.aa_join import qa_sample_problems
from openrouter_watch.aa_snapshot import scores_from_snapshot
from openrouter_watch.aa_version import g3_alignment
from openrouter_watch.fetcher import extract_benchmark_from_raw

ROOT = Path(__file__).resolve().parents[1]
AA = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def _grant() -> dict:
    return {
        "date": "2026-09-26",
        "grantor": "Artificial Analysis",
        "tier": "commercial",
        "expires": "2099-01-01",
        "instrument": "commercial_contract",
        "authorization_ref": "https://contracts.artificialanalysis.ai/openrouter-watch/2026",
        "verified_by": "Andriy Shen",
        "scope": {"page": True, "json": True, "redistributable": True},
    }


def _ready(**overrides: object) -> dict:
    flags = {
        "g0_record": _grant(),
        "consecutive_successes": 3,
        "page_failures": [],
        "g3_ok": True,
        "g4_ok": True,
        "g5_ok": True,
        "sit_passed": True,
    }
    flags.update(overrides)
    return flags


def test_g0_missing_blocks_display_and_collection_stop() -> None:
    assert "g0_missing" in g0_problems(None)
    allowed = cutover_allowed(**_ready(g0_record=None))
    assert not allowed
    openrouter_rows = [{"model_id": "openai/gpt-4o", "intelligence_index": 1}]
    aa_rows = [{"model_id": "openai/gpt-4o", "intelligence_index": 99}]
    selected = select_public_benchmark_rows(
        openrouter_rows,
        aa_rows,
        cutover_allowed=allowed,
    )
    assert selected is openrouter_rows
    publication = {
        "public_display_source": "artificial_analysis_api",
        "collect_openrouter_benchmark": False,
    }
    assert effective_display_source(publication, cutover_allowed=allowed) == "openrouter"
    assert effective_collect_openrouter_benchmark(
        publication,
        cutover_allowed=allowed,
        refresh_verified=True,
    )
    assert publication_problems(publication, cutover_allowed=allowed, refresh_verified=True) == [
        "public_display_blocked",
        "stop_collection_blocked",
    ]


def test_g0_rejects_missing_redistribution_rights() -> None:
    today = date(2026, 9, 26)
    withheld = _grant()
    withheld["scope"]["redistributable"] = False
    assert "scope_redistributable" in g0_problems(withheld, today=today)
    assert not cutover_allowed(**_ready(g0_record=withheld))

    free = _grant()
    free["tier"] = "free"
    assert "authorization_basis" in g0_problems(free, today=today)
    pro = _grant()
    pro["tier"] = "pro"
    assert "authorization_basis" in g0_problems(pro, today=today)

    expired = _grant()
    expired["expires"] = "2020-01-01"
    assert "expires_elapsed" in g0_problems(expired, today=today)
    assert not cutover_allowed(**_ready(g0_record=expired))

    placeholder = _grant()
    placeholder["authorization_ref"] = "https://example.invalid/aa-public-grant"
    assert "authorization_basis" in g0_problems(placeholder, today=today)

    bare_commercial = {
        "date": "2026-09-26",
        "grantor": "Artificial Analysis",
        "tier": "commercial",
        "expires": "2099-01-01",
        "scope": {"page": True, "json": True, "redistributable": True},
    }
    assert "authorization_basis" in g0_problems(bare_commercial, today=today)
    assert not cutover_allowed(**_ready(g0_record=bare_commercial))

    granted = _grant()
    granted["tier"] = "free"
    granted["instrument"] = "written_authorization"
    granted["authorization_ref"] = "https://files.artificialanalysis.ai/grants/openrouter-watch"
    granted["verified_by"] = "Andriy Shen"
    assert g0_problems(granted, today=today) == []


def test_incomplete_grant_and_each_later_gate_block_cutover() -> None:
    partial = _grant()
    del partial["expires"]
    assert "expires" in g0_problems(partial)
    assert not cutover_allowed(**_ready(g0_record=partial))
    assert not cutover_allowed(**_ready(consecutive_successes=2))
    assert not cutover_allowed(**_ready(page_failures=["F-UUID"]))
    assert not cutover_allowed(**_ready(g3_ok=False))
    assert not cutover_allowed(**_ready(g4_ok=False))
    assert not cutover_allowed(**_ready(g5_ok=False))
    assert not cutover_allowed(**_ready(sit_passed=False))


def test_stop_collection_needs_cutover_and_a_verified_refresh() -> None:
    assert not stop_collection_allowed(cutover_allowed=True, refresh_verified=False)
    assert not stop_collection_allowed(cutover_allowed=False, refresh_verified=True)
    assert stop_collection_allowed(cutover_allowed=True, refresh_verified=True)


def test_scores_do_not_cross_snapshots() -> None:
    current = {
        "aa_snapshot_id": "current",
        "models": [{"id": AA, "intelligence_index": 50, "coding_index": None, "agentic_index": 40}],
    }
    scores = scores_from_snapshot(current, AA)
    assert scores["coding_index"] is None
    assert scores["intelligence_index"] == 50


def test_g3_requires_eval_page_and_docs_to_agree_with_the_envelope() -> None:
    eval_page = "Artificial Analysis Intelligence Index v4.3"
    docs = "Current version: v4.3.2. Full composition follows."
    assert g3_alignment(4.3, eval_page, docs)["ok"]
    assert g3_alignment(4.1, eval_page, docs)["reason"] == "envelope_mismatch"
    conflict = g3_alignment(4.3, eval_page, "Current version: v4.2.0")
    assert conflict["reason"] == "official_sources_conflict"
    assert not conflict["ok"]
    assert g3_alignment(4.3, "no version here", docs)["reason"] == "parse_failed"


def test_committed_publication_and_sample_hold_the_public_page() -> None:
    publication = json.loads((ROOT / "data/aa_join/publication.json").read_text(encoding="utf-8"))
    sample = json.loads((ROOT / "data/aa_join/qa_sample.json").read_text(encoding="utf-8"))
    rows = json.loads((ROOT / "data/derived/models_latest.json").read_text(encoding="utf-8"))
    assert repo_publication_is_held(publication) == []
    assert qa_sample_problems(sample, rows) == []
    assert publication["g0"] is None
    index = (ROOT / "web/src/pages/index.astro").read_text(encoding="utf-8")
    table = (ROOT / "web/src/components/ModelTable.astro").read_text(encoding="utf-8")
    client = (ROOT / "web/src/lib/modelTableClient.js").read_text(encoding="utf-8")
    assert "aaScoreDisplay" not in index
    assert "aaScoreDisplay" not in table
    assert "aaScoreDisplay" not in client
    assert "models_latest.json" in index
    assert extract_benchmark_from_raw({"id": "openai/gpt-4o"}) is None
    refresh = (ROOT / ".github/workflows/data-refresh.yml").read_text(encoding="utf-8")
    assert "python scripts/fetch.py" in refresh
    assert "python scripts/derive.py" in refresh
    assert "fetch_aa.py" not in refresh
