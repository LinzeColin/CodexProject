#!/usr/bin/env python3
"""Validate the KMFA final NO_GO governance backup upload evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path(
    "KMFA/stage_artifacts/FINAL_GITHUB_BACKUP/machine/final_no_go_backup_upload_manifest.json"
)

FORBIDDEN_PUBLIC_TEXT = (
    "raw_value",
    "normalized_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "private://",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "recipient_email",
    "smtp",
    "sk-",
    "-----BEGIN",
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def _require_true(label: str, actual: Any) -> None:
    if actual is not True:
        raise ValueError(f"{label}: expected true, got {actual!r}")


def _require_false(label: str, actual: Any) -> None:
    if actual is not False:
        raise ValueError(f"{label}: expected false, got {actual!r}")


def _require_non_empty_list(label: str, value: Any) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label}: expected non-empty list")
    return value


def _require_existing_refs(label: str, refs: Any) -> None:
    missing = [
        ref
        for ref in _require_non_empty_list(label, refs)
        if not isinstance(ref, str) or not Path(ref).exists()
    ]
    if missing:
        raise ValueError(f"{label}: missing refs: " + ", ".join(map(str, missing)))


def _require_false_flags(label: str, payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict) or not payload:
        raise ValueError(f"{label}: expected non-empty object")
    for key, value in payload.items():
        _require_false(f"{label}.{key}", value)


def _validate_no_forbidden_public_text(label: str, payload: Any) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for text in FORBIDDEN_PUBLIC_TEXT:
        if text in encoded:
            raise ValueError(f"{label}: forbidden public text found: {text}")


def _git_rev(ref: str) -> str:
    return subprocess.check_output(["git", "rev-parse", ref], text=True).strip()


def _git_status_short() -> str:
    return subprocess.check_output(["git", "status", "--short"], text=True).strip()


def validate_final_no_go_backup_upload(
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    require_remote_parity: bool = False,
) -> dict[str, Any]:
    manifest = _read_json(manifest_path)
    _require_equal("schema_version", manifest.get("schema_version"), "kmfa.final_no_go_backup_upload_manifest.v1")
    _require_equal("project_id", manifest.get("project_id"), "KMFA")
    _require_equal("upload_id", manifest.get("upload_id"), "KMFA-FINAL-GITHUB-BACKUP-NO-GO-20260702")
    _require_equal("status", manifest.get("status"), "uploaded_to_github_main_no_go_governance_backup_only")
    _require_equal("target", manifest.get("target"), "LinzeColin/CodexProject main")
    _require_equal("branch", manifest.get("branch"), "codex/kmfa")

    decision = manifest.get("decision_state", {})
    if not isinstance(decision, dict):
        raise ValueError("decision_state: expected object")
    _require_equal("decision_state.go_no_go", decision.get("go_no_go"), "NO_GO")
    _require_false("decision_state.delivery_allowed", decision.get("delivery_allowed"))
    _require_false("decision_state.formal_report_allowed", decision.get("formal_report_allowed"))
    _require_false("decision_state.release_claim_allowed", decision.get("release_claim_allowed"))
    _require_false("decision_state.business_execution_allowed", decision.get("business_execution_allowed"))
    _require_equal("decision_state.pending_reconciliation_count", decision.get("pending_reconciliation_count"), 12)
    _require_equal("decision_state.actual_lineage_rows", decision.get("actual_lineage_rows"), 0)
    _require_equal("decision_state.report_grade_distribution", decision.get("report_grade_distribution"), {"D": 2})

    policy = manifest.get("backup_policy", {})
    if not isinstance(policy, dict):
        raise ValueError("backup_policy: expected object")
    _require_true("backup_policy.no_go_governance_backup_only", policy.get("no_go_governance_backup_only"))
    _require_false("backup_policy.delivery_claim_allowed", policy.get("delivery_claim_allowed"))
    _require_false("backup_policy.release_claim_allowed", policy.get("release_claim_allowed"))
    _require_false("backup_policy.formal_report_claim_allowed", policy.get("formal_report_claim_allowed"))
    if len(_require_non_empty_list("backup_policy.required_conditions", policy.get("required_conditions"))) < 6:
        raise ValueError("backup_policy.required_conditions: expected at least six conditions")

    validation = manifest.get("validation_summary", {})
    if not isinstance(validation, dict):
        raise ValueError("validation_summary: expected object")
    required_validation_keys = {
        "lineage_report_gate",
        "whole_project_final_review",
        "lineage_completeness",
        "report_grade_gate",
        "worktree_cleanup",
        "full_kmfa_tests",
        "lean_governance_validate",
        "project_governance_validate",
        "governance_sync_validate",
        "parse_checks",
        "raw_private_path_scan",
        "high_signal_secret_scan",
        "diff_check",
        "push_dry_run",
        "push",
        "post_push_parity",
    }
    missing = sorted(required_validation_keys - validation.keys())
    if missing:
        raise ValueError("validation_summary missing keys: " + ", ".join(missing))
    for key in required_validation_keys - {"push", "post_push_parity"}:
        if not str(validation[key]).startswith("PASS"):
            raise ValueError(f"validation_summary.{key}: expected PASS-like value")

    _require_existing_refs("source_refs", manifest.get("source_refs"))
    _require_existing_refs("evidence_refs", manifest.get("evidence_refs"))
    _require_false_flags("public_repo_safety", manifest.get("public_repo_safety", {}))
    if "release" not in manifest.get("out_of_scope", []):
        raise ValueError("out_of_scope must include release")
    _validate_no_forbidden_public_text("final_no_go_backup_upload_manifest", manifest)

    if require_remote_parity:
        head = _git_rev("HEAD")
        origin_main = _git_rev("origin/main")
        if head != origin_main:
            raise ValueError(f"remote parity failed: HEAD {head} != origin/main {origin_main}")
        if _git_status_short():
            raise ValueError("remote parity requires a clean worktree")

    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA final NO_GO backup upload evidence.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--require-remote-parity", action="store_true")
    args = parser.parse_args(argv)

    try:
        manifest = validate_final_no_go_backup_upload(
            args.manifest,
            require_remote_parity=args.require_remote_parity,
        )
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    parity = "checked" if args.require_remote_parity else "not_requested"
    print(
        "PASS: KMFA final NO_GO governance backup upload evidence is public-safe "
        f"(upload_id={manifest['upload_id']}, go_no_go=NO_GO, delivery_allowed=false, "
        f"remote_parity={parity})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
