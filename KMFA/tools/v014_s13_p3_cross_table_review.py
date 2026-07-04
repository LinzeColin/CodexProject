#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S13-P3 cross-table review evidence.

This phase replays the existing public-safe S13-P3 cross-table review model
under the v1.4 S13-P2 dependency and upload-deferral contract. It does not read
raw/private data, perform Stage 13 review, close differences, release a formal
report, execute business actions, or upload to GitHub.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s13_p2_collection_receivable_aging import (
    validate_v014_s13_p2_collection_receivable_aging,
)
from KMFA.tools.cross_table_review import (
    REQUIRED_REVIEW_DIMENSIONS,
    build_default_cross_table_review_artifacts,
    validate_cross_table_review_artifacts,
)


TASK_ID = "KMFA-V014-S13-P3-CROSS-TABLE-REVIEW-20260705"
ACCEPTANCE_ID = "ACC-V014-S13-P3-CROSS-TABLE-REVIEW"
SCHEMA_VERSION = "kmfa.v014_s13_p3_cross_table_review.v1"
PHASE_SCOPE = "v014_s13_p3_cross_table_review_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S13_P3_CROSS_TABLE_REVIEW")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
EXPORT_HTML_DIR = OUTPUT_DIR / "exports" / "html"
MANIFEST_PATH = MACHINE_DIR / "cross_table_review_manifest.json"
CHECKS_PATH = MACHINE_DIR / "cross_table_review_checks.jsonl"
DIFFERENCE_QUEUE_PATH = MACHINE_DIR / "cross_table_difference_queue.jsonl"
QUALITY_REPORT_PATH = MACHINE_DIR / "operating_report_quality_report.json"
HTML_QUALITY_PATH = EXPORT_HTML_DIR / "cross_table_quality_report.html"
REPORT_PATH = HUMAN_DIR / "cross_table_review_report.md"
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
    "Proceed to v0.1.4 Stage 13 overall review as a separate run. "
    "Do not perform GitHub upload, S14, protected source matching, lineage full "
    "check, formal report release, live connector, app reinstall, OpMe deep "
    "coupling, legal collection, payment, tax, invoice, difference closure, or "
    "business execution in the S13-P3 run."
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


def validate_s13_p2_dependency() -> dict[str, Any]:
    result = validate_v014_s13_p2_collection_receivable_aging()
    if result.get("stage_id") != "S13" or result.get("phase_id") != "S13-P2":
        raise RuntimeError("S13-P3 requires validated v0.1.4 S13-P2")
    if result.get("next_phase") != "S13-P3":
        raise RuntimeError("S13-P2 dependency must route to S13-P3")
    progress = result.get("stage13_phase_progress", {})
    if progress.get("s13_p1_performed") is not True or progress.get("s13_p2_performed") is not True:
        raise RuntimeError("S13-P3 requires S13-P1 and S13-P2 performed")
    if progress.get("s13_p3_performed") is not False:
        raise RuntimeError("S13-P2 dependency must not already include S13-P3")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("S13-P2 dependency must not include GitHub upload")
    if result.get("github_upload", {}).get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("v1.4 upload must remain deferred")
    raw = result.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_by_this_phase",
        "raw_inbox_listed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
    ):
        if raw.get(key) is not False:
            raise RuntimeError(f"S13-P2 raw boundary must keep {key}=false")
    return result


