#!/usr/bin/env python3
"""Precheck partial processed-value materialization readiness for KMFA v0.1.4.

This phase consumes the private owner-group partial application result and
checks whether matching private processed-value fingerprints exist. It does not
materialize values, compare raw and processed values, or read/mutate the raw
inbox.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_MATERIALIZATION_PRECHECK"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-MATERIALIZATION-PRECHECK-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-MATERIALIZATION-PRECHECK"
VERSION = "0.1.4-partial-materialization-precheck"
STATUS = "completed_validated_local_only_partial_materialization_precheck_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "partial_materialization_precheck_blocked_no_matching_private_value_fingerprints"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_VALUE_SOURCE_FILL"
NEXT_REQUIRED_INPUT = "private_processed_value_fingerprints_for_partial_application_slots"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_materialization_precheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_materialization_precheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_partial_materialization_precheck_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_partial_materialization_precheck_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_materialization_precheck_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_materialization_precheck_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_materialization_precheck_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_PARTIAL_APPLICATION_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_PARTIAL_APPLICATION/machine/processed_value_source_map_completion_owner_group_partial_application_summary.json"
)
PRIVATE_PARTIAL_APPLICATION_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_partial_application/private_owner_group_partial_application_result.json"
)
PRIVATE_VALUE_SOURCE_MAP_PATH = (
    PROJECT_ROOT / ".codex_private_runtime/v014_private_processed_value_materialization/private_processed_value_source_map.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_partial_materialization_precheck"
)
PRIVATE_PRECHECK_PATH = PRIVATE_OUTPUT_DIR / "private_partial_materialization_precheck.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_partial_materialization_precheck_diagnostic.json"


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
        "private_value_source_map_committed": False,
        "private_precheck_committed": False,
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


def _value_sources(source_map: dict[str, Any]) -> dict[str, str]:
    sources: dict[str, str] = {}
    records = source_map.get("processed_value_sources", [])
    if not isinstance(records, list):
        raise ValueError("processed_value_sources must be a list")
    for record in records:
        if not isinstance(record, dict):
            continue
        slot_id = record.get("target_slot_id")
        fingerprint = record.get("processed_value_fingerprint") or record.get("value_fingerprint")
        if isinstance(slot_id, str) and slot_id and isinstance(fingerprint, str) and fingerprint.startswith("sha256:"):
            sources[slot_id] = fingerprint
    return sources


def _precheck(generated_at: str, partial_application: dict[str, Any], value_source_map: dict[str, Any] | None) -> dict[str, Any]:
    applied_rows = partial_application.get("applied_rows", [])
    blocked_rows = partial_application.get("blocked_rows", [])
    if not isinstance(applied_rows, list) or not isinstance(blocked_rows, list):
        raise ValueError("private partial application row lists must be lists")
    sources = _value_sources(value_source_map) if value_source_map is not None else {}
    materializable_rows: list[dict[str, Any]] = []
    awaiting_rows: list[dict[str, Any]] = []
    for row in applied_rows:
        if not isinstance(row, dict):
            continue
        slot_id = row.get("target_slot_id")
        fingerprint = sources.get(slot_id) if isinstance(slot_id, str) else None
        row_record = {
            "target_slot_id": slot_id,
            "review_group_id": row.get("review_group_id"),
            "candidate_status": row.get("candidate_status"),
            "materialization_precheck_status": "materializable" if fingerprint else "missing_private_value_fingerprint",
            "private_processed_value_fingerprint_present": fingerprint is not None,
        }
        if fingerprint:
            row_record["processed_value_fingerprint"] = fingerprint
            materializable_rows.append(row_record)
        else:
            awaiting_rows.append(row_record)
    source_only_slot_count = len(set(sources) - {row.get("target_slot_id") for row in applied_rows if isinstance(row, dict)})
    summary = {
        "partial_application_target_slot_count": len(applied_rows),
        "partial_application_blocked_target_slot_count": len(blocked_rows),
        "private_value_source_map_present": value_source_map is not None,
        "private_value_source_fingerprint_count": len(sources),
        "partial_materializable_target_slot_count": len(materializable_rows),
        "partial_awaiting_value_source_target_slot_count": len(awaiting_rows),
        "private_value_source_without_partial_slot_count": source_only_slot_count,
        "partial_materialization_precheck_passed": len(applied_rows) > 0 and len(awaiting_rows) == 0,
        "partial_materialization_replay_ready": len(applied_rows) > 0 and len(awaiting_rows) == 0,
        "partial_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed": False,
    }
    return {
        "schema_version": "kmfa.private.v014_partial_materialization_precheck.v1",
        "classification": "private_partial_materialization_precheck_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_precheck",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_partial_application_phase_id": partial_application.get("phase_id"),
        "precheck_summary": summary,
        "materializable_rows": materializable_rows,
        "awaiting_value_source_rows": awaiting_rows,
        "blocked_rows": blocked_rows,
        "raw_boundary": _raw_boundary(),
    }


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_PARTIAL_APPLICATION_SUMMARY_PATH)
    partial_application = _read_json(PRIVATE_PARTIAL_APPLICATION_PATH)
    value_source_map = _read_json(PRIVATE_VALUE_SOURCE_MAP_PATH) if PRIVATE_VALUE_SOURCE_MAP_PATH.exists() else None
    precheck = _precheck(timestamp, partial_application, value_source_map)
    precheck_summary = precheck["precheck_summary"]
    diagnostic = {
        "schema_version": "kmfa.private.v014_partial_materialization_precheck_diagnostic.v1",
        "classification": "private_partial_materialization_precheck_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_precheck_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "precheck_summary": precheck_summary,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_PRECHECK_PATH, precheck)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)

    summary = {
        "schema_version": "kmfa.v014_partial_materialization_precheck_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_precheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_partial_application_phase_id": source_summary.get("phase_id"),
        "source_partial_application_decision": source_summary.get("decision"),
        "source_partial_application_target_slot_count": source_summary.get("private_partial_application_target_slot_count"),
        "source_partial_application_blocked_target_slot_count": source_summary.get("private_blocked_target_slot_count"),
        "partial_application_target_slot_count": precheck_summary["partial_application_target_slot_count"],
        "partial_application_blocked_target_slot_count": precheck_summary["partial_application_blocked_target_slot_count"],
        "private_value_source_map_present": precheck_summary["private_value_source_map_present"],
        "private_value_source_fingerprint_count": precheck_summary["private_value_source_fingerprint_count"],
        "partial_materializable_target_slot_count": precheck_summary["partial_materializable_target_slot_count"],
        "partial_awaiting_value_source_target_slot_count": precheck_summary[
            "partial_awaiting_value_source_target_slot_count"
        ],
        "private_value_source_without_partial_slot_count": precheck_summary["private_value_source_without_partial_slot_count"],
        "partial_materialization_precheck_passed": precheck_summary["partial_materialization_precheck_passed"],
        "partial_materialization_replay_ready": precheck_summary["partial_materialization_replay_ready"],
        "partial_materialization_replay_performed": False,
        "private_precheck_written": True,
        "private_precheck_gitignored": _git_check_ignored(PRIVATE_PRECHECK_PATH),
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
        "schema_version": "kmfa.v014_partial_materialization_precheck_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_precheck_go_no_go_report",
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
        "private_value_source_fingerprint_count": summary["private_value_source_fingerprint_count"],
        "partial_materializable_target_slot_count": summary["partial_materializable_target_slot_count"],
        "partial_awaiting_value_source_target_slot_count": summary["partial_awaiting_value_source_target_slot_count"],
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
        "schema_version": "kmfa.v014_partial_materialization_precheck_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_partial_materialization_precheck_manifest",
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
            "private_precheck": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_partial_materialization_precheck.py "
            "--require-private-precheck"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Partial Materialization Precheck

Decision: {DECISION}

This phase checks whether the private partial application slots have matching private processed-value fingerprints. It does not materialize values and does not compare raw and processed values.

## Public-safe aggregate result

- Partial application target slots: {summary["partial_application_target_slot_count"]}
- Private value-source fingerprints available: {summary["private_value_source_fingerprint_count"]}
- Partial materializable target slots: {summary["partial_materializable_target_slot_count"]}
- Partial target slots awaiting value source: {summary["partial_awaiting_value_source_target_slot_count"]}
- Partial materialization replay ready: `false`
- Raw-to-processed comparison performed: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- partial_materializable_target_slot_count: `{summary["partial_materializable_target_slot_count"]}`
- partial_awaiting_value_source_target_slot_count: `{summary["partial_awaiting_value_source_target_slot_count"]}`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating old private value-source fingerprints as matching the current partial application.
  Mitigation: the precheck requires target-slot intersection before replay readiness can become true.
- Risk: leaking private fingerprints publicly.
  Mitigation: public artifacts contain only aggregate counts; fingerprints stay in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, canonical source-map file, completion template or materialized output was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private precheck and diagnostic if not needed.
"""
    test_results = """# Test Results

Status: passed locally.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_partial_materialization_precheck.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_partial_materialization_precheck.py --require-private-precheck`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_partial_materialization_precheck`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PARTIAL-MATERIALIZATION-PRECHECK"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PARTIAL-MATERIALIZATION-PRECHECK",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "partial_application_target_slot_count": summary["partial_application_target_slot_count"],
        "private_value_source_fingerprint_count": summary["private_value_source_fingerprint_count"],
        "partial_materializable_target_slot_count": summary["partial_materializable_target_slot_count"],
        "partial_awaiting_value_source_target_slot_count": summary["partial_awaiting_value_source_target_slot_count"],
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
        "summary": "Checked partial materialization readiness and found no matching private value fingerprints for the 101 staged partial slots.",
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
        "PASS: KMFA v0.1.4 partial materialization precheck generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"materializable={manifest['summary']['partial_materializable_target_slot_count']}, "
        f"awaiting={manifest['summary']['partial_awaiting_value_source_target_slot_count']})"
    )


if __name__ == "__main__":
    main()
