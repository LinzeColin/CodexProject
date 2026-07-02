#!/usr/bin/env python3
"""Read-only IDS local environment and storage-root baseline check."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any


OPERATIONS_ENTRANCE = "IDS 系统运营入口"
PAUSED_WORKFLOWS = [
    "bulk_import",
    "ocr",
    "embedding",
    "index_rebuild",
    "batch_report_generation",
    "raw_material_cleanup",
]
SAFE_MODE_STATES = {
    "NOT_CONFIGURED",
    "OFFLINE",
    "RECONNECTED",
    "PERMISSION_DENIED",
    "PATH_CHANGED",
    "UNKNOWN",
}


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _path_string(path: str | None) -> str | None:
    if path is None:
        return None
    return str(Path(path).expanduser())


def _safe_common_fields(state: str) -> dict[str, Any]:
    safe_mode = state in SAFE_MODE_STATES
    return {
        "state": state,
        "safe_mode": safe_mode,
        "paused_workflows": PAUSED_WORKFLOWS[:] if safe_mode else [],
        "requires_operator_confirmation": state in {"PATH_CHANGED", "UNKNOWN"},
        "requires_revalidation": state in {"RECONNECTED", "PATH_CHANGED", "UNKNOWN"},
    }


def evaluate_ids_data_root(
    configured_path: str | None,
    *,
    expected_path: str | None = None,
    previous_state: str | None = None,
) -> dict[str, Any]:
    """Classify IDS_DATA_ROOT without creating, listing, moving, or deleting files."""

    configured_path = _normalize_optional(configured_path)
    expected_path = _normalize_optional(expected_path)
    previous_state = _normalize_optional(previous_state)

    if configured_path is None:
        report = _safe_common_fields("NOT_CONFIGURED")
        report.update(
            {
                "configured_path": None,
                "expected_path": _path_string(expected_path),
                "reason": "IDS_DATA_ROOT is not configured.",
            }
        )
        return report

    configured = Path(configured_path).expanduser()
    if expected_path is not None:
        expected = Path(expected_path).expanduser()
        if configured != expected:
            report = _safe_common_fields("PATH_CHANGED")
            report.update(
                {
                    "configured_path": str(configured),
                    "expected_path": str(expected),
                    "reason": "Configured IDS_DATA_ROOT does not match the expected path.",
                }
            )
            return report

    try:
        exists = configured.exists()
    except OSError as exc:
        report = _safe_common_fields("UNKNOWN")
        report.update(
            {
                "configured_path": str(configured),
                "expected_path": _path_string(expected_path),
                "reason": f"Unable to stat IDS_DATA_ROOT: {exc.__class__.__name__}",
            }
        )
        return report

    if not exists:
        report = _safe_common_fields("OFFLINE")
        report.update(
            {
                "configured_path": str(configured),
                "expected_path": _path_string(expected_path),
                "reason": "Configured IDS_DATA_ROOT path is absent.",
            }
        )
        return report

    if not os.access(configured, os.R_OK | os.X_OK):
        report = _safe_common_fields("PERMISSION_DENIED")
        report.update(
            {
                "configured_path": str(configured),
                "expected_path": _path_string(expected_path),
                "reason": "Configured IDS_DATA_ROOT is not readable and searchable.",
            }
        )
        return report

    if previous_state in {"OFFLINE", "NOT_CONFIGURED", "UNKNOWN"}:
        report = _safe_common_fields("RECONNECTED")
        report.update(
            {
                "configured_path": str(configured),
                "expected_path": _path_string(expected_path),
                "reason": "IDS_DATA_ROOT is present after a non-online prior state.",
            }
        )
        return report

    report = _safe_common_fields("ONLINE")
    report.update(
        {
            "configured_path": str(configured),
            "expected_path": _path_string(expected_path),
            "reason": "Configured IDS_DATA_ROOT path is present and readable.",
        }
    )
    return report


def evaluate_storage_budget(
    *,
    total_bytes: int,
    free_bytes: int,
    min_free_gib: int = 100,
    warn_free_gib: int = 200,
    max_used_percent: int = 85,
) -> dict[str, Any]:
    """Classify internal-disk space without creating files."""

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


def _run_version_command(args: list[str]) -> dict[str, Any]:
    if shutil.which(args[0]) is None:
        return {"available": False, "output": None}
    try:
        result = subprocess.run(
            args,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": False, "output": f"{exc.__class__.__name__}: {exc}"}
    return {
        "available": result.returncode == 0,
        "output": result.stdout.strip(),
        "returncode": result.returncode,
    }


def build_report(
    *,
    ids_data_root: str | None,
    expected_path: str | None = None,
    previous_state: str | None = None,
    internal_total_bytes: int | None = None,
    internal_free_bytes: int | None = None,
    min_free_gib: int = 100,
    warn_free_gib: int = 200,
    max_used_percent: int = 85,
) -> dict[str, Any]:
    if internal_total_bytes is None or internal_free_bytes is None:
        usage = shutil.disk_usage("/")
        internal_total_bytes = usage.total
        internal_free_bytes = usage.free

    ids_root_report = evaluate_ids_data_root(
        ids_data_root,
        expected_path=expected_path,
        previous_state=previous_state,
    )
    storage_report = evaluate_storage_budget(
        total_bytes=internal_total_bytes,
        free_bytes=internal_free_bytes,
        min_free_gib=min_free_gib,
        warn_free_gib=warn_free_gib,
        max_used_percent=max_used_percent,
    )

    return {
        "schema_version": "ids.stage006.environment_baseline.v1",
        "stage": "STAGE-006",
        "acceptance_id": "ACC-STAGE-006",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "docker": {
            "cli": _run_version_command(["docker", "--version"]),
            "compose": _run_version_command(["docker", "compose", "version"]),
        },
        "ids_data_root": ids_root_report,
        "internal_storage": storage_report,
        "safe_mode": ids_root_report["safe_mode"] or storage_report["safe_mode"],
        "does_not_start_services": True,
        "does_not_create_ids_data_root": True,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only IDS macOS/Docker/storage baseline check."
    )
    parser.add_argument("--ids-data-root", default=os.environ.get("IDS_DATA_ROOT"))
    parser.add_argument("--expected-path", default=None)
    parser.add_argument("--previous-state", default=None)
    parser.add_argument("--internal-total-gib", type=float, default=None)
    parser.add_argument("--internal-free-gib", type=float, default=None)
    parser.add_argument("--min-free-gib", type=int, default=100)
    parser.add_argument("--warn-free-gib", type=int, default=200)
    parser.add_argument("--max-used-percent", type=int, default=85)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    gib = 1024**3
    total_bytes = int(args.internal_total_gib * gib) if args.internal_total_gib is not None else None
    free_bytes = int(args.internal_free_gib * gib) if args.internal_free_gib is not None else None
    report = build_report(
        ids_data_root=args.ids_data_root,
        expected_path=args.expected_path,
        previous_state=args.previous_state,
        internal_total_bytes=total_bytes,
        internal_free_bytes=free_bytes,
        min_free_gib=args.min_free_gib,
        warn_free_gib=args.warn_free_gib,
        max_used_percent=args.max_used_percent,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
