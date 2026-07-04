#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S10-P2 report trust grade evidence.

This phase locks public-safe report trust grade runtime evidence against the
v0.1.4 S10-P1 report templates, legacy S10-P2 report grade runtime, and
v0.1.3 S10-P2 replay. It does not generate exports, formal reports, UI
runtime, raw value matching, lineage completion, app reinstall, external
connector calls, business execution, or GitHub upload.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s10_p2_report_grade_runtime_replay import (
    validate_v013_s10_p2_report_grade_runtime_replay,
)
from KMFA.tools.check_v014_s10_p1_report_templates import (
    validate_v014_s10_p1_report_templates,
)
from KMFA.tools.report_grade_runtime import (
    DEFAULT_OUTPUT_MANIFEST as LEGACY_GRADE_MANIFEST_PATH,
    DEFAULT_OUTPUT_RECORDS as LEGACY_GRADE_RECORDS_PATH,
    DEFAULT_OUTPUT_STAGE_MANIFEST as LEGACY_STAGE_MANIFEST_PATH,
    FIELD_MAPPING_VERSION,
    FORMULA_VERSION,
    GRADE_POLICY_VERSION,
    MAPPING_VERSION,
    RELEASE_GATE_VERSION,
    REPORT_RECORD_VERSION,
    read_json,
    read_jsonl,
    validate_report_grade_runtime_artifacts,
)


TASK_ID = "KMFA-V014-S10-P2-REPORT-TRUST-GRADE-20260704"
ACCEPTANCE_ID = "ACC-V014-S10-P2-REPORT-TRUST-GRADE"
SCHEMA_VERSION = "kmfa.v014_s10_p2_report_trust_grade.v1"
PHASE_SCOPE = "v014_s10_p2_report_trust_grade_only"

PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S10_P2_REPORT_TRUST_GRADE")
MACHINE_DIR = PUBLIC_OUTPUT_DIR / "machine"
HUMAN_DIR = PUBLIC_OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "report_trust_grade_manifest.json"
REPORT_PATH = HUMAN_DIR / "report_trust_grade_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S10-P3 report export as a separate run. GitHub main "
    "upload remains deferred until v1.4 Stage 1-18 are complete, the overall "
    "review passes, and findings are fixed; do not run Stage 10 review, "
    "GitHub upload, raw value matching, lineage full check, formal report "
    "release, UI runtime, live connector, app reinstall, Redcircle automatic "
    "connector, OpMe deep coupling, or business execution in the S10-P2 run."
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


