#!/usr/bin/env python3
"""Validate KMFA S08-P1 project composite key artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.project_composite_key import (
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_MATCHES,
    DEFAULT_OUTPUT_PROFILES,
    DEFAULT_OUTPUT_REVIEW_QUEUE,
    read_json,
    read_jsonl,
    validate_project_composite_key_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S08-P1 project composite key artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--profiles", type=Path, default=DEFAULT_OUTPUT_PROFILES)
    parser.add_argument("--matches", type=Path, default=DEFAULT_OUTPUT_MATCHES)
    parser.add_argument("--review-queue", type=Path, default=DEFAULT_OUTPUT_REVIEW_QUEUE)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    profiles = read_jsonl(args.profiles)
    match_results = read_jsonl(args.matches)
    review_queue = read_jsonl(args.review_queue)
    validate_project_composite_key_artifacts(manifest, profiles, match_results, review_queue)
    print(
        "PASS: KMFA S08-P1 project composite key check passed "
        f"(components={len(manifest['required_components'])}, "
        f"profiles={manifest['summary']['profile_count']}, "
        f"matches={manifest['summary']['match_result_count']}, "
        f"manual_review_queue={manifest['summary']['manual_review_queue_count']}, "
        f"strong_threshold_bps={manifest['thresholds_bps']['strong_auto_match']}, "
        f"human_review_threshold_bps={manifest['thresholds_bps']['human_review']}, "
        "formal_report_allowed=false, github_upload_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
