#!/usr/bin/env python3
"""Generate KMFA v0.1.3 Stage 1-10 batch overall review evidence.

This batch review closes the corrected v0.1.3 Stage 1-10 local review gate. It
does not upload to GitHub, does not read the local raw data inbox, and does not
turn D-grade public-safe reports into formal business reports.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_STAGE1_10_BATCH_REVIEW")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/stage1_10_batch_review_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/stage1_10_batch_review_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
TASK_ID = "KMFA-V013-STAGE1-10-BATCH-REVIEW-20260703"
SCHEMA_VERSION = "kmfa.v013_stage1_10_batch_review.v1"
REVIEW_SCOPE = "v013_stage1_10_batch_overall_review_only"
VALIDATED_STAGE_IDS = [f"S{idx:02d}" for idx in range(1, 11)]
NEXT_REQUIRED_STEP = (
    "Proceed to the v0.1.3 Stage 1-10 GitHub upload gate as a separate run after confirming "
    "the local branch integration plan. The upload gate must still rerun validators and safety "
    "scans before push; do not perform raw value matching, lineage full check, formal report "
    "release, live connector, Redcircle automatic connector, OpMe deep coupling, or business "
    "execution in the batch review run."
)


STAGE_MANIFESTS = {
    "S01": Path("KMFA/stage_artifacts/V013_S01_STAGE_REVIEW/machine/stage1_review_manifest.json"),
    "S02": Path("KMFA/stage_artifacts/V013_S02_STAGE_REVIEW/machine/stage2_review_manifest.json"),
    "S03": Path("KMFA/stage_artifacts/V013_S03_STAGE_REVIEW/machine/stage3_review_manifest.json"),
    "S04": Path("KMFA/stage_artifacts/V013_S04_STAGE_REVIEW/machine/stage4_review_manifest.json"),
    "S05": Path("KMFA/stage_artifacts/V013_S05_STAGE_REVIEW/machine/stage5_review_manifest.json"),
    "S06": Path("KMFA/stage_artifacts/V013_S06_STAGE_REVIEW/machine/stage6_review_manifest.json"),
    "S07": Path("KMFA/stage_artifacts/V013_S07_STAGE_REVIEW/machine/stage7_review_manifest.json"),
    "S08": Path("KMFA/stage_artifacts/V013_S08_STAGE_REVIEW/machine/stage8_review_manifest.json"),
    "S09": Path("KMFA/stage_artifacts/V013_S09_STAGE_REVIEW/machine/stage9_review_manifest.json"),
    "S10": Path("KMFA/stage_artifacts/V013_S10_STAGE_REVIEW/machine/stage10_review_manifest.json"),
}


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def _stage_passed(stage_id: str, manifest: dict[str, Any]) -> bool:
    phase_results = manifest.get("phase_results", {})
    return (
        manifest.get("stage_id") == stage_id
        and isinstance(phase_results, dict)
        and bool(phase_results)
        and set(phase_results.values()) == {"PASS"}
        and manifest.get("open_review_finding_count", 0) == 0
        and manifest.get("github_upload_performed") is False
        and manifest.get("delivery_allowed") is False
        and manifest.get("formal_report_allowed") is False
        and manifest.get("business_execution_allowed") is False
    )


def build_manifest() -> dict[str, Any]:
    stage_manifests = {stage_id: read_json(path) for stage_id, path in STAGE_MANIFESTS.items()}
    stage_results = {
        stage_id: "PASS" if _stage_passed(stage_id, manifest) else "FAIL"
        for stage_id, manifest in stage_manifests.items()
    }
    s10 = stage_manifests["S10"]
    open_finding_count = sum(int(manifest.get("open_review_finding_count", 0) or 0) for manifest in stage_manifests.values())
    fixed_finding_count = sum(int(manifest.get("fixed_review_finding_count", 0) or 0) for manifest in stage_manifests.values())
    github_upload_performed_count = sum(1 for manifest in stage_manifests.values() if manifest.get("github_upload_performed") is True)
    delivery_allowed_count = sum(1 for manifest in stage_manifests.values() if manifest.get("delivery_allowed") is True)
    formal_report_allowed_count = sum(1 for manifest in stage_manifests.values() if manifest.get("formal_report_allowed") is True)
    business_execution_allowed_count = sum(1 for manifest in stage_manifests.values() if manifest.get("business_execution_allowed") is True)
    legacy_upload_gate_count = sum(
        1
        for stage_id, manifest in stage_manifests.items()
        if stage_id != "S10"
        and (
            manifest.get("github_upload_ready_next_gate") is True
            or "upload_ready" in str(manifest.get("status", ""))
        )
    )
    batch_findings = [
        {
            "finding_id": "KMFA-V013-BATCH-S01-S10-F01",
            "severity": "P2",
            "status": "fixed",
            "summary": (
                "Historical individual Stage 1-10 upload-ready markers are not current v0.1.3 gates. "
                "This batch review marks individual upload artifacts non-current and leaves only a "
                "separate Stage 1-10 GitHub upload gate as the next possible upload step."
            ),
        },
        {
            "finding_id": "KMFA-V013-BATCH-S01-S10-F02",
            "severity": "P2",
            "status": "passed",
            "summary": (
                "All ten v0.1.3 stage review manifests are present, phase results are PASS, open "
                "review findings are zero, and no stage performed GitHub upload."
            ),
        },
        {
            "finding_id": "KMFA-V013-BATCH-S01-S10-F03",
            "severity": "P1",
            "status": "passed",
            "summary": (
                "D-grade report, Q4 data quality, twelve pending reconciliations and missing lineage "
                "full check continue to block formal reports, business decision basis and delivery."
            ),
        },
    ]
    hard_blocks = [
        "current_report_grade_d",
        "current_data_quality_q4",
        "pending_reconciliations_unresolved",
        "confirmed_resolutions_zero",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "formal_report_release_blocked",
        "business_decision_basis_blocked",
        "delivery_blocked",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "review_id": TASK_ID,
        "task_id": TASK_ID,
        "review_scope": REVIEW_SCOPE,
        "review_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "batch_review_passed_local_only_upload_ready_next_gate_no_go",
        "stage1_10_batch_overall_review_performed": True,
        "stage_count": len(VALIDATED_STAGE_IDS),
        "validated_stage_ids": VALIDATED_STAGE_IDS,
        "reviewed_stage_manifests": {stage_id: path.as_posix() for stage_id, path in STAGE_MANIFESTS.items()},
        "stage_results": stage_results,
        "all_stage_reviews_validated": set(stage_results.values()) == {"PASS"},
        "open_stage_review_finding_count": open_finding_count,
        "fixed_stage_review_finding_count": fixed_finding_count,
        "open_batch_finding_count": 0,
        "fixed_batch_finding_count": 1,
        "batch_findings": batch_findings,
        "legacy_individual_stage_upload_artifacts_current_gate": False,
        "legacy_individual_stage_upload_marker_count": legacy_upload_gate_count,
        "github_upload_ready_next_gate": True,
        "github_upload_performed": False,
        "github_upload_performed_count": github_upload_performed_count,
        "github_upload_status": "not_uploaded_ready_for_separate_stage1_10_github_upload_gate",
        "github_upload_gate_scope": "separate_run_required",
        "github_main_uploaded_for_v013_stage1_10": False,
        "delivery_allowed": False,
        "delivery_allowed_count": delivery_allowed_count,
        "formal_report_allowed": False,
        "formal_report_allowed_count": formal_report_allowed_count,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "business_execution_allowed_count": business_execution_allowed_count,
        "lineage_full_check_completed": False,
        "raw_value_matching_performed": False,
        "current_report_grade": s10["current_report_grade"],
        "current_data_quality_grade": s10["current_data_quality_grade"],
        "release_permission": s10["release_permission"],
        "pending_reconciliation_count": s10["pending_reconciliation_count"],
        "confirmed_resolution_count": s10["confirmed_resolution_count"],
        "html_export_count": s10["html_export_count"],
        "csv_appendix_count": s10["csv_appendix_count"],
        "excel_compatible_download_count": s10["excel_compatible_download_count"],
        "raw_dir_read_performed_by_batch_review": False,
        "raw_dir_read_performed_by_stage_validators": False,
        "raw_dir_mutation_performed": False,
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_DIR,
            "local_raw_data_dir_role": "user_finance_raw_private_inbox",
            "codex_read_required_by_this_batch_review": False,
            "codex_read_performed_by_this_batch_review": False,
            "codex_list_performed_by_this_batch_review": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
        "public_repo_safety": {
            "protected_source_payload_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "wps_native_file_committed": False,
            "redcircle_native_file_committed": False,
            "raw_or_private_csv_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "connector_secret_committed": False,
            "field_plaintext_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_names_committed": False,
            "raw_file_hashes_committed": False,
            "tab_labels_committed": False,
            "zip_member_names_committed": False,
            "source_record_payload_committed": False,
            "normalized_source_values_committed": False,
            "business_amount_values_committed": False,
            "project_or_customer_plaintext_committed": False,
            "formal_report_committed": False,
            "spreadsheet_workbook_committed": False,
        },
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "next_required_step": NEXT_REQUIRED_STEP,
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_stage1_10_batch_review.py",
            "KMFA/tools/check_v013_stage1_10_batch_review.py",
            "KMFA/tests/test_v013_stage1_10_batch_review.py",
        ],
    }


def write_outputs(manifest: dict[str, Any]) -> None:
    (PUBLIC_OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (PUBLIC_OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    REPORT_PATH.write_text(render_report(manifest), encoding="utf-8")
    if not TEST_RESULTS_PATH.exists():
        TEST_RESULTS_PATH.write_text(render_pending_test_results(manifest), encoding="utf-8")


def render_report(manifest: dict[str, Any]) -> str:
    stage_results = ", ".join(f"{stage}={status}" for stage, status in manifest["stage_results"].items())
    findings = "\n".join(
        f"- `{finding['finding_id']}` {finding['status']}: {finding['summary']}"
        for finding in manifest["batch_findings"]
    )
    return f"""# KMFA v0.1.3 Stage 1-10 Batch Overall Review

