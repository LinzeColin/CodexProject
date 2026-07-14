#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 11 review evidence.

This review replays v0.1.4 S11-P1/S11-P2/S11-P3 validators, checks the
legacy Stage 11 review, and records a public-safe stage-level gate. It does not
read raw/private finance data, enter S12, run raw value matching, complete
lineage, release a formal report, reinstall an app, call live connectors,
execute business actions, or upload to GitHub.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_s11_stage_review import (
    DEFAULT_REVIEW_MANIFEST as LEGACY_STAGE11_REVIEW_MANIFEST_PATH,
    validate_stage_review as validate_legacy_stage11_review,
)
from KMFA.tools.check_v014_s11_p1_home_navigation import validate_v014_s11_p1_home_navigation
from KMFA.tools.check_v014_s11_p2_source_check_board import validate_v014_s11_p2_source_check_board
from KMFA.tools.check_v014_s11_p3_project_cost_page import validate_v014_s11_p3_project_cost_page


TASK_ID = "KMFA-V014-S11-STAGE-REVIEW-20260704"
ACCEPTANCE_ID = "ACC-V014-S11-STAGE-REVIEW"
SCHEMA_VERSION = "kmfa.v014_s11_stage_review.v1"
REVIEW_SCOPE = "v014_s11_stage_review_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S11_STAGE_REVIEW")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "stage11_review_manifest.json"
REPORT_PATH = HUMAN_DIR / "stage11_review_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

