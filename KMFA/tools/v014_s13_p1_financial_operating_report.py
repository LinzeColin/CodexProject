#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S13-P1 financial operating report evidence.

This phase replays the existing public-safe S13-P1 financial operating report
draft model under the v1.4 Stage 12 review dependency and upload-deferral
contract. It does not read raw/private data, run S13-P2/S13-P3, perform Stage
13 review, complete lineage, release a formal report, execute business actions,
or upload to GitHub.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s12_stage_review import validate_v014_s12_stage_review
from KMFA.tools.financial_operating_report import (
    REPORT_SECTION_TITLES,
    REQUIRED_DRAFT_IDS,
    REQUIRED_SOURCE_LANES,
    build_default_financial_operating_report_artifacts,
    validate_financial_operating_report_artifacts,
)


TASK_ID = "KMFA-V014-S13-P1-FINANCIAL-OPERATING-REPORT-20260705"
ACCEPTANCE_ID = "ACC-V014-S13-P1-FINANCIAL-OPERATING-REPORT"
SCHEMA_VERSION = "kmfa.v014_s13_p1_financial_operating_report.v1"
PHASE_SCOPE = "v014_s13_p1_financial_operating_report_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S13_P1_FINANCIAL_OPERATING_REPORT")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
EXPORT_HTML_DIR = OUTPUT_DIR / "exports" / "html"
MANIFEST_PATH = MACHINE_DIR / "financial_operating_report_manifest.json"
LANES_PATH = MACHINE_DIR / "financial_operating_report_source_lanes.jsonl"
DRAFTS_PATH = MACHINE_DIR / "financial_operating_report_drafts.jsonl"
HTML_WEEKLY_PATH = EXPORT_HTML_DIR / "financial_operating_weekly_draft.html"
HTML_MONTHLY_PATH = EXPORT_HTML_DIR / "financial_operating_monthly_draft.html"
REPORT_PATH = HUMAN_DIR / "financial_operating_report.md"
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
    "Proceed to v0.1.4 S13-P2 collection receivable aging as a separate run. "
    "Do not perform S13-P3, Stage 13 overall review, GitHub upload, protected "
    "source matching, lineage full check, formal report release, live connector, "
    "app reinstall, OpMe deep coupling, or business execution in the S13-P1 run."
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


def validate_stage12_review_dependency() -> dict[str, Any]:
    result = validate_v014_s12_stage_review()
    if result.get("stage_id") != "S12":
        raise RuntimeError("S13-P1 requires validated v0.1.4 Stage 12 review")
    if result.get("stage_review_performed") is not True:
        raise RuntimeError("S13-P1 requires Stage 12 review performed")
    if result.get("next_phase") != "S13-P1":
        raise RuntimeError("Stage 12 review must route to S13-P1")
    if result.get("s13_p1_performed") is not False:
        raise RuntimeError("Stage 12 review dependency must not already include S13-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("Stage 12 review dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("v1.4 upload must remain deferred")
    raw = result.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_by_this_review",
        "raw_inbox_listed_by_this_review",
        "raw_inbox_mutated_by_this_review",
    ):
        if raw.get(key) is not False:
            raise RuntimeError(f"Stage 12 review raw boundary must keep {key}=false")
    return result


