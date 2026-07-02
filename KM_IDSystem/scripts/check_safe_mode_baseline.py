#!/usr/bin/env python3
"""Read-only Stage 011 safe-mode baseline preflight for IDS operations."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KM_IDSystem.scripts import check_local_path_contract as path_contract


OPERATIONS_ENTRANCE = "IDS 系统运营入口"
PAUSED_WORKFLOWS = [
    "bulk_import",
    "recursive_directory_scanning",
    "raw_material_cleanup",
    "ocr",
    "embedding",
    "index_rebuild",
    "backup_copy",
    "manifest_generation",
    "report_export",
    "batch_report_generation",
    "external_api_calls",
]
INDEX_SAFE_STATES = {"OK", "CLEAR", "INDEX_OK", "NOT_REQUIRED"}
API_SAFE_STATES = {"OK", "CLEAR", "BUDGET_OK", "OFFLINE_ALLOWED", "NOT_REQUIRED"}
INDEX_BLOCKED_STATES = {"FAILED", "STALE", "PARTIAL", "UNKNOWN", "INDEX_FAILED"}
API_BLOCKED_STATES = {
    "EXCEEDED",
    "OVER_BUDGET",
    "RATE_LIMITED",
    "UNKNOWN",
    "MISSING_KEY",
    "PROVIDER_UNSAFE",
    "API_BUDGET_EXCEEDED",
}
STATE_OPERATOR_ACTIONS = {
    "SAFE_MODE_CLEAR": ["bounded_preflight_only"],
    "SAFE_MODE_ROOT_NOT_CONFIGURED": ["configure_ids_data_root", "rerun_safe_mode_preflight"],
    "SAFE_MODE_DRIVE_OFFLINE": ["reconnect_external_drive", "rerun_safe_mode_preflight"],
    "SAFE_MODE_REVALIDATION_REQUIRED": [
        "revalidate_path_permission_structure",
        "rerun_safe_mode_preflight",
    ],
    "SAFE_MODE_PERMISSION_DENIED": ["fix_filesystem_permissions", "rerun_safe_mode_preflight"],
    "SAFE_MODE_STORAGE_BLOCKED": ["free_internal_disk_space", "rerun_safe_mode_preflight"],
    "SAFE_MODE_PATH_BLOCKED": ["correct_local_path_contract", "rerun_safe_mode_preflight"],
    "SAFE_MODE_INDEX_FAILED": ["repair_or_rebuild_index", "rerun_safe_mode_preflight"],
    "SAFE_MODE_API_BUDGET_EXCEEDED": [
        "pause_external_api_calls",
        "confirm_api_budget_or_use_offline_mode",
    ],
    "SAFE_MODE_UNKNOWN": ["manual_operator_review", "rerun_safe_mode_preflight"],
}


def _gib_to_bytes(value: float | None) -> int | None:
    if value is None:
        return None
    return int(value * 1024**3)


def _normalize_state(value: str | None, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    value = value.strip().upper()
    return value or default


def _merge_actions(*action_lists: list[str]) -> list[str]:
    merged: list[str] = []
    for actions in action_lists:
        for action in actions:
            if action not in merged:
                merged.append(action)
    return merged


def _map_safe_mode_state(local_path: dict[str, Any], index_state: str, api_budget_state: str) -> str:
    path_state = local_path.get("state", "PATH_CONTRACT_UNKNOWN")
    storage_state = local_path.get("storage_budget_state")
    removable_state = local_path.get("removable_drive_state")

    if removable_state == "NOT_CONFIGURED":
        return "SAFE_MODE_ROOT_NOT_CONFIGURED"
    if removable_state in {"OFFLINE", "ROOT_ABSENT"}:
        return "SAFE_MODE_DRIVE_OFFLINE"
    if removable_state in {"RECONNECTED_NEEDS_REVALIDATION", "PATH_CHANGED"}:
        return "SAFE_MODE_REVALIDATION_REQUIRED"
    if removable_state == "PERMISSION_DENIED":
        return "SAFE_MODE_PERMISSION_DENIED"
    if removable_state == "STORAGE_BLOCKED":
        return "SAFE_MODE_STORAGE_BLOCKED"
    if storage_state in {
        "BUDGET_BLOCKED_LOW_FREE",
        "BUDGET_BLOCKED_HIGH_WATERLINE",
        "BUDGET_UNKNOWN",
        "UNBOUNDED_OUTPUT_RISK",
    }:
        return "SAFE_MODE_STORAGE_BLOCKED"
    if path_state != "PATH_CONTRACT_OK":
        return "SAFE_MODE_PATH_BLOCKED"
    if index_state in INDEX_BLOCKED_STATES or index_state not in INDEX_SAFE_STATES:
        return "SAFE_MODE_INDEX_FAILED"
    if api_budget_state in API_BLOCKED_STATES or api_budget_state not in API_SAFE_STATES:
        return "SAFE_MODE_API_BUDGET_EXCEEDED"
    return "SAFE_MODE_CLEAR"


def evaluate_safe_mode_baseline(
    *,
    source_uri: str | None,
    processed_path: str | None,
    backup_path: str | None,
    manifest_path: str | None,
    report_export_path: str | None,
    ids_data_root: str | None = None,
    expected_path: str | None = None,
    previous_state: str | None = None,
    internal_total_bytes: int | None = None,
    internal_free_bytes: int | None = None,
    planned_output_bytes: int | None = None,
    job_kind: str = "bounded_preflight",
    require_external_root: bool | None = True,
    allow_real_disk_fallback: bool = True,
    min_free_gib: int = 100,
    warn_free_gib: int = 200,
    max_used_percent: int = 85,
    index_state: str | None = "OK",
    api_budget_state: str | None = "OK",
) -> dict[str, Any]:
    """Classify safe-mode state without starting services, reading data, or writing output."""

    normalized_index = _normalize_state(index_state, default="UNKNOWN")
    normalized_api = _normalize_state(api_budget_state, default="UNKNOWN")
    local_path = path_contract.evaluate_local_path_contract(
        source_uri=source_uri,
        processed_path=processed_path,
        backup_path=backup_path,
        manifest_path=manifest_path,
        report_export_path=report_export_path,
        ids_data_root=ids_data_root,
        expected_path=expected_path,
        previous_state=previous_state,
        internal_total_bytes=internal_total_bytes,
        internal_free_bytes=internal_free_bytes,
        planned_output_bytes=planned_output_bytes,
        job_kind=job_kind,
        require_external_root=require_external_root,
        allow_real_disk_fallback=allow_real_disk_fallback,
        min_free_gib=min_free_gib,
        warn_free_gib=warn_free_gib,
        max_used_percent=max_used_percent,
    )
    state = _map_safe_mode_state(local_path, normalized_index, normalized_api)
    safe_mode = state != "SAFE_MODE_CLEAR"
    upstream_actions = local_path.get("operator_actions", [])
    local_actions = STATE_OPERATOR_ACTIONS[state][:]
    if state == "SAFE_MODE_ROOT_NOT_CONFIGURED":
        upstream_actions = ["configure_ids_data_root", *upstream_actions]

    operator_actions = _merge_actions(local_actions, upstream_actions)
    requires_revalidation = safe_mode or local_path.get("requires_revalidation", False)
    requires_operator_confirmation = (
        safe_mode or local_path.get("requires_operator_confirmation", False)
    )

    return {
        "schema_version": "ids.stage011.safe_mode_baseline.v1",
        "stage": "STAGE-011",
        "phase": "Phase 2",
        "acceptance_id": "ACC-STAGE-011",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "state": state,
        "safe_mode": safe_mode,
        "auto_resume": False,
        "bounded_preflight_only": True,
        "paused_workflows": PAUSED_WORKFLOWS[:] if safe_mode else [],
        "operator_actions": operator_actions,
        "requires_operator_confirmation": requires_operator_confirmation,
        "requires_revalidation": requires_revalidation,
        "local_path_contract_state": local_path.get("state"),
        "storage_budget_state": local_path.get("storage_budget_state"),
        "removable_drive_state": local_path.get("removable_drive_state"),
        "index_state": normalized_index,
        "api_budget_state": normalized_api,
        "local_path_contract": local_path,
        "does_not_start_services": True,
        "does_not_create_ids_data_root": True,
        "does_not_scan_recursively": True,
        "does_not_scan_external_drive_contents": True,
        "does_not_open_source_files": True,
        "does_not_hash_source_files": True,
        "does_not_read_raw_metadata": True,
        "does_not_generate_outputs": True,
        "does_not_write_runtime_data": True,
        "does_not_write_manifests": True,
        "does_not_copy_backups": True,
        "does_not_call_external_apis": True,
    }


def _operations_only(report: dict[str, Any]) -> bool:
    return all(
        report.get(flag) is True
        for flag in [
            "does_not_start_services",
            "does_not_create_ids_data_root",
            "does_not_scan_recursively",
            "does_not_scan_external_drive_contents",
            "does_not_open_source_files",
            "does_not_hash_source_files",
            "does_not_read_raw_metadata",
            "does_not_generate_outputs",
            "does_not_write_runtime_data",
            "does_not_write_manifests",
            "does_not_copy_backups",
            "does_not_call_external_apis",
        ]
    )


def build_stage011_scenario_report(
    *,
    valid_source_uri: str,
    online_root: str,
    offline_root: str,
    reconnected_root: str,
    permission_denied_root: str,
    path_changed_current: str,
    path_changed_expected: str,
    processed_path: str,
    backup_path: str,
    manifest_path: str,
    report_export_path: str,
    storage_total_bytes: int,
    storage_ok_free_bytes: int,
    storage_low_free_bytes: int,
    planned_output_ok_bytes: int,
    planned_output_too_large_bytes: int,
    invalid_source_uri: str,
) -> dict[str, Any]:
    """Build deterministic Phase 3 safe-mode scenarios without side effects."""

    common = {
        "source_uri": valid_source_uri,
        "processed_path": processed_path,
        "backup_path": backup_path,
        "manifest_path": manifest_path,
        "report_export_path": report_export_path,
        "internal_total_bytes": storage_total_bytes,
        "internal_free_bytes": storage_ok_free_bytes,
        "planned_output_bytes": planned_output_ok_bytes,
        "job_kind": "bounded_preflight",
        "index_state": "OK",
        "api_budget_state": "OK",
    }
    scenarios = {
        "clear": evaluate_safe_mode_baseline(
            ids_data_root=online_root,
            **common,
        ),
        "drive_offline": evaluate_safe_mode_baseline(
            ids_data_root=offline_root,
            **common,
        ),
        "drive_reconnected": evaluate_safe_mode_baseline(
            ids_data_root=reconnected_root,
            previous_state="OFFLINE",
            **common,
        ),
        "permission_denied": evaluate_safe_mode_baseline(
            ids_data_root=permission_denied_root,
            **common,
        ),
        "path_changed": evaluate_safe_mode_baseline(
            ids_data_root=path_changed_current,
            expected_path=path_changed_expected,
            **common,
        ),
        "storage_low_free": evaluate_safe_mode_baseline(
            ids_data_root=online_root,
            source_uri=valid_source_uri,
            processed_path=processed_path,
            backup_path=backup_path,
            manifest_path=manifest_path,
            report_export_path=report_export_path,
            internal_total_bytes=storage_total_bytes,
            internal_free_bytes=storage_low_free_bytes,
            planned_output_bytes=planned_output_ok_bytes,
            job_kind="bounded_preflight",
            index_state="OK",
            api_budget_state="OK",
        ),
        "unbounded_output_missing_cap": evaluate_safe_mode_baseline(
            ids_data_root=online_root,
            source_uri=valid_source_uri,
            processed_path=processed_path,
            backup_path=backup_path,
            manifest_path=manifest_path,
            report_export_path=report_export_path,
            internal_total_bytes=storage_total_bytes,
            internal_free_bytes=storage_ok_free_bytes,
            planned_output_bytes=None,
            job_kind="embedding",
            index_state="OK",
            api_budget_state="OK",
        ),
        "path_blocked": evaluate_safe_mode_baseline(
            ids_data_root=online_root,
            source_uri=invalid_source_uri,
            processed_path=processed_path,
            backup_path=backup_path,
            manifest_path=manifest_path,
            report_export_path=report_export_path,
            internal_total_bytes=storage_total_bytes,
            internal_free_bytes=storage_ok_free_bytes,
            planned_output_bytes=planned_output_ok_bytes,
            job_kind="bounded_preflight",
            index_state="OK",
            api_budget_state="OK",
        ),
        "index_failed": evaluate_safe_mode_baseline(
            ids_data_root=online_root,
            source_uri=valid_source_uri,
            processed_path=processed_path,
            backup_path=backup_path,
            manifest_path=manifest_path,
            report_export_path=report_export_path,
            internal_total_bytes=storage_total_bytes,
            internal_free_bytes=storage_ok_free_bytes,
            planned_output_bytes=planned_output_ok_bytes,
            job_kind="bounded_preflight",
            index_state="FAILED",
            api_budget_state="OK",
        ),
        "api_budget_exceeded": evaluate_safe_mode_baseline(
            ids_data_root=online_root,
            source_uri=valid_source_uri,
            processed_path=processed_path,
            backup_path=backup_path,
            manifest_path=manifest_path,
            report_export_path=report_export_path,
            internal_total_bytes=storage_total_bytes,
            internal_free_bytes=storage_ok_free_bytes,
            planned_output_bytes=planned_output_ok_bytes,
            job_kind="bounded_preflight",
            index_state="OK",
            api_budget_state="EXCEEDED",
        ),
    }
    expected_states = {
        "clear": "SAFE_MODE_CLEAR",
        "drive_offline": "SAFE_MODE_DRIVE_OFFLINE",
        "drive_reconnected": "SAFE_MODE_REVALIDATION_REQUIRED",
        "permission_denied": "SAFE_MODE_PERMISSION_DENIED",
        "path_changed": "SAFE_MODE_REVALIDATION_REQUIRED",
        "storage_low_free": "SAFE_MODE_STORAGE_BLOCKED",
        "unbounded_output_missing_cap": "SAFE_MODE_STORAGE_BLOCKED",
        "path_blocked": "SAFE_MODE_PATH_BLOCKED",
        "index_failed": "SAFE_MODE_INDEX_FAILED",
        "api_budget_exceeded": "SAFE_MODE_API_BUDGET_EXCEEDED",
    }
    scenario_states = {name: report["state"] for name, report in scenarios.items()}
    blocked_names = [name for name, state in expected_states.items() if state != "SAFE_MODE_CLEAR"]
    blocked_valid = all(scenarios[name]["safe_mode"] for name in blocked_names)
    pause_valid = all(
        workflow in scenarios["drive_offline"]["paused_workflows"]
        for workflow in PAUSED_WORKFLOWS
    )
    no_auto_resume_valid = all(not scenarios[name]["auto_resume"] for name in scenarios)
    operations_only_valid = all(_operations_only(report) for report in scenarios.values())

    return {
        "schema_version": "ids.stage011.phase3_scenarios.v1",
        "stage": "STAGE-011",
        "phase": "Phase 3",
        "acceptance_id": "ACC-STAGE-011",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "overall_valid": (
            scenario_states == expected_states
            and blocked_valid
            and pause_valid
            and no_auto_resume_valid
            and operations_only_valid
        ),
        "scenario_states": scenario_states,
        "safe_mode_scenarios": scenarios,
        "safe_mode_pauses": PAUSED_WORKFLOWS[:],
        "does_not_start_services": True,
        "does_not_create_ids_data_root": True,
        "does_not_scan_recursively": True,
        "does_not_scan_external_drive_contents": True,
        "does_not_open_source_files": True,
        "does_not_hash_source_files": True,
        "does_not_read_raw_metadata": True,
        "does_not_generate_outputs": True,
        "does_not_write_runtime_data": True,
        "does_not_write_manifests": True,
        "does_not_copy_backups": True,
        "does_not_call_external_apis": True,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only IDS Stage 011 safe-mode baseline preflight."
    )
    parser.add_argument("--source-uri", required=True)
    parser.add_argument("--processed-path", required=True)
    parser.add_argument("--backup-path", required=True)
    parser.add_argument("--manifest-path", required=True)
    parser.add_argument("--report-export-path", required=True)
    parser.add_argument("--ids-data-root", default=os.environ.get("IDS_DATA_ROOT"))
    parser.add_argument("--expected-path", default=None)
    parser.add_argument("--previous-state", default=None)
    parser.add_argument("--internal-total-gib", type=float, default=None)
    parser.add_argument("--internal-free-gib", type=float, default=None)
    parser.add_argument("--planned-output-gib", type=float, default=None)
    parser.add_argument("--job-kind", default="bounded_preflight")
    parser.add_argument("--min-free-gib", type=int, default=100)
    parser.add_argument("--warn-free-gib", type=int, default=200)
    parser.add_argument("--max-used-percent", type=int, default=85)
    parser.add_argument("--index-state", default="OK")
    parser.add_argument("--api-budget-state", default="OK")
    parser.add_argument("--no-real-disk-fallback", action="store_true")
    external = parser.add_mutually_exclusive_group()
    external.add_argument("--require-external-root", action="store_true")
    external.add_argument("--no-require-external-root", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    require_external_root = True
    if args.require_external_root:
        require_external_root = True
    if args.no_require_external_root:
        require_external_root = False

    report = evaluate_safe_mode_baseline(
        source_uri=args.source_uri,
        processed_path=args.processed_path,
        backup_path=args.backup_path,
        manifest_path=args.manifest_path,
        report_export_path=args.report_export_path,
        ids_data_root=args.ids_data_root,
        expected_path=args.expected_path,
        previous_state=args.previous_state,
        internal_total_bytes=_gib_to_bytes(args.internal_total_gib),
        internal_free_bytes=_gib_to_bytes(args.internal_free_gib),
        planned_output_bytes=_gib_to_bytes(args.planned_output_gib),
        job_kind=args.job_kind,
        require_external_root=require_external_root,
        allow_real_disk_fallback=not args.no_real_disk_fallback,
        min_free_gib=args.min_free_gib,
        warn_free_gib=args.warn_free_gib,
        max_used_percent=args.max_used_percent,
        index_state=args.index_state,
        api_budget_state=args.api_budget_state,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
