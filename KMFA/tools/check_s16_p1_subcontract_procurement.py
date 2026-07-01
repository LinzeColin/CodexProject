#!/usr/bin/env python3
"""Validate KMFA S16-P1 subcontract procurement public-safe artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.subcontract_procurement_aggregation import (
    DEFAULT_OUTPUT_ANOMALY_CANDIDATES,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_PROJECT_MATCHES,
    DEFAULT_OUTPUT_SOURCE_LANES,
    DEFAULT_OUTPUT_UNALLOCATED_POOL,
    read_json,
    read_jsonl,
    validate_subcontract_procurement_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S16-P1 subcontract procurement artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--source-lanes", type=Path, default=DEFAULT_OUTPUT_SOURCE_LANES)
    parser.add_argument("--project-matches", type=Path, default=DEFAULT_OUTPUT_PROJECT_MATCHES)
    parser.add_argument("--unallocated-pool", type=Path, default=DEFAULT_OUTPUT_UNALLOCATED_POOL)
    parser.add_argument("--anomaly-candidates", type=Path, default=DEFAULT_OUTPUT_ANOMALY_CANDIDATES)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    source_lanes = read_jsonl(args.source_lanes)
    project_matches = read_jsonl(args.project_matches)
    unallocated_pool = read_jsonl(args.unallocated_pool)
    anomaly_candidates = read_jsonl(args.anomaly_candidates)

    validate_subcontract_procurement_artifacts(
        manifest,
        source_lanes,
        project_matches,
        unallocated_pool,
        anomaly_candidates,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S16-P1 subcontract procurement check passed "
        f"(source_lanes={summary['source_lane_count']}, "
        f"project_matches={summary['project_match_count']}, "
        f"unallocated_pool={summary['unallocated_cost_pool_count']}, "
        f"duplicate_payment_candidates={summary['duplicate_payment_candidate_count']}, "
        f"cross_project_candidates={summary['cross_project_cost_candidate_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "payment_execution=false, bank_operation=false, "
        "s16_p2_scope=false, s16_p3_scope=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
