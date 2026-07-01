#!/usr/bin/env python3
"""Validate KMFA S16-P2 project status lifecycle public-safe artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.project_status_lifecycle import (
    DEFAULT_OUTPUT_EXCEPTION_ITEMS,
    DEFAULT_OUTPUT_HANDOFF_GUARDS,
    DEFAULT_OUTPUT_LIFECYCLE_RECORDS,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_SOURCE_LANES,
    read_json,
    read_jsonl,
    validate_project_status_lifecycle_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S16-P2 project status lifecycle artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--source-lanes", type=Path, default=DEFAULT_OUTPUT_SOURCE_LANES)
    parser.add_argument("--lifecycle-records", type=Path, default=DEFAULT_OUTPUT_LIFECYCLE_RECORDS)
    parser.add_argument("--exception-items", type=Path, default=DEFAULT_OUTPUT_EXCEPTION_ITEMS)
    parser.add_argument("--handoff-guards", type=Path, default=DEFAULT_OUTPUT_HANDOFF_GUARDS)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    source_lanes = read_jsonl(args.source_lanes)
    lifecycle_records = read_jsonl(args.lifecycle_records)
    exception_items = read_jsonl(args.exception_items)
    handoff_guards = read_jsonl(args.handoff_guards)

    validate_project_status_lifecycle_artifacts(
        manifest,
        source_lanes,
        lifecycle_records,
        exception_items,
        handoff_guards,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S16-P2 project status lifecycle check passed "
        f"(source_lanes={summary['source_lane_count']}, "
        f"lifecycle_records={summary['lifecycle_record_count']}, "
        f"exception_items={summary['exception_item_count']}, "
        f"handoff_guards={summary['handoff_guard_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "site_construction=false, safety_signature=false, technical_signature=false, "
        "invoice_issuance=false, collection_action=false, "
        "s16_p3_scope=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
