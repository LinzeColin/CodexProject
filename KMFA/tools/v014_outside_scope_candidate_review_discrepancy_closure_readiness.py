#!/usr/bin/env python3
"""Assess closure readiness for owner-authorized discrepancy queue items."""

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
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_DISCREPANCY_CLOSURE_READINESS"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-DISCREPANCY-CLOSURE-READINESS-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-DISCREPANCY-CLOSURE-READINESS"
VERSION = "0.1.4-outside-scope-candidate-review-discrepancy-closure-readiness"
STATUS = "completed_validated_local_only_discrepancy_closure_readiness_no_go"
DECISION = "NO_GO"
SOURCE_PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_OWNER_AUTHORIZED_DISCREPANCY_REPORT"
READINESS_CONCLUSION = "no_discrepancy_item_has_authoritative_closure_evidence_private_closure_workpack_written"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_DISCREPANCY_CLOSURE_BLOCKER_AUDIT"
NEXT_REQUIRED_INPUT = "none_private_blocker_audit_can_continue_without_raw_mutation"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_discrepancy_closure_readiness_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_discrepancy_closure_readiness_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_candidate_review_discrepancy_closure_readiness_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_candidate_review_discrepancy_closure_readiness_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_discrepancy_closure_readiness_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_discrepancy_closure_readiness_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_discrepancy_closure_readiness_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_discrepancy_closure_readiness_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_discrepancy_closure_readiness_matrix_public_safe.json"

SOURCE_PUBLIC_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_summary.json"
)
SOURCE_PRIVATE_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report/private_owner_authorized_discrepancy_queue.jsonl"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_discrepancy_closure_readiness"
PRIVATE_RECORD_PATH = PRIVATE_OUTPUT_DIR / "private_discrepancy_closure_readiness_record.json"
PRIVATE_ITEMS_PATH = PRIVATE_OUTPUT_DIR / "private_discrepancy_closure_readiness_items.jsonl"
PRIVATE_BLOCKING_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_discrepancy_closure_blocking_queue.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_discrepancy_closure_readiness_diagnostic.json"
PRIVATE_WORKPACK_PATH = PRIVATE_OUTPUT_DIR / "private_discrepancy_closure_workpack.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


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


def _git_check_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_discrepancy_summary_read_by_this_phase": True,
        "source_private_discrepancy_queue_read_by_this_phase": True,
        "private_closure_readiness_record_written_by_this_phase": True,
        "private_closure_blocking_queue_written_by_this_phase": True,
        "private_closure_workpack_written_by_this_phase": True,
        "source_private_discrepancy_queue_mutated_by_this_phase": False,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "protected_source_identifier_derivation_performed_by_this_phase": False,
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
        "private_discrepancy_queue_committed": False,
        "private_closure_readiness_record_committed": False,
        "private_closure_blocking_queue_committed": False,
        "private_closure_workpack_committed": False,
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


def _closure_bucket(item: dict[str, Any]) -> tuple[str, str, str]:
    status = str(item.get("candidate_status"))
    if status == "auto_ambiguous_multiple_candidates_requires_owner_review":
        return (
            "ambiguous_tie_requires_authoritative_selection",
            "candidate_scores_tied_and_no_exact_private_match",
            "owner_verified_candidate_selection_or_new_source_reference",
        )
    if status == "auto_unmatched_requires_owner_review":
        return (
            "no_context_candidate_requires_authoritative_source_reference",
            "no_context_raw_candidate_available_for_private_processed_value",
            "new_authoritative_source_record_reference_or_owner_exclusion",
        )
    if status == "requires_non_numeric_owner_mapping":
        return (
            "non_numeric_or_calculation_requires_formula_mapping",
            "requires_authoritative_formula_or_non_numeric_mapping",
            "authoritative_formula_or_non_numeric_mapping",
        )
    return ("unsupported_status_requires_manual_triage", "unsupported_candidate_status", "manual_triage")


def _build_closure_items(generated_at: str, queue_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], Counter[str]]:
    items: list[dict[str, Any]] = []
    for index, row in enumerate(queue_rows, start=1):
        bucket, blocker, required_evidence = _closure_bucket(row)
        ready = False
        item = {
            "closure_readiness_item_id": f"OSCR-CLOSE-{index:03d}",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "source_resolution_item_id": row.get("resolution_item_id"),
            "source_review_item_id": row.get("source_review_item_id"),
            "source_alignment_item_index": row.get("source_alignment_item_index"),
            "target_slot_id": row.get("target_slot_id"),
            "candidate_status": row.get("candidate_status"),
            "closure_bucket": bucket,
            "closure_blocker_code": blocker,
            "required_evidence_class": required_evidence,
            "safe_auto_closure_available": False,
            "closure_ready": ready,
            "source_map_correction_ready": False,
            "raw_to_processed_value_comparison_allowed_by_this_phase": False,
            "business_value_consistency_verified_by_this_phase": False,
            "downstream_release_allowed_by_this_phase": False,
        }
        items.append(item)
    return items, Counter(str(item["closure_bucket"]) for item in items)


