"""Internal AA fetch. Writes a private snapshot and never touches the public table."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

from openrouter_watch.aa_fetch import FREE_MODELS_URL, advance_success_streak, fetch_language_models
from openrouter_watch.aa_snapshot import build_snapshot, store_snapshot
from openrouter_watch.aa_version import DOCS_URL, EVAL_PAGE_URL, g3_alignment

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "aa_internal"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def read_streak(out_dir: Path) -> int:
    path = out_dir / "streak.json"
    if not path.exists():
        return 0
    stored = json.loads(path.read_text(encoding="utf-8"))
    return int(stored.get("consecutive_successes") or 0)


def write_streak(out_dir: Path, streak: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    temporary = out_dir / "streak.json.tmp"
    temporary.write_text(
        json.dumps({"consecutive_successes": streak}, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, out_dir / "streak.json")


def commit_fetch(
    out_dir: Path,
    fetched: dict,
    *,
    previous: int,
    fetched_at: str,
    eval_text: str = "",
    docs_text: str = "",
) -> int:
    """Persist a capture. Failures zero the streak and leave existing snapshots in place."""
    if not fetched.get("ok"):
        write_streak(out_dir, 0)
        return 1
    snapshot = build_snapshot(fetched.get("pages") or [], fetched_at=fetched_at)
    if snapshot is None:
        write_streak(out_dir, 0)
        return 1
    alignment = g3_alignment(snapshot["intelligence_index_version"], eval_text, docs_text)
    snapshot["aa_official_index_version"] = alignment["official"]
    snapshot["g3"] = alignment
    try:
        store_snapshot(out_dir, snapshot)
    except FileExistsError:
        return 1
    write_streak(out_dir, advance_success_streak(previous, True))
    return 0 if alignment["ok"] else 1


def _official_texts(client: httpx.Client) -> tuple[str, str]:
    try:
        eval_page = client.get(EVAL_PAGE_URL, timeout=60)
        docs = client.get(DOCS_URL, timeout=60)
    except httpx.HTTPError:
        return "", ""
    return eval_page.text, docs.text


def main() -> int:
    api_key = os.environ.get("AA_API_KEY")
    if not api_key:
        print("AA_API_KEY is not set; internal fetch skipped. Public leaderboard unchanged.")
        return 2

    previous = read_streak(OUT_DIR)
    with httpx.Client(trust_env=False) as client:
        fetched = fetch_language_models(client, api_key=api_key, url=FREE_MODELS_URL)
        eval_text, docs_text = ("", "")
        if fetched["ok"]:
            eval_text, docs_text = _official_texts(client)

    code = commit_fetch(
        OUT_DIR,
        fetched,
        previous=previous,
        fetched_at=_utc_now(),
        eval_text=eval_text,
        docs_text=docs_text,
    )
    if code != 0 or not fetched["ok"]:
        print(
            "AA fetch did not publish a new public score. "
            f"failures={fetched['failures']} http_error={fetched['http_error']}. "
            "Public display and OpenRouter benchmark collection unchanged."
        )
        return code
    print(
        f"internal streak={read_streak(OUT_DIR)}. "
        "Public display stays on OpenRouter; benchmark collection stays on."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
