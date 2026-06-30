#!/usr/bin/env python3
"""Validate KMFA S08-P2 business entity model artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.business_entity_model import (
    DEFAULT_OUTPUT_LIFECYCLES,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_RELATIONSHIPS,
    DEFAULT_OUTPUT_SCHEMA,
    read_json,
    read_jsonl,
    validate_business_entity_model_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S08-P2 business entity model artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--schema", type=Path, default=DEFAULT_OUTPUT_SCHEMA)
    parser.add_argument("--relationships", type=Path, default=DEFAULT_OUTPUT_RELATIONSHIPS)
    parser.add_argument("--lifecycles", type=Path, default=DEFAULT_OUTPUT_LIFECYCLES)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    schema_doc = read_json(args.schema)
    relationships = read_jsonl(args.relationships)
    lifecycle_statuses = read_jsonl(args.lifecycles)
    validate_business_entity_model_artifacts(manifest, schema_doc, relationships, lifecycle_statuses)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S08-P2 business entity model check passed "
        f"(entities={summary['entity_type_count']}, "
        f"relationships={summary['relationship_count']}, "
        f"lifecycle_statuses={summary['lifecycle_status_count']}, "
        "s08_p3_scope=false, fact_layer_scope=false, formal_report_allowed=false, github_upload_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
