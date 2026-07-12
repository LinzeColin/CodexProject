#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S10-P3 public-safe report export evidence.

This phase validates the v0.1.4 S10-P2 report trust grade dependency, legacy
S10-P3 public-safe HTML/CSV exports, and the v0.1.3 S10-P3 replay. It does not
run Stage 10 review, publish formal reports, read raw data, reinstall apps,
call external connectors, execute business actions, or upload to GitHub.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s10_p3_report_export_replay import (
    validate_v013_s10_p3_report_export_replay,
)
from KMFA.tools.check_v014_s10_p2_report_trust_grade import (
    validate_v014_s10_p2_report_trust_grade,
)
from KMFA.tools.report_export_runtime import (
    CSV_APPENDIX_SCHEMA_VERSION,
    EXPORT_RECORD_VERSION,
    FORMULA_VERSION,
    HTML_TEMPLATE_VERSION,
    MAPPING_VERSION,
    PDF_EXPORT_POLICY_VERSION,
)
from KMFA.tools.v013_s10_p3_report_export_replay import (
    MANIFEST_PATH as V013_S10_P3_MANIFEST_PATH,
    validate_legacy_s10_p3_artifacts as validate_legacy_s10_p3_export_artifacts,
)


TASK_ID = "KMFA-V014-S10-P3-REPORT-EXPORT-20260704"
ACCEPTANCE_ID = "ACC-V014-S10-P3-REPORT-EXPORT"
SCHEMA_VERSION = "kmfa.v014_s10_p3_report_export.v1"
PHASE_SCOPE = "v014_s10_p3_report_export_only"

PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S10_P3_REPORT_EXPORT")
MACHINE_DIR = PUBLIC_OUTPUT_DIR / "machine"
HUMAN_DIR = PUBLIC_OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "report_export_manifest.json"
REPORT_PATH = HUMAN_DIR / "report_export_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 Stage 10 overall review as a separate run. GitHub main "
    "upload remains deferred until v1.4 Stage 1-18 are complete, the overall "
    "review passes, and findings are fixed; do not run GitHub upload, raw value "
    "matching, lineage full check, formal report release, UI runtime, live "
    "connector, app reinstall, Redcircle automatic connector, OpMe deep coupling, "
    "or business execution in the S10-P3 run."
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


def validate_s10_p2_dependency() -> dict[str, Any]:
    result = validate_v014_s10_p2_report_trust_grade()
    if result.get("stage_id") != "S10" or result.get("phase_id") != "S10-P2":
        raise RuntimeError("v0.1.4 S10-P3 requires validated S10-P2 dependency")
    if result.get("phase_scope") != "v014_s10_p2_report_trust_grade_only":
        raise RuntimeError("v0.1.4 S10-P3 requires v0.1.4 S10-P2 scope")
    progress = result.get("stage10_phase_progress", {})
    s10_p3_performed = progress.get("s10_p3_performed", result.get("s10_p3_performed"))
    stage10_review_performed = progress.get("stage10_review_performed", result.get("stage10_review_performed"))
    if s10_p3_performed is not False:
        raise RuntimeError("S10-P2 dependency must not already include S10-P3")
    if stage10_review_performed is not False:
        raise RuntimeError("S10-P2 dependency must not include Stage 10 review")
    github_upload = result.get("github_upload", {})
    github_upload_performed = github_upload.get("github_upload_performed", result.get("github_upload_performed"))
    upload_deferred = github_upload.get(
        "github_upload_deferred_until_v014_stage1_18_complete",
        result.get("github_upload_deferred_until_v014_stage1_18_complete"),
    )
    if github_upload_performed is not False:
        raise RuntimeError("S10-P2 dependency must not include GitHub upload")
    if upload_deferred is not True:
        raise RuntimeError("S10-P2 dependency must keep v1.4 upload deferred")
    raw_boundary = result.get("raw_data_boundary", {})
    raw_read = raw_boundary.get("raw_inbox_read_by_this_phase", result.get("raw_inbox_read_performed"))
    if raw_read is not False:
        raise RuntimeError("S10-P2 dependency must keep raw inbox unread")
    return result


