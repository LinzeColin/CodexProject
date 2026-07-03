#!/usr/bin/env python3
"""Validate KMFA v0.1.3 Stage 1-10 GitHub upload gate evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_stage1_10_batch_review import (
    validate_v013_stage1_10_batch_review,
)


DEFAULT_MANIFEST = Path(
    "KMFA/stage_artifacts/V013_STAGE1_10_GITHUB_UPLOAD/machine/"
    "stage1_10_github_upload_manifest.json"
)

REQUIRED_VALIDATION_KEYS = {
    "py_compile",
    "stage1_10_batch_review_validator",
    "s01_s10_stage_review_validators",
    "focused_upload_unit_test",
    "focused_batch_unit_test",
    "full_kmfa_tests",
    "no_float_money_check",
    "no_omission_check",
    "project_governance_validate",
    "lean_governance_validate",
    "governance_sync_validate",
    "structured_parse_checks",
    "yaml_parse_check",
    "raw_private_path_scan",
    "strict_key_shaped_secret_scan",
    "public_safe_evidence_semantic_scan",
    "diff_check",
    "push_dry_run",
    "push",
    "post_push_parity",
}
PUSH_PLACEHOLDER_KEYS = {"push_dry_run", "push", "post_push_parity"}
FORBIDDEN_PUBLIC_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename",
    "member_sha256:",
    "actual_package_sha256:",
    "authoritative_value_cents:",
    "system_value_cents:",
    "pdf_value_cents:",
    "excel_value_cents:",
    "sheet_name:",
    "row_value:",
    "cell_value:",
    "business_data_payload",
    "bank_statement:",
    "contract_full_text:",
    "salary_detail:",
    "tax_filing:",
    "connector_token:",
    "connector_password:",
    "api_key:",
    "private_key:",
    "-----" "BEGIN",
    "s" "k-",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "account_number",
)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"missing JSON file: {path}")
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


def _require_existing_refs(label: str, refs: Any) -> None:
    if not isinstance(refs, list) or not refs:
        raise ValueError(f"{label}: expected non-empty list")
    missing = [ref for ref in refs if not isinstance(ref, str) or not Path(ref).exists()]
    if missing:
        raise ValueError(f"{label}: missing refs: " + ", ".join(map(str, missing)))


def _require_false_flags(label: str, payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict) or not payload:
        raise ValueError(f"{label}: expected non-empty object")
    for key, value in payload.items():
        _require_false(f"{label}.{key}", value)


def _git_rev(ref: str) -> str:
    return subprocess.check_output(["git", "rev-parse", ref], text=True).strip()


def _git_status_short() -> str:
    return subprocess.check_output(["git", "status", "--short"], text=True).strip()


def _git_is_ancestor(ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _validate_no_forbidden_public_text(label: str, payload: Any) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).lower()
    for text in FORBIDDEN_PUBLIC_TEXT:
        if text.lower() in encoded:
            raise ValueError(f"{label}: forbidden public text found: {text}")


def validate_v013_stage1_10_github_upload(
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    require_remote_parity: bool = False,
) -> dict[str, Any]:
    manifest = _read_json(manifest_path)
    _require_equal("schema_version", manifest.get("schema_version"), "kmfa.v013_stage1_10_github_upload_manifest.v1")
    _require_equal("project_id", manifest.get("project_id"), "KMFA")
    _require_equal("version", manifest.get("version"), "0.1.3")
    _require_equal("upload_id", manifest.get("upload_id"), "KMFA-V013-STAGE1-10-GITHUB-UPLOAD-20260703")
    _require_equal("target", manifest.get("target"), "LinzeColin/CodexProject main")
    _require_equal("branch", manifest.get("branch"), "codex/kmfa")
    _require_equal("source_scope", manifest.get("source_scope"), "v0.1.3 Stage 1-10 batch overall review")
    _require_equal("status", manifest.get("status"), "ready_to_push_github_main_public_safe")

    integration = manifest.get("git_integration", {})
    if not isinstance(integration, dict):
        raise ValueError("git_integration: expected object")
    _require_true("git_integration.rebased_onto_origin_main", integration.get("rebased_onto_origin_main"))
    _require_true(
        "git_integration.origin_main_is_ancestor_of_upload_head",
        integration.get("origin_main_is_ancestor_of_upload_head"),
    )
    base = integration.get("upload_base_origin_main")
    reviewed = integration.get("reviewed_stage1_10_batch_commit")
    if not isinstance(base, str) or len(base) != 40:
        raise ValueError("git_integration.upload_base_origin_main must be a full commit hash")
    if not isinstance(reviewed, str) or len(reviewed) != 40:
        raise ValueError("git_integration.reviewed_stage1_10_batch_commit must be a full commit hash")
    if not _git_is_ancestor(base, "HEAD"):
        raise ValueError("origin main base is not an ancestor of HEAD")
    if not _git_is_ancestor(reviewed, "HEAD"):
        raise ValueError("reviewed Stage 1-10 batch commit is not an ancestor of HEAD")

    batch = validate_v013_stage1_10_batch_review()
    review_state = manifest.get("review_state", {})
    if not isinstance(review_state, dict):
        raise ValueError("review_state: expected object")
    _require_equal("review_state.stage_count", review_state.get("stage_count"), batch["stage_count"])
    _require_equal("review_state.open_batch_finding_count", review_state.get("open_batch_finding_count"), 0)
    _require_false(
        "review_state.github_upload_performed_before_this_gate",
        review_state.get("github_upload_performed_before_this_gate"),
    )
    _require_true("review_state.github_upload_ready_next_gate", review_state.get("github_upload_ready_next_gate"))

    decision = manifest.get("decision_state", {})
    if not isinstance(decision, dict):
        raise ValueError("decision_state: expected object")
    _require_false("decision_state.delivery_allowed", decision.get("delivery_allowed"))
    _require_false("decision_state.formal_report_allowed", decision.get("formal_report_allowed"))
    _require_false("decision_state.business_decision_basis_allowed", decision.get("business_decision_basis_allowed"))
    _require_false("decision_state.business_execution_allowed", decision.get("business_execution_allowed"))
    _require_equal("decision_state.current_report_grade", decision.get("current_report_grade"), "D")
    _require_equal("decision_state.current_data_quality_grade", decision.get("current_data_quality_grade"), "Q4")
    _require_equal("decision_state.pending_reconciliation_count", decision.get("pending_reconciliation_count"), 12)
    _require_equal("decision_state.confirmed_resolution_count", decision.get("confirmed_resolution_count"), 0)

    validation = manifest.get("validation_summary", {})
    if not isinstance(validation, dict):
        raise ValueError("validation_summary: expected object")
    missing = sorted(REQUIRED_VALIDATION_KEYS - validation.keys())
    if missing:
        raise ValueError("validation_summary missing keys: " + ", ".join(missing))
    for key in REQUIRED_VALIDATION_KEYS - PUSH_PLACEHOLDER_KEYS:
        if not str(validation[key]).startswith("PASS"):
            raise ValueError(f"validation_summary.{key}: expected PASS-like value")
    for key in PUSH_PLACEHOLDER_KEYS:
        value = str(validation[key])
        if not (value.startswith("PASS") or value.startswith("REQUIRED")):
            raise ValueError(f"validation_summary.{key}: expected PASS or REQUIRED marker")

    _require_existing_refs("source_refs", manifest.get("source_refs"))
    _require_existing_refs("evidence_refs", manifest.get("evidence_refs"))
    _require_false_flags("public_repo_safety", manifest.get("public_repo_safety", {}))
    _require_false_flags("raw_data_boundary", manifest.get("raw_data_boundary", {}))
    out_of_scope = manifest.get("out_of_scope", [])
    if not isinstance(out_of_scope, list):
        raise ValueError("out_of_scope: expected list")
    for item in ("raw value matching", "lineage full check", "formal report", "business execution"):
        if item not in out_of_scope:
            raise ValueError(f"out_of_scope must include {item}")
    _validate_no_forbidden_public_text("v013_stage1_10_github_upload_manifest", manifest)

    if require_remote_parity:
        head = _git_rev("HEAD")
        origin_main = _git_rev("origin/main")
        if head != origin_main:
            raise ValueError(f"remote parity failed: HEAD {head} != origin/main {origin_main}")
        if _git_status_short():
            raise ValueError("remote parity requires a clean worktree")

    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--require-remote-parity", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = validate_v013_stage1_10_github_upload(
            args.manifest,
            require_remote_parity=args.require_remote_parity,
        )
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    parity = "checked" if args.require_remote_parity else "not_requested"
    print(
        "PASS: KMFA v0.1.3 Stage 1-10 GitHub upload gate validated "
        f"(upload_id={manifest['upload_id']}, status={manifest['status']}, "
        f"remote_parity={parity})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
