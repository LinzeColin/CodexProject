#!/usr/bin/env python3
"""Validate KMFA S10-P2 report grade runtime artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.report_grade_runtime import (
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_RECORDS,
    read_json,
    read_jsonl,
    validate_report_grade_runtime_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S10-P2 report grade runtime artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--records", type=Path, default=DEFAULT_OUTPUT_RECORDS)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    records = read_jsonl(args.records)
    validate_report_grade_runtime_artifacts(manifest, records)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S10-P2 report grade runtime check passed "
        f"(grade_records={summary['report_grade_record_count']}, "
        f"grade_distribution={summary['grade_distribution']}, "
        f"pending_reconciliation_count={summary['pending_reconciliation_count']}, "
        "complete_trusted_report_display_allowed=false, formal_report_allowed=false, "
        "business_decision_basis_allowed=false, s10_p3_scope=false, export_artifact_count=0)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
