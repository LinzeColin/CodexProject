#!/usr/bin/env python3
"""Read-only Stage 009 storage-budget preflight for IDS operations."""

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

from KM_IDSystem.scripts import check_removable_drive_state as removable_drive
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
EXTERNAL_ROOT_REQUIRED_JOBS = {
    "bulk_import",
    "recursive_directory_scanning",
    "raw_material_cleanup",
    "ocr",
    "embedding",
    "index_rebuild",
    "batch_report_generation",
}
DECLARED_OUTPUT_REQUIRED_JOBS = {
    "ocr",
    "embedding",
    "index_rebuild",
    "batch_report_generation",
    "raw_material_cleanup",
}
SAFE_MODE_STATES = {
    "BUDGET_BLOCKED_LOW_FREE",
    "BUDGET_BLOCKED_HIGH_WATERLINE",
    "BUDGET_UNKNOWN",
    "EXTERNAL_ROOT_NOT_READY",
    "UNBOUNDED_OUTPUT_RISK",
}
STATE_OPERATOR_ACTIONS = {
    "BUDGET_OK": ["bounded_preflight_only"],
    "BUDGET_WARN": ["operator_review_before_large_job"],
    "BUDGET_BLOCKED_LOW_FREE": ["free_internal_disk_space", "rerun_storage_budget_preflight"],
    "BUDGET_BLOCKED_HIGH_WATERLINE": [
        "reduce_internal_disk_usage",
        "rerun_storage_budget_preflight",
    ],
    "BUDGET_UNKNOWN": ["manual_operator_review", "rerun_storage_budget_preflight"],
    "EXTERNAL_ROOT_NOT_READY": [
        "reconnect_or_configure_ids_data_root",
        "rerun_storage_budget_preflight",
    ],
    "UNBOUNDED_OUTPUT_RISK": ["declare_output_budget_or_cap", "rerun_storage_budget_preflight"],
}


def _gib_to_bytes(value: float | None) -> int | None:
    if value is None:
        return None
    return int(value * 1024**3)


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _default_external_requirement(job_kind: str) -> bool:
    return job_kind in EXTERNAL_ROOT_REQUIRED_JOBS


def _empty_unknown_storage_report(
    *,
    min_free_gib: int,
    warn_free_gib: int,
    max_used_percent: int,
) -> dict[str, Any]:
    return {
        "state": "UNKNOWN",
        "safe_mode": True,
        "reasons": ["internal_disk_unknown"],
        "total_gib": 0,
        "free_gib": 0,
        "used_percent": 0,
        "min_free_gib": min_free_gib,
        "warn_free_gib": warn_free_gib,
        "max_used_percent": max_used_percent,
    }


def _internal_storage_report(
    *,
    internal_total_bytes: int | None,
    internal_free_bytes: int | None,
    allow_real_disk_fallback: bool,
    min_free_gib: int,
    warn_free_gib: int,
    max_used_percent: int,
) -> dict[str, Any]:
    if internal_total_bytes is None or internal_free_bytes is None:
        if not allow_real_disk_fallback:
            return _empty_unknown_storage_report(
                min_free_gib=min_free_gib,
                warn_free_gib=warn_free_gib,
                max_used_percent=max_used_percent,
            )
        usage = shutil.disk_usage("/")
        internal_total_bytes = usage.total
        internal_free_bytes = usage.free

    return root_detector.evaluate_storage_guard(
        total_bytes=internal_total_bytes,
        free_bytes=internal_free_bytes,
        min_free_gib=min_free_gib,
        warn_free_gib=warn_free_gib,
        max_used_percent=max_used_percent,
    )


def _storage_guard_to_budget_state(storage: dict[str, Any]) -> str:
    if storage["state"] == "UNKNOWN":
        return "BUDGET_UNKNOWN"
    if storage["state"] == "BLOCKED":
        reasons = set(storage.get("reasons", []))
        if "internal_disk_low_free_space" in reasons:
            return "BUDGET_BLOCKED_LOW_FREE"
        if "internal_disk_high_waterline" in reasons:
            return "BUDGET_BLOCKED_HIGH_WATERLINE"
        return "BUDGET_UNKNOWN"
    if storage["state"] == "WARN":
        return "BUDGET_WARN"
    return "BUDGET_OK"


def _planned_output_report(
    *,
    planned_output_bytes: int | None,
    job_kind: str,
    internal_storage: dict[str, Any],
    min_free_gib: int,
) -> dict[str, Any]:
    if planned_output_bytes is None:
        if job_kind in DECLARED_OUTPUT_REQUIRED_JOBS:
            return {
                "state": "UNBOUNDED_OUTPUT_RISK",
                "planned_output_gib": None,
                "reason": "Job requires a declared output budget or cap.",
            }
        return {
            "state": "DECLARED_NOT_REQUIRED",
            "planned_output_gib": None,
            "reason": "This job kind does not require a declared output budget in Phase 2.",
        }

    gib = 1024**3
    planned_output_gib = round(planned_output_bytes / gib, 2)
    if planned_output_bytes < 0:
        return {
            "state": "UNBOUNDED_OUTPUT_RISK",
            "planned_output_gib": planned_output_gib,
            "reason": "Planned output budget cannot be negative.",
        }

    free_after_planned_gib = internal_storage["free_gib"] - planned_output_gib
    if free_after_planned_gib < min_free_gib:
        return {
            "state": "UNBOUNDED_OUTPUT_RISK",
            "planned_output_gib": planned_output_gib,
            "free_after_planned_gib": round(free_after_planned_gib, 2),
            "reason": "Planned output would cross the hard minimum free-space budget.",
        }

    return {
        "state": "DECLARED_BOUNDED",
        "planned_output_gib": planned_output_gib,
        "free_after_planned_gib": round(free_after_planned_gib, 2),
        "reason": "Planned output stays inside the declared storage budget.",
    }


