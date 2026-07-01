#!/usr/bin/env python3
"""Validate KMFA S17-P1 access/security public-safe artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.access_security_policy import (
    DEFAULT_OUTPUT_AUDIT_POLICY,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_ROLE_MATRIX,
    DEFAULT_OUTPUT_SENSITIVE_POLICY,
    read_json,
    read_jsonl,
    validate_access_security_policy_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S17-P1 access/security artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--role-matrix", type=Path, default=DEFAULT_OUTPUT_ROLE_MATRIX)
    parser.add_argument("--sensitive-policy", type=Path, default=DEFAULT_OUTPUT_SENSITIVE_POLICY)
    parser.add_argument("--audit-policy", type=Path, default=DEFAULT_OUTPUT_AUDIT_POLICY)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    role_matrix = read_jsonl(args.role_matrix)
    sensitive_policies = read_jsonl(args.sensitive_policy)
    audit_policies = read_jsonl(args.audit_policy)

    validate_access_security_policy_artifacts(
        manifest,
        role_matrix,
        sensitive_policies,
        audit_policies,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S17-P1 access/security check passed "
        f"(roles={summary['role_count']}, "
        f"sensitive_categories={summary['sensitive_policy_category_count']}, "
        f"audit_actions={summary['audit_action_type_count']}, "
        "raw_sensitive_public_repo=false, notification_delivery=false, "
        "stage17_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
