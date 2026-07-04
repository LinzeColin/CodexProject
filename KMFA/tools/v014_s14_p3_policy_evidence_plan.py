#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S14-P3 policy evidence planning evidence.

This phase replays the existing public-safe S14-P3 policy-evidence model under
the v1.4 S14-P2 dependency and upload-deferral contract. It does not read
raw/private data, perform Stage 14 review, complete lineage, release a formal
report, make policy eligibility conclusions, submit policy/subsidy material,
execute invoice, tax, payment, bank, loan, or other business actions, or upload
to GitHub.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s14_p2_invoice_tax_plan import validate_v014_s14_p2_invoice_tax_plan
from KMFA.tools.policy_evidence_plan import (
    REQUIRED_EVIDENCE_DIRECTORIES,
    REQUIRED_POLICY_PROGRAMS,
    build_default_policy_evidence_artifacts,
    validate_policy_evidence_artifacts,
)


TASK_ID = "KMFA-V014-S14-P3-POLICY-EVIDENCE-PLAN-20260705"
ACCEPTANCE_ID = "ACC-V014-S14-P3-POLICY-EVIDENCE-PLAN"
SCHEMA_VERSION = "kmfa.v014_s14_p3_policy_evidence_plan.v1"
PHASE_SCOPE = "v014_s14_p3_policy_evidence_plan_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S14_P3_POLICY_EVIDENCE_PLAN")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
EXPORT_HTML_DIR = OUTPUT_DIR / "exports" / "html"
MANIFEST_PATH = MACHINE_DIR / "policy_evidence_plan_manifest.json"
DIRECTORIES_PATH = MACHINE_DIR / "policy_evidence_directories.jsonl"
GAPS_PATH = MACHINE_DIR / "policy_evidence_gaps.jsonl"
RISK_TIPS_PATH = MACHINE_DIR / "policy_risk_tips.jsonl"
HTML_OVERVIEW_PATH = EXPORT_HTML_DIR / "policy_evidence_overview.html"
REPORT_PATH = HUMAN_DIR / "policy_evidence_plan_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_SOURCE_PACKAGE_MANIFEST = Path("KMFA/taskpack/v1_4/machine/source_package_manifest.json")
V14_HTML_ENTRY_PATH = Path("KMFA/taskpack/v1_4/html_uiux/00_KMFA_HTML_human_flow_entry_v1_4.html")
V14_HTML_AUDIT_REPORT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/KMFA_HTML_human_flow_audit_report_v1_4.md")
V14_HTML_AUDIT_SCRIPT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/kmfa_html_human_flow_audit.py")
V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 Stage 14 overall review as a separate run. Do not perform "
    "GitHub upload, protected source matching, lineage full check, formal report "
    "release, live connector, app reinstall, OpMe deep coupling, policy eligibility "
    "conclusion, policy filing, subsidy application, tax filing, invoice issuance, "
    "payment approval, payment execution, bank operation, loan management, difference "
    "closure, or business execution in the S14-P3 run."
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def _extract_first_int(pattern: str, text: str, label: str) -> int:
    match = re.search(pattern, text)
    if not match:
        raise RuntimeError(f"missing v1.4 HTML/UIUX audit value: {label}")
    return int(match.group(1))


def validate_s14_p2_dependency() -> dict[str, Any]:
    result = validate_v014_s14_p2_invoice_tax_plan()
    if result.get("stage_id") != "S14" or result.get("phase_id") != "S14-P2":
        raise RuntimeError("S14-P3 requires validated v0.1.4 S14-P2 evidence")
    if result.get("next_phase") != "S14-P3":
        raise RuntimeError("S14-P2 must route to S14-P3")
    progress = result.get("stage14_phase_progress", {})
    if progress.get("s14_p1_performed") is not True or progress.get("s14_p2_performed") is not True:
        raise RuntimeError("S14-P3 requires S14-P1 and S14-P2 to be performed")
    if progress.get("s14_p3_performed") is not False:
        raise RuntimeError("S14-P2 dependency must not already include S14-P3")
    if progress.get("stage14_review_performed") is not False:
        raise RuntimeError("S14-P2 dependency must not include Stage 14 review")
    upload = result.get("github_upload", {})
    if upload.get("github_upload_performed") is not False:
        raise RuntimeError("S14-P2 dependency must not include GitHub upload")
    if upload.get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("v1.4 upload must remain deferred")
    raw = result.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_by_this_phase",
        "raw_inbox_listed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
    ):
        if raw.get(key) is not False:
            raise RuntimeError(f"S14-P2 raw boundary must keep {key}=false")
    return result


