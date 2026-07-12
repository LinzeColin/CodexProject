#!/usr/bin/env python3
"""Precheck full raw-to-processed comparison after full materialization.

This phase consumes ignored private runtime artifacts only: the full
materialized processed-value replay and the private raw-derived candidate
catalog. It does not read, list, hash, parse, copy or mutate the raw inbox.
Public artifacts contain aggregate counts and the expected blocker state only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_FULL_RAW_TO_PROCESSED_COMPARISON_PRECHECK_AFTER_FULL_MATERIALIZATION"
TASK_ID = "KMFA-V014-FULL-RAW-TO-PROCESSED-COMPARISON-PRECHECK-AFTER-FULL-MATERIALIZATION-20260707"
ACCEPTANCE_ID = "ACC-V014-FULL-RAW-TO-PROCESSED-COMPARISON-PRECHECK-AFTER-FULL-MATERIALIZATION"
VERSION = "0.1.4-full-raw-to-processed-comparison-precheck-after-full-materialization"
STATUS = "completed_validated_local_only_full_comparison_precheck_blocked_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "full_comparison_precheck_blocked_by_outside_scope_missing_raw_candidate_records"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_RAW_CANDIDATE_ALIGNMENT_AFTER_FULL_PRECHECK"
NEXT_REQUIRED_INPUT = "resolve_72_outside_scope_materialized_records_missing_raw_candidate_before_full_comparison"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "full_raw_to_processed_comparison_precheck_after_full_materialization_summary.json"
MANIFEST_PATH = MACHINE_DIR / "full_raw_to_processed_comparison_precheck_after_full_materialization_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "full_raw_to_processed_comparison_precheck_after_full_materialization_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "full_raw_to_processed_comparison_precheck_after_full_materialization_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "full_raw_to_processed_comparison_precheck_after_full_materialization_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_full_raw_to_processed_comparison_precheck_after_full_materialization_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_full_raw_to_processed_comparison_precheck_after_full_materialization_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_full_raw_to_processed_comparison_precheck_after_full_materialization_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_full_raw_to_processed_comparison_precheck_after_full_materialization_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

SOURCE_FULL_MATERIALIZATION_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_full_materialization_replay_after_outside_scope_application_summary.json"
SOURCE_FULL_MATERIALIZATION_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_full_materialization_replay_after_outside_scope_application_manifest.json"
PRIVATE_FULL_REPLAY_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_full_processed_value_materialization_replay_after_outside_scope_application/private_full_materialization_replay.json"
PRIVATE_FULL_MATERIALIZED_RECORDS_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_full_processed_value_materialization_replay_after_outside_scope_application/private_full_materialized_records.jsonl"
PRIVATE_CANDIDATE_CATALOG_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_intake_prep/private_candidate_catalog.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_full_raw_to_processed_comparison_precheck_after_full_materialization"
PRIVATE_PRECHECK_PATH = PRIVATE_OUTPUT_DIR / "private_full_raw_to_processed_comparison_precheck.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_full_raw_to_processed_comparison_precheck_diagnostic.json"
PRIVATE_COMPARISON_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_full_comparison_precheck_records.jsonl"
PRIVATE_BLOCKER_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_full_comparison_precheck_blocker_records.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_full_raw_to_processed_comparison_precheck.md"

HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")

FILES_CHANGED = [
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/VERSION",
    "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
    "KMFA/docs/governance/MODEL_SPEC.md",
    "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md",
    "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml",
    "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/development_events.jsonl",
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
    METADATA_SUMMARY_PATH.as_posix(),
    METADATA_MANIFEST_PATH.as_posix(),
    METADATA_GO_NO_GO_PATH.as_posix(),
    METADATA_MATRIX_PATH.as_posix(),
    SUMMARY_PATH.as_posix(),
    MANIFEST_PATH.as_posix(),
    GO_NO_GO_PATH.as_posix(),
    MATRIX_PATH.as_posix(),
    REPORT_PATH.as_posix(),
    GO_NO_GO_RECORD_PATH.as_posix(),
    TEST_RESULTS_PATH.as_posix(),
    RISK_REGISTER_PATH.as_posix(),
    ROLLBACK_PATH.as_posix(),
    "KMFA/tests/test_v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py",
    "KMFA/tools/check_v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py",
    "KMFA/tools/v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py",
]


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


def _normalize_sha256(value: Any) -> str | None:
    if isinstance(value, str) and SHA256.fullmatch(value):
        return value
    if isinstance(value, str) and HEX64.fullmatch(value):
        return "sha256:" + value.lower()
    return None


def _candidate_by_record_ref(candidate_catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = candidate_catalog.get("candidate_catalog_records", [])
    if not isinstance(records, list):
        raise ValueError("candidate_catalog_records must be a list")
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        ref = record.get("record_ref_hash")
        if isinstance(ref, str) and ref:
            result[ref] = record
    return result


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_data_root_readonly_policy_active": True,
        "private_full_materialization_summary_read_by_this_phase": True,
        "private_full_replay_read_by_this_phase": True,
        "private_full_materialized_records_read_by_this_phase": True,
        "private_candidate_catalog_read_by_this_phase": True,
        "private_full_comparison_precheck_written_by_this_phase": True,
        "source_private_full_materialization_summary_mutated_by_this_phase": False,
        "source_private_full_replay_mutated_by_this_phase": False,
        "source_private_materialized_records_mutated_by_this_phase": False,
        "source_private_candidate_catalog_mutated_by_this_phase": False,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
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
        "private_full_replay_committed": False,
        "private_candidate_catalog_committed": False,
        "private_precheck_committed": False,
        "private_comparison_records_committed": False,
        "private_blocker_records_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "processed_value_fingerprint_committed": False,
        "private_value_source_identifier_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_precheck(
    *,
    generated_at: str,
    full_materialization_summary: dict[str, Any],
    private_full_replay: dict[str, Any],
    materialized_records: list[dict[str, Any]],
    candidate_catalog: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    candidates = _candidate_by_record_ref(candidate_catalog)
    comparison_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    mismatch_rows: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    missing_rows: list[dict[str, Any]] = []

    for row in materialized_records:
        slot_id = row.get("target_slot_id")
        record_ref = row.get("source_record_ref_hash")
        replay_fingerprint = _normalize_sha256(row.get("processed_value_fingerprint"))
        source_scope = row.get("source_scope") if isinstance(row.get("source_scope"), str) else "unknown"
        blocker_base = {
            "target_slot_id": slot_id,
            "review_group_id": row.get("review_group_id"),
            "source_scope": source_scope,
            "source_record_ref_hash": record_ref,
            "processed_replay_fingerprint": replay_fingerprint,
        }
        if not isinstance(record_ref, str) or not replay_fingerprint:
            blocker = {**blocker_base, "comparison_precheck_status": "invalid_private_full_materialized_record"}
            invalid_rows.append(blocker)
            blocker_rows.append(blocker)
            continue
        candidate = candidates.get(record_ref)
        if candidate is None:
            blocker = {**blocker_base, "comparison_precheck_status": "missing_private_candidate_record"}
            missing_rows.append(blocker)
            blocker_rows.append(blocker)
            continue
        candidate_fingerprint = _normalize_sha256(candidate.get("numeric_value_fingerprint"))
        if candidate_fingerprint != replay_fingerprint:
            blocker = {
                **blocker_base,
                "source_candidate_fingerprint": candidate_fingerprint,
                "comparison_precheck_status": "fingerprint_mismatch",
            }
            mismatch_rows.append(blocker)
            blocker_rows.append(blocker)
            continue
        comparison_rows.append(
            {
                "target_slot_id": slot_id,
                "review_group_id": row.get("review_group_id"),
                "source_scope": source_scope,
                "source_record_ref_hash": record_ref,
                "source_ref_hash": row.get("source_ref_hash"),
                "source_cell_ref_hash": row.get("source_cell_ref_hash"),
                "source_sheet_ref_hash": row.get("source_sheet_ref_hash"),
                "source_record_kind": row.get("source_record_kind"),
                "source_kind": row.get("source_kind"),
                "source_candidate_rank": row.get("source_candidate_rank"),
                "source_candidate_fingerprint": candidate_fingerprint,
                "processed_replay_fingerprint": replay_fingerprint,
                "comparison_precheck_status": "exact_fingerprint_match",
            }
        )

    linked_rows = [row for row in materialized_records if row.get("source_scope") == "linked"]
    outside_rows = [row for row in materialized_records if row.get("source_scope") == "outside_scope_extension"]
    linked_matches = [row for row in comparison_rows if row.get("source_scope") == "linked"]
    outside_matches = [row for row in comparison_rows if row.get("source_scope") == "outside_scope_extension"]
    linked_missing = [row for row in missing_rows if row.get("source_scope") == "linked"]
    outside_missing = [row for row in missing_rows if row.get("source_scope") == "outside_scope_extension"]
    linked_mismatches = [row for row in mismatch_rows if row.get("source_scope") == "linked"]
    outside_mismatches = [row for row in mismatch_rows if row.get("source_scope") == "outside_scope_extension"]
    private_summary = {
        "source_full_materialization_phase_id": full_materialization_summary.get("phase_id"),
        "source_private_replay_phase_id": private_full_replay.get("phase_id"),
        "processed_target_slot_count": full_materialization_summary.get("processed_target_slot_count"),
        "full_materialized_record_count": len(materialized_records),
        "candidate_catalog_record_count": int(candidate_catalog.get("candidate_catalog_record_count") or 0),
        "full_scope_candidate_record_match_count": len(comparison_rows) + len(mismatch_rows),
        "full_scope_private_fingerprint_precheck_pair_count": len(comparison_rows) + len(mismatch_rows),
        "full_scope_exact_fingerprint_match_count": len(comparison_rows),
        "full_scope_fingerprint_mismatch_count": len(mismatch_rows),
        "full_scope_missing_candidate_count": len(missing_rows),
        "full_scope_invalid_materialized_record_count": len(invalid_rows),
        "linked_materialized_record_count": len(linked_rows),
        "linked_exact_fingerprint_match_count": len(linked_matches),
        "linked_missing_candidate_count": len(linked_missing),
        "linked_fingerprint_mismatch_count": len(linked_mismatches),
        "outside_scope_materialized_record_count": len(outside_rows),
        "outside_scope_exact_fingerprint_match_count": len(outside_matches),
        "outside_scope_missing_candidate_count": len(outside_missing),
        "outside_scope_fingerprint_mismatch_count": len(outside_mismatches),
        "full_unique_source_record_ref_count": len({row.get("source_record_ref_hash") for row in materialized_records}),
        "full_unique_processed_value_fingerprint_count": len(
            {row.get("processed_value_fingerprint") for row in materialized_records}
        ),
        "full_raw_to_processed_value_comparison_precheck_performed": True,
        "full_raw_to_processed_value_comparison_precheck_passed": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    precheck = {
        "schema_version": "kmfa.private.v014_full_raw_to_processed_comparison_precheck.v1",
        "classification": "private_full_raw_to_processed_comparison_precheck_do_not_commit",
        "record_type": "v014_full_raw_to_processed_comparison_precheck",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_full_materialization_phase_id": full_materialization_summary.get("phase_id"),
        "source_private_replay_phase_id": private_full_replay.get("phase_id"),
        "private_summary": private_summary,
        "comparison_records": comparison_rows,
        "blocker_records": blocker_rows,
        "mismatch_records": mismatch_rows,
        "missing_candidate_records": missing_rows,
        "invalid_materialized_records": invalid_rows,
        "raw_boundary": _raw_boundary(),
    }
    return precheck, comparison_rows, blocker_rows, private_summary


def _build_matrix(generated_at: str, *, summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("full_materialized_records_available", summary["full_materialized_record_count"] == 149, summary["full_materialized_record_count"], 149),
        ("candidate_catalog_available", summary["candidate_catalog_record_count"] == 366, summary["candidate_catalog_record_count"], 366),
        ("linked_records_prechecked", summary["linked_exact_fingerprint_match_count"] == 77, summary["linked_exact_fingerprint_match_count"], 77),
        ("outside_scope_candidate_coverage_blocked", summary["outside_scope_missing_candidate_count"] == 0, summary["outside_scope_missing_candidate_count"], 0),
        ("full_precheck_unblocked", summary["full_scope_missing_candidate_count"] == 0 and summary["full_scope_fingerprint_mismatch_count"] == 0, summary["full_scope_missing_candidate_count"] + summary["full_scope_fingerprint_mismatch_count"], 0),
        ("full_comparison_not_claimed", summary["full_raw_to_processed_value_comparison_complete"] is False, False, False),
        ("downstream_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, passed, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_full_comparison_precheck_matrix_public_safe.v1",
        "record_type": "v014_full_comparison_precheck_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "full_precheck_check_count": len(rows),
        "full_precheck_pass_count": pass_count,
        "full_precheck_fail_count": len(rows) - pass_count,
        "processed_target_slot_count": summary["processed_target_slot_count"],
        "full_materialized_record_count": summary["full_materialized_record_count"],
        "full_scope_exact_fingerprint_match_count": summary["full_scope_exact_fingerprint_match_count"],
        "full_scope_missing_candidate_count": summary["full_scope_missing_candidate_count"],
        "outside_scope_missing_candidate_count": summary["outside_scope_missing_candidate_count"],
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "decision": DECISION,
        "checks": rows,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Full Raw-To-Processed Comparison Precheck After Full Materialization

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- full materialized records: `{summary["full_materialized_record_count"]}`
- candidate catalog records: `{summary["candidate_catalog_record_count"]}`
- exact fingerprint matches: `{summary["full_scope_exact_fingerprint_match_count"]}`
- missing candidate records: `{summary["full_scope_missing_candidate_count"]}`
- outside-scope missing candidate records: `{summary["outside_scope_missing_candidate_count"]}`
- full comparison ready: `false`
- full raw-to-processed comparison complete: `false`
- next recommended phase: `{NEXT_RECOMMENDED_PHASE}`

This phase prechecks private fingerprints only. It confirms the 77 linked records remain comparable and identifies 72 outside-scope materialized records without raw-derived candidate records. It does not read the raw inbox and does not complete full raw-to-processed comparison or reconciliation.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: 72 outside-scope materialized records are missing raw-derived candidate records, so full raw-to-processed comparison is not ready.
- readiness checks: `{matrix["full_precheck_pass_count"]}` pass / `{matrix["full_precheck_fail_count"]}` fail
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: full materialization could be mistaken for full business-value consistency.
- Control: public evidence records the 72-record outside-scope candidate gap and keeps full comparison, reconciliation, formal report, upload and business execution closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private precheck outputs, tool, validator, focused test and governance entries. The raw data inbox is not modified by this rollback.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py KMFA/tools/check_v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py KMFA/tests/test_v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py --require-private-precheck`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_full_raw_to_processed_comparison_precheck_after_full_materialization`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `git diff --check`

All listed commands must pass before local commit. This phase does not read, list, stat, hash, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
"""
    for path, text in (
        (REPORT_PATH, report),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback_plan),
        (TEST_RESULTS_PATH, test_results),
    ):
        _write_text(path, text)


