#!/usr/bin/env python3
"""Validate KMFA S18-P2 full-regression acceptance artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.full_regression_acceptance import (
    DEFAULT_OUTPUT_CHECKS,
    DEFAULT_OUTPUT_GO_NO_GO,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_STAGE_EVIDENCE,
    read_json,
    read_jsonl,
    validate_full_regression_acceptance_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S18-P2 full-regression acceptance artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--checks", type=Path, default=DEFAULT_OUTPUT_CHECKS)
    parser.add_argument("--stage-evidence", type=Path, default=DEFAULT_OUTPUT_STAGE_EVIDENCE)
    parser.add_argument("--go-no-go", type=Path, default=DEFAULT_OUTPUT_GO_NO_GO)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    check_results = read_jsonl(args.checks)
    stage_evidence = read_jsonl(args.stage_evidence)
    go_no_go = read_json(args.go_no_go)
    validate_full_regression_acceptance_artifacts(manifest, check_results, stage_evidence, go_no_go)
    print(
        "PASS: KMFA S18-P2 full regression acceptance check passed "
        f"(checks={len(check_results)}, "
        f"stages={len(stage_evidence)}, "
        f"decision={go_no_go['decision']}, "
        "delivery_allowed=false, s18_p3=false, stage18_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
