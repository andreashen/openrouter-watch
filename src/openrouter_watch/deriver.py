from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from .schema import NormalizedModel

_FIELDS = [
    "model_id",
    "author",
    "slug",
    "vendor_name",
    "name",
    "openrouter_model_url",
    "context_length",
    "max_completion_tokens",
    "input_price_usd_per_1m",
    "output_price_usd_per_1m",
    "supports_reasoning",
    "supports_tools",
    "supports_vision",
    "intelligence_index",
    "coding_index",
    "agentic_index",
    "officially_removed",
    "fetched_at",
    "updated_at",
    "is_pointer",
    "pointer_target_id",
    "pointer_kind",
]

BENCHMARK_FIELDS = ("intelligence_index", "coding_index", "agentic_index")
EXCLUDED_UPDATE_FIELDS = {
    "fetched_at",
    "updated_at",
    "is_pointer",
    "pointer_target_id",
    "pointer_kind",
}
_VERSION_TOKEN_RE = re.compile(r"(\d+(?:\.\d+)*)")


def _is_valid_benchmark(value: object) -> bool:
    return value is not None


def is_pointer_candidate(model_id: str) -> bool:
    """Return True when model_id looks like a rolling latest / tilde pointer."""
    if model_id.startswith("~"):
        return True
    slug = model_id.split("/", 1)[-1]
    return "-latest" in slug


def pointer_kind_for(model_id: str) -> str | None:
    if not is_pointer_candidate(model_id):
        return None
    if model_id.startswith("~"):
        return "tilde_latest"
    return "slug_latest"


def _url_path_slug(url: str | None) -> str | None:
    if not url:
        return None
    path = urlparse(url).path.strip("/")
    return path or None


def _version_numbers(model_id: str) -> tuple[tuple[int, ...], ...]:
    """Extract dotted version number tuples from a model slug."""
    slug = model_id.split("/", 1)[-1]
    parts = _VERSION_TOKEN_RE.findall(slug)
    if not parts:
        return ()
    return tuple(tuple(int(p) for p in part.split(".")) for part in parts)


def _family_prefix(model_id: str) -> str:
    """Strip tilde / -latest markers to get a family prefix for fuzzy matching."""
    author, _, slug = model_id.partition("/")
    author = author.lstrip("~")
    slug = slug or author
    if slug.endswith("-latest"):
        slug = slug[: -len("-latest")]
    slug = slug.removeprefix("~")
    return f"{author}/{slug}" if author and slug != author else slug


_SIMILARITY_FIELDS = (
    "context_length",
    "max_completion_tokens",
    "input_price_usd_per_1m",
    "output_price_usd_per_1m",
    "intelligence_index",
    "coding_index",
    "agentic_index",
)


def _field_similarity(pointer: dict, candidate: dict) -> tuple[int, float]:
    """Return (comparable_fields, negative_distance) — higher is better."""
    comparable = 0
    distance = 0.0
    for field in _SIMILARITY_FIELDS:
        left = pointer.get(field)
        right = candidate.get(field)
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            continue
        comparable += 1
        if left == 0 and right == 0:
            continue
        scale = max(abs(left), abs(right), 1.0)
        distance += abs(left - right) / scale
    return comparable, -distance


def _slug_noise_penalty(model_id: str) -> int:
    slug = model_id.split("/", 1)[-1].lower()
    penalty = 0
    for noise in (
        "preview",
        "image",
        "tts",
        "transcribe",
        "search",
        "customtools",
        "free",
        "fast",
        "multi-agent",
        "online",
        "extended",
    ):
        if noise in slug:
            penalty += 1
    if ":" in model_id:
        penalty += 1
    return penalty


def resolve_pointer_target(row: dict, index: dict[str, dict]) -> str | None:
    """Heuristically resolve the concrete model_id a pointer row refers to.

    Prefer openrouter_model_url canonical path when it differs from the pointer
    id and exists in the index; otherwise fuzzy-match same-author family and
    pick the best field-similarity / highest-version non-pointer candidate.
    """
    mid = row["model_id"]
    url_slug = _url_path_slug(row.get("openrouter_model_url"))
    pointer_slug = mid.split("/", 1)[-1]
    author = str(row.get("author") or mid.split("/", 1)[0]).lstrip("~")

    if url_slug and url_slug != mid.lstrip("~") and url_slug != pointer_slug:
        if "/" in url_slug:
            candidate = url_slug.lstrip("~")
        else:
            candidate = f"{author}/{url_slug}"
        if candidate in index and candidate != mid and not is_pointer_candidate(candidate):
            return candidate
        # URL may be a dated canonical slug that is not itself a model_id;
        # try matching other rows whose openrouter_model_url ends with it.
        for other_id, other in index.items():
            if other_id == mid or is_pointer_candidate(other_id):
                continue
            other_url = _url_path_slug(other.get("openrouter_model_url"))
            if other_url == url_slug or (other_url and other_url.endswith(url_slug)):
                return other_id

    family = _family_prefix(mid)
    family_author, _, family_slug = family.partition("/")
    family_tokens = [token for token in family_slug.split("-") if token and token != "latest"]
    # Single generic token (gpt / grok / kimi) is too broad for prefix matching;
    # fall back to same-author + field similarity.
    require_family_tokens = len(family_tokens) >= 2
    candidates: list[str] = []
    for other_id in index:
        if other_id == mid or is_pointer_candidate(other_id):
            continue
        other_author = other_id.split("/", 1)[0].lstrip("~")
        if family_author and other_author != family_author:
            continue
        other_slug = other_id.split("/", 1)[-1]
        if require_family_tokens:
            prefix_hit = (
                other_slug == family_slug
                or other_slug.startswith(f"{family_slug}-")
                or other_slug.startswith(f"{family_slug}.")
            )
            token_hit = all(
                token in other_slug.split("-") or f"-{token}-" in f"-{other_slug}-"
                for token in family_tokens
            )
            if not (prefix_hit or token_hit):
                continue
        candidates.append(other_id)

    if not candidates:
        return None

    def _rank(model_id: str) -> tuple:
        other = index[model_id]
        comparable, neg_distance = _field_similarity(row, other)
        noise = _slug_noise_penalty(model_id)
        versions = _version_numbers(model_id)
        if require_family_tokens:
            # Specific family (e.g. claude-opus): prefer highest version first,
            # then cleaner slug / closer fields.
            return (
                versions,
                -noise,
                comparable >= 2,
                neg_distance,
                model_id,
            )
        # Broad family (e.g. gpt / grok): field similarity is the main signal.
        return (
            comparable >= 2,
            comparable,
            neg_distance,
            -noise,
            versions,
            model_id,
        )

    candidates.sort(key=_rank)
    best = candidates[-1]
    comparable, _ = _field_similarity(row, index[best])
    # If family was broad and nothing is field-comparable, keep unresolved.
    if not require_family_tokens and comparable < 2:
        return None
    return best


