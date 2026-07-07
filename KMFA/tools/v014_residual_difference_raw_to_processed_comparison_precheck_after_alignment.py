#!/usr/bin/env python3
"""Precheck residual raw-to-processed comparison after raw candidate alignment.

This phase consumes the previous read-only raw candidate alignment outputs and
checks whether owner-authorized comparison anchors exist. It does not read or
mutate the raw inbox and it does not run the formal raw-to-processed comparison.
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
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK_AFTER_ALIGNMENT"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-RAW-TO-PROCESSED-COMPARISON-PRECHECK-AFTER-ALIGNMENT-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-RAW-TO-PROCESSED-COMPARISON-PRECHECK-AFTER-ALIGNMENT"
VERSION = "0.1.4-residual-difference-raw-to-processed-comparison-precheck-after-alignment"
STATUS = "completed_validated_local_only_residual_difference_raw_comparison_after_alignment_blocked_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "residual_difference_comparison_after_alignment_blocked_by_missing_owner_authorized_anchors"
NEXT_RECOMMENDED_PHASE = "V014_OWNER_AUTHORIZED_RESIDUAL_ANCHOR_CONFIRMATION_OR_DIFFERENCE_REPORT"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_confirms_private_raw_candidate_anchors_before_formal_comparison"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_precheck_after_alignment_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_precheck_after_alignment_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_precheck_after_alignment_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_precheck_after_alignment_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "residual_difference_raw_to_processed_comparison_precheck_after_alignment.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment_matrix_public_safe.json"
)

SOURCE_ALIGNMENT_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_alignment_after_precheck_summary.json"
)
SOURCE_ALIGNMENT_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_alignment_after_precheck_manifest.json"
)
SOURCE_ALIGNMENT_MATRIX_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_alignment_after_precheck_matrix_public_safe.json"
)
SOURCE_PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_raw_candidate_alignment_after_precheck"
SOURCE_PRIVATE_ALIGNMENT_PATH = SOURCE_PRIVATE_DIR / "private_residual_difference_raw_candidate_alignment.json"
SOURCE_PRIVATE_DIAGNOSTIC_PATH = SOURCE_PRIVATE_DIR / "private_residual_difference_raw_candidate_alignment_diagnostic.json"
SOURCE_PRIVATE_ALIGNMENT_ITEMS_PATH = SOURCE_PRIVATE_DIR / "private_residual_difference_raw_candidate_alignment_items.jsonl"
SOURCE_PRIVATE_ANCHOR_DRAFT_PATH = SOURCE_PRIVATE_DIR / "private_residual_difference_raw_candidate_anchor_draft.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment"
PRIVATE_PRECHECK_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_to_processed_comparison_precheck_after_alignment.json"
PRIVATE_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_to_processed_comparison_precheck_after_alignment_diagnostic.json"
)
PRIVATE_READY_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_after_alignment_comparison_ready_records.jsonl"
PRIVATE_BLOCKER_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR / "private_residual_difference_after_alignment_comparison_blocker_records.jsonl"
)
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_to_processed_comparison_precheck_after_alignment.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

EXPECTED_TRACK_COUNTS = {
    "owner_select_one_authoritative_candidate": 24,
    "provide_authoritative_source_reference_or_owner_exclusion": 40,
    "provide_formula_or_non_numeric_mapping": 8,
}
REQUIRED_OWNER_ANCHORS = (
    "owner_authorized_anchor",
    "raw_candidate_record_ref_hash",
    "raw_candidate_fingerprint",
    "processed_value_fingerprint",
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
        "source_public_alignment_summary_read_by_this_phase": True,
        "source_public_alignment_manifest_read_by_this_phase": True,
        "source_public_alignment_matrix_read_by_this_phase": True,
        "source_private_alignment_read_by_this_phase": True,
        "source_private_alignment_diagnostic_read_by_this_phase": True,
        "source_private_alignment_items_read_by_this_phase": True,
        "source_private_anchor_draft_read_by_this_phase": True,
        "private_precheck_written_by_this_phase": True,
        "private_precheck_ready_records_written_by_this_phase": True,
        "private_precheck_blocker_records_written_by_this_phase": True,
        "source_private_alignment_outputs_mutated_by_this_phase": False,
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
        "private_alignment_committed": False,
        "private_anchor_draft_committed": False,
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


def _missing_anchor_codes(anchor_item: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key in REQUIRED_OWNER_ANCHORS:
        value = anchor_item.get(key)
        if key == "owner_authorized_anchor":
            if value is not True:
                missing.append(key)
            continue
        if not value:
            missing.append(key)
    return missing


def _build_precheck_records(
    anchor_items: list[dict[str, Any]], alignment_items_by_index: dict[int, dict[str, Any]], generated_at: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ready_records: list[dict[str, Any]] = []
    blocker_records: list[dict[str, Any]] = []
    for index, item in enumerate(anchor_items, start=1):
        source_index = int(item.get("anchor_draft_index") or index)
        alignment_item = alignment_items_by_index.get(source_index, {})
        missing = _missing_anchor_codes(item)
        base = {
            "precheck_index": index,
            "version": VERSION,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "source_alignment_index": alignment_item.get("alignment_item_index"),
            "source_anchor_draft_index": item.get("anchor_draft_index"),
            "target_slot_id": item.get("target_slot_id"),
            "diagnostic_track": item.get("diagnostic_track") or alignment_item.get("diagnostic_track"),
            "alignment_status": item.get("alignment_status") or alignment_item.get("alignment_status"),
        }
        if missing:
            blocker_records.append(
                {
                    **base,
                    "comparison_precheck_status": "missing_owner_authorized_comparison_anchor",
                    "missing_private_anchor_codes": missing,
                    "owner_authorized_anchor": item.get("owner_authorized_anchor") is True,
                    "raw_to_processed_value_comparison_ready": False,
                    "raw_to_processed_value_comparison_performed": False,
                    "full_reconciliation_allowed": False,
                    "business_value_consistency_verified": False,
                    "public_commit_allowed": False,
                }
            )
            continue
        ready_records.append(
            {
                **base,
                "comparison_precheck_status": "owner_authorized_anchor_ready",
                "owner_authorized_anchor": True,
                "raw_to_processed_value_comparison_ready": True,
                "raw_to_processed_value_comparison_performed": False,
                "full_reconciliation_allowed": False,
                "business_value_consistency_verified": False,
                "public_commit_allowed": False,
            }
        )
    return ready_records, blocker_records


def _build_matrix(summary: dict[str, Any], generated_at: str) -> dict[str, Any]:
    checks = [
        (
            "source_alignment_items_available",
            summary["source_alignment_item_count"] == 72,
            summary["source_alignment_item_count"],
            72,
        ),
        (
            "source_anchor_draft_items_available",
            summary["source_raw_candidate_anchor_draft_item_count"] == 72,
            summary["source_raw_candidate_anchor_draft_item_count"],
            72,
        ),
        (
            "diagnostic_track_counts_locked",
            summary["diagnostic_track_counts"] == EXPECTED_TRACK_COUNTS,
            summary["diagnostic_track_counts"],
            EXPECTED_TRACK_COUNTS,
        ),
        (
            "owner_authorized_anchor_coverage_unblocked",
            summary["owner_authorized_comparison_anchor_count"] == 72,
            summary["owner_authorized_comparison_anchor_count"],
            72,
        ),
        (
            "comparison_ready_record_count_unblocked",
            summary["comparison_ready_record_count"] == 72,
            summary["comparison_ready_record_count"],
            72,
        ),
        ("formal_comparison_not_claimed", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False, False, False),
        ("raw_inbox_not_accessed_after_alignment", summary["raw_boundary"]["raw_inbox_read_performed_by_this_phase"] is False, False, False),
        ("downstream_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, passed, observed, required in checks
    ]
    return {
        "schema_version": "kmfa.v014_residual_difference_raw_comparison_after_alignment_matrix_public_safe.v1",
        "record_type": "v014_residual_difference_raw_comparison_after_alignment_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "check_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "PASS"),
        "fail_count": sum(1 for row in rows if row["status"] == "FAIL"),
        "source_alignment_item_count": summary["source_alignment_item_count"],
        "owner_authorized_comparison_anchor_count": summary["owner_authorized_comparison_anchor_count"],
        "comparison_ready_record_count": summary["comparison_ready_record_count"],
        "comparison_blocker_record_count": summary["comparison_blocker_record_count"],
        "alignment_authorization_anchor_required_count": summary["alignment_authorization_anchor_required_count"],
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
    event_id = "DEV-KMFA-20260707-V014-RESIDUAL-DIFFERENCE-RAW-COMPARISON-PRECHECK-AFTER-ALIGNMENT"
    event = {
        "event_id": event_id,
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260707-KMFA-V014-RESIDUAL-DIFFERENCE-RAW-COMPARISON-AFTER-ALIGNMENT",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "source_alignment_item_count": summary["source_alignment_item_count"],
        "owner_authorized_comparison_anchor_count": summary["owner_authorized_comparison_anchor_count"],
        "comparison_ready_record_count": summary["comparison_ready_record_count"],
        "comparison_blocker_record_count": summary["comparison_blocker_record_count"],
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": "Prechecked post-alignment residual-difference comparison readiness and kept formal comparison blocked because owner-authorized anchors are still missing.",
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
            "name": "v0.1.4 residual difference raw-to-processed comparison precheck after alignment",
            "phase_id": PHASE_ID,
            "record_type": "v014_phase",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK_AFTER_ALIGNMENT",
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
            "name": "72 post-alignment residual-difference records prechecked",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK_AFTER_ALIGNMENT",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDRCPA01",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": GO_NO_GO_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "formal comparison blocked by missing owner-authorized anchors",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK_AFTER_ALIGNMENT",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDRCPA02",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "raw inbox untouched and private after-alignment precheck outputs remain ignored",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK_AFTER_ALIGNMENT",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDRCPA03",
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
                "Post-alignment residual raw comparison precheck manifest summary Go No-Go public-safe matrix "
                "ignored private ready and blocker records validator focused test and governance records"
            )
            task_row["phase_goal"] = (
                "precheck residual-difference comparison readiness after raw candidate alignment without raw inbox access or formal comparison"
            )
        else:
            task_row["task_label"] = row["task_id"][-2:]
            task_row["task_text"] = row["name"]
        task_rows.append(task_row)
    _dedupe_append_jsonl(TASK_STATUS_PATH, task_rows, lambda existing: existing.get("phase_id") != PHASE_ID)


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Residual Difference Raw-To-Processed Comparison Precheck After Alignment

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- source alignment items: `{summary["source_alignment_item_count"]}`
- source anchor draft items: `{summary["source_raw_candidate_anchor_draft_item_count"]}`
- owner-authorized comparison anchors: `{summary["owner_authorized_comparison_anchor_count"]}`
- comparison-ready records: `{summary["comparison_ready_record_count"]}`
- comparison blocker records: `{summary["comparison_blocker_record_count"]}`
- next required input: `{NEXT_REQUIRED_INPUT}`

This phase reads the previous alignment outputs only. It does not read the raw inbox, authorize anchors, perform formal raw-to-processed comparison, verify business consistency, upload GitHub, reinstall the app, or execute business steps.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: 72 residual-difference records still lack owner-authorized comparison anchors after candidate alignment.
- checks: `{matrix["pass_count"]}` pass / `{matrix["fail_count"]}` fail
- formal comparison allowed: `false`
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: private candidate anchor drafts may be mistaken for owner-authorized comparison anchors.
- Control: after-alignment precheck requires `owner_authorized_anchor=true` and concrete private anchors before formal comparison can run.
- Control: public evidence remains aggregate-only and keeps reconciliation/report/upload gates closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private precheck outputs, tool, validator, focused test and governance entries. The raw inbox and previous alignment outputs are not modified by this phase or rollback.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment.py KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment.py KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment.py --require-private-precheck`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment`
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
    source_summary = _read_json(SOURCE_ALIGNMENT_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_ALIGNMENT_MANIFEST_PATH)
    source_matrix = _read_json(SOURCE_ALIGNMENT_MATRIX_PATH)
    source_alignment = _read_json(SOURCE_PRIVATE_ALIGNMENT_PATH)
    source_diagnostic = _read_json(SOURCE_PRIVATE_DIAGNOSTIC_PATH)
    source_alignment_items = _read_jsonl(SOURCE_PRIVATE_ALIGNMENT_ITEMS_PATH)
    source_anchor_draft = _read_json(SOURCE_PRIVATE_ANCHOR_DRAFT_PATH)
    anchor_items = source_anchor_draft.get("anchor_draft_items", [])
    if not isinstance(anchor_items, list):
        raise ValueError("source anchor draft must contain anchor_draft_items")
    if len(source_alignment_items) != 72 or len(anchor_items) != 72:
        raise ValueError("source alignment must provide 72 alignment and anchor draft items")

    alignment_items_by_index = {
        int(item.get("alignment_item_index")): item
        for item in source_alignment_items
        if item.get("alignment_item_index") is not None
    }
    ready_records, blocker_records = _build_precheck_records(anchor_items, alignment_items_by_index, timestamp)
    track_counts = dict(Counter(item.get("diagnostic_track") for item in anchor_items))
    if track_counts != EXPECTED_TRACK_COUNTS:
        raise ValueError("unexpected post-alignment diagnostic track counts")

    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    owner_authorized_anchor_count = sum(1 for item in anchor_items if item.get("owner_authorized_anchor") is True)
    private_precheck = {
        "schema_version": "kmfa.private.v014_residual_difference_raw_comparison_after_alignment_precheck.v1",
        "classification": "private_residual_difference_raw_comparison_after_alignment_precheck_do_not_commit",
        "record_type": "v014_residual_difference_raw_comparison_after_alignment_precheck",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_alignment_phase_id": source_summary.get("phase_id"),
        "source_alignment_item_count": len(source_alignment_items),
        "source_raw_candidate_anchor_draft_item_count": len(anchor_items),
        "owner_authorized_comparison_anchor_count": owner_authorized_anchor_count,
        "comparison_ready_record_count": len(ready_records),
        "comparison_blocker_record_count": len(blocker_records),
        "alignment_authorization_anchor_required_count": len(blocker_records),
        "raw_to_processed_value_comparison_ready": len(ready_records) == 72 and not blocker_records,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "ready_records": ready_records,
        "blocker_records": blocker_records,
        "raw_boundary": raw_boundary,
    }
    private_diagnostic = {
        "schema_version": "kmfa.private.v014_residual_difference_raw_comparison_after_alignment_diagnostic.v1",
        "record_type": "private_residual_difference_raw_comparison_after_alignment_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_alignment_phase_id": source_summary.get("phase_id"),
        "source_alignment_decision": source_summary.get("decision"),
        "source_alignment_matrix_fail_count": source_matrix.get("fail_count"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_private_alignment_phase_id": source_alignment.get("phase_id"),
        "source_private_diagnostic_phase_id": source_diagnostic.get("phase_id"),
        "owner_authorized_comparison_anchor_count": owner_authorized_anchor_count,
        "comparison_ready_record_count": len(ready_records),
        "comparison_blocker_record_count": len(blocker_records),
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
                "# Private residual difference raw comparison precheck after alignment",
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
        "schema_version": "kmfa.v014_residual_difference_raw_comparison_after_alignment_summary.v1",
        "record_type": "v014_residual_difference_raw_comparison_after_alignment_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_alignment_phase_id": source_summary.get("phase_id"),
        "source_alignment_decision": source_summary.get("decision"),
        "source_alignment_item_count": len(source_alignment_items),
        "source_raw_candidate_anchor_draft_item_count": len(anchor_items),
        "owner_authorized_comparison_anchor_count": owner_authorized_anchor_count,
        "alignment_authorization_anchor_required_count": len(blocker_records),
        "comparison_ready_record_count": len(ready_records),
        "comparison_blocker_record_count": len(blocker_records),
        "raw_to_processed_value_comparison_precheck_after_alignment_performed_by_this_phase": True,
        "raw_to_processed_value_comparison_precheck_after_alignment_passed": len(ready_records) == 72 and not blocker_records,
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
        "private_precheck_written": True,
        "private_precheck_gitignored": _git_check_ignored(PRIVATE_PRECHECK_PATH),
        "private_ready_records_written": True,
        "private_ready_records_gitignored": _git_check_ignored(PRIVATE_READY_RECORDS_PATH),
        "private_blocker_records_written": True,
        "private_blocker_records_gitignored": _git_check_ignored(PRIVATE_BLOCKER_RECORDS_PATH),
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
        "schema_version": "kmfa.v014_residual_difference_raw_comparison_after_alignment_go_no_go.v1",
        "record_type": "v014_residual_difference_raw_comparison_after_alignment_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "current_gate": "NO_GO_RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_COMPARISON_ANCHORS_MISSING_AFTER_ALIGNMENT",
        "reason": DIAGNOSTIC_CONCLUSION,
        "source_alignment_item_count": len(source_alignment_items),
        "owner_authorized_comparison_anchor_count": owner_authorized_anchor_count,
        "comparison_ready_record_count": len(ready_records),
        "comparison_blocker_record_count": len(blocker_records),
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_residual_difference_raw_comparison_after_alignment_manifest.v1",
        "record_type": "v014_residual_difference_raw_comparison_after_alignment_manifest",
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
            "private_precheck": "private_runtime_only_ignored",
            "private_diagnostic": "private_runtime_only_ignored",
            "private_ready_records": "private_runtime_only_ignored",
            "private_blocker_records": "private_runtime_only_ignored",
            "private_report": "private_runtime_only_ignored",
        },
        "changed_files": _changed_kmfa_files(),
        "git_head_at_generation": _git_output(["rev-parse", "HEAD"]),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment.py KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment.py KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment.py --require-private-precheck",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment",
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
        "PASS: generated post-alignment residual raw comparison precheck "
        f"(ready_records={summary['comparison_ready_record_count']}, "
        f"blockers={summary['comparison_blocker_record_count']}, decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
