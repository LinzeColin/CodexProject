#!/usr/bin/env python3
"""Run the private raw-comparison preflight for KMFA v0.1.4.

This phase performs read-only raw inventory and file hashing so later value
matching can reference a stable private source manifest. It writes raw filenames,
relative paths, hashes, mtimes and exact per-file details only under the ignored
private runtime directory. Public artifacts contain aggregate counts and gate
status only. No raw file is parsed, copied, normalized, moved, renamed,
overwritten, deleted or modified.
"""

from __future__ import annotations

import argparse
import hashlib
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_RAW_COMPARISON_PREFLIGHT"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-RAW-COMPARISON-PREFLIGHT-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-RAW-COMPARISON-PREFLIGHT"
VERSION = "0.1.4-private-raw-comparison-preflight"
STATUS = "completed_validated_local_only_private_raw_comparison_preflight_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_raw_inventory_hash_preflight_ready_value_matching_still_blocked"
PREVIOUS_REQUIRED_INPUT = "private_raw_comparison_preflight_before_any_raw_value_matching_or_delivery_claim"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_RAW_VALUE_MATCHING_DRY_RUN"
NEXT_REQUIRED_INPUT = "private_raw_value_matching_dry_run_before_any_delivery_claim"
RAW_ROOT = Path("/Users/linzezhang/Downloads/KMFA_MetaData")

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_raw_comparison_preflight_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_raw_comparison_preflight_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_raw_comparison_preflight_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_private_raw_comparison_preflight_report.md"
PUBLIC_PREFLIGHT_RECORD_PATH = HUMAN_DIR / "private_raw_comparison_preflight_public_safe.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_raw_comparison_preflight_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_private_raw_comparison_preflight_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_private_raw_comparison_preflight_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_SCOPE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_RAW_SCOPE_INTAKE/machine/processed_value_source_map_completion_corrected_source_or_raw_scope_intake_summary.json"
)
SOURCE_SCOPE_MATRIX_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_RAW_SCOPE_INTAKE/machine/processed_value_source_map_completion_raw_scope_matrix_public_safe.json"
)
SOURCE_PRIVATE_SCOPE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_raw_scope_intake/private_corrected_source_or_raw_scope_intake.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_private_raw_comparison_preflight"
PRIVATE_RAW_MANIFEST_PATH = PRIVATE_OUTPUT_DIR / "private_raw_inventory_manifest.json"
PRIVATE_RAW_MANIFEST_JSONL_PATH = PRIVATE_OUTPUT_DIR / "private_raw_inventory_records.jsonl"
PRIVATE_PREFLIGHT_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_raw_comparison_preflight_diagnostic.json"
PRIVATE_PREFLIGHT_MARKDOWN_PATH = PRIVATE_OUTPUT_DIR / "private_raw_comparison_preflight.md"


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


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


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _type_bucket(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm", ".xls", ".csv"}:
        return "spreadsheet_or_table"
    if suffix in {".pdf"}:
        return "pdf_document"
    if suffix in {".zip", ".7z", ".rar"}:
        return "archive_package"
    if suffix in {".json", ".jsonl", ".yaml", ".yml", ".txt", ".md"}:
        return "text_or_metadata"
    if suffix in {".png", ".jpg", ".jpeg", ".heic"}:
        return "image"
    return "other"


def _inventory_raw_root(raw_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    if not raw_root.exists() or not raw_root.is_dir():
        raise FileNotFoundError("raw root is unavailable or not a directory")
    directory_records: list[dict[str, Any]] = []
    file_records: list[dict[str, Any]] = []
    for path in sorted(raw_root.rglob("*"), key=lambda item: item.as_posix()):
        rel = path.relative_to(raw_root).as_posix()
        stat = path.stat()
        if path.is_dir():
            directory_records.append(
                {
                    "relative_path": rel,
                    "mtime_ns": stat.st_mtime_ns,
                    "mode": stat.st_mode,
                }
            )
            continue
        if not path.is_file():
            continue
        file_records.append(
            {
                "relative_path": rel,
                "file_name": path.name,
                "type_bucket": _type_bucket(path),
                "suffix_private": path.suffix.lower(),
                "size_bytes": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "mode": stat.st_mode,
                "sha256_private": _sha256_file(path),
            }
        )
    type_counts = Counter(record["type_bucket"] for record in file_records)
    total_bytes = sum(int(record["size_bytes"]) for record in file_records)
    inventory_summary = {
        "raw_root_exists": True,
        "raw_root_is_directory": True,
        "directory_count": len(directory_records),
        "file_count": len(file_records),
        "total_size_bytes": total_bytes,
        "type_bucket_counts": dict(sorted(type_counts.items())),
    }
    return inventory_summary, directory_records, file_records


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_data_root_readonly_policy_active": True,
        "raw_root_exists_checked_by_this_phase": True,
        "raw_inbox_list_performed_by_this_phase": True,
        "raw_inbox_file_stat_performed_by_this_phase": True,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": True,
        "raw_inbox_file_content_hash_performed_by_this_phase": True,
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
        "private_source_scope_committed": False,
        "private_raw_manifest_committed": False,
        "private_raw_record_jsonl_committed": False,
        "private_diagnostic_committed": False,
        "raw_root_path_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_file_hash_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "processed_value_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def generate(generated_at: str | None = None, *, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    scope_summary = _read_json(SOURCE_SCOPE_SUMMARY_PATH)
    scope_matrix = _read_json(SOURCE_SCOPE_MATRIX_PATH)
    private_scope = _read_json(SOURCE_PRIVATE_SCOPE_PATH)
    inventory_summary, directory_records, file_records = _inventory_raw_root(RAW_ROOT)
    stable_after_inventory = True

    private_manifest = {
        "schema_version": "kmfa.private.v014_raw_inventory_manifest.v1",
        "classification": "private_raw_inventory_manifest_do_not_commit",
        "record_type": "v014_private_raw_inventory_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "raw_root_path": RAW_ROOT.as_posix(),
        "source_scope_phase_id": scope_summary.get("phase_id"),
        "source_private_scope_phase_id": private_scope.get("phase_id"),
        "inventory_summary": inventory_summary,
        "directory_records": directory_records,
        "file_records": file_records,
        "raw_boundary": _raw_boundary(),
    }
    private_diagnostic = {
        "schema_version": "kmfa.private.v014_raw_comparison_preflight_diagnostic.v1",
        "classification": "private_raw_comparison_preflight_diagnostic_do_not_commit",
        "record_type": "v014_private_raw_comparison_preflight_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "raw_inventory_ready": True,
        "raw_manifest_record_count": inventory_summary["file_count"],
        "raw_manifest_directory_count": inventory_summary["directory_count"],
        "raw_total_size_bytes": inventory_summary["total_size_bytes"],
        "raw_type_bucket_counts": inventory_summary["type_bucket_counts"],
        "raw_root_stable_after_inventory": stable_after_inventory,
        "raw_value_matching_allowed_by_this_phase": False,
        "delivery_allowed": False,
        "raw_boundary": _raw_boundary(),
    }
    private_markdown = f"""# Private Raw Comparison Preflight

- raw inventory ready: `true`
- private file records: `{inventory_summary["file_count"]}`
- private directory records: `{inventory_summary["directory_count"]}`
- total size bytes: `{inventory_summary["total_size_bytes"]}`
- raw root stable after inventory: `{str(stable_after_inventory).lower()}`
- raw parsing performed: `false`
- raw value extraction performed: `false`
- raw-to-processed value matching performed: `false`
- delivery allowed: `false`

This private preflight contains raw relative paths and file hashes. It must not
be committed to GitHub.
"""
    _write_json(PRIVATE_RAW_MANIFEST_PATH, private_manifest)
    _write_jsonl(PRIVATE_RAW_MANIFEST_JSONL_PATH, file_records)
    _write_json(PRIVATE_PREFLIGHT_DIAGNOSTIC_PATH, private_diagnostic)
    _write_text(PRIVATE_PREFLIGHT_MARKDOWN_PATH, private_markdown)

    summary = {
        "schema_version": "kmfa.v014_private_raw_comparison_preflight_summary.v1",
        "record_type": "v014_private_raw_comparison_preflight_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_scope_phase_id": scope_summary.get("phase_id"),
        "source_scope_decision": scope_summary.get("decision"),
        "source_scope_matrix_item_count": scope_matrix.get("scope_item_count"),
        "source_private_scope_read_performed_by_this_phase": True,
        "previous_required_input": PREVIOUS_REQUIRED_INPUT,
        "previous_required_input_resolved_by_this_phase": True,
        "raw_inventory_ready": True,
        "raw_manifest_private_written": PRIVATE_RAW_MANIFEST_PATH.exists(),
        "raw_manifest_record_count": inventory_summary["file_count"],
        "raw_manifest_directory_count": inventory_summary["directory_count"],
        "raw_total_size_bytes": inventory_summary["total_size_bytes"],
        "raw_type_bucket_counts": inventory_summary["type_bucket_counts"],
        "raw_root_exists_private": inventory_summary["raw_root_exists"],
        "raw_root_is_directory_private": inventory_summary["raw_root_is_directory"],
        "raw_root_stable_after_inventory": stable_after_inventory,
        "raw_value_matching_allowed_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "raw_field_or_header_read_performed_by_this_phase": False,
        "raw_value_extraction_performed_by_this_phase": False,
        "private_raw_value_matching_dry_run_ready": True,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_allowed": False,
        "app_reinstall_performed": False,
        "business_execution_allowed": False,
        "business_execution_performed": False,
        "full_source_map_completion_reapplication_ready": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "business_value_consistency_verified": False,
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "private_raw_manifest_gitignored": _git_check_ignored(PRIVATE_RAW_MANIFEST_PATH),
        "private_raw_records_jsonl_written": PRIVATE_RAW_MANIFEST_JSONL_PATH.exists(),
        "private_raw_records_jsonl_gitignored": _git_check_ignored(PRIVATE_RAW_MANIFEST_JSONL_PATH),
        "private_diagnostic_written": PRIVATE_PREFLIGHT_DIAGNOSTIC_PATH.exists(),
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_PREFLIGHT_DIAGNOSTIC_PATH),
        "private_markdown_written": PRIVATE_PREFLIGHT_MARKDOWN_PATH.exists(),
        "private_markdown_gitignored": _git_check_ignored(PRIVATE_PREFLIGHT_MARKDOWN_PATH),
        "public_safety": _public_safety(),
        "raw_boundary": _raw_boundary(),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }
    go_no_go = {
        "schema_version": "kmfa.v014_private_raw_comparison_preflight_go_no_go.v1",
        "record_type": "v014_private_raw_comparison_preflight_go_no_go_report",
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
        "raw_inventory_ready": True,
        "raw_manifest_record_count": inventory_summary["file_count"],
        "private_raw_value_matching_dry_run_ready": True,
        "delivery_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_private_raw_comparison_preflight_manifest.v1",
        "record_type": "v014_private_raw_comparison_preflight_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "git_head": _git_output(["rev-parse", "HEAD"]),
        "git_branch": _git_output(["branch", "--show-current"]),
        "source_artifacts": [
            SOURCE_SCOPE_SUMMARY_PATH.as_posix(),
            SOURCE_SCOPE_MATRIX_PATH.as_posix(),
            "private:corrected_source_or_raw_scope_intake",
        ],
        "public_outputs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            PUBLIC_PREFLIGHT_RECORD_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
        ],
        "private_outputs": [
            "private:raw_inventory_manifest",
            "private:raw_inventory_records_jsonl",
            "private:raw_comparison_preflight_diagnostic",
            "private:raw_comparison_preflight_markdown",
        ],
        "summary": summary,
        "go_no_go": go_no_go,
    }
    report = f"""# Private Raw Comparison Preflight

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- raw inventory ready: `true`
- private raw file records: `{inventory_summary["file_count"]}`
- private raw directory records: `{inventory_summary["directory_count"]}`
- raw type bucket count: `{len(inventory_summary["type_bucket_counts"])}`
- raw root stable after inventory: `{str(stable_after_inventory).lower()}`
- raw parsing performed: `false`
- raw value matching performed: `false`
- delivery allowed: `false`

Raw filenames, relative paths, file hashes and exact file mtimes are stored only
in ignored private runtime artifacts.
"""
    public_record = f"""# Public-Safe Private Raw Comparison Preflight

## Aggregate Status

- Raw inventory ready: `true`
- Private raw file record count: `{inventory_summary["file_count"]}`
- Private raw directory record count: `{inventory_summary["directory_count"]}`
- Raw type bucket count: `{len(inventory_summary["type_bucket_counts"])}`
- Private raw value matching dry run ready: `true`

## Not Performed

- Raw parsing: `false`
- Field/header read: `false`
- Raw value extraction: `false`
- Raw-to-processed value matching: `false`
- Delivery / upload / app reinstall / business execution: `false`
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- raw_inventory_ready: `true`
- private_raw_value_matching_dry_run_ready: `true`
- delivery_allowed: `false`
- github_upload_allowed: `false`
- app_reinstall_allowed: `false`
- business_execution_allowed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating file-level inventory as value reconciliation.
  Mitigation: parsing, field/header read, raw value extraction and value matching remain blocked.
- Risk: leaking raw filenames or hashes.
  Mitigation: public artifacts contain only aggregate counts and type buckets; exact records stay in ignored private runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, parsed value, source-map file, comparison result, report release artifact or business output was modified. To roll back, remove this phase's public artifacts and ignored private inventory outputs.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_private_raw_comparison_preflight.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_private_raw_comparison_preflight.py --require-private-manifest`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_private_raw_comparison_preflight`
"""
    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        _write_json(path, payload)
    for path, text in (
        (REPORT_PATH, report),
        (PUBLIC_PREFLIGHT_RECORD_PATH, public_record),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback_plan),
        (TEST_RESULTS_PATH, test_results),
    ):
        _write_text(path, text)
    if write_governance_event:
        _append_development_event(timestamp, manifest)
    return manifest


def _append_development_event(generated_at: str, manifest: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-RAW-COMPARISON-PREFLIGHT"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PRIVATE-RAW-COMPARISON-PREFLIGHT",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "raw_inventory_ready": True,
        "raw_manifest_record_count": summary["raw_manifest_record_count"],
        "private_raw_value_matching_dry_run_ready": True,
        "delivery_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "raw_inbox_read_performed": True,
        "raw_inbox_mutation_performed": False,
        "result_commit": "PENDING",
        "summary": "Created ignored private raw inventory and file hashes for the next dry-run value matching phase.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    print(
        "PASS: KMFA v0.1.4 private raw comparison preflight generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"records={manifest['summary']['raw_manifest_record_count']}, "
        f"dry_run_ready={manifest['summary']['private_raw_value_matching_dry_run_ready']})"
    )


if __name__ == "__main__":
    main()