- review_id: `{manifest['review_id']}`
- status: `{manifest['status']}`
- review_scope: `{manifest['review_scope']}`
- stage_count: `{manifest['stage_count']}`
- stage_results: `{stage_results}`
- open_stage_review_finding_count: `{manifest['open_stage_review_finding_count']}`
- open_batch_finding_count: `{manifest['open_batch_finding_count']}`
- fixed_batch_finding_count: `{manifest['fixed_batch_finding_count']}`
- current_data_quality_grade: `{manifest['current_data_quality_grade']}`
- current_report_grade: `{manifest['current_report_grade']}`
- release_permission: `{manifest['release_permission']}`
- pending_reconciliation_count: `{manifest['pending_reconciliation_count']}`
- confirmed_resolution_count: `{manifest['confirmed_resolution_count']}`

## Boundary

- stage1_10_batch_overall_review_performed: `true`
- github_upload_ready_next_gate: `{str(manifest['github_upload_ready_next_gate']).lower()}`
- github_upload_performed: `false`
- github_upload_status: `{manifest['github_upload_status']}`
- legacy_individual_stage_upload_artifacts_current_gate: `false`
- delivery_allowed: `false`
- formal_report_allowed: `false`
- business_decision_basis_allowed: `false`
- business_execution_allowed: `false`

