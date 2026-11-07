"""Reject a mapping or publication file that would move the public leaderboard."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from openrouter_watch.aa_gates import repo_publication_is_held
from openrouter_watch.aa_join import qa_sample_problems
from openrouter_watch.aa_mapping import validate_mapping

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    mapping = json.loads((ROOT / "data/aa_join/mapping.json").read_text(encoding="utf-8"))
    publication = json.loads((ROOT / "data/aa_join/publication.json").read_text(encoding="utf-8"))
    sample = json.loads((ROOT / "data/aa_join/qa_sample.json").read_text(encoding="utf-8"))
    rows = json.loads((ROOT / "data/derived/models_latest.json").read_text(encoding="utf-8"))

    problems: list[str] = []
    result = validate_mapping(mapping)
    if not result.ok:
        problems.extend(result.codes)
    problems.extend(repo_publication_is_held(publication))
    problems.extend(qa_sample_problems(sample, rows))
    if problems:
        print("aa mapping check failed: " + ", ".join(problems))
        return 1
    print("aa mapping held: public display stays on OpenRouter; benchmark collection stays on")
    return 0


if __name__ == "__main__":
    sys.exit(main())