def validate_legacy_s13_p3_artifacts() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, str],
]:
    legacy_manifest, review_checks, difference_queue, quality_report, html_outputs = (
        build_default_cross_table_review_artifacts(generated_at="2026-07-05T07:40:00+10:00")
    )
    validate_cross_table_review_artifacts(
        legacy_manifest, review_checks, difference_queue, quality_report, html_outputs
    )
    return legacy_manifest, review_checks, difference_queue, quality_report, html_outputs


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

    for token in ("跨表复核", "项目、客户、金额、时间跨表一致性检查", "不一致进入差异队列", "经营报表质量报告"):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S13-P3 token: {token}")
    for token in ("跨表汇总", "差异队列", "不允许在前端或报告层直接改数", "同一个原始数据"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing cross-table token: {token}")
    for token in ("经营分析报告", "待处理事项工作台", "数据源检查板", "回款应收"):
        if token not in entry_text:
            raise RuntimeError(f"v1.4 HTML entry missing cross-table flow token: {token}")
    if "button" not in script_text or "input" not in script_text or "link" not in script_text:
        raise RuntimeError("v1.4 audit script must inspect links, inputs, and buttons")

    return {
        "taskpack_html_requirement_read": True,
        "human_flow_entry_exists": V14_HTML_ENTRY_PATH.exists(),
        "human_flow_audit_script_exists": V14_HTML_AUDIT_SCRIPT_PATH.exists(),
        "human_flow_audit_report_exists": V14_HTML_AUDIT_REPORT_PATH.exists(),
        **report_counts,
        "source_package_manifest_counts_match_report": True,
        "roadmap_includes_s13_p3_requirements": True,
        "taskpack_includes_cross_table_consistency_rules": True,
        "audit_script_inspects_links_inputs_buttons": True,
        "implementation_reflects_cross_table_review": False,
        "implementation_reflects_difference_queue": False,
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
        "cross_table_review_evidence_allowed": True,
        "difference_queue_output_allowed": True,
        "operating_report_quality_report_allowed": True,
        "complete_trusted_report_display_allowed": False,
        "full_trusted_report_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "legal_collection_decision_allowed": False,
        "payment_or_bank_operation_allowed": False,
        "tax_filing_allowed": False,
        "invoice_operation_allowed": False,
        "difference_auto_resolution_allowed": False,
        "auto_source_selection_allowed": False,
        "difference_closure_allowed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "derived_amount_calculation_allowed": False,
        "automatic_external_action_allowed": False,
        "s13_p1_reopen_allowed": False,
        "s13_p2_reopen_allowed": False,
        "stage13_review_allowed": False,
        "github_upload_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s13_p1_financial_operating_report_dependency_included": True,
        "s13_p2_collection_receivable_aging_dependency_included": True,
        "s13_p3_cross_table_review_scope_included": True,
        "stage13_review_scope_included": False,
        "s14_scope_included": False,
        "lineage_full_check_scope_included": False,
        "protected_source_matching_scope_included": False,
        "raw_value_matching_scope_included": False,
        "formal_report_scope_included": False,
        "difference_closure_scope_included": False,
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
        "difference_closure_committed": False,
        "legal_collection_decision_committed": False,
        "payment_or_bank_operation_committed": False,
        "tax_or_invoice_operation_committed": False,
    }


def _rewrite_checks_for_v014(review_checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rewritten: list[dict[str, Any]] = []
    for row in review_checks:
        item = dict(row)
        item["v014_s13_p1_ref"] = "KMFA/stage_artifacts/V014_S13_P1_FINANCIAL_OPERATING_REPORT/machine/financial_operating_report_manifest.json"
        item["v014_s13_p2_ref"] = "KMFA/stage_artifacts/V014_S13_P2_COLLECTION_RECEIVABLE_AGING/machine/collection_receivable_aging_manifest.json"
        item["html_quality_ref"] = HTML_QUALITY_PATH.as_posix()
        rewritten.append(item)
    return rewritten


def _rewrite_difference_queue_for_v014(difference_queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rewritten: list[dict[str, Any]] = []
    for row in difference_queue:
        item = dict(row)
        item["v014_review_ref"] = MANIFEST_PATH.as_posix()
        item["resolution_status"] = "pending_owner_or_authorized_review"
        rewritten.append(item)
    return rewritten


def _rewrite_quality_report_for_v014(quality_report: dict[str, Any]) -> dict[str, Any]:
    rewritten = dict(quality_report)
    rewritten["v014_review_ref"] = MANIFEST_PATH.as_posix()
    rewritten["html_quality_ref"] = HTML_QUALITY_PATH.as_posix()
    return rewritten


def build_manifest() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, str],
]:
    generated_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    s13_p2 = validate_s13_p2_dependency()
    legacy_manifest, legacy_checks, legacy_queue, legacy_quality_report, html_outputs = (
        validate_legacy_s13_p3_artifacts()
    )
    review_checks = _rewrite_checks_for_v014(legacy_checks)
    difference_queue = _rewrite_difference_queue_for_v014(legacy_queue)
    quality_report = _rewrite_quality_report_for_v014(legacy_quality_report)
    validate_cross_table_review_artifacts(
        legacy_manifest, review_checks, difference_queue, quality_report, html_outputs
    )
    baseline = load_v14_html_uiux_baseline()
    baseline["implementation_reflects_cross_table_review"] = True
    baseline["implementation_reflects_difference_queue"] = True
    baseline["implementation_reflects_no_external_action_limits"] = True
    summary = dict(legacy_manifest["summary"])

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s13_p3_cross_table_review_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S13",
        "phase_id": "S13-P3",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S13P3T01", "S13P3T02", "S13P3T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_cross_table_review_locked",
        "generated_at": generated_at,
        "git_head": git_output(["rev-parse", "HEAD"]),
        "s13_p2_dependency_validated": True,
        "legacy_s13_p3_dependency_validated": True,
        "v14_html_uiux_dependency_validated": True,
        "source_taskpack_refs": {
            "v14_taskpack": V14_TASKPACK_PATH.as_posix(),
            "v14_roadmap": V14_ROADMAP_PATH.as_posix(),
            "v14_html_audit": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
        },
        "dependency_summary": {
            "s13p2_completed_phase_count": s13_p2.get("stage13_phase_progress", {}).get("completed_phase_count"),
            "s13p2_next_phase": s13_p2.get("next_phase"),
            "legacy_s13p3_review_dimensions": summary["review_dimension_count"],
            "legacy_s13p3_difference_queue": summary["difference_queue_count"],
            "legacy_s13p3_quality_report": summary["quality_report_count"],
        },
        "stage13_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s13_p1_performed": True,
            "s13_p2_performed": True,
            "s13_p3_performed": True,
            "stage13_review_performed": False,
        },
        "cross_table_review_summary": {
            "review_dimension_count": summary["review_dimension_count"],
            "difference_queue_count": summary["difference_queue_count"],
            "quality_report_count": summary["quality_report_count"],
            "html_draft_count": 1,
            "pending_reconciliation_count": summary["pending_reconciliation_count"],
            "report_grade_visible": summary["report_grade_visible"],
            "formal_report_count": 0,
            "business_decision_basis_count": 0,
            "difference_auto_resolution_count": 0,
            "difference_closure_count": 0,
            "payment_or_bank_operation_count": 0,
            "legal_collection_decision_count": 0,
            "required_review_dimensions": list(REQUIRED_REVIEW_DIMENSIONS),
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
            "difference_auto_resolution_blocked",
            "difference_closure_blocked",
            "legal_collection_decision_blocked",
            "payment_or_bank_operation_blocked",
            "invoice_operation_blocked",
            "tax_filing_blocked",
            "stage13_review_not_performed",
            "s14_not_performed",
            "lineage_full_check_not_performed",
            "protected_source_matching_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "app_reinstall_not_performed",
            "business_execution_blocked",
        ],
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "review_checks": CHECKS_PATH.as_posix(),
            "difference_queue": DIFFERENCE_QUEUE_PATH.as_posix(),
            "quality_report": QUALITY_REPORT_PATH.as_posix(),
            "quality_html": HTML_QUALITY_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s13_p3_cross_table_review.py",
            "focused_test": "KMFA/tests/test_v014_s13_p3_cross_table_review.py",
        },
        "next_phase": "S13_STAGE_REVIEW",
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    return manifest, review_checks, difference_queue, quality_report, html_outputs