def _build_summary(
    *, generated_at: str, source_summary: dict[str, Any], closure_items: list[dict[str, Any]], bucket_counts: Counter[str]
) -> dict[str, Any]:
    blocked_count = sum(1 for item in closure_items if not item["closure_ready"])
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_discrepancy_closure_readiness_summary.v1",
        "record_type": "v014_outside_scope_candidate_review_discrepancy_closure_readiness_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_decision": source_summary.get("decision"),
        "readiness_conclusion": READINESS_CONCLUSION,
        "source_discrepancy_queue_item_count": int(source_summary.get("discrepancy_queue_item_count") or 0),
        "closure_readiness_assessed": True,
        "closure_plan_item_count": len(closure_items),
        "closure_ready_item_count": 0,
        "closure_blocked_item_count": blocked_count,
        "safe_auto_closure_count": 0,
        "ambiguous_tie_closure_blocker_count": bucket_counts["ambiguous_tie_requires_authoritative_selection"],
        "no_context_candidate_closure_blocker_count": bucket_counts[
            "no_context_candidate_requires_authoritative_source_reference"
        ],
        "non_numeric_or_calculation_closure_blocker_count": bucket_counts[
            "non_numeric_or_calculation_requires_formula_mapping"
        ],
        "unsupported_status_closure_blocker_count": bucket_counts["unsupported_status_requires_manual_triage"],
        "private_closure_readiness_record_written": True,
        "private_closure_blocking_queue_written": True,
        "private_closure_workpack_written": True,
        "all_discrepancy_items_classified_for_closure": len(closure_items) == 72,
        "source_map_correction_ready": False,
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
        "schema_version": "kmfa.v014_outside_scope_candidate_review_discrepancy_closure_readiness_go_no_go.v1",
        "record_type": "v014_outside_scope_candidate_review_discrepancy_closure_readiness_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "readiness_conclusion": READINESS_CONCLUSION,
        "closure_ready_item_count": summary["closure_ready_item_count"],
        "closure_blocked_item_count": summary["closure_blocked_item_count"],
        "safe_auto_closure_count": summary["safe_auto_closure_count"],
        "raw_to_processed_value_comparison_allowed": False,
        "source_map_correction_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_discrepancy_queue_loaded", summary["source_discrepancy_queue_item_count"] == 72),
        ("all_discrepancy_items_classified_for_closure", summary["all_discrepancy_items_classified_for_closure"]),
        ("no_safe_auto_closure_available", summary["safe_auto_closure_count"] == 0),
        ("all_closure_items_blocked", summary["closure_blocked_item_count"] == 72),
        ("ambiguous_tie_bucket_locked", summary["ambiguous_tie_closure_blocker_count"] == 24),
        ("no_context_bucket_locked", summary["no_context_candidate_closure_blocker_count"] == 40),
        ("non_numeric_bucket_locked", summary["non_numeric_or_calculation_closure_blocker_count"] == 8),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["source_map_correction_ready"] is False),
    ]
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_discrepancy_closure_readiness_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_candidate_review_discrepancy_closure_readiness_matrix_public_safe",
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
        "schema_version": "kmfa.v014_outside_scope_candidate_review_discrepancy_closure_readiness_manifest.v1",
        "record_type": "v014_outside_scope_candidate_review_discrepancy_closure_readiness_manifest",
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
            "source_public_summary": "public_safe_metadata_copy",
            "source_private_discrepancy_queue": "ignored_private_runtime",
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
            "private:discrepancy_closure_readiness_record",
            "private:discrepancy_closure_readiness_items",
            "private:discrepancy_closure_blocking_queue",
            "private:discrepancy_closure_readiness_diagnostic",
            "private:discrepancy_closure_workpack",
        ],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_discrepancy_closure_readiness.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_discrepancy_closure_readiness.py --require-private-readiness",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_discrepancy_closure_readiness",
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
    report = f"""# Outside-Scope Candidate Review Discrepancy Closure Readiness

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- source discrepancy queue items: `{summary['source_discrepancy_queue_item_count']}`
- closure plan items: `{summary['closure_plan_item_count']}`
- closure ready items: `{summary['closure_ready_item_count']}`
- closure blocked items: `{summary['closure_blocked_item_count']}`
- ambiguous tie blockers: `{summary['ambiguous_tie_closure_blocker_count']}`
- no-context candidate blockers: `{summary['no_context_candidate_closure_blocker_count']}`
- non-numeric/calculation blockers: `{summary['non_numeric_or_calculation_closure_blocker_count']}`
- raw boundary: raw inbox read/list/stat/parse/write/delete/move/rename/copy/normalize/mutation all `false` in this phase.
- downstream boundary: source-map correction, formal raw-to-processed comparison, reconciliation, formal report, GitHub upload, app reinstall and business execution all remain `false`.
"""
    _write_text(REPORT_PATH, report)
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"# Go/No-Go\n\n- decision: `{DECISION}`\n- reason: 72 discrepancy items remain blocked for closure; private closure workpack written.\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# Test Results",
                "",
                "- generator: pending current run",
                "- validator: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_discrepancy_closure_readiness.py --require-private-readiness`",
                "- focused unit test: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_discrepancy_closure_readiness`",
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        "# Risk Register\n\n- Risk: Treating a readiness workpack as discrepancy closure would corrupt value-consistency evidence.\n- Control: validator requires closure_ready_item_count=0, closure_blocked_item_count=72 and downstream gates closed.\n",
    )
    _write_text(
        ROLLBACK_PATH,
        "# Rollback Plan\n\nRemove current phase artifacts, metadata copies, ignored private closure readiness outputs, tool, validator, focused test and governance rows. Do not touch raw inbox.\n",
    )
    _write_text(
        PRIVATE_WORKPACK_PATH,
        "# Private Discrepancy Closure Workpack\n\nThis ignored private workpack contains private refs for 72 blocked discrepancy items. Do not commit.\n",
    )


