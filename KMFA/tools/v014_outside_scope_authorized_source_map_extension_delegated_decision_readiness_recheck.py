#!/usr/bin/env python3
"""Recheck application readiness after delegated outside-scope decisions.

This phase reads only the previous ignored private delegated decision record
and queue plus the previous public-safe summary. It proves that the delegated
KEEP_PENDING response did not unlock source-map extension application. It does
not read the raw inbox, mutate prior private inputs, write source-map records,
compare values, reconcile values, upload, reinstall, or execute business steps.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_DELEGATED_DECISION_READINESS_RECHECK"
TASK_ID = (
    "KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-"
    "DELEGATED-DECISION-READINESS-RECHECK-20260706"
)
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-DELEGATED-DECISION-READINESS-RECHECK"
VERSION = "0.1.4-outside-scope-authorized-source-map-extension-delegated-decision-readiness-recheck"
STATUS = "completed_validated_local_only_outside_scope_authorized_extension_delegated_decision_readiness_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "delegated_keep_pending_decision_confirms_source_map_extension_not_ready"
NEXT_REQUIRED_INPUT = "strong_authorized_source_map_extension_evidence_before_source_map_application_or_keep_no_go"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_POST_DELEGATION_BLOCKER_AUDIT"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck_matrix_public_safe.json"
)
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

PRIOR_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_summary.json"
)
PRIOR_PRIVATE_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision"
)
PRIOR_PRIVATE_DECISION_RECORD_PATH = PRIOR_PRIVATE_DIR / "private_delegated_keep_pending_decision_record.json"
PRIOR_PRIVATE_DECISION_QUEUE_PATH = PRIOR_PRIVATE_DIR / "private_delegated_keep_pending_decision_queue.jsonl"
PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck"
)
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_delegated_decision_readiness_recheck_diagnostic.json"

GOVERNANCE_FILES_CHANGED = [
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/VERSION",
    "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
    "KMFA/docs/governance/MODEL_SPEC.md",
    "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md",
    "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml",
    "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/development_events.jsonl",
    "KMFA/docs/governance/events.jsonl",
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
]


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain JSON object lines")
        rows.append(value)
    return rows


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
        "prior_private_delegated_decision_record_read_by_this_phase": True,
        "prior_private_delegated_decision_queue_read_by_this_phase": True,
        "prior_public_summary_read_by_this_phase": True,
        "private_readiness_diagnostic_written_by_this_phase": True,
        "prior_private_delegated_decision_record_mutated_by_this_phase": False,
        "prior_private_delegated_decision_queue_mutated_by_this_phase": False,
        "source_map_extension_written_by_this_phase": False,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
        "raw_inbox_file_content_hash_performed_by_this_phase": False,
        "raw_inbox_parse_performed_by_this_phase": False,
        "raw_inbox_field_or_header_read_performed_by_this_phase": False,
        "raw_inbox_value_extraction_performed_by_this_phase": False,
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
        "prior_private_record_committed": False,
        "prior_private_queue_committed": False,
        "private_readiness_diagnostic_committed": False,
        "private_source_map_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_file_hash_committed": False,
        "source_archive_label_committed": False,
        "source_schema_label_committed": False,
        "target_detail_committed": False,
        "row_content_committed": False,
        "sensitive_business_content_committed": False,
        "private_ref_committed": False,
        "credential_or_secret_committed": False,
    }


def _decision_counts(queue_rows: list[dict[str, Any]]) -> dict[str, int]:
    keep_pending = sum(1 for row in queue_rows if row.get("owner_decision_code") == "KEEP_PENDING")
    authorize = sum(1 for row in queue_rows if row.get("owner_decision_code") == "AUTHORIZE_SOURCE_MAP_EXTENSION")
    owner_exclusion = sum(
        1 for row in queue_rows if row.get("owner_decision_code") == "EXCLUDE_FROM_FULL_COMPARISON_WITH_OWNER_REASON"
    )
    application_allowed = sum(1 for row in queue_rows if row.get("source_map_extension_application_allowed") is True)
    return {
        "delegated_decision_record_count": len(queue_rows),
        "delegated_keep_pending_decision_count": keep_pending,
        "delegated_authorize_source_map_extension_count": authorize,
        "delegated_owner_exclusion_count": owner_exclusion,
        "delegated_application_allowed_count": application_allowed,
    }


def _build_summary(
    *, generated_at: str, prior_summary: dict[str, Any], prior_private_record: dict[str, Any], queue_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    counts = _decision_counts(queue_rows)
    prior_private_summary = prior_private_record.get("private_summary")
    if not isinstance(prior_private_summary, dict):
        raise ValueError("prior private delegated record missing private_summary")

    readiness_blockers = counts["delegated_keep_pending_decision_count"] + counts["delegated_owner_exclusion_count"]
    application_ready = (
        counts["delegated_decision_record_count"] == 72
        and counts["delegated_authorize_source_map_extension_count"] == 72
        and counts["delegated_application_allowed_count"] == 72
    )
    return {
        "schema_version": "kmfa.v014_outside_scope_delegated_decision_readiness_recheck_summary.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "prior_phase_id": prior_summary.get("phase_id"),
        "prior_decision": prior_summary.get("decision"),
        "prior_delegated_default_decision_applied": prior_summary.get("delegated_default_decision_applied_by_this_phase"),
        "prior_exact_source_record_ref_match_count": prior_summary.get("exact_source_record_ref_match_count"),
        "prior_exact_processed_ref_match_count": prior_summary.get("exact_processed_ref_match_count"),
        "prior_valid_authorized_extension_record_count": prior_summary.get("valid_authorized_extension_record_count"),
        "post_delegation_blocker_observation_count": 1,
        "post_delegation_blocked_audit_threshold_met": False,
        "goal_status_recommendation": "continue_waiting_for_strong_authorized_evidence",
        "private_record_summary_count_match": prior_private_summary.get("delegated_decision_record_count")
        == counts["delegated_decision_record_count"],
        **counts,
        "valid_authorized_extension_record_count": 0,
        "source_map_extension_ready_count": 0,
        "source_map_extension_blocker_count": readiness_blockers,
        "source_map_extension_application_ready": application_ready,
        "source_map_extension_application_feasible_after_delegated_decision": application_ready,
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "full_reconciliation_allowed": False,
        "processed_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("prior_phase_is_delegated_keep_pending", summary["prior_phase_id"].endswith("DELEGATED_KEEP_PENDING_DECISION")),
        ("delegated_decision_count_complete", summary["delegated_decision_record_count"] == 72),
        ("all_delegated_decisions_keep_pending", summary["delegated_keep_pending_decision_count"] == 72),
        ("no_delegated_authorization", summary["delegated_authorize_source_map_extension_count"] == 0),
        ("no_application_allowed", summary["delegated_application_allowed_count"] == 0),
        ("application_not_ready", summary["source_map_extension_application_ready"] is False),
        ("post_delegation_threshold_not_met", summary["post_delegation_blocked_audit_threshold_met"] is False),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_outside_scope_delegated_decision_readiness_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "readiness_recheck_count": len(rows),
        "readiness_recheck_pass_count": pass_count,
        "readiness_recheck_fail_count": len(rows) - pass_count,
        "decision": DECISION,
        "checks": rows,
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_outside_scope_delegated_decision_readiness_go_no_go.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "delegated_decision_record_count": summary["delegated_decision_record_count"],
        "delegated_keep_pending_decision_count": summary["delegated_keep_pending_decision_count"],
        "delegated_authorize_source_map_extension_count": summary["delegated_authorize_source_map_extension_count"],
        "valid_authorized_extension_record_count": summary["valid_authorized_extension_record_count"],
        "source_map_extension_application_ready": summary["source_map_extension_application_ready"],
        "post_delegation_blocker_observation_count": summary["post_delegation_blocker_observation_count"],
        "post_delegation_blocked_audit_threshold_met": summary["post_delegation_blocked_audit_threshold_met"],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "raw_to_processed_value_comparison_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    report = f"""# V014 Outside-Scope Delegated Decision Readiness Recheck

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- delegated decision records: `{summary["delegated_decision_record_count"]}`
- delegated keep-pending decisions: `{summary["delegated_keep_pending_decision_count"]}`
- delegated authorization decisions: `{summary["delegated_authorize_source_map_extension_count"]}`
- application allowed decisions: `{summary["delegated_application_allowed_count"]}`
- source-map application ready: `false`
- post-delegation blocker observation count: `{summary["post_delegation_blocker_observation_count"]}`
- blocked audit threshold met: `false`

