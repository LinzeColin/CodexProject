#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S13-P2 collection receivable aging evidence.

This phase replays the existing public-safe S13-P2 collection and receivable
aging priority model under the v1.4 S13-P1 dependency and upload-deferral
contract. It does not read raw/private data, run S13-P3, perform Stage 13
review, release a formal collection report, execute business actions, or upload
to GitHub.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s13_p1_financial_operating_report import (
    validate_v014_s13_p1_financial_operating_report,
)
from KMFA.tools.collection_receivable_aging import (
    REQUIRED_ISSUE_TYPES,
    REQUIRED_SOURCE_LANES,
    build_default_collection_receivable_aging_artifacts,
    validate_collection_receivable_aging_artifacts,
)


TASK_ID = "KMFA-V014-S13-P2-COLLECTION-RECEIVABLE-AGING-20260705"
ACCEPTANCE_ID = "ACC-V014-S13-P2-COLLECTION-RECEIVABLE-AGING"
SCHEMA_VERSION = "kmfa.v014_s13_p2_collection_receivable_aging.v1"
PHASE_SCOPE = "v014_s13_p2_collection_receivable_aging_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S13_P2_COLLECTION_RECEIVABLE_AGING")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
EXPORT_HTML_DIR = OUTPUT_DIR / "exports" / "html"
MANIFEST_PATH = MACHINE_DIR / "collection_receivable_aging_manifest.json"
LANES_PATH = MACHINE_DIR / "collection_receivable_aging_source_lanes.jsonl"
PRIORITY_PATH = MACHINE_DIR / "collection_receivable_aging_priority_items.jsonl"
RESPONSIBILITY_PATH = MACHINE_DIR / "collection_receivable_aging_responsibility_items.jsonl"
HTML_PRIORITY_PATH = EXPORT_HTML_DIR / "collection_receivable_aging_priority.html"
REPORT_PATH = HUMAN_DIR / "collection_receivable_aging_report.md"
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
    "Proceed to v0.1.4 S13-P3 cross-table review as a separate run. "
    "Do not perform Stage 13 overall review, GitHub upload, protected source "
    "matching, lineage full check, formal report release, live connector, app "
    "reinstall, OpMe deep coupling, legal collection, payment, tax, invoice, or "
    "business execution in the S13-P2 run."
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


def validate_s13_p1_dependency() -> dict[str, Any]:
    result = validate_v014_s13_p1_financial_operating_report()
    if result.get("stage_id") != "S13" or result.get("phase_id") != "S13-P1":
        raise RuntimeError("S13-P2 requires validated v0.1.4 S13-P1")
    if result.get("next_phase") != "S13-P2":
        raise RuntimeError("S13-P1 dependency must route to S13-P2")
    progress = result.get("stage13_phase_progress", {})
    if progress.get("s13_p1_performed") is not True:
        raise RuntimeError("S13-P1 dependency must be performed")
    if progress.get("s13_p2_performed") is not False:
        raise RuntimeError("S13-P1 dependency must not already include S13-P2")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("S13-P1 dependency must not include GitHub upload")
    if result.get("github_upload", {}).get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("v1.4 upload must remain deferred")
    raw = result.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_by_this_phase",
        "raw_inbox_listed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
    ):
        if raw.get(key) is not False:
            raise RuntimeError(f"S13-P1 raw boundary must keep {key}=false")
    return result


def validate_legacy_s13_p2_artifacts() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, str],
]:
    legacy_manifest, source_lanes, priority_items, responsibility_items, html_outputs = (
        build_default_collection_receivable_aging_artifacts(generated_at="2026-07-05T05:20:00+10:00")
    )
    validate_collection_receivable_aging_artifacts(
        legacy_manifest, source_lanes, priority_items, responsibility_items, html_outputs
    )
    return legacy_manifest, source_lanes, priority_items, responsibility_items, html_outputs


