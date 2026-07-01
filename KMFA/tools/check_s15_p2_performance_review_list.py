#!/usr/bin/env python3
"""Validate KMFA S15-P2 performance review list artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.performance_review_list import (
    DEFAULT_OUTPUT_FACT_TABLE,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_REVIEW_ITEMS,
    read_json,
    read_jsonl,
    validate_performance_review_list_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S15-P2 performance review list artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--fact-table", type=Path, default=DEFAULT_OUTPUT_FACT_TABLE)
    parser.add_argument("--review-items", type=Path, default=DEFAULT_OUTPUT_REVIEW_ITEMS)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    fact_rows = read_jsonl(args.fact_table)
    review_items = read_jsonl(args.review_items)

    validate_performance_review_list_artifacts(manifest, fact_rows, review_items)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S15-P2 performance review list check passed "
        f"(fact_rows={summary['performance_fact_row_count']}, "
        f"review_items={summary['abnormal_review_item_count']}, "
        "performance_fact_table=true, abnormal_review_list=true, "
        "salary_calculation=false, bonus_approval=false, payroll_export=false, "
        "final_compensation=false, s15_p3_scope=false, stage15_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