def write_human_evidence(manifest: dict[str, Any]) -> None:
    summary = manifest["cross_table_review_summary"]
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S13-P3 Cross-Table Review",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `completed_validated_local_only_no_go_upload_deferred`",
                "- phase_scope: `v014_s13_p3_cross_table_review_only`",
                f"- review_dimensions: `{summary['review_dimension_count']}`",
                f"- difference_queue_items: `{summary['difference_queue_count']}`",
                f"- quality_reports: `{summary['quality_report_count']}`",
                f"- html_drafts: `{summary['html_draft_count']}`",
                f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
                "- report_grade_visible: `D`",
                "- formal_report_allowed: `false`",
                "- business_decision_basis_allowed: `false`",
                "- difference_auto_resolution_allowed: `false`",
                "- stage13_review_performed: `false`",
                "- github_upload_performed: `false`",
                "- raw_inbox_read_by_this_phase: `false`",
                "",
                "## Coverage",
                "",
                "- T1: 覆盖项目、客户、金额、时间 4 个 public-safe 跨表一致性检查维度。",
                "- T2: 将 4 类不一致全部进入人工差异队列，不自动选源、不自动修正、不关闭差异。",
                "- T3: 输出 1 份经营报表质量报告和 1 个 HTML evidence，继续显示 D 级与限制。",
                "",
                "## Boundary",
                "",
                "- 不提交 raw business data、字段明文、真实金额、真实账号、Excel workbook、PDF、zip、sqlite/db、private CSV 或 credentials。",
                "- 不执行 Stage 13 review、S14、GitHub upload、protected source matching、lineage full check、正式报告、差异关闭、法务、付款、银行、开票、税务或业务执行。",
                "",
            ]
        ),
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S13-P3 Test Results",
                "",
                "- task_id: `KMFA-V014-S13-P3-CROSS-TABLE-REVIEW-20260705`",
                "- status: `pending_final_validation_capture`",
                "",
                "## Expected Commands",
                "",
                "- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s13_p3_cross_table_review.py KMFA/tools/check_v014_s13_p3_cross_table_review.py KMFA/tests/test_v014_s13_p3_cross_table_review.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s13_p3_cross_table_review.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s13_p3_cross_table_review.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s13_p3_cross_table_review -q`",
                "- governance validators and safety scans before commit",
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S13-P3 Risk Register",
                "",
                "| Risk | Control | Status |",
                "|---|---|---|",
                "| 跨表复核被误用为正式经营报告 | 报告等级 D、formal_report_allowed=false、business_decision_basis_allowed=false | controlled |",
                "| 差异队列被自动关闭或自动选源 | validator 检查 difference_auto_resolution_allowed=false、auto_source_selection_allowed=false、difference_closure_count=0 | controlled |",
                "| S13-P3 越界进入 Stage 13 review 或 upload | validator 检查 Stage 13 review、S14、GitHub upload 均为 false | controlled |",
                "| raw/private 数据泄漏 | 只复用 public-safe metadata，raw inbox read/list/stat/hash/mutation 全为 false | controlled |",
                "",
            ]
        ),
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S13-P3 Rollback Plan",
                "",
                "- 删除 `KMFA/stage_artifacts/V014_S13_P3_CROSS_TABLE_REVIEW/`。",
                "- 删除 `KMFA/tools/v014_s13_p3_cross_table_review.py` 和 `KMFA/tools/check_v014_s13_p3_cross_table_review.py`。",
                "- 删除 `KMFA/tests/test_v014_s13_p3_cross_table_review.py`。",
                "- 回滚本 phase 的治理 registry、开发记录、功能清单和模型参数文件更新。",
                "",
            ]
        ),
    )


def generate() -> dict[str, Any]:
    manifest, review_checks, difference_queue, quality_report, html_outputs = build_manifest()
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(CHECKS_PATH, review_checks)
    _write_jsonl(DIFFERENCE_QUEUE_PATH, difference_queue)
    _write_json(QUALITY_REPORT_PATH, quality_report)
    _write_text(HTML_QUALITY_PATH, html_outputs["cross_table_quality_report"])
    write_human_evidence(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["cross_table_review_summary"]
    print(
        "PASS: KMFA v0.1.4 S13-P3 cross-table review evidence generated "
        f"(review_dimensions={summary['review_dimension_count']}, "
        f"difference_queue={summary['difference_queue_count']}, "
        f"quality_report={summary['quality_report_count']}, html={summary['html_draft_count']}, "
        f"pending_reconciliation={summary['pending_reconciliation_count']}, "
        "report_grade=D, formal_report=false, difference_auto_resolution=false, "
        "stage13_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
