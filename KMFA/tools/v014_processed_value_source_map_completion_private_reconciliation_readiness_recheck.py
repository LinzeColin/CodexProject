#!/usr/bin/env python3
"""Recheck private full-reconciliation readiness for KMFA v0.1.4.

This phase consumes the prior private blocker-resolution decision intake and
records whether full raw-to-processed reconciliation may start. It does not
read the raw inbox, does not apply resolutions, and does not compare raw and
processed values.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_RECONCILIATION_READINESS_RECHECK"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-RECONCILIATION-READINESS-RECHECK-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-RECONCILIATION-READINESS-RECHECK"
VERSION = "0.1.4-private-reconciliation-readiness-recheck"
STATUS = "completed_validated_local_only_private_reconciliation_readiness_recheck_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_full_reconciliation_not_ready_resolution_decisions_still_blocked"
PREVIOUS_REQUIRED_INPUT = "corrected_private_source_or_owner_approved_resolution_before_full_reconciliation"
NEXT_RECOMMENDED_ACTION = "provide_corrected_private_source_or_owner_approved_resolution_then_rerun_readiness_recheck"
NEXT_REQUIRED_INPUT = "corrected_private_source_or_owner_approved_resolution_before_full_reconciliation"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_reconciliation_readiness_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_reconciliation_readiness_recheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_reconciliation_readiness_recheck_go_no_go_report.json"
READINESS_MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_reconciliation_readiness_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_private_reconciliation_readiness_recheck.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_reconciliation_readiness_recheck_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_private_reconciliation_readiness_recheck_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_private_reconciliation_readiness_recheck_go_no_go_report.json"
METADATA_READINESS_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_private_reconciliation_readiness_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_decision_intake_summary.json"
SOURCE_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_decision_intake_go_no_go_report.json"
SOURCE_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_decision_matrix_public_safe.json"
SOURCE_MISMATCH_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_mismatch_and_blocker_report_summary.json"
SOURCE_DRY_RUN_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_raw_value_matching_dry_run_summary.json"
SOURCE_PRIVATE_DECISION_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake/private_blocker_resolution_decision_queue.jsonl"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_private_reconciliation_readiness_recheck"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_reconciliation_readiness_recheck_diagnostic.json"
PRIVATE_QUEUE_STATUS_PATH = PRIVATE_OUTPUT_DIR / "private_reconciliation_readiness_queue_status.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_reconciliation_readiness_recheck.md"


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
        "private_decision_intake_summary_read_by_this_phase": True,
        "private_decision_queue_read_by_this_phase": True,
        "private_reconciliation_readiness_diagnostic_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_decision_queue_committed": False,
        "private_readiness_diagnostic_committed": False,
        "private_queue_status_committed": False,
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


def _queue_counts(queue: list[dict[str, Any]]) -> dict[str, Any]:
    decision_counts = Counter(str(row.get("decision_code", "missing")) for row in queue)
    blocked_count = sum(count for code, count in decision_counts.items() if code.startswith("keep_blocked"))
    resolution_applied_count = sum(1 for row in queue if row.get("resolution_applied") is True)
    full_reconciliation_allowed_count = sum(1 for row in queue if row.get("full_reconciliation_allowed_after_decision") is True)
    return {
        "private_decision_queue_count": len(queue),
        "blocked_private_decision_count": blocked_count,
        "resolution_applied_private_decision_count": resolution_applied_count,
        "full_reconciliation_allowed_private_decision_count": full_reconciliation_allowed_count,
        "keep_blocked_pending_corrected_source_or_owner_exclusion_count": decision_counts[
            "keep_blocked_pending_corrected_source_or_owner_exclusion"
        ],
        "keep_blocked_pending_private_disambiguation_count": decision_counts["keep_blocked_pending_private_disambiguation"],
    }


def _readiness_matrix(generated_at: str, source_summary: dict[str, Any], queue_counts: dict[str, Any]) -> dict[str, Any]:
    checks = [
        {
            "check_code": "source_decision_intake_completed",
            "status": "PASS" if source_summary.get("blocker_resolution_decision_intake_performed") is True else "FAIL",
            "public_safe_observed_value": bool(source_summary.get("blocker_resolution_decision_intake_performed")),
            "required_value": True,
        },
        {
            "check_code": "source_decision_intake_go",
            "status": "FAIL" if source_summary.get("decision") != "GO" else "PASS",
            "public_safe_observed_value": source_summary.get("decision"),
            "required_value": "GO",
        },
        {
            "check_code": "corrected_private_source_provided",
            "status": "FAIL" if source_summary.get("corrected_private_source_provided") is not True else "PASS",
            "public_safe_observed_value": bool(source_summary.get("corrected_private_source_provided")),
            "required_value": True,
        },
        {
            "check_code": "owner_resolution_or_disambiguation_provided",
            "status": "FAIL" if source_summary.get("owner_exclusion_or_disambiguation_provided") is not True else "PASS",
            "public_safe_observed_value": bool(source_summary.get("owner_exclusion_or_disambiguation_provided")),
            "required_value": True,
        },
        {
            "check_code": "resolution_applied",
            "status": "FAIL" if int(source_summary.get("resolution_applied_decision_count", 0)) == 0 else "PASS",
            "public_safe_observed_value": int(source_summary.get("resolution_applied_decision_count", 0)),
            "required_value": "greater_than_zero_and_all_required_blockers_resolved",
        },
        {
            "check_code": "private_decision_queue_unblocked",
            "status": "FAIL" if queue_counts["blocked_private_decision_count"] else "PASS",
            "public_safe_observed_value": queue_counts["blocked_private_decision_count"],
            "required_value": 0,
        },
        {
            "check_code": "private_queue_allows_full_reconciliation",
            "status": "FAIL" if queue_counts["full_reconciliation_allowed_private_decision_count"] == 0 else "PASS",
            "public_safe_observed_value": queue_counts["full_reconciliation_allowed_private_decision_count"],
            "required_value": "all_required_private_decisions_allow_full_reconciliation",
        },
        {
            "check_code": "confirmed_value_mismatch_absent",
            "status": "PASS" if int(source_summary.get("confirmed_value_mismatch_count", 0)) == 0 else "FAIL",
            "public_safe_observed_value": int(source_summary.get("confirmed_value_mismatch_count", 0)),
            "required_value": 0,
        },
    ]
    pass_count = sum(1 for row in checks if row["status"] == "PASS")
    fail_count = sum(1 for row in checks if row["status"] == "FAIL")
    return {
        "schema_version": "kmfa.v014_private_reconciliation_readiness_matrix_public_safe.v1",
        "record_type": "v014_processed_value_source_map_completion_private_reconciliation_readiness_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "readiness_check_count": len(checks),
        "readiness_pass_count": pass_count,
        "readiness_fail_count": fail_count,
        "full_reconciliation_ready": fail_count == 0,
        "full_reconciliation_allowed": False,
        "checks": checks,
        "decision": DECISION,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 private reconciliation readiness recheck",
                "",
                f"- Phase: `{PHASE_ID}`",
                f"- Decision: `{summary['decision']}`",
                f"- Readiness checks: `{matrix['readiness_pass_count']}` pass / `{matrix['readiness_fail_count']}` fail",
                f"- Private decision queue: `{summary['private_decision_queue_count']}` records, `{summary['blocked_private_decision_count']}` still blocked",
                f"- Resolution applied: `{summary['resolution_applied_decision_count']}`",
                f"- Full reconciliation performed: `{summary['full_raw_to_processed_reconciliation_performed_by_this_phase']}`",
                f"- Business value consistency verified: `{summary['business_value_consistency_verified']}`",
                "",
                "Result: full reconciliation remains blocked until corrected private source or owner-approved resolution is supplied.",
            ]
        )
        + "\n",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go/No-Go",
                "",
                f"- Decision: `{DECISION}`",
                f"- Blocked until: `{NEXT_REQUIRED_INPUT}`",
                "- GitHub upload: `false`",
                "- App reinstall: `false`",
                "- Business execution: `false`",
            ]
        )
        + "\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# Test Results",
                "",
                "- Planned validator: `python3 KMFA/tools/check_v014_processed_value_source_map_completion_private_reconciliation_readiness_recheck.py --require-private-diagnostic`",
                "- Planned focused test: `python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_private_reconciliation_readiness_recheck`",
                "- Planned governance validators: `scripts/lean_governance.py` and `scripts/validate_project_governance.py`",
                "- Raw inbox access: `false`",
            ]
        )
        + "\n",
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# Risk Register",
                "",
                "- R1: Full reconciliation is blocked because private resolution decisions are still blocked.",
                "- R2: Confirmed mismatch count is zero, but this does not prove business value consistency.",
                "- R3: Any future corrected source must stay private until converted to public-safe aggregate evidence.",
            ]
        )
        + "\n",
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# Rollback Plan",
                "",
                "- Remove this phase's public artifacts and metadata copies.",
                "- Remove ignored private diagnostic files under the phase runtime directory.",
                "- Re-run the previous decision-intake validator before retrying readiness recheck.",
            ]
        )
        + "\n",
    )


def _write_private_artifacts(summary: dict[str, Any], queue_counts: dict[str, Any], matrix: dict[str, Any]) -> None:
    diagnostic = {
        "schema_version": "kmfa.private.v014_private_reconciliation_readiness_recheck.v1",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_decision_queue_count": queue_counts["private_decision_queue_count"],
        "blocked_private_decision_count": queue_counts["blocked_private_decision_count"],
        "resolution_applied_private_decision_count": queue_counts["resolution_applied_private_decision_count"],
        "full_reconciliation_allowed_private_decision_count": queue_counts[
            "full_reconciliation_allowed_private_decision_count"
        ],
        "readiness_fail_count": matrix["readiness_fail_count"],
        "full_reconciliation_ready": False,
        "raw_inbox_accessed": False,
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_json(PRIVATE_QUEUE_STATUS_PATH, queue_counts)
    _write_text(
        PRIVATE_REPORT_PATH,
        "Private reconciliation readiness remains blocked; no row-level source value is required in this public phase.\n",
    )
    summary["private_diagnostic_written"] = True
    summary["private_queue_status_written"] = True
    summary["private_diagnostic_gitignored"] = _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH)
    summary["private_queue_status_gitignored"] = _git_check_ignored(PRIVATE_QUEUE_STATUS_PATH)


def _write_governance_event(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-PRIVATE-RECONCILIATION-READINESS-RECHECK"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PRIVATE-RECONCILIATION-READINESS-RECHECK",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "private_decision_queue_count": summary["private_decision_queue_count"],
        "blocked_private_decision_count": summary["blocked_private_decision_count"],
        "resolution_applied_decision_count": summary["resolution_applied_decision_count"],
        "full_raw_to_processed_reconciliation_performed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Rechecked private reconciliation readiness and kept full reconciliation blocked.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    source_go_no_go = _read_json(SOURCE_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_MATRIX_PATH)
    mismatch_summary = _read_json(SOURCE_MISMATCH_SUMMARY_PATH)
    dry_run_summary = _read_json(SOURCE_DRY_RUN_SUMMARY_PATH)
    private_queue = _read_jsonl(SOURCE_PRIVATE_DECISION_QUEUE_PATH)
    queue_counts = _queue_counts(private_queue)
    readiness_matrix = _readiness_matrix(timestamp, source_summary, queue_counts)

    summary = {
        "schema_version": "kmfa.v014_private_reconciliation_readiness_recheck_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_private_reconciliation_readiness_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_phase_id": source_summary["phase_id"],
        "source_decision": source_summary["decision"],
        "source_go_no_go_decision": source_go_no_go["decision"],
        "source_readiness_fail_count": readiness_matrix["readiness_fail_count"],
        "source_decision_track_count": source_matrix["decision_track_count"],
        "source_keep_blocked_decision_count": source_matrix["keep_blocked_decision_count"],
        "decision_track_count": source_summary["decision_track_count"],
        "keep_blocked_decision_count": source_summary["keep_blocked_decision_count"],
        "resolution_applied_decision_count": source_summary["resolution_applied_decision_count"],
        "corrected_private_source_provided": source_summary.get("corrected_private_source_provided", False),
        "owner_exclusion_or_disambiguation_provided": source_summary.get(
            "owner_exclusion_or_disambiguation_provided", False
        ),
        "private_resolution_queue_count": source_summary["private_resolution_queue_count"],
        **queue_counts,
        "dry_run_matched_target_count": dry_run_summary["dry_run_matched_target_count"],
        "dry_run_unmatched_target_count": dry_run_summary["dry_run_unmatched_target_count"],
        "dry_run_ambiguous_raw_match_target_count": dry_run_summary["dry_run_ambiguous_raw_match_target_count"],
        "confirmed_value_mismatch_count": mismatch_summary["confirmed_value_mismatch_count"],
        "confirmed_mismatch_report_required_now": mismatch_summary["confirmed_mismatch_report_required_now"],
        "repeated_cross_validation_mismatch_confirmed": False,
        "full_reconciliation_ready": False,
        "full_reconciliation_allowed": False,
        "full_raw_to_processed_reconciliation_performed_by_this_phase": False,
        "full_raw_to_processed_reconciliation_complete": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "processed_data_reconciliation_performed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "previous_required_input": PREVIOUS_REQUIRED_INPUT,
        "previous_required_input_resolved_by_this_phase": False,
        "next_recommended_action": NEXT_RECOMMENDED_ACTION,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    _write_private_artifacts(summary, queue_counts, readiness_matrix)

    go_no_go = {
        "schema_version": "kmfa.v014_private_reconciliation_readiness_recheck_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_private_reconciliation_readiness_recheck_go_no_go",
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
        "private_decision_queue_count": summary["private_decision_queue_count"],
        "blocked_private_decision_count": summary["blocked_private_decision_count"],
        "resolution_applied_decision_count": summary["resolution_applied_decision_count"],
        "full_reconciliation_ready": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_private_reconciliation_readiness_recheck_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_private_reconciliation_readiness_recheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "summary": summary,
        "go_no_go": go_no_go,
        "readiness_matrix": readiness_matrix,
        "public_artifacts": [path.as_posix() for path in (SUMMARY_PATH, MANIFEST_PATH, GO_NO_GO_PATH, READINESS_MATRIX_PATH)],
        "private_artifacts_gitignored": True,
    }

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (READINESS_MATRIX_PATH, readiness_matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_READINESS_MATRIX_PATH, readiness_matrix),
    ):
        _write_json(path, payload)
    _write_human_artifacts(summary, readiness_matrix)
    _write_governance_event(timestamp, summary)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    print(
        "PASS: KMFA v0.1.4 private reconciliation readiness recheck generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"blocked={manifest['summary']['blocked_private_decision_count']}, "
        f"ready={manifest['summary']['full_reconciliation_ready']})"
    )


if __name__ == "__main__":
    main()