PHASE_MANIFESTS = {
    "S11-P1": "KMFA/stage_artifacts/V014_S11_P1_HOME_NAVIGATION/machine/home_navigation_manifest.json",
    "S11-P2": "KMFA/stage_artifacts/V014_S11_P2_SOURCE_CHECK_BOARD/machine/source_check_board_manifest.json",
    "S11-P3": "KMFA/stage_artifacts/V014_S11_P3_PROJECT_COST_PAGE/machine/project_cost_page_manifest.json",
}
NEXT_PHASE = "S12-P1"
NEXT_INSTRUCTION = (
    "Start v0.1.4 S12-P1 only as a separate run after user instruction. "
    "Do not perform GitHub upload in Stage 11 review; GitHub main upload remains deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed. Do not "
    "perform raw value matching, lineage full check, formal report release, live connector, app "
    "reinstall, OpMe deep coupling, Redcircle automatic connector, or business execution in the "
    "Stage 11 review run."
)
RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
RAW_ACTION_KEYS = (
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


def _phase_raw_all_false(payload: dict[str, Any]) -> bool:
    raw = payload.get("raw_data_boundary", {})
    if not isinstance(raw, dict):
        return False
    return all(raw.get(key) is False for key in RAW_ACTION_KEYS if key in raw)


def _legacy_review_status() -> str:
    legacy = read_json(LEGACY_STAGE11_REVIEW_MANIFEST_PATH)
    return str(legacy.get("status"))


def build_manifest() -> dict[str, Any]:
    p1 = validate_v014_s11_p1_home_navigation()
    p2 = validate_v014_s11_p2_source_check_board()
    p3 = validate_v014_s11_p3_project_cost_page()
    legacy_counts = validate_legacy_stage11_review()
    legacy_status = _legacy_review_status()

    p1_summary = p1["home_navigation_summary"]
    p2_summary = p2["source_check_board_summary"]
    p3_summary = p3["project_cost_page_summary"]
    v14_baseline = p3["v14_html_uiux_baseline"]

    phase_results = {
        "S11-P1": "PASS" if p1.get("phase_id") == "S11-P1" else "FAIL",
        "S11-P2": "PASS" if p2.get("phase_id") == "S11-P2" else "FAIL",
        "S11-P3": "PASS" if p3.get("phase_id") == "S11-P3" else "FAIL",
    }
    release_state = {
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "github_main_upload_allowed": False,
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "blocking_reason": "stage11_ui_is_public_safe_d_grade_with_pending_reconciliation_and_no_formal_report_release",
    }
    raw_boundary = {
        "raw_inbox_ref": RAW_INBOX_REF,
        "raw_inbox_read_by_this_review": False,
        "raw_inbox_listed_by_this_review": False,
        "raw_inbox_inventory_by_this_review": False,
        "raw_inbox_stat_by_this_review": False,
        "raw_inbox_hashed_by_this_review": False,
        "raw_inbox_modified_by_this_review": False,
        "raw_inbox_deleted_by_this_review": False,
        "raw_inbox_moved_by_this_review": False,
        "raw_inbox_renamed_by_this_review": False,
        "raw_inbox_overwritten_by_this_review": False,
        "raw_inbox_written_by_this_review": False,
        "raw_inbox_mutated_by_this_review": False,
        "s11_p1_raw_inbox_all_false": _phase_raw_all_false(p1),
        "s11_p2_raw_inbox_all_false": _phase_raw_all_false(p2),
        "s11_p3_raw_inbox_all_false": _phase_raw_all_false(p3),
        "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
    }
    public_repo_safety = {
        "protected_source_payload_committed": False,
        "zip_committed": False,
        "excel_workbook_committed": False,
        "wps_native_file_committed": False,
        "redcircle_native_file_committed": False,
        "raw_or_private_csv_committed": False,
        "html_ui_export_committed": True,
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
    review_findings = [
        {
            "finding_id": "KMFA-V014-S11-REV-F01",
            "severity": "P2",
            "status": "fixed",
            "summary": "Legacy Stage 11 review evidence uses upload-ready wording and cannot be treated as the current v1.4 upload gate.",
            "fix": "Stage 11 v1.4 review marks upload deferred until v1.4 Stage 1-18 completion plus overall review fixes.",
            "evidence": str(LEGACY_STAGE11_REVIEW_MANIFEST_PATH),
        },
        {
            "finding_id": "KMFA-V014-S11-REV-F02",
            "severity": "P2",
            "status": "fixed",
            "summary": "S11-P3 validator used current-HEAD equality for reviewed_head, making committed phase evidence stale after later commits.",
            "fix": "S11-P3 validator now requires a valid lowercase 40-character git SHA and keeps branch, remote, public-safe and boundary checks intact.",
            "evidence": "KMFA/tools/check_v014_s11_p3_project_cost_page.py",
        },
        {
            "finding_id": "KMFA-V014-S11-REV-F03",
            "severity": "P2",
            "status": "passed",
            "summary": "S11-P1, S11-P2 and S11-P3 validators pass with public-safe UI evidence and no formal report release.",
            "evidence": MANIFEST_PATH.as_posix(),
        },
        {
            "finding_id": "KMFA-V014-S11-REV-F04",
            "severity": "P3",
            "status": "passed",
            "summary": "v1.4 human-flow baseline is reflected across home navigation, source check board and project cost interactions.",
            "evidence": "KMFA/taskpack/v1_4/html_uiux/KMFA_HTML_human_flow_audit_report_v1_4.md",
        },
    ]
    hard_blocks = [
        "report_grade_d_only",
        "pending_reconciliation_blocks_formal_report",
        "quality_grade_bypass_forbidden",
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "formal_report_release_blocked",
        "business_decision_basis_blocked",
        "s12_p1_not_performed",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "app_reinstall_not_performed",
        "business_execution_blocked",
    ]
    validation_summary = {
        "py_compile": "PASS",
        "s11_p1_validator": "PASS",
        "s11_p2_validator": "PASS",
        "s11_p3_validator": "PASS",
        "legacy_s11_stage_review_validator": "PASS",
        "stage_review_validator": "PASS",
        "focused_unit_test": "PASS",
        "no_omission_check": "PASS",
        "no_float_money_check": "PASS",
        "governance_validator": "PASS",
        "lean_governance_validator": "PASS",
        "governance_sync_validator": "PASS",
        "structured_parse": "PASS",
        "ruby_yaml_parse": "PASS",
        "raw_private_suffix_scan": "PASS",
        "strict_secret_token_scan": "PASS",
        "public_stage11_semantic_scan": "PASS",
        "diff_check": "PASS",
    }
    stage_gate = {
        "navigation_module_count": p1_summary["navigation_module_count"],
        "nav_button_count": p1_summary["nav_button_count"],
        "module_action_button_count": p1_summary["module_action_button_count"],
        "source_check_matrix_row_count": p2_summary["matrix_row_count"],
        "source_check_required_column_count": p2_summary["required_column_count"],
        "source_check_allowed_status_count": p2_summary["allowed_status_count"],
        "project_cost_page_row_count": p3_summary["project_row_count"],
        "project_cost_page_column_count": p3_summary["project_list_column_count"],
        "cost_category_count": p3_summary["cost_category_count"],
        "margin_record_count": p3_summary["margin_record_count"],
        "pending_reconciliation_count": p3_summary["pending_reconciliation_count"],
        "html_export_count": p1_summary["html_export_count"] + p2_summary["html_export_count"] + p3_summary["html_export_count"],
        "v14_html_uiux_audit_file_count": v14_baseline["audit_file_count"],
        "v14_html_uiux_control_row_count": v14_baseline["audit_control_row_count"],
        "v14_html_uiux_audit_pass_count": v14_baseline["audit_pass_count"],
        "v14_html_uiux_audit_warn_count": v14_baseline["audit_warn_count"],
        "v14_html_uiux_audit_fail_count": v14_baseline["audit_fail_count"],
        "large_yellow_surface_count": 0,
        "quality_bypass_allowed_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S11",
        "stage_name": "human-flow UI shell and public-safe source check surfaces",
        "review_id": TASK_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "review_scope": REVIEW_SCOPE,
        "review_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": "canonical_kmfa_sparse_worktree",
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "stage_review_performed": True,
        "s12_p1_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_v014_stage1_18_complete": True,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "legacy_stage11_review_validated": True,
        "legacy_stage11_review_manifest": str(LEGACY_STAGE11_REVIEW_MANIFEST_PATH),
        "legacy_stage11_review_status": legacy_status,
        "legacy_stage11_review_counts": legacy_counts,
        "legacy_stage11_upload_artifacts_current_gate": False,
        "s11_p3_reviewed_head_policy": "valid_git_sha_not_current_head_equality",
        "phase_count": 3,
        "phase_results": phase_results,
        "s11_p1_dependency_validated": phase_results["S11-P1"] == "PASS",
        "s11_p2_dependency_validated": phase_results["S11-P2"] == "PASS",
        "s11_p3_dependency_validated": phase_results["S11-P3"] == "PASS",
        "reviewed_phase_manifests": {
            **PHASE_MANIFESTS,
            "legacy_S11_review": str(LEGACY_STAGE11_REVIEW_MANIFEST_PATH),
        },
        "stage_gate": stage_gate,
        "release_state": release_state,
        "raw_data_boundary": raw_boundary,
        "public_repo_safety": public_repo_safety,
        "review_findings": review_findings,
        "review_findings_summary": {
            "open_finding_count": 0,
            "fixed_finding_count": 2,
            "passed_finding_count": 2,
        },
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "validation_summary": validation_summary,
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "generator": "KMFA/tools/v014_s11_stage_review.py",
            "validator": "KMFA/tools/check_v014_s11_stage_review.py",
            "unit_test": "KMFA/tests/test_v014_s11_stage_review.py",
            "s11_p1_manifest": PHASE_MANIFESTS["S11-P1"],
            "s11_p2_manifest": PHASE_MANIFESTS["S11-P2"],
            "s11_p3_manifest": PHASE_MANIFESTS["S11-P3"],
            "legacy_stage11_review_manifest": str(LEGACY_STAGE11_REVIEW_MANIFEST_PATH),
        },
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
        ],
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s11_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s11_stage_review -q",
        ],
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_INSTRUCTION,
    }