def validate_legacy_s14_p3_artifacts() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, str],
]:
    legacy_manifest, directories, gaps, risk_tips, html_outputs = build_default_policy_evidence_artifacts(
        generated_at="2026-07-05T08:05:00+10:00"
    )
    validate_policy_evidence_artifacts(legacy_manifest, directories, gaps, risk_tips, html_outputs)
    return legacy_manifest, directories, gaps, risk_tips, html_outputs


def load_v14_taskpack_baseline() -> dict[str, Any]:
    source_manifest = _read_json(V14_SOURCE_PACKAGE_MANIFEST)
    gate = source_manifest.get("html_human_flow_gate", {})
    report_text = V14_HTML_AUDIT_REPORT_PATH.read_text(encoding="utf-8")
    entry_text = V14_HTML_ENTRY_PATH.read_text(encoding="utf-8")
    script_text = V14_HTML_AUDIT_SCRIPT_PATH.read_text(encoding="utf-8")
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")

    report_counts = {
        "audit_file_count": _extract_first_int(r"HTML 文件数：(\d+)", report_text, "HTML file count"),
        "audit_control_row_count": _extract_first_int(r"核验行数：(\d+)", report_text, "control row count"),
        "audit_pass_count": _extract_first_int(r"PASS：(\d+)", report_text, "pass count"),
        "audit_warn_count": _extract_first_int(r"WARN：(\d+)", report_text, "warn count"),
        "audit_fail_count": _extract_first_int(r"FAIL：(\d+)", report_text, "fail count"),
    }
    manifest_counts = {
        "audit_file_count": int(gate.get("audit_files", -1)),
        "audit_control_row_count": int(gate.get("audit_rows", -1)),
        "audit_pass_count": int(gate.get("pass", -1)),
        "audit_warn_count": int(gate.get("warn", -1)),
        "audit_fail_count": int(gate.get("fail", -1)),
    }
    if report_counts != manifest_counts:
        raise RuntimeError("v1.4 HTML audit report counts do not match source package manifest")

    for token in (
        "政策证据",
        "登记科小、高新、专精特新、小巨人、研发费用证据目录",
        "只输出证据缺口和风险提示",
        "不输出正式政策资格结论",
    ):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S14-P3 token: {token}")
    for token in ("开票/纳税/税务政策线", "证据缺口和风险提示", "不做正式纳税申报"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing policy evidence token: {token}")
    for token in ("开票纳税", "财务资金", "报告中心", "系统治理"):
        if token not in entry_text:
            raise RuntimeError(f"v1.4 HTML entry missing policy flow token: {token}")
    if "button" not in script_text or "input" not in script_text or "link" not in script_text:
        raise RuntimeError("v1.4 audit script must inspect links, inputs, and buttons")

    return {
        "taskpack_html_requirement_read": True,
        "human_flow_entry_exists": V14_HTML_ENTRY_PATH.exists(),
        "human_flow_audit_script_exists": V14_HTML_AUDIT_SCRIPT_PATH.exists(),
        "human_flow_audit_report_exists": V14_HTML_AUDIT_REPORT_PATH.exists(),
        **report_counts,
        "source_package_manifest_counts_match_report": True,
        "roadmap_includes_s14_p3_requirements": True,
        "taskpack_includes_tax_policy_line": True,
        "html_entry_includes_tax_policy_flow": True,
        "audit_script_inspects_links_inputs_buttons": True,
        "implementation_reflects_policy_evidence_directories": False,
        "implementation_reflects_no_policy_conclusion_or_submission": False,
        "source_refs": {
            "source_package_manifest": V14_SOURCE_PACKAGE_MANIFEST.as_posix(),
            "html_human_flow_entry": V14_HTML_ENTRY_PATH.as_posix(),
            "html_human_flow_audit_script": V14_HTML_AUDIT_SCRIPT_PATH.as_posix(),
            "html_human_flow_audit_report": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
            "taskpack": V14_TASKPACK_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
        },
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "pending_reconciliation_count": 12,
        "confirmed_resolution_count": 0,
        "policy_evidence_directory_registration_allowed": True,
        "evidence_gap_signal_allowed": True,
        "risk_tip_allowed": True,
        "complete_trusted_report_display_allowed": False,
        "full_trusted_report_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "delivery_allowed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "derived_amount_calculation_allowed": False,
        "policy_qualification_conclusion_allowed": False,
        "formal_policy_conclusion_allowed": False,
        "policy_application_submission_allowed": False,
        "subsidy_application_allowed": False,
        "policy_filing_allowed": False,
        "tax_filing_allowed": False,
        "tax_declaration_generation_allowed": False,
        "invoice_issuance_allowed": False,
        "invoice_operation_allowed": False,
        "invoice_api_call_allowed": False,
        "payment_approval_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "loan_management_action_allowed": False,
        "automatic_external_action_allowed": False,
        "stage14_review_allowed": False,
        "github_upload_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s14_p1_dependency_included": True,
        "s14_p2_dependency_included": True,
        "s14_p3_policy_evidence_scope_included": True,
        "stage14_review_scope_included": False,
        "lineage_full_check_scope_included": False,
        "protected_source_matching_scope_included": False,
        "raw_value_matching_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "live_ui_runtime_scope_included": False,
        "app_reinstall_scope_included": False,
        "opme_deep_coupling_scope_included": False,
        "github_upload_scope_included": False,
        "payment_or_bank_operation_scope_included": False,
        "loan_management_scope_included": False,
        "invoice_issuance_scope_included": False,
        "tax_filing_scope_included": False,
        "policy_filing_scope_included": False,
        "policy_qualification_conclusion_scope_included": False,
        "subsidy_application_scope_included": False,
        "business_execution_scope_included": False,
    }


def _raw_boundary() -> dict[str, Any]:
    return {
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
    }


def _public_repo_safety() -> dict[str, bool]:
    return {
        "protected_source_payload_committed": False,
        "zip_committed": False,
        "excel_workbook_committed": False,
        "pdf_committed": False,
        "private_csv_committed": False,
        "sqlite_or_db_committed": False,
        "credentials_committed": False,
        "connector_secret_committed": False,
        "field_plaintext_committed": False,
        "source_header_plaintext_committed": False,
        "raw_file_names_committed": False,
        "tab_labels_committed": False,
        "source_record_payload_committed": False,
        "normalized_source_values_committed": False,
        "business_amount_values_committed": False,
        "tax_identifier_committed": False,
        "invoice_number_committed": False,
        "tax_declaration_number_committed": False,
        "account_number_committed": False,
        "project_or_customer_plaintext_committed": False,
        "formal_report_committed": False,
        "business_decision_basis_committed": False,
        "payment_or_bank_operation_committed": False,
        "loan_management_action_committed": False,
        "tax_or_invoice_operation_committed": False,
        "policy_or_subsidy_filing_committed": False,
        "policy_application_file_committed": False,
        "policy_score_committed": False,
        "formal_policy_conclusion_committed": False,
    }


def build_manifest() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, str],
]:
    generated_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    s14_p2 = validate_s14_p2_dependency()
    legacy_manifest, directories, gaps, risk_tips, html_outputs = validate_legacy_s14_p3_artifacts()
    validate_policy_evidence_artifacts(legacy_manifest, directories, gaps, risk_tips, html_outputs)
    baseline = load_v14_taskpack_baseline()
    baseline["implementation_reflects_policy_evidence_directories"] = True
    baseline["implementation_reflects_no_policy_conclusion_or_submission"] = True
    summary = dict(legacy_manifest["summary"])

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s14_p3_policy_evidence_plan_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S14",
        "phase_id": "S14-P3",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S14P3T01", "S14P3T02", "S14P3T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_policy_evidence_plan_locked",
        "generated_at": generated_at,
        "git_head": git_output(["rev-parse", "HEAD"]),
        "s14_p2_dependency_validated": True,
        "legacy_s14_p3_dependency_validated": True,
        "v14_taskpack_dependency_validated": True,
        "source_taskpack_refs": {
            "v14_taskpack": V14_TASKPACK_PATH.as_posix(),
            "v14_roadmap": V14_ROADMAP_PATH.as_posix(),
            "v14_html_audit": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
        },
        "dependency_summary": {
            "s14_p2_phase_progress": s14_p2.get("stage14_phase_progress"),
            "s14_p2_next_phase": s14_p2.get("next_phase"),
            "legacy_s14p3_policy_programs": summary["policy_program_count"],
            "legacy_s14p3_evidence_directories": summary["evidence_directory_count"],
            "legacy_s14p3_gaps": summary["evidence_gap_count"],
            "legacy_s14p3_risk_tips": summary["risk_tip_count"],
        },
        "stage14_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s14_p1_performed": True,
            "s14_p2_performed": True,
            "s14_p3_performed": True,
            "stage14_review_performed": False,
        },
        "policy_evidence_summary": {
            "policy_program_count": summary["policy_program_count"],
            "evidence_directory_count": summary["evidence_directory_count"],
            "evidence_gap_count": summary["evidence_gap_count"],
            "risk_tip_count": summary["risk_tip_count"],
            "html_output_count": summary["html_output_count"],
            "source_count": summary["source_count"],
            "field_mapping_count": summary["field_mapping_count"],
            "pending_reconciliation_count": summary["pending_reconciliation_count"],
            "report_grade_visible": summary["report_grade_visible"],
            "formal_report_count": summary["formal_report_count"],
            "formal_policy_conclusion_count": summary["formal_policy_conclusion_count"],
            "policy_application_submission_count": summary["policy_application_submission_count"],
            "subsidy_application_count": 0,
            "business_decision_basis_count": summary["business_decision_basis_count"],
            "external_connector_action_count": summary["external_connector_action_count"],
            "tax_filing_count": summary["tax_filing_count"],
            "invoice_issuance_count": summary["invoice_issuance_count"],
            "payment_or_bank_operation_count": summary["payment_or_bank_operation_count"],
            "required_policy_programs": list(REQUIRED_POLICY_PROGRAMS),
            "required_evidence_directories": list(REQUIRED_EVIDENCE_DIRECTORIES),
        },
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "raw_data_boundary": _raw_boundary(),
        "public_repo_safety": _public_repo_safety(),
        "v14_taskpack_baseline": baseline,
        "github_upload": {
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
            "github_upload_policy": "upload only after v1.4 Stage 1-18 completion, whole review, and finding fixes",
        },
        "hard_blocks": [
            "report_grade_d_only",
            "pending_reconciliation_blocks_formal_report",
            "raw_data_mutation_forbidden",
            "raw_value_publication_forbidden",
            "field_header_plaintext_publication_forbidden",
            "formal_report_release_blocked",
            "business_decision_basis_blocked",
            "policy_qualification_conclusion_blocked",
            "policy_application_submission_blocked",
            "subsidy_application_blocked",
            "tax_filing_blocked",
            "invoice_issuance_blocked",
            "payment_approval_blocked",
            "payment_execution_blocked",
            "bank_operation_blocked",
            "loan_management_action_blocked",
            "stage14_review_not_performed",
            "lineage_full_check_not_performed",
            "protected_source_matching_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "app_reinstall_not_performed",
            "business_execution_blocked",
        ],
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "policy_evidence_directories": DIRECTORIES_PATH.as_posix(),
            "policy_evidence_gaps": GAPS_PATH.as_posix(),
            "policy_risk_tips": RISK_TIPS_PATH.as_posix(),
            "html_overview": HTML_OVERVIEW_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s14_p3_policy_evidence_plan.py",
            "focused_test": "KMFA/tests/test_v014_s14_p3_policy_evidence_plan.py",
        },
        "next_phase": "S14_STAGE_REVIEW",
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    return manifest, directories, gaps, risk_tips, html_outputs


