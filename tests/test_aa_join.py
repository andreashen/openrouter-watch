"""Coverage denominator and slug suggestions that never become edges by themselves."""

from __future__ import annotations

from openrouter_watch.aa_join import (
    annotate_internal_scores,
    coverage,
    normalize_slug,
    propose_exact_slug,
    qa_sample_problems,
)
from openrouter_watch.aa_mapping import Edge

AA = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def _row(
    model_id: str,
    intelligence: float | None,
    *,
    removed: bool = False,
    pointer: bool = False,
) -> dict:
    author = model_id.split("/", 1)[0]
    return {
        "model_id": model_id,
        "author": author,
        "intelligence_index": intelligence,
        "coding_index": None,
        "agentic_index": None,
        "officially_removed": removed,
        "is_pointer": pointer,
    }


def test_coverage_uses_active_non_pointer_rows_and_rejects_empty_denominator() -> None:
    rows = [
        _row("openai/a", 10),
        _row("openai/b", 20),
        _row("openai/gone", 30, removed=True),
        _row("openai/pointer", 40, pointer=True),
        _row("openai/blank", None),
    ]
    snapshot = {
        "aa_snapshot_id": "snap",
        "models": [
            {
                "id": AA,
                "intelligence_index": 11,
                "coding_index": None,
                "agentic_index": None,
            }
        ],
    }
    edges = [Edge("openai/a", AA, "a", "rule")]
    stats = coverage(rows, edges, snapshot)
    assert stats["denominator"] == 2
    assert stats["numerator"] == 1
    assert stats["ratio"] == 0.5
    assert not stats["ok"]
    assert not coverage([_row("openai/blank", None)], [], snapshot)["ok"]


def test_pointer_row_does_not_inherit_a_target_score() -> None:
    rows = [_row("openai/gpt-4o", 10, pointer=True)]
    snapshot = {
        "aa_snapshot_id": "snap",
        "models": [{"id": AA, "intelligence_index": 80, "coding_index": 70, "agentic_index": 60}],
    }
    edges = [Edge("openai/gpt-4o", AA, "gpt-4o", "rule")]
    annotated = annotate_internal_scores(rows, edges, snapshot)
    assert annotated[0]["intelligence_index"] is None
    assert annotated[0]["aa_model_id"] is None


def test_slug_suggestion_requires_exactly_one_aa_candidate() -> None:
    models = [
        {"id": AA, "slug": "gpt-4o"},
        {"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "slug": "gpt-4o-mini"},
    ]
    one = propose_exact_slug("openai/gpt-4o", "gpt-4o", models)
    assert one is not None
    assert one["status"] == "candidate"
    assert one["match"] == "exact_slug"
    assert propose_exact_slug("openai/gpt-4o:free", "gpt-4o:free", models) is None
    ambiguous = [
        {"id": AA, "slug": "gpt-4o"},
        {"id": "cccccccc-cccc-cccc-cccc-cccccccccccc", "slug": "GPT_4o"},
    ]
    assert propose_exact_slug("openai/gpt-4o", "gpt-4o", ambiguous) is None
    assert normalize_slug("GPT_4o") == "gpt-4o"


def test_sample_rule_rejects_a_set_that_misses_the_top_scores() -> None:
    rows = [
        _row(f"vendor-{index}/m{index}", float(index))
        for index in range(1, 8)
    ]
    sample = {"openrouter_model_ids": [row["model_id"] for row in rows]}
    assert "sample_size" in qa_sample_problems(sample, rows)
    wide = [_row(f"author{index % 6}/model-{index}", float(20 - index)) for index in range(16)]
    ids = [row["model_id"] for row in wide[5:]]
    assert "sample_top_intelligence" in qa_sample_problems({"openrouter_model_ids": ids}, wide)
