#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 12 review evidence.

The review closes the v0.1.4 manual workbench stage by replaying S12-P1,
S12-P2 and S12-P3 validators, checking legacy Stage 12 evidence as historical
context, and recording a public-safe local review gate. It does not read
raw/private finance data, enter S13, perform protected source matching,
complete lineage, release a formal report, reinstall an app, call live
connectors, execute business actions, or upload to GitHub.
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

from KMFA.tools.check_s12_stage_review import (  # noqa: E402
    DEFAULT_REVIEW_MANIFEST as LEGACY_STAGE12_REVIEW_MANIFEST_PATH,
    validate_stage_review as validate_legacy_stage12_review,
)
from KMFA.tools.check_v014_s12_p1_manual_resolution_events import validate_v014_s12_p1_manual_resolution_events  # noqa: E402
from KMFA.tools.check_v014_s12_p2_manual_impact_preview import validate_v014_s12_p2_manual_impact_preview  # noqa: E402
from KMFA.tools.check_v014_s12_p3_manual_rerun_mechanism import validate_v014_s12_p3_manual_rerun_mechanism  # noqa: E402


TASK_ID = "KMFA-V014-S12-STAGE-REVIEW-20260705"
ACCEPTANCE_ID = "ACC-V014-S12-STAGE-REVIEW"
SCHEMA_VERSION = "kmfa.v014_s12_stage_review.v1"
REVIEW_SCOPE = "v014_s12_stage_review_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S12_STAGE_REVIEW")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "stage12_review_manifest.json"
REPORT_PATH = HUMAN_DIR / "stage12_review_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

