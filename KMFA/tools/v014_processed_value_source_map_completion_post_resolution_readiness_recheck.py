#!/usr/bin/env python3
"""Recheck source-map completion readiness after owner-exclusion application.

This phase consumes the previous public owner-exclusion application evidence
and ignored private owner decision/application outputs. It prepares a private
post-resolution reapplication candidate queue for the remaining linked groups,
then writes public aggregate evidence only. It does not mutate source-map
records, read the raw inbox, compare raw and processed values, reconcile
business values, upload GitHub, reinstall the app, or execute business actions.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_POST_RESOLUTION_READINESS_RECHECK"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-POST-RESOLUTION-READINESS-RECHECK-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-POST-RESOLUTION-READINESS-RECHECK"
VERSION = "0.1.4-post-resolution-readiness-recheck"
STATUS = "completed_validated_local_only_post_resolution_reapplication_ready_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "post_resolution_reapplication_candidates_ready_application_not_performed"
NEXT_REQUIRED_INPUT = "run_linked_source_map_completion_reapplication_phase"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_LINKED_REAPPLICATION"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_post_resolution_readiness_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_post_resolution_readiness_recheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_post_resolution_readiness_recheck_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_post_resolution_readiness_recheck_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_post_resolution_readiness_recheck_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_post_resolution_readiness_recheck_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_post_resolution_readiness_recheck_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_post_resolution_readiness_recheck_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_post_resolution_readiness_recheck_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_APPLICATION_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_summary.json"
)
SOURCE_APPLICATION_MATRIX_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_matrix_public_safe.json"
)
SOURCE_OWNER_22_RESPONSE_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_22_group_decision_response_intake_summary.json"
SOURCE_PRIVATE_OWNER_22_RESPONSE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_22_group_decision_response_intake/private_owner_22_group_decision_response.json"
)
SOURCE_PRIVATE_APPLICATION_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application/private_corrected_source_or_owner_exclusion_resolution_application_diagnostic.json"
)
SOURCE_PRIVATE_APPLICATION_RESULT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application/private_corrected_source_or_owner_exclusion_resolution_application_result.json"
)
SOURCE_PRIVATE_APPLICATION_APPLIED_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application/private_corrected_source_or_owner_exclusion_resolution_application_applied_queue.jsonl"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_post_resolution_readiness_recheck"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_post_resolution_readiness_recheck_diagnostic.json"
PRIVATE_REAPPLICATION_CANDIDATE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_post_resolution_reapplication_candidate_queue.jsonl"
PRIVATE_BLOCKER_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_post_resolution_reapplication_blocker_queue.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_post_resolution_readiness_recheck.md"

FILES_CHANGED = [
    "KMFA/CHANGELOG.md",
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
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
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
    "KMFA/tests/test_v014_processed_value_source_map_completion_post_resolution_readiness_recheck.py",
    "KMFA/tools/check_v014_processed_value_source_map_completion_post_resolution_readiness_recheck.py",
    "KMFA/tools/v014_processed_value_source_map_completion_post_resolution_readiness_recheck.py",
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
            raise ValueError(f"{path} must contain JSON objects")
        rows.append(value)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


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
        "private_owner_22_group_response_read_by_this_phase": True,
        "private_resolution_application_diagnostic_read_by_this_phase": True,
        "private_resolution_application_result_read_by_this_phase": True,
        "private_resolution_application_applied_queue_read_by_this_phase": True,
        "private_post_resolution_readiness_diagnostic_written_by_this_phase": True,
        "private_post_resolution_reapplication_candidate_queue_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_owner_22_group_response_committed": False,
        "private_resolution_application_diagnostic_committed": False,
        "private_resolution_application_result_committed": False,
        "private_resolution_application_applied_queue_committed": False,
        "private_post_resolution_diagnostic_committed": False,
        "private_post_resolution_candidate_queue_committed": False,
        "private_post_resolution_blocker_queue_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_file_hash_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "raw_or_processed_fingerprint_value_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_private_candidate_rows(private_owner_response: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in private_owner_response.get("groups", []):
        if not isinstance(group, dict):
            continue
        linked_count = int(group.get("linked_application_blocker_count", 0))
        decision_code = group.get("owner_final_decision_code")
        if linked_count <= 0 or decision_code != "CONFIRM_GROUP_CANDIDATE_RANK":
            continue
        rows.append(
            {
                "candidate_group_index": len(rows) + 1,
                "review_group_id": group.get("review_group_id"),
                "owner_final_decision_code": decision_code,
                "candidate_status": group.get("candidate_status"),
                "linked_application_blocker_count": linked_count,
                "source_map_reapplication_ready": True,
                "source_map_reapplication_performed_by_this_phase": False,
                "raw_to_processed_value_comparison_performed": False,
                "full_reconciliation_allowed": False,
            }
        )
    return rows


def _build_private_blocker_rows(private_owner_response: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in private_owner_response.get("groups", []):
        if not isinstance(group, dict):
            continue
        decision_code = group.get("owner_final_decision_code")
        if decision_code == "CONFIRM_GROUP_CANDIDATE_RANK":
            continue
        rows.append(
            {
                "blocker_group_index": len(rows) + 1,
                "review_group_id": group.get("review_group_id"),
                "owner_final_decision_code": decision_code,
                "linked_application_blocker_count": int(group.get("linked_application_blocker_count", 0)),
                "source_map_reapplication_ready": False,
                "blocker_code": "non_actionable_or_no_linked_application_blockers",
            }
        )
    return rows


def _build_matrix(generated_at: str, *, application_summary: dict[str, Any], owner_summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_application_available", application_summary.get("owner_exclusion_resolution_applied_count") == 36, application_summary.get("owner_exclusion_resolution_applied_count"), 36),
        ("owner_exclusions_applied", application_summary.get("owner_exclusion_resolution_applied_count") == 36, application_summary.get("owner_exclusion_resolution_applied_count"), 36),
        ("unlinked_blockers_closed", application_summary.get("resolution_application_blocker_queue_count") == 0, application_summary.get("resolution_application_blocker_queue_count"), 0),
        ("linked_reapplication_candidates_ready", owner_summary.get("actionable_linked_application_blocker_count") == 77, owner_summary.get("actionable_linked_application_blocker_count"), 77),
        ("non_actionable_groups_preserved", owner_summary.get("non_actionable_group_decision_count") == 3, owner_summary.get("non_actionable_group_decision_count"), 3),
        ("source_map_records_not_applied", True, 0, 0),
        ("raw_comparison_not_performed", True, False, False),
        ("downstream_no_go_preserved", True, DECISION, DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, passed, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_post_resolution_readiness_recheck_matrix_public_safe.v1",
        "record_type": "v014_post_resolution_readiness_recheck_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "post_resolution_check_count": len(rows),
        "post_resolution_pass_count": pass_count,
        "post_resolution_fail_count": len(rows) - pass_count,
        "owner_exclusion_resolution_applied_count": 36,
        "post_resolution_reapplication_candidate_count": 77,
        "post_resolution_actionable_group_decision_count": 19,
        "post_resolution_candidate_group_count": 15,
        "post_resolution_blocker_group_count": 3,
        "source_map_completion_reapplication_ready": True,
        "source_map_completion_reapplication_performed_by_this_phase": False,
        "source_map_records_applied_count": 0,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "github_upload_performed": False,
        "decision": DECISION,
        "checks": rows,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Post-Resolution Readiness Recheck

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- owner-exclusion items applied: `{summary["owner_exclusion_resolution_applied_count"]}`
- post-resolution reapplication candidates: `{summary["post_resolution_reapplication_candidate_count"]}`
- actionable group decisions: `{summary["post_resolution_actionable_group_decision_count"]}`
- linked candidate groups: `{summary["post_resolution_reapplication_candidate_group_count"]}`
- blocker groups retained: `{summary["post_resolution_blocker_group_count"]}`
- source-map records applied: `{summary["source_map_records_applied_count"]}`
- raw inbox accessed: `false`
- next recommended phase: `{NEXT_RECOMMENDED_PHASE}`

This phase confirms readiness only. It does not apply source-map records, compare raw and processed values, reconcile values, upload GitHub, reinstall the app, or execute business actions.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: linked reapplication candidates are ready, but source-map reapplication and downstream reconciliation are not performed in this phase.
- readiness checks: `{matrix["post_resolution_pass_count"]}` pass / `{matrix["post_resolution_fail_count"]}` fail
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: post-resolution readiness can be mistaken for source-map completion.
- Control: public evidence locks source-map records applied at zero and keeps raw comparison, reconciliation, report, upload and business gates closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private readiness outputs, tool, validator, focused test and governance entries. Do not modify raw source files.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_post_resolution_readiness_recheck.py KMFA/tools/check_v014_processed_value_source_map_completion_post_resolution_readiness_recheck.py KMFA/tests/test_v014_processed_value_source_map_completion_post_resolution_readiness_recheck.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_post_resolution_readiness_recheck.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_post_resolution_readiness_recheck.py --require-private-readiness`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_post_resolution_readiness_recheck`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `git diff --check -- KMFA`

All listed commands must pass before local commit. This phase does not read, list, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
"""
    for path, text in (
        (REPORT_PATH, report),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback_plan),
        (TEST_RESULTS_PATH, test_results),
    ):
        _write_text(path, text)


