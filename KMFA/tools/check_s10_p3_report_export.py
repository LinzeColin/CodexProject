#!/usr/bin/env python3
"""Validate KMFA S10-P3 report export artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.report_export_runtime import (
    DEFAULT_CSV_OUTPUT_DIR,
    DEFAULT_HTML_OUTPUT_DIR,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_RECORDS,
    REQUIRED_TEMPLATE_IDS,
    read_json,
    read_jsonl,
    validate_report_export_artifacts,
)


def _read_render_outputs(html_dir: Path, csv_dir: Path) -> dict[str, dict[str, str]]:
    return {
        "html": {
            template_id: (html_dir / f"{template_id}.html").read_text(encoding="utf-8")
            for template_id in REQUIRED_TEMPLATE_IDS
        },
        "csv": {
            template_id: (csv_dir / f"{template_id}_appendix.csv").read_text(encoding="utf-8")
            for template_id in REQUIRED_TEMPLATE_IDS
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S10-P3 report export artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--records", type=Path, default=DEFAULT_OUTPUT_RECORDS)
    parser.add_argument("--html-dir", type=Path, default=DEFAULT_HTML_OUTPUT_DIR)
    parser.add_argument("--csv-dir", type=Path, default=DEFAULT_CSV_OUTPUT_DIR)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    records = read_jsonl(args.records)
    render_outputs = _read_render_outputs(args.html_dir, args.csv_dir)
    validate_report_export_artifacts(manifest, records, render_outputs)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S10-P3 report export check passed "
        f"(export_records={summary['report_export_record_count']}, "
        f"html_exports={summary['html_export_count']}, "
        f"csv_appendices={summary['csv_appendix_count']}, "
        f"excel_compatible_downloads={summary['excel_compatible_download_count']}, "
        "pdf_private_runtime_enabled=true, committed_pdf_files=0, committed_excel_files=0, "
        "formal_report_allowed=false, business_decision_basis_allowed=false, "
        "stage10_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
