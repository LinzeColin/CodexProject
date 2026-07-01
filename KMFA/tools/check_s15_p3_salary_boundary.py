#!/usr/bin/env python3
"""Validate KMFA S15-P3 performance salary boundary artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.performance_salary_boundary import (
    DEFAULT_OUTPUT_INTERFACE_CONTRACT,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_READINESS_DRAFT,
    read_json,
    read_jsonl,
    validate_performance_salary_boundary_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S15-P3 performance salary boundary artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--interface-contract", type=Path, default=DEFAULT_OUTPUT_INTERFACE_CONTRACT)
    parser.add_argument("--readiness-draft", type=Path, default=DEFAULT_OUTPUT_READINESS_DRAFT)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    interface_contract = read_json(args.interface_contract)
    readiness_rows = read_jsonl(args.readiness_draft)

    validate_performance_salary_boundary_artifacts(manifest, interface_contract, readiness_rows)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S15-P3 salary boundary check passed "
        f"(interface_contracts={summary['fact_interface_contract_count']}, "
        f"readiness_rows={summary['future_salary_system_readiness_row_count']}, "
        "future_read_draft=true, live_integration=false, "
        "salary_calculation=false, bonus_approval=false, payroll_export=false, "
        "final_approval_human=true, payment_release_human=true, "
        "stage15_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
