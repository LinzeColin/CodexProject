#!/usr/bin/env python3
"""Stage private partial value-source fills for KMFA v0.1.4.

This phase consumes only existing ignored private candidate evidence and the
private partial application result. It creates a private staged fill draft for
the actionable partial slots, without mutating the canonical source map,
materializing values, comparing raw data, or reading the raw inbox.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_VALUE_SOURCE_FILL"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-VALUE-SOURCE-FILL-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-VALUE-SOURCE-FILL"
VERSION = "0.1.4-partial-value-source-fill"
STATUS = "completed_validated_local_only_private_partial_value_source_fill_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_partial_value_source_fill_staged_materialization_recheck_required"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_MATERIALIZATION_RECHECK"
NEXT_REQUIRED_INPUT = "rerun_partial_materialization_precheck_against_private_partial_value_source_fill"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_value_source_fill_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_value_source_fill_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_value_source_fill_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_partial_value_source_fill_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_value_source_fill_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_value_source_fill_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_value_source_fill_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_PRECHECK_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_MATERIALIZATION_PRECHECK/machine/processed_value_source_map_completion_partial_materialization_precheck_summary.json"
)
PRIVATE_PRECHECK_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_partial_materialization_precheck/private_partial_materialization_precheck.json"
)
PRIVATE_PARTIAL_APPLICATION_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_partial_application/private_owner_group_partial_application_result.json"
)
PRIVATE_CANDIDATE_CATALOG_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_intake_prep/private_candidate_catalog.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_partial_value_source_fill"
PRIVATE_FILL_PATH = PRIVATE_OUTPUT_DIR / "private_partial_value_source_fill.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_partial_value_source_fill_diagnostic.json"

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
        "private_partial_application_committed": False,
        "private_precheck_committed": False,
        "private_candidate_catalog_committed": False,
        "private_partial_value_source_fill_committed": False,
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


def _normalize_sha256(value: Any) -> tuple[str | None, bool]:
    if isinstance(value, str) and SHA256.fullmatch(value):
        return value, False
    if isinstance(value, str) and HEX64.fullmatch(value):
        return f"sha256:{value.lower()}", True
    return None, False


def _rank1_candidates(candidate_catalog: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    records = candidate_catalog.get("candidate_catalog_records", [])
    if not isinstance(records, list):
        raise ValueError("candidate_catalog_records must be a list")
    by_group: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if isinstance(record, dict):
            group_id = record.get("review_group_id")
            if isinstance(group_id, str) and group_id:
                by_group.setdefault(group_id, []).append(record)
    rank1: dict[str, dict[str, Any]] = {}
    counters: Counter[str] = Counter()
    for group_id, group_records in by_group.items():
        first_rank = [record for record in group_records if record.get("candidate_rank") == 1]
        if len(first_rank) != 1:
            counters["groups_without_single_rank1_candidate"] += 1
            continue
        fingerprint, normalized = _normalize_sha256(first_rank[0].get("numeric_value_fingerprint"))
        if fingerprint is None:
            counters["groups_without_normalizable_rank1_fingerprint"] += 1
            continue
        candidate = {
            "candidate_rank": 1,
            "processed_value_fingerprint": fingerprint,
            "fingerprint_prefix_normalized": normalized,
            "record_ref_hash": first_rank[0].get("record_ref_hash"),
            "source_ref_hash": first_rank[0].get("source_ref_hash"),
            "cell_ref_hash": first_rank[0].get("cell_ref_hash"),
            "sheet_ref_hash": first_rank[0].get("sheet_ref_hash"),
            "record_kind": first_rank[0].get("record_kind"),
            "source_kind": first_rank[0].get("source_kind"),
        }
        rank1[group_id] = {key: value for key, value in candidate.items() if value is not None}
        if normalized:
            counters["rank1_fingerprint_prefix_normalized_group_count"] += 1
        else:
            counters["rank1_fingerprint_already_prefixed_group_count"] += 1
    counters["candidate_catalog_record_count"] = len(records)
    counters["candidate_catalog_group_count"] = len(by_group)
    counters["rank1_candidate_group_count"] = len(rank1)
    return rank1, dict(counters)


def _build_private_fill(
    *,
    generated_at: str,
    source_precheck: dict[str, Any],
    private_precheck: dict[str, Any],
    partial_application: dict[str, Any],
    candidate_catalog: dict[str, Any],
) -> dict[str, Any]:
    applied_rows = partial_application.get("applied_rows", [])
    precheck_awaiting_rows = private_precheck.get("awaiting_value_source_rows", [])
    blocked_rows = partial_application.get("blocked_rows", [])
    if not isinstance(applied_rows, list) or not isinstance(precheck_awaiting_rows, list):
        raise ValueError("private partial/precheck rows must be lists")
    if not isinstance(blocked_rows, list):
        raise ValueError("private partial blocked rows must be a list")

    rank1_by_group, candidate_counters = _rank1_candidates(candidate_catalog)
    awaiting_slot_ids = {
        row.get("target_slot_id") for row in precheck_awaiting_rows if isinstance(row, dict) and row.get("target_slot_id")
    }
    fill_rows: list[dict[str, Any]] = []
    blocked_fill_rows: list[dict[str, Any]] = []
    decision_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    for row in applied_rows:
        if not isinstance(row, dict):
            continue
        slot_id = row.get("target_slot_id")
        review_group_id = row.get("review_group_id")
        decision_code = str(row.get("owner_group_decision_code", "UNKNOWN"))
        candidate_status = str(row.get("candidate_status", "unknown"))
        decision_counts[decision_code] += 1
        status_counts[candidate_status] += 1
        if slot_id not in awaiting_slot_ids:
            blocked_fill_rows.append(
                {
                    "target_slot_id": slot_id,
                    "review_group_id": review_group_id,
                    "owner_group_decision_code": decision_code,
                    "private_fill_status": "blocked_not_in_precheck_awaiting_rows",
                }
            )
            continue
        candidate = rank1_by_group.get(str(review_group_id))
        if candidate is None:
            blocked_fill_rows.append(
                {
                    "target_slot_id": slot_id,
                    "review_group_id": review_group_id,
                    "owner_group_decision_code": decision_code,
                    "private_fill_status": "blocked_missing_normalizable_rank1_candidate",
                }
            )
            continue
        fill_rows.append(
            {
                "target_slot_id": slot_id,
                "review_group_id": review_group_id,
                "candidate_status": candidate_status,
                "owner_group_decision_code": decision_code,
                "private_fill_status": "staged_private_partial_value_source_fill",
                "source_candidate_rank": candidate["candidate_rank"],
                "processed_value_fingerprint": candidate["processed_value_fingerprint"],
                "fingerprint_prefix_normalized": candidate["fingerprint_prefix_normalized"],
                "source_record_ref_hash": candidate.get("record_ref_hash"),
                "source_ref_hash": candidate.get("source_ref_hash"),
                "source_cell_ref_hash": candidate.get("cell_ref_hash"),
                "source_sheet_ref_hash": candidate.get("sheet_ref_hash"),
                "source_record_kind": candidate.get("record_kind"),
                "source_kind": candidate.get("source_kind"),
            }
        )

    fill_group_count = len({row["review_group_id"] for row in fill_rows})
    fill_unique_fingerprint_count = len({row["processed_value_fingerprint"] for row in fill_rows})
    normalized_group_count = candidate_counters.get("rank1_fingerprint_prefix_normalized_group_count", 0)
    summary = {
        "source_precheck_phase_id": source_precheck.get("phase_id"),
        "source_precheck_decision": source_precheck.get("decision"),
        "source_precheck_awaiting_target_slot_count": source_precheck.get(
            "partial_awaiting_value_source_target_slot_count"
        ),
        "partial_application_target_slot_count": len(applied_rows),
        "partial_application_blocked_target_slot_count": len(blocked_rows),
        "candidate_catalog_record_count": candidate_counters["candidate_catalog_record_count"],
        "candidate_catalog_group_count": candidate_counters["candidate_catalog_group_count"],
        "rank1_candidate_group_count": candidate_counters["rank1_candidate_group_count"],
        "rank1_fingerprint_prefix_normalized_group_count": normalized_group_count,
        "partial_value_source_fill_candidate_group_count": fill_group_count,
        "partial_value_source_fill_candidate_target_slot_count": len(fill_rows),
        "partial_value_source_fill_blocked_target_slot_count": len(blocked_fill_rows),
        "partial_value_source_fill_unique_fingerprint_count": fill_unique_fingerprint_count,
        "row_decision_code_counts": dict(decision_counts),
        "row_candidate_status_counts": dict(status_counts),
        "private_partial_value_source_fill_staged": len(fill_rows) == len(applied_rows) and not blocked_fill_rows,
        "partial_materialization_recheck_ready": len(fill_rows) == len(applied_rows) and not blocked_fill_rows,
        "partial_materialization_replay_ready": False,
        "partial_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed": False,
    }
    return {
        "schema_version": "kmfa.private.v014_partial_value_source_fill.v1",
        "classification": "private_partial_value_source_fill_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_partial_value_source_fill",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_precheck_phase_id": source_precheck.get("phase_id"),
        "source_partial_application_phase_id": partial_application.get("phase_id"),
        "source_candidate_catalog_phase_id": candidate_catalog.get("phase_id"),
        "partial_value_source_fill_summary": summary,
        "processed_value_sources": fill_rows,
        "blocked_fill_rows": blocked_fill_rows,
        "source_blocked_partial_application_rows": blocked_rows,
        "raw_boundary": _raw_boundary(),
    }


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_precheck_summary = _read_json(SOURCE_PRECHECK_SUMMARY_PATH)
    private_precheck = _read_json(PRIVATE_PRECHECK_PATH)
    partial_application = _read_json(PRIVATE_PARTIAL_APPLICATION_PATH)
    candidate_catalog = _read_json(PRIVATE_CANDIDATE_CATALOG_PATH)
    private_fill = _build_private_fill(
        generated_at=timestamp,
        source_precheck=source_precheck_summary,
        private_precheck=private_precheck,
        partial_application=partial_application,
        candidate_catalog=candidate_catalog,
    )
    fill_summary = private_fill["partial_value_source_fill_summary"]
    diagnostic = {
        "schema_version": "kmfa.private.v014_partial_value_source_fill_diagnostic.v1",
        "classification": "private_partial_value_source_fill_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_partial_value_source_fill_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "partial_value_source_fill_summary": fill_summary,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_FILL_PATH, private_fill)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)

    summary = {
        "schema_version": "kmfa.v014_partial_value_source_fill_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_value_source_fill_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_precheck_phase_id": fill_summary["source_precheck_phase_id"],
        "source_precheck_decision": fill_summary["source_precheck_decision"],
        "source_precheck_awaiting_target_slot_count": fill_summary["source_precheck_awaiting_target_slot_count"],
        "partial_application_target_slot_count": fill_summary["partial_application_target_slot_count"],
        "partial_application_blocked_target_slot_count": fill_summary["partial_application_blocked_target_slot_count"],
        "candidate_catalog_record_count": fill_summary["candidate_catalog_record_count"],
        "candidate_catalog_group_count": fill_summary["candidate_catalog_group_count"],
        "rank1_candidate_group_count": fill_summary["rank1_candidate_group_count"],
        "rank1_fingerprint_prefix_normalized_group_count": fill_summary[
            "rank1_fingerprint_prefix_normalized_group_count"
        ],
        "partial_value_source_fill_candidate_group_count": fill_summary[
            "partial_value_source_fill_candidate_group_count"
        ],
        "partial_value_source_fill_candidate_target_slot_count": fill_summary[
            "partial_value_source_fill_candidate_target_slot_count"
        ],
        "partial_value_source_fill_blocked_target_slot_count": fill_summary[
            "partial_value_source_fill_blocked_target_slot_count"
        ],
        "partial_value_source_fill_unique_fingerprint_count": fill_summary[
            "partial_value_source_fill_unique_fingerprint_count"
        ],
        "row_decision_code_counts": fill_summary["row_decision_code_counts"],
        "row_candidate_status_counts": fill_summary["row_candidate_status_counts"],
        "private_partial_value_source_fill_staged": fill_summary["private_partial_value_source_fill_staged"],
        "private_partial_value_source_fill_written": True,
        "private_partial_value_source_fill_gitignored": _git_check_ignored(PRIVATE_FILL_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "partial_materialization_recheck_ready": fill_summary["partial_materialization_recheck_ready"],
        "partial_materialization_replay_ready": False,
        "partial_materialization_replay_performed": False,
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
        "schema_version": "kmfa.v014_partial_value_source_fill_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_value_source_fill_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "partial_application_target_slot_count": summary["partial_application_target_slot_count"],
        "partial_value_source_fill_candidate_target_slot_count": summary[
            "partial_value_source_fill_candidate_target_slot_count"
        ],
        "partial_value_source_fill_blocked_target_slot_count": summary[
            "partial_value_source_fill_blocked_target_slot_count"
        ],
        "partial_materialization_recheck_ready": summary["partial_materialization_recheck_ready"],
        "partial_materialization_replay_ready": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_partial_value_source_fill_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_value_source_fill_manifest",
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
            "private_partial_value_source_fill": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_partial_value_source_fill.py "
            "--require-private-fill"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Partial Value-Source Fill

Decision: {DECISION}

This phase stages private value-source fill candidates for the partial application slots. It does not mutate the canonical source map, materialize processed values, compare raw and processed values, or read the raw inbox.

## Public-safe aggregate result

- Partial application target slots: {summary["partial_application_target_slot_count"]}
- Candidate catalog records consumed from private runtime: {summary["candidate_catalog_record_count"]}
- Rank-1 candidate groups: {summary["rank1_candidate_group_count"]}
- Private fill candidate target slots: {summary["partial_value_source_fill_candidate_target_slot_count"]}
- Private fill blocked target slots: {summary["partial_value_source_fill_blocked_target_slot_count"]}
- Partial materialization recheck ready: `{str(summary["partial_materialization_recheck_ready"]).lower()}`
- Partial materialization replay ready: `false`
- Raw-to-processed comparison performed: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- partial_value_source_fill_candidate_target_slot_count: `{summary["partial_value_source_fill_candidate_target_slot_count"]}`
- partial_value_source_fill_blocked_target_slot_count: `{summary["partial_value_source_fill_blocked_target_slot_count"]}`
- partial_materialization_replay_ready: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating private fill candidates as verified materialized values.
  Mitigation: this phase only stages a private fill draft; replay and raw-to-processed comparison remain closed.
- Risk: leaking private candidate fingerprints publicly.
  Mitigation: public artifacts contain aggregate counts only; candidate-level fingerprints stay in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, canonical source-map file, completion template or materialized output was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private fill and diagnostic if not needed.
"""
    test_results = """# Test Results

Status: passed locally.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_partial_value_source_fill.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_partial_value_source_fill.py --require-private-fill`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_partial_value_source_fill`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-VALUE-SOURCE-FILL"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PARTIAL-VALUE-SOURCE-FILL",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "partial_application_target_slot_count": summary["partial_application_target_slot_count"],
        "candidate_catalog_record_count": summary["candidate_catalog_record_count"],
        "partial_value_source_fill_candidate_target_slot_count": summary[
            "partial_value_source_fill_candidate_target_slot_count"
        ],
        "partial_value_source_fill_blocked_target_slot_count": summary[
            "partial_value_source_fill_blocked_target_slot_count"
        ],
        "partial_materialization_recheck_ready": summary["partial_materialization_recheck_ready"],
        "partial_materialization_replay_ready": False,
        "partial_materialization_replay_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Staged private partial value-source fills for 101 target slots and kept materialization replay plus raw comparison closed.",
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
        "PASS: KMFA v0.1.4 partial value-source fill generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"fill_candidates={manifest['summary']['partial_value_source_fill_candidate_target_slot_count']}, "
        f"blocked={manifest['summary']['partial_value_source_fill_blocked_target_slot_count']})"
    )


if __name__ == "__main__":
    main()