def write_human_evidence(manifest: dict[str, Any]) -> None:
    summary = manifest["policy_evidence_summary"]
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S14-P3 Policy Evidence Plan",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `completed_validated_local_only_no_go_upload_deferred`",
                "- phase_scope: `v014_s14_p3_policy_evidence_plan_only`",
                f"- policy_programs: `{summary['policy_program_count']}`",
                f"- evidence_directories: `{summary['evidence_directory_count']}`",
                f"- evidence_gaps: `{summary['evidence_gap_count']}`",
                f"- risk_tips: `{summary['risk_tip_count']}`",
                f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
                "- report_grade_visible: `D`",
                "- formal_report_allowed: `false`",
                "- business_decision_basis_allowed: `false`",
                "- policy_qualification_conclusion_allowed: `false`",
                "- policy_application_submission_allowed: `false`",
                "- subsidy_application_allowed: `false`",
                "- tax_filing_allowed: `false`",
                "- invoice_issuance_allowed: `false`",
                "- external_connector_action_count: `0`",
                "- stage14_review_performed: `false`",
                "- github_upload_performed: `false`",
                "- raw_inbox_read_by_this_phase: `false`",
                "",
                "## Coverage",
                "",
                "- T1: 登记科小、高新、专精特新、小巨人、研发费用 5 类 public-safe 证据目录。",
                "- T2: 只输出 5 条证据缺口和 5 条风险提示。",
                "- T3: 锁定不输出正式政策资格结论、不生成政策申报或补贴申请材料、不调用外部接口、不作为税务申报或经营决策依据。",
                "",
                "## Boundary",
                "",
                "- 不提交 raw business data、source schema plaintext、受保护业务数值、受保护税务标识、受保护票据标识、政策申报材料、合同材料、Excel workbook、PDF、zip、sqlite/db、private CSV 或 credentials。",
                "- 不执行 Stage 14 review、GitHub upload、protected source matching、lineage full check、正式报告、外部接口、政策资格结论、政策申报、补贴申请、开票、纳税申报、付款、银行、贷款管理或业务执行。",
                "",
            ]
        ),
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S14-P3 Test Results",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `pending_final_validation_capture`",
                "",
                "## Expected Commands",
                "",
                "- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s14_p3_policy_evidence_plan.py KMFA/tools/check_v014_s14_p3_policy_evidence_plan.py KMFA/tests/test_v014_s14_p3_policy_evidence_plan.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s14_p3_policy_evidence_plan.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s14_p3_policy_evidence_plan.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s14_p3_policy_evidence_plan.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s14_p3_policy_evidence_plan -q`",
                "- governance validators and safety scans before commit",
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S14-P3 Risk Register",
                "",
                "| Risk | Control | Status |",
                "|---|---|---|",
                "| 证据目录被误用为政策资格结论 | D 级展示，policy conclusion/submission gates 全部 false | controlled |",
                "| S14-P3 越界进入 Stage 14 review 或 upload | validator 检查 Stage 14 review 和 GitHub upload 均为 false | controlled |",
                "| raw/private 数据泄漏 | 只复用 public-safe metadata，raw inbox read/list/stat/hash/mutation 全为 false | controlled |",
                "",
            ]
        ),
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S14-P3 Rollback Plan",
                "",
                "- 删除 `KMFA/stage_artifacts/V014_S14_P3_POLICY_EVIDENCE_PLAN/`。",
                "- 删除 `KMFA/tools/v014_s14_p3_policy_evidence_plan.py` 和 `KMFA/tools/check_v014_s14_p3_policy_evidence_plan.py`。",
                "- 删除 `KMFA/tests/test_v014_s14_p3_policy_evidence_plan.py`。",
                "- 回滚本 phase 的治理 registry、开发记录、功能清单和模型参数文件更新。",
                "",
            ]
        ),
    )


def generate() -> dict[str, Any]:
    manifest, directories, gaps, risk_tips, html_outputs = build_manifest()
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(DIRECTORIES_PATH, directories)
    _write_jsonl(GAPS_PATH, gaps)
    _write_jsonl(RISK_TIPS_PATH, risk_tips)
    _write_text(HTML_OVERVIEW_PATH, html_outputs["policy_evidence_overview"])
    write_human_evidence(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["policy_evidence_summary"]
    print(
        "PASS: KMFA v0.1.4 S14-P3 policy evidence plan generated "
        f"(policy_programs={summary['policy_program_count']}, directories={summary['evidence_directory_count']}, "
        f"gaps={summary['evidence_gap_count']}, risk_tips={summary['risk_tip_count']}, "
        f"pending_reconciliation={summary['pending_reconciliation_count']}, report_grade=D, "
        "policy_conclusion=false, policy_submission=false, stage14_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
