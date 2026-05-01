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
    monkeypatch.setattr(derive_script, "fetch_benchmark", lambda model_id: None)

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
