#!/usr/bin/env python3
"""Validate KMFA S11-P3 public-safe project cost page artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.project_cost_page_runtime import (
    DEFAULT_HTML_OUTPUT,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_PROJECTS,
    read_json,
    read_jsonl,
    validate_project_cost_page_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S11-P3 project cost page artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--projects", type=Path, default=DEFAULT_OUTPUT_PROJECTS)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML_OUTPUT)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    projects = read_jsonl(args.projects)
    render_outputs = {"html": {"kmfa_project_cost_page": args.html.read_text(encoding="utf-8")}}
    validate_project_cost_page_artifacts(manifest, projects, render_outputs)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S11-P3 project cost page passed "
        f"(projects={summary['project_row_count']}, "
        f"margin_records={summary['margin_record_count']}, "
        f"cost_categories={summary['cost_category_count']}, "
        f"pending_reconciliations={summary['pending_reconciliation_count']}, "
        "report_preview=true, report_grade=D, quality_bypass=false, "
        "formal_report_allowed=false, stage11_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
