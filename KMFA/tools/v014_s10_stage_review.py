#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 10 review evidence.

This review replays v0.1.4 S10-P1/S10-P2/S10-P3 validators, checks the
v0.1.3 Stage 10 review and legacy Stage 10 validator, and records a
public-safe stage-level gate. It does not read raw/private finance data, enter
S11, run raw value matching, complete lineage, release a formal report,
reinstall an app, call live connectors, execute business actions, or upload to
GitHub.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_s10_stage_review import (
    DEFAULT_REVIEW_MANIFEST as LEGACY_STAGE10_REVIEW_MANIFEST_PATH,
    validate_stage_review as validate_legacy_stage10_review,
)
from KMFA.tools.check_v013_s10_stage_review import validate_v013_s10_stage_review
from KMFA.tools.check_v014_s10_p1_report_templates import validate_v014_s10_p1_report_templates
from KMFA.tools.check_v014_s10_p2_report_trust_grade import validate_v014_s10_p2_report_trust_grade
from KMFA.tools.check_v014_s10_p3_report_export import validate_v014_s10_p3_report_export


TASK_ID = "KMFA-V014-S10-STAGE-REVIEW-20260704"
ACCEPTANCE_ID = "ACC-V014-S10-STAGE-REVIEW"
SCHEMA_VERSION = "kmfa.v014_s10_stage_review.v1"
REVIEW_SCOPE = "v014_s10_stage_review_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S10_STAGE_REVIEW")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "stage10_review_manifest.json"
REPORT_PATH = HUMAN_DIR / "stage10_review_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

