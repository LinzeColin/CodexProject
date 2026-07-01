#!/usr/bin/env python3
"""Validate KMFA S15-P1 performance fact field artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.performance_fact_fields import (
    DEFAULT_OUTPUT_FIELD_BINDINGS,
    DEFAULT_OUTPUT_FIELD_DEFINITIONS,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_MANUAL_REVIEW_FIELDS,
    read_json,
    read_jsonl,
    validate_performance_fact_field_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S15-P1 performance fact field artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--field-definitions", type=Path, default=DEFAULT_OUTPUT_FIELD_DEFINITIONS)
    parser.add_argument("--field-bindings", type=Path, default=DEFAULT_OUTPUT_FIELD_BINDINGS)
    parser.add_argument("--manual-review-fields", type=Path, default=DEFAULT_OUTPUT_MANUAL_REVIEW_FIELDS)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    field_definitions = read_jsonl(args.field_definitions)
    field_bindings = read_jsonl(args.field_bindings)
    manual_review_fields = read_jsonl(args.manual_review_fields)

    validate_performance_fact_field_artifacts(
        manifest,
        field_definitions,
        field_bindings,
        manual_review_fields,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S15-P1 performance fact field check passed "
        f"(fields={summary['field_definition_count']}, "
        f"bindings={summary['field_binding_count']}, "
        f"manual_reviews={summary['manual_review_field_count']}, "
        "performance_fact_table=false, salary_calculation=false, "
        "bonus_approval=false, payroll_export=false, "
        "s15_p2_scope=false, s15_p3_scope=false, stage15_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
