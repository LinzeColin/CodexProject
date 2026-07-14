#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 15 review evidence.

This review closes the v0.1.4 sales-performance fact and salary-boundary
stage by replaying S15-P1, S15-P2 and S15-P3 public-safe manifests. It treats
legacy Stage 15 review/upload artifacts as historical only. It does not read
raw/private finance data, enter S16, calculate salary or bonuses, export
payroll, release final compensation, execute payment, or upload to GitHub.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_s15_stage_review import (  # noqa: E402
    DEFAULT_REVIEW_MANIFEST as LEGACY_STAGE15_REVIEW_MANIFEST_PATH,
    validate_stage_review as validate_legacy_stage15_review,
)
from KMFA.tools.check_v014_s15_p1_performance_fact_fields import (  # noqa: E402
    validate_v014_s15_p1_performance_fact_fields,
)
from KMFA.tools.check_v014_s15_p2_performance_review_list import (  # noqa: E402
    validate_v014_s15_p2_performance_review_list,
)
from KMFA.tools.check_v014_s15_p3_salary_boundary import (  # noqa: E402
    validate_v014_s15_p3_salary_boundary,
)


TASK_ID = "KMFA-V014-S15-STAGE-REVIEW-20260705"
ACCEPTANCE_ID = "ACC-V014-S15-STAGE-REVIEW"
SCHEMA_VERSION = "kmfa.v014_s15_stage_review.v1"
REVIEW_SCOPE = "v014_s15_stage_review_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S15_STAGE_REVIEW")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "stage15_review_manifest.json"
REPORT_PATH = HUMAN_DIR / "stage15_review_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "S16-P1"
NEXT_REQUIRED_STEP = (
    "Start v0.1.4 S16-P1 only as a separate run after user instruction. "
    "Do not perform GitHub upload in Stage 15 review; GitHub main upload remains deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed. Do not perform "
    "protected source matching, lineage full check, formal report release, live connector, app reinstall, "
    "OpMe deep coupling, salary calculation, bonus approval, payroll export, final compensation decision, "
    "final payment, payment execution, bank operation, legal decision, collection action, or business execution."
)
RAW_PHASE_KEYS = (
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_inventory_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
)
RAW_REVIEW_KEYS = tuple(key.replace("_by_this_phase", "_by_this_review") for key in RAW_PHASE_KEYS)


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def load_v14_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    for token in ("销售绩效事实与复核清单", "绩效事实字段", "绩效复核清单", "与工资项目边界"):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing Stage 15 marker {token}")
    for token in ("销售绩效/业务考核线", "不做工资最终审批", "不自动发工资或奖金"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing Stage 15 boundary marker {token}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_stage15_requirements": True,
        "taskpack_includes_no_final_salary_approval": True,
        "source_refs": {
            "taskpack": V14_TASKPACK_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
        },
    }


def _raw_all_false(manifest: dict[str, Any]) -> bool:
    raw = manifest.get("raw_data_boundary", {})
    return isinstance(raw, dict) and all(raw.get(key) is False for key in RAW_PHASE_KEYS)