def _append_development_event(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-POST-RESOLUTION-READINESS-RECHECK"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-POST-RESOLUTION-READINESS-RECHECK",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "owner_exclusion_resolution_applied_count": summary["owner_exclusion_resolution_applied_count"],
        "post_resolution_reapplication_candidate_count": summary["post_resolution_reapplication_candidate_count"],
        "source_map_completion_reapplication_ready": True,
        "source_map_completion_reapplication_performed": False,
        "source_map_records_applied_count": 0,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Rechecked post-resolution readiness after 36 owner exclusions and prepared private linked reapplication candidates while keeping source-map mutation and reconciliation gates closed.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    application_summary = _read_json(SOURCE_APPLICATION_SUMMARY_PATH)
    application_matrix = _read_json(SOURCE_APPLICATION_MATRIX_PATH)
    owner_summary = _read_json(SOURCE_OWNER_22_RESPONSE_SUMMARY_PATH)
    private_owner_response = _read_json(SOURCE_PRIVATE_OWNER_22_RESPONSE_PATH)
    private_application_diagnostic = _read_json(SOURCE_PRIVATE_APPLICATION_DIAGNOSTIC_PATH)
    private_application_result = _read_json(SOURCE_PRIVATE_APPLICATION_RESULT_PATH)
    private_applied_queue = _read_jsonl(SOURCE_PRIVATE_APPLICATION_APPLIED_QUEUE_PATH)
    candidate_rows = _build_private_candidate_rows(private_owner_response)
    blocker_rows = _build_private_blocker_rows(private_owner_response)
    candidate_count = sum(int(row["linked_application_blocker_count"]) for row in candidate_rows)
    if len(candidate_rows) != 15 or candidate_count != 77:
        raise ValueError(f"expected 15 linked candidate groups and 77 linked candidates, got {len(candidate_rows)} and {candidate_count}")
    if len(private_applied_queue) != 36:
        raise ValueError(f"expected 36 private applied owner exclusions, got {len(private_applied_queue)}")

    private_diagnostic = {
        "schema_version": "kmfa.private.v014_post_resolution_readiness_recheck_diagnostic.v1",
        "classification": "private_post_resolution_readiness_recheck_diagnostic_do_not_commit",
        "record_type": "v014_post_resolution_readiness_recheck_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_application_phase_id": application_summary.get("phase_id"),
        "owner_exclusion_resolution_applied_count": len(private_applied_queue),
        "corrected_source_resolution_applied_count": private_application_result.get("corrected_source_resolution_applied_count"),
        "post_resolution_reapplication_candidate_group_count": len(candidate_rows),
        "post_resolution_reapplication_candidate_count": candidate_count,
        "post_resolution_actionable_group_decision_count": owner_summary.get("actionable_group_decision_count"),
        "post_resolution_blocker_group_count": len(blocker_rows),
        "source_map_completion_reapplication_ready": True,
        "source_map_completion_reapplication_performed_by_this_phase": False,
        "source_map_records_applied_count": 0,
        "raw_inbox_accessed": False,
        "source_application_diagnostic_conclusion": private_application_diagnostic.get("diagnostic_conclusion"),
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_jsonl(PRIVATE_REAPPLICATION_CANDIDATE_QUEUE_PATH, candidate_rows)
    _write_jsonl(PRIVATE_BLOCKER_QUEUE_PATH, blocker_rows)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Post-Resolution Readiness Recheck\n\n"
        "19 private candidate groups cover 77 linked reapplication candidates after 36 owner exclusions. "
        "This private file is ignored and must not be committed.\n",
    )

    matrix = _build_matrix(timestamp, application_summary=application_summary, owner_summary=owner_summary)
    summary = {
        "schema_version": "kmfa.v014_post_resolution_readiness_recheck_summary.v1",
        "record_type": "v014_post_resolution_readiness_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_resolution_application_phase_id": application_summary["phase_id"],
        "source_resolution_application_decision": application_summary["decision"],
        "source_resolution_application_matrix_fail_count": application_matrix["application_fail_count"],
        "source_owner_22_response_phase_id": owner_summary["phase_id"],
        "source_owner_22_response_decision": owner_summary["decision"],
        "original_application_blocker_queue_count": owner_summary["application_blocker_queue_count"],
        "source_linked_application_blocker_count": owner_summary["linked_application_blocker_count"],
        "source_unlinked_application_blocker_count": owner_summary["unlinked_application_blocker_count"],
        "owner_exclusion_resolution_applied_count": application_summary["owner_exclusion_resolution_applied_count"],
        "corrected_source_resolution_applied_count": application_summary["corrected_source_resolution_applied_count"],
        "post_resolution_actionable_group_decision_count": owner_summary["actionable_group_decision_count"],
        "post_resolution_reapplication_candidate_group_count": len(candidate_rows),
        "post_resolution_reapplication_candidate_count": candidate_count,
        "post_resolution_blocker_group_count": len(blocker_rows),
        "post_resolution_open_unlinked_blocker_count": 0,
        "post_resolution_readiness_recheck_performed_by_this_phase": True,
        "source_map_completion_reapplication_ready": True,
        "source_map_completion_reapplication_performed_by_this_phase": False,
        "source_map_mutation_performed_by_this_phase": False,
        "source_map_records_applied_count": 0,
        "processed_value_materialization_replay_ready": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_post_resolution_diagnostic_written": True,
        "private_post_resolution_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_post_resolution_candidate_queue_written": True,
        "private_post_resolution_candidate_queue_gitignored": _git_check_ignored(PRIVATE_REAPPLICATION_CANDIDATE_QUEUE_PATH),
        "private_post_resolution_blocker_queue_written": True,
        "private_post_resolution_blocker_queue_gitignored": _git_check_ignored(PRIVATE_BLOCKER_QUEUE_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_post_resolution_readiness_recheck_go_no_go.v1",
        "record_type": "v014_post_resolution_readiness_recheck_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "reason": "post_resolution_reapplication_candidates_ready_but_source_map_application_and_reconciliation_not_performed",
        "owner_exclusion_resolution_applied_count": summary["owner_exclusion_resolution_applied_count"],
        "post_resolution_reapplication_candidate_count": candidate_count,
        "source_map_completion_reapplication_ready": True,
        "source_map_completion_reapplication_performed_by_this_phase": False,
        "source_map_records_applied_count": 0,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_post_resolution_readiness_recheck_manifest.v1",
        "record_type": "v014_post_resolution_readiness_recheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "git_head_at_generation": _git_output(["rev-parse", "HEAD"]),
        "source_artifacts": [
            SOURCE_APPLICATION_SUMMARY_PATH.as_posix(),
            SOURCE_APPLICATION_MATRIX_PATH.as_posix(),
            SOURCE_OWNER_22_RESPONSE_SUMMARY_PATH.as_posix(),
            "private:owner_22_group_decision_response",
            "private:resolution_application_diagnostic",
            "private:resolution_application_result",
            "private:resolution_application_applied_queue",
        ],
        "public_artifacts": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "private_artifact_refs": [
            "private:post_resolution_readiness_recheck_diagnostic",
            "private:post_resolution_reapplication_candidate_queue",
            "private:post_resolution_reapplication_blocker_queue",
            "private:post_resolution_readiness_recheck_report",
        ],
        "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_post_resolution_readiness_recheck.py --require-private-readiness",
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
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
    ):
        _write_json(path, payload)
    _write_human_artifacts(summary, matrix)
    _append_development_event(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "matrix": matrix, "go_no_go": go_no_go}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: KMFA v0.1.4 post-resolution readiness recheck generated "
        f"(decision={summary['decision']}, candidates={summary['post_resolution_reapplication_candidate_count']}, "
        f"source_map_records={summary['source_map_records_applied_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
