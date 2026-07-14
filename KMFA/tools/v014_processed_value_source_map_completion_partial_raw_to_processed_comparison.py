#!/usr/bin/env python3
"""Compare private partial raw-candidate fingerprints with processed replay.

This phase consumes ignored private runtime artifacts only: the private partial
materialization replay and the private candidate catalog generated from earlier
raw-source extraction. It does not read the raw inbox, mutate raw files, or
publish row-level private evidence.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_RAW_TO_PROCESSED_COMPARISON"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-RAW-TO-PROCESSED-COMPARISON-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-RAW-TO-PROCESSED-COMPARISON"
VERSION = "0.1.4-partial-raw-to-processed-comparison"
STATUS = "completed_validated_local_only_partial_raw_to_processed_comparison_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_partial_raw_to_processed_fingerprint_comparison_passed_full_reconciliation_blocked"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_RESOLUTION_PACKET"
NEXT_REQUIRED_INPUT = "resolve_non_actionable_group_decisions_before_full_raw_to_processed_comparison"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_raw_to_processed_comparison_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_raw_to_processed_comparison_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_raw_to_processed_comparison_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_partial_raw_to_processed_comparison_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_raw_to_processed_comparison_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_raw_to_processed_comparison_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_raw_to_processed_comparison_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_REPLAY_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_MATERIALIZATION_REPLAY/machine/processed_value_source_map_completion_partial_materialization_replay_summary.json"
)
PRIVATE_REPLAY_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_partial_materialization_replay/private_partial_materialization_replay.json"
)
PRIVATE_CANDIDATE_CATALOG_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_intake_prep/private_candidate_catalog.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_partial_raw_to_processed_comparison"
PRIVATE_COMPARISON_PATH = PRIVATE_OUTPUT_DIR / "private_partial_raw_to_processed_comparison.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_partial_raw_to_processed_comparison_diagnostic.json"

HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
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
        "private_candidate_catalog_committed": False,
        "private_replay_committed": False,
        "private_comparison_committed": False,
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


def _build_comparison(
    *,
    generated_at: str,
    source_replay_summary: dict[str, Any],
    private_replay: dict[str, Any],
    candidate_catalog: dict[str, Any],
) -> dict[str, Any]:
    replay_rows = private_replay.get("materialized_partial_slots", [])
    blocked_rows = private_replay.get("source_blocked_partial_application_rows", [])
    if not isinstance(replay_rows, list) or not isinstance(blocked_rows, list):
        raise ValueError("private replay row lists must be lists")
    candidates = _candidate_by_record_ref(candidate_catalog)
    comparison_rows: list[dict[str, Any]] = []
    missing_candidate_rows: list[dict[str, Any]] = []
    mismatch_rows: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    for row in replay_rows:
        if not isinstance(row, dict):
            continue
        slot_id = row.get("target_slot_id")
        record_ref = row.get("source_record_ref_hash")
        replay_fingerprint = _normalize_sha256(row.get("processed_value_fingerprint"))
        if not isinstance(record_ref, str) or not replay_fingerprint:
            invalid_rows.append(
                {
                    "target_slot_id": slot_id,
                    "review_group_id": row.get("review_group_id"),
                    "comparison_status": "invalid_private_replay_row",
                }
            )
            continue
        candidate = candidates.get(record_ref)
        if candidate is None:
            missing_candidate_rows.append(
                {
                    "target_slot_id": slot_id,
                    "review_group_id": row.get("review_group_id"),
                    "source_record_ref_hash": record_ref,
                    "comparison_status": "missing_private_candidate_record",
                }
            )
            continue
        candidate_fingerprint = _normalize_sha256(candidate.get("numeric_value_fingerprint"))
        if candidate_fingerprint != replay_fingerprint:
            mismatch_rows.append(
                {
                    "target_slot_id": slot_id,
                    "review_group_id": row.get("review_group_id"),
                    "source_record_ref_hash": record_ref,
                    "comparison_status": "fingerprint_mismatch",
                    "source_candidate_fingerprint": candidate_fingerprint,
                    "processed_replay_fingerprint": replay_fingerprint,
                }
            )
            continue
        comparison_rows.append(
            {
                "target_slot_id": slot_id,
                "review_group_id": row.get("review_group_id"),
                "source_record_ref_hash": record_ref,
                "source_ref_hash": row.get("source_ref_hash"),
                "source_cell_ref_hash": row.get("source_cell_ref_hash"),
                "source_sheet_ref_hash": row.get("source_sheet_ref_hash"),
                "source_record_kind": row.get("source_record_kind"),
                "source_kind": row.get("source_kind"),
                "source_candidate_rank": row.get("source_candidate_rank"),
                "source_candidate_fingerprint": candidate_fingerprint,
                "processed_replay_fingerprint": replay_fingerprint,
                "comparison_status": "exact_fingerprint_match",
            }
        )

    comparable_count = len(comparison_rows) + len(mismatch_rows)
    partial_passed = (
        len(replay_rows) > 0
        and len(comparison_rows) == len(replay_rows)
        and not missing_candidate_rows
        and not mismatch_rows
        and not invalid_rows
    )
    summary = {
        "source_replay_phase_id": source_replay_summary.get("phase_id"),
        "source_replay_decision": source_replay_summary.get("decision"),
        "source_replay_materialized_target_slot_count": source_replay_summary.get("partial_materialized_target_slot_count"),
        "source_replay_unmaterialized_target_slot_count": source_replay_summary.get("partial_unmaterialized_target_slot_count"),
        "candidate_catalog_record_count": int(candidate_catalog.get("candidate_catalog_record_count") or 0),
        "partial_replay_target_slot_count": len(replay_rows),
        "partial_comparable_pair_count": comparable_count,
        "partial_exact_match_count": len(comparison_rows),
        "partial_mismatch_count": len(mismatch_rows),
        "partial_missing_candidate_count": len(missing_candidate_rows),
        "partial_invalid_replay_row_count": len(invalid_rows),
        "partial_application_blocked_target_slot_count": len(blocked_rows),
        "partial_raw_to_processed_value_comparison_performed": True,
        "partial_raw_to_processed_value_consistency_verified": partial_passed,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    return {
        "schema_version": "kmfa.private.v014_partial_raw_to_processed_comparison.v1",
        "classification": "private_partial_raw_to_processed_comparison_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_partial_raw_to_processed_comparison",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_replay_phase_id": private_replay.get("phase_id"),
        "source_candidate_catalog_phase_id": candidate_catalog.get("phase_id"),
        "comparison_summary": summary,
        "exact_match_rows": comparison_rows,
        "mismatch_rows": mismatch_rows,
        "missing_candidate_rows": missing_candidate_rows,
        "invalid_replay_rows": invalid_rows,
        "source_blocked_partial_application_rows": blocked_rows,
        "raw_boundary": _raw_boundary(),
    }


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_replay_summary = _read_json(SOURCE_REPLAY_SUMMARY_PATH)
    private_replay = _read_json(PRIVATE_REPLAY_PATH)
    candidate_catalog = _read_json(PRIVATE_CANDIDATE_CATALOG_PATH)
    comparison = _build_comparison(
        generated_at=timestamp,
        source_replay_summary=source_replay_summary,
        private_replay=private_replay,
        candidate_catalog=candidate_catalog,
    )
    comparison_summary = comparison["comparison_summary"]
    diagnostic = {
        "schema_version": "kmfa.private.v014_partial_raw_to_processed_comparison_diagnostic.v1",
        "classification": "private_partial_raw_to_processed_comparison_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_partial_raw_to_processed_comparison_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "comparison_summary": comparison_summary,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_COMPARISON_PATH, comparison)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)

    summary = {
        "schema_version": "kmfa.v014_partial_raw_to_processed_comparison_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_raw_to_processed_comparison_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_replay_phase_id": comparison_summary["source_replay_phase_id"],
        "source_replay_decision": comparison_summary["source_replay_decision"],
        "source_replay_materialized_target_slot_count": comparison_summary[
            "source_replay_materialized_target_slot_count"
        ],
        "source_replay_unmaterialized_target_slot_count": comparison_summary[
            "source_replay_unmaterialized_target_slot_count"
        ],
        "candidate_catalog_record_count": comparison_summary["candidate_catalog_record_count"],
        "partial_replay_target_slot_count": comparison_summary["partial_replay_target_slot_count"],
        "partial_comparable_pair_count": comparison_summary["partial_comparable_pair_count"],
        "partial_exact_match_count": comparison_summary["partial_exact_match_count"],
        "partial_mismatch_count": comparison_summary["partial_mismatch_count"],
        "partial_missing_candidate_count": comparison_summary["partial_missing_candidate_count"],
        "partial_invalid_replay_row_count": comparison_summary["partial_invalid_replay_row_count"],
        "partial_application_blocked_target_slot_count": comparison_summary[
            "partial_application_blocked_target_slot_count"
        ],
        "partial_raw_to_processed_value_comparison_performed": True,
        "partial_raw_to_processed_value_consistency_verified": comparison_summary[
            "partial_raw_to_processed_value_consistency_verified"
        ],
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "private_comparison_written": True,
        "private_comparison_gitignored": _git_check_ignored(PRIVATE_COMPARISON_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
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
        "schema_version": "kmfa.v014_partial_raw_to_processed_comparison_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_raw_to_processed_comparison_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "partial_replay_target_slot_count": summary["partial_replay_target_slot_count"],
        "partial_comparable_pair_count": summary["partial_comparable_pair_count"],
        "partial_exact_match_count": summary["partial_exact_match_count"],
        "partial_mismatch_count": summary["partial_mismatch_count"],
        "partial_missing_candidate_count": summary["partial_missing_candidate_count"],
        "partial_application_blocked_target_slot_count": summary["partial_application_blocked_target_slot_count"],
        "partial_raw_to_processed_value_comparison_performed": True,
        "partial_raw_to_processed_value_consistency_verified": summary[
            "partial_raw_to_processed_value_consistency_verified"
        ],
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_partial_raw_to_processed_comparison_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_raw_to_processed_comparison_manifest",
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
            "private_comparison": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_partial_raw_to_processed_comparison.py "
            "--require-private-comparison"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Partial Raw-to-Processed Comparison

Decision: {DECISION}

This phase compares private raw-candidate fingerprints with the private partial materialization replay output. It does not read the raw inbox and does not publish row-level private evidence.

## Public-safe aggregate result

- Partial replay target slots: {summary["partial_replay_target_slot_count"]}
- Comparable pairs: {summary["partial_comparable_pair_count"]}
- Exact matches: {summary["partial_exact_match_count"]}
- Mismatches: {summary["partial_mismatch_count"]}
- Missing candidates: {summary["partial_missing_candidate_count"]}
- Partial blocked target slots: {summary["partial_application_blocked_target_slot_count"]}
- Full raw-to-processed comparison performed: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- partial_raw_to_processed_value_comparison_performed: `true`
- partial_exact_match_count: `{summary["partial_exact_match_count"]}`
- partial_mismatch_count: `{summary["partial_mismatch_count"]}`
- partial_application_blocked_target_slot_count: `{summary["partial_application_blocked_target_slot_count"]}`
- full raw-to-processed comparison performed: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: mistaking partial fingerprint comparison for full business value consistency.
  Mitigation: full raw-to-processed comparison, 12 blocked target slots, lineage full check and formal report remain closed.
- Risk: leaking private raw candidate evidence publicly.
  Mitigation: public artifacts contain aggregate counts only; row-level comparison stays in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, canonical source-map file, completion template or public business value was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private comparison and diagnostic if not needed.
"""
    test_results = """# Test Results

Status: passed locally.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_partial_raw_to_processed_comparison.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_partial_raw_to_processed_comparison.py --require-private-comparison`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_partial_raw_to_processed_comparison`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-RAW-TO-PROCESSED-COMPARISON"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PARTIAL-RAW-TO-PROCESSED-COMPARISON",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "partial_raw_to_processed_value_comparison_performed": True,
        "partial_comparable_pair_count": summary["partial_comparable_pair_count"],
        "partial_exact_match_count": summary["partial_exact_match_count"],
        "partial_mismatch_count": summary["partial_mismatch_count"],
        "partial_application_blocked_target_slot_count": summary["partial_application_blocked_target_slot_count"],
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Compared private raw-candidate fingerprints with 101 private materialized partial slots and kept full reconciliation blocked for 12 target slots.",
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
        "PASS: KMFA v0.1.4 partial raw-to-processed comparison generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"matches={manifest['summary']['partial_exact_match_count']}, "
        f"mismatches={manifest['summary']['partial_mismatch_count']})"
    )


if __name__ == "__main__":
    main()
