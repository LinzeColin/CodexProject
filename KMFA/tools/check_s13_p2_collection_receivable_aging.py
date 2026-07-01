#!/usr/bin/env python3
"""Validate KMFA S13-P2 collection receivable aging artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.collection_receivable_aging import (
    DEFAULT_HTML_OUTPUT_DIR,
    DEFAULT_OUTPUT_LANES,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_PRIORITY_ITEMS,
    DEFAULT_OUTPUT_RESPONSIBILITY_ITEMS,
    read_json,
    read_jsonl,
    validate_collection_receivable_aging_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S13-P2 collection receivable aging artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--lanes", type=Path, default=DEFAULT_OUTPUT_LANES)
    parser.add_argument("--priority-items", type=Path, default=DEFAULT_OUTPUT_PRIORITY_ITEMS)
    parser.add_argument("--responsibility-items", type=Path, default=DEFAULT_OUTPUT_RESPONSIBILITY_ITEMS)
    parser.add_argument("--html-output-dir", type=Path, default=DEFAULT_HTML_OUTPUT_DIR)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    lanes = read_jsonl(args.lanes)
    priority_items = read_jsonl(args.priority_items)
    responsibility_items = read_jsonl(args.responsibility_items)
    html_outputs = {
        "collection_receivable_aging_priority": (
            args.html_output_dir / "collection_receivable_aging_priority.html"
        ).read_text(encoding="utf-8")
    }
    validate_collection_receivable_aging_artifacts(
        manifest, lanes, priority_items, responsibility_items, html_outputs
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S13-P2 collection receivable aging check passed "
        f"(source_lanes={summary['source_lane_count']}, "
        f"issue_types={summary['required_issue_type_count']}, "
        f"priority_items={summary['priority_item_count']}, "
        f"responsibility_items={summary['responsibility_item_count']}, "
        f"field_mappings={summary['field_mapping_count']}, "
        f"pending_reconciliation={summary['pending_reconciliation_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "business_decision_basis=false, legal_collection_decision=false, "
        "payment_or_bank_operation=false, s13_p3_scope=false, "
        "stage13_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