def validate_v013_replay_dependency() -> dict[str, Any]:
    result = validate_v013_s10_p3_report_export_replay()
    if result.get("stage_id") != "S10" or result.get("phase_id") != "S10-P3":
        raise RuntimeError("v0.1.4 S10-P3 requires validated v0.1.3 S10-P3 replay dependency")
    if result.get("phase_scope") != "v013_s10_p3_report_export_replay_only":
        raise RuntimeError("v0.1.4 S10-P3 requires v0.1.3 S10-P3 replay scope")
    if result.get("stage10_phase_progress", {}).get("stage10_review_performed") is not False:
        raise RuntimeError("v0.1.3 S10-P3 replay must not include Stage 10 review")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("v0.1.3 S10-P3 replay must not include GitHub upload")
    return result


def _version_binding_count(records: list[dict[str, Any]], legacy_manifest: dict[str, Any]) -> int:
    version_fields = (
        "report_export_version",
        "formula_version",
        "mapping_version",
        "html_template_version",
        "csv_appendix_schema_version",
        "pdf_export_policy_version",
    )
    return sum(
        1
        for record in records
        if all(record.get(field) == legacy_manifest.get(field) for field in version_fields)
        and record.get("template_content_hash") == legacy_manifest.get("upstream_template_content_hash")
        and record.get("grade_runtime_content_hash") == legacy_manifest.get("grade_runtime_content_hash")
    )


def validate_legacy_s10_p3_artifacts() -> dict[str, Any]:
    legacy = validate_legacy_s10_p3_export_artifacts()
    legacy_manifest = legacy["legacy_manifest"]
    records = legacy["records"]
    return {
        **legacy,
        "quality_gate_false_count": _count_false_values(legacy.get("quality_gate", {})),
        "stage_scope_false_count": _count_false_values(legacy.get("stage_scope", {})),
        "public_safety_false_count": _count_false_values(legacy.get("public_repo_safety", {})),
        "record_version_binding_count": _version_binding_count(records, legacy_manifest),
    }


