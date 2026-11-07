"""Write an internal join report. Does not rewrite models_latest.json or the public switch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openrouter_watch.aa_gates import (
    effective_collect_openrouter_benchmark,
    effective_display_source,
    g0_ok,
    publication_problems,
)
from openrouter_watch.aa_join import annotate_internal_scores, coverage
from openrouter_watch.aa_mapping import validate_mapping

ROOT = Path(__file__).resolve().parents[1]


def build_report(
    *,
    mapping: dict,
    publication: dict,
    rows: list[dict],
    snapshot: dict | None,
) -> dict:
    result = validate_mapping(mapping, snapshot)
    report = {
        "mapping_ok": result.ok,
        "error_codes": result.codes,
        "edge_count": len(result.edges),
        "g0_ok": g0_ok(publication.get("g0")),
        "public_display_source": effective_display_source(publication, cutover_allowed=False),
        "collect_openrouter_benchmark": effective_collect_openrouter_benchmark(
            publication,
            cutover_allowed=False,
            refresh_verified=False,
        ),
        "publication_problems": publication_problems(
            publication,
            cutover_allowed=False,
            refresh_verified=False,
        ),
        "coverage": None,
        "rows": [],
    }
    if snapshot is not None and result.ok:
        report["coverage"] = coverage(rows, result.edges, snapshot)
        report["rows"] = annotate_internal_scores(rows, result.edges, snapshot)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Internal AA mapping report")
    parser.add_argument("--snapshot", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    mapping = json.loads((ROOT / "data/aa_join/mapping.json").read_text(encoding="utf-8"))
    publication = json.loads((ROOT / "data/aa_join/publication.json").read_text(encoding="utf-8"))
    rows = json.loads((ROOT / "data/derived/models_latest.json").read_text(encoding="utf-8"))
    snapshot = None
    if args.snapshot is not None:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    report = build_report(mapping=mapping, publication=publication, rows=rows, snapshot=snapshot)
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["mapping_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
