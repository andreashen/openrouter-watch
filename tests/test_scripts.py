"""Script-level tests for M1 pipeline entry points."""

from __future__ import annotations

import json
import re
from pathlib import Path

import scripts.derive as derive_script
import scripts.fetch as fetch_script
import scripts.normalize as normalize_script


def test_fetch_writes_full_payload_with_fetched_at(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(fetch_script, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(
        fetch_script,
        "fetch_models",
        lambda: {"data": [{"id": "openai/gpt-4o"}], "meta": {"source": "fixture"}},
    )

    fetch_script.main()

    raw_path = next((tmp_path / "raw").glob("*_models.json"))
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    assert payload["data"] == [{"id": "openai/gpt-4o"}]
    assert payload["meta"] == {"source": "fixture"}
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", payload["fetched_at"])


def test_fetch_debug_mainstream_filter_keeps_configured_models(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(fetch_script.DEBUG_MAINSTREAM_ENV, "1")
    monkeypatch.setattr(fetch_script, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(
        fetch_script,
        "fetch_models",
        lambda: {
            "data": [
                {"id": "not-mainstream"},
                {"id": fetch_script.MAINSTREAM_MODEL_IDS[1]},
                {"id": fetch_script.MAINSTREAM_MODEL_IDS[0]},
            ]
        },
    )

    fetch_script.main()

    raw_path = next((tmp_path / "raw").glob("*_models.json"))
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    assert [model["id"] for model in payload["data"]] == [
        fetch_script.MAINSTREAM_MODEL_IDS[0],
        fetch_script.MAINSTREAM_MODEL_IDS[1],
    ]


def test_normalize_inherits_raw_fetched_at(tmp_path, monkeypatch) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    raw_path = raw_dir / "20260102_030405_models.json"
    raw_path.write_text(
        json.dumps(
            {
                "fetched_at": "2026-01-02T03:04:05Z",
                "data": [{"id": "openai/gpt-4o", "name": "OpenAI: GPT-4o"}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(normalize_script, "RAW_DIR", raw_dir)
    monkeypatch.setattr(normalize_script, "NORM_DIR", tmp_path / "normalized")

    normalize_script.main()

    normalized_path = next((tmp_path / "normalized").glob("*_models.json"))
    records = json.loads(normalized_path.read_text(encoding="utf-8"))
    assert records[0]["fetched_at"] == "2026-01-02T03:04:05Z"


def test_derive_writes_single_stable_json_output_sorted(tmp_path, monkeypatch) -> None:
    norm_dir = tmp_path / "normalized"
    norm_dir.mkdir()
    records = [
        {
            "model_id": "zeta/model",
            "author": "zeta",
            "slug": "model",
            "vendor_name": "Zeta",
            "name": "Zeta: Model",
            "context_length": None,
            "max_completion_tokens": None,
            "input_price_usd_per_1m": None,
            "output_price_usd_per_1m": None,
            "supports_reasoning": False,
            "supports_tools": False,
            "supports_vision": False,
            "fetched_at": "2026-01-02T03:04:05Z",
        },
        {
            "model_id": "alpha/model",
            "author": "alpha",
            "slug": "model",
            "vendor_name": "Alpha",
            "name": "Alpha: Model",
            "context_length": None,
            "max_completion_tokens": None,
            "input_price_usd_per_1m": None,
            "output_price_usd_per_1m": None,
            "supports_reasoning": False,
            "supports_tools": False,
            "supports_vision": False,
            "fetched_at": "2026-01-02T03:04:05Z",
        },
    ]
    (norm_dir / "20260102_030405_models.json").write_text(json.dumps(records), encoding="utf-8")
    monkeypatch.setattr(derive_script, "NORM_DIR", norm_dir)
    monkeypatch.setattr(derive_script, "DERIVED_DIR", tmp_path / "derived")

    derive_script.main()

    derived_dir = tmp_path / "derived"
    latest_path = derived_dir / "models_latest.json"
    meta_path = derived_dir / "models_meta.json"
    assert latest_path.exists()
    assert meta_path.exists()
    assert not latest_path.is_symlink()
    assert sorted(path.name for path in derived_dir.iterdir()) == [
        "models_latest.json",
        "models_meta.json",
    ]

    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert [row["model_id"] for row in latest] == ["alpha/model", "zeta/model"]
    assert all(row["officially_removed"] is False for row in latest)
    assert all(row["updated_at"] == "2026-01-02T03:04:05Z" for row in latest)
    assert meta == {"refreshed_at": "2026-01-02T03:04:05Z"}


def _make_derived_row(
    model_id: str,
    vendor_name: str,
    *,
    intelligence_index=None,
    coding_index=None,
    agentic_index=None,
    officially_removed: bool = False,
) -> dict:
    return {
        "model_id": model_id,
        "author": vendor_name.lower(),
        "slug": "model",
        "vendor_name": vendor_name,
        "name": f"{vendor_name}: Model",
        "context_length": None,
        "max_completion_tokens": None,
        "input_price_usd_per_1m": None,
        "output_price_usd_per_1m": None,
        "supports_reasoning": False,
        "supports_tools": False,
        "supports_vision": False,
        "intelligence_index": intelligence_index,
        "coding_index": coding_index,
        "agentic_index": agentic_index,
        "officially_removed": officially_removed,
        "openrouter_model_url": f"https://openrouter.ai/{model_id}",
        "fetched_at": "2026-01-02T03:04:05Z",
        "updated_at": "2026-01-02T03:04:05Z",
    }


def test_derive_merges_removed_models_from_previous(tmp_path, monkeypatch) -> None:
    norm_dir = tmp_path / "normalized"
    derived_dir = tmp_path / "derived"
    norm_dir.mkdir()
    derived_dir.mkdir()

    previous_rows = [
        _make_derived_row("alpha/model", "Alpha", intelligence_index=10.0),
        _make_derived_row("removed/model", "Removed", intelligence_index=99.0),
    ]
    previous_json = derived_dir / "models_latest.json"
    previous_json.write_text(json.dumps(previous_rows), encoding="utf-8")

    current_records = [
        {
            "model_id": "alpha/model",
            "author": "alpha",
            "slug": "model",
            "vendor_name": "Alpha",
            "name": "Alpha: Model",
            "context_length": None,
            "max_completion_tokens": None,
            "input_price_usd_per_1m": None,
            "output_price_usd_per_1m": None,
            "supports_reasoning": False,
            "supports_tools": False,
            "supports_vision": False,
            "fetched_at": "2026-01-02T03:04:05Z",
        }
    ]
    (norm_dir / "20260102_030405_models.json").write_text(
        json.dumps(current_records), encoding="utf-8"
    )
    monkeypatch.setattr(derive_script, "NORM_DIR", norm_dir)
    monkeypatch.setattr(derive_script, "DERIVED_DIR", derived_dir)

    derive_script.main()

    latest = json.loads((derived_dir / "models_latest.json").read_text(encoding="utf-8"))
    by_id = {row["model_id"]: row for row in latest}
    assert by_id["removed/model"]["officially_removed"] is True
    assert by_id["removed/model"]["intelligence_index"] == 99.0
    assert by_id["removed/model"]["updated_at"] == "2026-01-02T03:04:05Z"
    assert by_id["alpha/model"]["officially_removed"] is False
    assert by_id["alpha/model"]["intelligence_index"] == 10.0


def test_derive_benchmark_blank_backfill_and_update(tmp_path, monkeypatch) -> None:
    norm_dir = tmp_path / "normalized"
    derived_dir = tmp_path / "derived"
    norm_dir.mkdir()
    derived_dir.mkdir()

    previous_rows = [
        _make_derived_row(
            "alpha/model",
            "Alpha",
            intelligence_index=10.0,
            coding_index=20.0,
            agentic_index=30.0,
        )
    ]
    previous_json = derived_dir / "models_latest.json"
    previous_json.write_text(json.dumps(previous_rows), encoding="utf-8")

    current_records = [
        {
            "model_id": "alpha/model",
            "author": "alpha",
            "slug": "model",
            "vendor_name": "Alpha",
            "name": "Alpha: Model",
            "context_length": None,
            "max_completion_tokens": None,
            "input_price_usd_per_1m": None,
            "output_price_usd_per_1m": None,
            "supports_reasoning": False,
            "supports_tools": False,
            "supports_vision": False,
            "intelligence_index": 50.0,
            "coding_index": None,
            "agentic_index": None,
            "fetched_at": "2026-01-02T03:04:05Z",
        }
    ]
    (norm_dir / "20260102_030405_models.json").write_text(
        json.dumps(current_records), encoding="utf-8"
    )
    monkeypatch.setattr(derive_script, "NORM_DIR", norm_dir)
    monkeypatch.setattr(derive_script, "DERIVED_DIR", derived_dir)

    derive_script.main()

    latest = json.loads((derived_dir / "models_latest.json").read_text(encoding="utf-8"))
    row = latest[0]
    assert row["intelligence_index"] == 50.0
    assert row["coding_index"] == 20.0
    assert row["agentic_index"] == 30.0
    assert row["updated_at"] == "2026-01-02T03:04:05Z"


def test_data_refresh_workflow_targets_main_only() -> None:
    workflow_text = Path(".github/workflows/data-refresh.yml").read_text(encoding="utf-8")

    assert "target_branch" not in workflow_text
    assert 'cron: "17 0 * * *"' in workflow_text
    assert "TARGET_BRANCH: main" in workflow_text
