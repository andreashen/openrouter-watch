"""Coverage, QA sample, and non-binding slug suggestions for the AA join."""

from __future__ import annotations

from .aa_mapping import Edge
from .aa_snapshot import BENCHMARK_FIELDS, scores_from_snapshot

COVERAGE_THRESHOLD = 0.90


def denominator_rows(rows: list[dict]) -> list[dict]:
    """Rows that currently claim at least one OpenRouter-transcribed AA score."""
    selected: list[dict] = []
    for row in rows:
        if row.get("officially_removed") or row.get("is_pointer"):
            continue
        if any(row.get(field) is not None for field in BENCHMARK_FIELDS):
            selected.append(row)
    return selected


def top_intelligence_ids(rows: list[dict], limit: int = 5) -> list[str]:
    scored = [
        row
        for row in denominator_rows(rows)
        if isinstance(row.get("intelligence_index"), (int, float))
        and not isinstance(row.get("intelligence_index"), bool)
    ]
    scored.sort(key=lambda row: (-float(row["intelligence_index"]), row["model_id"]))
    return [row["model_id"] for row in scored[:limit]]


def coverage(rows: list[dict], edges: list[Edge], snapshot: dict) -> dict:
    """G4 ratio. D == 0 is a failure. Conflicts are the caller's mapping errors."""
    by_or = {edge.openrouter_model_id: edge for edge in edges}
    base = denominator_rows(rows)
    denominator = len(base)
    numerator = 0
    for row in base:
        edge = by_or.get(row["model_id"])
        if edge is None:
            continue
        scores = scores_from_snapshot(snapshot, edge.aa_model_id)
        if any(scores[field] is not None for field in BENCHMARK_FIELDS):
            numerator += 1
    ratio = None if denominator == 0 else numerator / denominator
    return {
        "denominator": denominator,
        "numerator": numerator,
        "ratio": ratio,
        "ok": ratio is not None and ratio >= COVERAGE_THRESHOLD,
    }


def qa_sample_problems(sample: dict, rows: list[dict]) -> list[str]:
    """Structural G4 sample rule. The id list itself is data, not a frozen RFC name list."""
    problems: list[str] = []
    ids = sample.get("openrouter_model_ids") if isinstance(sample, dict) else None
    if not isinstance(ids, list) or any(not isinstance(item, str) or not item for item in ids):
        return ["sample_ids"]
    if len(ids) < 15:
        problems.append("sample_size")
    if len(ids) != len(set(ids)):
        problems.append("sample_duplicate")
    authors = {model_id.split("/", 1)[0] for model_id in ids if "/" in model_id}
    if len(authors) < 5:
        problems.append("sample_authors")
    missing = [model_id for model_id in top_intelligence_ids(rows) if model_id not in set(ids)]
    if missing:
        problems.append("sample_top_intelligence")
    return problems


def normalize_slug(slug: str) -> str:
    return slug.strip().lower().replace("_", "-")


def propose_exact_slug(openrouter_model_id: str, slug: str, aa_models: list[dict]) -> dict | None:
    """Suggest an exact_slug rule only when one AA slug normalizes to the same value.

    Zero or several matches produce no suggestion. Suggestions are not mapping
    entries and must not be shown as scores.
    """
    target = normalize_slug(slug)
    if not target or not openrouter_model_id:
        return None
    matches = [
        model
        for model in aa_models
        if isinstance(model, dict)
        and isinstance(model.get("slug"), str)
        and normalize_slug(model["slug"]) == target
    ]
    if len(matches) != 1:
        return None
    match = matches[0]
    return {
        "openrouter_model_id": openrouter_model_id,
        "aa_model_id": match.get("id"),
        "aa_slug": match.get("slug"),
        "match": "exact_slug",
        "status": "candidate",
    }


def annotate_internal_scores(rows: list[dict], edges: list[Edge], snapshot: dict) -> list[dict]:
    """Attach AA scores for an internal report. Pointer rows do not inherit a target."""
    by_or = {edge.openrouter_model_id: edge for edge in edges}
    snapshot_id = snapshot.get("aa_snapshot_id")
    annotated: list[dict] = []
    for row in rows:
        edge = None if row.get("is_pointer") else by_or.get(row.get("model_id"))
        if edge is None:
            scores = {field: None for field in BENCHMARK_FIELDS}
            aa_model_id = None
            aa_slug = None
        else:
            scores = scores_from_snapshot(snapshot, edge.aa_model_id)
            aa_model_id = edge.aa_model_id
            aa_slug = edge.aa_slug
        annotated.append(
            {
                "model_id": row.get("model_id"),
                "display_aa_snapshot_id": snapshot_id,
                "aa_model_id": aa_model_id,
                "aa_slug": aa_slug,
                **scores,
            }
        )
    return annotated
