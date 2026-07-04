#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S14-P1 fund/cash/loan planning evidence.

This phase replays the existing public-safe S14-P1 fund, cash, and loan
planning model under the v1.4 Stage 13 review dependency and upload-deferral
contract. It does not read raw/private data, run S14-P2/S14-P3, perform Stage
14 review, complete lineage, release a formal report, execute payment, bank,
loan, invoice, tax, policy, or other business actions, or upload to GitHub.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s13_stage_review import validate_v014_s13_stage_review
from KMFA.tools.fund_cash_loan_plan import (
    REQUIRED_OUTPUT_RECORD_TYPES,
    REQUIRED_SOURCE_LANES,
    build_default_fund_cash_loan_plan_artifacts,
    validate_fund_cash_loan_plan_artifacts,
)


TASK_ID = "KMFA-V014-S14-P1-FUND-CASH-LOAN-PLAN-20260705"
ACCEPTANCE_ID = "ACC-V014-S14-P1-FUND-CASH-LOAN-PLAN"
SCHEMA_VERSION = "kmfa.v014_s14_p1_fund_cash_loan_plan.v1"
PHASE_SCOPE = "v014_s14_p1_fund_cash_loan_plan_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S14_P1_FUND_CASH_LOAN_PLAN")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
EXPORT_HTML_DIR = OUTPUT_DIR / "exports" / "html"
MANIFEST_PATH = MACHINE_DIR / "fund_cash_loan_plan_manifest.json"
LANES_PATH = MACHINE_DIR / "fund_cash_loan_source_lanes.jsonl"
CASH_PRESSURE_PATH = MACHINE_DIR / "fund_cash_pressure_signals.jsonl"
LOAN_DUE_PATH = MACHINE_DIR / "loan_due_alerts.jsonl"
ACCOUNT_SUMMARY_PATH = MACHINE_DIR / "account_balance_summaries.jsonl"
HTML_OVERVIEW_PATH = EXPORT_HTML_DIR / "fund_cash_loan_plan_overview.html"
REPORT_PATH = HUMAN_DIR / "fund_cash_loan_plan_report.md"
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
    "Proceed to v0.1.4 S14-P2 invoice tax plan as a separate run. Do not perform "
    "S14-P3, Stage 14 overall review, GitHub upload, protected source matching, "
    "lineage full check, formal report release, live connector, app reinstall, "
    "OpMe deep coupling, payment approval, payment execution, bank operation, "
    "loan management, invoice issuance, tax filing, policy filing, subsidy "
    "application, difference closure, or business execution in the S14-P1 run."
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


def validate_stage13_review_dependency() -> dict[str, Any]:
    result = validate_v014_s13_stage_review()
    if result.get("stage_id") != "S13":
        raise RuntimeError("S14-P1 requires validated v0.1.4 Stage 13 review")
    if result.get("stage_review_performed") is not True:
        raise RuntimeError("S14-P1 requires Stage 13 review performed")
    if result.get("next_phase") != "S14-P1":
        raise RuntimeError("Stage 13 review must route to S14-P1")
    if result.get("s14_p1_performed") is not False:
        raise RuntimeError("Stage 13 review dependency must not already include S14-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("Stage 13 review dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("v1.4 upload must remain deferred")
    raw = result.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_by_this_review",
        "raw_inbox_listed_by_this_review",
        "raw_inbox_mutated_by_this_review",
    ):
        if raw.get(key) is not False:
            raise RuntimeError(f"Stage 13 review raw boundary must keep {key}=false")
    return result


