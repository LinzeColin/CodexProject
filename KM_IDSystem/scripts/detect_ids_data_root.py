#!/usr/bin/env python3
"""Read-only IDS_DATA_ROOT detector and top-level slot validator."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


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
ALL_SLOTS = [f"{index:02d}" for index in range(100)]


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _path_string(path: str | None) -> str | None:
    if path is None:
        return None
    return str(Path(path).expanduser())


def _slot_for_name(name: str) -> str | None:
    if len(name) == 2 and name.isdigit():
        return name
    if len(name) > 3 and name[:2].isdigit() and name[2] == "_":
        return name[:2]
    return None


def _common_report(
    state: str,
    *,
    configured_path: str | None,
    expected_path: str | None = None,
    reason: str,
    missing_slots: list[str] | None = None,
    duplicate_slots: list[str] | None = None,
    malformed_entries: list[str] | None = None,
    slot_directories: dict[str, str] | None = None,
) -> dict[str, Any]:
    safe_mode = state != "STRUCTURE_COMPLETE"
    missing_slots = missing_slots or []
    duplicate_slots = duplicate_slots or []
    malformed_entries = malformed_entries or []
    slot_directories = slot_directories or {}
    return {
        "schema_version": "ids.stage007.ids_data_root_detector.v1",
        "stage": "STAGE-007",
        "acceptance_id": "ACC-STAGE-007",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "state": state,
        "safe_mode": safe_mode,
        "paused_workflows": PAUSED_WORKFLOWS[:] if safe_mode else [],
        "configured_path": _path_string(configured_path),
        "expected_path": _path_string(expected_path),
        "reason": reason,
        "missing_slots": missing_slots,
        "duplicate_slots": duplicate_slots,
        "malformed_entries": malformed_entries,
        "slot_count": len(slot_directories),
        "slot_directories": slot_directories,
        "raw_material_slot": {
            "slot": "00",
            "present": "00" in slot_directories,
            "path": slot_directories.get("00"),
            "policy": "read_only_required",
        },
        "requires_operator_confirmation": state in {
            "PATH_CHANGED",
            "DUPLICATE_NUMERIC_SLOT",
            "MALFORMED_TOP_LEVEL_ENTRY",
            "UNKNOWN",
        },
        "requires_revalidation": state in {
            "RECONNECTED",
            "PATH_CHANGED",
            "ROOT_ABSENT",
            "ROOT_PERMISSION_DENIED",
            "UNKNOWN",
        },
        "does_not_start_services": True,
        "does_not_create_ids_data_root": True,
        "does_not_scan_recursively": True,
    }


def detect_ids_data_root(
    configured_path: str | None,
    *,
    expected_path: str | None = None,
    previous_state: str | None = None,
) -> dict[str, Any]:
    """Validate IDS_DATA_ROOT with top-level-only read checks."""

    configured_path = _normalize_optional(configured_path)
    expected_path = _normalize_optional(expected_path)
    previous_state = _normalize_optional(previous_state)

    if configured_path is None:
        return _common_report(
            "NOT_CONFIGURED",
            configured_path=None,
            expected_path=expected_path,
            reason="IDS_DATA_ROOT is not configured.",
        )

    configured = Path(configured_path).expanduser()
    if expected_path is not None:
        expected = Path(expected_path).expanduser()
        if configured != expected:
            return _common_report(
                "PATH_CHANGED",
                configured_path=str(configured),
                expected_path=str(expected),
                reason="Configured IDS_DATA_ROOT does not match the expected path.",
            )

    try:
        exists = configured.exists()
    except OSError as exc:
        return _common_report(
            "UNKNOWN",
            configured_path=str(configured),
            expected_path=expected_path,
            reason=f"Unable to stat IDS_DATA_ROOT: {exc.__class__.__name__}",
        )

    if not exists:
        return _common_report(
            "ROOT_ABSENT",
            configured_path=str(configured),
            expected_path=expected_path,
            reason="Configured IDS_DATA_ROOT path is absent.",
        )
    if not configured.is_dir():
        return _common_report(
            "ROOT_NOT_DIRECTORY",
            configured_path=str(configured),
            expected_path=expected_path,
            reason="Configured IDS_DATA_ROOT path is not a directory.",
        )
    if not os.access(configured, os.R_OK | os.X_OK):
        return _common_report(
            "ROOT_PERMISSION_DENIED",
            configured_path=str(configured),
            expected_path=expected_path,
            reason="Configured IDS_DATA_ROOT is not readable and searchable.",
        )

    try:
        children = sorted(configured.iterdir(), key=lambda child: child.name)
    except OSError as exc:
        return _common_report(
            "UNKNOWN",
            configured_path=str(configured),
            expected_path=expected_path,
            reason=f"Unable to inspect IDS_DATA_ROOT top level: {exc.__class__.__name__}",
        )

    slots: dict[str, list[str]] = {}
    malformed_entries: list[str] = []
    for child in children:
        slot = _slot_for_name(child.name)
        if slot is None or not child.is_dir():
            malformed_entries.append(child.name)
            continue
        slots.setdefault(slot, []).append(child.name)

    slot_directories = {
        slot: names[0]
        for slot, names in sorted(slots.items())
        if len(names) == 1
    }
    duplicate_slots = [slot for slot, names in sorted(slots.items()) if len(names) > 1]
    missing_slots = [slot for slot in ALL_SLOTS if slot not in slots]

    if malformed_entries:
        state = "MALFORMED_TOP_LEVEL_ENTRY"
        reason = "One or more top-level entries are not valid numeric slot directories."
    elif duplicate_slots:
        state = "DUPLICATE_NUMERIC_SLOT"
        reason = "One or more numeric top-level slots appear more than once."
    elif missing_slots:
        state = "MISSING_NUMERIC_SLOTS"
        reason = "One or more numeric top-level slots are missing."
    else:
        state = "STRUCTURE_COMPLETE"
        reason = "All numeric top-level slots 00 through 99 are present exactly once."
        if previous_state in {"ROOT_ABSENT", "OFFLINE", "NOT_CONFIGURED", "UNKNOWN"}:
            state = "RECONNECTED"
            reason = "IDS_DATA_ROOT is structurally complete after a non-online prior state."

    return _common_report(
        state,
        configured_path=str(configured),
        expected_path=expected_path,
        reason=reason,
        missing_slots=missing_slots,
        duplicate_slots=duplicate_slots,
        malformed_entries=malformed_entries,
        slot_directories=slot_directories,
    )


def evaluate_storage_guard(
    *,
    total_bytes: int,
    free_bytes: int,
    min_free_gib: int = 100,
    warn_free_gib: int = 200,
    max_used_percent: int = 85,
) -> dict[str, Any]:
    """Classify internal-disk pressure for Stage 007 scenario evidence."""

    gib = 1024**3
    total_gib = total_bytes / gib if total_bytes else 0
    free_gib = free_bytes / gib
    used_percent = 0.0 if total_bytes <= 0 else ((total_bytes - free_bytes) / total_bytes) * 100
    reasons: list[str] = []

    if total_bytes <= 0 or free_bytes < 0:
        state = "UNKNOWN"
        reasons.append("internal_disk_unknown")
    elif free_gib < min_free_gib:
        state = "BLOCKED"
        reasons.append("internal_disk_low_free_space")
    elif used_percent >= max_used_percent:
        state = "BLOCKED"
        reasons.append("internal_disk_high_waterline")
    elif free_gib < warn_free_gib:
        state = "WARN"
        reasons.append("internal_disk_free_space_warning")
    else:
        state = "OK"

    return {
        "state": state,
        "safe_mode": state in {"BLOCKED", "UNKNOWN"},
        "reasons": reasons,
        "total_gib": round(total_gib, 2),
        "free_gib": round(free_gib, 2),
        "used_percent": round(used_percent, 2),
        "min_free_gib": min_free_gib,
        "warn_free_gib": warn_free_gib,
        "max_used_percent": max_used_percent,
    }


def build_stage007_scenario_report(
    *,
    complete_root: str,
    absent_root: str,
    reconnected_root: str,
    permission_denied_root: str,
    path_changed_current: str,
    path_changed_expected: str,
    not_directory_path: str,
    missing_root: str,
    duplicate_root: str,
    malformed_root: str,
    storage_total_bytes: int,
    storage_ok_free_bytes: int,
    storage_low_free_bytes: int,
    storage_high_used_free_bytes: int,
    min_free_gib: int = 100,
    warn_free_gib: int = 200,
    max_used_percent: int = 85,
) -> dict[str, Any]:
    """Build a deterministic Stage 007 scenario matrix without raw-data scans."""

    ids_data_root_scenarios = {
        "complete": detect_ids_data_root(complete_root),
        "absent": detect_ids_data_root(absent_root),
        "reconnected": detect_ids_data_root(
            reconnected_root,
            previous_state="ROOT_ABSENT",
        ),
        "permission_denied": detect_ids_data_root(permission_denied_root),
        "path_changed": detect_ids_data_root(
            path_changed_current,
            expected_path=path_changed_expected,
        ),
        "not_directory": detect_ids_data_root(not_directory_path),
        "missing_slots": detect_ids_data_root(missing_root),
        "duplicate_slots": detect_ids_data_root(duplicate_root),
        "malformed_entries": detect_ids_data_root(malformed_root),
    }
    storage_scenarios = {
        "ok": evaluate_storage_guard(
            total_bytes=storage_total_bytes,
            free_bytes=storage_ok_free_bytes,
            min_free_gib=min_free_gib,
            warn_free_gib=warn_free_gib,
            max_used_percent=max_used_percent,
        ),
        "low_free_space": evaluate_storage_guard(
            total_bytes=storage_total_bytes,
            free_bytes=storage_low_free_bytes,
            min_free_gib=min_free_gib,
            warn_free_gib=warn_free_gib,
            max_used_percent=max_used_percent,
        ),
        "high_waterline": evaluate_storage_guard(
            total_bytes=storage_total_bytes,
            free_bytes=storage_high_used_free_bytes,
            min_free_gib=min_free_gib,
            warn_free_gib=warn_free_gib,
            max_used_percent=max_used_percent,
        ),
    }
    expected_root_states = {
        "complete": "STRUCTURE_COMPLETE",
        "absent": "ROOT_ABSENT",
        "reconnected": "RECONNECTED",
        "permission_denied": "ROOT_PERMISSION_DENIED",
        "path_changed": "PATH_CHANGED",
        "not_directory": "ROOT_NOT_DIRECTORY",
        "missing_slots": "MISSING_NUMERIC_SLOTS",
        "duplicate_slots": "DUPLICATE_NUMERIC_SLOT",
        "malformed_entries": "MALFORMED_TOP_LEVEL_ENTRY",
    }
    expected_storage_states = {
        "ok": "OK",
        "low_free_space": "BLOCKED",
        "high_waterline": "BLOCKED",
    }
    root_valid = all(
        ids_data_root_scenarios[name]["state"] == state
        for name, state in expected_root_states.items()
    )
    storage_valid = all(
        storage_scenarios[name]["state"] == state
        for name, state in expected_storage_states.items()
    )

    return {
        "schema_version": "ids.stage007.phase3_scenarios.v1",
        "stage": "STAGE-007",
        "acceptance_id": "ACC-STAGE-007",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "ids_data_root_scenarios": ids_data_root_scenarios,
        "storage_scenarios": storage_scenarios,
        "safe_mode_pauses": PAUSED_WORKFLOWS[:],
        "overall_valid": root_valid and storage_valid,
        "does_not_start_services": True,
        "does_not_create_ids_data_root": True,
        "does_not_scan_recursively": True,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only IDS_DATA_ROOT top-level structure detector."
    )
    parser.add_argument("--ids-data-root", default=os.environ.get("IDS_DATA_ROOT"))
    parser.add_argument("--expected-path", default=None)
    parser.add_argument("--previous-state", default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = detect_ids_data_root(
        args.ids_data_root,
        expected_path=args.expected_path,
        previous_state=args.previous_state,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
