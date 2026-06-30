#!/usr/bin/env python3
"""Validate KMFA S09-P3 scope reconciliation artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.project_scope_reconciliation import (
    DEFAULT_OUTPUT_DOMAIN_CONTROLS,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_RECONCILIATION_RECORDS,
    read_json,
    read_jsonl,
    validate_project_scope_reconciliation_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S09-P3 scope reconciliation artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--reconciliation-records", type=Path, default=DEFAULT_OUTPUT_RECONCILIATION_RECORDS)
    parser.add_argument("--domain-controls", type=Path, default=DEFAULT_OUTPUT_DOMAIN_CONTROLS)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    reconciliation_records = read_jsonl(args.reconciliation_records)
    domain_controls = read_jsonl(args.domain_controls)
    validate_project_scope_reconciliation_artifacts(manifest, reconciliation_records, domain_controls)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S09-P3 scope reconciliation check passed "
        f"(reconciliation_records={summary['reconciliation_record_count']}, "
        f"domain_controls={summary['domain_control_count']}, "
        f"confirmed_resolutions={summary['confirmed_resolution_count']}, "
        f"pending_resolutions={summary['pending_resolution_count']}, "
        "derived_metric_rerun_allowed=false, formal_report_allowed=false, "
        "stage9_review_allowed=false, github_upload_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
