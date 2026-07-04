#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S14-P2 invoice/tax planning evidence.

This phase replays the existing public-safe S14-P2 invoice and tax planning
model under the v1.4 S14-P1 dependency and upload-deferral contract. It does
not read raw/private data, run S14-P3, perform Stage 14 review, complete
lineage, release a formal report, execute invoice, tax, payment, bank, loan,
policy, subsidy, or other business actions, or upload to GitHub.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s14_p1_fund_cash_loan_plan import validate_v014_s14_p1_fund_cash_loan_plan
from KMFA.tools.invoice_tax_plan import (
    CASH_SUMMARY_BUCKETS,
    REQUIRED_ISSUE_CANDIDATE_TYPES,
    REQUIRED_SOURCE_LANES,
    build_default_invoice_tax_plan_artifacts,
    validate_invoice_tax_plan_artifacts,
)


TASK_ID = "KMFA-V014-S14-P2-INVOICE-TAX-PLAN-20260705"
ACCEPTANCE_ID = "ACC-V014-S14-P2-INVOICE-TAX-PLAN"
SCHEMA_VERSION = "kmfa.v014_s14_p2_invoice_tax_plan.v1"
PHASE_SCOPE = "v014_s14_p2_invoice_tax_plan_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S14_P2_INVOICE_TAX_PLAN")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
EXPORT_HTML_DIR = OUTPUT_DIR / "exports" / "html"
MANIFEST_PATH = MACHINE_DIR / "invoice_tax_plan_manifest.json"
LANES_PATH = MACHINE_DIR / "invoice_tax_source_lanes.jsonl"
ISSUE_CANDIDATES_PATH = MACHINE_DIR / "invoice_tax_issue_candidates.jsonl"
CASH_SUMMARIES_PATH = MACHINE_DIR / "invoice_tax_cash_summaries.jsonl"
HTML_OVERVIEW_PATH = EXPORT_HTML_DIR / "invoice_tax_plan_overview.html"
REPORT_PATH = HUMAN_DIR / "invoice_tax_plan_report.md"
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
    "Proceed to v0.1.4 S14-P3 policy evidence plan as a separate run. Do not perform "
    "Stage 14 overall review, GitHub upload, protected source matching, lineage full "
    "check, formal report release, live connector, app reinstall, OpMe deep coupling, "
    "payment approval, payment execution, bank operation, loan management, invoice "
    "issuance, tax filing, policy filing, subsidy application, difference closure, "
    "or business execution in the S14-P2 run."
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


def validate_s14_p1_dependency() -> dict[str, Any]:
    result = validate_v014_s14_p1_fund_cash_loan_plan()
    if result.get("stage_id") != "S14" or result.get("phase_id") != "S14-P1":
        raise RuntimeError("S14-P2 requires validated v0.1.4 S14-P1 evidence")
    if result.get("next_phase") != "S14-P2":
        raise RuntimeError("S14-P1 must route to S14-P2")
    progress = result.get("stage14_phase_progress", {})
    if progress.get("s14_p1_performed") is not True:
        raise RuntimeError("S14-P1 dependency must be performed")
    if progress.get("s14_p2_performed") is not False:
        raise RuntimeError("S14-P1 dependency must not already include S14-P2")
    if progress.get("stage14_review_performed") is not False:
        raise RuntimeError("S14-P1 dependency must not include Stage 14 review")
    upload = result.get("github_upload", {})
    if upload.get("github_upload_performed") is not False:
        raise RuntimeError("S14-P1 dependency must not include GitHub upload")
    if upload.get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("v1.4 upload must remain deferred")
    raw = result.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_by_this_phase",
        "raw_inbox_listed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
    ):
        if raw.get(key) is not False:
            raise RuntimeError(f"S14-P1 raw boundary must keep {key}=false")
    return result