def validate_legacy_s14_p1_artifacts() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, str],
]:
    legacy_manifest, lanes, cash_pressure, loan_due, account_summary, html_outputs = (
        build_default_fund_cash_loan_plan_artifacts(generated_at="2026-07-05T06:45:00+10:00")
    )
    validate_fund_cash_loan_plan_artifacts(
        legacy_manifest,
        lanes,
        cash_pressure,
        loan_due,
        account_summary,
        html_outputs,
    )
    return legacy_manifest, lanes, cash_pressure, loan_due, account_summary, html_outputs


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

    for token in ("资金计划现金贷款", "账户清单", "月度现金", "资金计划", "贷款明细", "付款审批", "银行操作"):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S14-P1 token: {token}")
    for token in ("资金计划/现金/贷款线", "资金缺口", "账户汇总", "贷款到期提示", "不做付款操作"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing fund/cash/loan token: {token}")
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
        "roadmap_includes_s14_p1_requirements": True,
        "taskpack_includes_fund_cash_loan_line": True,
        "html_entry_includes_financial_fund_flow": True,
        "audit_script_inspects_links_inputs_buttons": True,
        "implementation_reflects_cash_pressure_loan_due_account_summary": False,
        "implementation_reflects_no_payment_or_bank_operation": False,
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
        "planning_signal_allowed": True,
        "complete_trusted_report_display_allowed": False,
        "full_trusted_report_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "delivery_allowed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "derived_amount_calculation_allowed": False,
        "cash_forecast_decision_allowed": False,
        "payment_approval_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "loan_management_action_allowed": False,
        "tax_filing_allowed": False,
        "invoice_issuance_allowed": False,
        "policy_filing_allowed": False,
        "subsidy_application_allowed": False,
        "automatic_external_action_allowed": False,
        "s14_p2_allowed": False,
        "s14_p3_allowed": False,
        "stage14_review_allowed": False,
        "github_upload_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "stage13_review_dependency_included": True,
        "s14_p1_fund_cash_loan_plan_scope_included": True,
        "s14_p2_invoice_tax_plan_scope_included": False,
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
    list[dict[str, Any]],
    dict[str, str],
]:
    generated_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    stage13 = validate_stage13_review_dependency()
    legacy_manifest, lanes, cash_pressure, loan_due, account_summary, html_outputs = validate_legacy_s14_p1_artifacts()
    validate_fund_cash_loan_plan_artifacts(
        legacy_manifest,
        lanes,
        cash_pressure,
        loan_due,
        account_summary,
        html_outputs,
    )
    baseline = load_v14_taskpack_baseline()
    baseline["implementation_reflects_cash_pressure_loan_due_account_summary"] = True
    baseline["implementation_reflects_no_payment_or_bank_operation"] = True
    summary = dict(legacy_manifest["summary"])

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s14_p1_fund_cash_loan_plan_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S14",
        "phase_id": "S14-P1",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S14P1T01", "S14P1T02", "S14P1T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_fund_cash_loan_plan_locked",
        "generated_at": generated_at,
        "git_head": git_output(["rev-parse", "HEAD"]),
        "s13_stage_review_dependency_validated": True,
        "legacy_s14_p1_dependency_validated": True,
        "v14_taskpack_dependency_validated": True,
        "source_taskpack_refs": {
            "v14_taskpack": V14_TASKPACK_PATH.as_posix(),
            "v14_roadmap": V14_ROADMAP_PATH.as_posix(),
            "v14_html_audit": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
        },
        "dependency_summary": {
            "stage13_phase_results": stage13.get("phase_results"),
            "stage13_open_findings": stage13.get("review_findings_summary", {}).get("open_finding_count"),
            "stage13_fixed_findings": stage13.get("review_findings_summary", {}).get("fixed_finding_count"),
            "stage13_next_phase": stage13.get("next_phase"),
            "legacy_s14p1_source_lanes": summary["source_lane_count"],
            "legacy_s14p1_cash_pressure_records": summary["cash_pressure_record_count"],
            "legacy_s14p1_loan_due_alerts": summary["loan_due_alert_count"],
            "legacy_s14p1_account_summaries": summary["account_balance_summary_count"],
        },
        "stage14_phase_progress": {
            "completed_phase_count": 1,
            "total_phase_count": 3,
            "derived_percent_bps": 3333,
            "derived_percent_label": "33.33%",
            "s14_p1_performed": True,
            "s14_p2_performed": False,
            "s14_p3_performed": False,
            "stage14_review_performed": False,
        },
        "fund_cash_loan_summary": {
            "source_lane_count": summary["source_lane_count"],
            "source_count": summary["source_count"],
            "field_mapping_count": summary["field_mapping_count"],
            "cash_pressure_record_count": summary["cash_pressure_record_count"],
            "loan_due_alert_count": summary["loan_due_alert_count"],
            "account_balance_summary_count": summary["account_balance_summary_count"],
            "html_output_count": summary["html_output_count"],
            "pending_reconciliation_count": summary["pending_reconciliation_count"],
            "report_grade_visible": summary["report_grade_visible"],
            "payment_operation_count": summary["payment_operation_count"],
            "bank_operation_count": summary["bank_operation_count"],
            "loan_management_action_count": summary["loan_management_action_count"],
            "required_source_lanes": list(REQUIRED_SOURCE_LANES),
            "required_output_record_types": list(REQUIRED_OUTPUT_RECORD_TYPES),
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
            "payment_approval_blocked",
            "payment_execution_blocked",
            "bank_operation_blocked",
            "loan_management_action_blocked",
            "invoice_issuance_blocked",
            "tax_filing_blocked",
            "policy_filing_blocked",
            "s14_p2_not_performed",
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
            "cash_pressure_signals": CASH_PRESSURE_PATH.as_posix(),
            "loan_due_alerts": LOAN_DUE_PATH.as_posix(),
            "account_balance_summaries": ACCOUNT_SUMMARY_PATH.as_posix(),
            "html_overview": HTML_OVERVIEW_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s14_p1_fund_cash_loan_plan.py",
            "focused_test": "KMFA/tests/test_v014_s14_p1_fund_cash_loan_plan.py",
        },
        "next_phase": "S14-P2",
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    return manifest, lanes, cash_pressure, loan_due, account_summary, html_outputs