def load_v14_html_uiux_baseline() -> dict[str, Any]:
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

    for token in ("回款应收账龄", "已开票未回款", "输出回款优先级和责任事项"):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S13-P2 token: {token}")
    for token in ("回款/应收/账龄线", "催收优先级", "银行回款 ↔ 应收账龄"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing collection receivable token: {token}")
    for token in ("回款应收", "经营分析报告", "待处理事项工作台", "数据源检查板"):
        if token not in entry_text:
            raise RuntimeError(f"v1.4 HTML entry missing collection-flow token: {token}")
    if "button" not in script_text or "input" not in script_text or "link" not in script_text:
        raise RuntimeError("v1.4 audit script must inspect links, inputs, and buttons")

    return {
        "taskpack_html_requirement_read": True,
        "human_flow_entry_exists": V14_HTML_ENTRY_PATH.exists(),
        "human_flow_audit_script_exists": V14_HTML_AUDIT_SCRIPT_PATH.exists(),
        "human_flow_audit_report_exists": V14_HTML_AUDIT_REPORT_PATH.exists(),
        **report_counts,
        "source_package_manifest_counts_match_report": True,
        "roadmap_includes_s13_p2_requirements": True,
        "taskpack_includes_collection_receivable_line": True,
        "audit_script_inspects_links_inputs_buttons": True,
        "implementation_reflects_collection_receivable_aging": False,
        "implementation_reflects_priority_and_responsibility": False,
        "implementation_reflects_no_external_action_limits": False,
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
        "collection_receivable_priority_draft_allowed": True,
        "responsibility_item_draft_allowed": True,
        "complete_trusted_report_display_allowed": False,
        "full_trusted_report_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "collection_action_allowed": False,
        "legal_collection_decision_allowed": False,
        "payment_or_bank_operation_allowed": False,
        "tax_filing_allowed": False,
        "invoice_operation_allowed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "derived_amount_calculation_allowed": False,
        "automatic_external_action_allowed": False,
        "s13_p1_reopen_allowed": False,
        "s13_p3_allowed": False,
        "stage13_review_allowed": False,
        "github_upload_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s13_p1_financial_operating_report_dependency_included": True,
        "s13_p2_collection_receivable_aging_scope_included": True,
        "s13_p3_cross_table_review_scope_included": False,
        "stage13_review_scope_included": False,
        "lineage_full_check_scope_included": False,
        "protected_source_matching_scope_included": False,
        "raw_value_matching_scope_included": False,
        "formal_report_scope_included": False,
        "collection_action_scope_included": False,
        "legal_collection_scope_included": False,
        "payment_or_bank_operation_scope_included": False,
        "invoice_operation_scope_included": False,
        "tax_filing_scope_included": False,
        "external_connector_scope_included": False,
        "live_ui_runtime_scope_included": False,
        "app_reinstall_scope_included": False,
        "opme_deep_coupling_scope_included": False,
        "github_upload_scope_included": False,
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
        "collection_action_list_committed": False,
        "legal_collection_decision_committed": False,
        "payment_or_bank_operation_committed": False,
        "tax_or_invoice_operation_committed": False,
    }


def _rewrite_priority_items_for_v014(priority_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rewritten: list[dict[str, Any]] = []
    for item in priority_items:
        row = dict(item)
        row["stage_phase"] = "S13-P2"
        row["v014_dependency_ref"] = "KMFA/stage_artifacts/V014_S13_P1_FINANCIAL_OPERATING_REPORT/machine/financial_operating_report_manifest.json"
        row["html_draft_ref"] = HTML_PRIORITY_PATH.as_posix()
        rewritten.append(row)
    return rewritten


def _rewrite_responsibility_items_for_v014(responsibility_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rewritten: list[dict[str, Any]] = []
    for item in responsibility_items:
        row = dict(item)
        row["stage_phase"] = "S13-P2"
        row["v014_dependency_ref"] = "KMFA/stage_artifacts/V014_S13_P1_FINANCIAL_OPERATING_REPORT/machine/financial_operating_report_manifest.json"
        rewritten.append(row)
    return rewritten


def build_manifest() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, str],
]:
    generated_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    s13_p1 = validate_s13_p1_dependency()
    legacy_manifest, source_lanes, legacy_priority_items, legacy_responsibility_items, html_outputs = (
        validate_legacy_s13_p2_artifacts()
    )
    priority_items = _rewrite_priority_items_for_v014(legacy_priority_items)
    responsibility_items = _rewrite_responsibility_items_for_v014(legacy_responsibility_items)
    validate_collection_receivable_aging_artifacts(
        legacy_manifest, source_lanes, priority_items, responsibility_items, html_outputs
    )
    baseline = load_v14_html_uiux_baseline()
    baseline["implementation_reflects_collection_receivable_aging"] = True
    baseline["implementation_reflects_priority_and_responsibility"] = True
    baseline["implementation_reflects_no_external_action_limits"] = True
    summary = dict(legacy_manifest["summary"])

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s13_p2_collection_receivable_aging_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S13",
        "phase_id": "S13-P2",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S13P2T01", "S13P2T02", "S13P2T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_collection_receivable_aging_locked",
        "generated_at": generated_at,
        "git_head": git_output(["rev-parse", "HEAD"]),
        "s13_p1_dependency_validated": True,
        "legacy_s13_p2_dependency_validated": True,
        "v14_html_uiux_dependency_validated": True,
        "source_taskpack_refs": {
            "v14_taskpack": V14_TASKPACK_PATH.as_posix(),
            "v14_roadmap": V14_ROADMAP_PATH.as_posix(),
            "v14_html_audit": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
        },
        "dependency_summary": {
            "s13p1_completed_phase_count": s13_p1.get("stage13_phase_progress", {}).get("completed_phase_count"),
            "s13p1_next_phase": s13_p1.get("next_phase"),
            "legacy_s13p2_source_lanes": summary["source_lane_count"],
            "legacy_s13p2_priority_items": summary["priority_item_count"],
            "legacy_s13p2_responsibility_items": summary["responsibility_item_count"],
        },
        "stage13_phase_progress": {
            "completed_phase_count": 2,
            "total_phase_count": 3,
            "derived_percent_bps": 6667,
            "derived_percent_label": "66.67%",
            "s13_p1_performed": True,
            "s13_p2_performed": True,
            "s13_p3_performed": False,
            "stage13_review_performed": False,
        },
        "collection_receivable_summary": {
            "source_lane_count": summary["source_lane_count"],
            "source_count": summary["source_count"],
            "field_mapping_count": summary["field_mapping_count"],
            "required_issue_type_count": summary["required_issue_type_count"],
            "priority_item_count": summary["priority_item_count"],
            "responsibility_item_count": summary["responsibility_item_count"],
            "html_draft_count": summary["html_draft_count"],
            "pending_reconciliation_count": summary["pending_reconciliation_count"],
            "report_grade_visible": summary["report_grade_visible"],
            "formal_report_count": summary["formal_report_count"],
            "business_decision_basis_count": summary["business_decision_basis_count"],
            "collection_action_count": summary["collection_action_count"],
            "legal_collection_decision_count": summary["legal_collection_decision_count"],
            "payment_or_bank_operation_count": summary["payment_or_bank_operation_count"],
            "required_source_lanes": list(REQUIRED_SOURCE_LANES),
            "required_issue_types": list(REQUIRED_ISSUE_TYPES),
        },
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "raw_data_boundary": _raw_boundary(),
        "public_repo_safety": _public_repo_safety(),
        "v14_html_uiux_baseline": baseline,
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
            "legal_collection_decision_blocked",
            "payment_or_bank_operation_blocked",
            "invoice_operation_blocked",
            "tax_filing_blocked",
            "s13_p3_not_performed",
            "stage13_review_not_performed",
            "lineage_full_check_not_performed",
            "protected_source_matching_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "app_reinstall_not_performed",
            "business_execution_blocked",
        ],
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "source_lanes": LANES_PATH.as_posix(),
            "priority_items": PRIORITY_PATH.as_posix(),
            "responsibility_items": RESPONSIBILITY_PATH.as_posix(),
            "priority_html": HTML_PRIORITY_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s13_p2_collection_receivable_aging.py",
            "focused_test": "KMFA/tests/test_v014_s13_p2_collection_receivable_aging.py",
        },
        "next_phase": "S13-P3",
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    return manifest, source_lanes, priority_items, responsibility_items, html_outputs


