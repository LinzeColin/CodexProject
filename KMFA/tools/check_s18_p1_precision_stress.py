#!/usr/bin/env python3
"""Validate KMFA S18-P1 precision and stress test artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.precision_stress_validation import (
    DEFAULT_OUTPUT_ERROR_REPORTS,
    DEFAULT_OUTPUT_IMPORT_RUNS,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_SCENARIOS,
    read_json,
    read_jsonl,
    validate_precision_stress_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S18-P1 precision stress artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_OUTPUT_SCENARIOS)
    parser.add_argument("--import-runs", type=Path, default=DEFAULT_OUTPUT_IMPORT_RUNS)
    parser.add_argument("--error-reports", type=Path, default=DEFAULT_OUTPUT_ERROR_REPORTS)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    scenarios = read_jsonl(args.scenarios)
    import_runs = read_jsonl(args.import_runs)
    error_reports = read_jsonl(args.error_reports)
    validate_precision_stress_artifacts(manifest, scenarios, import_runs, error_reports)
    print(
        "PASS: KMFA S18-P1 precision stress check passed "
        f"(scenarios={len(scenarios)}, "
        f"runs={len(import_runs)}, "
        f"large_batch_files={manifest['large_batch']['synthetic_file_count']}, "
        f"elapsed_ms={manifest['large_batch']['elapsed_ms']}, "
        f"errors={len(error_reports)}, "
        "s18_p2=false, s18_p3=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
