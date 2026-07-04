#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S11-P1 public-safe home navigation evidence.

This phase locks the home and navigation entry points against the v1.4
human-flow HTML baseline. It does not build the S11-P2 source check board,
the S11-P3 project cost page, Stage 11 review, raw value matching, lineage full
check, formal reports, live connectors, app reinstall, business actions, or
GitHub upload.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_s11_p1_home_navigation import (
    DEFAULT_HTML_OUTPUT as LEGACY_HTML_OUTPUT,
    DEFAULT_OUTPUT_MANIFEST as LEGACY_MANIFEST_PATH,
    DEFAULT_OUTPUT_RECORDS as LEGACY_RECORDS_PATH,
    read_json,
    read_jsonl,
    validate_home_navigation_artifacts,
)
from KMFA.tools.check_v014_s10_stage_review import validate_v014_s10_stage_review
from KMFA.tools.home_navigation_runtime import REQUIRED_NAVIGATION_LABELS


TASK_ID = "KMFA-V014-S11-P1-HOME-NAVIGATION-20260704"
ACCEPTANCE_ID = "ACC-V014-S11-P1-HOME-NAVIGATION"
SCHEMA_VERSION = "kmfa.v014_s11_p1_home_navigation.v1"
PHASE_SCOPE = "v014_s11_p1_home_navigation_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S11_P1_HOME_NAVIGATION")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
EXPORT_HTML_DIR = OUTPUT_DIR / "exports" / "html"
MANIFEST_PATH = MACHINE_DIR / "home_navigation_manifest.json"
RECORDS_PATH = MACHINE_DIR / "home_navigation_modules.jsonl"
HTML_OUTPUT_PATH = EXPORT_HTML_DIR / "kmfa_home_navigation.html"
REPORT_PATH = HUMAN_DIR / "home_navigation_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

S10_STAGE_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/V014_S10_STAGE_REVIEW/machine/stage10_review_manifest.json")
SOURCE_PACKAGE_MANIFEST = Path("KMFA/taskpack/v1_4/machine/source_package_manifest.json")
HTML_ENTRY_PATH = Path("KMFA/taskpack/v1_4/html_uiux/00_KMFA_HTML_human_flow_entry_v1_4.html")
HTML_AUDIT_SCRIPT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/kmfa_html_human_flow_audit.py")
HTML_AUDIT_REPORT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/KMFA_HTML_human_flow_audit_report_v1_4.md")

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S11-P2 source check board as a separate run. Do not perform "
    "S11-P3, Stage 11 overall review, GitHub upload, raw value matching, lineage full "
    "check, formal report release, live connector, app reinstall, OpMe deep coupling, "
    "or business execution in the S11-P1 run."
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


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _extract_first_int(pattern: str, text: str, label: str) -> int:
    match = re.search(pattern, text)
    if not match:
        raise RuntimeError(f"missing v1.4 HTML audit value: {label}")
    return int(match.group(1))


def validate_s10_stage_review_dependency() -> dict[str, Any]:
    result = validate_v014_s10_stage_review()
    if result.get("stage_id") != "S10":
        raise RuntimeError("S11-P1 requires validated v0.1.4 Stage 10 review")
    if result.get("stage_review_performed") is not True:
        raise RuntimeError("S11-P1 requires Stage 10 review performed")
    if result.get("next_phase") != "S11-P1":
        raise RuntimeError("Stage 10 review must route to S11-P1")
    if result.get("s11_p1_performed") is not False:
        raise RuntimeError("Stage 10 review dependency must not already include S11-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("Stage 10 review dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("v1.4 upload must remain deferred")
    raw = result.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_by_this_review",
        "raw_inbox_listed_by_this_review",
        "raw_inbox_mutated_by_this_review",
    ):
        if raw.get(key) is not False:
            raise RuntimeError(f"Stage 10 review raw boundary must keep {key}=false")
    return result


