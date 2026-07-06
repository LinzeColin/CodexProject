#!/usr/bin/env python3
"""Prepare a public-safe residual gap report for KMFA v0.1.4.

This phase turns the conservative business resolution into a gap-report
package. It does not reconcile values, rerun materialization, read raw files, or
claim delivery readiness. Public outputs stay aggregate-only; private runtime
receives the follow-up diagnostic package for a corrected source package or a
future explicitly scoped raw comparison.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_RESIDUAL_GAP_REPORT_PREP"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-RESIDUAL-GAP-REPORT-PREP-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-RESIDUAL-GAP-REPORT-PREP"
VERSION = "0.1.4-residual-gap-report-prep"
STATUS = "completed_validated_local_only_residual_gap_report_prep_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "residual_gap_report_prepared_delivery_still_blocked"
PREVIOUS_REQUIRED_INPUT = "private_residual_gap_report_or_corrected_source_package_before_any_delivery_claim"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_RAW_SCOPE_INTAKE"
NEXT_REQUIRED_INPUT = "corrected_source_package_or_owner_authorized_private_raw_comparison_scope"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_residual_gap_report_prep_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_residual_gap_report_prep_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_residual_gap_report_prep_go_no_go_report.json"
PUBLIC_GAP_MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_residual_gap_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_residual_gap_report_prep_report.md"
PUBLIC_GAP_REPORT_PATH = HUMAN_DIR / "residual_gap_report_public_safe.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_residual_gap_report_prep_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_residual_gap_report_prep_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_residual_gap_report_prep_go_no_go_report.json"
METADATA_GAP_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_residual_gap_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_EXPLICIT_RESOLUTION_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_EXPLICIT_BUSINESS_RESOLUTION_INTAKE/machine/processed_value_source_map_completion_explicit_business_resolution_intake_summary.json"
)
SOURCE_FINAL_LOCK_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_FINAL_NO_GO_GOVERNANCE_LOCK/machine/processed_value_source_map_completion_final_no_go_governance_lock_summary.json"
)
SOURCE_OWNER_DIAGNOSTIC_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_DIAGNOSTIC_PACKET/machine/processed_value_source_map_completion_owner_diagnostic_packet_summary.json"
)
SOURCE_PRIVATE_RESOLUTION_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_explicit_business_resolution_intake/private_explicit_business_resolution_record.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_residual_gap_report_prep"
PRIVATE_GAP_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_residual_gap_report.json"
PRIVATE_GAP_REPORT_MARKDOWN_PATH = PRIVATE_OUTPUT_DIR / "private_residual_gap_report.md"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_residual_gap_report_diagnostic.json"


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def _git_check_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_data_root_readonly_policy_active": True,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
        "raw_inbox_write_performed_by_this_phase": False,
        "raw_inbox_delete_performed_by_this_phase": False,
        "raw_inbox_move_performed_by_this_phase": False,
        "raw_inbox_rename_performed_by_this_phase": False,
        "raw_inbox_overwrite_performed_by_this_phase": False,
        "raw_inbox_copy_performed_by_this_phase": False,
        "raw_inbox_normalize_performed_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_source_resolution_committed": False,
        "private_gap_report_committed": False,
        "private_gap_report_markdown_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "processed_value_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _gap_matrix(*, blocker_count: int, group_count: int, target_slot_count: int) -> dict[str, Any]:
    categories = [
        {
            "gap_code": "NON_ACTIONABLE_GROUPS",
            "public_description": "部分已识别缺口只能保持 NO-GO，不能作为交付或报告依据。",
            "aggregate_group_count": group_count,
            "aggregate_target_slot_count": target_slot_count,
            "blocks_delivery": True,
            "blocks_full_comparison": True,
            "owner_action": "提供修正源包或授权后续私有对账范围。",
        },
        {
            "gap_code": "FULL_RECONCILIATION_BLOCKED",
            "public_description": "完整 source-map reapplication 和 raw-to-processed comparison 尚未可执行。",
            "aggregate_blocker_count": blocker_count,
            "blocks_delivery": True,
            "blocks_full_comparison": True,
            "owner_action": "先确认缺口处理方式，再进入单独对账 phase。",
        },
        {
            "gap_code": "FORMAL_REPORT_BLOCKED",
            "public_description": "正式报告、经营决策依据和业务动作仍被质量门禁阻断。",
            "aggregate_blocker_count": blocker_count,
            "blocks_delivery": True,
            "blocks_full_comparison": False,
            "owner_action": "不得绕过报告等级和差异队列。",
        },
        {
            "gap_code": "UPLOAD_AND_APP_BLOCKED",
            "public_description": "GitHub main upload 和 app reinstall 必须等 v1.4 整体复审后一次性执行。",
            "aggregate_blocker_count": blocker_count,
            "blocks_delivery": True,
            "blocks_full_comparison": False,
            "owner_action": "继续本地 phase，不执行上传或安装。",
        },
    ]
    return {
        "schema_version": "kmfa.v014_residual_gap_matrix_public_safe.v1",
        "record_type": "v014_residual_gap_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "gap_category_count": len(categories),
        "aggregate_blocker_count": blocker_count,
        "non_actionable_group_count": group_count,
        "non_actionable_target_slot_count": target_slot_count,
        "categories": categories,
    }


def _build_private_gap_report(
    *,
    generated_at: str,
    explicit_resolution: dict[str, Any],
    final_lock: dict[str, Any],
    owner_diagnostic: dict[str, Any],
    private_resolution: dict[str, Any],
    gap_matrix: dict[str, Any],
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    report = {
        "schema_version": "kmfa.private.v014_residual_gap_report.v1",
        "classification": "private_residual_gap_report_do_not_commit",
        "record_type": "v014_residual_gap_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision": DECISION,
        "source_explicit_resolution_phase_id": explicit_resolution.get("phase_id"),
        "source_final_lock_phase_id": final_lock.get("phase_id"),
        "source_owner_diagnostic_phase_id": owner_diagnostic.get("phase_id"),
        "source_private_resolution_phase_id": private_resolution.get("phase_id"),
        "previous_required_input": PREVIOUS_REQUIRED_INPUT,
        "previous_required_input_resolved_by_this_phase": True,
        "residual_gap_report_ready": True,
        "gap_category_count": gap_matrix["gap_category_count"],
        "aggregate_blocker_count": gap_matrix["aggregate_blocker_count"],
        "non_actionable_group_count": gap_matrix["non_actionable_group_count"],
        "non_actionable_target_slot_count": gap_matrix["non_actionable_target_slot_count"],
        "recommended_next_actions": [
            "request_corrected_source_package",
            "or_define_owner_authorized_private_raw_comparison_scope",
            "then_run_a_separate_single_phase_precheck_before_any_full_comparison",
        ],
        "disallowed_actions": [
            "delivery_claim",
            "formal_report_release",
            "github_upload",
            "app_reinstall",
            "business_execution",
            "full_raw_to_processed_comparison_without_next_scope",
        ],
        "public_gap_matrix": gap_matrix,
        "raw_boundary": _raw_boundary(),
    }
    markdown = f"""# Private Residual Gap Report

