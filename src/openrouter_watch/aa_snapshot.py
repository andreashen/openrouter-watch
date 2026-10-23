"""Immutable AA score snapshots. Scores never move between snapshots."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .aa_fetch import INDEX_FIELDS, page_failures
from .aa_version import canonical_major_minor

BENCHMARK_FIELDS = ("intelligence_index", "coding_index", "agentic_index")


def _snapshot_id(fetched_at: str, version: str) -> str:
    compact = fetched_at.replace("-", "").replace(":", "")
    return f"{compact}_{version}"


def build_snapshot(pages: list[dict], *, fetched_at: str) -> dict | None:
    """Build one snapshot from a capture that already passed F-*. Otherwise return None."""
    if page_failures(pages):
        return None
    version = canonical_major_minor(pages[0].get("intelligence_index_version"))
    if version is None:
        return None
    models: list[dict] = []
    for page in pages:
        for raw in page.get("models") or []:
            evaluations = raw.get("evaluations") or {}
            model = {
                "id": raw.get("id"),
                "slug": raw.get("slug"),
            }
            for local_name, wire_name in INDEX_FIELDS.items():
                model[local_name] = evaluations.get(wire_name)
            if "openrouter_api_id" in raw:
                model["openrouter_api_id"] = raw.get("openrouter_api_id")
            models.append(model)
    return {
        "aa_snapshot_id": _snapshot_id(fetched_at, version),
        "aa_fetched_at": fetched_at,
        "intelligence_index_version": version,
        "aa_tier": pages[0].get("tier"),
        "pages_fetched": len(pages),
        "total_pages": pages[0].get("total_pages"),
        "models": models,
    }


def scores_from_snapshot(snapshot: dict, aa_model_id: str) -> dict[str, float | None]:
    """Read the three indices from this snapshot only.

    A null stays null. There is no previous-snapshot argument, so a caller
    cannot backfill one field from an older capture.
    """
    found: dict | None = None
    for model in snapshot.get("models") or []:
        if isinstance(model, dict) and model.get("id") == aa_model_id:
            found = model
            break
    if found is None:
        return {name: None for name in BENCHMARK_FIELDS}
    return {name: found.get(name) for name in BENCHMARK_FIELDS}


def _safe_snapshot_id(snapshot_id: object) -> str:
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("snapshot is missing aa_snapshot_id")
    if any(char in snapshot_id for char in "/\\") or snapshot_id in {".", ".."}:
        raise ValueError("aa_snapshot_id is not a safe file name")
    return snapshot_id


def store_snapshot(out_dir: Path, snapshot: dict) -> Path:
    """Write one immutable snapshot file, then point latest at it.

    An existing file with the same id and different bytes is left untouched,
    and the latest pointer is not moved. Identical bytes are not rewritten.
    """
    snapshot_id = _safe_snapshot_id(snapshot.get("aa_snapshot_id"))
    folder = out_dir / "snapshots"
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{snapshot_id}.json"
    payload = json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"
    if dest.exists():
        if dest.read_text(encoding="utf-8") != payload:
            raise FileExistsError(snapshot_id)
    else:
        temporary = folder / f".{snapshot_id}.json.tmp"
        temporary.write_text(payload, encoding="utf-8")
        try:
            os.link(temporary, dest)
        except FileExistsError:
            temporary.unlink(missing_ok=True)
            if dest.read_text(encoding="utf-8") != payload:
                raise FileExistsError(snapshot_id) from None
        else:
            temporary.unlink(missing_ok=True)
    pointer = {
        "aa_snapshot_id": snapshot_id,
        "snapshot_file": f"snapshots/{snapshot_id}.json",
    }
    pointer_tmp = out_dir / "latest_snapshot.json.tmp"
    pointer_tmp.write_text(json.dumps(pointer, indent=2) + "\n", encoding="utf-8")
    os.replace(pointer_tmp, out_dir / "latest_snapshot.json")
    return dest


def display_aa_snapshot_id(snapshot: dict) -> str:
    """The single snapshot id a public row would cite after cutover."""
    snapshot_id = snapshot.get("aa_snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("snapshot is missing aa_snapshot_id")
    return snapshot_id
