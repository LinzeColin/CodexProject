#!/usr/bin/env python3
"""Generate KMFA v0.1.4 source-map authorized-fill gap-resolution evidence.

This phase classifies the remaining authorized-fill gaps from the previous
private processed value source-map fill. It does not read the raw inbox, does
not infer missing values, and does not run materialization or value comparison.
The private owner worklist remains in ignored runtime; public artifacts contain
aggregate counts and release gates only.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_gap_resolution.v1"
GO_NO_GO_SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_gap_resolution_go_no_go.v1"
PRIVATE_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_source_map_gap_resolution.v1"
PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PHASE_ID = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_AUTHORIZED_FILL_GAP_RESOLUTION"
TASK_ID = "KMFA-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-AUTHORIZED-FILL-GAP-RESOLUTION-20260705"
ACCEPTANCE_ID = "ACC-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-AUTHORIZED-FILL-GAP-RESOLUTION"
STATUS = "completed_validated_local_only_no_go_authorized_fill_gap_resolution_locked"
NEXT_RECOMMENDED_PHASE = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE"
GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_AUTHORIZED_FILL_GAP_RESOLUTION")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "private_processed_value_source_map_gap_resolution_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "private_processed_value_source_map_gap_resolution_go_no_go_report.json"
SUMMARY_PATH = MACHINE_DIR / "private_processed_value_source_map_gap_resolution_summary.json"
GAP_MATRIX_PATH = MACHINE_DIR / "private_processed_value_source_map_gap_resolution_matrix.json"
REPORT_PATH = HUMAN_DIR / "private_processed_value_source_map_gap_resolution_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_gap_resolution_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_gap_resolution_go_no_go_report.json")
METADATA_SUMMARY_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_gap_resolution_summary.json")
METADATA_GAP_MATRIX_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_gap_resolution_matrix.json")

AUTHORIZED_FILL_PUBLIC_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_AUTHORIZED_FILL/machine/private_processed_value_source_map_authorized_fill_manifest.json"
)
AUTHORIZED_FILL_PRIVATE_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_source_map_authorized_fill/private_processed_value_source_map_authorized_fill.json"
)
AUTHORIZED_SOURCE_MAP_PRIVATE_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_source_map_authorized_fill/private_processed_value_source_map.json"
)
CAPTURE_PRIVATE_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_source_map_capture/private_processed_value_source_map_capture.json"
)

PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_private_processed_value_source_map_gap_resolution")
PRIVATE_OWNER_WORKLIST_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_fill_worklist.json"
PRIVATE_GAP_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_gap_resolution_diagnostic.json"


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return "UNKNOWN"
    return result.stdout.strip()


def _current_git_commit() -> str:
    return _git_output(["rev-parse", "HEAD"])


def stable_source_commit(
    *,
    manifest_path: Path = MANIFEST_PATH,
    fallback_git_commit: Callable[[], str] = _current_git_commit,
) -> str:
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        source_commit = existing.get("source_commit") if isinstance(existing, dict) else None
        if isinstance(source_commit, str) and GIT_COMMIT_RE.fullmatch(source_commit):
            return source_commit
    return fallback_git_commit()


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


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
        "raw_inbox_write_performed_by_this_phase": False,
        "raw_inbox_delete_performed_by_this_phase": False,
        "raw_inbox_move_performed_by_this_phase": False,
        "raw_inbox_rename_performed_by_this_phase": False,
        "raw_inbox_mutation_performed_by_this_phase": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_sheet_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_processed_ref_committed": False,
        "private_owner_worklist_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_gap_resolution(
    *,
    authorized_fill: dict[str, Any],
    capture: dict[str, Any],
    existing_source_map: dict[str, Any],
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    authorized_summary = authorized_fill.get("authorized_fill_summary", {})
    unfilled_items = authorized_fill.get("unfilled_items", [])
    filled_items = authorized_fill.get("filled_items", [])
    capture_slots = capture.get("source_map_capture_slots", [])
    if not isinstance(unfilled_items, list) or not isinstance(filled_items, list) or not isinstance(capture_slots, list):
        raise ValueError("authorized fill and capture payloads must contain list diagnostics")

    slots_by_id = {
        slot.get("target_slot_id"): slot
        for slot in capture_slots
        if isinstance(slot, dict) and isinstance(slot.get("target_slot_id"), str)
    }
    private_refs = [
        item.get("private_processed_ref")
        for item in unfilled_items
        if isinstance(item, dict) and isinstance(item.get("private_processed_ref"), str)
    ]
    target_ids = [
        item.get("target_slot_id")
        for item in unfilled_items
        if isinstance(item, dict) and isinstance(item.get("target_slot_id"), str)
    ]
    status_counts = Counter(
        item.get("fill_status")
        for item in unfilled_items
        if isinstance(item, dict) and isinstance(item.get("fill_status"), str)
    )
    source_root_buckets = {
        slots_by_id.get(target_id, {}).get("source_root_id")
        for target_id in target_ids
        if slots_by_id.get(target_id, {}).get("source_root_id") is not None
    }
    context_group_buckets = {
        slots_by_id.get(target_id, {}).get("context_group")
        for target_id in target_ids
        if slots_by_id.get(target_id, {}).get("context_group") is not None
    }
    shape_buckets = {
        slots_by_id.get(target_id, {}).get("private_processed_ref_shape_hash")
        for target_id in target_ids
        if slots_by_id.get(target_id, {}).get("private_processed_ref_shape_hash") is not None
    }
    source_records = existing_source_map.get("processed_value_sources", [])
    source_record_count = len(source_records) if isinstance(source_records, list) else 0

    unresolved_count = len(unfilled_items)
    unique_unresolved_count = len(set(private_refs))
    duplicate_unresolved_count = unresolved_count - unique_unresolved_count
    summary = {
        "previous_fill_request_item_count": int(authorized_summary.get("fill_request_item_count", 0)),
        "previous_authorized_filled_item_count": int(authorized_summary.get("authorized_filled_item_count", 0)),
        "previous_authorized_unfilled_item_count": int(authorized_summary.get("authorized_unfilled_item_count", 0)),
        "existing_source_map_record_count": source_record_count,
        "unresolved_gap_item_count": unresolved_count,
        "unresolved_unique_private_ref_count": unique_unresolved_count,
        "duplicate_unresolved_gap_item_count": duplicate_unresolved_count,
        "gap_reason_count": len(status_counts),
        "source_root_bucket_count": len(source_root_buckets),
        "context_group_bucket_count": len(context_group_buckets),
        "private_ref_shape_bucket_count": len(shape_buckets),
        "private_owner_worklist_item_count": unresolved_count,
        "new_authorized_fingerprint_count": 0,
        "additional_source_map_records_written_count": 0,
        "source_map_gap_resolution_complete": False,
        "owner_authorized_fill_intake_required": True,
        "metadata_hash_sibling_backfill_required": True,
        "processed_value_materialization_replay_ready": False,
        "raw_to_processed_value_comparison_ready": False,
        "business_value_consistency_verified": False,
        "gap_resolution_status": "blocked_owner_authorized_private_value_sources_required",
    }
    gap_matrix = {
        "schema_version": "kmfa.v014_private_processed_value_source_map_gap_resolution_matrix.v1",
        "record_type": "v014_private_processed_value_source_map_gap_resolution_matrix",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "public_commit_policy": "aggregate_counts_only_no_private_refs_or_values",
        "gap_reason_buckets": [
            {
                "gap_reason": reason,
                "gap_item_count": count,
                "resolution_lane": "owner_authorized_private_value_source_intake",
                "auto_fill_allowed": False,
                "raw_value_extraction_allowed_by_this_phase": False,
            }
            for reason, count in sorted(status_counts.items())
        ],
        "resolution_lanes": [
            {
                "lane_id": "PVSMAF-GAP-LANE-001",
                "lane_name": "owner_authorized_private_value_source_intake",
                "gap_item_count": unresolved_count,
                "owner_or_authorized_delegate_required": True,
                "public_value_commit_allowed": False,
            },
            {
                "lane_id": "PVSMAF-GAP-LANE-002",
                "lane_name": "metadata_hash_sibling_backfill_after_authorized_intake",
                "gap_item_count": unresolved_count,
                "owner_or_authorized_delegate_required": True,
                "public_value_commit_allowed": False,
            },
            {
                "lane_id": "PVSMAF-GAP-LANE-003",
                "lane_name": "materialization_replay_after_complete_private_source_map",
                "gap_item_count": unresolved_count,
                "owner_or_authorized_delegate_required": False,
                "public_value_commit_allowed": False,
            },
        ],
        "bucket_counts": {
            "source_root_bucket_count": summary["source_root_bucket_count"],
            "context_group_bucket_count": summary["context_group_bucket_count"],
            "private_ref_shape_bucket_count": summary["private_ref_shape_bucket_count"],
        },
        "blocked_follow_on_actions": {
            "processed_value_materialization_replay_allowed": False,
            "raw_to_processed_value_comparison_allowed": False,
            "lineage_full_check_allowed": False,
            "formal_report_allowed": False,
            "github_upload_allowed": False,
            "app_reinstall_allowed": False,
            "business_execution_allowed": False,
        },
    }
    owner_worklist_items: list[dict[str, Any]] = []
    for item in unfilled_items:
        if not isinstance(item, dict):
            continue
        target_id = item.get("target_slot_id")
        slot = slots_by_id.get(target_id, {}) if isinstance(target_id, str) else {}
        owner_worklist_items.append(
            {
                "target_slot_id": target_id,
                "private_processed_ref": item.get("private_processed_ref"),
                "private_processed_ref_hash": item.get("private_processed_ref_hash"),
                "fill_status": item.get("fill_status"),
                "source_root_id": slot.get("source_root_id"),
                "context_group": slot.get("context_group"),
                "source_artifact_ref_hash": slot.get("source_artifact_ref_hash"),
                "record_ref_hash": slot.get("record_ref_hash"),
                "target_key_ref_hash": slot.get("target_key_ref_hash"),
                "private_processed_ref_shape_hash": slot.get("private_processed_ref_shape_hash"),
                "required_owner_action": "supply_authorized_processed_value_fingerprint_or_authorized_private_source_pointer",
                "public_commit_policy": "do_not_commit_private_ref_or_value",
            }
        )
    private_worklist = {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "classification": "private_owner_authorized_fill_worklist_do_not_commit",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "owner_worklist_summary": {
            "owner_worklist_item_count": len(owner_worklist_items),
            "unique_private_ref_count": unique_unresolved_count,
            "duplicate_gap_item_count": duplicate_unresolved_count,
            "new_authorized_fingerprint_count": 0,
            "raw_to_processed_value_comparison_performed": False,
            "business_value_consistency_verified": False,
        },
        "owner_worklist_items": owner_worklist_items,
    }
    private_diagnostic = {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "classification": "private_gap_resolution_diagnostic_do_not_commit",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "gap_resolution_summary": summary,
        "gap_reason_counts": dict(status_counts),
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    return summary, gap_matrix, private_worklist, private_diagnostic


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": GO_NO_GO_SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_gap_resolution_go_no_go_report",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": "remaining authorized-fill gaps require owner-authorized private value source intake before replay or comparison",
        "unresolved_gap_item_count": summary["unresolved_gap_item_count"],
        "unresolved_unique_private_ref_count": summary["unresolved_unique_private_ref_count"],
        "source_map_gap_resolution_complete": summary["source_map_gap_resolution_complete"],
        "owner_authorized_fill_intake_required": summary["owner_authorized_fill_intake_required"],
        "processed_value_materialization_replay_allowed": False,
        "raw_to_processed_value_comparison_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "resolved_blocker_ids": [
            "AUTHORIZED_FILL_GAPS_CLASSIFIED_PUBLIC_SAFE",
            "PRIVATE_OWNER_WORKLIST_PREPARED",
            "RAW_INBOX_MUTATION_NOT_PERFORMED_BY_THIS_PHASE",
        ],
        "blocker_ids": [
            "OWNER_AUTHORIZED_PRIVATE_VALUE_SOURCE_INTAKE_REQUIRED",
            "AUTHORIZED_PROCESSED_VALUE_SOURCE_MAP_INCOMPLETE",
            "PROCESSED_VALUE_MATERIALIZATION_REPLAY_BLOCKED",
            "RAW_TO_PROCESSED_VALUE_COMPARISON_BLOCKED",
            "BUSINESS_VALUE_CONSISTENCY_NOT_VERIFIED",
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "FORMAL_REPORT_BLOCKED",
            "GITHUB_UPLOAD_DEFERRED",
            "APP_REINSTALL_BLOCKED",
            "BUSINESS_EXECUTION_BLOCKED",
        ],
    }


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    authorized_public_manifest = _read_json(AUTHORIZED_FILL_PUBLIC_MANIFEST_PATH)
    authorized_fill = _read_json(AUTHORIZED_FILL_PRIVATE_PATH)
    capture = _read_json(CAPTURE_PRIVATE_PATH)
    existing_source_map = _read_json(AUTHORIZED_SOURCE_MAP_PRIVATE_PATH)
    summary, gap_matrix, private_worklist, private_diagnostic = _build_gap_resolution(
        authorized_fill=authorized_fill,
        capture=capture,
        existing_source_map=existing_source_map,
        generated_at=timestamp,
    )
    go_no_go = _build_go_no_go(summary)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_gap_resolution_manifest",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "phase_name": "KMFA v0.1.4 authorized private processed value source-map gap resolution",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "status": STATUS,
        "generated_at": timestamp,
        "source_commit": stable_source_commit(),
        "branch": _git_output(["branch", "--show-current"]),
        "dependencies": {
            "authorized_fill_manifest": AUTHORIZED_FILL_PUBLIC_MANIFEST_PATH.as_posix(),
            "authorized_fill_status": authorized_public_manifest.get("status"),
            "private_authorized_fill_runtime": "private_runtime_previous_phase",
            "private_capture_runtime": "private_runtime_previous_phase",
            "private_source_map_runtime": "private_runtime_previous_phase",
        },
        "phase_scope_controls": {
            "current_phase_only": True,
            "gap_resolution_only": True,
            "previous_authorized_fill_consumed": True,
            "previous_capture_diagnostic_consumed": True,
            "private_owner_worklist_written": True,
            "public_gap_matrix_written": True,
            "new_fingerprints_materialized": False,
            "processed_value_materialization_replay_performed": False,
            "raw_to_processed_value_comparison_performed": False,
            "processed_data_reconciliation_performed": False,
            "lineage_full_check_performed": False,
            "formal_report_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "next_phase_started": False,
        },
        "raw_readonly_boundary": _raw_boundary(),
        "public_repo_safety": _public_safety(),
        "gap_resolution_summary": summary,
        "gap_resolution_matrix": gap_matrix,
        "private_owner_worklist_ref": "private_runtime_only_not_committed",
        "go_no_go": go_no_go,
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            SUMMARY_PATH.as_posix(),
            GAP_MATRIX_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_GAP_MATRIX_PATH.as_posix(),
        ],
        "github_upload_performed": False,
        "formal_report_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }

    for path, payload in (
        (PRIVATE_OWNER_WORKLIST_PATH, private_worklist),
        (PRIVATE_GAP_DIAGNOSTIC_PATH, private_diagnostic),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (SUMMARY_PATH, summary),
        (GAP_MATRIX_PATH, gap_matrix),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_GAP_MATRIX_PATH, gap_matrix),
    ):
        _write_json(path, payload)

    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Source-Map Authorized-Fill Gap Resolution",
                "",
                f"- phase_scope: `{PHASE_ID} only`",
                f"- previous_fill_request_item_count: `{summary['previous_fill_request_item_count']}`",
                f"- previous_authorized_filled_item_count: `{summary['previous_authorized_filled_item_count']}`",
                f"- unresolved_gap_item_count: `{summary['unresolved_gap_item_count']}`",
                f"- unresolved_unique_private_ref_count: `{summary['unresolved_unique_private_ref_count']}`",
                f"- duplicate_unresolved_gap_item_count: `{summary['duplicate_unresolved_gap_item_count']}`",
                f"- owner_authorized_fill_intake_required: `{str(summary['owner_authorized_fill_intake_required']).lower()}`",
                f"- source_map_gap_resolution_complete: `{str(summary['source_map_gap_resolution_complete']).lower()}`",
                "- raw_inbox_access_performed_by_this_phase: `false`",
                "- processed_value_materialization_replay_performed: `false`",
                "- raw_to_processed_value_comparison_performed: `false`",
                "- business_value_consistency_verified: `false`",
                "- github_upload_performed: `false`",
                "- go_no_go: `NO_GO`",
            ]
        )
        + "\n",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go No-Go Record",
                "",
                "- decision: `NO_GO`",
                "- reason: remaining authorized-fill gaps require owner-authorized private source intake before replay/comparison",
                f"- unresolved_gap_item_count: `{summary['unresolved_gap_item_count']}`",
                f"- next_recommended_phase: `{NEXT_RECOMMENDED_PHASE}`",
                "- github_upload_allowed: `false`",
                "- app_reinstall_allowed: `false`",
                "- business_execution_allowed: `false`",
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
                "- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_private_processed_value_source_map_gap_resolution -q` failed with missing validator/generator module.",
                "- GREEN verification required: focused validator, focused unit test, governance validators, public-safe scans and git boundary checks must pass before local commit.",
                "- Result source of truth: fresh command output from the current run; this file is refreshed after final verification.",
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
                "| Risk | Status | Control |",
                "| --- | --- | --- |",
                "| Missing 113 authorized fingerprints | open | owner-authorized private worklist prepared; release remains NO_GO |",
                "| Private refs leak to public artifacts | controlled | public validator scans artifacts and tracked files |",
                "| Raw inbox mutation | controlled | this phase performs no raw inbox access or mutation |",
                "| Premature materialization/comparison | blocked | Go/No-Go keeps replay and comparison false |",
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
                "1. Remove this phase's public artifacts and metadata quality copies.",
                "2. Remove ignored private runtime folder for this phase.",
                "3. Re-run the previous authorized-fill validator to restore the prior NO_GO gate.",
                "4. Do not touch the raw inbox during rollback.",
            ]
        )
        + "\n",
    )
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["gap_resolution_summary"]
    print(
        "Generated KMFA v0.1.4 source-map authorized-fill gap resolution "
        f"(unresolved={summary['unresolved_gap_item_count']}, "
        f"unique={summary['unresolved_unique_private_ref_count']}, "
        "go_no_go=NO_GO)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
