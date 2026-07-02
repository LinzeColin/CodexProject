#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S01-P2 scope-freeze evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


MANIFEST_PATH = Path("KMFA/stage_artifacts/V013_S01_SCOPE_FREEZE/machine/s01_p2_scope_freeze_manifest.json")
S01_P1_MANIFEST = Path("KMFA/stage_artifacts/V013_S01_PRECHECK/machine/s01_p1_preflight_manifest.json")
V12_ROADMAP = Path("KMFA/taskpack/v1_2/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md")
EXTERNAL_V013_ROADMAP = Path("/Users/linzezhang/Downloads/10_Codex_v0_1_3_Roadmap_STAGE_PHASE_TASK.md")
LOCAL_RAW_DATA_DIR = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
EVIDENCE_FILES = [
    Path("KMFA/stage_artifacts/V013_S01_SCOPE_FREEZE/human/scope_freeze_record.md"),
    Path("KMFA/stage_artifacts/V013_S01_SCOPE_FREEZE/human/non_scope_and_guardrails.md"),
    Path("KMFA/stage_artifacts/V013_S01_SCOPE_FREEZE/human/test_results.md"),
]
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


def validate_s01_p2_scope_freeze(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s01_p1 = read_json(S01_P1_MANIFEST)

    require(manifest.get("schema_version") == "kmfa.v013_s01_p2_scope_freeze.v1", "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "manifest project_id mismatch")
    require(manifest.get("stage_phase") == "S01-P2", "manifest stage_phase must be S01-P2")
    require(manifest.get("task_id") == "KMFA-V013-S01-P2-SCOPE-FREEZE-20260702", "task_id mismatch")
    require(manifest.get("phase_scope") == "scope_freeze_only", "phase_scope mismatch")
    require(manifest.get("scope_freeze_status") == "frozen_local_no_go", "scope freeze status mismatch")
    require(manifest.get("current_version_file_value") == "0.1.0-post-s18-final-no-go-backup-upload", "VERSION file value mismatch")
    require(manifest.get("target_fix_version") == "0.1.3-internal-mvp-candidate", "target fix version mismatch")
    require(manifest.get("external_v013_roadmap_available") == EXTERNAL_V013_ROADMAP.exists(), "external roadmap availability mismatch")
    require(manifest.get("external_v013_roadmap_available") is False, "external v0.1.3 roadmap must be recorded as unavailable")
    require(str(EXTERNAL_V013_ROADMAP) in manifest.get("external_v013_roadmap_path", ""), "external roadmap path not recorded")
    require(V12_ROADMAP.exists(), "v1.2 roadmap source missing")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == str(LOCAL_RAW_DATA_DIR), "raw data directory mismatch")
    require(LOCAL_RAW_DATA_DIR.exists(), "local raw data directory must exist")
    require(raw_boundary.get("codex_read_allowed_when_task_requires") is True, "raw data read boundary mismatch")
    require(raw_boundary.get("codex_modify_allowed") is False, "Codex must not modify raw data directory")
    require(raw_boundary.get("codex_delete_allowed") is False, "Codex must not delete raw data directory")
    require(raw_boundary.get("codex_move_allowed") is False, "Codex must not move raw data directory files")
    require(raw_boundary.get("github_commit_allowed") is False, "raw data directory must not be committed")
    require(raw_boundary.get("codex_private_workspace") == "KMFA/.codex_private_runtime/", "Codex private workspace mismatch")

    inherited = manifest.get("inherited_blockers", {})
    s01_p1_blockers = s01_p1.get("blocker_counts", {})
    for key, expected in (
        ("actual_lineage_rows", 0),
        ("pending_reconciliation_count", 12),
        ("d_grade_report_count", 2),
    ):
        require(inherited.get(key) == expected, f"inherited blocker {key} mismatch")
        require(s01_p1_blockers.get(key) == expected, f"S01-P1 blocker {key} mismatch")

    require(manifest.get("delivery_allowed") is False, "delivery_allowed must remain false")
    require(manifest.get("formal_report_allowed") is False, "formal_report_allowed must remain false")
    require(manifest.get("business_execution_allowed") is False, "business_execution_allowed must remain false")
    require(manifest.get("stage_review_scope_included") is False, "stage review must not be included")
    require(manifest.get("github_upload_this_phase") is False, "GitHub upload must not be included")
    require(manifest.get("lineage_full_check_completed") is False, "lineage full check must not be completed")
    require(manifest.get("raw_business_data_committed") is False, "raw business data must not be committed")
    require(manifest.get("zip_committed") is False, "zip files must not be committed")
    require(manifest.get("excel_workbook_committed") is False, "Excel workbooks must not be committed")
    require(manifest.get("pdf_committed") is False, "PDF files must not be committed")
    require(manifest.get("private_csv_committed") is False, "private CSV files must not be committed")
    require(manifest.get("credentials_committed") is False, "credentials must not be committed")

    next_step = manifest.get("next_required_step")
    require(next_step == "S01-P3; do not execute Stage 1 review or GitHub upload before all S01 phases pass.", "next step mismatch")

    frozen_scope = manifest.get("frozen_scope", {})
    require("S01-P2 freezes scope only; it does not resolve blockers." in frozen_scope.get("scope_statements", []), "scope statement missing")
    require("Stage 1 review" in frozen_scope.get("non_scope_items", []), "Stage 1 review non-scope missing")
    require("GitHub upload" in frozen_scope.get("non_scope_items", []), "GitHub upload non-scope missing")
    require("formal report release" in frozen_scope.get("non_scope_items", []), "formal report non-scope missing")

    for ref in manifest.get("source_evidence_refs", []):
        ref_path = Path(ref)
        require(ref_path.exists(), f"missing source evidence ref: {ref}")
    for evidence in EVIDENCE_FILES:
        require(evidence.exists(), f"missing human evidence: {evidence}")
        text = evidence.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_EVIDENCE_TEXT:
            require(forbidden not in text, f"forbidden evidence text {forbidden!r} in {evidence}")

    status = git_output(["status", "--short", "--branch"])
    require("codex/kmfa" in status, "git status must be on codex/kmfa")

    if errors:
        raise ValidationError("\n".join(errors))

    return {
        "task_id": manifest["task_id"],
        "stage_phase": manifest["stage_phase"],
        "phase_scope": manifest["phase_scope"],
        "scope_freeze_status": manifest["scope_freeze_status"],
        "inherited_blockers": inherited,
        "delivery_allowed": manifest["delivery_allowed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "stage_review_scope_included": manifest["stage_review_scope_included"],
        "github_upload_this_phase": manifest["github_upload_this_phase"],
        "external_v013_roadmap_available": manifest["external_v013_roadmap_available"],
        "raw_data_boundary": raw_boundary,
        "next_required_step": manifest["next_required_step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S01-P2 scope-freeze evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_s01_p2_scope_freeze(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 S01-P2 scope-freeze validation failed")
        print(exc)
        return 1
    inherited = result["inherited_blockers"]
    print(
        "PASS: KMFA v0.1.3 S01-P2 scope freeze remains local NO_GO "
        f"(actual_lineage_rows={inherited['actual_lineage_rows']}, "
        f"pending_reconciliation={inherited['pending_reconciliation_count']}, "
        f"grade_D={inherited['d_grade_report_count']}, "
        f"delivery_allowed={str(result['delivery_allowed']).lower()}, "
        f"stage_review={str(result['stage_review_scope_included']).lower()}, "
        f"github_upload={str(result['github_upload_this_phase']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
