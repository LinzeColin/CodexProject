#!/usr/bin/env python3
"""Read-only removable-drive lifecycle state machine for IDS operations."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KM_IDSystem.scripts import detect_ids_data_root as root_detector


OPERATIONS_ENTRANCE = "IDS 系统运营入口"
PAUSED_WORKFLOWS = [
    "bulk_import",
    "recursive_directory_scanning",
    "raw_material_cleanup",
    "ocr",
    "embedding",
    "index_rebuild",
    "batch_report_generation",
]

STATE_OPERATOR_ACTIONS = {
    "NOT_CONFIGURED": ["configure_ids_data_root"],
    "OFFLINE": ["reconnect_external_drive", "rerun_preflight"],
    "RECONNECTED_NEEDS_REVALIDATION": ["revalidate_path_permission_structure"],
    "PATH_CHANGED": ["confirm_expected_path", "rerun_preflight"],
    "PERMISSION_DENIED": ["fix_filesystem_permissions", "rerun_preflight"],
    "STRUCTURE_INVALID": ["repair_or_migrate_top_level_structure", "rerun_preflight"],
    "STORAGE_BLOCKED": ["free_internal_disk_space", "rerun_preflight"],
    "UNKNOWN": ["manual_operator_review", "rerun_preflight"],
    "ONLINE_VALIDATED": ["bounded_preflight_only"],
}


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _storage_report(
    *,
    storage_total_bytes: int | None,
    storage_free_bytes: int | None,
    min_free_gib: int,
    warn_free_gib: int,
    max_used_percent: int,
) -> dict[str, Any]:
    if storage_total_bytes is None or storage_free_bytes is None:
        usage = shutil.disk_usage("/")
        storage_total_bytes = usage.total
        storage_free_bytes = usage.free
    return root_detector.evaluate_storage_guard(
        total_bytes=storage_total_bytes,
        free_bytes=storage_free_bytes,
        min_free_gib=min_free_gib,
        warn_free_gib=warn_free_gib,
        max_used_percent=max_used_percent,
    )


def _map_root_state(root_state: str) -> str:
    if root_state == "ROOT_ABSENT":
        return "OFFLINE"
    if root_state == "RECONNECTED":
        return "RECONNECTED_NEEDS_REVALIDATION"
    if root_state == "ROOT_PERMISSION_DENIED":
        return "PERMISSION_DENIED"
    if root_state in {
        "ROOT_NOT_DIRECTORY",
        "MISSING_NUMERIC_SLOTS",
        "DUPLICATE_NUMERIC_SLOT",
        "MALFORMED_TOP_LEVEL_ENTRY",
    }:
        return "STRUCTURE_INVALID"
    if root_state == "STRUCTURE_COMPLETE":
        return "ONLINE_VALIDATED"
    return root_state


def evaluate_removable_drive_state(
    ids_data_root: str | None,
    *,
    expected_path: str | None = None,
    previous_state: str | None = None,
    storage_total_bytes: int | None = None,
    storage_free_bytes: int | None = None,
    min_free_gib: int = 100,
    warn_free_gib: int = 200,
    max_used_percent: int = 85,
) -> dict[str, Any]:
    """Classify removable-drive lifecycle state without mutating storage."""

    ids_data_root = _normalize_optional(ids_data_root)
    expected_path = _normalize_optional(expected_path)
    previous_state = _normalize_optional(previous_state)

    root_report = root_detector.detect_ids_data_root(
        ids_data_root,
        expected_path=expected_path,
        previous_state=previous_state,
    )
    storage = _storage_report(
        storage_total_bytes=storage_total_bytes,
        storage_free_bytes=storage_free_bytes,
        min_free_gib=min_free_gib,
        warn_free_gib=warn_free_gib,
        max_used_percent=max_used_percent,
    )

    state = _map_root_state(root_report["state"])
    if state == "ONLINE_VALIDATED" and storage["state"] in {"BLOCKED", "UNKNOWN"}:
        state = "STORAGE_BLOCKED"

    safe_mode = state != "ONLINE_VALIDATED"
    resume_allowed = state == "ONLINE_VALIDATED"
    requires_revalidation = state in {
        "RECONNECTED_NEEDS_REVALIDATION",
        "PATH_CHANGED",
        "PERMISSION_DENIED",
        "UNKNOWN",
    }
    requires_operator_confirmation = state in {
        "PATH_CHANGED",
        "STRUCTURE_INVALID",
        "UNKNOWN",
    }

    return {
        "schema_version": "ids.stage008.removable_drive_state.v1",
        "stage": "STAGE-008",
        "acceptance_id": "ACC-STAGE-008",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "state": state,
        "safe_mode": safe_mode,
        "resume_allowed": resume_allowed,
        "auto_resume": False,
        "bounded_preflight_only": True,
        "paused_workflows": PAUSED_WORKFLOWS[:] if safe_mode else [],
        "operator_actions": STATE_OPERATOR_ACTIONS[state][:],
        "requires_operator_confirmation": requires_operator_confirmation,
        "requires_revalidation": requires_revalidation,
        "root_detector_state": root_report["state"],
        "storage_state": storage["state"],
        "root_detector": root_report,
        "storage": storage,
        "does_not_start_services": True,
        "does_not_create_ids_data_root": True,
        "does_not_scan_recursively": True,
        "does_not_scan_external_drive_contents": True,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only IDS removable-drive lifecycle state check."
    )
    parser.add_argument("--ids-data-root", default=os.environ.get("IDS_DATA_ROOT"))
    parser.add_argument("--expected-path", default=None)
    parser.add_argument("--previous-state", default=None)
    parser.add_argument("--storage-total-gib", type=float, default=None)
    parser.add_argument("--storage-free-gib", type=float, default=None)
    parser.add_argument("--min-free-gib", type=int, default=100)
    parser.add_argument("--warn-free-gib", type=int, default=200)
    parser.add_argument("--max-used-percent", type=int, default=85)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    gib = 1024**3
    total_bytes = int(args.storage_total_gib * gib) if args.storage_total_gib is not None else None
    free_bytes = int(args.storage_free_gib * gib) if args.storage_free_gib is not None else None
    report = evaluate_removable_drive_state(
        args.ids_data_root,
        expected_path=args.expected_path,
        previous_state=args.previous_state,
        storage_total_bytes=total_bytes,
        storage_free_bytes=free_bytes,
        min_free_gib=args.min_free_gib,
        warn_free_gib=args.warn_free_gib,
        max_used_percent=args.max_used_percent,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
