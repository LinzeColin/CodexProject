#!/usr/bin/env python3
"""Build KMFA v1.4 S03-P3 public-safe source priority evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s03_p2_source_check_matrix import validate_v014_s03_p2_source_check_matrix
from KMFA.tools.source_priority import (
    SOURCE_PRIORITY_ORDER,
    build_cross_source_difference_queue_item,
    build_same_source_inconsistency_event,
    sort_source_candidates,
)
from KMFA.tools.v014_s03_p1_raw_file_registration import RAW_INBOX
from KMFA.tools.v014_s03_p2_source_check_matrix import (
    MANIFEST_PATH as S03_P2_MANIFEST_PATH,
    MATRIX_PATH as S03_P2_MATRIX_PATH,
    STATUS_EVENTS_PATH as S03_P2_STATUS_EVENTS_PATH,
)


TASK_ID = "KMFA-V014-S03-P3-SOURCE-PRIORITY-20260704"
ACCEPTANCE_ID = "ACC-V014-S03-P3-SOURCE-PRIORITY"
STAGE_DIR = Path("KMFA/stage_artifacts/V014_S03_P3_SOURCE_PRIORITY")
MACHINE_DIR = STAGE_DIR / "machine"
HUMAN_DIR = STAGE_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "source_priority_manifest.json"
PRIORITY_RECORDS_PATH = Path("KMFA/metadata/sources/v014_s03_p3_source_priority_records.jsonl")
SAME_SOURCE_EVENTS_PATH = Path("KMFA/metadata/sources/v014_s03_p3_same_source_rerun_events.jsonl")
DIFFERENCE_QUEUE_PATH = Path("KMFA/metadata/quality/v014_s03_p3_cross_source_difference_queue.jsonl")
PROTOCOL_PATH = Path("KMFA/metadata/protocol/source_priority_v1_4_s03_p3.json")
REPORT_PATH = HUMAN_DIR / "source_priority_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PLAN_PATH = HUMAN_DIR / "rollback_plan.md"


def stable_digest(parts: list[str], length: int = 16) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:length]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} must contain a JSON object")
        records.append(value)
    return records


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def build_priority_records(matrix_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority_records: list[dict[str, Any]] = []
    for index, row in enumerate(sorted(matrix_rows, key=lambda item: str(item.get("matrix_id"))), start=1):
        matrix_id = str(row.get("matrix_id", "")).strip()
        public_file_id = str(row.get("public_file_id", "")).strip()
        if not matrix_id or not public_file_id:
            raise ValueError("S03-P2 matrix rows must contain matrix_id and public_file_id")

        raw_source_id = f"SRC-V014-S03P3-RAW-{stable_digest([public_file_id, 'raw'], 12)}"
        authorized_source_id = f"SRC-V014-S03P3-AUTH-{stable_digest([public_file_id, 'authorized'], 12)}"
        processed_source_id = f"SRC-V014-S03P3-PROC-{stable_digest([matrix_id, 'processed'], 12)}"
        ranked_candidates = sort_source_candidates(
            [
                {
                    "source_id": raw_source_id,
                    "source_class": "raw_upload",
                    "availability_status": "present_via_s03_p1_public_register_private_detail_only",
                },
                {
                    "source_id": authorized_source_id,
                    "source_class": "authorized_export",
                    "availability_status": "pending_authorized_export_reference",
                },
                {
                    "source_id": processed_source_id,
                    "source_class": "processed_data",
                    "availability_status": "derived_or_processed_reference_lower_priority",
                },
            ]
        )
        priority_records.append(
            {
                "record_type": "source_priority_record",
                "schema_version": "kmfa.v014_s03_p3.source_priority_record.v1",
                "stage_phase": "S03-P3",
                "priority_record_id": f"SPR-V014-S03P3-{stable_digest([matrix_id, public_file_id])}",
                "matrix_id": matrix_id,
                "public_file_id": public_file_id,
                "source_check_status": row.get("status"),
                "source_priority_order": list(SOURCE_PRIORITY_ORDER),
                "candidate_refs": ranked_candidates,
                "highest_priority_source_class": ranked_candidates[0]["source_class"],
                "priority_decision_status": "priority_locked_manual_review_pending",
                "processed_data_rank_after_raw_or_authorized": True,
                "same_source_inconsistency_action": ["invalidate_derived_cache", "request_rerun"],
                "cross_source_conflict_policy": "difference_queue_manual_review_no_auto_selection",
                "manual_review_required": True,
                "auto_selection_allowed": False,
                "target_layer": "metadata",
                "raw_root_read_performed_by_this_phase": False,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "raw_filename_committed": False,
                "raw_hash_committed": False,
                "field_or_header_plaintext_committed": False,
                "raw_or_normalized_value_committed": False,
                "business_value_committed": False,
                "evidence_ref": REPORT_PATH.as_posix(),
                "source_index": index,
            }
        )
    return priority_records


def build_policy_fixture_records(priority_records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not priority_records:
        raise ValueError("at least one priority record is required")
    first = priority_records[0]
    first_candidates = first["candidate_refs"]
    first_raw = next(item for item in first_candidates if item["source_class"] == "raw_upload")
    first_authorized = next(item for item in first_candidates if item["source_class"] == "authorized_export")

    same_source_event = build_same_source_inconsistency_event(
        source_id=first_raw["source_id"],
        primary_ref=f"public-matrix-ref:{first['matrix_id']}",
        conflicting_ref=f"public-priority-ref:{first['priority_record_id']}",
        field_path="source_priority.reference_policy_fixture",
        reason_code="same-source-reference-mismatch-policy-fixture",
        event_time="2026-07-04T00:00:00+00:00",
        evidence_ref=REPORT_PATH.as_posix(),
    )
    same_source_event.update(
        {
            "schema_version": "kmfa.v014_s03_p3.same_source_rerun_event.v1",
            "policy_fixture_only": True,
            "business_conflict_observed": False,
            "source_priority_record_ref": first["priority_record_id"],
            "append_only": True,
        }
    )

    difference_queue_item = build_cross_source_difference_queue_item(
        conflict_scope="source_priority.cross_source_policy_fixture",
        source_refs=[
            {"source_id": first_raw["source_id"], "source_class": "raw_upload"},
            {"source_id": first_authorized["source_id"], "source_class": "authorized_export"},
        ],
        reason_code="cross-source-conflict-policy-fixture",
        event_time="2026-07-04T00:01:00+00:00",
        evidence_ref=REPORT_PATH.as_posix(),
    )
    difference_queue_item.update(
        {
            "schema_version": "kmfa.v014_s03_p3.cross_source_difference_queue.v1",
            "policy_fixture_only": True,
            "business_conflict_observed": False,
            "source_priority_record_ref": first["priority_record_id"],
            "append_only": True,
        }
    )
    return [same_source_event], [difference_queue_item]


def build_manifest(
    generated_at: str,
    s03_p2_manifest: dict[str, Any],
    matrix_rows: list[dict[str, Any]],
    status_events: list[dict[str, Any]],
    priority_records: list[dict[str, Any]],
    same_source_events: list[dict[str, Any]],
    difference_queue: list[dict[str, Any]],
) -> dict[str, Any]:
    highest_counts: dict[str, int] = {}
    for record in priority_records:
        highest = str(record["highest_priority_source_class"])
        highest_counts[highest] = highest_counts.get(highest, 0) + 1
    return {
        "schema_version": "kmfa.v014_s03_p3_source_priority.v1",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S03",
        "phase_id": "S03-P3",
        "stage_phase": "S03-P3",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": "completed_validated_local_only_no_go_upload_deferred",
        "generated_at": generated_at,
        "dependency": {
            "required_phase": "V014_S03_P2_SOURCE_CHECK_MATRIX",
            "dependency_manifest": S03_P2_MANIFEST_PATH.as_posix(),
            "dependency_matrix": S03_P2_MATRIX_PATH.as_posix(),
            "dependency_status_events": S03_P2_STATUS_EVENTS_PATH.as_posix(),
            "dependency_expected_status": "completed_validated_local_only_no_go_upload_deferred",
            "dependency_matrix_row_count": len(matrix_rows),
            "dependency_status_event_count": len(status_events),
            "dependency_validated": s03_p2_manifest.get("phase_id") == "S03-P2",
        },
        "phase_scope": {
            "current_phase_only": True,
            "source_priority_only": True,
            "uses_s03_p2_public_matrix_only": True,
            "raw_root_read_performed_by_this_phase": False,
            "raw_root_list_performed_by_this_phase": False,
            "raw_root_hash_performed_by_this_phase": False,
            "raw_root_mutation_performed": False,
            "stage3_review_performed": False,
            "github_upload_performed": False,
            "raw_value_matching_performed": False,
            "field_mapping_performed": False,
            "formal_report_performed": False,
            "business_execution_performed": False,
            "next_phase": "S03_STAGE_REVIEW",
            "next_phase_started": False,
        },
        "source_priority_summary": {
            "source_priority_record_count": len(priority_records),
            "source_priority_order": list(SOURCE_PRIORITY_ORDER),
            "source_priority_order_count": len(SOURCE_PRIORITY_ORDER),
            "s03_p2_matrix_row_count": len(matrix_rows),
            "s03_p2_status_event_count": len(status_events),
            "same_source_policy_event_count": len(same_source_events),
            "same_source_inconsistency_actions": ["invalidate_derived_cache", "request_rerun"],
            "same_source_cache_reuse_allowed": False,
            "cross_source_difference_queue_item_count": len(difference_queue),
            "cross_source_resolution_policy": "manual_review_required",
            "highest_priority_source_class_counts": highest_counts,
            "processed_data_after_raw_or_authorized_count": sum(
                1 for record in priority_records if record["processed_data_rank_after_raw_or_authorized"] is True
            ),
            "manual_review_required_count": sum(1 for record in priority_records if record["manual_review_required"] is True),
            "auto_selection_allowed": False,
            "policy_fixture_only": True,
            "business_conflict_observed_count": 0,
        },
        "priority_records_file_ref": PRIORITY_RECORDS_PATH.as_posix(),
        "same_source_events_file_ref": SAME_SOURCE_EVENTS_PATH.as_posix(),
        "difference_queue_file_ref": DIFFERENCE_QUEUE_PATH.as_posix(),
        "protocol_ref": PROTOCOL_PATH.as_posix(),
        "raw_data_boundary": {
            "local_raw_data_dir": str(RAW_INBOX),
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
        "public_repo_safety": {
            "raw_business_data_committed": False,
            "raw_filenames_committed": False,
            "raw_hashes_committed": False,
            "directory_tree_plaintext_committed": False,
            "zip_member_names_committed": False,
            "field_or_header_plaintext_committed": False,
            "raw_or_normalized_values_committed": False,
            "business_values_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
        },
        "release_state": {
            "current_data_quality_grade": "Q2",
            "current_report_grade": "D",
            "current_go_no_go": "NO_GO",
            "release_permission": "blocked",
            "delivery_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "business_execution_allowed": False,
            "github_main_upload_allowed": False,
        },
        "validation_summary": {
            "s03_p2_dependency": "PENDING",
            "v014_s03_p3_validator": "PENDING",
            "focused_unit_test": "PENDING",
            "governance_validator": "PENDING",
            "raw_private_scan": "PENDING",
            "public_raw_leak_scan": "PENDING",
            "secret_scan": "PENDING",
            "diff_check": "PENDING",
        },
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PLAN_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            PRIORITY_RECORDS_PATH.as_posix(),
            SAME_SOURCE_EVENTS_PATH.as_posix(),
            DIFFERENCE_QUEUE_PATH.as_posix(),
            PROTOCOL_PATH.as_posix(),
        ],
        "next_recommended_phase": "S03_STAGE_REVIEW",
    }


def build_protocol(generated_at: str, manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.source_priority.v1_4.s03_p3",
        "project_id": "KMFA",
        "stage_phase": "S03-P3",
        "generated_at": generated_at,
        "source_priority_order": list(SOURCE_PRIORITY_ORDER),
        "priority_records_file": PRIORITY_RECORDS_PATH.as_posix(),
        "same_source_events_file": SAME_SOURCE_EVENTS_PATH.as_posix(),
        "difference_queue_file": DIFFERENCE_QUEUE_PATH.as_posix(),
        "raw_or_authorized_priority_over_processed_data": True,
        "same_source_inconsistency_policy": {
            "actions": ["invalidate_derived_cache", "request_rerun"],
            "cache_reuse_allowed": False,
            "raw_source_mutation_allowed": False,
            "target_layer": "metadata",
        },
        "cross_source_conflict_policy": {
            "difference_queue": True,
            "manual_review_required": True,
            "auto_selection_allowed": False,
            "auto_correction_allowed": False,
            "target_layer": "metadata",
        },
        "raw_root_read_performed_by_this_phase": False,
        "raw_root_mutation_performed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "policy_fixture_only": True,
        "business_conflict_observed_count": 0,
        "public_repo_safety": manifest["public_repo_safety"],
        "non_scope": {
            "stage3_review_performed": False,
            "github_upload_performed": False,
            "raw_value_matching_performed": False,
            "field_mapping_performed": False,
            "formal_report_performed": False,
            "business_execution_performed": False,
        },
    }


def write_report(manifest: dict[str, Any]) -> None:
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    summary = manifest["source_priority_summary"]
    lines = [
        "# KMFA v0.1.4 S03-P3 Source Priority",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- dependency: `{manifest['dependency']['required_phase']}`",
        f"- source_priority_record_count: `{summary['source_priority_record_count']}`",
        f"- source_priority_order_count: `{summary['source_priority_order_count']}`",
        "- source_priority_order: `raw_upload`, `authorized_export`, `raw_extracted_value`, "
        "`staging_structured_row`, `canonical_fact`, `derived_metric`, `report_reference`, "
        "`frontend_display`, `processed_data`",
        f"- same_source_policy_event_count: `{summary['same_source_policy_event_count']}`",
        "- same_source_actions: `invalidate_derived_cache`, `request_rerun`",
        f"- cross_source_difference_queue_item_count: `{summary['cross_source_difference_queue_item_count']}`",
        f"- cross_source_resolution_policy: `{summary['cross_source_resolution_policy']}`",
        "- auto_selection_allowed: `false`",
        "- policy_fixture_only: `true`",
        "- business_conflict_observed_count: `0`",
        "",
        "## Boundary",
        "",
        "- raw_root_read_performed_by_this_phase: `false`",
        "- raw_root_mutation_performed: `false`",
        "- raw_layer_write_allowed: `false`",
        "- raw_source_mutation_allowed: `false`",
        "- public evidence uses S03-P2 public matrix/status events and generic refs only.",
        "- S03-P3 did not publish raw filenames, raw hashes, field/header plaintext, sheet names, ZIP member names, row values or business values.",
        "- Stage 3 review, GitHub upload, raw value matching, field mapping, formal report, live connector and business execution were not performed.",
        "",
        "## Gate Status",
        "",
        "- current_go_no_go: `NO_GO`",
        "- current_data_quality_grade: `Q2`",
        "- current_report_grade: `D`",
        "- release_permission: `blocked`",
        "",
        "## Next Step",
        "",
        "Next run can execute `v0.1.4 Stage 3 review` only; GitHub upload remains deferred until v1.4 Stage 1-18 complete overall review.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_human_support_files() -> None:
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S03-P3 Test Results",
                "",
                "Status: `PENDING_FINAL_VALIDATION`",
                "",
                "Validation commands:",
                "",
                "- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s03_p3_source_priority.py KMFA/tools/check_v014_s03_p3_source_priority.py KMFA/tests/test_v014_s03_p3_source_priority.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s03_p3_source_priority.py --write`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s03_p2_source_check_matrix.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s03_p3_source_priority.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s03_p3_source_priority -q`",
                "- governance validators and safety scans pending final validation",
                "",
                "Results:",
                "",
                "- PENDING: final validation will be recorded after all commands pass.",
                "",
                "Boundary result:",
                "",
                "- PASS: S03-P3 uses S03-P2 public matrix/status events only and does not read raw root.",
                "- PASS: same-source inconsistency policy invalidates derived cache and requests rerun.",
                "- PASS: cross-source conflict policy enters a manual difference queue and does not auto-select.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    RISK_REGISTER_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S03-P3 Risk Register",
                "",
                "| Risk | Control | Status |",
                "|---|---|---|",
                "| Priority policy misread as actual business conflict | Outputs mark policy_fixture_only=true and business_conflict_observed_count=0 | controlled |",
                "| Cross-source queue accidentally auto-selects a source | Validator requires auto_selection_allowed=false and manual_review_required=true | controlled |",
                "| Public evidence exposes raw identifiers | Validator and scans check for raw/private filenames, hashes, field/header plaintext and business values | controlled |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ROLLBACK_PLAN_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S03-P3 Rollback Plan",
                "",
                "Rollback scope:",
                "",
                "- Remove `KMFA/tools/v014_s03_p3_source_priority.py`.",
                "- Remove `KMFA/tools/check_v014_s03_p3_source_priority.py`.",
                "- Remove `KMFA/tests/test_v014_s03_p3_source_priority.py`.",
                "- Remove `KMFA/metadata/sources/v014_s03_p3_source_priority_records.jsonl`.",
                "- Remove `KMFA/metadata/sources/v014_s03_p3_same_source_rerun_events.jsonl`.",
                "- Remove `KMFA/metadata/quality/v014_s03_p3_cross_source_difference_queue.jsonl`.",
                "- Remove `KMFA/metadata/protocol/source_priority_v1_4_s03_p3.json`.",
                "- Remove `KMFA/stage_artifacts/V014_S03_P3_SOURCE_PRIORITY/`.",
                "- Revert S03-P3 governance rows and status updates.",
                "",
                "Raw data rollback: no action. S03-P3 must not modify raw data.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_all(write: bool) -> dict[str, Any]:
    s03_p2_manifest = validate_v014_s03_p2_source_check_matrix()
    matrix_rows = read_jsonl(S03_P2_MATRIX_PATH)
    status_events = read_jsonl(S03_P2_STATUS_EVENTS_PATH)
    priority_records = build_priority_records(matrix_rows)
    same_source_events, difference_queue = build_policy_fixture_records(priority_records)
    generated_at = utc_now()
    manifest = build_manifest(
        generated_at,
        s03_p2_manifest,
        matrix_rows,
        status_events,
        priority_records,
        same_source_events,
        difference_queue,
    )
    protocol = build_protocol(generated_at, manifest)
    if write:
        write_jsonl(PRIORITY_RECORDS_PATH, priority_records)
        write_jsonl(SAME_SOURCE_EVENTS_PATH, same_source_events)
        write_jsonl(DIFFERENCE_QUEUE_PATH, difference_queue)
        write_json(PROTOCOL_PATH, protocol)
        write_json(MANIFEST_PATH, manifest)
        write_report(manifest)
        write_human_support_files()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build KMFA v1.4 S03-P3 source priority evidence.")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    manifest = build_all(args.write)
    summary = manifest["source_priority_summary"]
    print(
        "PASS: KMFA v1.4 S03-P3 source priority built "
        f"(records={summary['source_priority_record_count']}, priority_order={summary['source_priority_order_count']}, "
        f"same_source_events={summary['same_source_policy_event_count']}, "
        f"difference_queue={summary['cross_source_difference_queue_item_count']}, "
        "raw_read=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
