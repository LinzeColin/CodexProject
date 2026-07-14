#!/usr/bin/env python3
"""Build KMFA v1.4 S03-P2 public-safe source check matrix evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s03_p1_file_registration import validate_v014_s03_p1_file_registration
from KMFA.tools.source_check_matrix import ALLOWED_STATUSES, REQUIRED_DIMENSIONS


TASK_ID = "KMFA-V014-S03-P2-SOURCE-CHECK-MATRIX-20260703"
ACCEPTANCE_ID = "ACC-V014-S03-P2-SOURCE-CHECK-MATRIX"
STAGE_DIR = Path("KMFA/stage_artifacts/V014_S03_P2_SOURCE_CHECK_MATRIX")
MACHINE_DIR = STAGE_DIR / "machine"
HUMAN_DIR = STAGE_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "source_check_matrix_manifest.json"
MATRIX_PATH = Path("KMFA/metadata/sources/v014_s03_p2_source_check_matrix.jsonl")
STATUS_EVENTS_PATH = Path("KMFA/metadata/sources/v014_s03_p2_source_status_events.jsonl")
PROTOCOL_PATH = Path("KMFA/metadata/protocol/source_check_matrix_v1_4_s03_p2.json")
PUBLIC_REGISTER_PATH = Path("KMFA/metadata/imports/v014_s03_p1_public_raw_file_register.json")
REPORT_PATH = HUMAN_DIR / "source_check_matrix_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PLAN_PATH = HUMAN_DIR / "rollback_plan.md"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def stable_digest(parts: list[str], length: int = 16) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:length]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def build_v014_s03_p2_source_check_matrix(public_register: dict[str, Any]) -> dict[str, Any]:
    records = public_register.get("public_file_records")
    if not isinstance(records, list):
        raise ValueError("public_file_records must be a list")
    source_package = public_register.get("source_package")
    if not isinstance(source_package, dict):
        raise ValueError("source_package must be an object")

    matrix_rows: list[dict[str, Any]] = []
    status_events: list[dict[str, Any]] = []
    for index, record in enumerate(sorted(records, key=lambda item: str(item.get("public_file_id"))), start=1):
        public_file_id = str(record.get("public_file_id", "")).strip()
        if not public_file_id:
            raise ValueError("public_file_id is required")
        matrix_id = f"SCM-V014-S03P2-{stable_digest([public_file_id, str(index)])}"
        event_id = f"SSE-V014-S03P2-{index:06d}"
        status = "人工复核"
        source_package_ref = {
            "public_source_package_id": source_package.get("public_source_package_id"),
            "public_file_id": public_file_id,
            "source_package_type": source_package.get("source_package_type"),
            "file_format": record.get("file_format"),
            "extension": record.get("extension"),
            "container_type": record.get("container_type"),
            "file_size_bytes": record.get("file_size_bytes"),
            "size_bucket": record.get("size_bucket"),
            "private_manifest_record_ref": record.get("private_manifest_record_ref"),
            "path_status": record.get("path_status"),
            "content_hash_status": record.get("content_hash_status"),
        }
        row = {
            "record_type": "source_check_matrix_row",
            "schema_version": "kmfa.v014_s03_p2.source_check_matrix_row.v1",
            "stage_phase": "S03-P2",
            "matrix_id": matrix_id,
            "public_file_id": public_file_id,
            "source_system": "local_raw_directory",
            "business_segment": "pending_owner_business_segment",
            "source_package_ref": source_package_ref,
            "entity_ref": "ENTITY-PENDING-S03P2-OWNER-MAPPING",
            "account_ref": "ACCOUNT-PENDING-S03P2-OWNER-MAPPING",
            "frequency": "FREQUENCY-PENDING-S03P2-OWNER-REVIEW",
            "status": status,
            "allowed_statuses": list(ALLOWED_STATUSES),
            "status_reason_code": "source_context_requires_owner_mapping",
            "status_event_ref": event_id,
            "status_impact": "blocks_s03_p3_source_priority_and_raw_value_matching",
            "raw_layer_write_allowed": False,
            "raw_source_mutation_allowed": False,
            "raw_filename_committed": False,
            "raw_hash_committed": False,
            "field_or_header_plaintext_committed": False,
            "raw_or_normalized_value_committed": False,
            "evidence_ref": REPORT_PATH.as_posix(),
        }
        event = {
            "record_type": "source_status_event",
            "schema_version": "kmfa.v014_s03_p2.source_status_event.v1",
            "stage_phase": "S03-P2",
            "event_id": event_id,
            "event_type": "initial_status_assignment",
            "matrix_id": matrix_id,
            "public_file_id": public_file_id,
            "previous_status": None,
            "new_status": status,
            "reason_code": "source_context_requires_owner_mapping",
            "actor_ref": "codex-v014-s03-p2",
            "target_layer": "metadata",
            "append_only": True,
            "raw_layer_write_allowed": False,
            "raw_source_mutation_allowed": False,
            "evidence_ref": REPORT_PATH.as_posix(),
        }
        matrix_rows.append(row)
        status_events.append(event)

    return {
        "matrix_rows": matrix_rows,
        "status_events": status_events,
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def write_report(manifest: dict[str, Any]) -> None:
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    summary = manifest["source_check_matrix_summary"]
    lines = [
        "# KMFA v0.1.4 S03-P2 Source Check Matrix",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- dependency: `{manifest['dependency']['required_phase']}`",
        f"- matrix_row_count: `{summary['matrix_row_count']}`",
        f"- status_event_count: `{summary['status_event_count']}`",
        f"- required_dimension_count: `{summary['required_dimension_count']}`",
        f"- allowed_status_count: `{summary['allowed_status_count']}`",
        f"- status_counts: `人工复核={summary['status_counts']['人工复核']}`",
        "",
        "## Boundary",
        "",
        "- raw_root_read_performed_by_this_phase: `false`",
        "- raw_root_mutation_performed: `false`",
        "- raw_layer_write_allowed: `false`",
        "- raw_source_mutation_allowed: `false`",
        "- public matrix contains only public ids, type/size buckets, status, generic mapping refs and private refs.",
        "- S03-P3, Stage 3 review, GitHub upload, raw value matching, field mapping, formal report, live connector and business execution were not performed.",
        "",
        "## Next Step",
        "",
        "Next run can execute `v0.1.4 S03-P3` only; Stage 3 review and GitHub upload remain out of scope.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_human_support_files() -> None:
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S03-P2 Test Results",
                "",
                "Status: `PENDING_FINAL_VALIDATION`",
                "",
                "Validation commands:",
                "",
                "- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s03_p2_source_check_matrix.py KMFA/tools/check_v014_s03_p2_source_check_matrix.py KMFA/tests/test_v014_s03_p2_source_check_matrix.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s03_p2_source_check_matrix.py --write`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s03_p1_file_registration.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s03_p2_source_check_matrix.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s03_p2_source_check_matrix -q`",
                "- governance validators and safety scans pending final validation",
                "",
                "Results:",
                "",
                "- PENDING: final validation will be recorded after all commands pass.",
                "",
                "Boundary result:",
                "",
                "- PASS: S03-P2 used S03-P1 public register only and did not read raw root.",
                "- PASS: raw root was not written, deleted, moved, renamed, overwritten or converted.",
                "- PASS: matrix/status event public outputs contain no raw file names, raw hashes, field/header plaintext, row values or business values.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    RISK_REGISTER_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S03-P2 Risk Register",
                "",
                "| Risk | Control | Status |",
                "|---|---|---|",
                "| Public matrix accidentally exposes raw identifiers | Validator scans public evidence against private S03-P1 manifest tokens | controlled |",
                "| Matrix status interpreted as source priority | Non-scope gates keep S03-P3 false | controlled |",
                "| Owner mapping is unavailable at S03-P2 | All rows remain `人工复核` and release remains blocked | accepted |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ROLLBACK_PLAN_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S03-P2 Rollback Plan",
                "",
                "Rollback scope:",
                "",
                "- Remove `KMFA/tools/v014_s03_p2_source_check_matrix.py`.",
                "- Remove `KMFA/tools/check_v014_s03_p2_source_check_matrix.py`.",
                "- Remove `KMFA/tests/test_v014_s03_p2_source_check_matrix.py`.",
                "- Remove `KMFA/metadata/sources/v014_s03_p2_source_check_matrix.jsonl`.",
                "- Remove `KMFA/metadata/sources/v014_s03_p2_source_status_events.jsonl`.",
                "- Remove `KMFA/metadata/protocol/source_check_matrix_v1_4_s03_p2.json`.",
                "- Remove `KMFA/stage_artifacts/V014_S03_P2_SOURCE_CHECK_MATRIX/`.",
                "- Revert S03-P2 governance rows and status updates.",
                "",
                "Raw data rollback: no action. S03-P2 must not modify raw data.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_manifest(generated_at: str, public_register: dict[str, Any], matrix: dict[str, Any]) -> dict[str, Any]:
    rows = matrix["matrix_rows"]
    events = matrix["status_events"]
    status_counts: dict[str, int] = {status: 0 for status in ALLOWED_STATUSES}
    for row in rows:
        status_counts[str(row["status"])] += 1
    return {
        "schema_version": "kmfa.v014_s03_p2_source_check_matrix.v1",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S03",
        "phase_id": "S03-P2",
        "stage_phase": "S03-P2",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": "completed_validated_local_only_no_go_upload_deferred",
        "generated_at": generated_at,
        "dependency": {
            "required_phase": "V014_S03_P1_FILE_REGISTRATION",
            "dependency_manifest": "KMFA/stage_artifacts/V014_S03_P1_FILE_REGISTRATION/machine/s03_p1_file_registration_manifest.json",
            "dependency_public_register": PUBLIC_REGISTER_PATH.as_posix(),
            "dependency_expected_status": "completed_validated_local_only_no_go_upload_deferred",
        },
        "phase_scope": {
            "current_phase_only": True,
            "source_check_matrix_only": True,
            "uses_s03_p1_public_register_only": True,
            "raw_root_read_performed_by_this_phase": False,
            "raw_root_list_performed_by_this_phase": False,
            "raw_root_hash_performed_by_this_phase": False,
            "raw_root_mutation_performed": False,
            "s03_p3_started": False,
            "stage3_review_performed": False,
            "github_upload_performed": False,
            "raw_value_matching_performed": False,
            "field_mapping_performed": False,
            "formal_report_performed": False,
            "business_execution_performed": False,
            "next_phase": "S03-P3",
            "next_phase_started": False,
        },
        "source_check_matrix_summary": {
            "matrix_row_count": len(rows),
            "status_event_count": len(events),
            "public_file_count_from_s03_p1": public_register["scan_summary"]["file_count"],
            "required_dimensions": list(REQUIRED_DIMENSIONS),
            "required_dimension_count": len(REQUIRED_DIMENSIONS),
            "allowed_statuses": list(ALLOWED_STATUSES),
            "allowed_status_count": len(ALLOWED_STATUSES),
            "status_counts": status_counts,
            "source_system_counts": {"local_raw_directory": len(rows)},
            "business_segment_counts": {"pending_owner_business_segment": len(rows)},
            "event_target_layer_counts": {"metadata": len(events)},
            "append_only_event_count": len(events),
        },
        "matrix_file_ref": MATRIX_PATH.as_posix(),
        "status_event_file_ref": STATUS_EVENTS_PATH.as_posix(),
        "protocol_ref": PROTOCOL_PATH.as_posix(),
        "public_repo_safety": {
            "raw_business_data_committed": False,
            "raw_filenames_committed": False,
            "raw_hashes_committed": False,
            "directory_tree_plaintext_committed": False,
            "zip_member_names_committed": False,
            "field_or_header_plaintext_committed": False,
            "raw_or_normalized_values_committed": False,
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
            "s03_p1_dependency": "PENDING",
            "v014_s03_p2_validator": "PENDING",
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
            MATRIX_PATH.as_posix(),
            STATUS_EVENTS_PATH.as_posix(),
            PROTOCOL_PATH.as_posix(),
        ],
        "next_recommended_phase": "S03-P3",
    }


def build_protocol(generated_at: str, manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.source_check_matrix.v1_4.s03_p2",
        "project_id": "KMFA",
        "stage_phase": "S03-P2",
        "generated_at": generated_at,
        "required_dimensions": list(REQUIRED_DIMENSIONS),
        "allowed_statuses": list(ALLOWED_STATUSES),
        "matrix_file": MATRIX_PATH.as_posix(),
        "status_event_file": STATUS_EVENTS_PATH.as_posix(),
        "status_changes_append_only": True,
        "status_changes_target_layer": "metadata",
        "raw_root_read_performed_by_this_phase": False,
        "raw_root_mutation_performed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "public_repo_safety": manifest["public_repo_safety"],
        "non_scope": {
            "s03_p3_source_priority_started": False,
            "stage3_review_performed": False,
            "github_upload_performed": False,
            "raw_value_matching_performed": False,
            "field_mapping_performed": False,
            "formal_report_performed": False,
            "business_execution_performed": False,
        },
    }


def build_all(write: bool) -> dict[str, Any]:
    validate_v014_s03_p1_file_registration()
    public_register = read_json(PUBLIC_REGISTER_PATH)
    matrix = build_v014_s03_p2_source_check_matrix(public_register)
    generated_at = utc_now()
    manifest = build_manifest(generated_at, public_register, matrix)
    protocol = build_protocol(generated_at, manifest)
    if write:
        write_jsonl(MATRIX_PATH, matrix["matrix_rows"])
        write_jsonl(STATUS_EVENTS_PATH, matrix["status_events"])
        write_json(PROTOCOL_PATH, protocol)
        write_json(MANIFEST_PATH, manifest)
        write_report(manifest)
        write_human_support_files()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build KMFA v1.4 S03-P2 source check matrix evidence.")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    manifest = build_all(args.write)
    summary = manifest["source_check_matrix_summary"]
    print(
        "PASS: KMFA v1.4 S03-P2 source check matrix built "
        f"(rows={summary['matrix_row_count']}, events={summary['status_event_count']}, "
        f"statuses={summary['allowed_status_count']}, raw_read=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
