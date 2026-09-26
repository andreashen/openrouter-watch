"""Cutover gates. Public display and OpenRouter collection stay put until they pass."""

from __future__ import annotations

G0_FIELDS = ("date", "grantor", "tier", "expires")
SUCCESS_STREAK = 3


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def g0_problems(record: object) -> list[str]:
    """A missing or incomplete grant is not a pass. Pricing-page tier text is not a record."""
    if record is None:
        return ["g0_missing"]
    if not isinstance(record, dict):
        return ["g0_shape"]
    problems: list[str] = []
    for field in G0_FIELDS:
        if not _nonempty(record.get(field)):
            problems.append(field)
    scope = record.get("scope")
    if not isinstance(scope, dict):
        problems.append("scope")
    else:
        if scope.get("page") is not True:
            problems.append("scope_page")
        if scope.get("json") is not True:
            problems.append("scope_json")
        if not isinstance(scope.get("redistributable"), bool):
            problems.append("scope_redistributable")
    return problems


def g0_ok(record: object) -> bool:
    return not g0_problems(record)


def cutover_allowed(
    *,
    g0_record: object,
    consecutive_successes: int,
    page_failures: list[str],
    g3_ok: bool,
    g4_ok: bool,
    g5_ok: bool,
    sit_passed: bool,
) -> bool:
    """G0–G6. Any false keeps the public page on OpenRouter scores."""
    return (
        g0_ok(g0_record)
        and consecutive_successes >= SUCCESS_STREAK
        and not page_failures
        and g3_ok
        and g4_ok
        and g5_ok
        and sit_passed
    )


def stop_collection_allowed(*, cutover_allowed: bool, refresh_verified: bool) -> bool:
    """Stop OpenRouter benchmark extraction only after cutover and one verified refresh."""
    return cutover_allowed and refresh_verified


def effective_display_source(publication: dict, *, cutover_allowed: bool) -> str:
    requested = publication.get("public_display_source")
    if requested == "artificial_analysis_api" and cutover_allowed:
        return "artificial_analysis_api"
    return "openrouter"


def effective_collect_openrouter_benchmark(
    publication: dict,
    *,
    cutover_allowed: bool,
    refresh_verified: bool,
) -> bool:
    """Fail closed: a premature stop request still collects."""
    wants_stop = publication.get("collect_openrouter_benchmark") is False
    if wants_stop and stop_collection_allowed(
        cutover_allowed=cutover_allowed,
        refresh_verified=refresh_verified,
    ):
        return False
    return True


def select_public_benchmark_rows(
    openrouter_rows: list[dict],
    aa_rows: list[dict],
    *,
    cutover_allowed: bool,
) -> list[dict]:
    """Public rows. Without cutover the OpenRouter rows are returned unchanged."""
    if cutover_allowed:
        return aa_rows
    return openrouter_rows


def publication_problems(
    publication: dict,
    *,
    cutover_allowed: bool,
    refresh_verified: bool,
) -> list[str]:
    problems: list[str] = []
    requested = publication.get("public_display_source")
    if requested == "artificial_analysis_api" and not cutover_allowed:
        problems.append("public_display_blocked")
    if publication.get("collect_openrouter_benchmark") is False and not stop_collection_allowed(
        cutover_allowed=cutover_allowed,
        refresh_verified=refresh_verified,
    ):
        problems.append("stop_collection_blocked")
    return problems


def repo_publication_is_held(publication: dict) -> list[str]:
    """The committed switch stays off. A later grant does not flip it by editing nothing else."""
    problems: list[str] = []
    if publication.get("public_display_source") != "openrouter":
        problems.append("public_display_source")
    if publication.get("collect_openrouter_benchmark") is not True:
        problems.append("collect_openrouter_benchmark")
    return problems
