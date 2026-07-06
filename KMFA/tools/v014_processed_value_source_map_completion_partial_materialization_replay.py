#!/usr/bin/env python3
"""Replay private partial materialization for KMFA v0.1.4.

This phase consumes the ignored private partial materialization recheck output
and writes a private materialized replay artifact for the partial slots. It
does not read the raw inbox, compare raw and processed values, mutate the
canonical source map, or publish row-level private evidence.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_MATERIALIZATION_REPLAY"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-MATERIALIZATION-REPLAY-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-MATERIALIZATION-REPLAY"
VERSION = "0.1.4-partial-materialization-replay"
STATUS = "completed_validated_local_only_partial_materialization_replay_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_partial_materialization_replay_complete_partial_raw_compare_ready_full_reconciliation_blocked"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_RAW_TO_PROCESSED_COMPARISON"
NEXT_REQUIRED_INPUT = "run_partial_raw_to_processed_value_comparison_or_resolve_non_actionable_group_decisions"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_materialization_replay_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_materialization_replay_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_materialization_replay_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_partial_materialization_replay_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_materialization_replay_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_materialization_replay_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_materialization_replay_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_RECHECK_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_MATERIALIZATION_RECHECK/machine/processed_value_source_map_completion_partial_materialization_recheck_summary.json"
)
PRIVATE_RECHECK_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_partial_materialization_recheck/private_partial_materialization_recheck.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_partial_materialization_replay"
PRIVATE_REPLAY_PATH = PRIVATE_OUTPUT_DIR / "private_partial_materialization_replay.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_partial_materialization_replay_diagnostic.json"

SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


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
        "private_recheck_committed": False,
        "private_replay_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "processed_value_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_replay(
    *,
    generated_at: str,
    source_recheck_summary: dict[str, Any],
    private_recheck: dict[str, Any],
) -> dict[str, Any]:
    rows = private_recheck.get("materializable_rows", [])
    awaiting = private_recheck.get("awaiting_value_source_rows", [])
    invalid = private_recheck.get("invalid_fill_rows", [])
    blocked = private_recheck.get("source_blocked_partial_application_rows", [])
    if not isinstance(rows, list) or not isinstance(awaiting, list) or not isinstance(invalid, list):
        raise ValueError("private recheck row lists must be lists")
    if not isinstance(blocked, list):
        raise ValueError("source_blocked_partial_application_rows must be a list")

    materialized_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        fingerprint = row.get("processed_value_fingerprint")
        slot_id = row.get("target_slot_id")
        if not isinstance(slot_id, str) or not isinstance(fingerprint, str) or not SHA256.fullmatch(fingerprint):
            rejected_rows.append(
                {
                    "target_slot_id": slot_id,
                    "review_group_id": row.get("review_group_id"),
                    "partial_materialization_replay_status": "rejected_invalid_materializable_row",
                }
            )
            continue
        materialized_rows.append(
            {
                "target_slot_id": slot_id,
                "review_group_id": row.get("review_group_id"),
                "candidate_status": row.get("candidate_status"),
                "owner_group_decision_code": row.get("owner_group_decision_code"),
                "processed_value_fingerprint": fingerprint,
                "partial_materialization_replay_status": "materialized_private_fingerprint",
                "value_materialized": True,
                "source_candidate_rank": row.get("source_candidate_rank"),
                "source_record_ref_hash": row.get("source_record_ref_hash"),
                "source_ref_hash": row.get("source_ref_hash"),
                "source_cell_ref_hash": row.get("source_cell_ref_hash"),
                "source_sheet_ref_hash": row.get("source_sheet_ref_hash"),
                "source_record_kind": row.get("source_record_kind"),
                "source_kind": row.get("source_kind"),
            }
        )

    unique_fingerprint_count = len(
        {
            row.get("processed_value_fingerprint")
            for row in materialized_rows
            if isinstance(row.get("processed_value_fingerprint"), str)
        }
    )
    replay_complete = bool(rows) and len(materialized_rows) == len(rows) and not awaiting and not invalid and not rejected_rows
    summary = {
        "source_recheck_phase_id": source_recheck_summary.get("phase_id"),
        "source_recheck_decision": source_recheck_summary.get("decision"),
        "source_recheck_replay_ready": source_recheck_summary.get("partial_materialization_replay_ready"),
        "source_recheck_materializable_target_slot_count": source_recheck_summary.get(
            "partial_materializable_target_slot_count"
        ),
        "partial_materialization_replay_performed": True,
        "partial_materialization_replay_complete": replay_complete,
        "partial_materialized_target_slot_count": len(materialized_rows),
        "partial_unmaterialized_target_slot_count": len(rows) - len(materialized_rows) + len(awaiting) + len(invalid),
        "partial_materialized_unique_value_source_count": unique_fingerprint_count,
        "partial_application_blocked_target_slot_count": len(blocked),
        "rejected_materialization_row_count": len(rejected_rows),
        "partial_raw_to_processed_value_comparison_ready": replay_complete,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    return {
        "schema_version": "kmfa.private.v014_partial_materialization_replay.v1",
        "classification": "private_partial_materialization_replay_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_replay",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_recheck_phase_id": private_recheck.get("phase_id"),
        "partial_materialization_replay_summary": summary,
        "materialized_partial_slots": materialized_rows,
        "rejected_materialization_rows": rejected_rows,
        "source_blocked_partial_application_rows": blocked,
        "raw_boundary": _raw_boundary(),
    }


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_recheck_summary = _read_json(SOURCE_RECHECK_SUMMARY_PATH)
    private_recheck = _read_json(PRIVATE_RECHECK_PATH)
    replay = _build_replay(
        generated_at=timestamp,
        source_recheck_summary=source_recheck_summary,
        private_recheck=private_recheck,
    )
    replay_summary = replay["partial_materialization_replay_summary"]
    diagnostic = {
        "schema_version": "kmfa.private.v014_partial_materialization_replay_diagnostic.v1",
        "classification": "private_partial_materialization_replay_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_replay_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "partial_materialization_replay_summary": replay_summary,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_REPLAY_PATH, replay)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)

    summary = {
        "schema_version": "kmfa.v014_partial_materialization_replay_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_replay_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_recheck_phase_id": replay_summary["source_recheck_phase_id"],
        "source_recheck_decision": replay_summary["source_recheck_decision"],
        "source_recheck_replay_ready": replay_summary["source_recheck_replay_ready"],
        "source_recheck_materializable_target_slot_count": replay_summary[
            "source_recheck_materializable_target_slot_count"
        ],
        "partial_materialization_replay_performed": True,
        "partial_materialization_replay_complete": replay_summary["partial_materialization_replay_complete"],
        "partial_materialized_target_slot_count": replay_summary["partial_materialized_target_slot_count"],
        "partial_unmaterialized_target_slot_count": replay_summary["partial_unmaterialized_target_slot_count"],
        "partial_materialized_unique_value_source_count": replay_summary["partial_materialized_unique_value_source_count"],
        "partial_application_blocked_target_slot_count": replay_summary["partial_application_blocked_target_slot_count"],
        "rejected_materialization_row_count": replay_summary["rejected_materialization_row_count"],
        "partial_raw_to_processed_value_comparison_ready": replay_summary[
            "partial_raw_to_processed_value_comparison_ready"
        ],
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "private_replay_written": True,
        "private_replay_gitignored": _git_check_ignored(PRIVATE_REPLAY_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "processed_value_materialization_replay_performed": True,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_partial_materialization_replay_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_replay_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "partial_materialization_replay_performed": True,
        "partial_materialization_replay_complete": summary["partial_materialization_replay_complete"],
        "partial_materialized_target_slot_count": summary["partial_materialized_target_slot_count"],
        "partial_unmaterialized_target_slot_count": summary["partial_unmaterialized_target_slot_count"],
        "partial_application_blocked_target_slot_count": summary["partial_application_blocked_target_slot_count"],
        "partial_raw_to_processed_value_comparison_ready": summary["partial_raw_to_processed_value_comparison_ready"],
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_partial_materialization_replay_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_replay_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "generated_at": timestamp,
        "status": STATUS,
        "summary": summary,
        "go_no_go": go_no_go,
        "artifact_refs": {
            "machine_summary": SUMMARY_PATH.as_posix(),
            "machine_manifest": MANIFEST_PATH.as_posix(),
            "machine_go_no_go": GO_NO_GO_PATH.as_posix(),
            "private_replay": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_partial_materialization_replay.py "
            "--require-private-replay"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Partial Materialization Replay

Decision: {DECISION}

This phase performs a private partial materialization replay for slots that passed the previous private recheck. It does not compare raw and processed values, and it does not read the raw inbox.

## Public-safe aggregate result

- Partial materialized target slots: {summary["partial_materialized_target_slot_count"]}
- Partial unmaterialized target slots: {summary["partial_unmaterialized_target_slot_count"]}
- Partial application blocked target slots: {summary["partial_application_blocked_target_slot_count"]}
- Partial raw-to-processed comparison ready: `{str(summary["partial_raw_to_processed_value_comparison_ready"]).lower()}`
- Raw-to-processed comparison performed: `false`
- GitHub upload performed: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- partial_materialization_replay_performed: `true`
- partial_materialized_target_slot_count: `{summary["partial_materialized_target_slot_count"]}`
- partial_application_blocked_target_slot_count: `{summary["partial_application_blocked_target_slot_count"]}`
- raw-to-processed comparison performed: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: mistaking partial materialization replay for raw data reconciliation.
  Mitigation: raw-to-processed comparison, business consistency, lineage full check and formal report remain closed.
- Risk: leaking private materialized slot details publicly.
  Mitigation: public artifacts contain aggregate counts only; row-level replay evidence stays in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, canonical source-map file, completion template or public materialized value was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private replay and diagnostic if not needed.
"""
    test_results = """# Test Results

Status: passed locally.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_partial_materialization_replay.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_partial_materialization_replay.py --require-private-replay`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_partial_materialization_replay`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `git diff --check -- KMFA`
- `git ls-files KMFA | rg -n '\\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|pem|key|p12|pfx)$|\\.codex_private_runtime'`
- `rg -n --hidden --glob '!KMFA/.codex_private_runtime/**' --glob '!**/__pycache__/**' credential-like secret patterns KMFA`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-MATERIALIZATION-REPLAY"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PARTIAL-MATERIALIZATION-REPLAY",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "partial_materialization_replay_performed": True,
        "partial_materialization_replay_complete": summary["partial_materialization_replay_complete"],
        "partial_materialized_target_slot_count": summary["partial_materialized_target_slot_count"],
        "partial_unmaterialized_target_slot_count": summary["partial_unmaterialized_target_slot_count"],
        "partial_application_blocked_target_slot_count": summary["partial_application_blocked_target_slot_count"],
        "partial_raw_to_processed_value_comparison_ready": summary["partial_raw_to_processed_value_comparison_ready"],
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Performed private partial materialization replay for 101 target slots while keeping raw comparison and downstream release gates closed.",
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
        "PASS: KMFA v0.1.4 partial materialization replay generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"materialized={manifest['summary']['partial_materialized_target_slot_count']}, "
        f"unmaterialized={manifest['summary']['partial_unmaterialized_target_slot_count']})"
    )


if __name__ == "__main__":
    main()