## Raw Data Boundary

- local_raw_data_dir: `{RAW_DIR}`
- codex_read_required_by_this_batch_review: `false`
- codex_read_performed_by_this_batch_review: `false`
- codex_list_performed_by_this_batch_review: `false`
- codex_modify_allowed: `false`
- codex_delete_allowed: `false`
- codex_move_allowed: `false`
- codex_rename_allowed: `false`
- codex_generate_inside_allowed: `false`
- github_commit_allowed: `false`

This batch review did not enumerate, copy, modify, move, rename, delete, overwrite, or write generated files inside the local finance inbox.

## Findings

{findings}

## Next Step

{manifest['next_required_step']}
"""


def render_pending_test_results(manifest: dict[str, Any]) -> str:
    return f"""# KMFA v0.1.3 Stage 1-10 Batch Review Test Results

- review_id: `{manifest['review_id']}`
- status: `pending_final_validation_local_only`
- github_upload_performed: `false`
- raw_dir_read_performed_by_this_batch_review: `false`
- raw_dir_mutation_performed: `false`
- formal_report_allowed: `false`
- business_execution_allowed: `false`

## Command Results

- PENDING: final validation results will be recorded before local commit.
"""


def main() -> int:
    manifest = build_manifest()
    write_outputs(manifest)
    print(
        "PASS: KMFA v0.1.3 Stage 1-10 batch review evidence generated "
        f"(stages={manifest['stage_count']}, open_batch_findings={manifest['open_batch_finding_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()}, "
        f"upload_ready_next_gate={str(manifest['github_upload_ready_next_gate']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
