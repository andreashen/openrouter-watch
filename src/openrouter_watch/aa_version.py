"""Canonical major.minor handling for the Artificial Analysis Intelligence Index."""

from __future__ import annotations

import math
import re

EVAL_PAGE_URL = "https://artificialanalysis.ai/evaluations/artificial-analysis-intelligence-index"
DOCS_URL = "https://artificialanalysis.ai/data-api/docs"

_EVAL_VERSION_RE = re.compile(
    r"Intelligence Index v(\d+)\.(\d+)(?:\.(\d+))?",
    re.IGNORECASE,
)
_DOCS_VERSION_RE = re.compile(
    r"Current version:\s*v(\d+)\.(\d+)(?:\.(\d+))?",
    re.IGNORECASE,
)
_TEXT_VERSION_RE = re.compile(r"v?(\d+)\.(\d+)(?:\.(\d+))?", re.IGNORECASE)


def canonical_major_minor(value: object) -> str | None:
    """Return ``major.minor`` without the leading ``v``.

    API payloads send the version as a JSON number (``4.3``). Official pages
    send ``v4.3`` or ``v4.3.2``. Patch is dropped. Unparseable input is ``None``.
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, str):
        match = _TEXT_VERSION_RE.fullmatch(value.strip())
        if not match:
            return None
        return f"{int(match.group(1))}.{int(match.group(2))}"
    if isinstance(value, int):
        return f"{value}.0"
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        # The wire field is major.minor only, so one decimal is the contract.
        rounded = round(value, 1)
        text = f"{rounded:.1f}"
        major, minor = text.split(".", 1)
        return f"{int(major)}.{int(minor)}"
    return None


def parse_eval_page_version(text: str) -> str | None:
    """First ``Intelligence Index vX.Y`` declaration on the evaluation page."""
    match = _EVAL_VERSION_RE.search(text or "")
    if not match:
        return None
    return f"{int(match.group(1))}.{int(match.group(2))}"


def parse_docs_current_version(text: str) -> str | None:
    """``Current version: vX.Y`` on the Data API docs page."""
    match = _DOCS_VERSION_RE.search(text or "")
    if not match:
        return None
    return f"{int(match.group(1))}.{int(match.group(2))}"


def g3_alignment(
    envelope_version: object,
    eval_page_text: str,
    docs_text: str,
) -> dict:
    """Decide whether a snapshot envelope matches the official current index.

    The evaluation page is the primary official source. If its major.minor
    disagrees with the docs ``Current version``, alignment fails and the
    difference is recorded. A parse failure also fails alignment.
    """
    eval_version = parse_eval_page_version(eval_page_text)
    docs_version = parse_docs_current_version(docs_text)
    envelope = canonical_major_minor(envelope_version)
    result = {
        "ok": False,
        "official": None,
        "eval_page": eval_version,
        "docs": docs_version,
        "envelope": envelope,
        "reason": "",
    }
    if eval_version is None or docs_version is None or envelope is None:
        result["reason"] = "parse_failed"
        return result
    if eval_version != docs_version:
        result["official"] = eval_version
        result["reason"] = "official_sources_conflict"
        return result
    result["official"] = eval_version
    if envelope != eval_version:
        result["reason"] = "envelope_mismatch"
        return result
    result["ok"] = True
    result["reason"] = "aligned"
    return result