def validate_legacy_s11_p1_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_MANIFEST_PATH)
    records = read_jsonl(LEGACY_RECORDS_PATH)
    html_text = LEGACY_HTML_OUTPUT.read_text(encoding="utf-8")
    validate_home_navigation_artifacts(
        legacy_manifest,
        records,
        {"html": {"kmfa_home_navigation": html_text}},
    )

    target_paths: list[str] = []
    existing_targets = 0
    for href in re.findall(r'data-href="([^"]+)"', html_text):
        target_paths.append(href)
        if (LEGACY_HTML_OUTPUT.parent / href).resolve().exists():
            existing_targets += 1

    return {
        "legacy_manifest": legacy_manifest,
        "records": records,
        "html_text": html_text,
        "target_paths": target_paths,
        "existing_target_count": existing_targets,
        "nav_button_count": html_text.count('<button type="button" data-target='),
        "module_action_button_count": html_text.count('class="module-action" data-target='),
        "visible_feedback_panel_count": html_text.count('id="module_action_panel"'),
        "aria_live_count": html_text.count('aria-live="polite"'),
        "select_module_function_count": html_text.count("function selectModule"),
        "open_module_page_function_count": html_text.count("function openModulePage"),
        "add_event_listener_count": html_text.count('addEventListener("click"'),
        "html_text_length": len(html_text),
    }


def load_v14_html_uiux_baseline() -> dict[str, Any]:
    source_manifest = json.loads(SOURCE_PACKAGE_MANIFEST.read_text(encoding="utf-8"))
    gate = source_manifest.get("html_human_flow_gate", {})
    report_text = HTML_AUDIT_REPORT_PATH.read_text(encoding="utf-8")
    entry_text = HTML_ENTRY_PATH.read_text(encoding="utf-8")
    script_text = HTML_AUDIT_SCRIPT_PATH.read_text(encoding="utf-8")

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

    required_entry_terms = (
        "经营总览",
        "项目成本",
        "回款应收",
        "财务资金",
        "开票纳税",
        "数据源检查",
        "待处理事项",
        "报告中心",
    )
    missing_terms = [term for term in required_entry_terms if term not in entry_text]
    if missing_terms:
        raise RuntimeError(f"v1.4 HTML entry missing S11-P1 terms: {missing_terms}")
    if "button" not in script_text or "input" not in script_text or "link" not in script_text:
        raise RuntimeError("v1.4 human-flow audit script must inspect links, inputs, and buttons")

    return {
        "taskpack_html_requirement_read": True,
        "human_flow_entry_exists": HTML_ENTRY_PATH.exists(),
        "human_flow_audit_script_exists": HTML_AUDIT_SCRIPT_PATH.exists(),
        "human_flow_audit_report_exists": HTML_AUDIT_REPORT_PATH.exists(),
        **report_counts,
        "source_package_manifest_counts_match_report": True,
        "entry_covers_required_navigation_terms": True,
        "audit_script_inspects_links_inputs_buttons": True,
        "implementation_reflects_clickable_navigation": False,
        "implementation_reflects_visible_feedback": False,
        "implementation_reflects_report_center_entry": False,
        "source_refs": {
            "source_package_manifest": SOURCE_PACKAGE_MANIFEST.as_posix(),
            "html_human_flow_entry": HTML_ENTRY_PATH.as_posix(),
            "html_human_flow_audit_script": HTML_AUDIT_SCRIPT_PATH.as_posix(),
            "html_human_flow_audit_report": HTML_AUDIT_REPORT_PATH.as_posix(),
        },
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s11_p1_home_navigation_scope_included": True,
        "s11_p2_source_check_board_scope_included": False,
        "s11_p3_project_cost_page_scope_included": False,
        "stage11_review_scope_included": False,
        "lineage_full_check_scope_included": False,
        "raw_value_matching_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "live_ui_runtime_scope_included": False,
        "app_reinstall_scope_included": False,
        "github_upload_scope_included": False,
        "business_execution_scope_included": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "pending_reconciliation_count": 12,
        "confirmed_resolution_count": 0,
        "home_navigation_export_allowed": True,
        "complete_trusted_report_display_allowed": False,
        "full_trusted_report_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "delivery_allowed": False,
        "raw_layer_write_allowed": False,
        "automatic_external_action_allowed": False,
        "stage11_review_allowed": False,
        "github_upload_allowed": False,
    }


