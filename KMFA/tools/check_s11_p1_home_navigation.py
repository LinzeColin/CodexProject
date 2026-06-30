#!/usr/bin/env python3
"""Validate KMFA S11-P1 public-safe home navigation artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.home_navigation_runtime import (
    DEFAULT_HTML_OUTPUT,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_RECORDS,
    read_json,
    read_jsonl,
    validate_home_navigation_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S11-P1 home navigation artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--records", type=Path, default=DEFAULT_OUTPUT_RECORDS)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML_OUTPUT)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    records = read_jsonl(args.records)
    render_outputs = {"html": {"kmfa_home_navigation": args.html.read_text(encoding="utf-8")}}
    validate_home_navigation_artifacts(manifest, records, render_outputs)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S11-P1 home navigation check passed "
        f"(navigation_modules={summary['navigation_module_count']}, "
        f"html_exports={summary['html_export_count']}, "
        "km_brand=true, blue_business_style=true, all_chinese=true, "
        "formal_report_allowed=false, business_decision_basis_allowed=false, "
        "s11_p2_scope=false, s11_p3_scope=false, stage11_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
