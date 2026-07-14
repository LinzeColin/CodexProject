#!/usr/bin/env python3
"""Validate KMFA v0.1.3 Stage 1 review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s01_p1_preflight import validate_s01_p1_preflight
from KMFA.tools.check_v013_s01_p2_scope_freeze import validate_s01_p2_scope_freeze
from KMFA.tools.check_v013_s01_p3_no_omission_gate import validate_s01_p3_no_omission_gate


MANIFEST_PATH = Path("KMFA/stage_artifacts/V013_S01_STAGE_REVIEW/machine/stage1_review_manifest.json")
REPORT_PATH = Path("KMFA/stage_artifacts/V013_S01_STAGE_REVIEW/human/stage1_review_report.md")
TEST_RESULTS_PATH = Path("KMFA/stage_artifacts/V013_S01_STAGE_REVIEW/human/test_results.md")
PHASE_MANIFESTS = {
    "S01-P1": Path("KMFA/stage_artifacts/V013_S01_PRECHECK/machine/s01_p1_preflight_manifest.json"),
    "S01-P2": Path("KMFA/stage_artifacts/V013_S01_SCOPE_FREEZE/machine/s01_p2_scope_freeze_manifest.json"),
    "S01-P3": Path("KMFA/stage_artifacts/V013_S01_NO_OMISSION_GATE/machine/s01_p3_no_omission_gate_manifest.json"),
}
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value",
    "normalized_value",
    "source_header_text",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "-----BEGIN",
    "sk-",
)
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
    "field_plaintext_committed",
    "normalized_business_values_committed",
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


def validate_v013_s01_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    p1_result = validate_s01_p1_preflight()
    p2_result = validate_s01_p2_scope_freeze()
    p3_result = validate_s01_p3_no_omission_gate()

    require(manifest.get("schema_version") == "kmfa.v013_s01_stage_review.v1", "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("stage_id") == "S01", "stage_id must be S01")
    require(manifest.get("review_id") == "KMFA-V013-S01-STAGE-REVIEW-20260702", "review_id mismatch")
    require(manifest.get("task_id") == "KMFA-V013-S01-STAGE-REVIEW-20260702", "task_id mismatch")
    require(manifest.get("review_scope") == "v013_s01_stage_review_only", "review scope mismatch")
    require(manifest.get("stage_review_performed") is True, "stage review must be performed")
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(manifest.get("delivery_allowed") is False, "delivery_allowed must remain false")
    require(manifest.get("formal_report_allowed") is False, "formal_report_allowed must remain false")
    require(manifest.get("business_execution_allowed") is False, "business_execution_allowed must remain false")
    require(manifest.get("lineage_full_check_completed") is False, "lineage full check must not be completed")
    require(manifest.get("phase_count") == 3, "phase_count must be 3")
    require(manifest.get("open_review_finding_count") == 0, "open review findings must be 0")
    require(manifest.get("fixed_review_finding_count") == 0, "fixed review findings must be 0")
    require(manifest.get("review_findings") == [], "review findings must be empty")
    require(
        manifest.get("next_required_step") == "Stage 1 GitHub upload gate after rebase and review evidence binding.",
        "next_required_step mismatch",
    )

    phase_results = manifest.get("phase_results", {})
    require(phase_results == {"S01-P1": "PASS", "S01-P2": "PASS", "S01-P3": "PASS"}, "phase_results mismatch")
    require(p1_result.get("stage_phase") == "S01-P1", "S01-P1 validator did not return S01-P1")
    require(p2_result.get("stage_phase") == "S01-P2", "S01-P2 validator did not return S01-P2")
    require(p3_result.get("stage_phase") == "S01-P3", "S01-P3 validator did not return S01-P3")
    require(p1_result.get("delivery_allowed") is False, "S01-P1 delivery gate mismatch")
    require(p2_result.get("delivery_allowed") is False, "S01-P2 delivery gate mismatch")
    require(p3_result.get("delivery_allowed") is False, "S01-P3 delivery gate mismatch")

    inherited = manifest.get("inherited_no_go_blockers", {})
    require(inherited.get("actual_lineage_rows") == 0, "actual_lineage_rows must remain 0")
    require(inherited.get("pending_reconciliation_count") == 12, "pending reconciliation count must remain 12")
    require(inherited.get("d_grade_report_count") == 2, "D grade report count must remain 2")
    require(inherited.get("delivery_allowed") is False, "inherited delivery_allowed must be false")

    counts = manifest.get("no_omission_counts", {})
    p3_counts = p3_result.get("no_omission", {})
    require(counts.get("requirements") == p3_counts.get("requirements") == 20, "requirements count mismatch")
    require(counts.get("p0") == p3_counts.get("p0") == 9, "P0 count mismatch")
    require(counts.get("p1") == p3_counts.get("p1") == 8, "P1 count mismatch")
    require(counts.get("stage_status_records") == p3_counts.get("stage_status_records") == 549, "stage status count mismatch")
    require(counts.get("task_records") == p3_counts.get("task_records") == 162, "task count mismatch")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == "/Users/linzezhang/Downloads/KMFA_MetaData", "raw directory mismatch")
    require(raw_boundary.get("codex_modify_allowed") is False, "raw directory modify must be false")
    require(raw_boundary.get("codex_delete_allowed") is False, "raw directory delete must be false")
    require(raw_boundary.get("codex_move_allowed") is False, "raw directory move must be false")
    require(raw_boundary.get("github_commit_allowed") is False, "raw directory commit must be false")

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    reviewed_phase_manifests = manifest.get("reviewed_phase_manifests", {})
    for phase, path in PHASE_MANIFESTS.items():
        require(reviewed_phase_manifests.get(phase) == str(path), f"{phase} manifest ref mismatch")
        require(path.exists(), f"missing phase manifest: {path}")
    for ref in manifest.get("evidence_refs", []):
        ref_path = Path(ref)
        require(ref_path.exists(), f"missing evidence ref: {ref}")
    for evidence in (REPORT_PATH, TEST_RESULTS_PATH):
        require(evidence.exists(), f"missing human evidence: {evidence}")
        if evidence.exists():
            text = evidence.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_EVIDENCE_TEXT:
                require(forbidden not in text, f"forbidden evidence text {forbidden!r} in {evidence}")

    status = git_output(["status", "--short", "--branch"])
    require("codex/kmfa" in status, "git status must be on codex/kmfa")

    if errors:
        raise ValidationError("\n".join(errors))

    return {
        "task_id": manifest["task_id"],
        "stage_id": manifest["stage_id"],
        "review_scope": manifest["review_scope"],
        "phase_count": manifest["phase_count"],
        "phase_results": phase_results,
        "stage_review_performed": manifest["stage_review_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "fixed_review_finding_count": manifest["fixed_review_finding_count"],
        "inherited_no_go_blockers": inherited,
        "no_omission_counts": counts,
        "next_required_step": manifest["next_required_step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 Stage 1 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_v013_s01_stage_review(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 Stage 1 review validation failed")
        print(exc)
        return 1
    blockers = result["inherited_no_go_blockers"]
    counts = result["no_omission_counts"]
    print(
        "PASS: KMFA v0.1.3 Stage 1 review remains local-only NO_GO "
        f"(phases={result['phase_count']}, findings_open={result['open_review_finding_count']}, "
        f"actual_lineage_rows={blockers['actual_lineage_rows']}, "
        f"pending_reconciliation={blockers['pending_reconciliation_count']}, "
        f"grade_D={blockers['d_grade_report_count']}, requirements={counts['requirements']}, "
        f"github_upload={str(result['github_upload_performed']).lower()}, "
        f"delivery_allowed={str(result['delivery_allowed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
