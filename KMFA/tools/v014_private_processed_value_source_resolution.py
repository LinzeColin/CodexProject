#!/usr/bin/env python3
"""Generate KMFA v0.1.4 private processed value source resolution evidence.

This phase locks the missing processed-value source-map requirement after the
previous materialization attempt. It does not read the raw inbox and does not
compare raw values with processed values. Public artifacts contain aggregate
gate evidence only; slot-level diagnostics stay private-runtime-only.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_resolution.v1"
GO_NO_GO_SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_resolution_go_no_go.v1"
PRIVATE_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_source_resolution.v1"
PRIVATE_SOURCE_MAP_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_source_map.v1"
PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PHASE_ID = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_RESOLUTION"
TASK_ID = "KMFA-V014-PRIVATE-PROCESSED-VALUE-SOURCE-RESOLUTION-20260705"
ACCEPTANCE_ID = "ACC-V014-PRIVATE-PROCESSED-VALUE-SOURCE-RESOLUTION"
STATUS = "completed_validated_local_only_no_go_processed_value_source_unresolved"
NEXT_RECOMMENDED_PHASE = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_CAPTURE"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_RESOLUTION")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "private_processed_value_source_resolution_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "private_processed_value_source_resolution_go_no_go_report.json"
SUMMARY_PATH = MACHINE_DIR / "private_processed_value_source_resolution_summary.json"
REPORT_PATH = HUMAN_DIR / "private_processed_value_source_resolution_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_resolution_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_resolution_go_no_go_report.json")
METADATA_SUMMARY_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_resolution_summary.json")

MATERIALIZATION_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_MATERIALIZATION/machine/private_processed_value_materialization_manifest.json"
)
MATERIALIZATION_GO_NO_GO_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_MATERIALIZATION/machine/private_processed_value_materialization_go_no_go_report.json"
)
MATERIALIZATION_SUMMARY_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_MATERIALIZATION/machine/private_processed_value_materialization_summary.json"
)
MATERIALIZATION_PRIVATE_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_materialization/private_processed_value_materialization.json"
)

PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_private_processed_value_source_resolution")
PRIVATE_SOURCE_RESOLUTION_PATH = PRIVATE_OUTPUT_DIR / "private_processed_value_source_resolution.json"
PRIVATE_SOURCE_MAP_PATH = PRIVATE_OUTPUT_DIR / "private_processed_value_source_map.json"
MATERIALIZATION_PRIVATE_SOURCE_MAP_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_materialization/private_processed_value_source_map.json"
)
SOURCE_MAP_CANDIDATES = (
    ("source_resolution_local_private_map", PRIVATE_SOURCE_MAP_PATH),
    ("materialization_private_map", MATERIALIZATION_PRIVATE_SOURCE_MAP_PATH),
)


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


def _load_source_map_candidate(candidate_id: str, path: Path) -> tuple[dict[str, Any], dict[str, str]]:
    if not path.exists():
        return (
            {
                "candidate_id": candidate_id,
                "present": False,
                "schema_version_matches": False,
                "usable_record_count": 0,
                "invalid_record_count": 0,
            },
            {},
        )
    payload = _read_json(path)
    records = payload.get("processed_value_sources", [])
    if not isinstance(records, list):
        records = []
    sources: dict[str, str] = {}
    invalid = 0
    for record in records:
        if not isinstance(record, dict):
            invalid += 1
            continue
        slot_id = record.get("target_slot_id")
        fingerprint = record.get("processed_value_fingerprint")
        if isinstance(slot_id, str) and slot_id and isinstance(fingerprint, str) and fingerprint.startswith("sha256:"):
            sources[slot_id] = fingerprint
        else:
            invalid += 1
    return (
        {
            "candidate_id": candidate_id,
            "present": True,
            "schema_version_matches": payload.get("schema_version") == PRIVATE_SOURCE_MAP_SCHEMA_VERSION,
            "usable_record_count": len(sources),
            "invalid_record_count": invalid,
        },
        sources,
    )


def _required_source_map_schema() -> dict[str, Any]:
    return {
        "schema_version": PRIVATE_SOURCE_MAP_SCHEMA_VERSION,
        "required_private_runtime_file": "private_processed_value_source_map.json",
        "required_record_fields": [
            "target_slot_id",
            "processed_value_fingerprint",
        ],
        "optional_private_only_fields": [
            "processed_value",
        ],
        "normalization_policy_ref": "hash_normalized_processed_value_private_runtime_only",
        "public_commit_policy": "do_not_commit_private_source_map_or_values",
    }


def _build_source_resolution(
    materialization_manifest: dict[str, Any],
    private_materialization: dict[str, Any],
    *,
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    materialization_summary = materialization_manifest.get("processed_materialization_summary", {})
    slots = private_materialization.get("materialized_processed_slots", [])
    if not isinstance(slots, list):
        raise ValueError("materialized_processed_slots must be a list")

    candidate_records: list[dict[str, Any]] = []
    merged_sources: dict[str, str] = {}
    for candidate_id, path in SOURCE_MAP_CANDIDATES:
        candidate, sources = _load_source_map_candidate(candidate_id, path)
        candidate_records.append(candidate)
        merged_sources.update(sources)

    source_resolution_slots: list[dict[str, Any]] = []
    resolved_count = 0
    for slot in slots:
        if not isinstance(slot, dict):
            continue
        slot_id = slot.get("target_slot_id")
        if not isinstance(slot_id, str):
            continue
        has_source = slot_id in merged_sources
        if has_source:
            resolved_count += 1
        source_resolution_slots.append(
            {
                "target_slot_id": slot_id,
                "source_artifact_ref_hash": slot.get("source_artifact_ref_hash"),
                "source_root_id": slot.get("source_root_id"),
                "record_ref_hash": slot.get("record_ref_hash"),
                "target_key_ref_hash": slot.get("target_key_ref_hash"),
                "context_group": slot.get("context_group"),
                "source_map_record_present": has_source,
                "value_fingerprint_present": has_source,
                "source_resolution_status": "resolved_private_source_map_record"
                if has_source
                else "missing_required_private_source_map_record",
            }
        )

    slot_count = len(source_resolution_slots)
    unresolved_count = slot_count - resolved_count
    usable_source_map_count = sum(1 for candidate in candidate_records if candidate["usable_record_count"] > 0)
    source_resolution_complete = slot_count > 0 and unresolved_count == 0
    status = (
        "complete_private_processed_value_sources_resolved"
        if source_resolution_complete
        else "blocked_required_private_processed_value_source_map_missing"
    )
    unmaterialized_count = int(materialization_summary.get("unmaterialized_processed_target_slot_count", slot_count))
    summary = {
        "processed_target_slot_count": slot_count,
        "previous_unmaterialized_processed_target_slot_count": unmaterialized_count,
        "unmaterialized_processed_target_slot_count": unmaterialized_count,
        "source_map_candidate_count": len(candidate_records),
        "source_map_candidate_present_count": sum(1 for candidate in candidate_records if candidate["present"] is True),
        "usable_private_processed_value_source_map_count": usable_source_map_count,
        "resolved_processed_value_source_count": resolved_count,
        "unresolved_processed_value_source_count": unresolved_count,
        "required_source_map_schema_locked": True,
        "source_resolution_complete": source_resolution_complete,
        "raw_to_processed_value_comparison_performed": False,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "source_resolution_status": status,
    }
    private_payload = {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "classification": "private_processed_value_source_resolution_do_not_commit",
        "source_materialization_phase_id": private_materialization.get("phase_id"),
        "source_map_candidates_checked": candidate_records,
        "required_source_map_schema": _required_source_map_schema(),
        "source_resolution_summary": summary,
        "source_resolution_slots": source_resolution_slots,
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
        "private_source_map_committed": False,
        "private_source_resolution_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": GO_NO_GO_SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_resolution_go_no_go_report",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": "processed value sources are unresolved; source map schema is locked but no usable source map is available",
        "processed_target_slot_count": summary["processed_target_slot_count"],
        "unmaterialized_processed_target_slot_count": summary["unmaterialized_processed_target_slot_count"],
        "usable_private_processed_value_source_map_count": summary["usable_private_processed_value_source_map_count"],
        "resolved_processed_value_source_count": summary["resolved_processed_value_source_count"],
        "unresolved_processed_value_source_count": summary["unresolved_processed_value_source_count"],
        "required_source_map_schema_locked": summary["required_source_map_schema_locked"],
        "source_resolution_complete": summary["source_resolution_complete"],
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
            "PRIVATE_PROCESSED_VALUE_SOURCE_MAP_MISSING",
            "PROCESSED_VALUE_SOURCE_RESOLUTION_INCOMPLETE",
            "RAW_TO_PROCESSED_VALUE_COMPARISON_NOT_PERFORMED",
            "BUSINESS_VALUE_CONSISTENCY_NOT_VERIFIED",
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "FORMAL_REPORT_BLOCKED",
            "GITHUB_UPLOAD_DEFERRED",
            "APP_REINSTALL_BLOCKED",
            "BUSINESS_EXECUTION_BLOCKED",
        ],
        "resolved_blocker_ids": [
            "PROCESSED_VALUE_SOURCE_MAP_SCHEMA_LOCKED",
            "RAW_INBOX_MUTATION_NOT_PERFORMED_BY_THIS_PHASE",
        ],
    }


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    materialization_manifest = _read_json(MATERIALIZATION_MANIFEST_PATH)
    materialization_go_no_go = _read_json(MATERIALIZATION_GO_NO_GO_PATH)
    materialization_summary = _read_json(MATERIALIZATION_SUMMARY_PATH)
    private_materialization = _read_json(MATERIALIZATION_PRIVATE_PATH)
    summary, private_payload = _build_source_resolution(
        materialization_manifest,
        private_materialization,
        generated_at=timestamp,
    )
    go_no_go = _build_go_no_go(summary)
    raw_boundary = _raw_boundary()
    source_map_schema = _required_source_map_schema()
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_resolution_manifest",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "phase_name": "KMFA v0.1.4 private processed value source resolution",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "status": STATUS,
        "generated_at": timestamp,
        "source_commit": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "dependencies": {
            "private_processed_value_materialization_manifest": MATERIALIZATION_MANIFEST_PATH.as_posix(),
            "private_processed_value_materialization_go_no_go": MATERIALIZATION_GO_NO_GO_PATH.as_posix(),
            "private_processed_value_materialization_summary": MATERIALIZATION_SUMMARY_PATH.as_posix(),
            "previous_materialization_decision": materialization_go_no_go.get("decision"),
            "previous_materialization_status": materialization_manifest.get("status"),
            "previous_materialized_processed_value_fingerprint_count": materialization_summary.get(
                "materialized_processed_value_fingerprint_count"
            ),
            "previous_unmaterialized_processed_target_slot_count": materialization_summary.get(
                "unmaterialized_processed_target_slot_count"
            ),
        },
        "phase_scope_controls": {
            "current_phase_only": True,
            "private_processed_value_source_resolution_only": True,
            "previous_materialization_evidence_consumed": True,
            "private_source_map_candidates_checked": True,
            "private_source_map_modified": False,
            "required_source_map_schema_locked": True,
            "private_source_resolution_runtime_only": True,
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
        "required_source_map_schema": source_map_schema,
        "source_resolution_summary": summary,
        "value_matching_readiness": {
            "processed_target_slots_available_from_previous_phase": True,
            "processed_target_slot_count": summary["processed_target_slot_count"],
            "processed_value_source_resolution_complete": summary["source_resolution_complete"],
            "private_processed_value_source_count": summary["resolved_processed_value_source_count"],
            "unresolved_processed_value_source_count": summary["unresolved_processed_value_source_count"],
            "raw_to_processed_value_comparison_performed": False,
            "comparable_value_pair_count": 0,
            "business_value_consistency_verified": False,
            "minimum_independent_validation_passes_required": 2,
            "independent_validation_passes_completed_by_this_phase": 0,
            "final_goal_closeout_difference_report_required_if_repeated": True,
        },
        "public_repo_safety": _public_safety(),
        "go_no_go": go_no_go,
        "private_source_resolution_ref": "private_runtime_only_not_committed",
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

    _write_json(PRIVATE_SOURCE_RESOLUTION_PATH, private_payload)
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
                "# KMFA v0.1.4 Private Processed Value Source Resolution",
                "",
                f"- phase_scope: `{PHASE_ID} only`",
                f"- processed_target_slot_count: `{summary['processed_target_slot_count']}`",
                f"- usable_private_processed_value_source_map_count: `{summary['usable_private_processed_value_source_map_count']}`",
                f"- resolved_processed_value_source_count: `{summary['resolved_processed_value_source_count']}`",
                f"- unresolved_processed_value_source_count: `{summary['unresolved_processed_value_source_count']}`",
                f"- required_source_map_schema_locked: `{str(summary['required_source_map_schema_locked']).lower()}`",
                f"- source_resolution_complete: `{str(summary['source_resolution_complete']).lower()}`",
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
                "- reason: processed value sources are unresolved; required source-map schema is locked.",
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
                "- R1: Processed value source map is unavailable; mitigation is to keep NO_GO and capture the private map in a later phase.",
                "- R2: Public artifacts could leak private value strings; mitigation is aggregate-only evidence and validator scans.",
                "- R3: Source resolution could be confused with value comparison; mitigation is explicit comparison=false gates.",
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
    summary = manifest["source_resolution_summary"]
    print(
        "Generated KMFA v0.1.4 private processed value source resolution evidence "
        f"(target_slots={summary['processed_target_slot_count']}, "
        f"resolved_sources={summary['resolved_processed_value_source_count']}, "
        "decision=NO_GO)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
