#!/usr/bin/env python3
"""Validate KMFA S08-P3 entity matching quality artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.entity_matching_quality import (
    DEFAULT_OUTPUT_CASES,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_REPORT,
    DEFAULT_OUTPUT_REVIEW_QUEUE,
    read_json,
    read_jsonl,
    validate_entity_matching_quality_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S08-P3 entity matching quality artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--cases", type=Path, default=DEFAULT_OUTPUT_CASES)
    parser.add_argument("--report", type=Path, default=DEFAULT_OUTPUT_REPORT)
    parser.add_argument("--review-queue", type=Path, default=DEFAULT_OUTPUT_REVIEW_QUEUE)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    cases = read_jsonl(args.cases)
    report = read_json(args.report)
    review_queue = read_jsonl(args.review_queue)
    validate_entity_matching_quality_artifacts(manifest, cases, report, review_queue)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S08-P3 entity matching quality check passed "
        f"(scenarios={summary['scenario_count']}, "
        f"quality_cases={summary['quality_case_count']}, "
        f"manual_review_queue={summary['manual_review_queue_count']}, "
        "stage8_review_scope=false, fact_layer_scope=false, formal_report_allowed=false, "
        "github_upload_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
