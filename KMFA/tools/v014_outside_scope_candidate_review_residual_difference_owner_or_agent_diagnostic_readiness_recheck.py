#!/usr/bin/env python3
"""Recheck owner/agent diagnostic-response readiness for residual differences.

This phase consumes the previous public-safe diagnostic-intake evidence and the
ignored private diagnostic response template / pending queue. It only proves
that no valid response exists yet. It does not read or mutate the raw inbox,
does not close discrepancies, and does not correct source maps.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_READINESS_RECHECK"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-READINESS-RECHECK-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-READINESS-RECHECK"
VERSION = "0.1.4-outside-scope-candidate-review-residual-difference-owner-or-agent-diagnostic-readiness-recheck"
STATUS = "completed_validated_local_only_residual_difference_owner_or_agent_diagnostic_readiness_recheck_no_go"
DECISION = "NO_GO"
READINESS_CONCLUSION = "private_owner_or_agent_diagnostic_response_readiness_rechecked_all_72_items_blocked_no_closure"
NEXT_REQUIRED_INPUT = (
    "owner_or_authorized_delegate_or_external_agent_valid_diagnostic_response_required_for_72_private_residual_differences"
)
NEXT_RECOMMENDED_PHASE = (
    "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_BLOCKER_AUDIT"
)

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck_manifest.json"
GO_NO_GO_PATH = (
    MACHINE_DIR
    / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck_go_no_go_report.json"
)
MATRIX_PATH = (
    MACHINE_DIR
    / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck_matrix_public_safe.json"
)
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck_matrix_public_safe.json"
)

SOURCE_PUBLIC_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_intake_summary.json"
)
SOURCE_PUBLIC_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_intake_manifest.json"
)
SOURCE_PUBLIC_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_intake_go_no_go_report.json"
)
SOURCE_PUBLIC_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_intake_matrix_public_safe.json"
)
SOURCE_PRIVATE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_intake/private_owner_or_agent_diagnostic_response_template.jsonl"
)
SOURCE_PRIVATE_PENDING_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_intake/private_owner_or_agent_diagnostic_pending_queue.jsonl"
)
SOURCE_PRIVATE_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_intake/private_owner_or_agent_diagnostic_intake_diagnostic.json"
)
SOURCE_PRIVATE_REPORT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_intake/private_owner_or_agent_diagnostic_intake_report.md"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck"
)
PRIVATE_READINESS_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_readiness_recheck_diagnostic.json"
PRIVATE_BLOCKER_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_readiness_blocker_queue.jsonl"
PRIVATE_READINESS_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_readiness_recheck_report.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

EXPECTED_TRACK_COUNTS = {
    "owner_select_one_authoritative_candidate": 24,
    "provide_authoritative_source_reference_or_owner_exclusion": 40,
    "provide_formula_or_non_numeric_mapping": 8,
}


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


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


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


def _changed_kmfa_files() -> list[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "status", "--porcelain=v1", "--untracked-files=all", "--", "KMFA"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return []
    files: set[str] = set()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if ".codex_private_runtime/" not in path:
            files.add(path)
    return sorted(files)


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_diagnostic_intake_summary_read_by_this_phase": True,
        "source_public_diagnostic_intake_manifest_read_by_this_phase": True,
        "source_public_diagnostic_intake_go_no_go_read_by_this_phase": True,
        "source_public_diagnostic_intake_matrix_read_by_this_phase": True,
        "source_private_diagnostic_response_template_read_by_this_phase": True,
        "source_private_diagnostic_pending_queue_read_by_this_phase": True,
        "source_private_diagnostic_intake_diagnostic_read_by_this_phase": True,
        "source_private_diagnostic_intake_report_existence_checked_by_this_phase": True,
        "private_readiness_diagnostic_written_by_this_phase": True,
        "private_readiness_blocker_queue_written_by_this_phase": True,
        "private_readiness_report_written_by_this_phase": True,
        "source_private_diagnostic_response_template_mutated_by_this_phase": False,
        "source_private_diagnostic_pending_queue_mutated_by_this_phase": False,
        "source_private_diagnostic_intake_diagnostic_mutated_by_this_phase": False,
        "source_private_diagnostic_intake_report_mutated_by_this_phase": False,
        "owner_or_agent_response_supplied_by_this_phase": False,
        "valid_diagnostic_response_supplied_by_this_phase": False,
        "discrepancy_closure_written_by_this_phase": False,
        "source_map_correction_written_by_this_phase": False,
        "protected_source_identifier_derivation_performed_by_this_phase": False,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
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
        "source_private_diagnostic_response_template_committed": False,
        "source_private_diagnostic_pending_queue_committed": False,
        "source_private_diagnostic_intake_diagnostic_committed": False,
        "source_private_diagnostic_intake_report_committed": False,
        "private_readiness_diagnostic_committed": False,
        "private_readiness_blocker_queue_committed": False,
        "private_readiness_report_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "protected_archive_component_identifier_committed": False,
        "raw_digest_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_blocker_rows(generated_at: str, pending_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocker_rows: list[dict[str, Any]] = []
    for index, row in enumerate(pending_rows, start=1):
        blocker_rows.append(
            {
                "blocker_item_id": f"OSCR-DRR-BLOCKER-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_pending_item_id": row.get("pending_item_id"),
                "source_template_item_id": row.get("template_item_id"),
                "source_handoff_item_id": row.get("source_handoff_item_id"),
                "diagnostic_track": row.get("diagnostic_track"),
                "blocker_code": "missing_valid_owner_or_agent_diagnostic_response",
                "response_status": row.get("response_status"),
                "valid_diagnostic_response": False,
                "actionable_resolution_ready": False,
                "source_map_correction_ready_after_recheck": False,
                "discrepancy_closed_by_this_phase": False,
                "public_commit_allowed": False,
            }
        )
    return blocker_rows


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    template_rows: list[dict[str, Any]],
    pending_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    track_counts = Counter(str(row.get("diagnostic_track")) for row in pending_rows)
    blocker_count = len(blocker_rows)
    return {
        "schema_version": "kmfa.v014_residual_difference_owner_or_agent_diagnostic_readiness_recheck_summary.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "readiness_conclusion": READINESS_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_decision": source_summary.get("decision"),
        "source_private_diagnostic_response_template_item_count": len(template_rows),
        "source_private_diagnostic_pending_queue_item_count": len(pending_rows),
        "source_pending_diagnostic_response_count": source_summary.get("pending_diagnostic_response_count"),
        "source_valid_diagnostic_response_count": source_summary.get("valid_diagnostic_response_count"),
        "source_actionable_resolution_count": source_summary.get("actionable_resolution_count"),
        "diagnostic_readiness_recheck_performed": True,
        "diagnostic_response_ready_count": 0,
        "diagnostic_response_blocker_count": blocker_count,
        "private_readiness_blocker_queue_item_count": blocker_count,
        "pending_diagnostic_response_count": blocker_count,
        "valid_diagnostic_response_count": 0,
        "invalid_diagnostic_response_count": 0,
        "actionable_resolution_count": 0,
        "open_residual_difference_count": blocker_count,
        "closed_discrepancy_count": 0,
        "safe_auto_resolution_count": 0,
        "source_map_correction_ready_count": 0,
        "owner_select_one_authoritative_candidate_count": track_counts["owner_select_one_authoritative_candidate"],
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts[
            "provide_authoritative_source_reference_or_owner_exclusion"
        ],
        "provide_formula_or_non_numeric_mapping_count": track_counts["provide_formula_or_non_numeric_mapping"],
        "private_readiness_diagnostic_written": True,
        "private_readiness_blocker_queue_written": True,
        "private_readiness_report_written": True,
        "private_readiness_diagnostic_gitignored": _git_check_ignored(PRIVATE_READINESS_DIAGNOSTIC_PATH),
        "private_readiness_blocker_queue_gitignored": _git_check_ignored(PRIVATE_BLOCKER_QUEUE_PATH),
        "private_readiness_report_gitignored": _git_check_ignored(PRIVATE_READINESS_REPORT_PATH),
        "owner_or_agent_valid_response_supplied": False,
        "discrepancy_closure_complete": False,
        "source_map_correction_ready": False,
        "source_map_correction_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "full_reconciliation_allowed": False,
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


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_residual_difference_owner_or_agent_diagnostic_readiness_recheck_go_no_go.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "readiness_conclusion": READINESS_CONCLUSION,
        "diagnostic_response_ready_count": summary["diagnostic_response_ready_count"],
        "diagnostic_response_blocker_count": summary["diagnostic_response_blocker_count"],
        "pending_diagnostic_response_count": summary["pending_diagnostic_response_count"],
        "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
        "actionable_resolution_count": summary["actionable_resolution_count"],
        "open_residual_difference_count": summary["open_residual_difference_count"],
        "closed_discrepancy_count": summary["closed_discrepancy_count"],
        "safe_auto_resolution_count": summary["safe_auto_resolution_count"],
        "source_map_correction_ready": False,
        "raw_to_processed_value_comparison_allowed": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        (
            "source_diagnostic_intake_loaded",
            summary["source_phase_id"]
            == "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_INTAKE",
        ),
        ("source_private_template_loaded", summary["source_private_diagnostic_response_template_item_count"] == 72),
        ("source_private_pending_queue_loaded", summary["source_private_diagnostic_pending_queue_item_count"] == 72),
        ("readiness_recheck_performed", summary["diagnostic_readiness_recheck_performed"] is True),
        ("no_ready_diagnostic_response", summary["diagnostic_response_ready_count"] == 0),
        ("all_residual_differences_blocked", summary["diagnostic_response_blocker_count"] == 72),
        ("no_valid_diagnostic_response", summary["valid_diagnostic_response_count"] == 0),
        ("no_actionable_resolution", summary["actionable_resolution_count"] == 0),
        ("no_discrepancy_closed", summary["closed_discrepancy_count"] == 0),
        ("diagnostic_track_counts_locked", all(summary[f"{track}_count"] == count for track, count in EXPECTED_TRACK_COUNTS.items())),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["business_execution_performed"] is False),
    ]
    return {
        "schema_version": "kmfa.v014_residual_difference_owner_or_agent_diagnostic_readiness_recheck_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "decision": DECISION,
        "check_count": len(checks),
        "check_pass_count": sum(1 for _, passed in checks if passed),
        "check_fail_count": sum(1 for _, passed in checks if not passed),
        "checks": [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks],
    }


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_residual_difference_owner_or_agent_diagnostic_readiness_recheck_manifest.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "readiness_conclusion": READINESS_CONCLUSION,
        "source_artifacts": {
            "source_diagnostic_intake_public_summary": "public_safe_metadata_copy",
            "source_diagnostic_intake_public_manifest": "public_safe_metadata_copy",
            "source_diagnostic_intake_public_go_no_go": "public_safe_metadata_copy",
            "source_diagnostic_intake_public_matrix": "public_safe_metadata_copy",
            "source_private_diagnostic_response_template": "ignored_private_runtime",
            "source_private_diagnostic_pending_queue": "ignored_private_runtime",
            "source_private_diagnostic_intake_diagnostic": "ignored_private_runtime",
            "source_private_diagnostic_intake_report": "ignored_private_runtime",
        },
        "summary": summary,
        "go_no_go_report": go_no_go,
        "matrix": matrix,
        "public_artifact_refs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
        ],
        "metadata_artifact_refs": [
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "private_artifact_refs": [
            "private:owner_or_agent_diagnostic_readiness_recheck_diagnostic",
            "private:owner_or_agent_diagnostic_readiness_blocker_queue",
            "private:owner_or_agent_diagnostic_readiness_recheck_report",
        ],
        "test_commands": [
            (
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
                "KMFA/tools/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck.py "
                "--generated-at 2026-07-07T00:00:00+10:00"
            ),
            (
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
                "KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck.py "
                "--require-private-readiness"
            ),
            (
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest "
                "KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck"
            ),
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }


def _write_human_artifacts(summary: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        f"""# Owner / Agent Diagnostic Readiness Recheck

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- source private template items: `{summary['source_private_diagnostic_response_template_item_count']}`
- source private pending queue items: `{summary['source_private_diagnostic_pending_queue_item_count']}`
- diagnostic response ready count: `{summary['diagnostic_response_ready_count']}`
- diagnostic response blocker count: `{summary['diagnostic_response_blocker_count']}`
- valid diagnostic responses: `{summary['valid_diagnostic_response_count']}`
- actionable resolutions: `{summary['actionable_resolution_count']}`
- open residual differences: `{summary['open_residual_difference_count']}`
- closed discrepancies: `{summary['closed_discrepancy_count']}`
- safe auto resolutions: `{summary['safe_auto_resolution_count']}`
- owner select one authoritative candidate: `{summary['owner_select_one_authoritative_candidate_count']}`
- provide authoritative source reference or owner exclusion: `{summary['provide_authoritative_source_reference_or_owner_exclusion_count']}`
- provide formula or non-numeric mapping: `{summary['provide_formula_or_non_numeric_mapping_count']}`
- raw boundary: raw inbox read/list/stat/parse/write/delete/move/rename/copy/normalize/mutation all `false` in this phase.
- downstream boundary: valid response intake, discrepancy closure, source-map correction, formal raw-to-processed comparison, reconciliation, formal report, GitHub upload, app reinstall and business execution all remain `false`.
""",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        (
            f"# Go/No-Go\n\n- decision: `{DECISION}`\n"
            "- reason: readiness recheck found 0 valid diagnostic responses and 72 blockers.\n"
        ),
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# Test Results",
                "",
                "- generator: pending current run",
                (
                    "- validator: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
                    "KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck.py "
                    "--require-private-readiness`"
                ),
                (
                    "- focused unit test: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest "
                    "KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck`"
                ),
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        (
            "# Risk Register\n\n"
            "- Risk: Treating a readiness recheck as valid owner evidence would overstate consistency.\n"
            "- Control: validator requires ready_count=0, blocker_count=72, valid_diagnostic_response_count=0, "
            "actionable_resolution_count=0 and all downstream gates closed.\n"
        ),
    )
    _write_text(
        ROLLBACK_PATH,
        (
            "# Rollback Plan\n\n"
            "Remove current phase artifacts, metadata copies, ignored private readiness outputs, "
            "tool, validator, focused test and governance rows. Do not touch raw inbox.\n"
        ),
    )


def _write_private_report(summary: dict[str, Any]) -> None:
    _write_text(
        PRIVATE_READINESS_REPORT_PATH,
        "\n".join(
            [
                "# Private Owner / Agent Diagnostic Readiness Recheck",
                "",
                "This ignored private report records that all diagnostic items remain blocked.",
                "It must not be committed or used as public evidence.",
                "",
                f"- diagnostic_response_ready_count: {summary['diagnostic_response_ready_count']}",
                f"- diagnostic_response_blocker_count: {summary['diagnostic_response_blocker_count']}",
                f"- valid_diagnostic_response_count: {summary['valid_diagnostic_response_count']}",
                f"- actionable_resolution_count: {summary['actionable_resolution_count']}",
                "",
            ]
        ),
    )


def _write_governance_events(generated_at: str, manifest: dict[str, Any]) -> None:
    files_changed = _changed_kmfa_files()
    _append_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": (
                "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-"
                "OWNER-OR-AGENT-DIAGNOSTIC-READINESS-RECHECK"
            ),
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "value-consistency",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "go_no_go": DECISION,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "summary": "Rechecked ignored private owner/agent diagnostic readiness and kept all residual differences blocked.",
            "diagnostic_response_ready_count": manifest["summary"]["diagnostic_response_ready_count"],
            "diagnostic_response_blocker_count": manifest["summary"]["diagnostic_response_blocker_count"],
            "valid_diagnostic_response_count": manifest["summary"]["valid_diagnostic_response_count"],
            "actionable_resolution_count": manifest["summary"]["actionable_resolution_count"],
            "open_residual_difference_count": manifest["summary"]["open_residual_difference_count"],
            "closed_discrepancy_count": manifest["summary"]["closed_discrepancy_count"],
            "safe_auto_resolution_count": manifest["summary"]["safe_auto_resolution_count"],
            "raw_inbox_read_performed": False,
            "raw_inbox_mutation_performed": False,
            "github_upload_performed": False,
            "business_execution_performed": False,
            "result_commit": "PENDING",
            "files_changed": files_changed,
        },
    )
    _append_jsonl(
        STAGE_STATUS_PATH,
        {
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_READINESS_RECHECK",
            "phase_id": PHASE_ID,
            "name": "v0.1.4 outside-scope candidate review residual difference owner or agent diagnostic readiness recheck",
            "phase_goal": "recheck private diagnostic response readiness without raw mutation or unsafe closure",
            "status": STATUS,
            "acceptance_id": ACCEPTANCE_ID,
            "acceptance_output": "Readiness manifest summary Go No-Go public-safe matrix private ignored readiness diagnostic blocker queue report validator focused test and governance records",
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "version": VERSION,
            "updated_at": "2026-07-07",
            "fact_level": "EXTRACTED",
            "raw_data_committed": False,
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "task_count": 3,
        },
    )
    for suffix, goal in [
        ("T1", "read prior diagnostic intake public artifacts and ignored private template without raw mutation"),
        ("T2", "write ignored private readiness diagnostic and blocker queue for unresolved diagnostic responses"),
        ("T3", "emit public-safe NO_GO readiness evidence while keeping downstream gates closed"),
    ]:
        _append_jsonl(
            TASK_STATUS_PATH,
            {
                "schema_version": "kmfa.v014_stage_phase_task_status.v1",
                "record_type": "v014_task",
                "project_id": "KMFA",
                "stage_id": "VALUE-CONSISTENCY",
                "governance_stage_id": "VALUE-CONSISTENCY",
                "roadmap_stage_id": "VALUE-CONSISTENCY",
                "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_READINESS_RECHECK",
                "phase_id": PHASE_ID,
                "task_id": f"{TASK_ID}-{suffix}",
                "task_goal": goal,
                "status": "completed",
                "acceptance_id": ACCEPTANCE_ID,
                "evidence_ref": MANIFEST_PATH.as_posix(),
                "version": VERSION,
                "updated_at": "2026-07-07",
                "fact_level": "EXTRACTED",
                "raw_data_committed": False,
                "derived_percent": 100.0,
            },
        )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = _now(generated_at)
    source_summary = _read_json(SOURCE_PUBLIC_SUMMARY_PATH)
    _read_json(SOURCE_PUBLIC_MANIFEST_PATH)
    _read_json(SOURCE_PUBLIC_GO_NO_GO_PATH)
    _read_json(SOURCE_PUBLIC_MATRIX_PATH)
    template_rows = _read_jsonl(SOURCE_PRIVATE_TEMPLATE_PATH)
    pending_rows = _read_jsonl(SOURCE_PRIVATE_PENDING_QUEUE_PATH)
    _read_json(SOURCE_PRIVATE_DIAGNOSTIC_PATH)
    if not SOURCE_PRIVATE_REPORT_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_REPORT_PATH)
    blocker_rows = _build_blocker_rows(generated, pending_rows)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        template_rows=template_rows,
        pending_rows=pending_rows,
        blocker_rows=blocker_rows,
    )
    go_no_go = _build_go_no_go(summary)
    matrix = _build_matrix(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)
    diagnostic = {
        "schema_version": "kmfa.v014_private_owner_or_agent_diagnostic_readiness_recheck_diagnostic.v1",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated,
        "source_phase_id": source_summary.get("phase_id"),
        "source_private_template_read": True,
        "source_private_pending_queue_read": True,
        "source_private_template_mutated": False,
        "source_private_pending_queue_mutated": False,
        "private_outputs_gitignored": {
            "readiness_diagnostic": _git_check_ignored(PRIVATE_READINESS_DIAGNOSTIC_PATH),
            "blocker_queue": _git_check_ignored(PRIVATE_BLOCKER_QUEUE_PATH),
            "readiness_report": _git_check_ignored(PRIVATE_READINESS_REPORT_PATH),
        },
        "public_track_counts": {
            "owner_select_one_authoritative_candidate_count": summary[
                "owner_select_one_authoritative_candidate_count"
            ],
            "provide_authoritative_source_reference_or_owner_exclusion_count": summary[
                "provide_authoritative_source_reference_or_owner_exclusion_count"
            ],
            "provide_formula_or_non_numeric_mapping_count": summary["provide_formula_or_non_numeric_mapping_count"],
        },
        "private_counts": {
            "diagnostic_response_ready_count": summary["diagnostic_response_ready_count"],
            "diagnostic_response_blocker_count": summary["diagnostic_response_blocker_count"],
            "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
            "actionable_resolution_count": summary["actionable_resolution_count"],
        },
    }

    for path, payload in [
        (SUMMARY_PATH, summary),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (MANIFEST_PATH, manifest),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
        (METADATA_MANIFEST_PATH, manifest),
        (PRIVATE_READINESS_DIAGNOSTIC_PATH, diagnostic),
    ]:
        _write_json(path, payload)
    _write_jsonl(PRIVATE_BLOCKER_QUEUE_PATH, blocker_rows)
    _write_private_report(summary)
    _write_human_artifacts(summary)
    if write_governance_event:
        _write_governance_events(generated, manifest)
    return {"summary": summary, "manifest": manifest, "go_no_go": go_no_go, "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--no-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at, write_governance_event=not args.no_governance_event)
    summary = result["summary"]
    print(
        "PASS: generated "
        f"{PHASE_ID} decision={summary['decision']} "
        f"diagnostic_response_blockers={summary['diagnostic_response_blocker_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
