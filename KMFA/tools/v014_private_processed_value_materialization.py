#!/usr/bin/env python3
"""Generate KMFA v0.1.4 private processed value materialization evidence.

This phase consumes the previous private processed value staging output from
ignored private runtime. It does not read the raw inbox and does not compare raw
values with processed values. Public artifacts contain aggregate gate evidence
only; slot-level materialization diagnostics stay private-runtime-only.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


SCHEMA_VERSION = "kmfa.v014_private_processed_value_materialization.v1"
GO_NO_GO_SCHEMA_VERSION = "kmfa.v014_private_processed_value_materialization_go_no_go.v1"
PRIVATE_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_materialization.v1"
PRIVATE_SOURCE_MAP_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_source_map.v1"
PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PHASE_ID = "V014_PRIVATE_PROCESSED_VALUE_MATERIALIZATION"
TASK_ID = "KMFA-V014-PRIVATE-PROCESSED-VALUE-MATERIALIZATION-20260705"
ACCEPTANCE_ID = "ACC-V014-PRIVATE-PROCESSED-VALUE-MATERIALIZATION"
STATUS = "completed_validated_local_only_no_go_processed_value_source_missing"
NEXT_RECOMMENDED_PHASE = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_RESOLUTION"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_MATERIALIZATION")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "private_processed_value_materialization_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "private_processed_value_materialization_go_no_go_report.json"
SUMMARY_PATH = MACHINE_DIR / "private_processed_value_materialization_summary.json"
REPORT_PATH = HUMAN_DIR / "private_processed_value_materialization_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_materialization_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_materialization_go_no_go_report.json")
METADATA_SUMMARY_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_materialization_summary.json")

STAGING_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_STAGING/machine/private_processed_value_staging_manifest.json"
)
STAGING_GO_NO_GO_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_STAGING/machine/private_processed_value_staging_go_no_go_report.json"
)
STAGING_PRIVATE_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_staging/private_processed_value_staging.json"
)

PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_private_processed_value_materialization")
PRIVATE_MATERIALIZATION_PATH = PRIVATE_OUTPUT_DIR / "private_processed_value_materialization.json"
PRIVATE_VALUE_SOURCE_MAP_PATH = PRIVATE_OUTPUT_DIR / "private_processed_value_source_map.json"


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


def _hash_processed_value(value: Any) -> str:
    if isinstance(value, str):
        normalized = value.strip()
    else:
        normalized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


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


def _load_private_value_sources(path: Path) -> tuple[bool, dict[str, str]]:
    if not path.exists():
        return False, {}
    payload = _read_json(path)
    records = payload.get("processed_value_sources", [])
    if not isinstance(records, list):
        raise ValueError("processed_value_sources must be a list")
    sources: dict[str, str] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        slot_id = record.get("target_slot_id")
        if not isinstance(slot_id, str) or not slot_id:
            continue
        fingerprint = record.get("processed_value_fingerprint") or record.get("value_fingerprint")
        if isinstance(fingerprint, str) and fingerprint.startswith("sha256:"):
            sources[slot_id] = fingerprint
            continue
        if "processed_value" in record:
            sources[slot_id] = _hash_processed_value(record["processed_value"])
        elif "value" in record:
            sources[slot_id] = _hash_processed_value(record["value"])
    return True, sources


def _build_materialization(
    staging: dict[str, Any],
    *,
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    slots = staging.get("processed_target_slots", [])
    if not isinstance(slots, list):
        raise ValueError("processed_target_slots must be a list")

    source_map_present, value_sources = _load_private_value_sources(PRIVATE_VALUE_SOURCE_MAP_PATH)
    materialized_slots: list[dict[str, Any]] = []
    materialized_count = 0

    for slot in slots:
        if not isinstance(slot, dict):
            continue
        slot_id = slot.get("target_slot_id")
        if not isinstance(slot_id, str):
            continue
        fingerprint = value_sources.get(slot_id)
        value_materialized = fingerprint is not None
        if value_materialized:
            materialized_count += 1
        materialized_slots.append(
            {
                "target_slot_id": slot_id,
                "source_artifact_ref_hash": slot.get("source_artifact_ref_hash"),
                "source_root_id": slot.get("source_root_id"),
                "record_ref_hash": slot.get("record_ref_hash"),
                "target_key_ref_hash": slot.get("target_key_ref_hash"),
                "context_group": slot.get("context_group"),
                "private_processed_ref_hash": slot.get("private_processed_ref_hash"),
                "value_fingerprint": fingerprint,
                "value_materialized": value_materialized,
                "materialization_status": "materialized" if value_materialized else "missing_private_value_source",
            }
        )

    slot_count = len(materialized_slots)
    unmaterialized_count = slot_count - materialized_count
    complete = slot_count > 0 and unmaterialized_count == 0
    status = (
        "complete_private_processed_value_fingerprints_available"
        if complete
        else "blocked_private_processed_value_source_missing_or_incomplete"
    )
    summary = {
        "processed_target_slot_count": slot_count,
        "private_processed_value_source_map_present": source_map_present,
        "private_processed_value_source_count": len(value_sources),
        "materialized_processed_value_fingerprint_count": materialized_count,
        "unmaterialized_processed_target_slot_count": unmaterialized_count,
        "processed_value_materialization_complete": complete,
        "processed_business_values_committed_publicly": False,
        "private_processed_values_committed_publicly": False,
        "raw_to_processed_value_comparison_performed": False,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "materialization_status": status,
    }
    private_payload = {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "classification": "private_processed_value_materialization_do_not_commit",
        "source_staging_phase_id": staging.get("phase_id"),
        "source_private_staging_ref": "private_runtime_previous_phase",
        "private_value_source_map_present": source_map_present,
        "processed_materialization_summary": summary,
        "materialized_processed_slots": materialized_slots,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    return summary, private_payload


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
        "processed_private_value_strings_committed": False,
        "processed_private_ref_strings_committed": False,
        "private_materialization_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": GO_NO_GO_SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_materialization_go_no_go_report",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": "processed value fingerprints are not fully materialized and raw-to-processed comparison is not performed",
        "processed_target_slot_count": summary["processed_target_slot_count"],
        "private_processed_value_source_count": summary["private_processed_value_source_count"],
        "private_processed_value_source_map_present": summary["private_processed_value_source_map_present"],
        "materialized_processed_value_fingerprint_count": summary[
            "materialized_processed_value_fingerprint_count"
        ],
        "unmaterialized_processed_target_slot_count": summary["unmaterialized_processed_target_slot_count"],
        "processed_value_materialization_complete": summary["processed_value_materialization_complete"],
        "raw_to_processed_value_comparison_performed": False,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "blocker_ids": [
            "PRIVATE_PROCESSED_VALUE_SOURCE_MAP_MISSING_OR_INCOMPLETE",
            "PROCESSED_VALUE_MATERIALIZATION_INCOMPLETE",
            "RAW_TO_PROCESSED_VALUE_COMPARISON_NOT_PERFORMED",
            "BUSINESS_VALUE_CONSISTENCY_NOT_VERIFIED",
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "FORMAL_REPORT_BLOCKED",
            "GITHUB_UPLOAD_DEFERRED",
            "APP_REINSTALL_BLOCKED",
            "BUSINESS_EXECUTION_BLOCKED",
        ],
        "resolved_blocker_ids": [
            "PRIVATE_PROCESSED_TARGET_SLOTS_STAGED",
            "RAW_INBOX_MUTATION_NOT_PERFORMED_BY_THIS_PHASE",
        ],
    }


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    staging_manifest = _read_json(STAGING_MANIFEST_PATH)
    staging_go_no_go = _read_json(STAGING_GO_NO_GO_PATH)
    private_staging = _read_json(STAGING_PRIVATE_PATH)
    summary, private_payload = _build_materialization(private_staging, generated_at=timestamp)
    go_no_go = _build_go_no_go(summary)
    raw_boundary = _raw_boundary()
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_materialization_manifest",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "phase_name": "KMFA v0.1.4 private processed value materialization",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "status": STATUS,
        "generated_at": timestamp,
        "source_commit": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "dependencies": {
            "private_processed_value_staging_manifest": STAGING_MANIFEST_PATH.as_posix(),
            "private_processed_value_staging_go_no_go": STAGING_GO_NO_GO_PATH.as_posix(),
            "private_processed_target_slot_count": staging_manifest.get("processed_staging_summary", {}).get(
                "processed_target_slot_count"
            ),
            "previous_go_no_go_decision": staging_go_no_go.get("decision"),
        },
        "phase_scope_controls": {
            "current_phase_only": True,
            "private_processed_value_materialization_only": True,
            "previous_private_staging_consumed": True,
            "private_value_source_map_checked": True,
            "private_value_source_map_modified": False,
            "private_materialization_attempted": True,
            "private_materialization_runtime_only": True,
            "raw_to_processed_value_comparison_performed": False,
            "processed_data_reconciliation_performed": False,
            "lineage_full_check_performed": False,
            "formal_report_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "next_phase_started": False,
        },
        "raw_readonly_boundary": raw_boundary,
        "processed_materialization_summary": summary,
        "value_matching_readiness": {
            "raw_value_fingerprints_available_from_previous_phase": True,
            "raw_value_fingerprint_count_from_previous_phase": private_staging.get("source_raw_value_fingerprint_count"),
            "processed_target_slots_staged": True,
            "processed_target_slot_count": summary["processed_target_slot_count"],
            "private_processed_value_fingerprint_count": summary[
                "materialized_processed_value_fingerprint_count"
            ],
            "processed_value_materialization_complete": summary["processed_value_materialization_complete"],
            "raw_to_processed_value_comparison_performed": False,
            "comparable_value_pair_count": 0,
            "business_value_consistency_verified": False,
            "minimum_independent_validation_passes_required": 2,
            "independent_validation_passes_completed_by_this_phase": 0,
            "final_goal_closeout_difference_report_required_if_repeated": True,
        },
        "public_repo_safety": _public_safety(),
        "go_no_go": go_no_go,
        "private_materialization_ref": "private_runtime_only_not_committed",
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

    _write_json(PRIVATE_MATERIALIZATION_PATH, private_payload)
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
                "# KMFA v0.1.4 Private Processed Value Materialization",
                "",
                f"- phase_scope: `{PHASE_ID} only`",
                f"- processed_target_slot_count: `{summary['processed_target_slot_count']}`",
                f"- private_processed_value_source_map_present: `{str(summary['private_processed_value_source_map_present']).lower()}`",
                f"- materialized_processed_value_fingerprint_count: `{summary['materialized_processed_value_fingerprint_count']}`",
                f"- unmaterialized_processed_target_slot_count: `{summary['unmaterialized_processed_target_slot_count']}`",
                f"- processed_value_materialization_complete: `{str(summary['processed_value_materialization_complete']).lower()}`",
                "- raw_to_processed_value_comparison_performed: `false`",
                "- business_value_consistency_verified: `false`",
                "- go_no_go: `NO_GO`",
                "",
                "Only aggregate gate evidence is public. Slot-level diagnostics stay in ignored private runtime.",
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
                "- reason: processed value fingerprints are not fully materialized; comparison was not performed.",
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
                "- R1: Processed values are not materialized; mitigation is to keep NO_GO and resolve private value sources.",
                "- R2: Public artifacts could leak private value strings; mitigation is aggregate-only evidence and validator scans.",
                "- R3: Raw data could be changed accidentally; mitigation is no raw inbox access in this phase.",
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
                "- Remove current phase ignored private runtime diagnostics.",
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
    summary = manifest["processed_materialization_summary"]
    print(
        "Generated KMFA v0.1.4 private processed value materialization evidence "
        f"(target_slots={summary['processed_target_slot_count']}, "
        f"materialized={summary['materialized_processed_value_fingerprint_count']}, "
        "decision=NO_GO)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
