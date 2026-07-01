#!/usr/bin/env python3
"""Validate KMFA S14-P3 policy evidence public-safe artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.policy_evidence_plan import (
    DEFAULT_HTML_OUTPUT_DIR,
    DEFAULT_OUTPUT_DIRECTORIES,
    DEFAULT_OUTPUT_GAPS,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_RISK_TIPS,
    read_json,
    read_jsonl,
    validate_policy_evidence_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S14-P3 policy evidence artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--directories", type=Path, default=DEFAULT_OUTPUT_DIRECTORIES)
    parser.add_argument("--gaps", type=Path, default=DEFAULT_OUTPUT_GAPS)
    parser.add_argument("--risk-tips", type=Path, default=DEFAULT_OUTPUT_RISK_TIPS)
    parser.add_argument("--html-output-dir", type=Path, default=DEFAULT_HTML_OUTPUT_DIR)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    directories = read_jsonl(args.directories)
    gaps = read_jsonl(args.gaps)
    risk_tips = read_jsonl(args.risk_tips)
    html_outputs = {
        "policy_evidence_overview": (args.html_output_dir / "policy_evidence_overview.html").read_text(
            encoding="utf-8"
        )
    }

    validate_policy_evidence_artifacts(manifest, directories, gaps, risk_tips, html_outputs)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S14-P3 policy evidence check passed "
        f"(policy_programs={summary['policy_program_count']}, "
        f"directories={summary['evidence_directory_count']}, "
        f"gaps={summary['evidence_gap_count']}, "
        f"risk_tips={summary['risk_tip_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "policy_conclusion=false, policy_submission=false, "
        "stage14_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