def write_human_evidence(manifest: dict[str, Any]) -> None:
    summary = manifest["fund_cash_loan_summary"]
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S14-P1 Fund Cash Loan Plan",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `completed_validated_local_only_no_go_upload_deferred`",
                "- phase_scope: `v014_s14_p1_fund_cash_loan_plan_only`",
                f"- source_lanes: `{summary['source_lane_count']}`",
                f"- cash_pressure_signals: `{summary['cash_pressure_record_count']}`",
                f"- loan_due_alerts: `{summary['loan_due_alert_count']}`",
                f"- account_balance_summaries: `{summary['account_balance_summary_count']}`",
                f"- field_mappings: `{summary['field_mapping_count']}`",
                f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
                "- report_grade_visible: `D`",
                "- formal_report_allowed: `false`",
                "- business_decision_basis_allowed: `false`",
                "- payment_approval_allowed: `false`",
                "- bank_operation_allowed: `false`",
                "- loan_management_action_allowed: `false`",
                "- s14_p2_performed: `false`",
                "- s14_p3_performed: `false`",
                "- stage14_review_performed: `false`",
                "- github_upload_performed: `false`",
                "- raw_inbox_read_by_this_phase: `false`",
                "",
                "## Coverage",
                "",
                "- T1: 接入账户清单、月度现金、资金计划、贷款明细 4 条 public-safe source lanes。",
                "- T2: 输出 4 条现金压力信号、3 条贷款到期提示、3 条账户余额汇总和 1 个 HTML overview。",
                "- T3: 锁定不做付款审批、付款执行、银行操作、贷款管理动作、开票、纳税申报或正式资金结论。",
                "",
                "## Boundary",
                "",
                "- 不提交 raw business data、字段明文、真实金额、真实账号、Excel workbook、PDF、zip、sqlite/db、private CSV 或 credentials。",
                "- 不执行 S14-P2、S14-P3、Stage 14 review、GitHub upload、protected source matching、lineage full check、正式报告、外部接口、付款、银行、贷款管理、开票、税务、政策申报、补贴申请或业务执行。",
                "",
            ]
        ),
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S14-P1 Test Results",
                "",
                "- task_id: `KMFA-V014-S14-P1-FUND-CASH-LOAN-PLAN-20260705`",
                "- status: `pending_final_validation_capture`",
                "",
                "## Expected Commands",
                "",
                "- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s14_p1_fund_cash_loan_plan.py KMFA/tools/check_v014_s14_p1_fund_cash_loan_plan.py KMFA/tests/test_v014_s14_p1_fund_cash_loan_plan.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s14_p1_fund_cash_loan_plan.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s14_p1_fund_cash_loan_plan.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s14_p1_fund_cash_loan_plan.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s14_p1_fund_cash_loan_plan -q`",
                "- governance validators and safety scans before commit",
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S14-P1 Risk Register",
                "",
                "| Risk | Control | Status |",
                "|---|---|---|",
                "| 资金计划信号被误用为付款或银行操作依据 | D 级展示、payment/bank/loan actions 全部 false | controlled |",
                "| S14-P1 越界进入开票纳税、政策证据、复审或 upload | validator 检查 S14-P2/P3、Stage 14 review 和 GitHub upload 均为 false | controlled |",
                "| raw/private 数据泄漏 | 只复用 public-safe metadata，raw inbox read/list/stat/hash/mutation 全为 false | controlled |",
                "",
            ]
        ),
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S14-P1 Rollback Plan",
                "",
                "- 删除 `KMFA/stage_artifacts/V014_S14_P1_FUND_CASH_LOAN_PLAN/`。",
                "- 删除 `KMFA/tools/v014_s14_p1_fund_cash_loan_plan.py` 和 `KMFA/tools/check_v014_s14_p1_fund_cash_loan_plan.py`。",
                "- 删除 `KMFA/tests/test_v014_s14_p1_fund_cash_loan_plan.py`。",
                "- 回滚本 phase 的治理 registry、开发记录、功能清单和模型参数文件更新。",
                "",
            ]
        ),
    )


def generate() -> dict[str, Any]:
    manifest, lanes, cash_pressure, loan_due, account_summary, html_outputs = build_manifest()
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(LANES_PATH, lanes)
    _write_jsonl(CASH_PRESSURE_PATH, cash_pressure)
    _write_jsonl(LOAN_DUE_PATH, loan_due)
    _write_jsonl(ACCOUNT_SUMMARY_PATH, account_summary)
    _write_text(HTML_OVERVIEW_PATH, html_outputs["fund_cash_loan_plan_overview"])
    write_human_evidence(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["fund_cash_loan_summary"]
    print(
        "PASS: KMFA v0.1.4 S14-P1 fund cash loan plan evidence generated "
        f"(source_lanes={summary['source_lane_count']}, cash_pressure={summary['cash_pressure_record_count']}, "
        f"loan_due={summary['loan_due_alert_count']}, account_summaries={summary['account_balance_summary_count']}, "
        "formal_report=false, payment=false, bank=false, loan_management=false, "
        "s14_p2=false, s14_p3=false, stage14_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
