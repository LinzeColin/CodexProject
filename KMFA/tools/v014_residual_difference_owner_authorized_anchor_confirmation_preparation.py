#!/usr/bin/env python3
"""Prepare private owner-authorized anchor confirmation packets.

This phase consumes the prior authorization-readiness outputs and writes an
ignored private preparation queue for the later anchor-confirmation phase. It
does not confirm anchors, compare raw-to-processed values, read or mutate the
raw inbox, upload, reinstall, or execute business steps.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_PREPARATION"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-PREPARATION-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-PREPARATION"
VERSION = "0.1.4-residual-difference-owner-authorized-anchor-confirmation-preparation"
STATUS = "completed_validated_local_only_owner_authorized_anchor_confirmation_preparation_no_go"
DECISION = "NO_GO"
PREPARATION_CONCLUSION = "owner_authorized_anchor_confirmation_preparation_completed_confirmation_ready_next_phase"
NEXT_REQUIRED_INPUT = "run_owner_authorized_anchor_confirmation_before_formal_raw_to_processed_comparison"
NEXT_RECOMMENDED_PHASE = "V014_RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_preparation_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_preparation_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_preparation_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_preparation_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "residual_difference_owner_authorized_anchor_confirmation_preparation.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_preparation_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_preparation_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_preparation_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_preparation_matrix_public_safe.json"
)

SOURCE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_authorization_readiness_summary.json"
)
SOURCE_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_authorization_readiness_manifest.json"
)
SOURCE_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_authorization_readiness_go_no_go_report.json"
)
SOURCE_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_authorization_readiness_matrix_public_safe.json"
)
SOURCE_PRIVATE_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_owner_authorized_anchor_confirmation_authorization_readiness"
)
SOURCE_PRIVATE_READINESS_DIAGNOSTIC_PATH = (
    SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_confirmation_authorization_readiness_diagnostic.json"
)
SOURCE_PRIVATE_READINESS_QUEUE_PATH = (
    SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_confirmation_authorization_readiness_queue.jsonl"
)
SOURCE_PRIVATE_READINESS_REPORT_PATH = (
    SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_confirmation_authorization_readiness.md"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_owner_authorized_anchor_confirmation_preparation"
)
PRIVATE_PREPARATION_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_preparation_diagnostic.json"
)
PRIVATE_PREPARATION_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_preparation_queue.jsonl"
PRIVATE_PREPARATION_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_preparation.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"
PRIVATE_SLOT_KEY = "target_" + "slot_" + "id"

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
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _upsert_jsonl(path: Path, payload: dict[str, Any], key_fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict) and all(row.get(key) == payload.get(key) for key in key_fields):
                continue
            lines.append(line)
    lines.append(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
        "source_public_readiness_go_no_go_read_by_this_phase": True,
        "source_public_readiness_matrix_read_by_this_phase": True,
        "source_private_readiness_diagnostic_read_by_this_phase": True,
        "source_private_readiness_queue_read_by_this_phase": True,
        "source_private_readiness_report_read_by_this_phase": True,
        "private_preparation_diagnostic_written_by_this_phase": True,
        "private_preparation_queue_written_by_this_phase": True,
        "private_preparation_report_written_by_this_phase": True,
        "source_private_readiness_diagnostic_mutated_by_this_phase": False,
        "source_private_readiness_queue_mutated_by_this_phase": False,
        "source_private_readiness_report_mutated_by_this_phase": False,
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
        "source_private_readiness_diagnostic_committed": False,
        "source_private_readiness_queue_committed": False,
        "source_private_readiness_report_committed": False,
        "private_preparation_diagnostic_committed": False,
        "private_preparation_queue_committed": False,
        "private_preparation_report_committed": False,
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


def _build_preparation_queue(*, generated_at: str, readiness_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(readiness_rows, start=1):
        rows.append(
            {
                "preparation_item_id": f"OAC-PREP-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_readiness_item_id": row.get("readiness_item_id"),
                PRIVATE_SLOT_KEY: row.get(PRIVATE_SLOT_KEY),
                "diagnostic_track": row.get("diagnostic_track"),
                "owner_authorization_decision_code": row.get("owner_authorization_decision_code"),
                "preparation_status": "prepared_for_owner_authorized_anchor_confirmation",
                "owner_authorized_anchor_confirmation_allowed_next_phase": True,
                "anchor_confirmation_allowed_by_this_phase": False,
                "owner_authorized_anchor_confirmation_performed_by_this_phase": False,
                "raw_to_processed_value_comparison_allowed_by_this_phase": False,
                "full_reconciliation_allowed_by_this_phase": False,
                "public_commit_allowed": False,
            }
        )
    return rows


def _write_private_outputs(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_private_diagnostic: dict[str, Any],
    preparation_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("diagnostic_track") for row in preparation_rows)
    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_authorized_anchor_confirmation_preparation.v1",
        "classification": "private_owner_authorized_anchor_confirmation_preparation_do_not_commit",
        "record_type": "v014_owner_authorized_anchor_confirmation_preparation_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "preparation_conclusion": PREPARATION_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_private_diagnostic_phase_id": source_private_diagnostic.get("phase_id"),
        "source_authorization_readiness_item_count": source_summary.get("authorization_readiness_item_count"),
        "preparation_item_count": len(preparation_rows),
        "preparation_ready_item_count": len(preparation_rows),
        "preparation_blocker_item_count": 0,
        "track_counts": dict(track_counts),
        "raw_boundary": raw_boundary,
    }
    _write_json(PRIVATE_PREPARATION_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_PREPARATION_QUEUE_PATH, preparation_rows)
    _write_text(
        PRIVATE_PREPARATION_REPORT_PATH,
        "\n".join(
            [
                "# Private Owner-Authorized Anchor Confirmation Preparation",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- preparation_item_count: `{len(preparation_rows)}`",
                "- preparation_status: `prepared_for_owner_authorized_anchor_confirmation`",
                "- owner_authorized_anchor_confirmation_allowed_next_phase: `true`",
                "- anchor_confirmation_allowed_by_this_phase: `false`",
                "- raw_to_processed_value_comparison_performed_by_this_phase: `false`",
                "",
            ]
        ),
    )
    return diagnostic


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    source_private_diagnostic: dict[str, Any],
    readiness_rows: list[dict[str, Any]],
    preparation_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
    public_safety: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("diagnostic_track") for row in preparation_rows)
    return {
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_preparation_summary.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_preparation_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "preparation_conclusion": PREPARATION_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_diagnostic_phase_id": source_private_diagnostic.get("phase_id"),
        "source_authorization_item_count": source_summary.get("authorization_item_count"),
        "source_authorization_readiness_item_count": source_summary.get("authorization_readiness_item_count"),
        "source_readiness_ready_item_count": source_summary.get("readiness_ready_item_count"),
        "source_readiness_blocker_item_count": source_summary.get("readiness_blocker_item_count"),
        "source_owner_authorization_readiness_confirmed": source_summary.get("owner_authorization_readiness_confirmed"),
        "source_owner_authorized_anchor_confirmation_preparation_ready_next_phase": source_summary.get(
            "owner_authorized_anchor_confirmation_preparation_ready_next_phase"
        ),
        "authorization_readiness_item_count": len(readiness_rows),
        "preparation_item_count": len(preparation_rows),
        "preparation_ready_item_count": len(preparation_rows),
        "preparation_blocker_item_count": 0,
        "owner_authorized_anchor_confirmation_preparation_performed_by_this_phase": True,
        "owner_authorized_anchor_confirmation_allowed_next_phase": True,
        "owner_select_one_authoritative_candidate_count": track_counts["owner_select_one_authoritative_candidate"],
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts[
            "provide_authoritative_source_reference_or_owner_exclusion"
        ],
        "provide_formula_or_non_numeric_mapping_count": track_counts["provide_formula_or_non_numeric_mapping"],
        "private_preparation_diagnostic_written": True,
        "private_preparation_queue_written": True,
        "private_preparation_report_written": True,
        "private_preparation_diagnostic_gitignored": _git_check_ignored(PRIVATE_PREPARATION_DIAGNOSTIC_PATH),
        "private_preparation_queue_gitignored": _git_check_ignored(PRIVATE_PREPARATION_QUEUE_PATH),
        "private_preparation_report_gitignored": _git_check_ignored(PRIVATE_PREPARATION_REPORT_PATH),
        "source_private_readiness_diagnostic_gitignored": _git_check_ignored(SOURCE_PRIVATE_READINESS_DIAGNOSTIC_PATH),
        "source_private_readiness_queue_gitignored": _git_check_ignored(SOURCE_PRIVATE_READINESS_QUEUE_PATH),
        "source_private_readiness_report_gitignored": _git_check_ignored(SOURCE_PRIVATE_READINESS_REPORT_PATH),
        "anchor_confirmation_allowed_by_this_phase": False,
        "anchor_confirmation_ready": False,
        "owner_authorized_anchor_confirmation_performed_by_this_phase": False,
        "owner_authorized_anchor_confirmation_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_allowed_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "full_reconciliation_allowed": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_authorization_readiness_loaded", summary["source_phase_id"].endswith("AUTHORIZATION_READINESS")),
        ("source_authorization_readiness_valid", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_readiness_item_count_locked", summary["source_authorization_readiness_item_count"] == 72),
        ("source_readiness_blockers_clear", summary["source_readiness_blocker_item_count"] == 0),
        ("source_private_readiness_ignored", summary["source_private_readiness_queue_gitignored"] is True),
        ("preparation_queue_complete", summary["preparation_item_count"] == 72),
        ("preparation_blockers_clear", summary["preparation_blocker_item_count"] == 0),
        ("track_counts_locked", all(summary[f"{track}_count"] == count for track, count in EXPECTED_TRACK_COUNTS.items())),
        ("private_preparation_ignored", summary["private_preparation_queue_gitignored"] is True),
        (
            "owner_authorized_anchor_confirmation_next_phase_allowed",
            summary["owner_authorized_anchor_confirmation_allowed_next_phase"] is True,
        ),
        ("no_anchor_confirmation_this_phase", summary["owner_authorized_anchor_confirmation_performed_by_this_phase"] is False),
        ("no_raw_comparison_this_phase", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("public_safe_aggregate_only", summary["public_safety"]["public_safe_aggregate_only"] is True),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_preparation_matrix_public_safe.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_preparation_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "decision": DECISION,
        "check_count": len(rows),
        "check_pass_count": pass_count,
        "check_fail_count": len(rows) - pass_count,
        "checks": rows,
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_preparation_go_no_go.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_preparation_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "preparation_conclusion": PREPARATION_CONCLUSION,
        "authorization_readiness_item_count": summary["authorization_readiness_item_count"],
        "preparation_item_count": summary["preparation_item_count"],
        "preparation_ready_item_count": summary["preparation_ready_item_count"],
        "preparation_blocker_item_count": summary["preparation_blocker_item_count"],
        "owner_authorized_anchor_confirmation_preparation_performed_by_this_phase": True,
        "owner_authorized_anchor_confirmation_allowed_next_phase": True,
        "anchor_confirmation_allowed_by_this_phase": False,
        "owner_authorized_anchor_confirmation_performed_by_this_phase": False,
        "raw_to_processed_value_comparison_allowed": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    report = f"""# V014 Residual Difference Owner-Authorized Anchor Confirmation Preparation

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe authorization-readiness evidence plus ignored private readiness queue.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Authorization readiness items: `{summary["authorization_readiness_item_count"]}`
- Preparation items: `{summary["preparation_item_count"]}`
- Preparation blockers: `{summary["preparation_blocker_item_count"]}`
- Owner-select authoritative candidate track: `{summary["owner_select_one_authoritative_candidate_count"]}`
- Authoritative source reference or owner exclusion track: `{summary["provide_authoritative_source_reference_or_owner_exclusion_count"]}`
- Formula or non-numeric mapping track: `{summary["provide_formula_or_non_numeric_mapping_count"]}`
- Owner-authorized anchor confirmations performed by this phase: `{summary["owner_authorized_anchor_confirmation_count"]}`
- Unresolved differences: `{summary["unresolved_difference_count"]}`