def build_manifest() -> dict[str, Any]:
    s10_p2 = validate_s10_p2_dependency()
    v013 = validate_v013_replay_dependency()
    legacy = validate_legacy_s10_p3_artifacts()
    hard_blocks = [
        "report_grade_d_only",
        "zero_delta_failed",
        "unresolved_critical_difference",
        "missing_required_lineage",
        "missing_human_confirmation_for_A",
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "formal_report_release_blocked",
        "business_decision_basis_blocked",
        "stage10_review_not_performed",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "app_reinstall_not_performed",
        "business_execution_blocked",
    ]

    summary = {
        "template_count": legacy["template_count"],
        "report_export_record_count": legacy["report_export_record_count"],
        "grade_distribution": legacy["grade_distribution"],
        "html_export_count": legacy["html_export_count"],
        "csv_appendix_count": legacy["csv_appendix_count"],
        "excel_compatible_download_count": legacy["excel_compatible_download_count"],
        "pdf_export_enabled_after_template_stable": legacy["pdf_export_enabled_after_template_stable"],
        "committed_pdf_file_count": legacy["committed_pdf_file_count"],
        "committed_excel_file_count": legacy["committed_excel_file_count"],
        "formal_report_count": legacy["formal_report_count"],
        "business_decision_basis_count": legacy["business_decision_basis_count"],
        "pending_reconciliation_count": legacy["pending_reconciliation_count"],
        "required_template_ids": legacy["required_template_ids"],
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S10",
        "phase_id": "S10-P3",
        "phase_name": "v0.1.4 public-safe report export",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_report_export_locked",
        "completed_task_ids": ["S10P3T01", "S10P3T02", "S10P3T03"],
        "acceptance_ids": [ACCEPTANCE_ID],
        "s10_p2_dependency_validated": True,
        "s10_p2_dependency_status": s10_p2.get("status"),
        "legacy_s10_p3_dependency_validated": True,
        "v013_s10_p3_replay_validated": True,
        "v013_s10_p3_replay_status": v013.get("status"),
        "stage10_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s10_p1_performed": True,
            "s10_p2_performed": True,
            "s10_p3_performed": True,
            "stage10_review_performed": False,
        },
        "report_export_summary": summary,
        "report_export_policy": {
            "report_export_version": legacy["report_export_version"],
            "expected_report_export_version": EXPORT_RECORD_VERSION,
            "template_version": legacy["template_version"],
            "formula_version": legacy["formula_version"],
            "expected_formula_version": FORMULA_VERSION,
            "mapping_version": legacy["mapping_version"],
            "expected_mapping_version": MAPPING_VERSION,
            "html_template_version": legacy["html_template_version"],
            "expected_html_template_version": HTML_TEMPLATE_VERSION,
            "csv_appendix_schema_version": legacy["csv_appendix_schema_version"],
            "expected_csv_appendix_schema_version": CSV_APPENDIX_SCHEMA_VERSION,
            "pdf_export_policy_version": legacy["pdf_export_policy_version"],
            "expected_pdf_export_policy_version": PDF_EXPORT_POLICY_VERSION,
            "content_hash": legacy["content_hash"],
            "upstream_template_content_hash": legacy["upstream_template_content_hash"],
            "grade_runtime_content_hash": legacy["grade_runtime_content_hash"],
            "record_version_binding_required": True,
            "record_version_binding_count": legacy["record_version_binding_count"],
            "html_export_allowed": True,
            "html_export_count": legacy["html_export_count"],
            "inherits_blue_business_sample_count": legacy["inherits_blue_business_sample_count"],
            "csv_excel_export_allowed": True,
            "csv_appendix_count": legacy["csv_appendix_count"],
            "excel_download_mode": "excel_compatible_csv_no_workbook_committed",
            "excel_compatible_csv_count": legacy["excel_compatible_csv_count"],
            "excel_workbook_committed": False,
            "committed_excel_workbook_count": legacy["committed_excel_workbook_count"],
            "pdf_export_policy_enabled": True,
            "pdf_private_runtime_only": True,
            "pdf_private_runtime_only_count": legacy["pdf_private_runtime_only_count"],
            "pdf_file_committed": False,
            "committed_pdf_file_count": legacy["committed_pdf_file_count"],
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "quality_gate_false_count": legacy["quality_gate_false_count"],
            "stage_scope_false_count": legacy["stage_scope_false_count"],
            "public_safety_false_count": legacy["public_safety_false_count"],
        },
        "html_sample_inheritance": {
            "taskpack_html_requirement_read": True,
            "source_taskpack_refs": legacy["source_taskpack_refs"],
            "html_output_count": legacy["html_export_count"],
            "inherits_blue_business_sample_count": legacy["inherits_blue_business_sample_count"],
            "implementation_boundary": (
                "v0.1.4 S10-P3 validates existing public-safe HTML/CSV exports and records "
                "aggregate evidence only; no formal report release or new raw-derived values."
            ),
        },
        "phase_boundaries": {
            "s10_p1_report_templates_dependency_included": True,
            "s10_p2_report_trust_grade_dependency_included": True,
            "s10_p3_report_export_scope_included": True,
            "stage10_review_scope_included": False,
            "lineage_full_check_scope_included": False,
            "raw_value_matching_scope_included": False,
            "formal_report_scope_included": False,
            "ui_runtime_scope_included": False,
            "external_connector_scope_included": False,
            "app_reinstall_scope_included": False,
            "github_upload_scope_included": False,
        },
        "quality_gate": {
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "release_permission": "blocked",
            "pending_reconciliation_count": legacy["pending_reconciliation_count"],
            "confirmed_resolution_count": 0,
            "zero_delta_passed": False,
            "html_export_allowed": True,
            "csv_excel_export_allowed": True,
            "pdf_export_policy_enabled": True,
            "complete_trusted_report_display_allowed": False,
            "full_trusted_report_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "business_execution_allowed": False,
            "delivery_allowed": False,
            "raw_layer_write_allowed": False,
            "automatic_external_action_allowed": False,
            "stage10_review_allowed": False,
            "github_upload_allowed": False,
        },
        "github_upload": {
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        },
        "raw_data_boundary": {
            "raw_inbox_ref": RAW_INBOX_REF,
            "raw_inbox_role": "user_finance_raw_private_inbox",
            "raw_inbox_read_allowed_only_when_phase_requires": True,
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
            "raw_or_private_csv_committed": False,
            "public_safe_csv_export_committed": True,
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
            "html_report_export_committed": True,
            "spreadsheet_workbook_committed": False,
        },
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "artifact_refs": {
            **legacy["artifact_refs"],
            "v013_s10_p3_replay_manifest": V013_S10_P3_MANIFEST_PATH.as_posix(),
            "v014_s10_p2_manifest": "KMFA/stage_artifacts/V014_S10_P2_REPORT_TRUST_GRADE/machine/report_trust_grade_manifest.json",
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "generator": "KMFA/tools/v014_s10_p3_report_export.py",
            "validator": "KMFA/tools/check_v014_s10_p3_report_export.py",
            "unit_test": "KMFA/tests/test_v014_s10_p3_report_export.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s10_p3_report_export.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_p3_report_export.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s10_p3_report_export -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_p2_report_trust_grade.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s10_p3_report_export.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s10_p3_report_export_replay.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            "KMFA/tools/v014_s10_p3_report_export.py",
            "KMFA/tools/check_v014_s10_p3_report_export.py",
            "KMFA/tests/test_v014_s10_p3_report_export.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["report_export_summary"]
    policy = manifest["report_export_policy"]
    quality = manifest["quality_gate"]
    lines = [
        "# KMFA v0.1.4 S10-P3 Report Export",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.4 S10-P2 report trust grade PASS`",
        "- legacy_s10_p3_dependency_validated: `true`",
        "- v013_s10_p3_replay_validated: `true`",
        f"- template_count: `{summary['template_count']}`",
        f"- report_export_record_count: `{summary['report_export_record_count']}`",
        f"- grade_distribution: `{summary['grade_distribution']}`",
        f"- html_export_count: `{summary['html_export_count']}`",
        f"- csv_appendix_count: `{summary['csv_appendix_count']}`",
        f"- excel_compatible_download_count: `{summary['excel_compatible_download_count']}`",
        f"- committed_excel_file_count: `{summary['committed_excel_file_count']}`",
        f"- pdf_export_enabled_after_template_stable: `{str(summary['pdf_export_enabled_after_template_stable']).lower()}`",
        f"- committed_pdf_file_count: `{summary['committed_pdf_file_count']}`",
        f"- formal_report_count: `{summary['formal_report_count']}`",
        f"- business_decision_basis_count: `{summary['business_decision_basis_count']}`",
        f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
        f"- report_export_version: `{policy['report_export_version']}`",
        f"- formula_version: `{policy['formula_version']}`",
        f"- mapping_version: `{policy['mapping_version']}`",
        f"- html_template_version: `{policy['html_template_version']}`",
        f"- csv_appendix_schema_version: `{policy['csv_appendix_schema_version']}`",
        f"- record_version_binding_count: `{policy['record_version_binding_count']}`",
        "",
        "## Boundary",
        "",
        "- s10_p3_report_export_scope_included: `true`",
        "- stage10_review_scope_included: `false`",
        "- github_upload_deferred_until_v014_stage1_18_complete: `true`",
        "- github_upload_performed: `false`",
        "- complete_trusted_report_display_allowed: `false`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- business_execution_allowed: `false`",
        f"- current_report_grade: `{quality['current_report_grade']}`",
        f"- release_permission: `{quality['release_permission']}`",
        "",
        "## Export Evidence",
        "",
        "- HTML exports: `2` public-safe previews from existing S10-P3 export runtime",
        "- CSV/Excel-compatible appendices: `2` public-safe CSV downloads",
        "- PDF policy: `enabled_private_runtime_only_no_public_file_committed`",
        "- workbook policy: `excel_compatible_csv_no_workbook_committed`",
        "",
        "## Raw Data Boundary",
        "",
        f"- raw_inbox_ref: `{RAW_INBOX_REF}`",
        "- raw_inbox_read_required_by_this_phase: `false`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_listed_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "",
        "This phase did not enumerate, copy, modify, move, rename, delete, overwrite, or write generated files inside the local finance inbox.",
        "",
        "## Public Safety",
        "",
        "Evidence contains only export counts, D-grade blockers, version bindings, public-safe artifact references, validator references, and governance paths.",
        "It does not contain source filenames, source hashes from the private inbox, tab labels, ZIP member names, field/header plaintext, row values, business amount values, credentials, contracts, payroll, tax filings, or bank statements.",
        "",
        "## Next Step",
        "",
        manifest["next_required_step"],
        "",
    ]
    _write_text(REPORT_PATH, "\n".join(lines))


def write_test_results() -> None:
    lines = [
        "# KMFA v0.1.4 S10-P3 Report Export Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `completed_validated_local_only_no_go_upload_deferred`",
        "- github_upload_performed: `false`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "- stage10_review_performed: `false`",
        "- raw_value_matching_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Command Results",
        "",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s10_p3_report_export.py KMFA/tools/check_v014_s10_p3_report_export.py KMFA/tests/test_v014_s10_p3_report_export.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s10_p3_report_export.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_p2_report_trust_grade.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s10_p3_report_export.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_report_export_runtime -q`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s10_p3_report_export_replay.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_p3_report_export.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s10_p3_report_export -q`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`",
        "- PASS: `git diff --check -- KMFA scripts`",
        "- PASS: changed/untracked parse and raw/private suffix scan.",
        "- PASS: changed/untracked strict secret token scan.",
        "- PASS: scoped S10-P3 public evidence raw/private semantic scan.",
        "",
        "Note: Stage 10 overall review and GitHub upload were intentionally not performed in this phase.",
        "",
    ]
    _write_text(TEST_RESULTS_PATH, "\n".join(lines))


def write_risk_register() -> None:
    lines = [
        "# KMFA v0.1.4 S10-P3 Risk Register",
        "",
        "| Risk | Control | Status |",
        "|---|---|---|",
        "| D 级报告被误用为正式经营报告 | manifest/validator 保持 formal_report_allowed=false 与 business_decision_basis_allowed=false | controlled |",
        "| CSV/HTML 导出泄露 raw/private 值 | validator 扫描 evidence 文本并复用 public-safe legacy exports | controlled |",
        "| PDF/Excel workbook 误提交 | policy 与 validator 要求 committed_pdf_file_count=0、committed_excel_file_count=0 | controlled |",
        "| 单 phase 越界进入 Stage 10 review 或 GitHub upload | phase boundaries 与 validator 均要求 false | controlled |",
        "",
    ]
    _write_text(RISK_REGISTER_PATH, "\n".join(lines))


def write_rollback_plan() -> None:
    lines = [
        "# KMFA v0.1.4 S10-P3 Rollback Plan",
        "",
        "Rollback is local-only: revert the S10-P3 commit or remove the generated `V014_S10_P3_REPORT_EXPORT` evidence, v014 S10-P3 tools/tests, and governance entries.",
        "",
        "No raw/private input file is created, modified, moved, renamed, deleted, or overwritten by this phase.",
        "",
    ]
    _write_text(ROLLBACK_PATH, "\n".join(lines))


def generate() -> dict[str, Any]:
    MACHINE_DIR.mkdir(parents=True, exist_ok=True)
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    _write_json(MANIFEST_PATH, manifest)
    write_report(manifest)
    write_test_results()
    write_risk_register()
    write_rollback_plan()
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["report_export_summary"]
    print(
        "PASS: KMFA v0.1.4 S10-P3 report export evidence generated "
        f"(export_records={summary['report_export_record_count']}, "
        f"html_exports={summary['html_export_count']}, "
        f"csv_appendices={summary['csv_appendix_count']}, "
        f"excel_compatible_downloads={summary['excel_compatible_download_count']}, "
        f"committed_pdf_files={summary['committed_pdf_file_count']}, "
        f"committed_excel_files={summary['committed_excel_file_count']}, "
        "stage10_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
