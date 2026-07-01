#!/usr/bin/env python3
"""Validate KMFA S13-P3 cross-table review artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.cross_table_review import (
    DEFAULT_HTML_OUTPUT_DIR,
    DEFAULT_OUTPUT_CHECKS,
    DEFAULT_OUTPUT_DIFFERENCE_QUEUE,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_QUALITY_REPORT,
    read_json,
    read_jsonl,
    validate_cross_table_review_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S13-P3 cross-table review artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--checks", type=Path, default=DEFAULT_OUTPUT_CHECKS)
    parser.add_argument("--difference-queue", type=Path, default=DEFAULT_OUTPUT_DIFFERENCE_QUEUE)
    parser.add_argument("--quality-report", type=Path, default=DEFAULT_OUTPUT_QUALITY_REPORT)
    parser.add_argument("--html-output-dir", type=Path, default=DEFAULT_HTML_OUTPUT_DIR)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    review_checks = read_jsonl(args.checks)
    difference_queue = read_jsonl(args.difference_queue)
    quality_report = read_json(args.quality_report)
    html_outputs = {
        "cross_table_quality_report": (args.html_output_dir / "cross_table_quality_report.html").read_text(
            encoding="utf-8"
        )
    }
    validate_cross_table_review_artifacts(
        manifest, review_checks, difference_queue, quality_report, html_outputs
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S13-P3 cross-table review check passed "
        f"(review_dimensions={summary['review_dimension_count']}, "
        f"difference_queue={summary['difference_queue_count']}, "
        f"quality_report={summary['quality_report_count']}, "
        f"pending_reconciliation={summary['pending_reconciliation_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "business_decision_basis=false, difference_auto_resolution=false, "
        "stage13_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
