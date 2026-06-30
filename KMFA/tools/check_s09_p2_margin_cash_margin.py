#!/usr/bin/env python3
"""Validate KMFA S09-P2 margin and cash margin artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.project_margin_cash_margin import (
    DEFAULT_OUTPUT_DIFFERENCE_SUMMARY,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_MARGIN_RECORDS,
    read_json,
    read_jsonl,
    validate_project_margin_cash_margin_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S09-P2 margin and cash margin artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--margin-records", type=Path, default=DEFAULT_OUTPUT_MARGIN_RECORDS)
    parser.add_argument("--difference-summary", type=Path, default=DEFAULT_OUTPUT_DIFFERENCE_SUMMARY)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    margin_records = read_jsonl(args.margin_records)
    difference_summary = read_jsonl(args.difference_summary)
    validate_project_margin_cash_margin_artifacts(manifest, margin_records, difference_summary)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S09-P2 margin and cash margin check passed "
        f"(margin_records={summary['margin_record_count']}, "
        f"difference_summary={summary['difference_summary_count']}, "
        f"upstream_manual_review_queue={summary['upstream_manual_review_queue_count']}, "
        f"upstream_unresolved_differences={summary['upstream_unresolved_difference_count']}, "
        "s09_p3_scope=false, formal_report_allowed=false, github_upload_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