def validate_legacy_s14_p2_artifacts() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, str],
]:
    legacy_manifest, lanes, issue_candidates, cash_summaries, html_outputs = (
        build_default_invoice_tax_plan_artifacts(generated_at="2026-07-05T07:20:00+10:00")
    )
    validate_invoice_tax_plan_artifacts(
        legacy_manifest,
        lanes,
        issue_candidates,
        cash_summaries,
        html_outputs,
    )
    return legacy_manifest, lanes, issue_candidates, cash_summaries, html_outputs


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
        "开票纳税",
        "接入开票计划、纳税明细、开票纳税资金汇总",
        "识别待开票、已开票未回款、税率异常候选",
        "不做纳税申报和发票开具",
    ):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S14-P2 token: {token}")
    for token in ("开票/纳税/税务政策线", "不做正式纳税申报", "不自动开发票", "开票纳税"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing invoice/tax token: {token}")
    for token in ("财务资金", "开票纳税", "报告中心", "系统治理"):
        if token not in entry_text:
            raise RuntimeError(f"v1.4 HTML entry missing S14 flow token: {token}")
    if "button" not in script_text or "input" not in script_text or "link" not in script_text:
        raise RuntimeError("v1.4 audit script must inspect links, inputs, and buttons")

    return {
        "taskpack_html_requirement_read": True,
        "human_flow_entry_exists": V14_HTML_ENTRY_PATH.exists(),
        "human_flow_audit_script_exists": V14_HTML_AUDIT_SCRIPT_PATH.exists(),
        "human_flow_audit_report_exists": V14_HTML_AUDIT_REPORT_PATH.exists(),
        **report_counts,
        "source_package_manifest_counts_match_report": True,
        "roadmap_includes_s14_p2_requirements": True,
        "taskpack_includes_invoice_tax_line": True,
        "html_entry_includes_invoice_tax_flow": True,
        "audit_script_inspects_links_inputs_buttons": True,
        "implementation_reflects_invoice_tax_candidates": False,
        "implementation_reflects_no_tax_filing_or_invoice_issuance": False,
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
        "invoice_tax_planning_signal_allowed": True,
        "issue_candidate_review_allowed": True,
        "tax_rate_exception_candidate_allowed": True,
        "complete_trusted_report_display_allowed": False,
        "full_trusted_report_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "delivery_allowed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "derived_amount_calculation_allowed": False,
        "tax_filing_allowed": False,
        "tax_declaration_generation_allowed": False,
        "invoice_issuance_allowed": False,
        "invoice_operation_allowed": False,
        "invoice_api_call_allowed": False,
        "payment_approval_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "loan_management_action_allowed": False,
        "policy_filing_allowed": False,
        "subsidy_application_allowed": False,
        "automatic_external_action_allowed": False,
        "s14_p3_allowed": False,
        "stage14_review_allowed": False,
        "github_upload_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s14_p1_dependency_included": True,
        "s14_p2_invoice_tax_plan_scope_included": True,
        "s14_p3_policy_evidence_scope_included": False,
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
        "tax_rate_public_value_committed": False,
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
    }


def build_manifest() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, str],
]:
    generated_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    s14_p1 = validate_s14_p1_dependency()
    legacy_manifest, lanes, issue_candidates, cash_summaries, html_outputs = validate_legacy_s14_p2_artifacts()
    validate_invoice_tax_plan_artifacts(
        legacy_manifest,
        lanes,
        issue_candidates,
        cash_summaries,
        html_outputs,
    )
    baseline = load_v14_taskpack_baseline()
    baseline["implementation_reflects_invoice_tax_candidates"] = True
    baseline["implementation_reflects_no_tax_filing_or_invoice_issuance"] = True
    summary = dict(legacy_manifest["summary"])

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s14_p2_invoice_tax_plan_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S14",
        "phase_id": "S14-P2",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S14P2T01", "S14P2T02", "S14P2T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_invoice_tax_plan_locked",
        "generated_at": generated_at,
        "git_head": git_output(["rev-parse", "HEAD"]),
        "s14_p1_dependency_validated": True,
        "legacy_s14_p2_dependency_validated": True,
        "v14_taskpack_dependency_validated": True,
        "source_taskpack_refs": {
            "v14_taskpack": V14_TASKPACK_PATH.as_posix(),
            "v14_roadmap": V14_ROADMAP_PATH.as_posix(),
            "v14_html_audit": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
        },
        "dependency_summary": {
            "s14_p1_phase_progress": s14_p1.get("stage14_phase_progress"),
            "s14_p1_next_phase": s14_p1.get("next_phase"),
            "legacy_s14p2_source_lanes": summary["source_lane_count"],
            "legacy_s14p2_issue_candidates": summary["issue_candidate_count"],
            "legacy_s14p2_cash_summaries": summary["cash_summary_count"],
        },
        "stage14_phase_progress": {
            "completed_phase_count": 2,
            "total_phase_count": 3,
            "derived_percent_bps": 6667,
            "derived_percent_label": "66.67%",
            "s14_p1_performed": True,
            "s14_p2_performed": True,
            "s14_p3_performed": False,
            "stage14_review_performed": False,
        },
        "invoice_tax_summary": {
            "source_lane_count": summary["source_lane_count"],
            "source_count": summary["source_count"],
            "field_mapping_count": summary["field_mapping_count"],
            "issue_candidate_count": summary["issue_candidate_count"],
            "cash_summary_count": summary["cash_summary_count"],
            "html_output_count": summary["html_output_count"],
            "pending_reconciliation_count": summary["pending_reconciliation_count"],
            "report_grade_visible": summary["report_grade_visible"],
            "formal_report_count": summary["formal_report_count"],
            "business_decision_basis_count": summary["business_decision_basis_count"],
            "invoice_issuance_count": summary["invoice_issuance_count"],
            "tax_filing_count": summary["tax_filing_count"],
            "external_connector_action_count": summary["external_connector_action_count"],
            "payment_or_bank_operation_count": summary["payment_or_bank_operation_count"],
            "required_source_lanes": list(REQUIRED_SOURCE_LANES),
            "required_issue_candidate_types": list(REQUIRED_ISSUE_CANDIDATE_TYPES),
            "required_cash_summary_buckets": list(CASH_SUMMARY_BUCKETS),
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
            "tax_filing_blocked",
            "tax_declaration_generation_blocked",
            "invoice_issuance_blocked",
            "invoice_operation_blocked",
            "payment_approval_blocked",
            "payment_execution_blocked",
            "bank_operation_blocked",
            "loan_management_action_blocked",
            "policy_filing_blocked",
            "subsidy_application_blocked",
            "s14_p3_not_performed",
            "stage14_review_not_performed",
            "lineage_full_check_not_performed",
            "protected_source_matching_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "app_reinstall_not_performed",
            "business_execution_blocked",
        ],
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "source_lanes": LANES_PATH.as_posix(),
            "issue_candidates": ISSUE_CANDIDATES_PATH.as_posix(),
            "cash_summaries": CASH_SUMMARIES_PATH.as_posix(),
            "html_overview": HTML_OVERVIEW_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s14_p2_invoice_tax_plan.py",
            "focused_test": "KMFA/tests/test_v014_s14_p2_invoice_tax_plan.py",
        },
        "next_phase": "S14-P3",
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    return manifest, lanes, issue_candidates, cash_summaries, html_outputs