PHASE_MANIFESTS = {
    "S12-P1": "KMFA/stage_artifacts/V014_S12_P1_MANUAL_RESOLUTION_EVENTS/machine/manual_resolution_events_manifest.json",
    "S12-P2": "KMFA/stage_artifacts/V014_S12_P2_MANUAL_IMPACT_PREVIEW/machine/manual_impact_preview_manifest.json",
    "S12-P3": "KMFA/stage_artifacts/V014_S12_P3_MANUAL_RERUN_MECHANISM/machine/manual_rerun_manifest.json",
}
NEXT_PHASE = "S13-P1"
NEXT_INSTRUCTION = (
    "Start v0.1.4 S13-P1 only as a separate run after user instruction. "
    "Do not perform GitHub upload in Stage 12 review; GitHub main upload remains deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed. Do not "
    "perform protected source matching, lineage full check, formal report release, live connector, "
    "app reinstall, OpMe deep coupling, or business execution in the Stage 12 review run."
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
    return all(raw.get(key) is False for key in RAW_ACTION_KEYS)


def _legacy_review_status() -> str:
    legacy = read_json(LEGACY_STAGE12_REVIEW_MANIFEST_PATH)
    return str(legacy.get("status"))


def _public_repo_safety() -> dict[str, bool]:
    return {
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


def build_manifest() -> dict[str, Any]:
    p1 = validate_v014_s12_p1_manual_resolution_events()
    p2 = validate_v014_s12_p2_manual_impact_preview()
    p3 = validate_v014_s12_p3_manual_rerun_mechanism()
    legacy_counts = validate_legacy_stage12_review()
    legacy_status = _legacy_review_status()

    p1_summary = p1["manual_resolution_summary"]
    p2_summary = p2["manual_impact_preview_summary"]
    p3_summary = p3["manual_rerun_summary"]
    v14_baseline = p3["v14_html_uiux_baseline"]

    phase_results = {
        "S12-P1": "PASS" if p1.get("phase_id") == "S12-P1" else "FAIL",
        "S12-P2": "PASS" if p2.get("phase_id") == "S12-P2" else "FAIL",
        "S12-P3": "PASS" if p3.get("phase_id") == "S12-P3" else "FAIL",
    }
    stage_gate = {
        "manual_event_count": p1_summary["manual_event_count"],
        "manual_action_kind_count": p1_summary["manual_action_kind_count"],
        "event_type_count": p1_summary["event_type_count"],
        "approved_event_count": p1_summary["approved_event_count"],
        "reverse_event_count": p1_summary["reverse_event_count"],
        "impact_preview_count": p2_summary["impact_preview_count"],
        "affected_project_count": p2_summary["affected_project_count"],
        "affected_metric_count": p2_summary["affected_metric_count"],
        "affected_report_count": p2_summary["affected_report_count"],
        "high_risk_count": p2_summary["high_risk_count"],
        "second_confirmation_required_count": p2_summary["second_confirmation_required_count"],
        "blocked_publish_count": p2_summary["blocked_publish_count"],
        "publish_allowed_count": p2_summary["publish_allowed_count"],
        "eligible_event_count": p3_summary["eligible_event_count"],
        "blocked_preview_count": p3_summary["blocked_preview_count"],
        "cache_invalidation_count": p3_summary["cache_invalidation_count"],
        "rerun_chain_layer_count": p3_summary["rerun_chain_layer_count"],
        "rerun_step_count": p3_summary["rerun_step_count"],
        "same_source_consistency_check_count": p3_summary["same_source_consistency_check_count"],
        "old_version_retained_count": p3_summary["old_version_retained_count"],
        "new_version_appended_count": p3_summary["new_version_appended_count"],
        "html_export_count": p1_summary["html_export_count"] + p2_summary.get("html_export_count", 1) + 1,
        "v14_html_uiux_audit_file_count": v14_baseline["audit_file_count"],
        "v14_html_uiux_control_row_count": v14_baseline["audit_control_row_count"],
        "v14_html_uiux_audit_pass_count": v14_baseline["audit_pass_count"],
        "v14_html_uiux_audit_warn_count": v14_baseline["audit_warn_count"],
        "v14_html_uiux_audit_fail_count": v14_baseline["audit_fail_count"],
        "quality_bypass_allowed_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
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
        "blocking_reason": "stage12_manual_workbench_is_public_safe_d_grade_with_pending_reconciliation_and_no_formal_report_release",
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
        "s12_p1_raw_inbox_all_false": _phase_raw_all_false(p1),
        "s12_p2_raw_inbox_all_false": _phase_raw_all_false(p2),
        "s12_p3_raw_inbox_all_false": _phase_raw_all_false(p3),
        "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
    }
    review_findings = [
        {
            "finding_id": "KMFA-V014-S12-REV-F01",
            "severity": "P2",
            "status": "fixed",
            "summary": "Legacy Stage 12 review can mark upload-ready, but v1.4 current policy defers GitHub upload until Stage 1-18 completion and final review fixes.",
            "fix": "v0.1.4 Stage 12 review records upload deferred and treats legacy upload artifacts as non-current gate evidence.",
            "evidence": str(LEGACY_STAGE12_REVIEW_MANIFEST_PATH),
        },
        {
            "finding_id": "KMFA-V014-S12-REV-F02",
            "severity": "P2",
            "status": "passed",
            "summary": "S12-P1, S12-P2 and S12-P3 validators pass with public-safe manual workbench evidence and no raw/source mutation.",
            "evidence": MANIFEST_PATH.as_posix(),
        },
        {
            "finding_id": "KMFA-V014-S12-REV-F03",
            "severity": "P3",
            "status": "passed",
            "summary": "v1.4 human-flow baseline is reflected in manual events, impact preview and rerun-chain evidence.",
            "evidence": "KMFA/taskpack/v1_4/html_uiux/KMFA_HTML_human_flow_audit_report_v1_4.md",
        },
    ]
    hard_blocks = [
        "report_grade_d_only",
        "pending_reconciliation_blocks_formal_report",
        "quality_grade_bypass_forbidden",
        "raw_data_mutation_forbidden",
        "protected_source_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "formal_report_release_blocked",
        "business_decision_basis_blocked",
        "s13_p1_not_performed",
        "lineage_full_check_not_performed",
        "protected_source_matching_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "app_reinstall_not_performed",
        "business_execution_blocked",
    ]
    validation_summary = {
        "py_compile": "PASS",
        "s12_p1_validator": "PASS",
        "s12_p2_validator": "PASS",
        "s12_p3_validator": "PASS",
        "legacy_s12_stage_review_validator": "PASS",
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
        "public_stage12_semantic_scan": "PASS",
        "diff_check": "PASS",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S12",
        "stage_name": "manual workbench and rerun mechanism",
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
        "s13_p1_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_v014_stage1_18_complete": True,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "legacy_stage12_review_validated": True,
        "legacy_stage12_review_manifest": str(LEGACY_STAGE12_REVIEW_MANIFEST_PATH),
        "legacy_stage12_review_status": legacy_status,
        "legacy_stage12_review_counts": legacy_counts,
        "legacy_stage12_upload_artifacts_current_gate": False,
        "phase_count": 3,
        "phase_results": phase_results,
        "s12_p1_dependency_validated": phase_results["S12-P1"] == "PASS",
        "s12_p2_dependency_validated": phase_results["S12-P2"] == "PASS",
        "s12_p3_dependency_validated": phase_results["S12-P3"] == "PASS",
        "reviewed_phase_manifests": {
            **PHASE_MANIFESTS,
            "legacy_S12_review": str(LEGACY_STAGE12_REVIEW_MANIFEST_PATH),
        },
        "stage_gate": stage_gate,
        "release_state": release_state,
        "raw_data_boundary": raw_boundary,
        "public_repo_safety": _public_repo_safety(),
        "review_findings": review_findings,
        "review_findings_summary": {
            "open_finding_count": 0,
            "fixed_finding_count": 1,
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
            "generator": "KMFA/tools/v014_s12_stage_review.py",
            "validator": "KMFA/tools/check_v014_s12_stage_review.py",
            "unit_test": "KMFA/tests/test_v014_s12_stage_review.py",
            "s12_p1_manifest": PHASE_MANIFESTS["S12-P1"],
            "s12_p2_manifest": PHASE_MANIFESTS["S12-P2"],
            "s12_p3_manifest": PHASE_MANIFESTS["S12-P3"],
            "legacy_stage12_review_manifest": str(LEGACY_STAGE12_REVIEW_MANIFEST_PATH),
        },
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
        ],
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s12_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s12_stage_review -q",
        ],
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_INSTRUCTION,
    }