def validate_legacy_s13_p1_artifacts() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    legacy_manifest, source_lanes, drafts, html_outputs = build_default_financial_operating_report_artifacts(
        generated_at="2026-07-05T03:50:00+10:00"
    )
    validate_financial_operating_report_artifacts(legacy_manifest, source_lanes, drafts, html_outputs)
    return legacy_manifest, source_lanes, drafts, html_outputs


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

    for token in ("财务经营报表", "经营周报/月报初稿", "经营报告显示数据状态和限制"):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S13-P1 token: {token}")
    for token in ("财务经营分析报表线", "经营周/月报初稿"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing S13 business line token: {token}")
    for token in ("经营分析报告", "可切换章节", "数据源检查板", "待处理事项工作台"):
        if token not in entry_text:
            raise RuntimeError(f"v1.4 HTML entry missing report-flow token: {token}")
    if "button" not in script_text or "input" not in script_text or "link" not in script_text:
        raise RuntimeError("v1.4 audit script must inspect links, inputs, and buttons")

    return {
        "taskpack_html_requirement_read": True,
        "human_flow_entry_exists": V14_HTML_ENTRY_PATH.exists(),
        "human_flow_audit_script_exists": V14_HTML_AUDIT_SCRIPT_PATH.exists(),
        "human_flow_audit_report_exists": V14_HTML_AUDIT_REPORT_PATH.exists(),
        **report_counts,
        "source_package_manifest_counts_match_report": True,
        "roadmap_includes_s13_p1_requirements": True,
        "taskpack_includes_financial_operating_line": True,
        "audit_script_inspects_links_inputs_buttons": True,
        "implementation_reflects_weekly_monthly_drafts": False,
        "implementation_reflects_data_status_and_limits": False,
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
        "draft_report_allowed": True,
        "weekly_draft_allowed": True,
        "monthly_draft_allowed": True,
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
        "payment_or_bank_operation_allowed": False,
        "loan_management_action_allowed": False,
        "tax_filing_allowed": False,
        "automatic_external_action_allowed": False,
        "s13_p2_allowed": False,
        "s13_p3_allowed": False,
        "stage13_review_allowed": False,
        "github_upload_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "stage12_review_dependency_included": True,
        "s13_p1_financial_operating_report_scope_included": True,
        "s13_p2_collection_receivable_aging_scope_included": False,
        "s13_p3_cross_table_review_scope_included": False,
        "stage13_review_scope_included": False,
        "lineage_full_check_scope_included": False,
        "protected_source_matching_scope_included": False,
        "raw_value_matching_scope_included": False,
        "formal_report_scope_included": False,
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
    }


def _rewrite_drafts_for_v014(drafts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rewritten: list[dict[str, Any]] = []
    for draft in drafts:
        row = dict(draft)
        row["stage_phase"] = "S13-P1"
        row["html_draft_ref"] = (
            "KMFA/stage_artifacts/V014_S13_P1_FINANCIAL_OPERATING_REPORT/exports/html/"
            f"{row['draft_id']}.html"
        )
        row["v014_review_dependency"] = "KMFA/stage_artifacts/V014_S12_STAGE_REVIEW/machine/stage12_review_manifest.json"
        rewritten.append(row)
    return rewritten


def _html_path_for_draft(draft_id: str) -> Path:
    if draft_id == "financial_operating_weekly_draft":
        return HTML_WEEKLY_PATH
    if draft_id == "financial_operating_monthly_draft":
        return HTML_MONTHLY_PATH
    return EXPORT_HTML_DIR / f"{draft_id}.html"


def build_manifest() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    generated_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    stage12 = validate_stage12_review_dependency()
    legacy_manifest, source_lanes, legacy_drafts, html_outputs = validate_legacy_s13_p1_artifacts()
    drafts = _rewrite_drafts_for_v014(legacy_drafts)
    validate_financial_operating_report_artifacts(legacy_manifest, source_lanes, drafts, html_outputs)
    baseline = load_v14_html_uiux_baseline()
    baseline["implementation_reflects_weekly_monthly_drafts"] = True
    baseline["implementation_reflects_data_status_and_limits"] = True
    summary = dict(legacy_manifest["summary"])

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s13_p1_financial_operating_report_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S13",
        "phase_id": "S13-P1",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S13P1T01", "S13P1T02", "S13P1T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_financial_operating_report_locked",
        "generated_at": generated_at,
        "git_head": git_output(["rev-parse", "HEAD"]),
        "s12_stage_review_dependency_validated": True,
        "legacy_s13_p1_dependency_validated": True,
        "v14_html_uiux_dependency_validated": True,
        "source_taskpack_refs": {
            "v14_taskpack": V14_TASKPACK_PATH.as_posix(),
            "v14_roadmap": V14_ROADMAP_PATH.as_posix(),
            "v14_html_audit": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
        },
        "dependency_summary": {
            "stage12_phase_results": stage12.get("phase_results"),
            "stage12_open_findings": stage12.get("open_review_finding_count"),
            "stage12_fixed_findings": stage12.get("fixed_review_finding_count"),
            "stage12_next_phase": stage12.get("next_phase"),
            "legacy_s13p1_source_lanes": summary["source_lane_count"],
            "legacy_s13p1_drafts": summary["draft_report_count"],
        },
        "stage13_phase_progress": {
            "completed_phase_count": 1,
            "total_phase_count": 3,
            "derived_percent_bps": 3333,
            "derived_percent_label": "33.33%",
            "s13_p1_performed": True,
            "s13_p2_performed": False,
            "s13_p3_performed": False,
            "stage13_review_performed": False,
        },
        "financial_operating_summary": {
            "source_lane_count": summary["source_lane_count"],
            "source_count": summary["source_count"],
            "field_mapping_count": summary["field_mapping_count"],
            "draft_report_count": summary["draft_report_count"],
            "html_draft_count": summary["html_draft_count"],
            "pending_reconciliation_count": summary["pending_reconciliation_count"],
            "report_grade_visible": summary["report_grade_visible"],
            "formal_report_count": summary["formal_report_count"],
            "business_decision_basis_count": summary["business_decision_basis_count"],
            "required_source_lanes": list(REQUIRED_SOURCE_LANES),
            "required_draft_ids": list(REQUIRED_DRAFT_IDS),
            "required_section_titles": list(REPORT_SECTION_TITLES),
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
            "s13_p2_not_performed",
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
            "drafts": DRAFTS_PATH.as_posix(),
            "weekly_html": HTML_WEEKLY_PATH.as_posix(),
            "monthly_html": HTML_MONTHLY_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s13_p1_financial_operating_report.py",
            "focused_test": "KMFA/tests/test_v014_s13_p1_financial_operating_report.py",
        },
        "next_phase": "S13-P2",
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    return manifest, source_lanes, drafts, html_outputs


def write_human_evidence(manifest: dict[str, Any]) -> None:
    summary = manifest["financial_operating_summary"]
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S13-P1 Financial Operating Report",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `completed_validated_local_only_no_go_upload_deferred`",
                "- phase_scope: `v014_s13_p1_financial_operating_report_only`",
                f"- source_lanes: `{summary['source_lane_count']}`",
                f"- drafts: `{summary['draft_report_count']}`",
                f"- html_drafts: `{summary['html_draft_count']}`",
                f"- field_mappings: `{summary['field_mapping_count']}`",
                f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
                "- report_grade_visible: `D`",
                "- formal_report_allowed: `false`",
                "- business_decision_basis_allowed: `false`",
                "- s13_p2_performed: `false`",
                "- s13_p3_performed: `false`",
                "- stage13_review_performed: `false`",
                "- github_upload_performed: `false`",
                "- raw_inbox_read_by_this_phase: `false`",
                "",
                "## Coverage",
                "",
                "- T1: 接入经营情况、费用税金资产、现金情况、贷款明细 4 条 public-safe source lanes。",
                "- T2: 生成经营周报初稿和经营月报初稿，两份 HTML draft 均为 public-safe。",
                "- T3: 显示数据状态、报告等级 D、12 条 pending reconciliation 和正式报告/经营决策限制。",
                "",
                "## Boundary",
                "",
                "- 不提交 raw business data、字段明文、真实金额、真实账号、Excel workbook、PDF、zip、sqlite/db、private CSV 或 credentials。",
                "- 不执行 S13-P2、S13-P3、Stage 13 review、GitHub upload、protected source matching、lineage full check、正式报告、外部接口、付款、贷款管理、税务申报或业务执行。",
                "",
            ]
        ),
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S13-P1 Test Results",
                "",
                "- task_id: `KMFA-V014-S13-P1-FINANCIAL-OPERATING-REPORT-20260705`",
                "- status: `pending_final_validation_capture`",
                "",
                "## Expected Commands",
                "",
                "- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s13_p1_financial_operating_report.py KMFA/tools/check_v014_s13_p1_financial_operating_report.py KMFA/tests/test_v014_s13_p1_financial_operating_report.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s13_p1_financial_operating_report.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s13_p1_financial_operating_report.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s13_p1_financial_operating_report -q`",
                "- governance validators and safety scans before commit",
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S13-P1 Risk Register",
                "",
                "| Risk | Control | Status |",
                "|---|---|---|",
                "| 经营初稿被误用为正式报告 | 报告等级 D、formal_report_allowed=false、business_decision_basis_allowed=false | controlled |",
                "| S13-P1 越界进入回款/跨表/复审/upload | validator 检查 S13-P2/P3、Stage 13 review 和 GitHub upload 均为 false | controlled |",
                "| raw/private 数据泄漏 | 只复用 public-safe metadata，raw inbox read/list/stat/hash/mutation 全为 false | controlled |",
                "",
            ]
        ),
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S13-P1 Rollback Plan",
                "",
                "- 删除 `KMFA/stage_artifacts/V014_S13_P1_FINANCIAL_OPERATING_REPORT/`。",
                "- 删除 `KMFA/tools/v014_s13_p1_financial_operating_report.py` 和 `KMFA/tools/check_v014_s13_p1_financial_operating_report.py`。",
                "- 删除 `KMFA/tests/test_v014_s13_p1_financial_operating_report.py`。",
                "- 回滚本 phase 的治理 registry、开发记录、功能清单和模型参数文件更新。",
                "",
            ]
        ),
    )


def generate() -> dict[str, Any]:
    manifest, source_lanes, drafts, html_outputs = build_manifest()
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(LANES_PATH, source_lanes)
    _write_jsonl(DRAFTS_PATH, drafts)
    for draft_id, html_text in html_outputs.items():
        _write_text(_html_path_for_draft(draft_id), html_text)
    write_human_evidence(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["financial_operating_summary"]
    print(
        "PASS: KMFA v0.1.4 S13-P1 financial operating report evidence generated "
        f"(source_lanes={summary['source_lane_count']}, drafts={summary['draft_report_count']}, "
        f"html={summary['html_draft_count']}, field_mappings={summary['field_mapping_count']}, "
        "formal_report=false, s13_p2=false, s13_p3=false, stage13_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
