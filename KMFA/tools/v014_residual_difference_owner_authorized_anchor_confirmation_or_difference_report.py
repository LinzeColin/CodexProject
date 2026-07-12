#!/usr/bin/env python3
"""Write owner-authorized anchor confirmation or difference report.

This phase consumes the prior owner-authorized anchor readiness outputs. When
anchors are not ready, it writes a private unresolved-difference report and
keeps all raw comparison and business-consistency gates closed. It does not
read or mutate the raw inbox.
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
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_OR_DIFFERENCE_REPORT"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-OR-DIFFERENCE-REPORT-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-OR-DIFFERENCE-REPORT"
VERSION = "0.1.4-residual-difference-owner-authorized-anchor-confirmation-or-difference-report"
STATUS = "completed_validated_local_only_owner_authorized_anchor_difference_report_no_go"
DECISION = "NO_GO"
REPORT_CONCLUSION = "owner_authorized_anchor_confirmation_blocked_difference_report_written_72_unresolved"
NEXT_RECOMMENDED_PHASE = "V014_RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_BLOCKER_AUDIT"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_confirms_private_raw_candidate_anchors_before_formal_comparison"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_or_difference_report_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_or_difference_report_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_or_difference_report_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_or_difference_report_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "residual_difference_owner_authorized_anchor_confirmation_or_difference_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report_matrix_public_safe.json"
)

SOURCE_READINESS_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_readiness_summary.json"
)
SOURCE_READINESS_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_readiness_manifest.json"
)
SOURCE_READINESS_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_readiness_matrix_public_safe.json"
)
SOURCE_PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_owner_authorized_anchor_confirmation_readiness"
SOURCE_PRIVATE_READINESS_PATH = SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_confirmation_readiness.json"
SOURCE_PRIVATE_READY_QUEUE_PATH = SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_confirmation_ready_queue.jsonl"
SOURCE_PRIVATE_BLOCKER_QUEUE_PATH = SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_confirmation_blocker_queue.jsonl"

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report"
)
PRIVATE_DIFFERENCE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_difference_report.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_difference_report_diagnostic.json"
PRIVATE_UNRESOLVED_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_unresolved_difference_queue.jsonl"
PRIVATE_CONFIRMATION_READY_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_ready_queue.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_difference_report.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

EXPECTED_TRACK_COUNTS = {
    "owner_select_one_authoritative_candidate": 24,
    "provide_authoritative_source_reference_or_owner_exclusion": 40,
    "provide_formula_or_non_numeric_mapping": 8,
}


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
        "source_public_readiness_summary_read_by_this_phase": True,
        "source_public_readiness_manifest_read_by_this_phase": True,
        "source_public_readiness_matrix_read_by_this_phase": True,
        "source_private_readiness_read_by_this_phase": True,
        "source_private_ready_queue_read_by_this_phase": True,
        "source_private_blocker_queue_read_by_this_phase": True,
        "private_difference_report_written_by_this_phase": True,
        "private_unresolved_queue_written_by_this_phase": True,
        "private_confirmation_ready_queue_written_by_this_phase": True,
        "source_private_readiness_mutated_by_this_phase": False,
        "source_private_ready_queue_mutated_by_this_phase": False,
        "source_private_blocker_queue_mutated_by_this_phase": False,
        "owner_authorized_anchor_confirmation_performed_by_this_phase": False,
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
        "private_difference_report_committed": False,
        "private_unresolved_queue_committed": False,
        "private_confirmation_ready_queue_committed": False,
        "private_diagnostic_committed": False,
        "private_source_readiness_committed": False,
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


def _build_report_rows(blocker_rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    report_rows: list[dict[str, Any]] = []
    for index, row in enumerate(blocker_rows, start=1):
        report_rows.append(
            {
                "difference_report_index": index,
                "version": VERSION,
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_readiness_index": row.get("readiness_index"),
                "source_anchor_draft_index": row.get("source_anchor_draft_index"),
                "target_slot_id": row.get("target_slot_id"),
                "diagnostic_track": row.get("diagnostic_track"),
                "alignment_status": row.get("alignment_status"),
                "private_candidate_sample_available": row.get("private_candidate_sample_available") is True,
                "private_top_candidate_record_count": int(row.get("private_top_candidate_record_count") or 0),
                "missing_private_anchor_codes": row.get("missing_private_anchor_codes", []),
                "difference_report_status": "unresolved_missing_owner_authorized_anchor_confirmation_inputs",
                "owner_authorized_anchor_confirmation_counted": False,
                "anchor_confirmation_ready": False,
                "raw_to_processed_value_comparison_ready": False,
                "raw_to_processed_value_comparison_performed": False,
                "business_value_consistency_verified": False,
                "public_commit_allowed": False,
            }
        )
    return report_rows


def _build_matrix(summary: dict[str, Any], generated_at: str) -> dict[str, Any]:
    checks = [
        ("source_readiness_blockers_available", summary["source_readiness_blocker_count"] == 72, summary["source_readiness_blocker_count"], 72),
        ("source_anchor_draft_items_available", summary["source_anchor_draft_item_count"] == 72, summary["source_anchor_draft_item_count"], 72),
        ("difference_report_items_written", summary["difference_report_item_count"] == 72, summary["difference_report_item_count"], 72),
        ("diagnostic_track_counts_locked", summary["diagnostic_track_counts"] == EXPECTED_TRACK_COUNTS, summary["diagnostic_track_counts"], EXPECTED_TRACK_COUNTS),
        (
            "owner_authorized_anchor_confirmation_unblocked",
            summary["owner_authorized_anchor_confirmation_count"] == 72,
            summary["owner_authorized_anchor_confirmation_count"],
            72,
        ),
        ("missing_owner_authorized_anchor_cleared", summary["missing_owner_authorized_anchor_count"] == 0, summary["missing_owner_authorized_anchor_count"], 0),
        ("missing_private_anchor_fingerprints_cleared", summary["missing_processed_value_fingerprint_count"] == 0 and summary["missing_raw_candidate_anchor_count"] == 0, [summary["missing_processed_value_fingerprint_count"], summary["missing_raw_candidate_anchor_count"]], [0, 0]),
        ("formal_comparison_not_claimed", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False, False, False),
        ("raw_inbox_not_accessed", summary["raw_boundary"]["raw_inbox_read_performed_by_this_phase"] is False, False, False),
        ("downstream_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, passed, observed, required in checks
    ]
    return {
        "schema_version": "kmfa.v014_owner_authorized_anchor_difference_report_matrix_public_safe.v1",
        "record_type": "v014_owner_authorized_anchor_difference_report_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "check_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "PASS"),
        "fail_count": sum(1 for row in rows if row["status"] == "FAIL"),
        "source_readiness_blocker_count": summary["source_readiness_blocker_count"],
        "difference_report_item_count": summary["difference_report_item_count"],
        "unresolved_difference_count": summary["unresolved_difference_count"],
        "anchor_confirmation_ready": False,
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
    event_id = "DEV-KMFA-20260707-V014-RESIDUAL-DIFFERENCE-OWNER-AUTHORIZED-ANCHOR-DIFFERENCE-REPORT"
    event = {
        "event_id": event_id,
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260707-KMFA-V014-OWNER-AUTHORIZED-ANCHOR-DIFFERENCE-REPORT",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "source_readiness_blocker_count": summary["source_readiness_blocker_count"],
        "difference_report_item_count": summary["difference_report_item_count"],
        "unresolved_difference_count": summary["unresolved_difference_count"],
        "owner_authorized_anchor_confirmation_count": summary["owner_authorized_anchor_confirmation_count"],
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": "Wrote a private owner-authorized anchor difference report and kept formal comparison blocked because all 72 residual items remain unresolved.",
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
            "name": "v0.1.4 residual difference owner-authorized anchor confirmation or difference report",
            "phase_id": PHASE_ID,
            "record_type": "v014_phase",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_OR_DIFFERENCE_REPORT",
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
            "name": "72 owner-authorized anchor readiness blockers converted to private difference report queue",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_OR_DIFFERENCE_REPORT",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OADR01",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": GO_NO_GO_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "owner-authorized anchor confirmation remains unavailable",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_OR_DIFFERENCE_REPORT",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OADR02",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "raw inbox untouched and private difference report remains ignored",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_OR_DIFFERENCE_REPORT",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OADR03",
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
                "Owner-authorized anchor confirmation or difference report manifest summary Go No-Go public-safe "
                "matrix ignored private unresolved queue validator focused test and governance records"
            )
            task_row["phase_goal"] = (
                "write a public-safe difference report gate when owner-authorized private anchors cannot be confirmed "
                "without raw inbox access or formal comparison"
            )
        else:
            task_row["task_label"] = row["task_id"][-2:]
            task_row["task_text"] = row["name"]
        task_rows.append(task_row)
    _dedupe_append_jsonl(TASK_STATUS_PATH, task_rows, lambda existing: existing.get("phase_id") != PHASE_ID)


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Residual Difference Owner-Authorized Anchor Confirmation Or Difference Report

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- source readiness blockers: `{summary["source_readiness_blocker_count"]}`
- difference report items: `{summary["difference_report_item_count"]}`
- unresolved differences: `{summary["unresolved_difference_count"]}`
- owner-authorized anchor confirmations: `{summary["owner_authorized_anchor_confirmation_count"]}`
- next required input: `{NEXT_REQUIRED_INPUT}`

This phase writes a private unresolved-difference report from prior readiness outputs only. It does not read the raw inbox, authorize anchors, perform formal raw-to-processed comparison, verify business consistency, upload GitHub, reinstall the app, or execute business steps.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: 72 residual-difference records still lack complete owner-authorized private anchors for confirmation.
- checks: `{matrix["pass_count"]}` pass / `{matrix["fail_count"]}` fail
- anchor confirmation ready: `false`
- formal comparison allowed: `false`
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: the private difference report could be mistaken for completed owner confirmation.
- Control: confirmation count remains zero and all raw comparison, reconciliation, report, upload and business gates stay closed.
- Control: public evidence remains aggregate-only; private unresolved records remain ignored.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private report outputs, tool, validator, focused test and governance entries. The raw inbox and previous readiness outputs are not modified by this phase or rollback.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report.py KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report.py KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report.py --require-private-report`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report`
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
    source_summary = _read_json(SOURCE_READINESS_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_READINESS_MANIFEST_PATH)
    source_matrix = _read_json(SOURCE_READINESS_MATRIX_PATH)
    source_private_readiness = _read_json(SOURCE_PRIVATE_READINESS_PATH)
    source_ready_rows = _read_jsonl(SOURCE_PRIVATE_READY_QUEUE_PATH)
    source_blocker_rows = _read_jsonl(SOURCE_PRIVATE_BLOCKER_QUEUE_PATH)
    if len(source_blocker_rows) != 72 or source_ready_rows:
        raise ValueError("source readiness must provide 72 blockers and zero ready records")

    report_rows = _build_report_rows(source_blocker_rows, timestamp)
    track_counts = dict(Counter(row.get("diagnostic_track") for row in source_blocker_rows))
    if track_counts != EXPECTED_TRACK_COUNTS:
        raise ValueError("unexpected diagnostic track counts")
    candidate_sample_count = sum(1 for row in source_blocker_rows if row.get("private_candidate_sample_available") is True)
    candidate_missing_count = len(source_blocker_rows) - candidate_sample_count

    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    private_difference_report = {
        "schema_version": "kmfa.private.v014_owner_authorized_anchor_difference_report.v1",
        "classification": "private_owner_authorized_anchor_difference_report_do_not_commit",
        "record_type": "v014_owner_authorized_anchor_difference_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_readiness_phase_id": source_summary.get("phase_id"),
        "source_readiness_blocker_count": len(source_blocker_rows),
        "source_anchor_draft_item_count": int(source_summary.get("source_anchor_draft_item_count") or 0),
        "owner_authorized_anchor_confirmation_count": 0,
        "difference_report_item_count": len(report_rows),
        "unresolved_difference_count": len(report_rows),
        "anchor_confirmation_ready": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "unresolved_difference_rows": report_rows,
        "raw_boundary": raw_boundary,
    }
    private_diagnostic = {
        "schema_version": "kmfa.private.v014_owner_authorized_anchor_difference_report_diagnostic.v1",
        "record_type": "private_owner_authorized_anchor_difference_report_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_readiness_phase_id": source_summary.get("phase_id"),
        "source_readiness_decision": source_summary.get("decision"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_matrix_fail_count": source_matrix.get("fail_count"),
        "source_private_readiness_phase_id": source_private_readiness.get("phase_id"),
        "owner_authorized_anchor_confirmation_count": 0,
        "difference_report_item_count": len(report_rows),
        "unresolved_difference_count": len(report_rows),
        "private_candidate_sample_item_count": candidate_sample_count,
        "private_candidate_missing_sample_item_count": candidate_missing_count,
        "diagnostic_track_counts": track_counts,
        "raw_inbox_accessed": False,
        "raw_inbox_mutated": False,
    }

    _write_json(PRIVATE_DIFFERENCE_REPORT_PATH, private_difference_report)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_jsonl(PRIVATE_UNRESOLVED_QUEUE_PATH, report_rows)
    _write_jsonl(PRIVATE_CONFIRMATION_READY_QUEUE_PATH, [])
    _write_text(
        PRIVATE_REPORT_PATH,
        "\n".join(
            [
                "# Private owner-authorized anchor difference report",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- difference_report_item_count: `{len(report_rows)}`",
                f"- owner_authorized_anchor_confirmation_count: `0`",
                "- formal raw-to-processed comparison was not performed.",
                "- raw inbox access and mutation were not performed.",
            ]
        )
        + "\n",
    )

    summary = {
        "schema_version": "kmfa.v014_owner_authorized_anchor_difference_report_summary.v1",
        "record_type": "v014_owner_authorized_anchor_difference_report_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "report_conclusion": REPORT_CONCLUSION,
        "source_readiness_phase_id": source_summary.get("phase_id"),
        "source_readiness_decision": source_summary.get("decision"),
        "source_readiness_blocker_count": len(source_blocker_rows),
        "source_readiness_ready_count": len(source_ready_rows),
        "source_anchor_draft_item_count": int(source_summary.get("source_anchor_draft_item_count") or 0),
        "owner_authorized_anchor_ready_count": int(source_summary.get("owner_authorized_anchor_ready_count") or 0),
        "owner_authorized_anchor_blocker_count": int(source_summary.get("owner_authorized_anchor_blocker_count") or 0),
        "difference_report_item_count": len(report_rows),
        "unresolved_difference_count": len(report_rows),
        "owner_authorized_anchor_confirmation_count": 0,
        "missing_owner_authorized_anchor_count": int(source_summary.get("missing_owner_authorized_anchor_count") or 0),
        "missing_processed_value_fingerprint_count": int(source_summary.get("missing_processed_value_fingerprint_count") or 0),
        "missing_raw_candidate_anchor_count": int(source_summary.get("missing_raw_candidate_anchor_count") or 0),
        "anchor_confirmation_ready": False,
        "owner_authorized_anchor_confirmation_performed_by_this_phase": False,
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
        "diagnostic_track_counts": track_counts,
        "owner_select_one_authoritative_candidate_count": track_counts.get("owner_select_one_authoritative_candidate", 0),
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts.get(
            "provide_authoritative_source_reference_or_owner_exclusion", 0
        ),
        "provide_formula_or_non_numeric_mapping_count": track_counts.get("provide_formula_or_non_numeric_mapping", 0),
        "private_candidate_sample_item_count": candidate_sample_count,
        "private_candidate_missing_sample_item_count": candidate_missing_count,
        "private_difference_report_written": True,
        "private_difference_report_gitignored": _git_check_ignored(PRIVATE_DIFFERENCE_REPORT_PATH),
        "private_unresolved_queue_written": True,
        "private_unresolved_queue_gitignored": _git_check_ignored(PRIVATE_UNRESOLVED_QUEUE_PATH),
        "private_confirmation_ready_queue_written": True,
        "private_confirmation_ready_queue_gitignored": _git_check_ignored(PRIVATE_CONFIRMATION_READY_QUEUE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
    }
    matrix = _build_matrix(summary, timestamp)
    go_no_go = {
        "schema_version": "kmfa.v014_owner_authorized_anchor_difference_report_go_no_go.v1",
        "record_type": "v014_owner_authorized_anchor_difference_report_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "current_gate": "NO_GO_RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_BLOCKED_DIFFERENCE_REPORT_WRITTEN",
        "reason": REPORT_CONCLUSION,
        "source_readiness_blocker_count": len(source_blocker_rows),
        "difference_report_item_count": len(report_rows),
        "unresolved_difference_count": len(report_rows),
        "owner_authorized_anchor_confirmation_count": 0,
        "anchor_confirmation_ready": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_owner_authorized_anchor_difference_report_manifest.v1",
        "record_type": "v014_owner_authorized_anchor_difference_report_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
        "private_artifacts": {
            "private_difference_report": "private_runtime_only_ignored",
            "private_diagnostic": "private_runtime_only_ignored",
            "private_unresolved_queue": "private_runtime_only_ignored",
            "private_confirmation_ready_queue": "private_runtime_only_ignored",
            "private_report": "private_runtime_only_ignored",
        },
        "changed_files": _changed_kmfa_files(),
        "git_head_at_generation": _git_output(["rev-parse", "HEAD"]),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report.py KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report.py KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report.py --require-private-report",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report",
            "python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync",
            "python3 scripts/validate_project_governance.py --changed-only --base-ref HEAD --enforce-sync",
            "python3 scripts/lean_governance.py validate --changed-only --base-ref HEAD --enforce-sync",
            "git diff --check",
        ],
    }

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
        _append_governance_records(manifest)
    return {"summary": summary, "manifest": manifest, "matrix": matrix, "go_no_go": go_no_go}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: generated owner-authorized anchor difference report "
        f"(report_items={summary['difference_report_item_count']}, "
        f"unresolved={summary['unresolved_difference_count']}, decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