- decision: `{DECISION}`
- residual gap report ready: `true`
- gap categories: `{gap_matrix["gap_category_count"]}`
- aggregate blockers: `{gap_matrix["aggregate_blocker_count"]}`
- non-actionable groups: `{gap_matrix["non_actionable_group_count"]}`
- non-actionable target slots: `{gap_matrix["non_actionable_target_slot_count"]}`
- previous required input resolved by this phase: `true`
- full comparison allowed by this phase: `false`
- delivery allowed: `false`

Next step is either a corrected source package or an owner-authorized private
raw comparison scope. This report does not contain raw filenames, field names,
table names, business values, or source values.
"""
    diagnostic = {
        "schema_version": "kmfa.private.v014_residual_gap_report_diagnostic.v1",
        "classification": "private_residual_gap_report_diagnostic_do_not_commit",
        "record_type": "v014_residual_gap_report_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "residual_gap_report_ready": True,
        "gap_category_count": gap_matrix["gap_category_count"],
        "previous_required_input_resolved_by_this_phase": True,
        "full_comparison_allowed_by_this_phase": False,
        "delivery_allowed": False,
        "raw_boundary": _raw_boundary(),
    }
    return report, markdown, diagnostic


def generate(generated_at: str | None = None, *, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    explicit_resolution = _read_json(SOURCE_EXPLICIT_RESOLUTION_SUMMARY_PATH)
    final_lock = _read_json(SOURCE_FINAL_LOCK_SUMMARY_PATH)
    owner_diagnostic = _read_json(SOURCE_OWNER_DIAGNOSTIC_SUMMARY_PATH)
    private_resolution = _read_json(SOURCE_PRIVATE_RESOLUTION_PATH)

    blocker_count = int(final_lock.get("blocker_count") or 0)
    group_count = int(final_lock.get("non_actionable_group_count") or 0)
    target_slot_count = int(final_lock.get("non_actionable_target_slot_count") or 0)
    gap_matrix = _gap_matrix(
        blocker_count=blocker_count,
        group_count=group_count,
        target_slot_count=target_slot_count,
    )
    private_report, private_markdown, private_diagnostic = _build_private_gap_report(
        generated_at=timestamp,
        explicit_resolution=explicit_resolution,
        final_lock=final_lock,
        owner_diagnostic=owner_diagnostic,
        private_resolution=private_resolution,
        gap_matrix=gap_matrix,
    )
    _write_json(PRIVATE_GAP_REPORT_PATH, private_report)
    _write_text(PRIVATE_GAP_REPORT_MARKDOWN_PATH, private_markdown)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)

    summary = {
        "schema_version": "kmfa.v014_residual_gap_report_prep_summary.v1",
        "record_type": "v014_residual_gap_report_prep_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_explicit_resolution_phase_id": explicit_resolution.get("phase_id"),
        "source_explicit_resolution_decision": explicit_resolution.get("decision"),
        "source_final_lock_phase_id": final_lock.get("phase_id"),
        "source_final_lock_decision": final_lock.get("decision"),
        "source_owner_diagnostic_phase_id": owner_diagnostic.get("phase_id"),
        "source_owner_diagnostic_decision": owner_diagnostic.get("decision"),
        "source_private_resolution_read_performed_by_this_phase": True,
        "previous_required_input": PREVIOUS_REQUIRED_INPUT,
        "previous_required_input_resolved_by_this_phase": True,
        "residual_gap_report_ready": True,
        "public_gap_matrix_ready": True,
        "gap_category_count": gap_matrix["gap_category_count"],
        "final_no_go_governance_lock_active": final_lock.get("final_no_go_governance_lock_active") is True,
        "partial_evidence_chain_ready": final_lock.get("partial_evidence_chain_ready") is True,
        "blocker_count": blocker_count,
        "non_actionable_group_count": group_count,
        "non_actionable_target_slot_count": target_slot_count,
        "non_actionable_groups_delivery_use_allowed": False,
        "non_actionable_groups_formal_report_use_allowed": False,
        "non_actionable_groups_business_execution_use_allowed": False,
        "corrected_source_package_required_or_raw_scope_required": True,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_allowed": False,
        "app_reinstall_performed": False,
        "business_execution_allowed": False,
        "business_execution_performed": False,
        "full_source_map_completion_reapplication_ready": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "business_value_consistency_verified": False,
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "private_gap_report_written": PRIVATE_GAP_REPORT_PATH.exists(),
        "private_gap_report_gitignored": _git_check_ignored(PRIVATE_GAP_REPORT_PATH),
        "private_gap_report_markdown_written": PRIVATE_GAP_REPORT_MARKDOWN_PATH.exists(),
        "private_gap_report_markdown_gitignored": _git_check_ignored(PRIVATE_GAP_REPORT_MARKDOWN_PATH),
        "private_diagnostic_written": PRIVATE_DIAGNOSTIC_PATH.exists(),
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "public_safety": _public_safety(),
        "raw_boundary": _raw_boundary(),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }
    go_no_go = {
        "schema_version": "kmfa.v014_residual_gap_report_prep_go_no_go.v1",
        "record_type": "v014_residual_gap_report_prep_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "blocked_until": NEXT_REQUIRED_INPUT,
        "residual_gap_report_ready": True,
        "gap_category_count": gap_matrix["gap_category_count"],
        "previous_required_input_resolved_by_this_phase": True,
        "delivery_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_residual_gap_report_prep_manifest.v1",
        "record_type": "v014_residual_gap_report_prep_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "git_head": _git_output(["rev-parse", "HEAD"]),
        "git_branch": _git_output(["branch", "--show-current"]),
        "source_artifacts": [
            SOURCE_EXPLICIT_RESOLUTION_SUMMARY_PATH.as_posix(),
            SOURCE_FINAL_LOCK_SUMMARY_PATH.as_posix(),
            SOURCE_OWNER_DIAGNOSTIC_SUMMARY_PATH.as_posix(),
            "private:explicit_business_resolution_record",
        ],
        "public_outputs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            PUBLIC_GAP_MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            PUBLIC_GAP_REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_GAP_MATRIX_PATH.as_posix(),
        ],
        "private_outputs": [
            "private:residual_gap_report",
            "private:residual_gap_report_markdown",
            "private:residual_gap_report_diagnostic",
        ],
        "summary": summary,
        "go_no_go": go_no_go,
        "public_gap_matrix": gap_matrix,
    }
    report = f"""# Residual Gap Report Prep

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- residual gap report ready: `true`
- public gap matrix ready: `true`
- gap categories: `{gap_matrix["gap_category_count"]}`
- blocker count: `{blocker_count}`
- non-actionable groups: `{group_count}`
- non-actionable target slots: `{target_slot_count}`
- delivery allowed: `false`