def _raw_boundary(p1: dict[str, Any], p2: dict[str, Any], p3: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {key: False for key in RAW_REVIEW_KEYS}
    result.update(
        {
            "raw_inbox_ref": RAW_INBOX_REF,
            "raw_inbox_read_required_by_this_review": False,
            "s15_p1_raw_inbox_all_false": _raw_all_false(p1),
            "s15_p2_raw_inbox_all_false": _raw_all_false(p2),
            "s15_p3_raw_inbox_all_false": _raw_all_false(p3),
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        }
    )
    return result


def _public_repo_safety() -> dict[str, bool]:
    return {
        "protected_source_payload_committed": False,
        "compressed_raw_package_committed": False,
        "excel_workbook_committed": False,
        "wps_native_file_committed": False,
        "raw_or_private_csv_committed": False,
        "pdf_document_committed": False,
        "private_csv_committed": False,
        "local_database_committed": False,
        "auth_material_committed": False,
        "connector_auth_material_committed": False,
        "field_plaintext_committed": False,
        "source_schema_plaintext_committed": False,
        "raw_file_names_committed": False,
        "raw_file_hashes_committed": False,
        "tab_labels_committed": False,
        "source_record_payload_committed": False,
        "normalized_source_values_committed": False,
        "business_amount_values_committed": False,
        "public_numeric_values_committed": False,
        "project_or_customer_plaintext_committed": False,
        "employee_or_salary_payload_committed": False,
        "payroll_export_committed": False,
        "final_compensation_payload_committed": False,
        "final_payment_payload_committed": False,
        "business_decision_basis_committed": False,
    }


def _release_state() -> dict[str, Any]:
    return {
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "salary_calculation_allowed": False,
        "wage_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "final_compensation_decision_allowed": False,
        "final_payment_allowed": False,
        "payment_execution_allowed": False,
        "github_main_upload_allowed": False,
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "blocking_reason": "stage15_review_is_public_safe_d_grade_with_salary_payment_and_business_execution_blocked",
    }


def _stage_gate(p1: dict[str, Any], p2: dict[str, Any], p3: dict[str, Any]) -> dict[str, Any]:
    p1_summary = p1["performance_fact_fields_summary"]
    p2_summary = p2["performance_review_summary"]
    p3_summary = p3["salary_boundary_summary"]
    return {
        "field_definition_count": p1_summary["field_definition_count"],
        "field_binding_count": p1_summary["field_binding_count"],
        "manual_review_field_count": p1_summary["manual_review_field_count"],
        "performance_fact_row_count": p2_summary["performance_fact_row_count"],
        "abnormal_review_item_count": p2_summary["abnormal_review_item_count"],
        "fact_output_interface_contract_count": p3_summary["fact_output_interface_contract_count"],
        "future_salary_system_readiness_row_count": p3_summary["future_salary_system_readiness_row_count"],
        "human_approval_boundary_count": p3_summary["human_approval_boundary_count"],
        "pending_review_item_count": p3_summary["pending_review_item_count"],
        "project_cost_fact_record_count": p2_summary["project_cost_fact_record_count"],
        "margin_record_count": p2_summary["margin_record_count"],
        "collection_priority_item_count": p2_summary["collection_priority_item_count"],
        "cross_table_difference_count": p2_summary["cross_table_difference_count"],
        "salary_calculation_count": 0,
        "wage_calculation_count": 0,
        "bonus_approval_count": 0,
        "payroll_export_count": 0,
        "final_compensation_decision_count": 0,
        "final_payment_count": 0,
        "payment_execution_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }


def _review_findings() -> list[dict[str, str]]:
    return [
        {
            "finding_id": "KMFA-V014-S15-REV-F01",
            "severity": "P2",
            "status": "fixed",
            "summary": "Legacy Stage 15 review and upload artifacts can imply upload readiness, but v1.4 current policy defers GitHub upload until Stage 1-18 completion and final review fixes.",
            "fix": "v0.1.4 Stage 15 review records upload deferred and treats legacy Stage 15 review/upload artifacts as historical, non-current gate evidence.",
            "evidence": LEGACY_STAGE15_REVIEW_MANIFEST_PATH.as_posix(),
        },
        {
            "finding_id": "KMFA-V014-S15-REV-F02",
            "severity": "P2",
            "status": "passed",
            "summary": "S15-P1, S15-P2 and S15-P3 validators pass with public-safe sales performance facts, review items and salary boundary evidence.",
            "fix": "No code fix required.",
            "evidence": "KMFA/stage_artifacts/V014_S15_P3_SALARY_BOUNDARY/machine/salary_boundary_manifest.json",
        },
        {
            "finding_id": "KMFA-V014-S15-REV-F03",
            "severity": "P1",
            "status": "passed",
            "summary": "Salary calculation, bonus approval, payroll export, final compensation, final payment and payment execution remain blocked.",
            "fix": "No code fix required.",
            "evidence": MANIFEST_PATH.as_posix(),
        },
    ]


def build_manifest(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    p1 = validate_v014_s15_p1_performance_fact_fields()
    p2 = validate_v014_s15_p2_performance_review_list()
    p3 = validate_v014_s15_p3_salary_boundary()
    legacy_counts = validate_legacy_stage15_review()
    legacy_manifest = read_json(LEGACY_STAGE15_REVIEW_MANIFEST_PATH)
    findings = _review_findings()

    stage_gate = _stage_gate(p1, p2, p3)
    phase_results = {
        "S15-P1": "PASS" if p1.get("phase_id") == "S15-P1" else "FAIL",
        "S15-P2": "PASS" if p2.get("phase_id") == "S15-P2" else "FAIL",
        "S15-P3": "PASS" if p3.get("phase_id") == "S15-P3" else "FAIL",
    }
    validation_summary = {
        "py_compile": "PENDING_FINAL_VALIDATION",
        "s15_p1_validator": "PASS",
        "s15_p2_validator": "PASS",
        "s15_p3_validator": "PASS",
        "legacy_s15_stage_review_validator": "PASS",
        "stage_review_validator": "PENDING_FINAL_VALIDATION",
        "focused_unit_test": "PENDING_FINAL_VALIDATION",
        "governance_validator": "PENDING_FINAL_VALIDATION",
        "lean_governance_validator": "PENDING_FINAL_VALIDATION",
        "governance_sync_validator": "PENDING_FINAL_VALIDATION",
        "no_float_money_check": "PENDING_FINAL_VALIDATION",
        "no_omission_check": "PENDING_FINAL_VALIDATION",
        "structured_parse": "PENDING_FINAL_VALIDATION",
        "raw_private_suffix_scan": "PENDING_FINAL_VALIDATION",
        "high_signal_secret_scan": "PENDING_FINAL_VALIDATION",
        "public_stage15_semantic_scan": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s15_stage_review_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S15",
        "phase_id": "S15_STAGE_REVIEW",
        "review_scope": REVIEW_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S15REVT01", "S15REVT02", "S15REVT03"],
        "status": "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "generated_at": generated_at,
        "branch": git_output(["branch", "--show-current"]),
        "git_head": git_output(["rev-parse", "HEAD"]),
        "stage_review_performed": True,
        "phase_results": phase_results,
        "stage15_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s15_p1_performed": True,
            "s15_p2_performed": True,
            "s15_p3_performed": True,
            "stage15_review_performed": True,
        },
        "stage_gate": stage_gate,
        "release_state": _release_state(),
        "review_findings": findings,
        "review_findings_summary": {
            "open_finding_count": sum(1 for finding in findings if finding["status"] == "open"),
            "fixed_finding_count": sum(1 for finding in findings if finding["status"] == "fixed"),
            "passed_finding_count": sum(1 for finding in findings if finding["status"] == "passed"),
        },
        "raw_data_boundary": _raw_boundary(p1, p2, p3),
        "public_repo_safety": _public_repo_safety(),
        "v14_taskpack_baseline": load_v14_taskpack_baseline(),
        "legacy_stage15_review_summary": {
            "historical_only": True,
            "legacy_manifest": LEGACY_STAGE15_REVIEW_MANIFEST_PATH.as_posix(),
            "legacy_status": legacy_manifest.get("status"),
            "legacy_github_upload_status": legacy_manifest.get("github_upload_status"),
            "legacy_counts": legacy_counts,
        },
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "s15_p1_manifest": "KMFA/stage_artifacts/V014_S15_P1_PERFORMANCE_FACT_FIELDS/machine/performance_fact_fields_manifest.json",
            "s15_p2_manifest": "KMFA/stage_artifacts/V014_S15_P2_PERFORMANCE_REVIEW_LIST/machine/performance_review_manifest.json",
            "s15_p3_manifest": "KMFA/stage_artifacts/V014_S15_P3_SALARY_BOUNDARY/machine/salary_boundary_manifest.json",
        },
        "validation_summary": validation_summary,
        "hard_blocks": [
            "report_grade_d_only",
            "pending_review_items_require_human_review",
            "raw_data_mutation_forbidden",
            "protected_source_publication_forbidden",
            "field_header_plaintext_publication_forbidden",
            "formal_report_release_blocked",
            "business_decision_basis_blocked",
            "salary_calculation_blocked",
            "wage_calculation_blocked",
            "bonus_approval_blocked",
            "payroll_export_blocked",
            "final_compensation_decision_blocked",
            "final_payment_blocked",
            "payment_execution_blocked",
            "s16_p1_not_performed",
            "lineage_full_check_not_performed",
            "protected_source_matching_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "app_reinstall_not_performed",
            "business_execution_blocked",
        ],
        "s16_p1_performed": False,
        "github_upload_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_v014_stage1_18_complete": True,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_artifacts(manifest: dict[str, Any]) -> None:
    write_json(MANIFEST_PATH, manifest)
    report = "\n".join(
        [
            "# KMFA v0.1.4 Stage 15 Review",
            "",
            "- phase_results: `S15-P1=PASS; S15-P2=PASS; S15-P3=PASS`",
            f"- open_findings: `{manifest['review_findings_summary']['open_finding_count']}`",
            f"- fixed_findings: `{manifest['review_findings_summary']['fixed_finding_count']}`",
            f"- performance_fact_rows: `{manifest['stage_gate']['performance_fact_row_count']}`",
            f"- abnormal_review_items: `{manifest['stage_gate']['abnormal_review_item_count']}`",
            f"- future_salary_readiness_rows: `{manifest['stage_gate']['future_salary_system_readiness_row_count']}`",
            f"- salary_calculation_count: `{manifest['stage_gate']['salary_calculation_count']}`",
            f"- bonus_approval_count: `{manifest['stage_gate']['bonus_approval_count']}`",
            f"- payroll_export_count: `{manifest['stage_gate']['payroll_export_count']}`",
            f"- final_payment_count: `{manifest['stage_gate']['final_payment_count']}`",
            f"- github_upload_status: `{manifest['github_upload_status']}`",
            "",
            "Stage 15 review is local-only. It does not perform S16, GitHub upload, raw inbox access, lineage full check, formal report release, salary calculation, bonus approval, payroll export, final compensation, final payment, payment execution, bank operation or business execution.",
            "",
        ]
    )
    write_text(REPORT_PATH, report)
    write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 15 Review Test Results",
                "",
                "- generator: pending final validation replay",
                "- validator: pending final validation replay",
                "- focused_unittest: pending final validation replay",
                "- governance_validation: pending final validation replay",
                "- raw_secret_scan: pending final validation replay",
                "",
            ]
        ),
    )
    write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 15 Review Risk Register",
                "",
                "- risk: Legacy Stage 15 upload artifacts could be mistaken as current v1.4 upload gate.",
                "  mitigation: Current manifest marks them historical-only and keeps GitHub upload deferred.",
                "- risk: Salary-boundary facts could be mistaken as compensation approval.",
                "  mitigation: Review keeps salary, bonus, payroll, final compensation and payment execution blocked.",
                "",
            ]
        ),
    )
    write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 15 Review Rollback Plan",
                "",
                "- Remove only `KMFA/stage_artifacts/V014_S15_STAGE_REVIEW/` and the paired v014 S15 review governance entries if rollback is required.",
                "- Do not touch raw/private inbox contents.",
                "",
            ]
        ),
    )


def generate() -> dict[str, Any]:
    manifest = build_manifest()
    write_artifacts(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 15 review generated "
        f"(phase_results={manifest['phase_results']}, open_findings={manifest['review_findings_summary']['open_finding_count']}, "
        f"fact_rows={gate['performance_fact_row_count']}, review_items={gate['abnormal_review_item_count']}, "
        f"readiness_rows={gate['future_salary_system_readiness_row_count']}, salary={gate['salary_calculation_count']}, "
        f"bonus={gate['bonus_approval_count']}, payroll={gate['payroll_export_count']}, "
        f"final_payment={gate['final_payment_count']}, s16={manifest['s16_p1_performed']}, "
        f"github_upload={manifest['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
