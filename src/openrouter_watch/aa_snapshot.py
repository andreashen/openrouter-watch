"""Immutable AA score snapshots. Scores never move between snapshots."""

from __future__ import annotations

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


def display_aa_snapshot_id(snapshot: dict) -> str:
    """The single snapshot id a public row would cite after cutover."""
    snapshot_id = snapshot.get("aa_snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("snapshot is missing aa_snapshot_id")
    return snapshot_id
