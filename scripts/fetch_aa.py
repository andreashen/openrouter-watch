"""Internal AA fetch. Writes a private snapshot and never touches the public table."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

from openrouter_watch.aa_fetch import FREE_MODELS_URL, advance_success_streak, fetch_language_models
from openrouter_watch.aa_snapshot import build_snapshot
from openrouter_watch.aa_version import DOCS_URL, EVAL_PAGE_URL, g3_alignment

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "aa_internal"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def main() -> int:
    api_key = os.environ.get("AA_API_KEY")
    if not api_key:
        print("AA_API_KEY is not set; internal fetch skipped. Public leaderboard unchanged.")
        return 2

    state_path = OUT_DIR / "streak.json"
    previous = 0
    if state_path.exists():
        stored = json.loads(state_path.read_text(encoding="utf-8"))
        previous = int(stored.get("consecutive_successes") or 0)

    with httpx.Client(trust_env=False) as client:
        fetched = fetch_language_models(client, api_key=api_key, url=FREE_MODELS_URL)
        eval_page = client.get(EVAL_PAGE_URL, timeout=60)
        docs = client.get(DOCS_URL, timeout=60)

    streak = advance_success_streak(previous, bool(fetched["ok"]))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"consecutive_successes": streak}, indent=2) + "\n",
        encoding="utf-8",
    )
    if not fetched["ok"]:
        print(
            "AA fetch discarded; no snapshot written. "
            f"failures={fetched['failures']} http_error={fetched['http_error']}. "
            "Public display and OpenRouter benchmark collection unchanged."
        )
        return 1

    fetched_at = _utc_now()
    snapshot = build_snapshot(fetched["pages"], fetched_at=fetched_at)
    if snapshot is None:
        print("Snapshot build returned nothing. Public display unchanged.")
        return 1
    alignment = g3_alignment(
        snapshot["intelligence_index_version"],
        eval_page.text,
        docs.text,
    )
    snapshot["aa_official_index_version"] = alignment["official"]
    snapshot["g3"] = alignment
    (OUT_DIR / "latest_snapshot.json").write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"internal snapshot {snapshot['aa_snapshot_id']} g3={alignment['reason']} "
        f"streak={streak}. Public display stays on OpenRouter; benchmark collection stays on."
    )
    return 0 if alignment["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
