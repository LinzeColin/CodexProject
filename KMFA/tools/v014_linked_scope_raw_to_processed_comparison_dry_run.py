#!/usr/bin/env python3
"""Dry-run linked-scope raw-to-processed comparison.

This phase consumes the ignored private linked-scope comparison precheck records
from the previous phase. It does not read, list, stat, hash, parse, copy or
mutate the raw inbox. Public artifacts contain aggregate counts and gate status
only.
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
PHASE_ID = "V014_LINKED_SCOPE_RAW_TO_PROCESSED_COMPARISON_DRY_RUN"
TASK_ID = "KMFA-V014-LINKED-SCOPE-RAW-TO-PROCESSED-COMPARISON-DRY-RUN-20260706"
ACCEPTANCE_ID = "ACC-V014-LINKED-SCOPE-RAW-TO-PROCESSED-COMPARISON-DRY-RUN"
VERSION = "0.1.4-linked-scope-raw-to-processed-comparison-dry-run"
STATUS = "completed_validated_local_only_linked_scope_comparison_dry_run_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "linked_scope_private_fingerprint_dry_run_passed_full_comparison_and_reconciliation_not_complete"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_TARGET_OUTSIDE_LINKED_SCOPE_RESOLUTION"
NEXT_REQUIRED_INPUT = "resolve_72_processed_target_slots_outside_linked_replay_scope_before_full_raw_to_processed_comparison"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "linked_scope_raw_to_processed_comparison_dry_run_summary.json"
MANIFEST_PATH = MACHINE_DIR / "linked_scope_raw_to_processed_comparison_dry_run_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "linked_scope_raw_to_processed_comparison_dry_run_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "linked_scope_raw_to_processed_comparison_dry_run_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "linked_scope_raw_to_processed_comparison_dry_run_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_scope_raw_to_processed_comparison_dry_run_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_scope_raw_to_processed_comparison_dry_run_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_scope_raw_to_processed_comparison_dry_run_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_scope_raw_to_processed_comparison_dry_run_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_PRECHECK_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_linked_scope_raw_to_processed_comparison_precheck_summary.json"
)
SOURCE_PRECHECK_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_linked_scope_raw_to_processed_comparison_precheck_manifest.json"
)
PRIVATE_PRECHECK_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_linked_scope_raw_to_processed_comparison_precheck/private_linked_scope_raw_to_processed_comparison_precheck.json"
)
PRIVATE_PRECHECK_RECORDS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_linked_scope_raw_to_processed_comparison_precheck/private_linked_scope_comparison_precheck_records.jsonl"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_linked_scope_raw_to_processed_comparison_dry_run"
PRIVATE_DRY_RUN_PATH = PRIVATE_OUTPUT_DIR / "private_linked_scope_raw_to_processed_comparison_dry_run.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_linked_scope_raw_to_processed_comparison_dry_run_diagnostic.json"
PRIVATE_DRY_RUN_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_linked_scope_comparison_dry_run_records.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_linked_scope_raw_to_processed_comparison_dry_run.md"

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
    "KMFA/docs/governance/events.jsonl",
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
    "KMFA/tests/test_v014_linked_scope_raw_to_processed_comparison_dry_run.py",
    "KMFA/tools/check_v014_linked_scope_raw_to_processed_comparison_dry_run.py",
    "KMFA/tools/v014_linked_scope_raw_to_processed_comparison_dry_run.py",
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


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_data_root_readonly_policy_active": True,
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
        "private_precheck_committed": False,
        "private_precheck_records_committed": False,
        "private_dry_run_committed": False,
        "private_dry_run_records_committed": False,
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


def _build_dry_run(
    *,
    generated_at: str,
    precheck_summary: dict[str, Any],
    private_precheck: dict[str, Any],
    precheck_records: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    dry_run_records: list[dict[str, Any]] = []
    mismatch_records: list[dict[str, Any]] = []
    invalid_records: list[dict[str, Any]] = []
    for row in precheck_records:
        source_fp = row.get("source_candidate_fingerprint")
        processed_fp = row.get("processed_replay_fingerprint")
        if not (isinstance(source_fp, str) and isinstance(processed_fp, str) and SHA256.fullmatch(source_fp) and SHA256.fullmatch(processed_fp)):
            invalid_records.append({"dry_run_status": "invalid_private_precheck_record"})
            continue
        if source_fp != processed_fp:
            mismatch_records.append(
                {
                    "target_slot_id": row.get("target_slot_id"),
                    "review_group_id": row.get("review_group_id"),
                    "source_record_ref_hash": row.get("source_record_ref_hash"),
                    "source_candidate_fingerprint": source_fp,
                    "processed_replay_fingerprint": processed_fp,
                    "dry_run_status": "dry_run_fingerprint_mismatch",
                }
            )
            continue
        dry_run_records.append(
            {
                "target_slot_id": row.get("target_slot_id"),
                "review_group_id": row.get("review_group_id"),
                "source_record_ref_hash": row.get("source_record_ref_hash"),
                "source_ref_hash": row.get("source_ref_hash"),
                "source_cell_ref_hash": row.get("source_cell_ref_hash"),
                "source_sheet_ref_hash": row.get("source_sheet_ref_hash"),
                "source_record_kind": row.get("source_record_kind"),
                "source_kind": row.get("source_kind"),
                "source_candidate_rank": row.get("source_candidate_rank"),
                "source_candidate_fingerprint": source_fp,
                "processed_replay_fingerprint": processed_fp,
                "dry_run_status": "dry_run_exact_fingerprint_match",
            }
        )

    private_summary = {
        "source_precheck_phase_id": precheck_summary.get("phase_id"),
        "source_private_precheck_phase_id": private_precheck.get("phase_id"),
        "processed_target_slot_count": precheck_summary.get("processed_target_slot_count"),
        "linked_materialized_record_count": precheck_summary.get("linked_materialized_record_count"),
        "candidate_catalog_record_count": precheck_summary.get("candidate_catalog_record_count"),
        "linked_scope_private_fingerprint_precheck_pair_count": precheck_summary.get(
            "linked_scope_private_fingerprint_precheck_pair_count"
        ),
        "linked_scope_dry_run_pair_count": len(dry_run_records) + len(mismatch_records),
        "linked_scope_dry_run_exact_match_count": len(dry_run_records),
        "linked_scope_dry_run_mismatch_count": len(mismatch_records),
        "linked_scope_dry_run_invalid_record_count": len(invalid_records),
        "linked_unique_source_record_ref_count": precheck_summary.get("linked_unique_source_record_ref_count"),
        "linked_unique_processed_value_fingerprint_count": precheck_summary.get(
            "linked_unique_processed_value_fingerprint_count"
        ),
        "processed_target_slot_outside_linked_replay_scope_count": precheck_summary.get(
            "processed_target_slot_outside_linked_replay_scope_count"
        ),
        "linked_scope_raw_to_processed_value_comparison_dry_run_performed": True,
        "linked_scope_raw_to_processed_value_comparison_dry_run_passed": (
            len(precheck_records) == 77 and len(dry_run_records) == 77 and not mismatch_records and not invalid_records
        ),
        "linked_scope_private_fingerprint_consistency_dry_run_verified": (
            len(precheck_records) == 77 and len(dry_run_records) == 77 and not mismatch_records and not invalid_records
        ),
        "raw_to_processed_value_comparison_performed": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
    }
    dry_run = {
        "schema_version": "kmfa.private.v014_linked_scope_raw_to_processed_comparison_dry_run.v1",
        "classification": "private_linked_scope_comparison_dry_run_do_not_commit",
        "record_type": "v014_linked_scope_raw_to_processed_comparison_dry_run",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "private_summary": private_summary,
        "dry_run_records": dry_run_records,
        "mismatch_records": mismatch_records,
        "invalid_records": invalid_records,
        "raw_boundary": _raw_boundary(),
    }
    return dry_run, dry_run_records, private_summary


def _build_matrix(generated_at: str, *, summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_precheck_dependency_passed", summary["source_precheck_decision"] == "NO_GO" and summary["source_precheck_passed"] is True, summary["source_precheck_passed"], True),
        ("private_precheck_records_available", summary["linked_scope_private_fingerprint_precheck_pair_count"] == 77, summary["linked_scope_private_fingerprint_precheck_pair_count"], 77),
        ("dry_run_pairs_built", summary["linked_scope_dry_run_pair_count"] == 77, summary["linked_scope_dry_run_pair_count"], 77),
        ("dry_run_exact_matches", summary["linked_scope_dry_run_exact_match_count"] == 77, summary["linked_scope_dry_run_exact_match_count"], 77),
        ("dry_run_mismatch_free", summary["linked_scope_dry_run_mismatch_count"] == 0 and summary["linked_scope_dry_run_invalid_record_count"] == 0, summary["linked_scope_dry_run_mismatch_count"] + summary["linked_scope_dry_run_invalid_record_count"], 0),
        ("outside_scope_preserved", summary["processed_target_slot_outside_linked_replay_scope_count"] == 72, summary["processed_target_slot_outside_linked_replay_scope_count"], 72),
        ("full_comparison_not_claimed", summary["full_raw_to_processed_value_comparison_complete"] is False, False, False),
        ("downstream_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, passed, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_linked_scope_comparison_dry_run_matrix_public_safe.v1",
        "record_type": "v014_linked_scope_comparison_dry_run_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "linked_scope_dry_run_check_count": len(rows),
        "linked_scope_dry_run_check_pass_count": pass_count,
        "linked_scope_dry_run_check_fail_count": len(rows) - pass_count,
        "processed_target_slot_count": summary["processed_target_slot_count"],
        "linked_scope_dry_run_exact_match_count": summary["linked_scope_dry_run_exact_match_count"],
        "linked_scope_dry_run_mismatch_count": summary["linked_scope_dry_run_mismatch_count"],
        "processed_target_slot_outside_linked_replay_scope_count": summary["processed_target_slot_outside_linked_replay_scope_count"],
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "decision": DECISION,
        "checks": rows,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Linked-Scope Raw-To-Processed Comparison Dry Run

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- linked dry-run pairs: `{summary["linked_scope_dry_run_pair_count"]}`
- linked exact fingerprint matches: `{summary["linked_scope_dry_run_exact_match_count"]}`
- linked dry-run mismatches: `{summary["linked_scope_dry_run_mismatch_count"]}`
- linked dry-run invalid records: `{summary["linked_scope_dry_run_invalid_record_count"]}`
- outside linked replay scope slots: `{summary["processed_target_slot_outside_linked_replay_scope_count"]}`
- full raw-to-processed comparison complete: `false`
- next recommended phase: `{NEXT_RECOMMENDED_PHASE}`

This phase performs a private linked-scope dry run only. It does not read the raw inbox and does not complete full raw-to-processed comparison or reconciliation.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: linked-scope private fingerprint dry run passed, but full comparison and reconciliation are not complete.
- readiness checks: `{matrix["linked_scope_dry_run_check_pass_count"]}` pass / `{matrix["linked_scope_dry_run_check_fail_count"]}` fail
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: linked-scope dry run could be mistaken for full business-value consistency.
- Control: public evidence keeps full comparison, reconciliation, formal report, upload and business execution closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private dry-run outputs, tool, validator, focused test and governance entries. The raw data inbox is not modified by this rollback.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_linked_scope_raw_to_processed_comparison_dry_run.py KMFA/tools/check_v014_linked_scope_raw_to_processed_comparison_dry_run.py KMFA/tests/test_v014_linked_scope_raw_to_processed_comparison_dry_run.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_linked_scope_raw_to_processed_comparison_dry_run.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_linked_scope_raw_to_processed_comparison_dry_run.py --require-private-dry-run`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_linked_scope_raw_to_processed_comparison_dry_run`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `git diff --check -- KMFA`

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


def _append_development_event(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-LINKED-SCOPE-COMPARISON-DRY-RUN"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-LINKED-SCOPE-COMPARISON-DRY-RUN",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "linked_scope_dry_run_exact_match_count": summary["linked_scope_dry_run_exact_match_count"],
        "linked_scope_dry_run_mismatch_count": summary["linked_scope_dry_run_mismatch_count"],
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Dry-ran linked-scope private raw-derived fingerprints against processed replay fingerprints while keeping full comparison and reconciliation gates closed.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    precheck_summary = _read_json(SOURCE_PRECHECK_SUMMARY_PATH)
    _read_json(SOURCE_PRECHECK_MANIFEST_PATH)
    private_precheck = _read_json(PRIVATE_PRECHECK_PATH)
    precheck_records = _read_jsonl(PRIVATE_PRECHECK_RECORDS_PATH)
    dry_run, dry_run_records, private_summary = _build_dry_run(
        generated_at=timestamp,
        precheck_summary=precheck_summary,
        private_precheck=private_precheck,
        precheck_records=precheck_records,
    )
    summary = {
        "schema_version": "kmfa.v014_linked_scope_comparison_dry_run_summary.v1",
        "record_type": "v014_linked_scope_comparison_dry_run_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_precheck_phase_id": precheck_summary.get("phase_id"),
        "source_precheck_decision": precheck_summary.get("decision"),
        "source_precheck_passed": precheck_summary.get("linked_scope_raw_to_processed_value_comparison_precheck_passed"),
        **private_summary,
        "linked_scope_raw_to_processed_value_comparison_dry_run_performed_by_this_phase": True,
        "linked_scope_raw_to_processed_value_comparison_dry_run_passed": private_summary[
            "linked_scope_raw_to_processed_value_comparison_dry_run_passed"
        ],
        "linked_scope_private_fingerprint_consistency_dry_run_verified": private_summary[
            "linked_scope_private_fingerprint_consistency_dry_run_verified"
        ],
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_dry_run_written": True,
        "private_dry_run_gitignored": _git_check_ignored(PRIVATE_DRY_RUN_PATH),
        "private_dry_run_records_written": True,
        "private_dry_run_records_gitignored": _git_check_ignored(PRIVATE_DRY_RUN_RECORDS_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    matrix = _build_matrix(timestamp, summary=summary)
    go_no_go = {
        "schema_version": "kmfa.v014_linked_scope_comparison_dry_run_go_no_go.v1",
        "record_type": "v014_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "linked_scope_dry_run_pair_count": summary["linked_scope_dry_run_pair_count"],
        "linked_scope_dry_run_exact_match_count": summary["linked_scope_dry_run_exact_match_count"],
        "linked_scope_dry_run_mismatch_count": summary["linked_scope_dry_run_mismatch_count"],
        "processed_target_slot_outside_linked_replay_scope_count": summary[
            "processed_target_slot_outside_linked_replay_scope_count"
        ],
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_linked_scope_comparison_dry_run_manifest.v1",
        "record_type": "v014_phase_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "source_precheck_summary_ref": SOURCE_PRECHECK_SUMMARY_PATH.as_posix(),
        "source_precheck_manifest_ref": SOURCE_PRECHECK_MANIFEST_PATH.as_posix(),
        "private_inputs": {
            "private_precheck_read": True,
            "private_precheck_records_read": True,
            "raw_inbox_read": False,
        },
        "private_outputs": {
            "private_dry_run_written": True,
            "private_dry_run_gitignored": summary["private_dry_run_gitignored"],
            "private_dry_run_records_written": True,
            "private_dry_run_records_gitignored": summary["private_dry_run_records_gitignored"],
            "private_diagnostic_written": True,
            "private_diagnostic_gitignored": summary["private_diagnostic_gitignored"],
        },
        "git": {
            "head": _git_output(["rev-parse", "HEAD"]),
            "branch": _git_output(["branch", "--show-current"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
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
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_linked_scope_comparison_dry_run_diagnostic.v1",
        "classification": "private_linked_scope_comparison_dry_run_diagnostic_do_not_commit",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "private_summary": private_summary,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_DRY_RUN_PATH, dry_run)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_DRY_RUN_RECORDS_PATH, dry_run_records)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Linked-Scope Raw-To-Processed Comparison Dry Run\n\n"
        "77 linked-scope private fingerprint pairs were dry-run compared. This file is ignored and must not be committed.\n",
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
        _append_development_event(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "matrix": matrix, "go_no_go": go_no_go}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: KMFA v0.1.4 linked-scope comparison dry-run generated "
        f"(decision={summary['decision']}, exact_matches={summary['linked_scope_dry_run_exact_match_count']}, "
        f"mismatches={summary['linked_scope_dry_run_mismatch_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