def enrich_pointer_metadata(rows: list[dict]) -> list[dict]:
    """Attach is_pointer / pointer_target_id / pointer_kind to every derived row."""
    index = {row["model_id"]: row for row in rows}
    enriched: list[dict] = []
    for row in rows:
        out = dict(row)
        mid = out["model_id"]
        if is_pointer_candidate(mid):
            out["is_pointer"] = True
            out["pointer_kind"] = pointer_kind_for(mid)
            out["pointer_target_id"] = resolve_pointer_target(out, index)
        else:
            out["is_pointer"] = False
            out["pointer_kind"] = None
            out["pointer_target_id"] = None
        enriched.append(_normalize_row(out))
    return enriched


def to_row(model: NormalizedModel, benchmark: dict | None = None) -> dict:
    row = model.model_dump()
    if benchmark:
        row["intelligence_index"] = benchmark.get("intelligence_index")
        row["coding_index"] = benchmark.get("coding_index")
        row["agentic_index"] = benchmark.get("agentic_index")
    row["officially_removed"] = False
    row["updated_at"] = None
    row["is_pointer"] = False
    row["pointer_target_id"] = None
    row["pointer_kind"] = None
    return {k: row.get(k) for k in _FIELDS}


def merge_benchmark_fields(current: dict, previous: dict | None) -> dict:
    """Merge benchmark fields: new value wins; blank current inherits previous."""
    if previous is None:
        return current
    merged = dict(current)
    for field in BENCHMARK_FIELDS:
        current_val = merged.get(field)
        previous_val = previous.get(field)
        if _is_valid_benchmark(current_val):
            continue
        if _is_valid_benchmark(previous_val):
            merged[field] = previous_val
        else:
            merged[field] = None
    return merged


def load_previous_models(latest_path: Path | str) -> dict[str, dict]:
    """Load previous derived rows indexed by model_id; empty if no prior run."""
    latest_path = Path(latest_path)
    if not latest_path.exists():
        return {}
    with open(latest_path, encoding="utf-8") as f:
        rows = json.load(f)
    previous_map: dict[str, dict] = {}
    for row in rows:
        model_id = row["model_id"]
        if "officially_removed" not in row:
            row = {**row, "officially_removed": False}
        previous_map[model_id] = row
    return previous_map


def _normalize_row(row: dict) -> dict:
    normalized = {k: row.get(k) for k in _FIELDS}
    if normalized.get("is_pointer") is None:
        normalized["is_pointer"] = False
    if "pointer_target_id" not in row:
        normalized["pointer_target_id"] = None
    if "pointer_kind" not in row:
        normalized["pointer_kind"] = None
    return normalized


def _tracked_row_for_update(row: dict) -> dict:
    return {k: row.get(k) for k in _FIELDS if k not in EXCLUDED_UPDATE_FIELDS}


def _resolve_updated_at(current_row: dict, previous_row: dict | None, refreshed_at: str) -> str:
    if previous_row is None:
        return refreshed_at

    normalized_previous = _normalize_row(previous_row)
    if _tracked_row_for_update(current_row) != _tracked_row_for_update(normalized_previous):
        return refreshed_at

    return (
        normalized_previous.get("updated_at")
        or normalized_previous.get("fetched_at")
        or refreshed_at
    )


def merge_derived_rows(
    current_rows: list[dict], previous_map: dict[str, dict], refreshed_at: str
) -> list[dict]:
    """Union current and previous models with removal flags and benchmark backfill."""
    current_map = {row["model_id"]: row for row in current_rows}
    merged: list[dict] = []

    for model_id, current_row in current_map.items():
        previous_row = previous_map.get(model_id)
        row = _normalize_row(current_row)
        row["officially_removed"] = False
        row = merge_benchmark_fields(row, previous_row)
        row["updated_at"] = _resolve_updated_at(row, previous_row, refreshed_at)
        merged.append(row)

    for model_id, previous_row in previous_map.items():
        if model_id in current_map:
            continue
        row = _normalize_row(previous_row)
        row["officially_removed"] = True
        row["updated_at"] = _resolve_updated_at(row, previous_row, refreshed_at)
        merged.append(row)

    merged.sort(key=lambda row: (row["vendor_name"], row["model_id"]))
    return enrich_pointer_metadata(merged)


def write_csv(rows: list[dict], path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows: list[dict], path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
