#!/usr/bin/env python3
"""Validate KMFA S14-P2 invoice/tax public-safe artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.invoice_tax_plan import (
    DEFAULT_HTML_OUTPUT_DIR,
    DEFAULT_OUTPUT_CASH_SUMMARIES,
    DEFAULT_OUTPUT_ISSUE_CANDIDATES,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_SOURCE_LANES,
    read_json,
    read_jsonl,
    validate_invoice_tax_plan_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S14-P2 invoice/tax planning artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--source-lanes", type=Path, default=DEFAULT_OUTPUT_SOURCE_LANES)
    parser.add_argument("--issue-candidates", type=Path, default=DEFAULT_OUTPUT_ISSUE_CANDIDATES)
    parser.add_argument("--cash-summaries", type=Path, default=DEFAULT_OUTPUT_CASH_SUMMARIES)
    parser.add_argument("--html-output-dir", type=Path, default=DEFAULT_HTML_OUTPUT_DIR)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    source_lanes = read_jsonl(args.source_lanes)
    issue_candidates = read_jsonl(args.issue_candidates)
    cash_summaries = read_jsonl(args.cash_summaries)
    html_outputs = {
        "invoice_tax_plan_overview": (args.html_output_dir / "invoice_tax_plan_overview.html").read_text(
            encoding="utf-8"
        )
    }

    validate_invoice_tax_plan_artifacts(
        manifest,
        source_lanes,
        issue_candidates,
        cash_summaries,
        html_outputs,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S14-P2 invoice tax plan check passed "
        f"(source_lanes={summary['source_lane_count']}, "
        f"issue_candidates={summary['issue_candidate_count']}, "
        f"cash_summaries={summary['cash_summary_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "tax_filing=false, invoice_issuance=false, "
        "s14_p3_scope=false, stage14_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