def write_human_evidence(manifest: dict[str, Any]) -> None:
    summary = manifest["invoice_tax_summary"]
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S14-P2 Invoice Tax Plan",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `completed_validated_local_only_no_go_upload_deferred`",
                "- phase_scope: `v014_s14_p2_invoice_tax_plan_only`",
                f"- source_lanes: `{summary['source_lane_count']}`",
                f"- source_count: `{summary['source_count']}`",
                f"- field_mappings: `{summary['field_mapping_count']}`",
                f"- issue_candidates: `{summary['issue_candidate_count']}`",
                f"- cash_summaries: `{summary['cash_summary_count']}`",
                f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
                "- report_grade_visible: `D`",
                "- formal_report_allowed: `false`",
                "- business_decision_basis_allowed: `false`",
                "- tax_filing_allowed: `false`",
                "- tax_declaration_generation_allowed: `false`",
                "- invoice_issuance_allowed: `false`",
                "- invoice_operation_allowed: `false`",
                "- payment_or_bank_operation_count: `0`",
                "- external_connector_action_count: `0`",
                "- s14_p3_performed: `false`",
                "- stage14_review_performed: `false`",
                "- github_upload_performed: `false`",
                "- raw_inbox_read_by_this_phase: `false`",
                "",
                "## Coverage",
                "",
                "- T1: 接入开票计划、纳税明细、开票纳税资金汇总 3 条 public-safe source lanes。",
                "- T2: 输出待开票、已开票未回款、税率异常候选 3 类候选事项，以及 3 条开票纳税资金汇总状态。",
                "- T3: 锁定不做纳税申报、申报文件生成、发票开具、发票接口调用、付款、银行操作、贷款管理、正式报告或业务执行。",
                "",
                "## Boundary",
                "",
                "- 不提交 raw business data、source schema plaintext、真实金额、真实税率值、真实发票号、税务申报号、Excel workbook、PDF、zip、sqlite/db、private CSV 或 credentials。",
                "- 不执行 S14-P3、Stage 14 review、GitHub upload、protected source matching、lineage full check、正式报告、外部接口、付款、银行、贷款管理、开票、纳税申报、政策申报、补贴申请或业务执行。",
                "",
            ]
        ),
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S14-P2 Test Results",
                "",
                "- task_id: `KMFA-V014-S14-P2-INVOICE-TAX-PLAN-20260705`",
                "- status: `pending_final_validation_capture`",
                "",
                "## Expected Commands",
                "",
                "- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s14_p2_invoice_tax_plan.py KMFA/tools/check_v014_s14_p2_invoice_tax_plan.py KMFA/tests/test_v014_s14_p2_invoice_tax_plan.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s14_p2_invoice_tax_plan.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s14_p2_invoice_tax_plan.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s14_p2_invoice_tax_plan.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s14_p2_invoice_tax_plan -q`",
                "- governance validators and safety scans before commit",
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S14-P2 Risk Register",
                "",
                "| Risk | Control | Status |",
                "|---|---|---|",
                "| 开票纳税候选被误用为纳税申报或发票开具依据 | D 级展示，tax/invoice operation gates 全部 false | controlled |",
                "| S14-P2 越界进入政策证据、Stage 14 review 或 upload | validator 检查 S14-P3、Stage 14 review 和 GitHub upload 均为 false | controlled |",
                "| raw/private 数据泄漏 | 只复用 public-safe metadata，raw inbox read/list/stat/hash/mutation 全为 false | controlled |",
                "",
            ]
        ),
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S14-P2 Rollback Plan",
                "",
                "- 删除 `KMFA/stage_artifacts/V014_S14_P2_INVOICE_TAX_PLAN/`。",
                "- 删除 `KMFA/tools/v014_s14_p2_invoice_tax_plan.py` 和 `KMFA/tools/check_v014_s14_p2_invoice_tax_plan.py`。",
                "- 删除 `KMFA/tests/test_v014_s14_p2_invoice_tax_plan.py`。",
                "- 回滚本 phase 的治理 registry、开发记录、功能清单和模型参数文件更新。",
                "",
            ]
        ),
    )


def generate() -> dict[str, Any]:
    manifest, lanes, issue_candidates, cash_summaries, html_outputs = build_manifest()
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(LANES_PATH, lanes)
    _write_jsonl(ISSUE_CANDIDATES_PATH, issue_candidates)
    _write_jsonl(CASH_SUMMARIES_PATH, cash_summaries)
    _write_text(HTML_OVERVIEW_PATH, html_outputs["invoice_tax_plan_overview"])
    write_human_evidence(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["invoice_tax_summary"]
    print(
        "PASS: KMFA v0.1.4 S14-P2 invoice tax plan evidence generated "
        f"(source_lanes={summary['source_lane_count']}, issue_candidates={summary['issue_candidate_count']}, "
        f"cash_summaries={summary['cash_summary_count']}, pending_reconciliation={summary['pending_reconciliation_count']}, "
        "formal_report=false, tax_filing=false, invoice_issuance=false, payment_bank=false, "
        "s14_p3=false, stage14_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
