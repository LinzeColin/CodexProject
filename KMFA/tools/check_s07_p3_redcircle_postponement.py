#!/usr/bin/env python3
"""Validate KMFA S07-P3 Redcircle postponement policy artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.redcircle_postponement_policy import (
    DEFAULT_OUTPUT_CONNECTOR_POLICY,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_REGISTRY,
    DEFAULT_OUTPUT_ROLLBACK_PLAN,
    DEFAULT_OUTPUT_TEMPLATES,
    read_json,
    read_jsonl,
    validate_redcircle_postponement_policy,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S07-P3 Redcircle postponement artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--templates", type=Path, default=DEFAULT_OUTPUT_TEMPLATES)
    parser.add_argument("--connector-policy", type=Path, default=DEFAULT_OUTPUT_CONNECTOR_POLICY)
    parser.add_argument("--rollback-plan", type=Path, default=DEFAULT_OUTPUT_ROLLBACK_PLAN)
    parser.add_argument("--registry", type=Path, default=DEFAULT_OUTPUT_REGISTRY)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    templates = read_jsonl(args.templates)
    connector_policy = read_json(args.connector_policy)
    rollback_plan = read_jsonl(args.rollback_plan)
    registry = read_json(args.registry)
    validate_redcircle_postponement_policy(
        manifest,
        templates,
        connector_policy,
        rollback_plan,
        registry=registry,
    )
    print(
        "PASS: KMFA S07-P3 Redcircle postponement check passed "
        f"(templates={manifest['summary']['reserved_template_count']}, "
        f"rollback_plans={manifest['summary']['rollback_plan_count']}, "
        "d15_connector_allowed=false, "
        "read_only_required=true, hash_retention_required=true, rollback_plan_required=true, "
        "formal_report_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