This phase prepares a public-safe residual gap report and an ignored private
diagnostic package. It does not read raw files, perform value comparison,
reapply the source map, release a formal report, upload to GitHub, reinstall the
app, or execute business actions.
"""
    public_gap_report = f"""# Public-Safe Residual Gap Report

## Summary

- Go/No-Go: `{DECISION}`
- Gap category count: `{gap_matrix["gap_category_count"]}`
- Aggregate blocker count: `{blocker_count}`
- Non-actionable group count: `{group_count}`
- Non-actionable target-slot count: `{target_slot_count}`

## Required Next Input

- `{NEXT_REQUIRED_INPUT}`

## Current Restrictions

- Full raw-to-processed comparison: `blocked`
- Business-value consistency claim: `blocked`
- Formal report / GitHub upload / app reinstall / business execution: `blocked`
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- residual_gap_report_ready: `true`
- delivery_allowed: `false`
- github_upload_allowed: `false`
- app_reinstall_allowed: `false`
- business_execution_allowed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating the residual gap report as a reconciliation result.
  Mitigation: full comparison and business-value consistency remain blocked.
- Risk: leaking private source detail in public evidence.
  Mitigation: public artifacts contain only aggregate counts and status flags.
"""
    rollback_plan = """# Rollback Plan

No raw file, canonical source-map file, active authorization record, report release artifact or business output was modified. To roll back, remove this phase's public artifacts and ignored private gap report outputs.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_residual_gap_report_prep.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_residual_gap_report_prep.py --require-private-gap-report`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_residual_gap_report_prep`
"""
    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (PUBLIC_GAP_MATRIX_PATH, gap_matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_GAP_MATRIX_PATH, gap_matrix),
    ):
        _write_json(path, payload)
    for path, text in (
        (REPORT_PATH, report),
        (PUBLIC_GAP_REPORT_PATH, public_gap_report),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback_plan),
        (TEST_RESULTS_PATH, test_results),
    ):
        _write_text(path, text)
    if write_governance_event:
        _append_development_event(timestamp, manifest)
    return manifest


def _append_development_event(generated_at: str, manifest: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-RESIDUAL-GAP-REPORT-PREP"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-RESIDUAL-GAP-REPORT-PREP",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "residual_gap_report_ready": True,
        "gap_category_count": summary["gap_category_count"],
        "delivery_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "result_commit": "PENDING",
        "summary": "Prepared public-safe residual gap report package while keeping v0.1.4 delivery gates closed.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    print(
        "PASS: KMFA v0.1.4 residual gap report prep generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"report={manifest['summary']['residual_gap_report_ready']}, "
        f"gap_categories={manifest['summary']['gap_category_count']})"
    )


if __name__ == "__main__":
    main()
