#!/usr/bin/env python3
"""Validate KMFA v1.4 S01-P1 read-only scope lock evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S01_P1_READ_ONLY_SCOPE_LOCK/machine/"
    "s01_p1_read_only_scope_lock_manifest.json"
)
EVIDENCE_FILES = [
    Path("KMFA/stage_artifacts/V014_S01_P1_READ_ONLY_SCOPE_LOCK/human/implementation_plan.md"),
    Path("KMFA/stage_artifacts/V014_S01_P1_READ_ONLY_SCOPE_LOCK/human/files_to_read.md"),
    Path("KMFA/stage_artifacts/V014_S01_P1_READ_ONLY_SCOPE_LOCK/human/files_to_modify.md"),
    Path("KMFA/stage_artifacts/V014_S01_P1_READ_ONLY_SCOPE_LOCK/human/rollback_plan.md"),
    Path("KMFA/stage_artifacts/V014_S01_P1_READ_ONLY_SCOPE_LOCK/human/risk_register.md"),
    Path("KMFA/stage_artifacts/V014_S01_P1_READ_ONLY_SCOPE_LOCK/human/stop_conditions.md"),
    Path("KMFA/stage_artifacts/V014_S01_P1_READ_ONLY_SCOPE_LOCK/human/test_results.md"),
]
FORBIDDEN_EVIDENCE_TEXT = (
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
)


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_v014_s01_p1_read_only_scope_lock(
    manifest_path: Path = MANIFEST_PATH,
    *,
    require_source_package_present: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)

    require(manifest.get("schema_version") == "kmfa.v014_s01_p1_read_only_scope_lock.v1", "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version must be 0.1.4", errors)
    require(manifest.get("stage_phase") == "S01-P1", "stage_phase must be S01-P1", errors)
    require(
        manifest.get("task_id") == "KMFA-V014-S01-P1-READ-ONLY-SCOPE-LOCK-20260703",
        "task_id mismatch",
        errors,
    )
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred",
        "status mismatch",
        errors,
    )

    package = manifest.get("source_package", {})
    require(isinstance(package, dict), "source_package must be object", errors)
    package_path = Path(str(package.get("path", "")))
    package_sha = str(package.get("sha256", ""))
    require(len(package_sha) == 64, "source package sha256 must be full hash", errors)
    require(package.get("private_raw_directory_members_excluded") is True, "private raw members must be excluded", errors)
    require(package.get("raw_private_member_names_committed") is False, "raw private member names must not be committed", errors)
    require(package.get("zip_or_raw_payload_committed") is False, "zip or raw payload must not be committed", errors)
    if require_source_package_present:
        require(package_path.exists(), f"source package missing: {package_path}", errors)
        if package_path.exists():
            require(sha256_file(package_path) == package_sha, "source package sha256 mismatch", errors)

    public_sources = manifest.get("selected_public_sources", [])
    require(isinstance(public_sources, list) and len(public_sources) >= 8, "selected public sources incomplete", errors)
    labels = {str(item.get("label", "")) for item in public_sources if isinstance(item, dict)}
    for label in (
        "v1.4 taskpack",
        "v1.4 roadmap",
        "v1.4 HTML human-flow audit report",
        "v1.4 raw data roots policy",
        "v1.4 Codex read-only raw-data prompt",
    ):
        require(label in labels, f"missing selected public source label: {label}", errors)

    scope = manifest.get("scope_lock", {})
    require(scope.get("current_phase_only") is True, "current_phase_only must be true", errors)
    require(scope.get("phase_scope") == "read_only_plan_and_scope_lock", "phase scope mismatch", errors)
    require(scope.get("business_code_modified") is False, "business code must not be modified", errors)
    require(scope.get("product_runtime_modified") is False, "product runtime must not be modified", errors)
    require(scope.get("github_upload_this_phase") is False, "github upload must be false", errors)
    require(scope.get("stage_review_this_phase") is False, "stage review must be false", errors)
    require(scope.get("next_phase") == "S01-P2", "next phase must be S01-P2", errors)
    require(scope.get("next_phase_started") is False, "next phase must not be started", errors)

    path_policy = manifest.get("path_policy", {})
    require("main_worktree/CodexProject/kmfa" in str(path_policy.get("canonical_worktree_path", "")), "canonical worktree path mismatch", errors)
    require(path_policy.get("standalone_or_old_path_used") is False, "old or standalone path must not be used", errors)
    require(path_policy.get("new_worktree_created") is False, "new worktree must not be created", errors)

    gates = manifest.get("v14_gates", {})
    require(gates.get("raw_data_root") == "/Users/linzezhang/Downloads/KMFA_MetaData", "raw data root mismatch", errors)
    require(gates.get("raw_data_root_mode") == "read_only", "raw data root mode mismatch", errors)
    require(gates.get("html_audit_pass") == 54, "HTML audit pass count must be 54", errors)
    require(gates.get("html_audit_warn") == 0, "HTML audit warn count must be 0", errors)
    require(gates.get("html_audit_fail") == 0, "HTML audit fail count must be 0", errors)
    require(gates.get("s02_s03_raw_readonly_contract_required") is True, "S02/S03 raw contract gate missing", errors)
    require(gates.get("s10_s11_s12_human_flow_required") is True, "S10/S11/S12 human-flow gate missing", errors)

    raw_boundary = manifest.get("raw_data_boundary", {})
    if not isinstance(raw_boundary, dict):
        errors.append("raw_data_boundary must be object")
    else:
        for key, value in raw_boundary.items():
            require(value is False, f"raw_data_boundary.{key} must be false", errors)

    release = manifest.get("release_state", {})
    for key in ("delivery_allowed", "formal_report_allowed", "business_decision_basis_allowed", "business_execution_allowed"):
        require(release.get(key) is False, f"release_state.{key} must be false", errors)
    require(release.get("current_report_grade") == "D", "report grade must remain D", errors)
    require(release.get("release_permission") == "blocked", "release permission must remain blocked", errors)

    for evidence in EVIDENCE_FILES:
        require(evidence.exists(), f"missing evidence file: {evidence}", errors)
        if evidence.exists():
            text = evidence.read_text(encoding="utf-8").lower()
            for forbidden in FORBIDDEN_EVIDENCE_TEXT:
                require(forbidden.lower() not in text, f"forbidden evidence text {forbidden!r} in {evidence}", errors)

    status = git_output(["status", "--short", "--branch"])
    require("codex/kmfa" in status, "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--require-source-package-present", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_s01_p1_read_only_scope_lock(
            args.manifest,
            require_source_package_present=args.require_source_package_present,
        )
    except ValidationError as exc:
        print("FAIL: KMFA v1.4 S01-P1 read-only scope lock validation failed")
        print(exc)
        return 1
    gates = manifest["v14_gates"]
    print(
        "PASS: KMFA v1.4 S01-P1 read-only scope lock validated "
        f"(task_id={manifest['task_id']}, html_audit={gates['html_audit_pass']}/"
        f"{gates['html_audit_warn']}/{gates['html_audit_fail']}, "
        f"raw_read={str(manifest['raw_data_boundary']['raw_inbox_read_by_this_phase']).lower()}, "
        f"github_upload={str(manifest['scope_lock']['github_upload_this_phase']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