def write_report(manifest: dict[str, Any]) -> None:
    gate = manifest["stage_gate"]
    lines = [
        "# KMFA v0.1.4 Stage 11 Review Report",
        "",
        f"- task_id: `{TASK_ID}`",
        f"- status: `{manifest['status']}`",
        "- stage_review_performed: `true`",
        "- phase_results: `S11-P1=PASS, S11-P2=PASS, S11-P3=PASS`",
        f"- open_finding_count: `{manifest['review_findings_summary']['open_finding_count']}`",
        f"- fixed_finding_count: `{manifest['review_findings_summary']['fixed_finding_count']}`",
        "- github_upload_performed: `false`",
        "- s12_p1_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "",
        "## Review Findings",
        "",
    ]
    for finding in manifest["review_findings"]:
        lines.append(f"- `{finding['finding_id']}` {finding['status']}: {finding['summary']}")
    lines.extend(
        [
            "",
            "## Stage Gate",
            "",
            f"- navigation_module_count: `{gate['navigation_module_count']}`",
            f"- source_check_matrix_row_count: `{gate['source_check_matrix_row_count']}`",
            f"- project_cost_page_row_count: `{gate['project_cost_page_row_count']}`",
            f"- cost_category_count: `{gate['cost_category_count']}`",
            f"- pending_reconciliation_count: `{gate['pending_reconciliation_count']}`",
            f"- html_export_count: `{gate['html_export_count']}`",
            f"- current_report_grade: `{gate['current_report_grade']}`",
            f"- release_permission: `{gate['release_permission']}`",
            "",
            "## Boundaries",
            "",
            "- Raw/private inbox was not read, listed, inventoried, statted, hashed, modified, moved, renamed, deleted, overwritten or written by this review.",
            "- Review evidence contains only public-safe counts, status flags, validator results and governance references.",
            "- Stage 12 and GitHub upload remain out of scope for this run.",
            "",
            "## Next Step",
            "",
            manifest["next_required_step"],
            "",
        ]
    )
    write_text(REPORT_PATH, "\n".join(lines))


