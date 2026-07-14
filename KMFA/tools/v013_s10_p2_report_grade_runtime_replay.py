#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S10-P2 report grade runtime replay evidence.

This replay validates the v0.1.3 S10-P1 dependency, reuses the existing
public-safe S10-P2 report grade runtime artifacts, and records the phase-level
no-go / upload-deferred boundary for the v0.1.3 Stage 1-10 run. It does not
generate exports, formal reports, or business-decision outputs.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s10_p1_report_templates_replay import (
    validate_v013_s10_p1_report_templates_replay,
)
from KMFA.tools.report_grade_runtime import (
    DEFAULT_OUTPUT_MANIFEST as LEGACY_GRADE_MANIFEST_PATH,
    DEFAULT_OUTPUT_RECORDS as LEGACY_GRADE_RECORDS_PATH,
    DEFAULT_OUTPUT_STAGE_MANIFEST as LEGACY_STAGE_MANIFEST_PATH,
    GRADE_POLICY_VERSION,
    MAPPING_VERSION,
    RELEASE_GATE_VERSION,
    REPORT_RECORD_VERSION,
    FIELD_MAPPING_VERSION,
    FORMULA_VERSION,
    read_json,
    read_jsonl,
    validate_report_grade_runtime_artifacts,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S10_P2_REPORT_GRADE_RUNTIME_REPLAY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/report_grade_runtime_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/report_grade_runtime_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
TASK_ID = "KMFA-V013-S10-P2-REPORT-GRADE-RUNTIME-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s10_p2_report_grade_runtime_replay.v1"
PHASE_SCOPE = "v013_s10_p2_report_grade_runtime_replay_only"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S10-P3 as a separate run. GitHub main upload remains deferred until "
    "v0.1.3 Stages 1-10 are complete, the whole Stage 1-10 review passes, and findings are fixed; "
    "do not run Stage 10 review, GitHub upload, raw value matching, lineage full check, "
    "formal report release, live connector, Redcircle automatic connector, or business execution "
    "in the S10-P2 run."
)


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