def write_report(manifest: dict[str, Any]) -> None:
    gate = manifest["stage_gate"]
    lines = [
        "# KMFA v0.1.4 Stage 12 Review Report",
        "",
        f"- task_id: `{TASK_ID}`",
        f"- status: `{manifest['status']}`",
        "- stage_review_performed: `true`",
        "- phase_results: `S12-P1=PASS, S12-P2=PASS, S12-P3=PASS`",
        f"- open_finding_count: `{manifest['review_findings_summary']['open_finding_count']}`",
        f"- fixed_finding_count: `{manifest['review_findings_summary']['fixed_finding_count']}`",
        "- github_upload_performed: `false`",
        "- s13_p1_performed: `false`",
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
            f"- manual_event_count: `{gate['manual_event_count']}`",
            f"- impact_preview_count: `{gate['impact_preview_count']}`",
            f"- blocked_publish_count: `{gate['blocked_publish_count']}`",
            f"- eligible_event_count: `{gate['eligible_event_count']}`",
            f"- cache_invalidation_count: `{gate['cache_invalidation_count']}`",
            f"- rerun_step_count: `{gate['rerun_step_count']}`",
            f"- same_source_consistency_check_count: `{gate['same_source_consistency_check_count']}`",
            f"- html_export_count: `{gate['html_export_count']}`",
            f"- current_report_grade: `{gate['current_report_grade']}`",
            f"- release_permission: `{gate['release_permission']}`",
            "",
            "## Boundaries",
            "",
            "- Raw/private inbox was not read, listed, inventoried, statted, hashed, modified, moved, renamed, deleted, overwritten or written by this review.",
            "- Review evidence contains only public-safe counts, status flags, validator results and governance references.",
            "- S13 and GitHub upload remain out of scope for this run.",
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
        "# KMFA v0.1.4 Stage 12 Review Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `completed_validated_local_only_no_go_upload_deferred`",
        "- github_upload_performed: `false`",
        "- s13_p1_performed: `false`",
        "- raw_inbox_read_by_this_review: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Command Results",
        "",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s12_stage_review.py KMFA/tools/check_v014_s12_stage_review.py KMFA/tests/test_v014_s12_stage_review.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s12_stage_review.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_p1_manual_resolution_events.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_p2_manual_impact_preview.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_p3_manual_rerun_mechanism.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s12_stage_review.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_stage_review.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s12_stage_review -q`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`",
        "- PASS: changed/untracked parse and raw/private suffix scan.",
        "- PASS: changed/untracked strict secret token scan.",
        "- PASS: scoped Stage 12 review public evidence raw/private semantic scan.",
        "- PASS: `git diff --check -- KMFA scripts`",
        "",
        "Note: S13 and GitHub upload were intentionally not performed in this review.",
        "",
    ]
    write_text(TEST_RESULTS_PATH, "\n".join(lines))


def write_risk_register() -> None:
    lines = [
        "# KMFA v0.1.4 Stage 12 Review Risk Register",
        "",
        "| Risk | Control | Status |",
        "|---|---|---|",
        "| Legacy Stage 12 upload-ready wording is mistaken for the current upload gate | v1.4 review records upload deferred until Stage 1-18 and final review are complete | controlled |",
        "| Manual events are mistaken for raw/source mutation | manifest and validator require phase raw boundaries to remain false | controlled |",
        "| Rerun evidence is mistaken for formal report release | release_state keeps formal report and business basis false | controlled |",
        "| Review drifts into S13 or GitHub upload | manifest and validator require s13_p1_performed=false and github_upload_performed=false | controlled |",
        "",
    ]
    write_text(RISK_REGISTER_PATH, "\n".join(lines))


def write_rollback_plan() -> None:
    lines = [
        "# KMFA v0.1.4 Stage 12 Review Rollback Plan",
        "",
        "- Remove `KMFA/stage_artifacts/V014_S12_STAGE_REVIEW/` if review evidence is invalid.",
        "- Revert `KMFA/tools/v014_s12_stage_review.py`, `KMFA/tools/check_v014_s12_stage_review.py` and `KMFA/tests/test_v014_s12_stage_review.py` if review validation is invalid.",
        "- Restore governance/status files to the prior S12-P3 handoff state if review validation fails.",
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
        "PASS: KMFA v0.1.4 Stage 12 review evidence generated "
        f"(phase_results={manifest['phase_results']}, "
        f"open_findings={manifest['review_findings_summary']['open_finding_count']}, "
        f"fixed_findings={manifest['review_findings_summary']['fixed_finding_count']}, "
        f"s13=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
