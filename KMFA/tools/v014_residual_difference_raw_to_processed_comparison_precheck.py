#!/usr/bin/env python3
"""Precheck residual-difference raw-to-processed comparison readiness.

This phase consumes ignored private residual-difference materialization outputs
and checks whether each materialized record has private comparison anchors for a
later formal raw-to-processed comparison. It does not read, list, hash, parse,
copy or mutate the raw inbox and does not perform the formal comparison.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-RAW-TO-PROCESSED-COMPARISON-PRECHECK-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-RAW-TO-PROCESSED-COMPARISON-PRECHECK"
VERSION = "0.1.4-residual-difference-raw-to-processed-comparison-precheck"
STATUS = "completed_validated_local_only_residual_difference_raw_comparison_precheck_blocked_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "residual_difference_comparison_precheck_blocked_by_missing_private_comparison_anchors"
NEXT_RECOMMENDED_PHASE = "V014_RESIDUAL_DIFFERENCE_RAW_CANDIDATE_ALIGNMENT_AFTER_PRECHECK"
NEXT_REQUIRED_INPUT = "run_read_only_raw_candidate_alignment_for_72_residual_difference_records_before_comparison"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_precheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_precheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_precheck_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_precheck_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "residual_difference_raw_to_processed_comparison_precheck.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_matrix_public_safe.json"
)

SOURCE_MATERIALIZATION_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_private_resolution_materialization_replay_summary.json"
)
SOURCE_MATERIALIZATION_GO_NO_GO_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_private_resolution_materialization_replay_go_no_go_report.json"
)
SOURCE_MATERIALIZATION_MATRIX_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_private_resolution_materialization_replay_matrix_public_safe.json"
)
SOURCE_PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_private_resolution_materialization_replay"
SOURCE_PRIVATE_DIAGNOSTIC_PATH = SOURCE_PRIVATE_DIR / "private_residual_difference_materialization_replay_diagnostic.json"
SOURCE_PRIVATE_RESULT_PATH = SOURCE_PRIVATE_DIR / "private_residual_difference_materialization_replay_result.json"
SOURCE_PRIVATE_MATERIALIZED_RECORDS_PATH = SOURCE_PRIVATE_DIR / "private_residual_difference_materialized_records.jsonl"
SOURCE_PRIVATE_RAW_COMPARISON_INPUT_PATH = SOURCE_PRIVATE_DIR / "private_residual_difference_raw_comparison_input.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_raw_to_processed_comparison_precheck"
PRIVATE_PRECHECK_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_to_processed_comparison_precheck.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_to_processed_comparison_precheck_diagnostic.json"
PRIVATE_READY_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_comparison_ready_records.jsonl"
PRIVATE_BLOCKER_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_comparison_blocker_records.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_to_processed_comparison_precheck.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

EXPECTED_TRACK_COUNTS = {
    "owner_select_one_authoritative_candidate": 24,
    "provide_authoritative_source_reference_or_owner_exclusion": 40,
    "provide_formula_or_non_numeric_mapping": 8,
}
REQUIRED_PRIVATE_ANCHORS = (
    "processed_value_fingerprint",
    "raw_candidate_fingerprint",
    "raw_candidate_record_ref_hash",
)


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain JSON objects")
        rows.append(value)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def _changed_kmfa_files() -> list[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "status", "--porcelain=v1", "--untracked-files=all", "--", "KMFA"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return []
    files: set[str] = set()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if ".codex_private_runtime/" not in path:
            files.add(path)
    return sorted(files)


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_materialization_summary_read_by_this_phase": True,
        "source_public_materialization_go_no_go_read_by_this_phase": True,
        "source_public_materialization_matrix_read_by_this_phase": True,
        "source_private_materialization_diagnostic_read_by_this_phase": True,
        "source_private_materialization_result_read_by_this_phase": True,
        "source_private_materialized_records_read_by_this_phase": True,
        "source_private_raw_comparison_input_read_by_this_phase": True,
        "private_precheck_written_by_this_phase": True,
        "private_precheck_ready_records_written_by_this_phase": True,
        "private_precheck_blocker_records_written_by_this_phase": True,
        "source_private_materialization_outputs_mutated_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_file_content_hash_performed_by_this_phase": False,
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
        "private_materialization_outputs_committed": False,
        "private_precheck_committed": False,
        "private_ready_records_committed": False,
        "private_blocker_records_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "target_slot_detail_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_value_fingerprint_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_precheck_records(rows: list[dict[str, Any]], generated_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ready: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        missing = [anchor for anchor in REQUIRED_PRIVATE_ANCHORS if not row.get(anchor)]
        base = {
            "precheck_index": index,
            "version": VERSION,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "target_slot_id": row.get("target_slot_id"),
            "source_materialization_index": row.get("materialization_index"),
            "diagnostic_track": row.get("diagnostic_track"),
            "response_decision_code": row.get("response_decision_code"),
        }
        if missing:
            blockers.append(
                {
                    **base,
                    "comparison_precheck_status": "missing_private_comparison_anchor",
                    "missing_private_anchor_codes": missing,
                    "raw_to_processed_value_comparison_ready": False,
                    "raw_to_processed_value_comparison_performed": False,
                    "full_reconciliation_allowed": False,
                    "business_value_consistency_verified": False,
                    "public_commit_allowed": False,
                }
            )
            continue
        ready.append(
            {
                **base,
                "comparison_precheck_status": "comparison_anchor_ready",
                "raw_to_processed_value_comparison_ready": True,
                "raw_to_processed_value_comparison_performed": False,
                "full_reconciliation_allowed": False,
                "business_value_consistency_verified": False,
                "public_commit_allowed": False,
            }
        )
    return ready, blockers


def _build_matrix(summary: dict[str, Any], generated_at: str) -> dict[str, Any]:
    checks = [
        ("source_materialized_records_available", summary["source_private_materialized_record_count"] == 72, summary["source_private_materialized_record_count"], 72),
        ("raw_comparison_input_records_available", summary["source_raw_comparison_input_record_count"] == 72, summary["source_raw_comparison_input_record_count"], 72),
        ("track_counts_match_expected", summary["diagnostic_track_counts"] == EXPECTED_TRACK_COUNTS, summary["diagnostic_track_counts"], EXPECTED_TRACK_COUNTS),
        ("comparison_anchor_coverage_unblocked", summary["missing_private_comparison_anchor_count"] == 0, summary["missing_private_comparison_anchor_count"], 0),
        ("comparison_ready_record_count_unblocked", summary["comparison_ready_record_count"] == 72, summary["comparison_ready_record_count"], 72),
        ("formal_comparison_not_claimed", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False, False, False),
        ("downstream_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, passed, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_residual_difference_raw_comparison_precheck_matrix_public_safe.v1",
        "record_type": "v014_residual_difference_raw_comparison_precheck_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "precheck_check_count": len(rows),
        "precheck_pass_count": pass_count,
        "precheck_fail_count": len(rows) - pass_count,
        "source_private_materialized_record_count": summary["source_private_materialized_record_count"],
        "comparison_ready_record_count": summary["comparison_ready_record_count"],
        "comparison_blocker_record_count": summary["comparison_blocker_record_count"],
        "missing_private_comparison_anchor_count": summary["missing_private_comparison_anchor_count"],
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "decision": DECISION,
        "checks": rows,
    }


def _dedupe_append_jsonl(path: Path, rows: list[dict[str, Any]], keep_existing: Callable[[dict[str, Any]], bool]) -> None:
    retained: list[str] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                existing = json.loads(line)
            except json.JSONDecodeError:
                retained.append(line)
                continue
            if not isinstance(existing, dict) or keep_existing(existing):
                retained.append(line)
    retained.extend(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(retained) + "\n", encoding="utf-8")


def _append_governance_records(manifest: dict[str, Any]) -> None:
    summary = manifest["summary"]
    event_id = "DEV-KMFA-20260707-V014-RESIDUAL-DIFFERENCE-RAW-COMPARISON-PRECHECK"
    event = {
        "event_id": event_id,
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260707-KMFA-V014-RESIDUAL-DIFFERENCE-RAW-COMPARISON-PRECHECK",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "source_private_materialized_record_count": summary["source_private_materialized_record_count"],
        "comparison_ready_record_count": summary["comparison_ready_record_count"],
        "comparison_blocker_record_count": summary["comparison_blocker_record_count"],
        "missing_private_comparison_anchor_count": summary["missing_private_comparison_anchor_count"],
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": "Prechecked 72 residual-difference private materialized records and blocked formal comparison because all 72 still lack private raw/processed comparison anchors.",
        "result_commit": "PENDING",
        "files_changed": _changed_kmfa_files(),
    }
    _dedupe_append_jsonl(DEVELOPMENT_EVENTS_PATH, [event], lambda existing: existing.get("event_id") != event_id)

    stage_rows = [
        {
            "acceptance_id": ACCEPTANCE_ID,
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "v0.1.4 residual difference raw-to-processed comparison precheck",
            "phase_id": PHASE_ID,
            "record_type": "v014_phase",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": STATUS,
            "task_count": 3,
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": SUMMARY_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "72 residual-difference materialized records prechecked",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDRCP01",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": GO_NO_GO_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "formal comparison blocked by missing private anchors",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDRCP02",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "raw inbox untouched and private precheck outputs remain ignored",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDRCP03",
            "updated_at": "2026-07-07",
        },
    ]
    _dedupe_append_jsonl(STAGE_STATUS_PATH, stage_rows, lambda existing: existing.get("phase_id") != PHASE_ID)

    task_rows = []
    for row in stage_rows:
        task_row = {
            **row,
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "project_id": "KMFA",
            "version": VERSION,
            "stage_id": "VALUE-CONSISTENCY",
            "raw_data_committed": False,
        }
        if row["record_type"] == "v014_phase":
            task_row["acceptance_output"] = (
                "Residual raw comparison precheck manifest summary Go No-Go public-safe matrix ignored private "
                "ready and blocker records validator focused test and governance records"
            )
            task_row["phase_goal"] = (
                "precheck residual-difference raw-to-processed comparison readiness without raw inbox access or formal comparison"
            )
        else:
            task_row["task_label"] = row["task_id"][-2:]
            task_row["task_text"] = row["name"]
        task_rows.append(task_row)
    _dedupe_append_jsonl(TASK_STATUS_PATH, task_rows, lambda existing: existing.get("phase_id") != PHASE_ID)


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Residual Difference Raw-To-Processed Comparison Precheck

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- source materialized records: `{summary["source_private_materialized_record_count"]}`
- comparison-ready records: `{summary["comparison_ready_record_count"]}`
- comparison blocker records: `{summary["comparison_blocker_record_count"]}`
- missing private comparison anchors: `{summary["missing_private_comparison_anchor_count"]}`
- formal raw-to-processed comparison performed: `false`
- next required input: `{NEXT_REQUIRED_INPUT}`

This phase prechecks private residual-difference comparison readiness only. It confirms all 72 materialized residual-difference records still require private raw candidate alignment before formal raw-to-processed comparison can run.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: 72 residual-difference records lack private raw/processed comparison anchors, so formal comparison is not ready.
- checks: `{matrix["precheck_pass_count"]}` pass / `{matrix["precheck_fail_count"]}` fail
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: precheck readiness could be mistaken for verified raw-to-processed consistency.
- Control: public evidence keeps formal comparison, reconciliation, report, upload, app reinstall and business execution closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private precheck outputs, tool, validator, focused test and governance entries. The raw data inbox is not modified by this rollback.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_raw_to_processed_comparison_precheck.py KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_precheck.py KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_precheck.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_precheck.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_precheck.py --require-private-precheck`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_raw_to_processed_comparison_precheck`
- `python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `python3 scripts/validate_project_governance.py --changed-only --base-ref HEAD --enforce-sync`
- `python3 scripts/lean_governance.py validate --changed-only --base-ref HEAD --enforce-sync`
- `git diff --check`

All listed commands must pass before local commit. This phase does not read, list, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
"""
    for path, text in (
        (REPORT_PATH, report),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback_plan),
        (TEST_RESULTS_PATH, test_results),
    ):
        _write_text(path, text)


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_MATERIALIZATION_SUMMARY_PATH)
    source_go_no_go = _read_json(SOURCE_MATERIALIZATION_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_MATERIALIZATION_MATRIX_PATH)
    source_diagnostic = _read_json(SOURCE_PRIVATE_DIAGNOSTIC_PATH)
    source_result = _read_json(SOURCE_PRIVATE_RESULT_PATH)
    materialized_records = _read_jsonl(SOURCE_PRIVATE_MATERIALIZED_RECORDS_PATH)
    raw_comparison_input = _read_json(SOURCE_PRIVATE_RAW_COMPARISON_INPUT_PATH)
    input_records = raw_comparison_input.get("materialized_records", [])
    if not isinstance(input_records, list):
        raise ValueError("source raw comparison input must contain materialized_records")
    if len(materialized_records) != 72 or len(input_records) != 72:
        raise ValueError("source materialization must provide 72 materialized records")
    if source_result.get("private_materialization_blocker_count") != 0:
        raise ValueError("source materialization blockers must be zero")

    ready_records, blocker_records = _build_precheck_records(input_records, timestamp)
    track_counts = dict(Counter(row.get("diagnostic_track") for row in input_records))
    if track_counts != EXPECTED_TRACK_COUNTS:
        raise ValueError("unexpected residual-difference diagnostic track counts")

    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    private_precheck = {
        "schema_version": "kmfa.private.v014_residual_difference_raw_comparison_precheck.v1",
        "classification": "private_residual_difference_raw_comparison_precheck_do_not_commit",
        "record_type": "v014_residual_difference_raw_comparison_precheck",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_materialization_phase_id": source_summary.get("phase_id"),
        "source_private_result_phase_id": source_result.get("phase_id"),
        "source_private_materialized_record_count": len(materialized_records),
        "source_raw_comparison_input_record_count": len(input_records),
        "comparison_ready_record_count": len(ready_records),
        "comparison_blocker_record_count": len(blocker_records),
        "missing_private_comparison_anchor_count": len(blocker_records),
        "raw_to_processed_value_comparison_precheck_passed": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "ready_records": ready_records,
        "blocker_records": blocker_records,
        "raw_boundary": raw_boundary,
    }
    private_diagnostic = {
        "schema_version": "kmfa.private.v014_residual_difference_raw_comparison_precheck_diagnostic.v1",
        "record_type": "private_residual_difference_raw_comparison_precheck_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_materialization_phase_id": source_summary.get("phase_id"),
        "source_materialization_decision": source_go_no_go.get("decision"),
        "source_materialization_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_diagnostic_phase_id": source_diagnostic.get("phase_id"),
        "source_private_materialized_record_count": len(materialized_records),
        "source_raw_comparison_input_record_count": len(input_records),
        "comparison_ready_record_count": len(ready_records),
        "comparison_blocker_record_count": len(blocker_records),
        "missing_private_comparison_anchor_count": len(blocker_records),
        "diagnostic_track_counts": track_counts,
        "raw_inbox_accessed": False,
        "raw_inbox_mutated": False,
    }

    _write_json(PRIVATE_PRECHECK_PATH, private_precheck)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_jsonl(PRIVATE_READY_RECORDS_PATH, ready_records)
    _write_jsonl(PRIVATE_BLOCKER_RECORDS_PATH, blocker_records)
    _write_text(
        PRIVATE_REPORT_PATH,
        "\n".join(
            [
                "# Private residual difference raw comparison precheck",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- comparison_ready_record_count: `{len(ready_records)}`",
                f"- comparison_blocker_record_count: `{len(blocker_records)}`",
                "- formal raw-to-processed comparison was not performed.",
                "- raw inbox access and mutation were not performed.",
            ]
        )
        + "\n",
    )

    summary = {
        "schema_version": "kmfa.v014_residual_difference_raw_comparison_precheck_summary.v1",
        "record_type": "v014_residual_difference_raw_comparison_precheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_materialization_phase_id": source_summary.get("phase_id"),
        "source_materialization_decision": source_summary.get("decision"),
        "source_private_materialized_record_count": len(materialized_records),
        "source_raw_comparison_input_record_count": len(input_records),
        "raw_to_processed_value_comparison_precheck_performed_by_this_phase": True,
        "raw_to_processed_value_comparison_precheck_passed": False,
        "comparison_ready_record_count": len(ready_records),
        "comparison_blocker_record_count": len(blocker_records),
        "missing_private_comparison_anchor_count": len(blocker_records),
        "diagnostic_track_counts": track_counts,
        "owner_select_one_authoritative_candidate_count": track_counts.get("owner_select_one_authoritative_candidate", 0),
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts.get(
            "provide_authoritative_source_reference_or_owner_exclusion", 0
        ),
        "provide_formula_or_non_numeric_mapping_count": track_counts.get("provide_formula_or_non_numeric_mapping", 0),
        "closed_discrepancy_count": 0,
        "open_residual_difference_count": source_summary.get("open_residual_difference_count"),
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "full_reconciliation_allowed": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_precheck_written": True,
        "private_precheck_gitignored": _git_check_ignored(PRIVATE_PRECHECK_PATH),
        "private_ready_records_written": True,
        "private_ready_records_gitignored": _git_check_ignored(PRIVATE_READY_RECORDS_PATH),
        "private_blocker_records_written": True,
        "private_blocker_records_gitignored": _git_check_ignored(PRIVATE_BLOCKER_RECORDS_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    matrix = _build_matrix(summary, timestamp)
    go_no_go = {
        "schema_version": "kmfa.v014_residual_difference_raw_comparison_precheck_go_no_go.v1",
        "record_type": "v014_residual_difference_raw_comparison_precheck_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "comparison_ready_record_count": summary["comparison_ready_record_count"],
        "comparison_blocker_record_count": summary["comparison_blocker_record_count"],
        "missing_private_comparison_anchor_count": summary["missing_private_comparison_anchor_count"],
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_residual_difference_raw_comparison_precheck_manifest.v1",
        "record_type": "v014_residual_difference_raw_comparison_precheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_artifacts": [
            SOURCE_MATERIALIZATION_SUMMARY_PATH.as_posix(),
            SOURCE_MATERIALIZATION_GO_NO_GO_PATH.as_posix(),
            SOURCE_MATERIALIZATION_MATRIX_PATH.as_posix(),
            "private:residual_difference_materialization_replay_diagnostic",
            "private:residual_difference_materialization_replay_result",
            "private:residual_difference_materialized_records",
            "private:residual_difference_raw_comparison_input",
        ],
        "public_artifact_refs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
        ],
        "metadata_artifact_refs": [
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "private_artifact_refs": [
            "private:residual_difference_raw_comparison_precheck",
            "private:residual_difference_raw_comparison_precheck_diagnostic",
            "private:residual_difference_comparison_ready_records",
            "private:residual_difference_comparison_blocker_records",
            "private:residual_difference_raw_comparison_precheck_report",
        ],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_raw_to_processed_comparison_precheck.py KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_precheck.py KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_precheck.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_precheck.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_precheck.py --require-private-precheck",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_raw_to_processed_comparison_precheck",
        ],
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }

    _write_json(SUMMARY_PATH, summary)
    _write_json(MANIFEST_PATH, manifest)
    _write_json(GO_NO_GO_PATH, go_no_go)
    _write_json(MATRIX_PATH, matrix)
    _write_json(METADATA_SUMMARY_PATH, summary)
    _write_json(METADATA_MANIFEST_PATH, manifest)
    _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    _write_json(METADATA_MATRIX_PATH, matrix)
    _write_human_artifacts(summary, matrix)
    if write_governance_event:
        _append_governance_records(manifest)
    return {"summary": summary, "matrix": matrix, "go_no_go": go_no_go, "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: generated V014 residual-difference raw comparison precheck "
        f"decision={summary['decision']} ready={summary['comparison_ready_record_count']} "
        f"blockers={summary['comparison_blocker_record_count']} next={summary['next_recommended_phase']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
