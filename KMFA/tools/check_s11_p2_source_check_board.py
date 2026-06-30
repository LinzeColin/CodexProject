#!/usr/bin/env python3
"""Validate KMFA S11-P2 public-safe source check board artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.source_check_board_runtime import (
    DEFAULT_HTML_OUTPUT,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_ROWS,
    read_json,
    read_jsonl,
    validate_source_check_board_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S11-P2 source check board artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--rows", type=Path, default=DEFAULT_OUTPUT_ROWS)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML_OUTPUT)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    rows = read_jsonl(args.rows)
    render_outputs = {"html": {"kmfa_source_check_board": args.html.read_text(encoding="utf-8")}}
    validate_source_check_board_artifacts(manifest, rows, render_outputs)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S11-P2 source check board passed "
        f"(matrix_rows={summary['matrix_row_count']}, "
        f"html_exports={summary['html_export_count']}, "
        "columns=11, statuses=5, status_click_detail=true, "
        "blue_gray_surface=true, large_yellow_surface_count=0, "
        "formal_report_allowed=false, s11_p3_scope=false, stage11_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
