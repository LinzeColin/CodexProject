#!/usr/bin/env python3
"""Build owner-authorized anchor confirmation readiness for residual differences.

This phase consumes the previous post-alignment comparison precheck outputs and
checks whether owner-authorized private anchors are ready for confirmation. It
does not read or mutate the raw inbox and it does not run the formal
raw-to-processed comparison.
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
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_READINESS"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-READINESS-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-READINESS"
VERSION = "0.1.4-residual-difference-owner-authorized-anchor-confirmation-readiness"
STATUS = "completed_validated_local_only_owner_authorized_anchor_confirmation_readiness_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "owner_authorized_anchor_confirmation_blocked_by_missing_private_authorized_anchors"
NEXT_RECOMMENDED_PHASE = "V014_RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_OR_DIFFERENCE_REPORT"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_confirms_private_raw_candidate_anchors_before_formal_comparison"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_readiness_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_readiness_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_readiness_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_readiness_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "residual_difference_owner_authorized_anchor_confirmation_readiness.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_readiness_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_readiness_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_readiness_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_readiness_matrix_public_safe.json"
)

SOURCE_AFTER_ALIGNMENT_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment_summary.json"
)
SOURCE_AFTER_ALIGNMENT_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment_manifest.json"
)
SOURCE_AFTER_ALIGNMENT_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment_matrix_public_safe.json"
)
SOURCE_PRIVATE_AFTER_ALIGNMENT_BLOCKERS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_raw_to_processed_comparison_precheck_after_alignment/private_residual_difference_after_alignment_comparison_blocker_records.jsonl"
)
SOURCE_PRIVATE_ALIGNMENT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_raw_candidate_alignment_after_precheck/private_residual_difference_raw_candidate_alignment.json"
)
SOURCE_PRIVATE_ANCHOR_DRAFT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_raw_candidate_alignment_after_precheck/private_residual_difference_raw_candidate_anchor_draft.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_owner_authorized_anchor_confirmation_readiness"
PRIVATE_READINESS_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_readiness.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_readiness_diagnostic.json"
PRIVATE_READY_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_ready_queue.jsonl"
PRIVATE_BLOCKER_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_blocker_queue.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_readiness.md"

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
        "source_public_after_alignment_summary_read_by_this_phase": True,
        "source_public_after_alignment_manifest_read_by_this_phase": True,
        "source_public_after_alignment_matrix_read_by_this_phase": True,
        "source_private_after_alignment_blockers_read_by_this_phase": True,
        "source_private_alignment_read_by_this_phase": True,
        "source_private_anchor_draft_read_by_this_phase": True,
        "private_readiness_written_by_this_phase": True,
        "private_ready_queue_written_by_this_phase": True,
        "private_blocker_queue_written_by_this_phase": True,
        "source_private_anchor_draft_mutated_by_this_phase": False,
        "source_private_after_alignment_outputs_mutated_by_this_phase": False,
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
        "private_readiness_committed": False,
        "private_ready_queue_committed": False,
        "private_blocker_queue_committed": False,
        "private_diagnostic_committed": False,
        "private_report_committed": False,
        "private_source_anchor_draft_committed": False,
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


def _item_readiness(item: dict[str, Any]) -> tuple[bool, list[str]]:
    missing: list[str] = []
    if item.get("owner_authorized_anchor") is not True:
        missing.append("owner_authorized_anchor")
    if not item.get("processed_value_fingerprint"):
        missing.append("processed_value_fingerprint")
    if not item.get("raw_candidate_record_ref_hash"):
        missing.append("raw_candidate_record_ref_hash")
    if not item.get("raw_candidate_fingerprint"):
        missing.append("raw_candidate_fingerprint")
    return not missing, missing


def _build_readiness_queues(anchor_items: list[dict[str, Any]], blockers: list[dict[str, Any]], generated_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blocker_by_anchor_index = {
        int(row.get("source_anchor_draft_index")): row
        for row in blockers
        if row.get("source_anchor_draft_index") is not None
    }
    ready_queue: list[dict[str, Any]] = []
    blocker_queue: list[dict[str, Any]] = []
    for index, item in enumerate(anchor_items, start=1):
        source_index = int(item.get("anchor_draft_index") or index)
        precheck_blocker = blocker_by_anchor_index.get(source_index, {})
        ready, missing = _item_readiness(item)
        base = {
            "readiness_index": index,
            "version": VERSION,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "source_anchor_draft_index": source_index,
            "source_after_alignment_precheck_index": precheck_blocker.get("precheck_index"),
            "target_slot_id": item.get("target_slot_id") or precheck_blocker.get("target_slot_id"),
            "diagnostic_track": item.get("diagnostic_track") or precheck_blocker.get("diagnostic_track"),
            "alignment_status": item.get("alignment_status") or precheck_blocker.get("alignment_status"),
            "private_candidate_sample_available": bool((item.get("private_top_candidate_record_count") or 0) > 0),
            "private_top_candidate_record_count": int(item.get("private_top_candidate_record_count") or 0),
        }
        if ready:
            ready_queue.append(
                {
                    **base,
                    "owner_authorized_anchor_confirmation_status": "ready_for_owner_authorized_anchor_confirmation",
                    "anchor_confirmation_ready": True,
                    "raw_to_processed_value_comparison_ready": True,
                    "raw_to_processed_value_comparison_performed": False,
                    "business_value_consistency_verified": False,
                    "public_commit_allowed": False,
                }
            )
            continue
        blocker_queue.append(
            {
                **base,
                "owner_authorized_anchor_confirmation_status": "blocked_missing_owner_authorized_anchor_inputs",
                "missing_private_anchor_codes": missing,
                "anchor_confirmation_ready": False,
                "raw_to_processed_value_comparison_ready": False,
                "raw_to_processed_value_comparison_performed": False,
                "business_value_consistency_verified": False,
                "public_commit_allowed": False,
            }
        )
    return ready_queue, blocker_queue


def _build_matrix(summary: dict[str, Any], generated_at: str) -> dict[str, Any]:
    checks = [
        (
            "source_after_alignment_blockers_available",
            summary["source_after_alignment_blocker_count"] == 72,
            summary["source_after_alignment_blocker_count"],
            72,
        ),
        (
            "source_anchor_draft_items_available",
            summary["source_anchor_draft_item_count"] == 72,
            summary["source_anchor_draft_item_count"],
            72,
        ),
        (
            "diagnostic_track_counts_locked",
            summary["diagnostic_track_counts"] == EXPECTED_TRACK_COUNTS,
            summary["diagnostic_track_counts"],
            EXPECTED_TRACK_COUNTS,
        ),
        (
            "owner_authorized_anchor_confirmation_unblocked",
            summary["owner_authorized_anchor_ready_count"] == 72,
            summary["owner_authorized_anchor_ready_count"],
            72,
        ),
        (
            "processed_value_fingerprints_available",
            summary["missing_processed_value_fingerprint_count"] == 0,
            summary["missing_processed_value_fingerprint_count"],
            0,
        ),
        (
            "raw_candidate_anchors_available",
            summary["missing_raw_candidate_anchor_count"] == 0,
            summary["missing_raw_candidate_anchor_count"],
            0,
        ),
        ("formal_comparison_not_claimed", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False, False, False),
        ("raw_inbox_not_accessed", summary["raw_boundary"]["raw_inbox_read_performed_by_this_phase"] is False, False, False),
        ("downstream_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, passed, observed, required in checks
    ]
    return {
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_readiness_matrix_public_safe.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_readiness_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "check_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "PASS"),
        "fail_count": sum(1 for row in rows if row["status"] == "FAIL"),
        "source_after_alignment_blocker_count": summary["source_after_alignment_blocker_count"],
        "source_anchor_draft_item_count": summary["source_anchor_draft_item_count"],
        "owner_authorized_anchor_ready_count": summary["owner_authorized_anchor_ready_count"],
        "owner_authorized_anchor_blocker_count": summary["owner_authorized_anchor_blocker_count"],
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
    event_id = "DEV-KMFA-20260707-V014-RESIDUAL-DIFFERENCE-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-READINESS"
    event = {
        "event_id": event_id,
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260707-KMFA-V014-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-READINESS",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "source_after_alignment_blocker_count": summary["source_after_alignment_blocker_count"],
        "source_anchor_draft_item_count": summary["source_anchor_draft_item_count"],
        "owner_authorized_anchor_ready_count": summary["owner_authorized_anchor_ready_count"],
        "owner_authorized_anchor_blocker_count": summary["owner_authorized_anchor_blocker_count"],
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": (
            "Checked owner-authorized residual-difference anchor confirmation readiness and kept formal "
            "raw-to-processed comparison blocked because 72 private anchors remain unauthorized/incomplete."
        ),
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
            "name": "v0.1.4 residual difference owner-authorized anchor confirmation readiness",
            "phase_id": PHASE_ID,
            "record_type": "v014_phase",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_READINESS",
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
            "name": "72 post-alignment residual-difference anchor drafts checked",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_READINESS",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OACR01",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": GO_NO_GO_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "owner-authorized anchor confirmation blocked by missing private anchors",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_READINESS",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OACR02",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "raw inbox untouched and private readiness queues remain ignored",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_READINESS",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OACR03",
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
                "Owner-authorized anchor confirmation readiness manifest summary Go No-Go public-safe "
                "matrix ignored private ready/blocker queues validator focused test and governance records"
            )
            task_row["phase_goal"] = (
                "check whether residual-difference private anchors are ready for owner-authorized confirmation "
                "without raw inbox access or formal comparison"
            )
        else:
            task_row["task_label"] = row["task_id"][-2:]
            task_row["task_text"] = row["name"]
        task_rows.append(task_row)
    _dedupe_append_jsonl(TASK_STATUS_PATH, task_rows, lambda existing: existing.get("phase_id") != PHASE_ID)


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Residual Difference Owner-Authorized Anchor Confirmation Readiness

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- source after-alignment blockers: `{summary["source_after_alignment_blocker_count"]}`
- source anchor draft items: `{summary["source_anchor_draft_item_count"]}`
- owner-authorized anchor ready records: `{summary["owner_authorized_anchor_ready_count"]}`
- owner-authorized anchor blocker records: `{summary["owner_authorized_anchor_blocker_count"]}`
- candidate sample items: `{summary["private_candidate_sample_item_count"]}`
- candidate missing sample items: `{summary["private_candidate_missing_sample_item_count"]}`
- next required input: `{NEXT_REQUIRED_INPUT}`

This phase reads previous public-safe artifacts and ignored private anchor draft/precheck queues only. It does not read the raw inbox, authorize anchors, perform formal raw-to-processed comparison, verify business consistency, upload GitHub, reinstall the app, or execute business steps.
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

- Risk: candidate anchor drafts may be mistaken for owner-authorized confirmation records.
- Control: readiness requires owner authorization plus processed and raw candidate private anchors before downstream comparison can run.
- Control: public evidence remains aggregate-only and keeps reconciliation/report/upload gates closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private readiness outputs, tool, validator, focused test and governance entries. The raw inbox and previous alignment/precheck outputs are not modified by this phase or rollback.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_readiness.py KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_readiness.py KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_readiness.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_readiness.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_readiness.py --require-private-readiness`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_owner_authorized_anchor_confirmation_readiness`
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
    source_summary = _read_json(SOURCE_AFTER_ALIGNMENT_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_AFTER_ALIGNMENT_MANIFEST_PATH)
    source_matrix = _read_json(SOURCE_AFTER_ALIGNMENT_MATRIX_PATH)
    source_blockers = _read_jsonl(SOURCE_PRIVATE_AFTER_ALIGNMENT_BLOCKERS_PATH)
    source_alignment = _read_json(SOURCE_PRIVATE_ALIGNMENT_PATH)
    source_anchor_draft = _read_json(SOURCE_PRIVATE_ANCHOR_DRAFT_PATH)
    anchor_items = source_anchor_draft.get("anchor_draft_items", [])
    if not isinstance(anchor_items, list):
        raise ValueError("source anchor draft must contain anchor_draft_items")
    if len(source_blockers) != 72 or len(anchor_items) != 72:
        raise ValueError("source readiness inputs must provide 72 blockers and 72 anchor draft items")

    ready_queue, blocker_queue = _build_readiness_queues(anchor_items, source_blockers, timestamp)
    track_counts = dict(Counter(item.get("diagnostic_track") for item in anchor_items))
    if track_counts != EXPECTED_TRACK_COUNTS:
        raise ValueError("unexpected diagnostic track counts")

    missing_owner_authorized_anchor_count = sum(1 for item in anchor_items if item.get("owner_authorized_anchor") is not True)
    missing_processed_value_fingerprint_count = sum(1 for item in anchor_items if not item.get("processed_value_fingerprint"))
    missing_raw_candidate_anchor_count = sum(
        1 for item in anchor_items if not item.get("raw_candidate_record_ref_hash") or not item.get("raw_candidate_fingerprint")
    )
    private_candidate_sample_item_count = sum(1 for item in anchor_items if (item.get("private_top_candidate_record_count") or 0) > 0)
    private_candidate_missing_sample_item_count = len(anchor_items) - private_candidate_sample_item_count

    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    private_readiness = {
        "schema_version": "kmfa.private.v014_owner_authorized_anchor_confirmation_readiness.v1",
        "classification": "private_owner_authorized_anchor_confirmation_readiness_do_not_commit",
        "record_type": "v014_owner_authorized_anchor_confirmation_readiness",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_after_alignment_phase_id": source_summary.get("phase_id"),
        "source_after_alignment_blocker_count": len(source_blockers),
        "source_anchor_draft_item_count": len(anchor_items),
        "owner_authorized_anchor_ready_count": len(ready_queue),
        "owner_authorized_anchor_blocker_count": len(blocker_queue),
        "missing_owner_authorized_anchor_count": missing_owner_authorized_anchor_count,
        "missing_processed_value_fingerprint_count": missing_processed_value_fingerprint_count,
        "missing_raw_candidate_anchor_count": missing_raw_candidate_anchor_count,
        "anchor_confirmation_ready": len(ready_queue) == 72 and not blocker_queue,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "ready_queue": ready_queue,
        "blocker_queue": blocker_queue,
        "raw_boundary": raw_boundary,
    }
    private_diagnostic = {
        "schema_version": "kmfa.private.v014_owner_authorized_anchor_confirmation_readiness_diagnostic.v1",
        "record_type": "private_owner_authorized_anchor_confirmation_readiness_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_after_alignment_phase_id": source_summary.get("phase_id"),
        "source_after_alignment_decision": source_summary.get("decision"),
        "source_after_alignment_manifest_phase_id": source_manifest.get("phase_id"),
        "source_after_alignment_matrix_fail_count": source_matrix.get("fail_count"),
        "source_private_alignment_phase_id": source_alignment.get("phase_id"),
        "owner_authorized_anchor_ready_count": len(ready_queue),
        "owner_authorized_anchor_blocker_count": len(blocker_queue),
        "private_candidate_sample_item_count": private_candidate_sample_item_count,
        "private_candidate_missing_sample_item_count": private_candidate_missing_sample_item_count,
        "diagnostic_track_counts": track_counts,
        "raw_inbox_accessed": False,
        "raw_inbox_mutated": False,
    }

    _write_json(PRIVATE_READINESS_PATH, private_readiness)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_jsonl(PRIVATE_READY_QUEUE_PATH, ready_queue)
    _write_jsonl(PRIVATE_BLOCKER_QUEUE_PATH, blocker_queue)
    _write_text(
        PRIVATE_REPORT_PATH,
        "\n".join(
            [
                "# Private owner-authorized anchor confirmation readiness",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- owner_authorized_anchor_ready_count: `{len(ready_queue)}`",
                f"- owner_authorized_anchor_blocker_count: `{len(blocker_queue)}`",
                "- formal raw-to-processed comparison was not performed.",
                "- raw inbox access and mutation were not performed.",
            ]
        )
        + "\n",
    )

    summary = {
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_readiness_summary.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_readiness_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_after_alignment_phase_id": source_summary.get("phase_id"),
        "source_after_alignment_decision": source_summary.get("decision"),
        "source_after_alignment_blocker_count": len(source_blockers),
        "source_anchor_draft_item_count": len(anchor_items),
        "owner_authorized_anchor_ready_count": len(ready_queue),
        "owner_authorized_anchor_blocker_count": len(blocker_queue),
        "missing_owner_authorized_anchor_count": missing_owner_authorized_anchor_count,
        "missing_processed_value_fingerprint_count": missing_processed_value_fingerprint_count,
        "missing_raw_candidate_anchor_count": missing_raw_candidate_anchor_count,
        "anchor_confirmation_ready": False,
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
        "private_candidate_sample_item_count": private_candidate_sample_item_count,
        "private_candidate_missing_sample_item_count": private_candidate_missing_sample_item_count,
        "private_readiness_written": True,
        "private_readiness_gitignored": _git_check_ignored(PRIVATE_READINESS_PATH),
        "private_ready_queue_written": True,
        "private_ready_queue_gitignored": _git_check_ignored(PRIVATE_READY_QUEUE_PATH),
        "private_blocker_queue_written": True,
        "private_blocker_queue_gitignored": _git_check_ignored(PRIVATE_BLOCKER_QUEUE_PATH),
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
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_readiness_go_no_go.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_readiness_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "current_gate": "NO_GO_RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_NOT_READY",
        "reason": DIAGNOSTIC_CONCLUSION,
        "source_after_alignment_blocker_count": len(source_blockers),
        "source_anchor_draft_item_count": len(anchor_items),
        "owner_authorized_anchor_ready_count": len(ready_queue),
        "owner_authorized_anchor_blocker_count": len(blocker_queue),
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
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_readiness_manifest.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_readiness_manifest",
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
            "private_readiness": "private_runtime_only_ignored",
            "private_diagnostic": "private_runtime_only_ignored",
            "private_ready_queue": "private_runtime_only_ignored",
            "private_blocker_queue": "private_runtime_only_ignored",
            "private_report": "private_runtime_only_ignored",
        },
        "changed_files": _changed_kmfa_files(),
        "git_head_at_generation": _git_output(["rev-parse", "HEAD"]),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_readiness.py KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_readiness.py KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_readiness.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_readiness.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_readiness.py --require-private-readiness",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_owner_authorized_anchor_confirmation_readiness",
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
        "PASS: generated owner-authorized anchor confirmation readiness "
        f"(ready={summary['owner_authorized_anchor_ready_count']}, "
        f"blockers={summary['owner_authorized_anchor_blocker_count']}, decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
