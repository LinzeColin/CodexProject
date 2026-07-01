#!/usr/bin/env python3
"""Validate KMFA S16-P3 customer business analysis public-safe artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.customer_business_analysis import (
    DEFAULT_OUTPUT_EXCEPTIONS,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_SOURCE_LANES,
    DEFAULT_OUTPUT_SUMMARIES,
    read_json,
    read_jsonl,
    validate_customer_business_analysis_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S16-P3 customer business analysis artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--source-lanes", type=Path, default=DEFAULT_OUTPUT_SOURCE_LANES)
    parser.add_argument("--customer-summaries", type=Path, default=DEFAULT_OUTPUT_SUMMARIES)
    parser.add_argument("--exception-items", type=Path, default=DEFAULT_OUTPUT_EXCEPTIONS)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    source_lanes = read_jsonl(args.source_lanes)
    customer_summaries = read_jsonl(args.customer_summaries)
    exception_items = read_jsonl(args.exception_items)

    validate_customer_business_analysis_artifacts(
        manifest,
        source_lanes,
        customer_summaries,
        exception_items,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S16-P3 customer business analysis check passed "
        f"(source_lanes={summary['source_lane_count']}, "
        f"customer_summaries={summary['customer_summary_count']}, "
        f"exception_items={summary['exception_item_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "business_decision_basis=false, collection_action=false, legal_collection_decision=false, "
        "stage16_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
