"""Script-level tests for M1 pipeline entry points."""

from __future__ import annotations

import json
import re

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


def test_derive_writes_timestamped_outputs_sorted_and_latest(tmp_path, monkeypatch) -> None:
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
    monkeypatch.setattr(
        derive_script,
        "fetch_benchmark_details",
        lambda model_id, canonical_slug=None: None,
    )

    derive_script.main()

    derived_dir = tmp_path / "derived"
    json_files = [
        path.name for path in derived_dir.glob("models_*.json") if path.name != "models_latest.json"
    ]
    csv_files = [path.name for path in derived_dir.glob("models_*.csv")]
    assert any(re.fullmatch(r"models_\d{8}_\d{6}\.json", name) for name in json_files)
    assert any(re.fullmatch(r"models_\d{8}_\d{6}\.csv", name) for name in csv_files)

    latest_path = derived_dir / "models_latest.json"
    timestamped_path = derived_dir / json_files[0]

    assert latest_path.is_symlink()
    assert latest_path.resolve() == timestamped_path.resolve()

    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    timestamped = json.loads(timestamped_path.read_text(encoding="utf-8"))
    assert [row["model_id"] for row in latest] == ["alpha/model", "zeta/model"]
    assert latest == timestamped
    assert all(row["officially_removed"] is False for row in latest)