def _write_governance_events(generated_at: str, manifest: dict[str, Any]) -> None:
    files_changed = _changed_kmfa_files()
    _append_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-DISCREPANCY-CLOSURE-READINESS",
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
            "summary": "Assessed private discrepancy closure readiness and wrote a private closure workpack while keeping all downstream gates closed.",
            "closure_plan_item_count": manifest["summary"]["closure_plan_item_count"],
            "closure_ready_item_count": manifest["summary"]["closure_ready_item_count"],
            "closure_blocked_item_count": manifest["summary"]["closure_blocked_item_count"],
            "safe_auto_closure_count": manifest["summary"]["safe_auto_closure_count"],
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
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_DISCREPANCY_CLOSURE_READINESS",
            "phase_id": PHASE_ID,
            "name": "v0.1.4 outside-scope candidate review discrepancy closure readiness",
            "phase_goal": "classify 72 private discrepancy queue items into closure blockers without raw mutation or unsafe closure",
            "status": STATUS,
            "acceptance_id": ACCEPTANCE_ID,
            "acceptance_output": "Discrepancy closure readiness manifest summary Go No-Go public-safe matrix private ignored closure workpack validator focused test and governance records",
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
        ("T1", "read prior public summary and private discrepancy queue without raw mutation"),
        ("T2", "classify all discrepancy items into private closure blockers"),
        ("T3", "emit public-safe NO_GO closure readiness evidence while keeping downstream gates closed"),
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
                "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_DISCREPANCY_CLOSURE_READINESS",
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
    source_queue = _read_jsonl(SOURCE_PRIVATE_QUEUE_PATH)
    closure_items, bucket_counts = _build_closure_items(generated, source_queue)
    summary = _build_summary(generated_at=generated, source_summary=source_summary, closure_items=closure_items, bucket_counts=bucket_counts)
    go_no_go = _build_go_no_go(summary)
    matrix = _build_matrix(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)

    private_record = {
        "schema_version": "kmfa.v014_private_discrepancy_closure_readiness_record.v1",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated,
        "source_phase_id": SOURCE_PHASE_ID,
        "summary_private": {
            "closure_plan_item_count": len(closure_items),
            "closure_ready_item_count": 0,
            "closure_blocked_item_count": summary["closure_blocked_item_count"],
            "bucket_counts": dict(bucket_counts),
        },
        "closure_items": closure_items,
    }
    diagnostic = {
        "schema_version": "kmfa.v014_private_discrepancy_closure_readiness_diagnostic.v1",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated,
        "source_private_queue_read": True,
        "source_private_queue_mutated": False,
        "private_outputs_gitignored": {
            "record": _git_check_ignored(PRIVATE_RECORD_PATH),
            "items": _git_check_ignored(PRIVATE_ITEMS_PATH),
            "blocking_queue": _git_check_ignored(PRIVATE_BLOCKING_QUEUE_PATH),
            "diagnostic": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
            "workpack": _git_check_ignored(PRIVATE_WORKPACK_PATH),
        },
        "closure_bucket_counts": dict(bucket_counts),
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
        (PRIVATE_RECORD_PATH, private_record),
        (PRIVATE_DIAGNOSTIC_PATH, diagnostic),
    ):
        _write_json(path, payload)
    _write_jsonl(PRIVATE_ITEMS_PATH, closure_items)
    _write_jsonl(PRIVATE_BLOCKING_QUEUE_PATH, closure_items)
    _write_human_artifacts(summary)
    if write_governance_event:
        _write_governance_events(generated, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--skip-governance-event", action="store_true")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at, write_governance_event=not args.skip_governance_event)
    summary = manifest["summary"]
    print(
        "PASS: generated "
        f"{PHASE_ID} decision={summary['decision']} "
        f"closure_blocked={summary['closure_blocked_item_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