def write_human_evidence(manifest: dict[str, Any]) -> None:
    summary = manifest["collection_receivable_summary"]
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S13-P2 Collection Receivable Aging",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `completed_validated_local_only_no_go_upload_deferred`",
                "- phase_scope: `v014_s13_p2_collection_receivable_aging_only`",
                f"- source_lanes: `{summary['source_lane_count']}`",
                f"- sources: `{summary['source_count']}`",
                f"- field_mappings: `{summary['field_mapping_count']}`",
                f"- issue_types: `{summary['required_issue_type_count']}`",
                f"- priority_items: `{summary['priority_item_count']}`",
                f"- responsibility_items: `{summary['responsibility_item_count']}`",
                f"- html_drafts: `{summary['html_draft_count']}`",
                f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
                "- report_grade_visible: `D`",
                "- formal_report_allowed: `false`",
                "- business_decision_basis_allowed: `false`",
                "- legal_collection_decision_allowed: `false`",
                "- payment_or_bank_operation_allowed: `false`",
                "- s13_p3_performed: `false`",
                "- stage13_review_performed: `false`",
                "- github_upload_performed: `false`",
                "- raw_inbox_read_by_this_phase: `false`",
                "",
                "## Coverage",
                "",
                "- T1: 接入回款表、应收账龄、客户账龄、日记账、开票计划 5 条 public-safe source lanes。",
                "- T2: 锁定已开票未回款、完工未结算、结算未开票、超期应收 4 类问题候选。",
                "- T3: 输出 4 条回款优先级草案和 4 条责任事项草案，并显示报告等级 D 与执行限制。",
                "",
                "## Boundary",
                "",
                "- 不提交 raw business data、字段明文、真实金额、真实账号、Excel workbook、PDF、zip、sqlite/db、private CSV 或 credentials。",
                "- 不执行 S13-P3、Stage 13 review、GitHub upload、protected source matching、lineage full check、正式报告、催收、法务、付款、银行、开票、税务或业务执行。",
                "",
            ]
        ),
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S13-P2 Test Results",
                "",
                "- task_id: `KMFA-V014-S13-P2-COLLECTION-RECEIVABLE-AGING-20260705`",
                "- status: `pending_final_validation_capture`",
                "",
                "## Expected Commands",
                "",
                "- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s13_p2_collection_receivable_aging.py KMFA/tools/check_v014_s13_p2_collection_receivable_aging.py KMFA/tests/test_v014_s13_p2_collection_receivable_aging.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s13_p2_collection_receivable_aging.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s13_p2_collection_receivable_aging.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s13_p2_collection_receivable_aging -q`",
                "- governance validators and safety scans before commit",
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S13-P2 Risk Register",
                "",
                "| Risk | Control | Status |",
                "|---|---|---|",
                "| 回款优先级被误用为催收或经营决策 | 报告等级 D、formal_report_allowed=false、business_decision_basis_allowed=false、legal_collection_decision_allowed=false | controlled |",
                "| S13-P2 越界进入跨表复核、复审或 upload | validator 检查 S13-P3、Stage 13 review 和 GitHub upload 均为 false | controlled |",
                "| raw/private 数据泄漏 | 只复用 public-safe metadata，raw inbox read/list/stat/hash/mutation 全为 false | controlled |",
                "",
            ]
        ),
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S13-P2 Rollback Plan",
                "",
                "- 删除 `KMFA/stage_artifacts/V014_S13_P2_COLLECTION_RECEIVABLE_AGING/`。",
                "- 删除 `KMFA/tools/v014_s13_p2_collection_receivable_aging.py` 和 `KMFA/tools/check_v014_s13_p2_collection_receivable_aging.py`。",
                "- 删除 `KMFA/tests/test_v014_s13_p2_collection_receivable_aging.py`。",
                "- 回滚本 phase 的治理 registry、开发记录、功能清单和模型参数文件更新。",
                "",
            ]
        ),
    )


def generate() -> dict[str, Any]:
    manifest, source_lanes, priority_items, responsibility_items, html_outputs = build_manifest()
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(LANES_PATH, source_lanes)
    _write_jsonl(PRIORITY_PATH, priority_items)
    _write_jsonl(RESPONSIBILITY_PATH, responsibility_items)
    _write_text(HTML_PRIORITY_PATH, html_outputs["collection_receivable_aging_priority"])
    write_human_evidence(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["collection_receivable_summary"]
    print(
        "PASS: KMFA v0.1.4 S13-P2 collection receivable aging evidence generated "
        f"(source_lanes={summary['source_lane_count']}, sources={summary['source_count']}, "
        f"priority_items={summary['priority_item_count']}, responsibility_items={summary['responsibility_item_count']}, "
        f"html={summary['html_draft_count']}, field_mappings={summary['field_mapping_count']}, "
        "formal_report=false, legal_collection=false, payment_or_bank=false, "
        "s13_p3=false, stage13_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