The delegated response remains conservative. It does not provide authoritative evidence for source-map extension application, so downstream comparison and release gates stay closed.
"""
    go_no_go_record = f"""# Go / No-Go

- decision: `{go_no_go["decision"]}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- next required input: `{NEXT_REQUIRED_INPUT}`
- source-map application ready: `false`
- full comparison complete: `false`
- GitHub upload performed: `false`
- app reinstall performed: `false`
"""
    test_results = f"""# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck`

Current generated check matrix: `{matrix["readiness_recheck_pass_count"]}` pass / `{matrix["readiness_recheck_fail_count"]}` fail.
"""
    risk_register = """# Risk Register

- R1: A readiness recheck could be mistaken for application approval.
- R2: Delegated KEEP_PENDING is not source-map authorization.
- R3: Release, upload, reinstall and business execution remain blocked.
"""
    rollback_plan = """# Rollback Plan

No raw inbox, prior private decision record, prior private decision queue, source-map, materialization, reconciliation or authorization file was mutated. To roll back, remove this phase's public artifacts, metadata copies, private diagnostic, tool, validator, focused test and governance entries.
"""
    for path, text in (
        (REPORT_PATH, report),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (TEST_RESULTS_PATH, test_results),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback_plan),
    ):
        _write_text(path, text)


def _append_development_event(manifest: dict[str, Any]) -> None:
    summary = manifest["summary"]
    event_id = "DEV-KMFA-20260706-V014-OUTSIDE-SCOPE-DELEGATED-DECISION-READINESS-RECHECK"
    event = {
        "event_id": event_id,
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260706-KMFA-V014-OUTSIDE-SCOPE-DELEGATED-DECISION-READINESS-RECHECK",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "delegated_decision_record_count": summary["delegated_decision_record_count"],
        "delegated_keep_pending_decision_count": summary["delegated_keep_pending_decision_count"],
        "delegated_authorize_source_map_extension_count": summary["delegated_authorize_source_map_extension_count"],
        "source_map_extension_application_ready": False,
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed": False,
        "processed_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": "Rechecked delegated outside-scope source-map extension decisions and kept application blocked.",
        "result_commit": "PENDING",
        "files_changed": GOVERNANCE_FILES_CHANGED
        + [
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            "KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py",
            "KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py",
            "KMFA/tools/v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py",
        ],
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    retained_lines: list[str] = []
    if DEVELOPMENT_EVENTS_PATH.exists():
        for line in DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                existing = json.loads(line)
            except json.JSONDecodeError:
                retained_lines.append(line)
                continue
            if not isinstance(existing, dict) or existing.get("event_id") != event_id:
                retained_lines.append(line)
    retained_lines.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(retained_lines) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    prior_summary = _read_json(PRIOR_SUMMARY_PATH)
    prior_private_record = _read_json(PRIOR_PRIVATE_DECISION_RECORD_PATH)
    queue_rows = _read_jsonl(PRIOR_PRIVATE_DECISION_QUEUE_PATH)
    summary = _build_summary(
        generated_at=timestamp,
        prior_summary=prior_summary,
        prior_private_record=prior_private_record,
        queue_rows=queue_rows,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = {
        "schema_version": "kmfa.v014_outside_scope_delegated_decision_readiness_recheck_manifest.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_artifacts": [
            "public:delegated_keep_pending_decision_summary",
            "private:delegated_keep_pending_decision_record",
            "private:delegated_keep_pending_decision_queue",
        ],
        "public_artifact_refs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
        ],
        "metadata_artifact_refs": [
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "private_artifact_refs": ["private:delegated_decision_readiness_recheck_diagnostic"],
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
            "KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py "
            "--require-private-diagnostic"
        ),
        "summary": summary,
        "go_no_go_report": go_no_go,
        "matrix": matrix,
        "git": {
            "head": _git_output(["rev-parse", "HEAD"]),
            "branch": _git_output(["branch", "--show-current"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_outside_scope_delegated_decision_readiness_recheck.v1",
        "classification": "private_delegated_decision_readiness_recheck_diagnostic_do_not_commit",
        "record_type": "v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "summary": summary,
        "private_input_counts": _decision_counts(queue_rows),
    }

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
        (PRIVATE_DIAGNOSTIC_PATH, diagnostic),
    ):
        _write_json(path, payload)
    _write_human_artifacts(summary, matrix, go_no_go)
    if write_governance_event:
        _append_development_event(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope delegated decision readiness rechecked "
        f"(decision_records={summary['delegated_decision_record_count']}, "
        f"keep_pending={summary['delegated_keep_pending_decision_count']}, "
        f"application_ready={summary['source_map_extension_application_ready']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
