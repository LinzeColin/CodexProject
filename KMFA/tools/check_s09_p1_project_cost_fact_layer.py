#!/usr/bin/env python3
"""Validate KMFA S09-P1 project cost fact layer artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.project_cost_fact_layer import (
    DEFAULT_OUTPUT_FACT_RECORDS,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_UNALLOCATED_POOL,
    read_json,
    read_jsonl,
    validate_project_cost_fact_layer_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S09-P1 project cost fact layer artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--fact-records", type=Path, default=DEFAULT_OUTPUT_FACT_RECORDS)
    parser.add_argument("--unallocated-pool", type=Path, default=DEFAULT_OUTPUT_UNALLOCATED_POOL)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    fact_records = read_jsonl(args.fact_records)
    unallocated_pool = read_jsonl(args.unallocated_pool)
    validate_project_cost_fact_layer_artifacts(manifest, fact_records, unallocated_pool)
    summary = manifest["summary"]
    upstream = manifest["upstream_quality_summary"]
    print(
        "PASS: KMFA S09-P1 project cost fact layer check passed "
        f"(fact_records={summary['fact_record_count']}, "
        f"cost_categories={summary['cost_category_count']}, "
        f"unallocated_pool={summary['unallocated_pool_count']}, "
        f"manual_review_queue={upstream['manual_review_queue_count']}, "
        f"unresolved_differences={upstream['unresolved_difference_count']}, "
        "s09_p2_scope=false, s09_p3_scope=false, formal_report_allowed=false, github_upload_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