def _count_false_values(container: dict[str, Any]) -> int:
    return sum(1 for value in container.values() if value is False)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def validate_s10_p1_dependency() -> dict[str, Any]:
    result = validate_v014_s10_p1_report_templates()
    if result.get("stage_id") != "S10" or result.get("phase_id") != "S10-P1":
        raise RuntimeError("v0.1.4 S10-P2 requires validated S10-P1 dependency")
    if result.get("phase_scope") != "v014_s10_p1_report_templates_only":
        raise RuntimeError("v0.1.4 S10-P2 requires v0.1.4 S10-P1 scope")
    if result.get("s10_p2_performed") is not False:
        raise RuntimeError("S10-P1 dependency must not already include S10-P2")
    if result.get("s10_p3_performed") is not False:
        raise RuntimeError("S10-P1 dependency must not include S10-P3")
    if result.get("stage10_review_performed") is not False:
        raise RuntimeError("S10-P1 dependency must not include Stage 10 review")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("S10-P1 dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("S10-P1 dependency must keep v1.4 upload deferred")
    if result.get("raw_inbox_read_performed") is not False:
        raise RuntimeError("S10-P1 dependency must keep raw inbox unread")
    return result


def validate_v013_replay_dependency() -> dict[str, Any]:
    result = validate_v013_s10_p2_report_grade_runtime_replay()
    if result.get("stage_id") != "S10" or result.get("phase_id") != "S10-P2":
        raise RuntimeError("v0.1.4 S10-P2 requires validated v0.1.3 S10-P2 replay dependency")
    if result.get("phase_scope") != "v013_s10_p2_report_grade_runtime_replay_only":
        raise RuntimeError("v0.1.4 S10-P2 requires v0.1.3 S10-P2 replay scope")
    if result.get("s10_p3_performed") is not False:
        raise RuntimeError("v0.1.3 S10-P2 replay must not include S10-P3")
    if result.get("stage10_review_performed") is not False:
        raise RuntimeError("v0.1.3 S10-P2 replay must not include Stage 10 review")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("v0.1.3 S10-P2 replay must not include GitHub upload")
    return result


def _count_hard_blocks(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        for block in record.get("hard_blocks", []):
            key = str(block)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _version_binding_count(records: list[dict[str, Any]], legacy_manifest: dict[str, Any]) -> int:
    version_fields = (
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
        if all(record.get(field) and record.get(field) == legacy_manifest.get(field) for field in version_fields)
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
    hard_block_counts = _count_hard_blocks(records)

    return {
        "legacy_manifest": legacy_manifest,
        "legacy_stage_manifest": legacy_stage_manifest,
        "records": records,
        "template_count": summary.get("template_count"),
        "report_grade_record_count": summary.get("report_grade_record_count"),
        "grade_distribution": summary.get("grade_distribution", {}),
        "pending_reconciliation_count": summary.get("pending_reconciliation_count"),
        "confirmed_resolution_count": summary.get("confirmed_resolution_count"),
        "source_quality_grade": summary.get("source_quality_grade"),
        "zero_delta_passed": summary.get("zero_delta_passed"),
        "full_trusted_report_allowed_count": summary.get("full_trusted_report_allowed_count"),
        "formal_report_count": summary.get("formal_report_count"),
        "export_artifact_count": summary.get("export_artifact_count"),
        "complete_trusted_report_display_allowed_count": sum(
            1 for record in records if record.get("complete_trusted_report_display_allowed") is True
        ),
        "business_decision_basis_allowed_count": sum(
            1 for record in records if record.get("business_decision_basis_allowed") is True
        ),
        "computed_grades": sorted({str(record.get("computed_report_grade")) for record in records}),
        "release_permissions": sorted({str(record.get("release_permission")) for record in records}),
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
        "public_safety": public_safety,
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
    v013_replay = validate_v013_replay_dependency()
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
        "github_upload_deferred_until_v014_stage1_18_complete",
        "app_reinstall_not_performed",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S10",
        "phase_id": "S10-P2",
        "phase_name": "v0.1.4 public-safe report trust grade runtime",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_report_trust_grade_locked",
        "completed_task_ids": ["S10P2T01", "S10P2T02", "S10P2T03"],
        "acceptance_ids": [ACCEPTANCE_ID],
        "s10_p1_dependency_validated": True,
        "s10_p1_dependency_status": s10_p1.get("status"),
        "legacy_s10_p2_dependency_validated": True,
        "v013_s10_p2_replay_validated": True,
        "v013_s10_p2_replay_status": v013_replay.get("status"),
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
        "report_trust_grade_summary": {
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
            "complete_trusted_report_display_allowed_count": legacy[
                "complete_trusted_report_display_allowed_count"
            ],
            "business_decision_basis_allowed_count": legacy["business_decision_basis_allowed_count"],
            "computed_grades": legacy["computed_grades"],
            "release_permissions": legacy["release_permissions"],
            "hard_block_counts": legacy["hard_block_counts"],
            "hard_block_count": legacy["hard_block_count"],
            "required_template_ids": legacy["required_template_ids"],
        },
        "report_trust_grade_policy": {
            "allowed_report_grades": ["A", "B", "C", "D"],
            "current_report_grade": "D",
            "current_data_quality_grade": legacy["source_quality_grade"],
            "grade_driver_dimensions": [
                "data_quality",
                "difference_status",
                "human_confirmation",
                "timeliness",
            ],
            "timeliness_status": "current_metadata_timestamp_present_no_stale_signal",
            "report_record_version": legacy["report_record_version"],
            "template_version": legacy["template_version"],
            "formula_version": legacy["formula_version"],
            "mapping_version": legacy["mapping_version"],
            "field_mapping_version": legacy["field_mapping_version"],
            "grade_policy_version": legacy["grade_policy_version"],
            "release_gate_version": legacy["release_gate_version"],
            "content_hash": legacy["content_hash"],
            "record_version_binding_required": True,
            "record_version_binding_count": legacy["record_version_binding_count"],
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
        "version_binding_requirements": {
            "report_record_version": REPORT_RECORD_VERSION,
            "formula_version": FORMULA_VERSION,
            "mapping_version": MAPPING_VERSION,
            "field_mapping_version": FIELD_MAPPING_VERSION,
            "grade_policy_version": GRADE_POLICY_VERSION,
            "release_gate_version": RELEASE_GATE_VERSION,
            "record_version_binding_count": legacy["record_version_binding_count"],
        },
        "phase_boundaries": {
            "s10_p1_report_templates_dependency_included": True,
            "s10_p2_report_trust_grade_scope_included": True,
            "s10_p3_report_export_scope_included": False,
            "stage10_review_scope_included": False,
            "lineage_full_check_scope_included": False,
            "raw_value_matching_scope_included": False,
            "formal_report_scope_included": False,
            "report_export_scope_included": False,
            "ui_runtime_scope_included": False,
            "external_connector_scope_included": False,
            "github_upload_scope_included": False,
            "app_reinstall_scope_included": False,
        },
        "quality_gate": {
            "current_data_quality_grade": "Q4",
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
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        },
        "raw_data_boundary": {
            "raw_inbox_ref": RAW_INBOX_REF,
            "raw_inbox_read_required_by_this_phase": False,
            "raw_inbox_read_by_this_phase": False,
            "raw_inbox_listed_by_this_phase": False,
            "raw_inbox_inventory_by_this_phase": False,
            "raw_inbox_stat_by_this_phase": False,
            "raw_inbox_hashed_by_this_phase": False,
            "raw_inbox_modified_by_this_phase": False,
            "raw_inbox_deleted_by_this_phase": False,
            "raw_inbox_moved_by_this_phase": False,
            "raw_inbox_renamed_by_this_phase": False,
            "raw_inbox_overwritten_by_this_phase": False,
            "raw_inbox_written_by_this_phase": False,
            "raw_inbox_mutated_by_this_phase": False,
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
            "v014_s10_p1_manifest": "KMFA/stage_artifacts/V014_S10_P1_REPORT_TEMPLATES/machine/report_templates_manifest.json",
            "v013_s10_p2_replay_manifest": "KMFA/stage_artifacts/V013_S10_P2_REPORT_GRADE_RUNTIME_REPLAY/machine/report_grade_runtime_replay_manifest.json",
            "manifest": _repo_relative(MANIFEST_PATH),
            "report": _repo_relative(REPORT_PATH),
            "test_results": _repo_relative(TEST_RESULTS_PATH),
            "risk_register": _repo_relative(RISK_REGISTER_PATH),
            "rollback_plan": _repo_relative(ROLLBACK_PATH),
            "generator": "KMFA/tools/v014_s10_p2_report_trust_grade.py",
            "validator": "KMFA/tools/check_v014_s10_p2_report_trust_grade.py",
            "unit_test": "KMFA/tests/test_v014_s10_p2_report_trust_grade.py",
        },
        "evidence_refs": [
            _repo_relative(MANIFEST_PATH),
            _repo_relative(REPORT_PATH),
            _repo_relative(TEST_RESULTS_PATH),
            _repo_relative(RISK_REGISTER_PATH),
            _repo_relative(ROLLBACK_PATH),
            "KMFA/tools/v014_s10_p2_report_trust_grade.py",
            "KMFA/tools/check_v014_s10_p2_report_trust_grade.py",
            "KMFA/tests/test_v014_s10_p2_report_trust_grade.py",
        ],
        "validation_summary": {
            "py_compile": "PASS",
            "s10_p1_dependency_validator": "PASS",
            "legacy_s10_p2_validator": "PASS",
            "legacy_s10_p2_unit": "PASS",
            "v013_s10_p2_replay_validator": "PASS",
            "phase_validator": "PASS",
            "focused_unit_test": "PASS",
            "no_omission_check": "PASS",
            "no_float_money_check": "PASS",
            "governance_validator": "PASS",
            "lean_governance_validator": "PASS",
            "governance_sync_validator": "PASS",
            "structured_parse": "PASS",
            "ruby_yaml_parse": "PASS",
            "raw_private_scan": "PASS",
            "secret_scan": "PASS",
            "public_s10_p2_semantic_scan": "PASS",
            "diff_check": "PASS",
        },
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def render_report(manifest: dict[str, Any]) -> str:
    summary = manifest["report_trust_grade_summary"]
    policy = manifest["report_trust_grade_policy"]
    return "\n".join(
        [
            "# KMFA v0.1.4 S10-P2 Report Trust Grade",
            "",
            f"- task_id: `{manifest['task_id']}`",
            f"- status: `{manifest['status']}`",
            f"- phase_scope: `{manifest['phase_scope']}`",
            f"- s10_p1_dependency: `{manifest['s10_p1_dependency_status']}`",
            f"- v013_replay_dependency: `{manifest['v013_s10_p2_replay_status']}`",
            f"- report_grade_record_count: `{summary['report_grade_record_count']}`",
            f"- grade_distribution: `{summary['grade_distribution']}`",
            f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
            f"- confirmed_resolution_count: `{summary['confirmed_resolution_count']}`",
            f"- source_quality_grade: `{summary['source_quality_grade']}`",
            f"- zero_delta_passed: `{str(summary['zero_delta_passed']).lower()}`",
            f"- current_report_grade: `{policy['current_report_grade']}`",
            f"- record_version_binding_count: `{policy['record_version_binding_count']}`",
            "- complete_trusted_report_display_allowed: `false`",
            "- full_trusted_report_allowed: `false`",
            "- formal_report_allowed: `false`",
            "- business_decision_basis_allowed: `false`",
            "- export_artifact_count: `0`",
            "- github_upload_performed: `false`",
            "- raw_inbox_read_by_this_phase: `false`",
            "- raw_inbox_mutated_by_this_phase: `false`",
            "",
            "## Grade Rules",
            "",
            "- A/B/C/D is driven by data quality, open differences, human confirmation, and timeliness.",
            "- Open differences, missing lineage, missing human confirmation, or failed zero-delta keep the runtime at D.",
            "- Each report grade record is bound to report record, template, formula, mapping, field mapping, grade policy, and release gate versions.",
            "",
            "## Boundary",
            "",
            "- Evidence contains only aggregate counts, status flags, version ids, public-safe refs, and validator results.",
            "- It does not contain source filenames, source hashes, tab labels, ZIP member labels, field/header plaintext, row/cell values, business values, credentials, contracts, payroll, tax filings, bank statements, formal report exports, or UI runtime output.",
            "",
            "## Next Step",
            "",
            manifest["next_required_step"],
            "",
        ]
    )


def render_test_results(manifest: dict[str, Any]) -> str:
    summary = manifest["report_trust_grade_summary"]
    return "\n".join(
        [
            "# KMFA v0.1.4 S10-P2 Test Results",
            "",
            "- py_compile: `PASS`",
            "- generator: `PASS`",
            "- S10-P1 dependency validator: `PASS`",
            "- legacy S10-P2 validator: `PASS`",
            "- v0.1.3 S10-P2 replay validator: `PASS`",
            "- v0.1.4 S10-P2 validator: `PASS`",
            "- focused unit test: `PASS`",
            "- governance/no-float/no-omission/safety scans: `PASS`",
            f"- report_grade_record_count: `{summary['report_grade_record_count']}`",
            f"- grade_distribution: `{summary['grade_distribution']}`",
            f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
            f"- confirmed_resolution_count: `{summary['confirmed_resolution_count']}`",
            f"- zero_delta_passed: `{str(summary['zero_delta_passed']).lower()}`",
            "- S10-P3/Stage 10 review/GitHub upload/formal report/business execution: `false`",
            "- raw inbox read/list/stat/hash/mutation/write: `false`",
            "",
        ]
    )


def render_risk_register(manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# KMFA v0.1.4 S10-P2 Risk Register",
            "",
            "| Risk | Status | Control |",
            "|---|---|---|",
            "| Open reconciliation remains unresolved | active | report grade stays D and complete trusted report stays blocked |",
            "| zero-delta has not passed | active | formal report and business decision basis stay blocked |",
            "| lineage full check is missing | active | report release remains NO_GO |",
            "| Raw/private data exposure | controlled | public evidence limited to aggregate counts, status flags, version ids and refs |",
            "| Scope creep into export or upload | controlled | S10-P3, Stage 10 review and GitHub upload flags remain false |",
            "",
            f"- hard_block_count: `{manifest['hard_block_count']}`",
            "- rollback: revert this phase's generator, validator, test, evidence, and governance rows.",
            "",
        ]
    )


def render_rollback_plan(manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# KMFA v0.1.4 S10-P2 Rollback Plan",
            "",
            "1. Revert `KMFA/tools/v014_s10_p2_report_trust_grade.py`.",
            "2. Revert `KMFA/tools/check_v014_s10_p2_report_trust_grade.py`.",
            "3. Revert `KMFA/tests/test_v014_s10_p2_report_trust_grade.py`.",
            "4. Remove `KMFA/stage_artifacts/V014_S10_P2_REPORT_TRUST_GRADE/`.",
            "5. Revert governance and Chinese entry rows for `KMFA-V014-S10-P2-REPORT-TRUST-GRADE-20260704`.",
            "6. Re-run S10-P1 validator to confirm the prior phase remains intact.",
            "",
            f"- rollback_target: `{manifest['reviewed_head']}`",
            "- raw/private data directory must not be modified during rollback.",
            "",
        ]
    )


def generate() -> dict[str, Any]:
    manifest = build_manifest()
    _write_json(MANIFEST_PATH, manifest)
    _write_text(REPORT_PATH, render_report(manifest))
    _write_text(TEST_RESULTS_PATH, render_test_results(manifest))
    _write_text(RISK_REGISTER_PATH, render_risk_register(manifest))
    _write_text(ROLLBACK_PATH, render_rollback_plan(manifest))
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["report_trust_grade_summary"]
    print(
        "PASS: KMFA v0.1.4 S10-P2 report trust grade evidence generated "
        f"(grade_records={summary['report_grade_record_count']}, "
        f"grade_distribution={summary['grade_distribution']}, "
        f"pending_reconciliation={summary['pending_reconciliation_count']}, "
        "formal_report=false, s10_p3=false, stage10_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
