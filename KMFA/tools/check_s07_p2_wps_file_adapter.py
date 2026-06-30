#!/usr/bin/env python3
"""Validate KMFA S07-P2 WPS file adapter artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.wps_file_adapter import (
    DEFAULT_OUTPUT_CONVERSION_GUIDANCE,
    DEFAULT_OUTPUT_FIELD_REPORT,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_MAPPINGS,
    DEFAULT_OUTPUT_REGISTRY,
    DEFAULT_OUTPUT_RULE_VERSIONS,
    read_json,
    read_jsonl,
    validate_wps_adapter,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S07-P2 WPS file adapter artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--mappings", type=Path, default=DEFAULT_OUTPUT_MAPPINGS)
    parser.add_argument("--conversion-guidance", type=Path, default=DEFAULT_OUTPUT_CONVERSION_GUIDANCE)
    parser.add_argument("--field-report", type=Path, default=DEFAULT_OUTPUT_FIELD_REPORT)
    parser.add_argument("--rule-versions", type=Path, default=DEFAULT_OUTPUT_RULE_VERSIONS)
    parser.add_argument("--registry", type=Path, default=DEFAULT_OUTPUT_REGISTRY)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    mappings = read_jsonl(args.mappings)
    conversion_guidance = read_jsonl(args.conversion_guidance)
    field_report = read_jsonl(args.field_report)
    rule_versions = read_json(args.rule_versions)
    registry = read_json(args.registry)
    validate_wps_adapter(
        manifest,
        mappings,
        conversion_guidance,
        field_report,
        rule_versions,
        registry=registry,
    )
    print(
        "PASS: KMFA S07-P2 WPS file adapter check passed "
        f"(exports={manifest['summary']['source_export_type_count']}, "
        f"field_mappings={manifest['summary']['field_mapping_count']}, "
        f"conversion_guidance={manifest['summary']['conversion_guidance_count']}, "
        f"rule_versions={manifest['summary']['mapping_rule_version_count']}, "
        f"source_header_hashes={manifest['summary']['source_header_hash_count']}, "
        "finance_scope=false, redcircle_scope=false, formal_report_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