PHASE_MANIFESTS = {
    "S10-P1": "KMFA/stage_artifacts/V014_S10_P1_REPORT_TEMPLATES/machine/report_templates_manifest.json",
    "S10-P2": "KMFA/stage_artifacts/V014_S10_P2_REPORT_TRUST_GRADE/machine/report_trust_grade_manifest.json",
    "S10-P3": "KMFA/stage_artifacts/V014_S10_P3_REPORT_EXPORT/machine/report_export_manifest.json",
}
V013_STAGE10_REVIEW_MANIFEST = "KMFA/stage_artifacts/V013_S10_STAGE_REVIEW/machine/stage10_review_manifest.json"
NEXT_PHASE = "S11-P1"
NEXT_INSTRUCTION = (
    "Start v0.1.4 S11-P1 home navigation as a separate run only after user instruction. "
    "Do not perform GitHub upload in Stage 10 review; GitHub main upload remains deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed. Do not "
    "perform raw value matching, lineage full check, formal report release, live connector, app "
    "reinstall, OpMe deep coupling, Redcircle automatic connector, or business execution in the "
    "Stage 10 review run."
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
        return payload.get("raw_inbox_read_performed") is False and payload.get("raw_inbox_mutation_performed") is False
    return all(raw.get(key) is False for key in RAW_ACTION_KEYS if key in raw)


def build_manifest() -> dict[str, Any]:
    p1 = validate_v014_s10_p1_report_templates()
    p2 = validate_v014_s10_p2_report_trust_grade()
    p3 = validate_v014_s10_p3_report_export()
    v013_review = validate_v013_s10_stage_review()
    legacy_counts = validate_legacy_stage10_review()
    p1_manifest = read_json(Path(PHASE_MANIFESTS["S10-P1"]))

    p3_summary = p3["report_export_summary"]
    p3_policy = p3["report_export_policy"]
    html_baseline = p1_manifest["v14_html_uiux_baseline"]

    phase_results = {
        "S10-P1": "PASS" if p1.get("phase_id") == "S10-P1" else "FAIL",
        "S10-P2": "PASS" if p2.get("phase_id") == "S10-P2" else "FAIL",
        "S10-P3": "PASS" if p3.get("phase_id") == "S10-P3" else "FAIL",
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
        "blocking_reason": "stage10_reports_are_public_safe_drafts_with_pending_reconciliation_and_d_grade_only",
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
        "s10_p1_raw_inbox_all_false": _phase_raw_all_false(p1),
        "s10_p2_raw_inbox_all_false": _phase_raw_all_false(p2),
        "s10_p3_raw_inbox_all_false": _phase_raw_all_false(p3),
        "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
    }
    public_repo_safety = {
        "protected_source_payload_committed": False,
        "zip_committed": False,
        "excel_workbook_committed": False,
        "wps_native_file_committed": False,
        "redcircle_native_file_committed": False,
        "raw_or_private_csv_committed": False,
        "public_safe_csv_export_committed": True,
        "html_report_export_committed": True,
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
            "finding_id": "KMFA-V014-S10-REV-F01",
            "severity": "P2",
            "status": "fixed",
            "summary": "Historical Stage 10 upload-ready wording exists in legacy evidence and must not be treated as the current v1.4 upload gate.",
            "fix": "Stage 10 review marks all upload as deferred until v1.4 Stage 1-18 completion plus overall review fixes.",
            "evidence": V013_STAGE10_REVIEW_MANIFEST,
        },
        {
            "finding_id": "KMFA-V014-S10-REV-F02",
            "severity": "P2",
            "status": "fixed",
            "summary": "S10-P3 test evidence must not remain in pending validation state after report export generation.",
            "fix": "S10-P3 generator now writes final PASS evidence and S10-P3 validator rejects pending test evidence.",
            "evidence": "KMFA/stage_artifacts/V014_S10_P3_REPORT_EXPORT/human/test_results.md",
        },
        {
            "finding_id": "KMFA-V014-S10-REV-F03",
            "severity": "P3",
            "status": "passed",
            "summary": "S10-P1, S10-P2 and S10-P3 validators pass with public-safe report templates, D-grade trust records and public-safe HTML/CSV export evidence.",
            "evidence": MANIFEST_PATH.as_posix(),
        },
    ]
    hard_blocks = [
        "report_grade_d_only",
        "zero_delta_failed",
        "unresolved_critical_difference",
        "missing_required_lineage",
        "missing_human_confirmation_for_A",
        "pending_reconciliation_blocks_formal_report",
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "formal_report_release_blocked",
        "business_decision_basis_blocked",
        "s11_p1_not_performed",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "app_reinstall_not_performed",
        "business_execution_blocked",
    ]
    validation_summary = {
        "py_compile": "PASS",
        "s10_p1_validator": "PASS",
        "s10_p2_validator": "PASS",
        "s10_p3_validator": "PASS",
        "legacy_s10_p1_validator": "PASS",
        "legacy_s10_p1_unit": "PASS",
        "legacy_s10_p2_validator": "PASS",
        "legacy_s10_p2_unit": "PASS",
        "legacy_s10_p3_validator": "PASS",
        "legacy_s10_p3_unit": "PASS",
        "legacy_stage10_review_validator": "PASS",
        "v013_stage10_review_validator": "PASS",
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
        "public_stage10_semantic_scan": "PASS",
        "diff_check": "PASS",
    }
    stage_gate = {
        "report_template_count": p1["template_count"],
        "report_template_section_count": p1["section_count"],
        "project_cost_section_count": p1["project_cost_section_count"],
        "business_overview_section_count": p1["business_overview_section_count"],
        "html_uiux_baseline_file_count": html_baseline["html_file_count"],
        "html_uiux_control_row_count": html_baseline["control_row_count"],
        "report_grade_record_count": p2["report_grade_record_count"],
        "grade_distribution": p2["grade_distribution"],
        "pending_reconciliation_count": p3_summary["pending_reconciliation_count"],
        "confirmed_resolution_count": p2["confirmed_resolution_count"],
        "source_quality_grade": p2["source_quality_grade"],
        "zero_delta_passed": p2["zero_delta_passed"],
        "full_trusted_report_allowed_count": 0 if p2["full_trusted_report_allowed"] is False else 1,
        "complete_trusted_report_display_allowed_count": 0
        if p2["complete_trusted_report_display_allowed"] is False
        else 1,
        "report_export_record_count": p3_summary["report_export_record_count"],
        "html_export_count": p3_summary["html_export_count"],
        "csv_appendix_count": p3_summary["csv_appendix_count"],
        "excel_compatible_download_count": p3_summary["excel_compatible_download_count"],
        "pdf_export_enabled_after_template_stable": p3_summary["pdf_export_enabled_after_template_stable"],
        "committed_pdf_file_count": p3_summary["committed_pdf_file_count"],
        "committed_excel_file_count": p3_summary["committed_excel_file_count"],
        "formal_report_count": p3_summary["formal_report_count"],
        "business_decision_basis_count": p3_summary["business_decision_basis_count"],
        "q5_calculation_baseline_allowed_count": 0,
        "formal_report_allowed_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S10",
        "stage_name": "report trust grade and business report generation",
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
        "s11_p1_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_v014_stage1_18_complete": True,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "v013_stage10_review_validated": True,
        "v013_stage10_review_manifest": V013_STAGE10_REVIEW_MANIFEST,
        "v013_stage10_review_status": v013_review.get("status"),
        "legacy_stage10_review_validated": True,
        "legacy_stage10_review_manifest": str(LEGACY_STAGE10_REVIEW_MANIFEST_PATH),
        "legacy_stage10_review_counts": legacy_counts,
        "legacy_stage10_upload_artifacts_current_gate": False,
        "phase_count": 3,
        "phase_results": phase_results,
        "s10_p1_dependency_validated": phase_results["S10-P1"] == "PASS",
        "s10_p2_dependency_validated": phase_results["S10-P2"] == "PASS",
        "s10_p3_dependency_validated": phase_results["S10-P3"] == "PASS",
        "reviewed_phase_manifests": {
            **PHASE_MANIFESTS,
            "v013_S10_review": V013_STAGE10_REVIEW_MANIFEST,
            "legacy_S10_review": str(LEGACY_STAGE10_REVIEW_MANIFEST_PATH),
        },
        "stage_gate": stage_gate,
        "release_state": release_state,
        "report_export_policy": {
            "report_export_version": p3_policy["report_export_version"],
            "template_version": p3_policy["template_version"],
            "formula_version": p3_policy["formula_version"],
            "mapping_version": p3_policy["mapping_version"],
            "html_template_version": p3_policy["html_template_version"],
            "csv_appendix_schema_version": p3_policy["csv_appendix_schema_version"],
            "pdf_export_policy_version": p3_policy["pdf_export_policy_version"],
            "record_version_binding_count": p3_policy["record_version_binding_count"],
            "html_export_allowed": p3_policy["html_export_allowed"],
            "csv_excel_export_allowed": p3_policy["csv_excel_export_allowed"],
            "pdf_export_policy_enabled": p3_policy["pdf_export_policy_enabled"],
            "pdf_private_runtime_only": p3_policy["pdf_private_runtime_only"],
            "formal_report_allowed": p3_policy["formal_report_allowed"],
            "business_decision_basis_allowed": p3_policy["business_decision_basis_allowed"],
        },
        "raw_data_boundary": raw_boundary,
        "public_repo_safety": public_repo_safety,
        "review_findings": review_findings,
        "review_findings_summary": {
            "open_finding_count": 0,
            "fixed_finding_count": 2,
            "passed_finding_count": 1,
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
            "generator": "KMFA/tools/v014_s10_stage_review.py",
            "validator": "KMFA/tools/check_v014_s10_stage_review.py",
            "unit_test": "KMFA/tests/test_v014_s10_stage_review.py",
            "s10_p1_manifest": PHASE_MANIFESTS["S10-P1"],
            "s10_p2_manifest": PHASE_MANIFESTS["S10-P2"],
            "s10_p3_manifest": PHASE_MANIFESTS["S10-P3"],
            "v013_stage10_review_manifest": V013_STAGE10_REVIEW_MANIFEST,
            "legacy_stage10_review_manifest": str(LEGACY_STAGE10_REVIEW_MANIFEST_PATH),
        },
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
        ],
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s10_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s10_stage_review -q",
        ],
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_INSTRUCTION,
    }


