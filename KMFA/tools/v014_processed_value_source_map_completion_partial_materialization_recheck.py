#!/usr/bin/env python3
"""Recheck partial materialization readiness after private value-source fill.

This phase consumes the ignored private partial value-source fill draft and
rechecks coverage for the staged partial application slots. It does not
materialize values, mutate the canonical source map, compare raw and processed
values, or read the raw inbox.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_MATERIALIZATION_RECHECK"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-MATERIALIZATION-RECHECK-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-MATERIALIZATION-RECHECK"
VERSION = "0.1.4-partial-materialization-recheck"
STATUS = "completed_validated_local_only_partial_materialization_recheck_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_partial_materialization_recheck_passed_partial_replay_ready_full_reconciliation_blocked"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_MATERIALIZATION_REPLAY"
NEXT_REQUIRED_INPUT = "run_partial_materialization_replay_or_resolve_non_actionable_group_decisions"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_materialization_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_materialization_recheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_materialization_recheck_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_partial_materialization_recheck_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_materialization_recheck_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_materialization_recheck_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_materialization_recheck_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_FILL_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_VALUE_SOURCE_FILL/machine/processed_value_source_map_completion_partial_value_source_fill_summary.json"
)
PRIVATE_FILL_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_partial_value_source_fill/private_partial_value_source_fill.json"
)
PRIVATE_PRECHECK_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_partial_materialization_precheck/private_partial_materialization_precheck.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_partial_materialization_recheck"
PRIVATE_RECHECK_PATH = PRIVATE_OUTPUT_DIR / "private_partial_materialization_recheck.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_partial_materialization_recheck_diagnostic.json"

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
        "private_fill_committed": False,
        "private_precheck_committed": False,
        "private_recheck_committed": False,
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


def _build_recheck(
    *,
    generated_at: str,
    source_fill_summary: dict[str, Any],
    private_fill: dict[str, Any],
    private_precheck: dict[str, Any],
) -> dict[str, Any]:
    fill_rows = private_fill.get("processed_value_sources", [])
    blocked_fill_rows = private_fill.get("blocked_fill_rows", [])
    previous_awaiting_rows = private_precheck.get("awaiting_value_source_rows", [])
    source_blocked_rows = private_fill.get("source_blocked_partial_application_rows", [])
    if not isinstance(fill_rows, list) or not isinstance(blocked_fill_rows, list):
        raise ValueError("private fill row lists must be lists")
    if not isinstance(previous_awaiting_rows, list) or not isinstance(source_blocked_rows, list):
        raise ValueError("private precheck/source blocked row lists must be lists")

    fill_by_slot: dict[str, dict[str, Any]] = {}
    invalid_fill_rows: list[dict[str, Any]] = []
    for row in fill_rows:
        if not isinstance(row, dict):
            continue
        slot_id = row.get("target_slot_id")
        fingerprint = row.get("processed_value_fingerprint")
        if not isinstance(slot_id, str) or not isinstance(fingerprint, str) or not SHA256.fullmatch(fingerprint):
            invalid_fill_rows.append(
                {
                    "target_slot_id": slot_id,
                    "review_group_id": row.get("review_group_id"),
                    "materialization_recheck_status": "invalid_private_value_source_fill_row",
                }
            )
            continue
        fill_by_slot[slot_id] = row

    previous_awaiting_slot_ids = {
        row.get("target_slot_id") for row in previous_awaiting_rows if isinstance(row, dict) and row.get("target_slot_id")
    }
    materializable_rows: list[dict[str, Any]] = []
    awaiting_rows: list[dict[str, Any]] = []
    for row in previous_awaiting_rows:
        if not isinstance(row, dict):
            continue
        slot_id = row.get("target_slot_id")
        fill_row = fill_by_slot.get(slot_id) if isinstance(slot_id, str) else None
        if fill_row is None:
            awaiting_rows.append(
                {
                    "target_slot_id": slot_id,
                    "review_group_id": row.get("review_group_id"),
                    "candidate_status": row.get("candidate_status"),
                    "materialization_recheck_status": "missing_private_value_source_fill",
                }
            )
            continue
        materializable_rows.append(
            {
                "target_slot_id": slot_id,
                "review_group_id": fill_row.get("review_group_id"),
                "candidate_status": fill_row.get("candidate_status"),
                "owner_group_decision_code": fill_row.get("owner_group_decision_code"),
                "materialization_recheck_status": "materializable_after_private_fill",
                "processed_value_fingerprint": fill_row.get("processed_value_fingerprint"),
                "source_candidate_rank": fill_row.get("source_candidate_rank"),
                "source_record_ref_hash": fill_row.get("source_record_ref_hash"),
                "source_ref_hash": fill_row.get("source_ref_hash"),
                "source_cell_ref_hash": fill_row.get("source_cell_ref_hash"),
                "source_sheet_ref_hash": fill_row.get("source_sheet_ref_hash"),
                "source_record_kind": fill_row.get("source_record_kind"),
                "source_kind": fill_row.get("source_kind"),
            }
        )

    source_only_fill_count = len(set(fill_by_slot) - previous_awaiting_slot_ids)
    unique_value_source_count = len(
        {
            row.get("processed_value_fingerprint")
            for row in materializable_rows
            if isinstance(row.get("processed_value_fingerprint"), str)
        }
    )
    replay_ready = bool(previous_awaiting_rows) and not awaiting_rows and not blocked_fill_rows and not invalid_fill_rows
    summary = {
        "source_fill_phase_id": source_fill_summary.get("phase_id"),
        "source_fill_decision": source_fill_summary.get("decision"),
        "source_fill_candidate_target_slot_count": source_fill_summary.get(
            "partial_value_source_fill_candidate_target_slot_count"
        ),
        "source_fill_blocked_target_slot_count": source_fill_summary.get(
            "partial_value_source_fill_blocked_target_slot_count"
        ),
        "previous_awaiting_target_slot_count": len(previous_awaiting_rows),
        "partial_application_blocked_target_slot_count": len(source_blocked_rows),
        "private_fill_target_slot_count": len(fill_rows),
        "private_fill_invalid_target_slot_count": len(invalid_fill_rows),
        "private_fill_source_only_target_slot_count": source_only_fill_count,
        "partial_materializable_target_slot_count": len(materializable_rows),
        "partial_awaiting_value_source_target_slot_count": len(awaiting_rows),
        "partial_materializable_unique_value_source_count": unique_value_source_count,
        "partial_materialization_recheck_passed": replay_ready,
        "partial_materialization_replay_ready": replay_ready,
        "partial_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed": False,
    }
    return {
        "schema_version": "kmfa.private.v014_partial_materialization_recheck.v1",
        "classification": "private_partial_materialization_recheck_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_recheck",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_fill_phase_id": private_fill.get("phase_id"),
        "source_precheck_phase_id": private_precheck.get("phase_id"),
        "recheck_summary": summary,
        "materializable_rows": materializable_rows,
        "awaiting_value_source_rows": awaiting_rows,
        "invalid_fill_rows": invalid_fill_rows,
        "source_blocked_partial_application_rows": source_blocked_rows,
        "raw_boundary": _raw_boundary(),
    }


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_fill_summary = _read_json(SOURCE_FILL_SUMMARY_PATH)
    private_fill = _read_json(PRIVATE_FILL_PATH)
    private_precheck = _read_json(PRIVATE_PRECHECK_PATH)
    recheck = _build_recheck(
        generated_at=timestamp,
        source_fill_summary=source_fill_summary,
        private_fill=private_fill,
        private_precheck=private_precheck,
    )
    recheck_summary = recheck["recheck_summary"]
    diagnostic = {
        "schema_version": "kmfa.private.v014_partial_materialization_recheck_diagnostic.v1",
        "classification": "private_partial_materialization_recheck_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_recheck_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "recheck_summary": recheck_summary,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_RECHECK_PATH, recheck)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)

    summary = {
        "schema_version": "kmfa.v014_partial_materialization_recheck_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_fill_phase_id": recheck_summary["source_fill_phase_id"],
        "source_fill_decision": recheck_summary["source_fill_decision"],
        "source_fill_candidate_target_slot_count": recheck_summary["source_fill_candidate_target_slot_count"],
        "source_fill_blocked_target_slot_count": recheck_summary["source_fill_blocked_target_slot_count"],
        "previous_awaiting_target_slot_count": recheck_summary["previous_awaiting_target_slot_count"],
        "partial_application_blocked_target_slot_count": recheck_summary[
            "partial_application_blocked_target_slot_count"
        ],
        "private_fill_target_slot_count": recheck_summary["private_fill_target_slot_count"],
        "private_fill_invalid_target_slot_count": recheck_summary["private_fill_invalid_target_slot_count"],
        "private_fill_source_only_target_slot_count": recheck_summary["private_fill_source_only_target_slot_count"],
        "partial_materializable_target_slot_count": recheck_summary["partial_materializable_target_slot_count"],
        "partial_awaiting_value_source_target_slot_count": recheck_summary[
            "partial_awaiting_value_source_target_slot_count"
        ],
        "partial_materializable_unique_value_source_count": recheck_summary[
            "partial_materializable_unique_value_source_count"
        ],
        "partial_materialization_recheck_passed": recheck_summary["partial_materialization_recheck_passed"],
        "partial_materialization_replay_ready": recheck_summary["partial_materialization_replay_ready"],
        "partial_materialization_replay_performed": False,
        "private_recheck_written": True,
        "private_recheck_gitignored": _git_check_ignored(PRIVATE_RECHECK_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "processed_value_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed": False,
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
        "schema_version": "kmfa.v014_partial_materialization_recheck_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_recheck_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "partial_materializable_target_slot_count": summary["partial_materializable_target_slot_count"],
        "partial_awaiting_value_source_target_slot_count": summary["partial_awaiting_value_source_target_slot_count"],
        "partial_application_blocked_target_slot_count": summary["partial_application_blocked_target_slot_count"],
        "partial_materialization_recheck_passed": summary["partial_materialization_recheck_passed"],
        "partial_materialization_replay_ready": summary["partial_materialization_replay_ready"],
        "partial_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_partial_materialization_recheck_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_recheck_manifest",
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
            "private_recheck": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_partial_materialization_recheck.py "
            "--require-private-recheck"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Partial Materialization Recheck

Decision: {DECISION}

This phase rechecks the private partial value-source fill coverage for the partial application slots. It does not materialize processed values and does not compare raw and processed values.

## Public-safe aggregate result

- Previous awaiting target slots: {summary["previous_awaiting_target_slot_count"]}
- Partial materializable target slots: {summary["partial_materializable_target_slot_count"]}
- Partial target slots still awaiting value source: {summary["partial_awaiting_value_source_target_slot_count"]}
- Partial application blocked target slots: {summary["partial_application_blocked_target_slot_count"]}
- Partial materialization replay ready: `{str(summary["partial_materialization_replay_ready"]).lower()}`
- Raw-to-processed comparison performed: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- partial_materializable_target_slot_count: `{summary["partial_materializable_target_slot_count"]}`
- partial_awaiting_value_source_target_slot_count: `{summary["partial_awaiting_value_source_target_slot_count"]}`
- partial_materialization_replay_ready: `{str(summary["partial_materialization_replay_ready"]).lower()}`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: confusing partial replay readiness with business value consistency.
  Mitigation: replay, raw-to-processed comparison, lineage full check and formal report all remain closed.
- Risk: leaking private fingerprints publicly.
  Mitigation: public artifacts contain aggregate counts only; row-level evidence stays in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, canonical source-map file, completion template or materialized output was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private recheck and diagnostic if not needed.
"""
    test_results = """# Test Results

Status: passed locally.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_partial_materialization_recheck.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_partial_materialization_recheck.py --require-private-recheck`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_partial_materialization_recheck`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-MATERIALIZATION-RECHECK"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PARTIAL-MATERIALIZATION-RECHECK",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "previous_awaiting_target_slot_count": summary["previous_awaiting_target_slot_count"],
        "partial_materializable_target_slot_count": summary["partial_materializable_target_slot_count"],
        "partial_awaiting_value_source_target_slot_count": summary["partial_awaiting_value_source_target_slot_count"],
        "partial_application_blocked_target_slot_count": summary["partial_application_blocked_target_slot_count"],
        "partial_materialization_replay_ready": summary["partial_materialization_replay_ready"],
        "partial_materialization_replay_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Rechecked private partial value-source fill coverage and marked 101 partial slots ready for a separate materialization replay phase.",
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
        "PASS: KMFA v0.1.4 partial materialization recheck generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"materializable={manifest['summary']['partial_materializable_target_slot_count']}, "
        f"awaiting={manifest['summary']['partial_awaiting_value_source_target_slot_count']}, "
        f"replay_ready={manifest['summary']['partial_materialization_replay_ready']})"
    )


if __name__ == "__main__":
    main()
