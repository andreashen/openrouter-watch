"""Mapping uniqueness plus group identity evidence."""

from __future__ import annotations

import json
from pathlib import Path

from openrouter_watch.aa_mapping import validate_mapping

ROOT = Path(__file__).resolve().parents[1]
AA = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
BB = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def _rule(model_id: str = "anthropic/claude-sonnet-4.6", **overrides: object) -> dict:
    rule = {
        "openrouter_model_id": model_id,
        "aa_model_id": AA,
        "aa_slug": "claude-sonnet-4-6",
        "match": "exact_slug",
    }
    rule.update(overrides)
    return rule


def _member(model_id: str, kind: str = "manual_override") -> dict:
    return {
        "openrouter_model_id": model_id,
        "kind": kind,
        "ref": f"https://openrouter.ai/{model_id}",
        "note": f"{model_id} is the same model as the AA slug on this group",
        **({"observed": model_id} if kind == "openrouter_api_id" else {}),
    }


def _group(member_ids: list[str] | None = None, **overrides: object) -> dict:
    member_ids = member_ids or ["openai/gpt-4o", "openai/gpt-4o:free"]
    group = {
        "group": "gpt-4o-family",
        "aa_model_id": BB,
        "aa_slug": "gpt-4o",
        "match": "manual_override",
        "openrouter_model_ids": member_ids,
        "evidence": {
            "mode": "per_member",
            "items": [_member(model_id) for model_id in member_ids],
        },
    }
    group.update(overrides)
    return group


def _mapping(rules: list[dict] | None = None, groups: list[dict] | None = None) -> dict:
    return {"schema_version": 1, "rules": rules or [], "one_to_many": groups or []}


def _snapshot(models: list[dict] | None = None) -> dict:
    return {
        "models": models
        or [
            {"id": AA, "slug": "claude-sonnet-4-6"},
            {"id": BB, "slug": "gpt-4o", "openrouter_api_id": "openai/gpt-4o"},
        ]
    }


def test_xor_rejects_rule_and_group_overlap() -> None:
    result = validate_mapping(
        _mapping(
            [_rule("openai/gpt-4o", aa_model_id=BB, aa_slug="gpt-4o")],
            [_group()],
        )
    )
    assert "V-XOR" in result.codes
    assert result.edges == []


def test_duplicate_rule_and_overlapping_groups_fail() -> None:
    assert "V-RULE-UNIQ" in validate_mapping(_mapping([_rule(), _rule()])).codes
    shared = _group()
    other = _group(["openai/gpt-4o", "openai/gpt-4o-mini"], group="other-family")
    assert "V-GROUP-DISJOINT" in validate_mapping(_mapping(groups=[shared, other])).codes


def test_group_shape_failures() -> None:
    empty = _group([])
    empty["openrouter_model_ids"] = []
    empty["evidence"] = {"mode": "per_member", "items": []}
    assert "V-GROUP-NAME" in validate_mapping(_mapping(groups=[empty])).codes

    duplicated = _group(["openai/gpt-4o", "openai/gpt-4o"])
    assert "V-GROUP-MEM-UNIQ" in validate_mapping(_mapping(groups=[duplicated])).codes

    renamed = _group()
    twin = _group(["openai/gpt-4o-mini"], group="gpt-4o-family")
    assert "V-GROUP-NAME" in validate_mapping(_mapping(groups=[renamed, twin])).codes


def test_legal_rule_and_group_each_emit_one_edge_per_id() -> None:
    result = validate_mapping(_mapping([_rule()], [_group()]), _snapshot())
    assert result.ok
    assert len(result.edges) == 3
    grouped = [edge for edge in result.edges if edge.source == "group"]
    assert {edge.openrouter_model_id for edge in grouped} == {
        "openai/gpt-4o",
        "openai/gpt-4o:free",
    }
    assert {edge.aa_model_id for edge in grouped} == {BB}


def test_rule_manual_override_does_not_need_group_evidence_fields() -> None:
    result = validate_mapping(_mapping([_rule(match="manual_override")]))
    assert result.ok
    assert len(result.edges) == 1


def test_live_uuid_and_slug_without_evidence_still_fail() -> None:
    group = _group()
    del group["evidence"]
    result = validate_mapping(_mapping(groups=[group]), _snapshot())
    assert not result.ok
    assert "V-GROUP-EVIDENCE" in result.codes
    assert "V-UUID-LIVE" not in result.codes
    assert "V-SLUG" not in result.codes
    assert result.edges == []


def test_evidence_that_skips_a_member_fails_even_when_slug_matches() -> None:
    group = _group()
    group["evidence"]["items"] = [_member("openai/gpt-4o")]
    result = validate_mapping(_mapping(groups=[group]), _snapshot())
    assert "V-GROUP-COVER" in result.codes
    assert "V-SLUG" not in result.codes
    assert result.edges == []


def test_exact_slug_is_not_a_group_identity() -> None:
    group = _group(match="exact_slug")
    result = validate_mapping(_mapping(groups=[group]))
    assert "V-GROUP-MATCH" in result.codes


def test_shared_evidence_covers_every_member() -> None:
    group = _group()
    group["evidence"] = {
        "mode": "shared",
        "item": {
            "kind": "canonical_identity",
            "ref": "https://openrouter.ai/openai/gpt-4o",
            "note": "OpenRouter lists both ids as endpoints of gpt-4o",
            "covers": "all_members",
        },
    }
    group["match"] = "canonical_identity"
    result = validate_mapping(_mapping(groups=[group]), _snapshot())
    assert result.ok
    assert len(result.edges) == 2


def test_shared_openrouter_api_id_cannot_cover_a_family() -> None:
    group = _group(match="openrouter_api_id")
    group["evidence"] = {
        "mode": "shared",
        "item": {
            "kind": "openrouter_api_id",
            "ref": "pro-field:openrouter_api_id",
            "note": "Pro field cites one id only",
            "covers": "all_members",
            "observed": "openai/gpt-4o",
        },
    }
    assert "V-GROUP-EVIDENCE" in validate_mapping(_mapping(groups=[group])).codes


def test_snapshot_openrouter_api_id_must_match_the_cited_member() -> None:
    group = _group(
        ["openai/gpt-4o", "openai/gpt-4o:free"],
        match="openrouter_api_id",
    )
    group["evidence"]["items"] = [
        _member("openai/gpt-4o", "openrouter_api_id"),
        _member("openai/gpt-4o:free", "canonical_identity"),
    ]
    missing_field = validate_mapping(
        _mapping(groups=[group]),
        {"models": [{"id": BB, "slug": "gpt-4o"}]},
    )
    assert "V-OR-API-ID" in missing_field.codes

    mismatched = validate_mapping(
        _mapping(groups=[group]),
        {"models": [{"id": BB, "slug": "gpt-4o", "openrouter_api_id": "openai/other"}]},
    )
    assert "V-OR-API-ID" in mismatched.codes

    matched = validate_mapping(_mapping(groups=[group]), _snapshot())
    assert matched.ok


def test_uuid_and_slug_drift_fail_g4() -> None:
    mapping = _mapping([_rule()])
    assert "V-UUID-LIVE" in validate_mapping(mapping, {"models": []}).codes
    drifted = validate_mapping(
        mapping,
        {"models": [{"id": AA, "slug": "renamed"}]},
    )
    assert "V-SLUG" in drifted.codes
    assert drifted.edges == []


def test_committed_mapping_file_is_valid_and_empty() -> None:
    mapping = json.loads((ROOT / "data/aa_join/mapping.json").read_text(encoding="utf-8"))
    result = validate_mapping(mapping)
    assert result.ok
    assert result.edges == []
