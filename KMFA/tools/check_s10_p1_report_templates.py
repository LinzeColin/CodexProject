#!/usr/bin/env python3
"""Validate KMFA S10-P1 report template artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.report_templates import (
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_SECTIONS,
    DEFAULT_OUTPUT_TEMPLATES,
    read_json,
    read_jsonl,
    validate_report_template_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S10-P1 report template artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--templates", type=Path, default=DEFAULT_OUTPUT_TEMPLATES)
    parser.add_argument("--sections", type=Path, default=DEFAULT_OUTPUT_SECTIONS)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    templates = read_jsonl(args.templates)
    sections = read_jsonl(args.sections)
    validate_report_template_artifacts(manifest, templates, sections)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S10-P1 report template check passed "
        f"(templates={summary['template_count']}, "
        f"sections={summary['section_count']}, "
        f"project_cost_sections={summary['project_cost_section_count']}, "
        f"business_overview_sections={summary['business_overview_section_count']}, "
        "formal_report_allowed=false, trusted_grade_assignment_allowed=false, "
        "s10_p2_scope=false, s10_p3_scope=false, ui_scope=false, "
        "lineage_full_check_scope=false, external_connector_scope=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
