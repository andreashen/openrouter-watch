"""Cutover gates. Public display and OpenRouter collection stay put until they pass."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from urllib.parse import urlparse

G0_FIELDS = ("date", "grantor", "tier", "expires")
SUCCESS_STREAK = 3
_SELF_SERVE_TIERS = frozenset({"free", "pro"})
_INSTRUMENTS = frozenset({"written_authorization", "commercial_contract"})
_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_RESERVED_HOSTS = frozenset(
    {"example", "example.com", "example.org", "example.net", "example.edu", "localhost"}
)


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parse_day(value: object) -> date | None:
    if not isinstance(value, str) or not _DAY.fullmatch(value):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _reviewable_ref(value: object) -> bool:
    """Field shape only. A human still has to read the document this locator names."""
    if not isinstance(value, str):
        return False
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme not in {"https", "http"} or not host or "." not in host:
        return False
    if host in _RESERVED_HOSTS or host.endswith((".example", ".invalid", ".test", ".localhost")):
        return False
    return parsed.path not in {"", "/"}


def _authorization_basis(record: dict) -> bool:
    instrument = record.get("instrument")
    tier = record.get("tier")
    tier_name = tier.strip().lower() if isinstance(tier, str) else ""
    if instrument not in _INSTRUMENTS or not _reviewable_ref(record.get("authorization_ref")):
        return False
    if not _nonempty(record.get("verified_by")):
        return False
    if tier_name in _SELF_SERVE_TIERS and instrument != "written_authorization":
        return False
    return True


def g0_problems(record: object, *, today: date | None = None) -> list[str]:
    """A missing or incomplete grant is not a pass. Pricing-page tier text is not a record.

    Every tier, including Commercial, needs a reviewable document or contract
    locator and the name of the person who checked that it covers the public
    page and JSON. ``redistributable`` must be true. An expiry before ``today`` fails.
    """
    if record is None:
        return ["g0_missing"]
    if not isinstance(record, dict):
        return ["g0_shape"]
    problems: list[str] = []
    for field in G0_FIELDS:
        if not _nonempty(record.get(field)):
            problems.append(field)
    if "date" not in problems and _parse_day(record.get("date")) is None:
        problems.append("date")
    if "expires" not in problems:
        expires = _parse_day(record.get("expires"))
        if expires is None:
            problems.append("expires")
        elif expires < (today or datetime.now(timezone.utc).date()):
            problems.append("expires_elapsed")
    if not _authorization_basis(record):
        problems.append("authorization_basis")
    scope = record.get("scope")
    if not isinstance(scope, dict):
        problems.append("scope")
    else:
        if scope.get("page") is not True:
            problems.append("scope_page")
        if scope.get("json") is not True:
            problems.append("scope_json")
        if scope.get("redistributable") is not True:
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