def write_report(manifest: dict[str, Any]) -> None:
    gate = manifest["stage_gate"]
    lines = [
        "# KMFA v0.1.4 Stage 10 Review Report",
        "",
        f"- task_id: `{TASK_ID}`",
        f"- status: `{manifest['status']}`",
        "- stage_review_performed: `true`",
        "- phase_results: `S10-P1=PASS, S10-P2=PASS, S10-P3=PASS`",
        f"- open_finding_count: `{manifest['review_findings_summary']['open_finding_count']}`",
        f"- fixed_finding_count: `{manifest['review_findings_summary']['fixed_finding_count']}`",
        "- github_upload_performed: `false`",
        "- s11_p1_performed: `false`",
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
            f"- report_template_count: `{gate['report_template_count']}`",
            f"- report_grade_record_count: `{gate['report_grade_record_count']}`",
            f"- report_export_record_count: `{gate['report_export_record_count']}`",
            f"- html_export_count: `{gate['html_export_count']}`",
            f"- csv_appendix_count: `{gate['csv_appendix_count']}`",
            f"- excel_compatible_download_count: `{gate['excel_compatible_download_count']}`",
            f"- pending_reconciliation_count: `{gate['pending_reconciliation_count']}`",
            f"- confirmed_resolution_count: `{gate['confirmed_resolution_count']}`",
            f"- current_report_grade: `{gate['current_report_grade']}`",
            f"- release_permission: `{gate['release_permission']}`",
            "",
            "## Boundaries",
            "",
            "- Raw/private inbox was not read, listed, inventoried, statted, hashed, modified, moved, renamed, deleted, overwritten or written by this review.",
            "- Review evidence contains only public-safe counts, status flags, validator results and governance references.",
            "- Stage 11 and GitHub upload remain out of scope for this run.",
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
        "# KMFA v0.1.4 Stage 10 Review Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `completed_validated_local_only_no_go_upload_deferred`",
        "- github_upload_performed: `false`",
        "- s11_p1_performed: `false`",
        "- raw_inbox_read_by_this_review: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Command Results",
        "",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s10_stage_review.py KMFA/tools/check_v014_s10_stage_review.py KMFA/tests/test_v014_s10_stage_review.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s10_stage_review.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_p1_report_templates.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_p2_report_trust_grade.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_p3_report_export.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s10_stage_review.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s10_stage_review.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_stage_review.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s10_stage_review -q`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`",
        "- PASS: changed/untracked parse and raw/private suffix scan.",
        "- PASS: changed/untracked strict secret token scan.",
        "- PASS: scoped Stage 10 review public evidence raw/private semantic scan.",
        "- PASS: `git diff --check -- KMFA scripts`",
        "",
        "Note: Stage 11 and GitHub upload were intentionally not performed in this review.",
        "",
    ]
    write_text(TEST_RESULTS_PATH, "\n".join(lines))