def _append_jsonl_event(path: Path, event_id: str, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    path.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def _append_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260707-V014-FULL-COMPARISON-PRECHECK"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260707-KMFA-V014-FULL-COMPARISON-PRECHECK",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "full_materialized_record_count": summary["full_materialized_record_count"],
        "full_scope_exact_fingerprint_match_count": summary["full_scope_exact_fingerprint_match_count"],
        "full_scope_missing_candidate_count": summary["full_scope_missing_candidate_count"],
        "outside_scope_missing_candidate_count": summary["outside_scope_missing_candidate_count"],
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Prechecked full materialized records against private raw-derived candidate fingerprints and found 72 outside-scope missing candidate blockers.",
    }
    _append_jsonl_event(DEVELOPMENT_EVENTS_PATH, event_id, event)
    _append_jsonl_event(
        STAGE_STATUS_PATH,
        event_id,
        {
            "event_id": event_id,
            "event_time": generated_at,
            "project_id": "KMFA",
            "stage_id": "value-consistency",
            "phase_id": PHASE_ID,
            "status": STATUS,
            "decision": DECISION,
            "next_required_input": NEXT_REQUIRED_INPUT,
            "evidence_ref": MANIFEST_PATH.as_posix(),
        },
    )
    _append_jsonl_event(
        TASK_STATUS_PATH,
        event_id,
        {
            "event_id": event_id,
            "event_time": generated_at,
            "task_id": TASK_ID,
            "phase_id": PHASE_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "status": STATUS,
            "decision": DECISION,
            "evidence_ref": MANIFEST_PATH.as_posix(),
        },
    )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    full_summary = _read_json(SOURCE_FULL_MATERIALIZATION_SUMMARY_PATH)
    _read_json(SOURCE_FULL_MATERIALIZATION_MANIFEST_PATH)
    private_replay = _read_json(PRIVATE_FULL_REPLAY_PATH)
    materialized_records = _read_jsonl(PRIVATE_FULL_MATERIALIZED_RECORDS_PATH)
    candidate_catalog = _read_json(PRIVATE_CANDIDATE_CATALOG_PATH)
    precheck, comparison_rows, blocker_rows, private_summary = _build_precheck(
        generated_at=timestamp,
        full_materialization_summary=full_summary,
        private_full_replay=private_replay,
        materialized_records=materialized_records,
        candidate_catalog=candidate_catalog,
    )
    summary = {
        "schema_version": "kmfa.v014_full_comparison_precheck_summary.v1",
        "record_type": "v014_full_comparison_precheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_full_materialization_phase_id": full_summary["phase_id"],
        "source_full_materialization_decision": full_summary["decision"],
        **private_summary,
        "full_raw_to_processed_value_comparison_precheck_performed_by_this_phase": True,
        "full_raw_to_processed_value_comparison_precheck_passed": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_precheck_written": True,
        "private_precheck_gitignored": _git_check_ignored(PRIVATE_PRECHECK_PATH),
        "private_comparison_records_written": True,
        "private_comparison_records_gitignored": _git_check_ignored(PRIVATE_COMPARISON_RECORDS_PATH),
        "private_blocker_records_written": True,
        "private_blocker_records_gitignored": _git_check_ignored(PRIVATE_BLOCKER_RECORDS_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    matrix = _build_matrix(timestamp, summary=summary)
    go_no_go = {
        "schema_version": "kmfa.v014_full_comparison_precheck_go_no_go.v1",
        "record_type": "v014_full_comparison_precheck_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "reason": "outside_scope_materialized_records_missing_raw_derived_candidate_records",
        "full_materialized_record_count": summary["full_materialized_record_count"],
        "full_scope_exact_fingerprint_match_count": summary["full_scope_exact_fingerprint_match_count"],
        "full_scope_missing_candidate_count": summary["full_scope_missing_candidate_count"],
        "outside_scope_missing_candidate_count": summary["outside_scope_missing_candidate_count"],
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_full_comparison_precheck_manifest.v1",
        "record_type": "v014_full_comparison_precheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "git_head_at_generation": _git_output(["rev-parse", "HEAD"]),
        "source_artifacts": [
            SOURCE_FULL_MATERIALIZATION_SUMMARY_PATH.as_posix(),
            SOURCE_FULL_MATERIALIZATION_MANIFEST_PATH.as_posix(),
            "private:full_materialization_replay",
            "private:full_materialized_records",
            "private:candidate_catalog",
        ],
        "public_artifacts": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "private_artifact_refs": [
            "private:full_comparison_precheck",
            "private:full_comparison_records",
            "private:full_comparison_blocker_records",
            "private:full_comparison_diagnostic",
        ],
        "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py --require-private-precheck",
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_full_comparison_precheck_diagnostic.v1",
        "classification": "private_full_comparison_precheck_diagnostic_do_not_commit",
        "record_type": "v014_full_comparison_precheck_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_summary": private_summary,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_PRECHECK_PATH, precheck)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_COMPARISON_RECORDS_PATH, comparison_rows)
    _write_jsonl(PRIVATE_BLOCKER_RECORDS_PATH, blocker_rows)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Full Raw-To-Processed Comparison Precheck\n\n"
        "77 private fingerprint pairs matched and 72 outside-scope records are missing raw-derived candidates. This file is ignored and must not be committed.\n",
    )
    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _write_json(path, payload)
    _write_human_artifacts(summary, matrix)
    if write_governance_event:
        _append_governance_events(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "matrix": matrix, "go_no_go": go_no_go}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: KMFA v0.1.4 full comparison precheck generated "
        f"(decision={summary['decision']}, exact_matches={summary['full_scope_exact_fingerprint_match_count']}, "
        f"missing_candidates={summary['full_scope_missing_candidate_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