def evaluate_storage_budget(
    *,
    ids_data_root: str | None = None,
    expected_path: str | None = None,
    previous_state: str | None = None,
    internal_total_bytes: int | None = None,
    internal_free_bytes: int | None = None,
    planned_output_bytes: int | None = None,
    job_kind: str = "bounded_preflight",
    require_external_root: bool | None = None,
    allow_real_disk_fallback: bool = True,
    min_free_gib: int = 100,
    warn_free_gib: int = 200,
    max_used_percent: int = 85,
) -> dict[str, Any]:
    """Classify storage budget without creating roots, outputs, or scans."""

    ids_data_root = _normalize_optional(ids_data_root)
    expected_path = _normalize_optional(expected_path)
    previous_state = _normalize_optional(previous_state)
    job_kind = _normalize_optional(job_kind) or "bounded_preflight"
    external_required = (
        _default_external_requirement(job_kind)
        if require_external_root is None
        else require_external_root
    )
    internal_storage = _internal_storage_report(
        internal_total_bytes=internal_total_bytes,
        internal_free_bytes=internal_free_bytes,
        allow_real_disk_fallback=allow_real_disk_fallback,
        min_free_gib=min_free_gib,
        warn_free_gib=warn_free_gib,
        max_used_percent=max_used_percent,
    )
    removable_report = None
    if external_required:
        removable_report = removable_drive.evaluate_removable_drive_state(
            ids_data_root,
            expected_path=expected_path,
            previous_state=previous_state,
            storage_total_bytes=internal_total_bytes,
            storage_free_bytes=internal_free_bytes,
            min_free_gib=min_free_gib,
            warn_free_gib=warn_free_gib,
            max_used_percent=max_used_percent,
        )

    planned_output = _planned_output_report(
        planned_output_bytes=planned_output_bytes,
        job_kind=job_kind,
        internal_storage=internal_storage,
        min_free_gib=min_free_gib,
    )
    state = _storage_guard_to_budget_state(internal_storage)
    if removable_report is not None and removable_report["state"] != "ONLINE_VALIDATED":
        state = "EXTERNAL_ROOT_NOT_READY"
    elif state in {"BUDGET_OK", "BUDGET_WARN"} and planned_output["state"] == "UNBOUNDED_OUTPUT_RISK":
        state = "UNBOUNDED_OUTPUT_RISK"

    safe_mode = state in SAFE_MODE_STATES
    large_jobs_require_review = state == "BUDGET_WARN"
    requires_operator_confirmation = large_jobs_require_review or state in SAFE_MODE_STATES

    return {
        "schema_version": "ids.stage009.storage_budget.v1",
        "stage": "STAGE-009",
        "acceptance_id": "ACC-STAGE-009",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "state": state,
        "safe_mode": safe_mode,
        "auto_resume": False,
        "bounded_preflight_only": True,
        "job_kind": job_kind,
        "requires_external_root": external_required,
        "requires_operator_confirmation": requires_operator_confirmation,
        "requires_revalidation": state in {"EXTERNAL_ROOT_NOT_READY", "BUDGET_UNKNOWN"},
        "large_jobs_require_review": large_jobs_require_review,
        "paused_workflows": PAUSED_WORKFLOWS[:] if safe_mode else [],
        "operator_actions": STATE_OPERATOR_ACTIONS[state][:],
        "budget_defaults": {
            "internal_min_free_gib": min_free_gib,
            "internal_warn_free_gib": warn_free_gib,
            "internal_max_used_percent": max_used_percent,
            "external_cold_root_nominal_tb": 5,
            "internal_budget_label_gb": 800,
        },
        "internal_storage": internal_storage,
        "planned_output": planned_output,
        "removable_drive_state": removable_report["state"] if removable_report else None,
        "removable_drive": removable_report,
        "does_not_start_services": True,
        "does_not_create_ids_data_root": True,
        "does_not_scan_recursively": True,
        "does_not_scan_external_drive_contents": True,
        "does_not_generate_outputs": True,
        "does_not_write_runtime_data": True,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only IDS Stage 009 storage-budget preflight."
    )
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
    parser.add_argument("--no-real-disk-fallback", action="store_true")
    external = parser.add_mutually_exclusive_group()
    external.add_argument("--require-external-root", action="store_true")
    external.add_argument("--no-require-external-root", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    require_external_root = None
    if args.require_external_root:
        require_external_root = True
    if args.no_require_external_root:
        require_external_root = False

    report = evaluate_storage_budget(
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
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