def _make_derived_row(
    model_id: str,
    vendor_name: str,
    *,
    intelligence_index=None,
    coding_index=None,
    agentic_index=None,
    officially_removed: bool = False,
    latest_alias_target: str | None = None,
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
        "latest_alias_target": latest_alias_target,
        "fetched_at": "2026-01-02T03:04:05Z",
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
    previous_json = derived_dir / "models_20260101_000000.json"
    previous_json.write_text(json.dumps(previous_rows), encoding="utf-8")
    (derived_dir / "models_latest.json").symlink_to(previous_json.name)

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
    monkeypatch.setattr(
        derive_script,
        "fetch_benchmark_details",
        lambda model_id, canonical_slug=None: (
            None
            if model_id == "alpha/model"
            else {
                "indices": {
                    "intelligence_index": 99.0,
                    "coding_index": None,
                    "agentic_index": None,
                },
                "heuristic_openrouter_slug": None,
                "permaslug": None,
                "query_slug": model_id,
            }
        ),
    )

    derive_script.main()

    latest = json.loads((derived_dir / "models_latest.json").read_text(encoding="utf-8"))
    by_id = {row["model_id"]: row for row in latest}
    assert by_id["removed/model"]["officially_removed"] is True
    assert by_id["removed/model"]["intelligence_index"] == 99.0
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
    previous_json = derived_dir / "models_20260101_000000.json"
    previous_json.write_text(json.dumps(previous_rows), encoding="utf-8")
    (derived_dir / "models_latest.json").symlink_to(previous_json.name)

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
    monkeypatch.setattr(
        derive_script,
        "fetch_benchmark_details",
        lambda model_id, canonical_slug=None: {
            "indices": {
                "intelligence_index": 50.0,
                "coding_index": None,
                "agentic_index": None,
            },
            "heuristic_openrouter_slug": None,
            "permaslug": None,
            "query_slug": canonical_slug or model_id,
        },
    )

    derive_script.main()

    latest = json.loads((derived_dir / "models_latest.json").read_text(encoding="utf-8"))
    row = latest[0]
    assert row["intelligence_index"] == 50.0
    assert row["coding_index"] == 20.0
    assert row["agentic_index"] == 30.0


def test_derive_sets_latest_alias_target_from_benchmark_relation(tmp_path, monkeypatch) -> None:
    norm_dir = tmp_path / "normalized"
    derived_dir = tmp_path / "derived"
    norm_dir.mkdir()
    derived_dir.mkdir()

    current_records = [
        {
            "model_id": "moonshotai/kimi-k2.6",
            "author": "moonshotai",
            "slug": "kimi-k2.6",
            "vendor_name": "MoonshotAI",
            "name": "MoonshotAI: Kimi K2.6",
            "context_length": 262144,
            "max_completion_tokens": 262142,
            "input_price_usd_per_1m": 0.68,
            "output_price_usd_per_1m": 3.41,
            "supports_reasoning": True,
            "supports_tools": True,
            "supports_vision": True,
            "fetched_at": "2026-01-02T03:04:05Z",
            "canonical_slug": "moonshotai/kimi-k2.6-20260420",
        },
        {
            "model_id": "~moonshotai/kimi-latest",
            "author": "~moonshotai",
            "slug": "kimi-latest",
            "vendor_name": "~moonshotai",
            "name": "MoonshotAI Kimi Latest",
            "context_length": 262144,
            "max_completion_tokens": 262142,
            "input_price_usd_per_1m": 0.68,
            "output_price_usd_per_1m": 3.41,
            "supports_reasoning": True,
            "supports_tools": True,
            "supports_vision": True,
            "fetched_at": "2026-01-02T03:04:05Z",
            "canonical_slug": "~moonshotai/kimi-latest",
        },
    ]
    (norm_dir / "20260102_030405_models.json").write_text(
        json.dumps(current_records), encoding="utf-8"
    )

    def _fake_fetch_benchmark_details(model_id: str, canonical_slug: str | None = None) -> dict:
        if model_id == "moonshotai/kimi-k2.6":
            return {
                "indices": {
                    "intelligence_index": 53.9,
                    "coding_index": 47.1,
                    "agentic_index": 66.0,
                },
                "heuristic_openrouter_slug": None,
                "permaslug": "moonshotai/kimi-k2.6-20260420",
                "query_slug": model_id,
            }
        if model_id == "~moonshotai/kimi-latest":
            return {
                "indices": {
                    "intelligence_index": 53.9,
                    "coding_index": 47.1,
                    "agentic_index": 66.0,
                },
                "heuristic_openrouter_slug": "moonshotai/kimi-k2.6",
                "permaslug": "moonshotai/kimi-k2.6-20260420",
                "query_slug": model_id,
            }
        raise AssertionError(f"Unexpected model id: {model_id}, canonical={canonical_slug}")

    monkeypatch.setattr(derive_script, "NORM_DIR", norm_dir)
    monkeypatch.setattr(derive_script, "DERIVED_DIR", derived_dir)
    monkeypatch.setattr(derive_script, "fetch_benchmark_details", _fake_fetch_benchmark_details)

    derive_script.main()

    latest = json.loads((derived_dir / "models_latest.json").read_text(encoding="utf-8"))
    by_id = {row["model_id"]: row for row in latest}
    assert by_id["~moonshotai/kimi-latest"]["latest_alias_target"] == "moonshotai/kimi-k2.6"
    assert by_id["moonshotai/kimi-k2.6"]["latest_alias_target"] is None


def test_derive_keeps_previous_gpt55_pro_benchmark_when_live_is_null(tmp_path, monkeypatch) -> None:
    norm_dir = tmp_path / "normalized"
    derived_dir = tmp_path / "derived"
    norm_dir.mkdir()
    derived_dir.mkdir()

    previous_rows = [
        _make_derived_row(
            "openai/gpt-5.5-pro",
            "OpenAI",
            intelligence_index=62.0,
            coding_index=58.0,
            agentic_index=75.0,
        )
    ]
    previous_json = derived_dir / "models_20260101_000000.json"
    previous_json.write_text(json.dumps(previous_rows), encoding="utf-8")
    (derived_dir / "models_latest.json").symlink_to(previous_json.name)

    current_records = [
        {
            "model_id": "openai/gpt-5.5-pro",
            "author": "openai",
            "slug": "gpt-5.5-pro",
            "vendor_name": "OpenAI",
            "name": "OpenAI: GPT-5.5 Pro",
            "context_length": 1050000,
            "max_completion_tokens": 128000,
            "input_price_usd_per_1m": 30.0,
            "output_price_usd_per_1m": 180.0,
            "supports_reasoning": True,
            "supports_tools": True,
            "supports_vision": True,
            "fetched_at": "2026-01-02T03:04:05Z",
            "canonical_slug": "openai/gpt-5.5-pro-20260423",
        }
    ]
    (norm_dir / "20260102_030405_models.json").write_text(
        json.dumps(current_records), encoding="utf-8"
    )
    monkeypatch.setattr(derive_script, "NORM_DIR", norm_dir)
    monkeypatch.setattr(derive_script, "DERIVED_DIR", derived_dir)
    monkeypatch.setattr(
        derive_script,
        "fetch_benchmark_details",
        lambda model_id, canonical_slug=None: {
            "indices": {
                "intelligence_index": None,
                "coding_index": None,
                "agentic_index": None,
            },
            "heuristic_openrouter_slug": None,
            "permaslug": "openai/gpt-5.5-pro-20260423",
            "query_slug": canonical_slug or model_id,
        },
    )

    derive_script.main()

    latest = json.loads((derived_dir / "models_latest.json").read_text(encoding="utf-8"))
    row = latest[0]
    assert row["model_id"] == "openai/gpt-5.5-pro"
    assert row["intelligence_index"] == 62.0
    assert row["coding_index"] == 58.0
    assert row["agentic_index"] == 75.0
