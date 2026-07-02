#!/usr/bin/env python3
"""Read-only Stage 010 local path contract preflight for IDS operations."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KM_IDSystem.scripts import check_storage_budget as storage_budget


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
]
PATH_STATE_ORDER = [
    "SOURCE_URI_INVALID",
    "SOURCE_PATH_NOT_READY",
    "PROCESSED_PATH_UNBOUNDED",
    "BACKUP_PATH_UNSAFE",
    "MANIFEST_PATH_UNSAFE",
    "REPORT_EXPORT_PATH_UNSAFE",
    "PATH_CONTRACT_UNKNOWN",
]
ROLE_FAILURE_STATE = {
    "processed": "PROCESSED_PATH_UNBOUNDED",
    "backup": "BACKUP_PATH_UNSAFE",
    "manifest": "MANIFEST_PATH_UNSAFE",
    "report_export": "REPORT_EXPORT_PATH_UNSAFE",
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


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _parse_source_uri(source_uri: str | None) -> dict[str, Any]:
    source_uri = _normalize_optional(source_uri)
    if source_uri is None:
        return {
            "state": "SOURCE_URI_INVALID",
            "uri": None,
            "path": None,
            "reason": "source_uri is required.",
        }

    parsed = urlparse(source_uri)
    if parsed.scheme != "file":
        return {
            "state": "SOURCE_URI_INVALID",
            "uri": source_uri,
            "path": None,
            "reason": "source_uri must use the file:// scheme.",
        }
    if parsed.netloc not in {"", "localhost"}:
        return {
            "state": "SOURCE_URI_INVALID",
            "uri": source_uri,
            "path": None,
            "reason": "source_uri must point to a local file path.",
        }
    if not parsed.path:
        return {
            "state": "SOURCE_URI_INVALID",
            "uri": source_uri,
            "path": None,
            "reason": "source_uri path is missing.",
        }

    path = Path(unquote(parsed.path)).expanduser()
    if not path.is_absolute():
        return {
            "state": "SOURCE_URI_INVALID",
            "uri": source_uri,
            "path": str(path),
            "reason": "source_uri must normalize to an absolute local path.",
        }

    return {
        "state": "OK",
        "uri": source_uri,
        "path": str(_resolved(path)),
        "reason": "source_uri is a normalized local file URI.",
    }


def _classify_source_path(source: dict[str, Any]) -> dict[str, Any]:
    if source["state"] != "OK" or source["path"] is None:
        return source

    path = Path(source["path"])
    try:
        exists = path.exists()
    except OSError as exc:
        return {
            **source,
            "state": "SOURCE_PATH_NOT_READY",
            "reason": f"Unable to stat source path: {exc.__class__.__name__}",
        }
    if not exists:
        return {
            **source,
            "state": "SOURCE_PATH_NOT_READY",
            "reason": "source path is absent.",
        }
    if not os.access(path, os.R_OK):
        return {
            **source,
            "state": "SOURCE_PATH_NOT_READY",
            "reason": "source path is not readable.",
        }
    return source


def _classify_path_role(
    role: str,
    path_value: str | None,
    *,
    source_path: str | None,
    ids_data_root: str | None,
) -> dict[str, Any]:
    failure_state = ROLE_FAILURE_STATE[role]
    path_value = _normalize_optional(path_value)
    if path_value is None:
        return {
            "state": failure_state,
            "path": None,
            "reason": f"{role} path is required.",
        }

    path = Path(path_value).expanduser()
    if not path.is_absolute():
        return {
            "state": failure_state,
            "path": str(path),
            "reason": f"{role} path must be absolute.",
        }

    resolved_path = _resolved(path)
    source = _resolved(Path(source_path)) if source_path else None
    root = _resolved(Path(ids_data_root)) if _normalize_optional(ids_data_root) else None

    if source is not None:
        if resolved_path == source or _is_relative_to(resolved_path, source):
            return {
                "state": failure_state,
                "path": str(resolved_path),
                "reason": f"{role} path must not be the source path or inside the source path.",
            }
    if root is not None and _is_relative_to(resolved_path, root):
        return {
            "state": failure_state,
            "path": str(resolved_path),
            "reason": f"{role} path must not write inside IDS_DATA_ROOT in Stage 010 Phase 2.",
        }
    if role == "manifest" and resolved_path.suffix not in {".json", ".jsonl"}:
        return {
            "state": failure_state,
            "path": str(resolved_path),
            "reason": "manifest path must be a small JSON or JSONL metadata file.",
        }

    return {
        "state": "OK",
        "path": str(resolved_path),
        "reason": f"{role} path is declared and side-effect free in this preflight.",
    }


def _first_failure(*states: str) -> str:
    failures = [state for state in states if state != "OK" and state != "PATH_CONTRACT_OK"]
    if not failures:
        return "PATH_CONTRACT_OK"
    for preferred in PATH_STATE_ORDER:
        if preferred in failures:
            return preferred
    return failures[0] if failures else "PATH_CONTRACT_OK"


def _merge_actions(*action_lists: list[str]) -> list[str]:
    merged: list[str] = []
    for actions in action_lists:
        for action in actions:
            if action not in merged:
                merged.append(action)
    return merged


def evaluate_local_path_contract(
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
) -> dict[str, Any]:
    """Classify local path readiness without creating, opening, or writing files."""

    source = _classify_source_path(_parse_source_uri(source_uri))
    source_path = source["path"] if source["state"] == "OK" else None

    budget = storage_budget.evaluate_storage_budget(
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

    path_roles = {
        "processed": _classify_path_role(
            "processed",
            processed_path,
            source_path=source_path,
            ids_data_root=ids_data_root,
        ),
        "backup": _classify_path_role(
            "backup",
            backup_path,
            source_path=source_path,
            ids_data_root=ids_data_root,
        ),
        "manifest": _classify_path_role(
            "manifest",
            manifest_path,
            source_path=source_path,
            ids_data_root=ids_data_root,
        ),
        "report_export": _classify_path_role(
            "report_export",
            report_export_path,
            source_path=source_path,
            ids_data_root=ids_data_root,
        ),
    }

    removable_state = budget.get("removable_drive_state")
    storage_state = budget["state"]
    storage_path_state = "OK"
    if storage_state == "EXTERNAL_ROOT_NOT_READY":
        storage_path_state = "SOURCE_PATH_NOT_READY"
    elif storage_state in {
        "UNBOUNDED_OUTPUT_RISK",
        "BUDGET_BLOCKED_LOW_FREE",
        "BUDGET_BLOCKED_HIGH_WATERLINE",
        "BUDGET_UNKNOWN",
    }:
        storage_path_state = "PROCESSED_PATH_UNBOUNDED"
        if path_roles["processed"]["state"] == "OK":
            path_roles["processed"] = {
                **path_roles["processed"],
                "state": "PROCESSED_PATH_UNBOUNDED",
                "reason": "storage budget does not allow derived output work.",
            }

    state = _first_failure(
        source["state"],
        storage_path_state,
        path_roles["processed"]["state"],
        path_roles["backup"]["state"],
        path_roles["manifest"]["state"],
        path_roles["report_export"]["state"],
    )
    safe_mode = state != "PATH_CONTRACT_OK"

    local_actions: list[str] = []
    if state == "SOURCE_URI_INVALID":
        local_actions.append("correct_source_uri")
    if source["state"] == "SOURCE_PATH_NOT_READY":
        local_actions.append("provide_existing_readable_source_path")
    if path_roles["processed"]["state"] == "PROCESSED_PATH_UNBOUNDED":
        local_actions.append("declare_bounded_processed_path")
    if path_roles["backup"]["state"] == "BACKUP_PATH_UNSAFE":
        local_actions.append("choose_safe_backup_path")
    if path_roles["manifest"]["state"] == "MANIFEST_PATH_UNSAFE":
        local_actions.append("choose_safe_manifest_path")
    if path_roles["report_export"]["state"] == "REPORT_EXPORT_PATH_UNSAFE":
        local_actions.append("choose_safe_report_export_path")

    operator_actions = _merge_actions(local_actions, budget.get("operator_actions", []))

    return {
        "schema_version": "ids.stage010.local_path_contract.v1",
        "stage": "STAGE-010",
        "phase": "Phase 2",
        "acceptance_id": "ACC-STAGE-010",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "state": state,
        "safe_mode": safe_mode,
        "auto_resume": False,
        "bounded_preflight_only": True,
        "paused_workflows": PAUSED_WORKFLOWS[:] if safe_mode else [],
        "operator_actions": operator_actions,
        "requires_operator_confirmation": safe_mode or budget.get("requires_operator_confirmation", False),
        "requires_revalidation": safe_mode or budget.get("requires_revalidation", False),
        "source_uri": source,
        "path_roles": path_roles,
        "storage_budget_state": storage_state,
        "removable_drive_state": removable_state,
        "storage_budget": budget,
        "does_not_start_services": True,
        "does_not_create_ids_data_root": True,
        "does_not_scan_recursively": True,
        "does_not_scan_external_drive_contents": True,
        "does_not_open_source_files": True,
        "does_not_hash_source_files": True,
        "does_not_generate_outputs": True,
        "does_not_write_runtime_data": True,
        "does_not_write_manifests": True,
        "does_not_copy_backups": True,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only IDS Stage 010 local path contract preflight."
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

    report = evaluate_local_path_contract(
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
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
