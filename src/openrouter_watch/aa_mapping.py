"""Frozen mapping file checks for OpenRouter ids joined to AA models.

``rules`` stay one-to-one. ``one_to_many`` is the only many-to-one channel.
A group is not accepted just because its members are listed: every member
needs reviewable identity evidence, at the same strength as a
``rules[].manual_override`` PR basis (a locator plus a confirmation note).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
RULE_MATCHES = frozenset({"exact_slug", "manual_override", "openrouter_api_id"})
GROUP_MATCHES = frozenset({"manual_override", "openrouter_api_id", "canonical_identity"})
EVIDENCE_KINDS = GROUP_MATCHES
_REF_PREFIXES = ("https://", "http://", "snapshot:")
_PRO_FIELD_REF = "pro-field:openrouter_api_id"


@dataclass(frozen=True)
class MappingError:
    code: str
    message: str


@dataclass(frozen=True)
class Edge:
    openrouter_model_id: str
    aa_model_id: str
    aa_slug: str
    source: str
    group: str | None = None


@dataclass
class MappingResult:
    ok: bool
    errors: list[MappingError] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    @property
    def codes(self) -> list[str]:
        return [error.code for error in self.errors]


def _nonempty(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _valid_ref(value: object) -> bool:
    text = _nonempty(value)
    if text is None:
        return False
    if text == _PRO_FIELD_REF:
        return True
    return text.startswith(_REF_PREFIXES) and len(text) > len("snapshot:")


def _add(errors: list[MappingError], code: str, message: str) -> None:
    errors.append(MappingError(code, message))


def _snapshot_index(snapshot: dict | None) -> dict[str, dict] | None:
    if snapshot is None:
        return None
    models = snapshot.get("models")
    if not isinstance(models, list):
        return {}
    index: dict[str, dict] = {}
    for model in models:
        if isinstance(model, dict) and isinstance(model.get("id"), str):
            index[model["id"]] = model
    return index


def _check_evidence_item(
    errors: list[MappingError],
    item: object,
    *,
    require_member_id: bool,
) -> dict | None:
    if not isinstance(item, dict):
        _add(errors, "V-GROUP-EVIDENCE", "evidence item must be an object")
        return None
    kind = item.get("kind")
    if kind not in EVIDENCE_KINDS:
        _add(
            errors,
            "V-GROUP-EVIDENCE",
            "evidence.kind must be manual_override, openrouter_api_id, or canonical_identity",
        )
    if not _valid_ref(item.get("ref")):
        _add(errors, "V-GROUP-EVIDENCE", "evidence.ref is missing or not a locator")
    if _nonempty(item.get("note")) is None:
        _add(errors, "V-GROUP-EVIDENCE", "evidence.note must be a non-empty confirmation")
    member_id = _nonempty(item.get("openrouter_model_id")) if require_member_id else None
    if require_member_id and member_id is None:
        _add(errors, "V-GROUP-EVIDENCE", "per-member evidence is missing openrouter_model_id")
    if kind == "openrouter_api_id":
        observed = _nonempty(item.get("observed"))
        if observed is None or (member_id is not None and observed != member_id):
            _add(
                errors,
                "V-OR-API-ID",
                "openrouter_api_id evidence needs observed equal to that member id",
            )
    return item


def _check_group_evidence(
    errors: list[MappingError],
    group: dict,
    member_ids: list[str],
) -> None:
    match = group.get("match")
    if match not in GROUP_MATCHES:
        _add(
            errors,
            "V-GROUP-MATCH",
            "group.match must be manual_override, openrouter_api_id, or canonical_identity",
        )
    evidence = group.get("evidence")
    if not isinstance(evidence, dict):
        _add(errors, "V-GROUP-EVIDENCE", "group.evidence is required")
        return
    mode = evidence.get("mode")
    used_kinds: list[str] = []
    api_id_items = 0
    if mode == "shared":
        item = evidence.get("item")
        if not isinstance(item, dict) or item.get("covers") != "all_members":
            _add(errors, "V-GROUP-COVER", "shared evidence must set covers to all_members")
        checked = _check_evidence_item(errors, item, require_member_id=False)
        if isinstance(checked, dict):
            kind = checked.get("kind")
            if isinstance(kind, str) and kind in EVIDENCE_KINDS:
                used_kinds.append(kind)
            if kind == "openrouter_api_id":
                _add(
                    errors,
                    "V-GROUP-EVIDENCE",
                    "shared evidence cannot use openrouter_api_id for every member",
                )
    elif mode == "per_member":
        items = evidence.get("items")
        if not isinstance(items, list) or not items:
            _add(errors, "V-GROUP-EVIDENCE", "per_member evidence items must be a non-empty list")
            items = []
        seen: list[str] = []
        for item in items:
            checked = _check_evidence_item(errors, item, require_member_id=True)
            if not isinstance(checked, dict):
                continue
            member_id = _nonempty(checked.get("openrouter_model_id"))
            if member_id is not None:
                seen.append(member_id)
            kind = checked.get("kind")
            if isinstance(kind, str) and kind in EVIDENCE_KINDS:
                used_kinds.append(kind)
            if kind == "openrouter_api_id":
                api_id_items += 1
        if sorted(seen) != sorted(member_ids):
            _add(
                errors,
                "V-GROUP-COVER",
                "per_member evidence must cover each group member exactly once",
            )
    else:
        _add(errors, "V-GROUP-EVIDENCE", "evidence.mode must be per_member or shared")
    if api_id_items > 1:
        _add(errors, "V-OR-API-ID", "a group may cite openrouter_api_id for at most one member")
    if match in GROUP_MATCHES and match not in used_kinds:
        _add(errors, "V-GROUP-MATCH", "group.match must be the kind used by the evidence")


def _check_live_api_id(
    errors: list[MappingError],
    group: dict,
    models_by_id: dict[str, dict],
) -> None:
    evidence = group.get("evidence")
    if not isinstance(evidence, dict) or evidence.get("mode") != "per_member":
        return
    items = evidence.get("items")
    if not isinstance(items, list):
        return
    aa_model_id = group.get("aa_model_id")
    model = models_by_id.get(aa_model_id) if isinstance(aa_model_id, str) else None
    for item in items:
        if not isinstance(item, dict) or item.get("kind") != "openrouter_api_id":
            continue
        member_id = _nonempty(item.get("openrouter_model_id"))
        if model is None:
            _add(errors, "V-OR-API-ID", "openrouter_api_id evidence has no snapshot model to check")
            continue
        if "openrouter_api_id" not in model:
            _add(
                errors,
                "V-OR-API-ID",
                "snapshot is missing openrouter_api_id; this evidence kind cannot pass",
            )
            continue
        if model.get("openrouter_api_id") != member_id:
            _add(errors, "V-OR-API-ID", "snapshot openrouter_api_id does not equal the member id")


def validate_mapping(mapping: object, snapshot: dict | None = None) -> MappingResult:
    """Validate a mapping document. Any error rejects the file and yields no edges."""
    errors: list[MappingError] = []
    if not isinstance(mapping, dict):
        return MappingResult(False, [MappingError("V-SCHEMA", "mapping must be an object")])
    if mapping.get("schema_version") != 1:
        _add(errors, "V-SCHEMA", "schema_version must be 1")

    rules = mapping.get("rules")
    groups = mapping.get("one_to_many")
    if not isinstance(rules, list):
        _add(errors, "V-ID", "rules must be a list")
        rules = []
    if not isinstance(groups, list):
        _add(errors, "V-ID", "one_to_many must be a list")
        groups = []

    rule_ids: list[str] = []
    tentative: list[Edge] = []
    for rule in rules:
        if not isinstance(rule, dict):
            _add(errors, "V-ID", "rule must be an object")
            continue
        if "one_to_many_group" in rule:
            _add(errors, "V-XOR", "rules must not carry one_to_many_group")
        or_id = _nonempty(rule.get("openrouter_model_id"))
        aa_id = _nonempty(rule.get("aa_model_id"))
        slug = _nonempty(rule.get("aa_slug"))
        if or_id is None or slug is None or aa_id is None or not UUID_RE.fullmatch(aa_id):
            _add(errors, "V-ID", "rule is missing a UUID aa_model_id or a non-empty id/slug")
            if or_id is not None:
                rule_ids.append(or_id)
            continue
        if rule.get("match") not in RULE_MATCHES:
            _add(errors, "V-MATCH", "rules[].match is not an allowed value")
        rule_ids.append(or_id)
        tentative.append(Edge(or_id, aa_id, slug, "rule"))

    if len(rule_ids) != len(set(rule_ids)):
        _add(errors, "V-RULE-UNIQ", "the same openrouter_model_id appears on more than one rule")

    group_names: list[str] = []
    membership: dict[str, str] = {}
    for group in groups:
        if not isinstance(group, dict):
            _add(errors, "V-ID", "group must be an object")
            continue
        name = _nonempty(group.get("group"))
        aa_id = _nonempty(group.get("aa_model_id"))
        slug = _nonempty(group.get("aa_slug"))
        members = group.get("openrouter_model_ids")
        if name is None or slug is None or aa_id is None or not UUID_RE.fullmatch(aa_id):
            _add(errors, "V-ID", "group is missing a UUID, slug, or name")
        members_ok = isinstance(members, list) and bool(members)
        members_ok = members_ok and all(_nonempty(member) is not None for member in members)
        if not members_ok:
            _add(errors, "V-GROUP-NAME", "group name is missing or the member list is empty")
            member_ids: list[str] = []
        else:
            member_ids = [str(member).strip() for member in members]
        if name is not None:
            group_names.append(name)
        if len(member_ids) != len(set(member_ids)):
            _add(errors, "V-GROUP-MEM-UNIQ", f"group {name or ''} repeats a member id")
        for member_id in member_ids:
            if member_id in membership:
                _add(errors, "V-GROUP-DISJOINT", f"{member_id} is in more than one group")
            else:
                membership[member_id] = name or ""
            if member_id in rule_ids:
                _add(errors, "V-XOR", f"{member_id} is both a rule and a group member")
            uuid_ok = isinstance(aa_id, str) and UUID_RE.fullmatch(aa_id) is not None
            if name is not None and slug is not None and uuid_ok:
                tentative.append(Edge(member_id, aa_id, slug, "group", name))
        _check_group_evidence(errors, group, member_ids)

    if len(group_names) != len(set(group_names)):
        _add(errors, "V-GROUP-NAME", "two groups share a name")

    by_or: dict[str, set[tuple[str, str]]] = {}
    edge_counts: dict[str, int] = {}
    for edge in tentative:
        by_or.setdefault(edge.openrouter_model_id, set()).add((edge.aa_model_id, edge.aa_slug))
        edge_counts[edge.openrouter_model_id] = edge_counts.get(edge.openrouter_model_id, 0) + 1
    listed_ids = set(rule_ids) | set(membership)
    for or_id in listed_ids:
        targets = by_or.get(or_id, set())
        if edge_counts.get(or_id, 0) != 1 or len(targets) != 1:
            _add(errors, "V-FLAT", f"{or_id} does not flatten to exactly one edge")

    models_by_id = _snapshot_index(snapshot)
    if models_by_id is not None:
        for edge in tentative:
            model = models_by_id.get(edge.aa_model_id)
            if model is None:
                _add(errors, "V-UUID-LIVE", f"{edge.aa_model_id} is not in the current snapshot")
                continue
            if model.get("slug") != edge.aa_slug:
                _add(errors, "V-SLUG", f"{edge.aa_model_id} slug drifted from {edge.aa_slug}")
        for group in groups:
            if isinstance(group, dict):
                _check_live_api_id(errors, group, models_by_id)

    if errors:
        return MappingResult(False, errors, [])
    return MappingResult(True, [], tentative)