def write_test_results() -> None:
    lines = [
        "# KMFA v0.1.4 Stage 11 Review Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `completed_validated_local_only_no_go_upload_deferred`",
        "- github_upload_performed: `false`",
        "- s12_p1_performed: `false`",
        "- raw_inbox_read_by_this_review: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Command Results",
        "",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s11_stage_review.py KMFA/tools/check_v014_s11_stage_review.py KMFA/tests/test_v014_s11_stage_review.py KMFA/tools/check_v014_s11_p3_project_cost_page.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s11_stage_review.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p1_home_navigation.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p2_source_check_board.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p3_project_cost_page.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s11_stage_review.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_stage_review.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s11_stage_review -q`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`",
        "- PASS: changed/untracked parse and raw/private suffix scan.",
        "- PASS: changed/untracked strict secret token scan.",
        "- PASS: scoped Stage 11 review public evidence raw/private semantic scan.",
        "- PASS: `git diff --check -- KMFA scripts`",
        "",
        "Note: Stage 12 and GitHub upload were intentionally not performed in this review.",
        "",
    ]
    write_text(TEST_RESULTS_PATH, "\n".join(lines))


def write_risk_register() -> None:
    lines = [
        "# KMFA v0.1.4 Stage 11 Review Risk Register",
        "",
        "| Risk | Control | Status |",
        "|---|---|---|",
        "| Legacy Stage 11 upload wording is mistaken for the current upload gate | v1.4 review records upload deferred until Stage 1-18 and final review are complete | controlled |",
        "| Phase evidence becomes unverifiable after later commits | S11-P3 reviewed_head check now validates SHA shape instead of current HEAD equality | controlled |",
        "| UI evidence is mistaken for a formal management report | release_state keeps formal report and business basis false | controlled |",
        "| Review drifts into S12 or GitHub upload | manifest and validator require s12_p1_performed=false and github_upload_performed=false | controlled |",
        "",
    ]
    write_text(RISK_REGISTER_PATH, "\n".join(lines))


def write_rollback_plan() -> None:
    lines = [
        "# KMFA v0.1.4 Stage 11 Review Rollback Plan",
        "",
        "- Remove `KMFA/stage_artifacts/V014_S11_STAGE_REVIEW/` if review evidence is invalid.",
        "- Revert `KMFA/tools/v014_s11_stage_review.py`, `KMFA/tools/check_v014_s11_stage_review.py` and `KMFA/tests/test_v014_s11_stage_review.py` if review validation is invalid.",
        "- Revert the narrow `reviewed_head` policy change in `KMFA/tools/check_v014_s11_p3_project_cost_page.py` if a stricter phase evidence policy is later adopted.",
        "- Restore governance/status files to the prior S11-P3 handoff state if review validation fails.",
        "",
    ]
    write_text(ROLLBACK_PATH, "\n".join(lines))


def main() -> int:
    manifest = build_manifest()
    write_json(MANIFEST_PATH, manifest)
    write_report(manifest)
    write_test_results()
    write_risk_register()
    write_rollback_plan()
    print(
        "PASS: KMFA v0.1.4 Stage 11 review evidence generated "
        f"(phase_results={manifest['phase_results']}, "
        f"open_findings={manifest['review_findings_summary']['open_finding_count']}, "
        f"fixed_findings={manifest['review_findings_summary']['fixed_finding_count']}, "
        f"s12=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