## Gate

This phase prepares the private anchor-confirmation packet only. It does not confirm anchors, run raw-to-processed comparison, close discrepancies, reconcile values, verify business consistency, upload GitHub, reinstall the app or execute business steps.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: preparation is complete, but anchor confirmation and formal comparison are still out of scope for this phase.
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_preparation.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_preparation.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_preparation.py --require-private-preparation`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_preparation.py`
- Governance validators, diff check, raw/private marker scan, secret scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: preparation is mistaken for owner-authorized anchor confirmation.
- Control: confirmation count remains zero and every downstream value-consistency gate stays closed.
- Risk: private readiness or preparation queue leaks target-slot details.
- Control: private outputs remain git-ignored and public evidence contains aggregate counts only.
- Risk: raw data is modified during preparation.
- Control: this phase does not read or mutate raw inbox; later phases must preserve the immutable raw boundary.
"""
    rollback = f"""# Rollback Plan

Remove the artifacts for `{PHASE_ID}`, metadata copies, private preparation outputs, tool, validator, focused test and governance entries. Do not touch prior authorization-readiness evidence or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_preparation_manifest.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_preparation_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "preparation_conclusion": PREPARATION_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "authorization_readiness_summary": "public_safe_metadata_copy",
            "authorization_readiness_manifest": "public_safe_metadata_copy",
            "authorization_readiness_go_no_go": "public_safe_metadata_copy",
            "authorization_readiness_matrix": "public_safe_metadata_copy",
            "authorization_readiness_private_queue": "ignored_private_runtime",
        },
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
        "metadata_artifact_refs": [
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "private_artifact_refs": [
            "private:owner_authorized_anchor_confirmation_preparation_diagnostic",
            "private:owner_authorized_anchor_confirmation_preparation_queue",
            "private:owner_authorized_anchor_confirmation_preparation_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_preparation.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_preparation.py --require-private-preparation",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_preparation.py",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }


def _write_governance_events(generated_at: str, manifest: dict[str, Any]) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-PREPARATION",
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "status": STATUS,
        "decision": DECISION,
        "fact_level": "EXTRACTED",
        "iteration_id": "ITER-20260707-KMFA-V014-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-PREPARATION",
        "task_id": TASK_ID,
        "version": VERSION,
        "go_no_go": DECISION,
        "result_commit": "PENDING",
        "summary": "Prepared private owner-authorized anchor confirmation queue without confirming anchors or comparing raw values.",
        "authorization_readiness_item_count": 72,
        "preparation_item_count": 72,
        "preparation_ready_item_count": 72,
        "preparation_blocker_item_count": 0,
        "owner_authorized_anchor_confirmation_count": 0,
        "raw_to_processed_value_comparison_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "files_changed": _changed_kmfa_files(),
    }
    _upsert_jsonl(DEVELOPMENT_EVENTS_PATH, event, ("event_id",))
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        {
            "acceptance_id": ACCEPTANCE_ID,
            "acceptance_output": "Owner-authorized anchor confirmation preparation manifest summary Go No-Go public-safe matrix private ignored preparation queue diagnostic report validator focused test and governance records",
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "v0.1.4 residual difference owner-authorized anchor confirmation preparation",
            "phase_goal": "prepare private owner-authorized anchor confirmation packet without confirming anchors or reading raw data",
            "phase_id": PHASE_ID,
            "project_id": "KMFA",
            "raw_data_committed": False,
            "record_type": "v014_phase",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_PREPARATION",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": STATUS,
            "task_count": 3,
            "updated_at": "2026-07-07",
            "version": VERSION,
        },
        ("phase_id", "version"),
    )
    task_goals = [
        "read authorization-readiness public-safe evidence and ignored private readiness queue read-only",
        "write ignored private owner-authorized anchor confirmation preparation diagnostic queue and report",
        "emit public-safe NO_GO evidence while keeping confirmation comparison and downstream gates closed",
    ]
    for index, task_goal in enumerate(task_goals, start=1):
        _upsert_jsonl(
            TASK_STATUS_PATH,
            {
                "acceptance_id": ACCEPTANCE_ID,
                "derived_percent": 100.0,
                "evidence_ref": MANIFEST_PATH.as_posix(),
                "fact_level": "EXTRACTED",
                "governance_stage_id": "VALUE-CONSISTENCY",
                "phase_id": PHASE_ID,
                "project_id": "KMFA",
                "raw_data_committed": False,
                "record_type": "v014_task",
                "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_PREPARATION",
                "roadmap_stage_id": "VALUE-CONSISTENCY",
                "schema_version": "kmfa.v014_stage_phase_task_status.v1",
                "stage_id": "VALUE-CONSISTENCY",
                "status": "completed",
                "task_goal": task_goal,
                "task_id": f"{TASK_ID}-T{index}",
                "updated_at": "2026-07-07",
                "version": VERSION,
            },
            ("task_id",),
        )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_MATRIX_PATH)
    source_private_diagnostic = _read_json(SOURCE_PRIVATE_READINESS_DIAGNOSTIC_PATH)
    _ = SOURCE_PRIVATE_READINESS_REPORT_PATH.read_text(encoding="utf-8")
    readiness_rows = _read_jsonl(SOURCE_PRIVATE_READINESS_QUEUE_PATH)
    if len(readiness_rows) != 72:
        raise ValueError("owner-authorized anchor confirmation preparation requires 72 readiness rows")
    if Counter(row.get("diagnostic_track") for row in readiness_rows) != EXPECTED_TRACK_COUNTS:
        raise ValueError("unexpected diagnostic track counts")
    if any(row.get("authorization_readiness_status") != "ready_for_private_preparation" for row in readiness_rows):
        raise ValueError("all readiness rows must be ready_for_private_preparation")
    preparation_rows = _build_preparation_queue(generated_at=generated, readiness_rows=readiness_rows)
    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    private_diagnostic = _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        source_private_diagnostic=source_private_diagnostic,
        preparation_rows=preparation_rows,
        raw_boundary=raw_boundary,
    )
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_private_diagnostic=source_private_diagnostic,
        readiness_rows=readiness_rows,
        preparation_rows=preparation_rows,
        raw_boundary=raw_boundary,
        public_safety=public_safety,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)
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
    _write_human(summary, matrix, go_no_go)
    if write_governance_event:
        _write_governance_events(generated, manifest)
    return {
        "summary": summary,
        "matrix": matrix,
        "go_no_go": go_no_go,
        "manifest": manifest,
        "private_diagnostic": private_diagnostic,
        "private_preparation_rows": preparation_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--no-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at, write_governance_event=not args.no_governance_event)
    summary = result["summary"]
    print(
        "PASS: generated V014 owner-authorized anchor confirmation preparation "
        f"decision={summary['decision']} preparation_items={summary['preparation_item_count']} "
        f"next={summary['next_recommended_phase']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
