#!/usr/bin/env python3
"""Generate KMFA v0.1.4 private processed value source-map capture evidence.

This phase inspects the previous private processed target staging and source
resolution diagnostics. It does not read the raw inbox, does not resolve raw
values, and does not compare raw values with processed values. Public artifacts
contain aggregate gate evidence only; slot-level private refs and fill requests
stay private-runtime-only.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_capture.v1"
GO_NO_GO_SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_capture_go_no_go.v1"
PRIVATE_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_source_map_capture.v1"
PRIVATE_FILL_REQUEST_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_source_map_fill_request.v1"
SOURCE_MAP_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_source_map.v1"
PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PHASE_ID = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_CAPTURE"
TASK_ID = "KMFA-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-CAPTURE-20260705"
ACCEPTANCE_ID = "ACC-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-CAPTURE"
STATUS = "completed_validated_local_only_no_go_authorized_processed_value_source_map_fill_required"
NEXT_RECOMMENDED_PHASE = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_AUTHORIZED_FILL"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_CAPTURE")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "private_processed_value_source_map_capture_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "private_processed_value_source_map_capture_go_no_go_report.json"
SUMMARY_PATH = MACHINE_DIR / "private_processed_value_source_map_capture_summary.json"
REPORT_PATH = HUMAN_DIR / "private_processed_value_source_map_capture_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_capture_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_capture_go_no_go_report.json")
METADATA_SUMMARY_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_capture_summary.json")

STAGING_PRIVATE_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_staging/private_processed_value_staging.json"
)
SOURCE_RESOLUTION_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_RESOLUTION/machine/private_processed_value_source_resolution_manifest.json"
)
SOURCE_RESOLUTION_PRIVATE_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_source_resolution/private_processed_value_source_resolution.json"
)
SOURCE_MAP_CANDIDATES = (
    Path("KMFA/.codex_private_runtime/v014_private_processed_value_source_resolution/private_processed_value_source_map.json"),
    Path("KMFA/.codex_private_runtime/v014_private_processed_value_materialization/private_processed_value_source_map.json"),
)

PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_private_processed_value_source_map_capture")
PRIVATE_CAPTURE_PATH = PRIVATE_OUTPUT_DIR / "private_processed_value_source_map_capture.json"
PRIVATE_FILL_REQUEST_PATH = PRIVATE_OUTPUT_DIR / "private_processed_value_source_map_fill_request.json"

DECIMAL_VALUE_LITERAL_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+[.,]\d{1,6}(?![A-Za-z])")
VALUE_WORD_RE = re.compile(r"(amount|balance|cash|cent|cost|gross|invoice|margin|profit|rate|revenue|tax|value)", re.I)


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


def _hash_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _shape_ref(value: str) -> str:
    shaped = re.sub(r"[A-Za-z]+", "A", value)
    shaped = re.sub(r"\d+", "9", shaped)
    return shaped[:160]


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


def _load_existing_source_map_records() -> tuple[int, int]:
    present_count = 0
    usable_records: dict[str, str] = {}
    for path in SOURCE_MAP_CANDIDATES:
        if not path.exists():
            continue
        present_count += 1
        payload = _read_json(path)
        records = payload.get("processed_value_sources", [])
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            slot_id = record.get("target_slot_id")
            fingerprint = record.get("processed_value_fingerprint") or record.get("value_fingerprint")
            if isinstance(slot_id, str) and isinstance(fingerprint, str) and fingerprint.startswith("sha256:"):
                usable_records[slot_id] = fingerprint
    return present_count, len(usable_records)


def _build_capture(
    staging: dict[str, Any],
    source_resolution: dict[str, Any],
    *,
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    slots = staging.get("processed_target_slots", [])
    if not isinstance(slots, list):
        raise ValueError("processed_target_slots must be a list")

    candidate_present_count, usable_source_map_count = _load_existing_source_map_records()
    capture_slots: list[dict[str, Any]] = []
    fill_request_items: list[dict[str, Any]] = []
    direct_literal_count = 0
    existing_fingerprint_count = 0
    value_word_count = 0
    shape_hashes: set[str] = set()

    for slot in slots:
        if not isinstance(slot, dict):
            continue
        slot_id = slot.get("target_slot_id")
        private_ref = slot.get("private_processed_ref")
        if not isinstance(slot_id, str) or not isinstance(private_ref, str):
            continue
        existing_fingerprint = slot.get("value_fingerprint")
        has_existing_fingerprint = isinstance(existing_fingerprint, str) and existing_fingerprint.startswith("sha256:")
        if has_existing_fingerprint:
            existing_fingerprint_count += 1
        has_direct_literal = bool(DECIMAL_VALUE_LITERAL_RE.search(private_ref))
        if has_direct_literal:
            direct_literal_count += 1
        if VALUE_WORD_RE.search(private_ref):
            value_word_count += 1
        shape_hashes.add(_hash_text(_shape_ref(private_ref)))
        capture_status = (
            "existing_value_fingerprint_available"
            if has_existing_fingerprint
            else "path_only_private_ref_authorized_value_source_required"
        )
        capture_slots.append(
            {
                "target_slot_id": slot_id,
                "source_artifact_ref_hash": slot.get("source_artifact_ref_hash"),
                "source_root_id": slot.get("source_root_id"),
                "record_ref_hash": slot.get("record_ref_hash"),
                "target_key_ref_hash": slot.get("target_key_ref_hash"),
                "context_group": slot.get("context_group"),
                "private_processed_ref": private_ref,
                "private_processed_ref_hash": slot.get("private_processed_ref_hash"),
                "private_processed_ref_shape_hash": _hash_text(_shape_ref(private_ref)),
                "direct_value_literal_detected": has_direct_literal,
                "processed_value_fingerprint_present": has_existing_fingerprint,
                "source_map_capture_status": capture_status,
            }
        )
        if not has_existing_fingerprint:
            fill_request_items.append(
                {
                    "target_slot_id": slot_id,
                    "private_processed_ref": private_ref,
                    "private_processed_ref_hash": slot.get("private_processed_ref_hash"),
                    "required_field": "processed_value_fingerprint",
                    "optional_private_only_field": "processed_value",
                    "public_commit_policy": "do_not_commit_private_source_map_or_values",
                    "fill_status": "authorized_private_value_source_required",
                }
            )

    slot_count = len(capture_slots)
    captured_count = existing_fingerprint_count
    path_only_count = slot_count - existing_fingerprint_count
    authorized_fill_required_count = len(fill_request_items)
    complete = slot_count > 0 and authorized_fill_required_count == 0 and usable_source_map_count == slot_count
    summary = {
        "processed_target_slot_count": slot_count,
        "existing_source_map_candidate_present_count": candidate_present_count,
        "existing_usable_private_processed_value_source_map_record_count": usable_source_map_count,
        "private_processed_ref_shape_count": len(shape_hashes),
        "private_ref_value_semantic_word_count": value_word_count,
        "path_only_private_ref_slot_count": path_only_count,
        "direct_processed_value_literal_count": direct_literal_count,
        "existing_processed_value_fingerprint_count": existing_fingerprint_count,
        "captured_processed_value_fingerprint_count": captured_count,
        "usable_private_processed_value_source_map_record_count": usable_source_map_count,
        "private_source_map_write_performed": False,
        "authorized_fill_required_slot_count": authorized_fill_required_count,
        "source_map_capture_complete": complete,
        "raw_to_processed_value_comparison_performed": False,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "source_map_capture_status": (
            "complete_private_source_map_available"
            if complete
            else "blocked_path_only_private_refs_authorized_fill_required"
        ),
    }
    private_capture = {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "classification": "private_processed_value_source_map_capture_do_not_commit",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_staging_phase_id": staging.get("phase_id"),
        "source_resolution_phase_id": source_resolution.get("phase_id"),
        "source_map_schema_version": SOURCE_MAP_SCHEMA_VERSION,
        "source_map_capture_summary": summary,
        "source_map_capture_slots": capture_slots,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    fill_request = {
        "schema_version": PRIVATE_FILL_REQUEST_SCHEMA_VERSION,
        "classification": "private_processed_value_source_map_fill_request_do_not_commit",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_map_schema_version": SOURCE_MAP_SCHEMA_VERSION,
        "required_output_file": "private_processed_value_source_map.json",
        "required_record_fields": ["target_slot_id", "processed_value_fingerprint"],
        "optional_private_only_fields": ["processed_value"],
        "public_commit_policy": "do_not_commit_private_source_map_or_values",
        "fill_request_item_count": len(fill_request_items),
        "fill_request_items": fill_request_items,
    }
    return summary, private_capture, fill_request


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
        "raw_inbox_copy_performed_by_this_phase": False,
        "raw_inbox_overwrite_performed_by_this_phase": False,
        "raw_inbox_normalize_performed_by_this_phase": False,
        "raw_inbox_create_extra_files_inside_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "raw_business_data_committed": False,
        "source_document_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "private_csv_committed": False,
        "raw_filenames_committed": False,
        "raw_hashes_committed": False,
        "field_or_header_plaintext_committed": False,
        "sheet_names_committed": False,
        "archive_entry_names_committed": False,
        "raw_or_processed_business_values_committed": False,
        "processed_private_ref_strings_committed": False,
        "processed_private_value_strings_committed": False,
        "private_source_map_committed": False,
        "private_source_map_capture_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": GO_NO_GO_SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_capture_go_no_go_report",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": "processed private refs are path-only and require authorized private value-source fill before fingerprints can be materialized",
        "processed_target_slot_count": summary["processed_target_slot_count"],
        "path_only_private_ref_slot_count": summary["path_only_private_ref_slot_count"],
        "direct_processed_value_literal_count": summary["direct_processed_value_literal_count"],
        "captured_processed_value_fingerprint_count": summary["captured_processed_value_fingerprint_count"],
        "usable_private_processed_value_source_map_record_count": summary[
            "usable_private_processed_value_source_map_record_count"
        ],
        "authorized_fill_required_slot_count": summary["authorized_fill_required_slot_count"],
        "source_map_capture_complete": summary["source_map_capture_complete"],
        "raw_to_processed_value_comparison_performed": False,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "resolved_blocker_ids": [
            "PRIVATE_PROCESSED_VALUE_SOURCE_MAP_CAPTURE_REQUIREMENT_CLASSIFIED",
            "RAW_INBOX_MUTATION_NOT_PERFORMED_BY_THIS_PHASE",
        ],
        "blocker_ids": [
            "AUTHORIZED_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_FILL_REQUIRED",
            "PROCESSED_VALUE_FINGERPRINTS_NOT_CAPTURED",
            "RAW_TO_PROCESSED_VALUE_COMPARISON_NOT_PERFORMED",
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
    staging = _read_json(STAGING_PRIVATE_PATH)
    source_resolution_manifest = _read_json(SOURCE_RESOLUTION_MANIFEST_PATH)
    source_resolution_private = _read_json(SOURCE_RESOLUTION_PRIVATE_PATH)
    summary, private_capture, fill_request = _build_capture(
        staging,
        source_resolution_private,
        generated_at=timestamp,
    )
    go_no_go = _build_go_no_go(summary)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_capture_manifest",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "phase_name": "KMFA v0.1.4 private processed value source-map capture",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "status": STATUS,
        "generated_at": timestamp,
        "source_commit": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "dependencies": {
            "private_processed_value_staging_private_runtime": "private_runtime_previous_phase",
            "private_processed_value_source_resolution_manifest": SOURCE_RESOLUTION_MANIFEST_PATH.as_posix(),
            "private_processed_value_source_resolution_private_runtime": "private_runtime_previous_phase",
            "source_resolution_status": source_resolution_manifest.get("status"),
        },
        "phase_scope_controls": {
            "current_phase_only": True,
            "private_processed_value_source_map_capture_only": True,
            "previous_staging_private_runtime_consumed": True,
            "previous_source_resolution_evidence_consumed": True,
            "private_capture_request_written": True,
            "private_source_map_write_performed": False,
            "processed_value_materialization_performed": False,
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
        "source_map_capture_summary": summary,
        "value_matching_readiness": {
            "processed_target_slot_count": summary["processed_target_slot_count"],
            "processed_source_map_capture_complete": summary["source_map_capture_complete"],
            "private_processed_value_fingerprint_count": summary["captured_processed_value_fingerprint_count"],
            "authorized_fill_required_slot_count": summary["authorized_fill_required_slot_count"],
            "raw_to_processed_value_comparison_performed": False,
            "comparable_value_pair_count": 0,
            "business_value_consistency_verified": False,
            "minimum_independent_validation_passes_required": 2,
            "independent_validation_passes_completed_by_this_phase": 0,
            "final_goal_closeout_difference_report_required_if_repeated": True,
        },
        "public_repo_safety": _public_safety(),
        "private_capture_ref": "private_runtime_only_not_committed",
        "private_fill_request_ref": "private_runtime_only_not_committed",
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
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
        ],
        "github_upload_performed": False,
        "formal_report_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }
    _write_json(PRIVATE_CAPTURE_PATH, private_capture)
    _write_json(PRIVATE_FILL_REQUEST_PATH, fill_request)
    for path, payload in (
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
    ):
        _write_json(path, payload)

    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Private Processed Value Source-Map Capture",
                "",
                f"- phase_scope: `{PHASE_ID} only`",
                f"- processed_target_slot_count: `{summary['processed_target_slot_count']}`",
                f"- path_only_private_ref_slot_count: `{summary['path_only_private_ref_slot_count']}`",
                f"- direct_processed_value_literal_count: `{summary['direct_processed_value_literal_count']}`",
                f"- captured_processed_value_fingerprint_count: `{summary['captured_processed_value_fingerprint_count']}`",
                f"- usable_private_processed_value_source_map_record_count: `{summary['usable_private_processed_value_source_map_record_count']}`",
                f"- authorized_fill_required_slot_count: `{summary['authorized_fill_required_slot_count']}`",
                f"- source_map_capture_complete: `{str(summary['source_map_capture_complete']).lower()}`",
                "- raw_to_processed_value_comparison_performed: `false`",
                "- business_value_consistency_verified: `false`",
                "- go_no_go: `NO_GO`",
                "",
                "Public evidence is aggregate-only. Slot-level capture diagnostics and fill requests stay in ignored private runtime.",
            ]
        )
        + "\n",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go/No-Go",
                "",
                "- decision: `NO_GO`",
                "- reason: path-only processed private refs require an authorized private value-source fill before fingerprints can be materialized.",
                "- formal_report_allowed: `false`",
                "- github_upload_allowed: `false`",
                "- app_reinstall_allowed: `false`",
                "- business_execution_allowed: `false`",
                f"- next_recommended_phase: `{NEXT_RECOMMENDED_PHASE}`",
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
                "- R1: Path-only processed private refs cannot prove processed business values; mitigation is `NO_GO` until authorized fill supplies fingerprints.",
                "- R2: Private fill request could disclose internal refs if committed; mitigation is ignored runtime and validator Git-boundary checks.",
                "- R3: Raw-to-processed comparison could be claimed too early; mitigation is explicit comparison=false and consistency=false gates.",
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
                "- Remove current phase public evidence directory.",
                "- Remove current phase metadata quality copies.",
                "- Remove current phase tool, validator and focused test.",
                "- Remove ignored private runtime capture diagnostics and fill request.",
                "- Revert governance entries for this phase.",
            ]
        )
        + "\n",
    )
    if not TEST_RESULTS_PATH.exists():
        _write_text(
            TEST_RESULTS_PATH,
            "\n".join(
                [
                    "# Test Results",
                    "",
                    f"- phase: `{PHASE_ID}`",
                    "- status: `PENDING_FINAL_VALIDATION`",
                    "- red_test_recorded: `true`",
                    "- raw_inbox_access_performed: `false`",
                    "- raw_inbox_mutation_performed: `false`",
                ]
            )
            + "\n",
        )
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["source_map_capture_summary"]
    print(
        "Generated KMFA v0.1.4 private processed value source-map capture evidence "
        f"(target_slots={summary['processed_target_slot_count']}, "
        f"captured_fingerprints={summary['captured_processed_value_fingerprint_count']}, "
        f"authorized_fill_required={summary['authorized_fill_required_slot_count']}, "
        "decision=NO_GO)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
