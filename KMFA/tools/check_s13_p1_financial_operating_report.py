#!/usr/bin/env python3
"""Validate KMFA S13-P1 financial operating report artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.financial_operating_report import (
    DEFAULT_HTML_OUTPUT_DIR,
    DEFAULT_OUTPUT_DRAFTS,
    DEFAULT_OUTPUT_LANES,
    DEFAULT_OUTPUT_MANIFEST,
    REQUIRED_DRAFT_IDS,
    read_json,
    read_jsonl,
    validate_financial_operating_report_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S13-P1 financial operating report artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--lanes", type=Path, default=DEFAULT_OUTPUT_LANES)
    parser.add_argument("--drafts", type=Path, default=DEFAULT_OUTPUT_DRAFTS)
    parser.add_argument("--html-output-dir", type=Path, default=DEFAULT_HTML_OUTPUT_DIR)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    lanes = read_jsonl(args.lanes)
    drafts = read_jsonl(args.drafts)
    html_outputs = {
        draft_id: (args.html_output_dir / f"{draft_id}.html").read_text(encoding="utf-8")
        for draft_id in REQUIRED_DRAFT_IDS
    }
    validate_financial_operating_report_artifacts(manifest, lanes, drafts, html_outputs)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S13-P1 financial operating report check passed "
        f"(source_lanes={summary['source_lane_count']}, "
        f"drafts={summary['draft_report_count']}, "
        f"html={summary['html_draft_count']}, "
        f"field_mappings={summary['field_mapping_count']}, "
        f"pending_reconciliation={summary['pending_reconciliation_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "business_decision_basis=false, s13_p2_scope=false, s13_p3_scope=false, "
        "lineage_full_check_scope=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