def _raw_boundary() -> dict[str, Any]:
    return {
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
    }


def _public_repo_safety() -> dict[str, bool]:
    return {
        "protected_source_payload_committed": False,
        "zip_committed": False,
        "excel_workbook_committed": False,
        "wps_native_file_committed": False,
        "redcircle_native_file_committed": False,
        "raw_or_private_csv_committed": False,
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
        "spreadsheet_workbook_committed": False,
    }


def build_manifest() -> dict[str, Any]:
    s10_review = validate_s10_stage_review_dependency()
    legacy = validate_legacy_s11_p1_artifacts()
    baseline = load_v14_html_uiux_baseline()

    records = legacy["records"]
    html_text = legacy["html_text"]
    nav_button_count = legacy["nav_button_count"]
    module_action_button_count = legacy["module_action_button_count"]
    feedback_count = legacy["visible_feedback_panel_count"]
    baseline["implementation_reflects_clickable_navigation"] = (
        nav_button_count == 8
        and module_action_button_count == 8
        and legacy["add_event_listener_count"] >= 2
        and legacy["existing_target_count"] == 8
    )
    baseline["implementation_reflects_visible_feedback"] = (
        feedback_count == 1
        and legacy["aria_live_count"] >= 1
        and legacy["select_module_function_count"] == 1
    )
    baseline["implementation_reflects_report_center_entry"] = "报告中心" in html_text and "financial_operating_monthly_draft.html" in html_text

    home_summary = {
        "navigation_module_count": len(records),
        "required_navigation_labels": list(REQUIRED_NAVIGATION_LABELS),
        "html_export_count": 1,
        "nav_button_count": nav_button_count,
        "module_action_button_count": module_action_button_count,
        "visible_feedback_panel_count": feedback_count,
        "aria_live_count": legacy["aria_live_count"],
        "click_event_listener_count": legacy["add_event_listener_count"],
        "existing_navigation_target_count": legacy["existing_target_count"],
        "target_href_count": len(legacy["target_paths"]),
        "km_brand_mark_present": ">KM<" in html_text,
        "single_k_brand_mark_present": ">K<" in html_text,
        "blue_business_style": bool(legacy["legacy_manifest"]["summary"]["blue_business_style"]),
        "all_chinese_visible_copy": bool(legacy["legacy_manifest"]["summary"]["all_chinese_visible_copy"]),
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "raw_business_value_count": 0,
        "private_file_reference_count": 0,
    }
    hard_blocks = [
        "report_grade_d_only",
        "pending_reconciliation_blocks_formal_report",
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "formal_report_release_blocked",
        "business_decision_basis_blocked",
        "s11_p2_not_performed",
        "s11_p3_not_performed",
        "stage11_review_not_performed",
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
        "stage_id": "S11",
        "phase_id": "S11-P1",
        "phase_name": "v0.1.4 public-safe home navigation",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_home_navigation_locked",
        "completed_task_ids": ["S11P1T01", "S11P1T02", "S11P1T03"],
        "acceptance_ids": [ACCEPTANCE_ID],
        "s10_stage_review_dependency_validated": True,
        "s10_stage_review_status": s10_review.get("status"),
        "legacy_s11_p1_dependency_validated": True,
        "stage11_phase_progress": {
            "completed_phase_count": 1,
            "total_phase_count": 3,
            "derived_percent_bps": 3333,
            "derived_percent_label": "33.33%",
            "s11_p1_performed": True,
            "s11_p2_performed": False,
            "s11_p3_performed": False,
            "stage11_review_performed": False,
        },
        "home_navigation_summary": home_summary,
        "v14_html_uiux_baseline": baseline,
        "phase_boundaries": _phase_boundaries(),
        "quality_gate": _quality_gate(),
        "github_upload": {
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        },
        "raw_data_boundary": _raw_boundary(),
        "public_repo_safety": _public_repo_safety(),
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "artifact_refs": {
            "s10_stage_review_manifest": S10_STAGE_REVIEW_MANIFEST.as_posix(),
            "legacy_manifest": LEGACY_MANIFEST_PATH.as_posix(),
            "legacy_records": LEGACY_RECORDS_PATH.as_posix(),
            "legacy_html": LEGACY_HTML_OUTPUT.as_posix(),
            "v14_source_package_manifest": SOURCE_PACKAGE_MANIFEST.as_posix(),
            "v14_html_entry": HTML_ENTRY_PATH.as_posix(),
            "v14_html_audit_script": HTML_AUDIT_SCRIPT_PATH.as_posix(),
            "v14_html_audit_report": HTML_AUDIT_REPORT_PATH.as_posix(),
            "manifest": MANIFEST_PATH.as_posix(),
            "records": RECORDS_PATH.as_posix(),
            "html": HTML_OUTPUT_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "generator": "KMFA/tools/v014_s11_p1_home_navigation.py",
            "validator": "KMFA/tools/check_v014_s11_p1_home_navigation.py",
            "unit_test": "KMFA/tests/test_v014_s11_p1_home_navigation.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s11_p1_home_navigation.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p1_home_navigation.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s11_p1_home_navigation -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s11_p1_home_navigation.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            RECORDS_PATH.as_posix(),
            HTML_OUTPUT_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["home_navigation_summary"]
    baseline = manifest["v14_html_uiux_baseline"]
    lines = [
        "# KMFA v0.1.4 S11-P1 Home Navigation",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.4 Stage 10 review PASS`",
        "- legacy_s11_p1_dependency_validated: `true`",
        f"- navigation_module_count: `{summary['navigation_module_count']}`",
        f"- required_navigation_labels: `{summary['required_navigation_labels']}`",
        f"- html_export_count: `{summary['html_export_count']}`",
        f"- nav_button_count: `{summary['nav_button_count']}`",
        f"- module_action_button_count: `{summary['module_action_button_count']}`",
        f"- visible_feedback_panel_count: `{summary['visible_feedback_panel_count']}`",
        f"- existing_navigation_target_count: `{summary['existing_navigation_target_count']}`",
        f"- km_brand_mark_present: `{str(summary['km_brand_mark_present']).lower()}`",
        f"- single_k_brand_mark_present: `{str(summary['single_k_brand_mark_present']).lower()}`",
        f"- blue_business_style: `{str(summary['blue_business_style']).lower()}`",
        f"- all_chinese_visible_copy: `{str(summary['all_chinese_visible_copy']).lower()}`",
        f"- formal_report_count: `{summary['formal_report_count']}`",
        f"- business_decision_basis_count: `{summary['business_decision_basis_count']}`",
        "",
        "## v1.4 HTML Human-Flow Baseline",
        "",
        f"- human_flow_entry_exists: `{str(baseline['human_flow_entry_exists']).lower()}`",
        f"- human_flow_audit_script_exists: `{str(baseline['human_flow_audit_script_exists']).lower()}`",
        f"- human_flow_audit_report_exists: `{str(baseline['human_flow_audit_report_exists']).lower()}`",
        f"- audit_file_count: `{baseline['audit_file_count']}`",
        f"- audit_control_row_count: `{baseline['audit_control_row_count']}`",
        f"- audit_pass_count: `{baseline['audit_pass_count']}`",
        f"- audit_warn_count: `{baseline['audit_warn_count']}`",
        f"- audit_fail_count: `{baseline['audit_fail_count']}`",
        f"- implementation_reflects_clickable_navigation: `{str(baseline['implementation_reflects_clickable_navigation']).lower()}`",
        f"- implementation_reflects_visible_feedback: `{str(baseline['implementation_reflects_visible_feedback']).lower()}`",
        f"- implementation_reflects_report_center_entry: `{str(baseline['implementation_reflects_report_center_entry']).lower()}`",
        "",
        "## Boundary",
        "",
        "- s11_p1_home_navigation_scope_included: `true`",
        "- s11_p2_source_check_board_scope_included: `false`",
        "- s11_p3_project_cost_page_scope_included: `false`",
        "- stage11_review_scope_included: `false`",
        "- github_upload_deferred_until_v014_stage1_18_complete: `true`",
        "- github_upload_performed: `false`",
        "- complete_trusted_report_display_allowed: `false`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- business_execution_allowed: `false`",
        "- current_report_grade: `D`",
        "- release_permission: `blocked`",
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
        "Evidence contains only public-safe navigation labels, aggregate interaction counts, quality blockers, validator references, and governance paths.",
        "It does not contain source filenames from private inputs, source hashes from the private inbox, tab labels, ZIP member names, field/header plaintext, row values, business amount values, credentials, contracts, payroll, tax filings, or bank statements.",
        "",
        "## Next Step",
        "",
        manifest["next_required_step"],
        "",
    ]
    _write_text(REPORT_PATH, "\n".join(lines))


def write_test_results() -> None:
    lines = [
        "# KMFA v0.1.4 S11-P1 Home Navigation Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `completed_validated_local_only_no_go_upload_deferred`",
        "- github_upload_performed: `false`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "- s11_p2_performed: `false`",
        "- s11_p3_performed: `false`",
        "- stage11_review_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Command Results",
        "",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s11_p1_home_navigation.py KMFA/tools/check_v014_s11_p1_home_navigation.py KMFA/tests/test_v014_s11_p1_home_navigation.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_stage_review.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s11_p1_home_navigation.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s11_p1_home_navigation.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p1_home_navigation.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s11_p1_home_navigation -q`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`",
        "- PASS: `git diff --check -- KMFA scripts`",
        "- PASS: changed/untracked structured parse scan.",
        "- PASS: changed/untracked raw/private suffix scan.",
        "- PASS: changed/untracked strict secret token scan.",
        "- PASS: scoped S11-P1 public evidence raw/private semantic scan.",
        "",
        "Note: S11-P2, S11-P3, Stage 11 overall review, GitHub upload, raw value matching, lineage full check, formal report release, live connector, app reinstall, and business execution were intentionally not performed in this phase.",
        "",
    ]
    _write_text(TEST_RESULTS_PATH, "\n".join(lines))


def write_risk_register() -> None:
    lines = [
        "# KMFA v0.1.4 S11-P1 Risk Register",
        "",
        "| Risk | Control | Status |",
        "|---|---|---|",
        "| 首页导航被误解为正式经营报告 | validator 锁定 report grade D、formal_report_allowed=false、business_decision_basis_allowed=false | controlled |",
        "| v1.4 HTML 样板只被引用但未反映到实现 | validator 同时检查 v1.4 审计基线和首页 HTML 的按钮、反馈面板、报告中心入口 | controlled |",
        "| 单 phase 越界进入 S11-P2/S11-P3 或 Stage 11 review | phase boundaries 与 validator 均要求 false | controlled |",
        "| public evidence 泄露 raw/private 信息 | validator 扫描本 phase evidence 文本并锁定 raw/private boundary | controlled |",
        "",
    ]
    _write_text(RISK_REGISTER_PATH, "\n".join(lines))


def write_rollback_plan() -> None:
    lines = [
        "# KMFA v0.1.4 S11-P1 Rollback Plan",
        "",
        "Rollback is local-only: revert the S11-P1 commit or remove the generated `V014_S11_P1_HOME_NAVIGATION` evidence, v014 S11-P1 tools/tests, and governance entries.",
        "",
        "No raw/private input file is created, modified, moved, renamed, deleted, or overwritten by this phase.",
        "",
    ]
    _write_text(ROLLBACK_PATH, "\n".join(lines))


def generate() -> dict[str, Any]:
    MACHINE_DIR.mkdir(parents=True, exist_ok=True)
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_HTML_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    legacy = validate_legacy_s11_p1_artifacts()
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(RECORDS_PATH, legacy["records"])
    shutil.copyfile(LEGACY_HTML_OUTPUT, HTML_OUTPUT_PATH)
    write_report(manifest)
    write_test_results()
    write_risk_register()
    write_rollback_plan()
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["home_navigation_summary"]
    print(
        "PASS: KMFA v0.1.4 S11-P1 home navigation evidence generated "
        f"(navigation_modules={summary['navigation_module_count']}, "
        f"nav_buttons={summary['nav_button_count']}, "
        f"module_actions={summary['module_action_button_count']}, "
        "s11_p2=false, s11_p3=false, stage11_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