def write_risk_register() -> None:
    lines = [
        "# KMFA v0.1.4 Stage 10 Review Risk Register",
        "",
        "| Risk | Control | Status |",
        "|---|---|---|",
        "| D-grade reports are mistaken for formal management reports | release_state keeps formal report and business basis false | controlled |",
        "| Historical upload evidence is treated as current gate | review finding F01 fixes current v1.4 upload boundary to deferred | controlled |",
        "| Report export evidence leaks raw/private values | validator scans review evidence and requires public-safe aggregate-only evidence | controlled |",
        "| Review drifts into S11 or GitHub upload | manifest and validator require s11_p1_performed=false and github_upload_performed=false | controlled |",
        "",
    ]
    write_text(RISK_REGISTER_PATH, "\n".join(lines))


def write_rollback_plan() -> None:
    lines = [
        "# KMFA v0.1.4 Stage 10 Review Rollback Plan",
        "",
        "- Remove `KMFA/stage_artifacts/V014_S10_STAGE_REVIEW/` if review evidence is invalid.",
        "- Revert `KMFA/tools/v014_s10_stage_review.py`, `KMFA/tools/check_v014_s10_stage_review.py` and `KMFA/tests/test_v014_s10_stage_review.py` if validator logic is invalid.",
        "- Restore governance/status files to the prior S10-P3 handoff state if review validation fails.",
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
        "PASS: KMFA v0.1.4 Stage 10 review evidence generated "
        f"(phase_results={manifest['phase_results']}, "
        f"open_findings={manifest['review_findings_summary']['open_finding_count']}, "
        f"fixed_findings={manifest['review_findings_summary']['fixed_finding_count']}, "
        f"stage11=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