def _repo_relative(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def validate_s10_p1_dependency() -> dict[str, Any]:
    result = validate_v013_s10_p1_report_templates_replay()
    if result.get("stage_id") != "S10" or result.get("phase_id") != "S10-P1":
        raise RuntimeError("v0.1.3 S10-P2 requires validated S10-P1 dependency")
    if result.get("phase_scope") != "v013_s10_p1_report_templates_replay_only":
        raise RuntimeError("v0.1.3 S10-P2 requires v0.1.3 S10-P1 replay scope")
    if result.get("s10_p2_performed") is not False:
        raise RuntimeError("S10-P1 dependency must not already include S10-P2")
    if result.get("s10_p3_performed") is not False:
        raise RuntimeError("S10-P1 dependency must not include S10-P3")
    if result.get("stage10_review_performed") is not False:
        raise RuntimeError("S10-P1 dependency must not include Stage 10 review")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("S10-P1 dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_stage10_batch") is not True:
        raise RuntimeError("S10-P1 dependency must keep upload deferred")
    return result


def _count_false_values(container: dict[str, Any]) -> int:
    return sum(1 for value in container.values() if value is False)


def _count_hard_blocks(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        for block in record.get("hard_blocks", []):
            key = str(block)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _version_binding_count(records: list[dict[str, Any]], legacy_manifest: dict[str, Any]) -> int:
    version_fields = (
        "report_record_version",
        "template_version",
        "formula_version",
        "mapping_version",
        "field_mapping_version",
        "grade_policy_version",
        "release_gate_version",
    )
    return sum(
        1
        for record in records
        if all(record.get(field) and record.get(field) == legacy_manifest.get(field) for field in version_fields[1:])
        and record.get("report_record_version") == REPORT_RECORD_VERSION
        and record.get("template_content_hash") == legacy_manifest.get("upstream_template_content_hash")
    )


def validate_legacy_s10_p2_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_GRADE_MANIFEST_PATH)
    records = read_jsonl(LEGACY_GRADE_RECORDS_PATH)
    legacy_stage_manifest = read_json(LEGACY_STAGE_MANIFEST_PATH)
    validate_report_grade_runtime_artifacts(legacy_manifest, records)

    summary = legacy_manifest.get("summary", {})
    quality_gate = legacy_manifest.get("quality_gate", {})
    stage_scope = legacy_manifest.get("stage_scope", {})
    public_safety = legacy_manifest.get("public_repo_safety", {})
    grade_distribution = summary.get("grade_distribution", {})
    hard_block_counts = _count_hard_blocks(records)
    computed_grades = sorted({str(record.get("computed_report_grade")) for record in records})
    release_permissions = sorted({str(record.get("release_permission")) for record in records})

    return {
        "legacy_manifest": legacy_manifest,
        "legacy_stage_manifest": legacy_stage_manifest,
        "records": records,
        "template_count": summary.get("template_count"),
        "report_grade_record_count": summary.get("report_grade_record_count"),
        "grade_distribution": grade_distribution,
        "pending_reconciliation_count": summary.get("pending_reconciliation_count"),
        "confirmed_resolution_count": summary.get("confirmed_resolution_count"),
        "source_quality_grade": summary.get("source_quality_grade"),
        "zero_delta_passed": summary.get("zero_delta_passed"),
        "full_trusted_report_allowed_count": summary.get("full_trusted_report_allowed_count"),
        "formal_report_count": summary.get("formal_report_count"),
        "export_artifact_count": summary.get("export_artifact_count"),
        "computed_grades": computed_grades,
        "release_permissions": release_permissions,
        "hard_block_counts": hard_block_counts,
        "hard_block_count": sum(hard_block_counts.values()),
        "record_version_binding_count": _version_binding_count(records, legacy_manifest),
        "required_template_ids": legacy_manifest.get("required_template_ids", []),
        "report_record_version": legacy_manifest.get("report_record_version"),
        "template_version": legacy_manifest.get("template_version"),
        "formula_version": legacy_manifest.get("formula_version"),
        "mapping_version": legacy_manifest.get("mapping_version"),
        "field_mapping_version": legacy_manifest.get("field_mapping_version"),
        "grade_policy_version": legacy_manifest.get("grade_policy_version"),
        "release_gate_version": legacy_manifest.get("release_gate_version"),
        "content_hash": legacy_manifest.get("content_hash"),
        "quality_gate": quality_gate,
        "stage_scope": stage_scope,
        "public_repo_safety": public_safety,
        "quality_gate_false_count": _count_false_values(quality_gate),
        "stage_scope_false_count": _count_false_values(stage_scope),
        "public_safety_false_count": _count_false_values(public_safety),
        "artifact_refs": {
            "legacy_manifest": _repo_relative(LEGACY_GRADE_MANIFEST_PATH),
            "legacy_records": _repo_relative(LEGACY_GRADE_RECORDS_PATH),
            "legacy_stage_manifest": _repo_relative(LEGACY_STAGE_MANIFEST_PATH),
            "legacy_completion_record": "KMFA/stage_artifacts/S10_P2_report_grade_runtime/human/s10_p2_completion_record.md",
            "legacy_test_results": "KMFA/stage_artifacts/S10_P2_report_grade_runtime/human/test_results.md",
        },
    }


def build_manifest() -> dict[str, Any]:
    s10_p1 = validate_s10_p1_dependency()
    legacy = validate_legacy_s10_p2_artifacts()
    hard_blocks = [
        "zero_delta_failed",
        "unresolved_critical_difference",
        "missing_required_lineage",
        "missing_human_confirmation_for_A",
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "complete_trusted_report_display_blocked",
        "formal_report_release_blocked",
        "business_decision_basis_blocked",
        "s10_p3_export_not_performed",
        "stage10_review_not_performed",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_stage10_batch",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S10",
        "phase_id": "S10-P2",
        "phase_name": "v0.1.3 public-safe report grade runtime replay",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_report_grade_runtime_replayed",
        "completed_task_ids": ["S10PBT01", "S10PBT02", "S10PBT03"],
        "acceptance_ids": ["ACC-V013-S10-P2-REPORT-GRADE-RUNTIME-REPLAY"],
        "s10_p1_dependency_validated": True,
        "s10_p1_dependency_status": s10_p1.get("status"),
        "legacy_s10_p2_dependency_validated": True,
        "stage10_phase_progress": {
            "completed_phase_count": 2,
            "total_phase_count": 3,
            "derived_percent_bps": 6667,
            "derived_percent_label": "66.67%",
            "s10_p1_performed": True,
            "s10_p2_performed": True,
            "s10_p3_performed": False,
            "stage10_review_performed": False,
        },
        "legacy_s10_p2_summary": {
            "template_count": legacy["template_count"],
            "report_grade_record_count": legacy["report_grade_record_count"],
            "grade_distribution": legacy["grade_distribution"],
            "pending_reconciliation_count": legacy["pending_reconciliation_count"],
            "confirmed_resolution_count": legacy["confirmed_resolution_count"],
            "source_quality_grade": legacy["source_quality_grade"],
            "zero_delta_passed": legacy["zero_delta_passed"],
            "full_trusted_report_allowed_count": legacy["full_trusted_report_allowed_count"],
            "formal_report_count": legacy["formal_report_count"],
            "export_artifact_count": legacy["export_artifact_count"],
            "computed_grades": legacy["computed_grades"],
            "release_permissions": legacy["release_permissions"],
            "hard_block_counts": legacy["hard_block_counts"],
            "hard_block_count": legacy["hard_block_count"],
            "required_template_ids": legacy["required_template_ids"],
        },
        "report_grade_runtime_policy": {
            "allowed_report_grades": ["A", "B", "C", "D"],
            "current_report_grade": "D",
            "current_data_quality_grade": legacy["source_quality_grade"],
            "report_record_version": legacy["report_record_version"],
            "template_version": legacy["template_version"],
            "formula_version": legacy["formula_version"],
            "mapping_version": legacy["mapping_version"],
            "field_mapping_version": legacy["field_mapping_version"],
            "grade_policy_version": legacy["grade_policy_version"],
            "release_gate_version": legacy["release_gate_version"],
            "expected_report_record_version": REPORT_RECORD_VERSION,
            "expected_formula_version": FORMULA_VERSION,
            "expected_mapping_version": MAPPING_VERSION,
            "expected_field_mapping_version": FIELD_MAPPING_VERSION,
            "expected_grade_policy_version": GRADE_POLICY_VERSION,
            "expected_release_gate_version": RELEASE_GATE_VERSION,
            "record_version_binding_required": True,
            "record_version_binding_count": legacy["record_version_binding_count"],
            "content_hash": legacy["content_hash"],
            "complete_trusted_report_display_allowed": False,
            "full_trusted_report_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "s10_p3_export_allowed": False,
            "report_runtime_scope_count": legacy["report_grade_record_count"],
            "quality_gate_false_count": legacy["quality_gate_false_count"],
            "stage_scope_false_count": legacy["stage_scope_false_count"],
            "public_safety_false_count": legacy["public_safety_false_count"],
        },
        "phase_boundaries": {
            "s10_p1_report_templates_dependency_included": True,
            "s10_p2_report_grade_runtime_scope_included": True,
            "s10_p3_report_export_scope_included": False,
            "stage10_review_scope_included": False,
            "lineage_full_check_scope_included": False,
            "raw_value_matching_scope_included": False,
            "formal_report_scope_included": False,
            "report_export_scope_included": False,
            "ui_scope_included": False,
            "external_connector_scope_included": False,
            "github_upload_scope_included": False,
        },
        "quality_gate": {
            "current_data_quality_grade": legacy["source_quality_grade"],
            "current_report_grade": "D",
            "release_permission": "blocked",
            "pending_reconciliation_count": legacy["pending_reconciliation_count"],
            "confirmed_resolution_count": legacy["confirmed_resolution_count"],
            "zero_delta_passed": legacy["zero_delta_passed"],
            "complete_trusted_report_display_allowed": False,
            "full_trusted_report_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "business_execution_allowed": False,
            "delivery_allowed": False,
            "raw_layer_write_allowed": False,
            "automatic_external_action_allowed": False,
            "s10_p3_export_allowed": False,
            "html_export_allowed": False,
            "csv_excel_export_allowed": False,
            "pdf_export_allowed": False,
        },
        "github_upload": {
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_stage10_batch": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_stage10_batch",
        },
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_DIR,
            "local_raw_data_dir_role": "user_finance_raw_private_inbox",
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_required_by_this_phase": False,
            "codex_read_performed_by_this_phase": False,
            "codex_list_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "codex_create_extra_files_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
        "public_repo_safety": {
            "protected_source_payload_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "wps_native_file_committed": False,
            "redcircle_native_file_committed": False,
            "csv_committed": False,
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
            "report_export_committed": False,
            "html_report_export_committed": False,
            "spreadsheet_report_export_committed": False,
        },
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "artifact_refs": {
            **legacy["artifact_refs"],
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "generator": "KMFA/tools/v013_s10_p2_report_grade_runtime_replay.py",
            "validator": "KMFA/tools/check_v013_s10_p2_report_grade_runtime_replay.py",
            "unit_test": "KMFA/tests/test_v013_s10_p2_report_grade_runtime_replay.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s10_p2_report_grade_runtime_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s10_p2_report_grade_runtime_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s10_p2_report_grade_runtime_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s10_p2_report_grade_runtime.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_report_grade_runtime -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s10_p1_report_templates_replay.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s10_p2_report_grade_runtime_replay.py",
            "KMFA/tools/check_v013_s10_p2_report_grade_runtime_replay.py",
            "KMFA/tests/test_v013_s10_p2_report_grade_runtime_replay.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["legacy_s10_p2_summary"]
    policy = manifest["report_grade_runtime_policy"]
    quality = manifest["quality_gate"]
    lines = [
        "# KMFA v0.1.3 S10-P2 Report Grade Runtime Replay",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.3 S10-P1 report templates replay PASS`",
        "- legacy_s10_p2_dependency_validated: `true`",
        f"- template_count: `{summary['template_count']}`",
        f"- report_grade_record_count: `{summary['report_grade_record_count']}`",
        f"- grade_distribution: `{summary['grade_distribution']}`",
        f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
        f"- confirmed_resolution_count: `{summary['confirmed_resolution_count']}`",
        f"- source_quality_grade: `{summary['source_quality_grade']}`",
        f"- zero_delta_passed: `{str(summary['zero_delta_passed']).lower()}`",
        f"- full_trusted_report_allowed_count: `{summary['full_trusted_report_allowed_count']}`",
        f"- formal_report_count: `{summary['formal_report_count']}`",
        f"- export_artifact_count: `{summary['export_artifact_count']}`",
        f"- report_record_version: `{policy['report_record_version']}`",
        f"- formula_version: `{policy['formula_version']}`",
        f"- mapping_version: `{policy['mapping_version']}`",
        f"- field_mapping_version: `{policy['field_mapping_version']}`",
        f"- record_version_binding_count: `{policy['record_version_binding_count']}`",
        "",
        "## Boundary",
        "",
        "- s10_p2_report_grade_runtime_scope_included: `true`",
        "- s10_p3_report_export_scope_included: `false`",
        "- stage10_review_scope_included: `false`",
        "- github_upload_deferred_until_stage10_batch: `true`",
        "- github_upload_performed: `false`",
        "- complete_trusted_report_display_allowed: `false`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- business_execution_allowed: `false`",
        f"- current_report_grade: `{quality['current_report_grade']}`",
        f"- release_permission: `{quality['release_permission']}`",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{RAW_DIR}`",
        "- local_raw_data_dir_role: `user_finance_raw_private_inbox`",
        "- codex_read_required_by_this_phase: `false`",
        "- codex_read_performed_by_this_phase: `false`",
        "- codex_list_performed_by_this_phase: `false`",
        "- codex_modify_allowed: `false`",
        "- codex_delete_allowed: `false`",
        "- codex_move_allowed: `false`",
        "- codex_rename_allowed: `false`",
        "- codex_generate_inside_allowed: `false`",
        "- codex_create_extra_files_inside_allowed: `false`",
        "- github_commit_allowed: `false`",
        "",
        (
            "This phase did not enumerate, copy, modify, move, rename, delete, overwrite, "
            "or write generated files inside the local finance inbox. It only replayed "
            "public-safe report grade runtime metadata already present in the repository."
        ),
        "",
        "## Public Safety",
        "",
        (
            "Evidence contains only report grades, version bindings, aggregate counts, "
            "hard-block codes, validator references, quality blockers, and governance paths."
        ),
        (
            "It does not contain source filenames, source hashes from the private inbox, tab labels, "
            "ZIP member names, field/header plaintext, row values, business amount values, credentials, "
            "contracts, payroll, tax filings, or bank statements."
        ),
        "",
        "## Next Step",
        "",
        manifest["next_required_step"],
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_test_results() -> None:
    lines = [
        "# KMFA v0.1.3 S10-P2 Report Grade Runtime Replay Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed_by_this_phase: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- s10_p3_performed: `false`",
        "- stage10_review_performed: `false`",
        "- raw_value_matching_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Command Results",
        "",
        "- PENDING: final validation results will be recorded before local commit.",
        "",
    ]
    TEST_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def generate() -> dict[str, Any]:
    (PUBLIC_OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (PUBLIC_OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_test_results()
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["legacy_s10_p2_summary"]
    print(
        "PASS: KMFA v0.1.3 S10-P2 report grade runtime replay generated "
        f"(grade_records={summary['report_grade_record_count']}, "
        f"grade_distribution={summary['grade_distribution']}, "
        f"pending_reconciliations={summary['pending_reconciliation_count']}, "
        "s10p3=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
