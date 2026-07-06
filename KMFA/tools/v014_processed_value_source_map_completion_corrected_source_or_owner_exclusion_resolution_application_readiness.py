#!/usr/bin/env python3
"""Check application readiness for the 36 corrected-source/owner-exclusion items."""

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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION_READINESS"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-APPLICATION-READINESS-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-APPLICATION-READINESS"
VERSION = "0.1.4-corrected-source-or-owner-exclusion-resolution-application-readiness"
STATUS = "completed_validated_local_only_corrected_source_or_owner_exclusion_resolution_application_readiness_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "resolution_application_not_ready_36_owner_inputs_missing"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_fills_36_corrected_source_or_exclusion_resolution_items"
NEXT_RECOMMENDED_PHASE = (
    "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT_RETRY"
)

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_readiness_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_readiness_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_readiness_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_readiness_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_INPUT_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_summary.json"
SOURCE_INPUT_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_matrix_public_safe.json"
SOURCE_PRIVATE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input/private_corrected_source_or_owner_exclusion_resolution_input_template.json"
)
SOURCE_PRIVATE_PENDING_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input/private_corrected_source_or_owner_exclusion_pending_queue.jsonl"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness"
)
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_application_readiness_diagnostic.json"
PRIVATE_BLOCKER_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_application_blocker_queue.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_application_readiness.md"

VALID_OWNER_DECISION_CODES = {
    "REGISTER_CORRECTED_SOURCE_REF",
    "OWNER_EXCLUDE_FROM_RECONCILIATION",
}
PENDING_VALUES = {"", "PENDING_PRIVATE_INPUT", "PENDING_CORRECTED_SOURCE_OR_OWNER_EXCLUSION"}
FILES_CHANGED = [
    "KMFA/CHANGELOG.md",
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
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_readiness_go_no_go_report.json",
    "KMFA/metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_readiness_manifest.json",
    "KMFA/metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_readiness_matrix_public_safe.json",
    "KMFA/metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_readiness_summary.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION_READINESS/human/go_no_go_record.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION_READINESS/human/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness_report.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION_READINESS/human/risk_register.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION_READINESS/human/rollback_plan.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION_READINESS/human/test_results.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION_READINESS/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness_go_no_go_report.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION_READINESS/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness_manifest.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION_READINESS/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness_matrix_public_safe.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION_READINESS/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness_summary.json",
    "KMFA/tests/test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness.py",
    "KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness.py",
    "KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness.py",
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
        "private_36_item_template_read_by_this_phase": True,
        "private_36_item_pending_queue_read_by_this_phase": True,
        "private_application_readiness_diagnostic_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_template_committed": False,
        "private_pending_queue_committed": False,
        "private_application_diagnostic_committed": False,
        "private_application_blocker_queue_committed": False,
        "private_report_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_file_hash_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "raw_or_processed_fingerprint_value_committed": False,
        "credential_or_secret_committed": False,
    }


def _item_has_owner_input(item: dict[str, Any]) -> bool:
    decision = str(item.get("required_owner_decision_code") or "")
    corrected_ref = str(item.get("corrected_source_package_ref") or "")
    exclusion_ref = str(item.get("owner_exclusion_basis_ref") or "")
    if decision not in VALID_OWNER_DECISION_CODES:
        return False
    if decision == "REGISTER_CORRECTED_SOURCE_REF":
        return corrected_ref not in PENDING_VALUES
    if decision == "OWNER_EXCLUDE_FROM_RECONCILIATION":
        return exclusion_ref not in PENDING_VALUES
    return False


def _build_blocker_queue(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for item in items:
        if _item_has_owner_input(item):
            continue
        blockers.append(
            {
                "target_slot_id": item.get("target_slot_id"),
                "source_decision_code": item.get("source_decision_code"),
                "application_blocker_code": "missing_36_item_corrected_source_or_owner_exclusion_input",
                "owner_input_status": "missing",
                "resolution_application_allowed": False,
                "full_reconciliation_allowed": False,
            }
        )
    return blockers


def _build_matrix(generated_at: str, source_summary: dict[str, Any], item_count: int, valid_count: int) -> dict[str, Any]:
    checks = [
        {
            "check_code": "source_input_phase_available",
            "status": "PASS" if source_summary.get("private_resolution_item_count") == 36 else "FAIL",
            "observed_public_safe": source_summary.get("private_resolution_item_count"),
            "required": 36,
        },
        {
            "check_code": "source_private_template_count_locked",
            "status": "PASS" if item_count == 36 else "FAIL",
            "observed_public_safe": item_count,
            "required": 36,
        },
        {
            "check_code": "owner_resolution_input_present",
            "status": "FAIL" if valid_count == 0 else "PASS",
            "observed_public_safe": valid_count > 0,
            "required": True,
        },
        {
            "check_code": "all_36_inputs_valid",
            "status": "FAIL" if valid_count != 36 else "PASS",
            "observed_public_safe": valid_count,
            "required": 36,
        },
        {
            "check_code": "all_36_unlinked_blockers_resolved",
            "status": "FAIL" if valid_count != 36 else "PASS",
            "observed_public_safe": valid_count,
            "required": 36,
        },
        {
            "check_code": "resolution_application_allowed",
            "status": "FAIL",
            "observed_public_safe": False,
            "required": True,
        },
        {
            "check_code": "full_reconciliation_allowed",
            "status": "FAIL",
            "observed_public_safe": False,
            "required": True,
        },
    ]
    pass_count = sum(1 for row in checks if row["status"] == "PASS")
    fail_count = sum(1 for row in checks if row["status"] == "FAIL")
    return {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_application_readiness_matrix_public_safe.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_application_readiness_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "application_readiness_check_count": len(checks),
        "application_readiness_pass_count": pass_count,
        "application_readiness_fail_count": fail_count,
        "owner_resolution_input_present": valid_count > 0,
        "all_36_inputs_valid": valid_count == 36,
        "all_36_unlinked_blockers_resolved": valid_count == 36,
        "resolution_application_ready": False,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "decision": DECISION,
        "checks": checks,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# KMFA v0.1.4 Corrected Source Or Owner Exclusion Application Readiness

Decision: `{DECISION}`

This phase checks whether the 36-item private corrected-source or owner-exclusion input has been supplied. It does not apply source-map records and does not run raw-to-processed comparison.

## Public-safe aggregate result

- Private resolution item count: `{summary["private_resolution_item_count"]}`
- Valid owner input count: `{summary["valid_owner_input_count"]}`
- Missing owner input count: `{summary["missing_owner_input_count"]}`
- Decision checks: `{matrix["application_readiness_pass_count"]}` pass / `{matrix["application_readiness_fail_count"]}` fail
- Resolution application ready: `false`
- Full reconciliation allowed: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- blocked_until: `{NEXT_REQUIRED_INPUT}`
- private_resolution_item_count: `{summary["private_resolution_item_count"]}`
- valid_owner_input_count: `{summary["valid_owner_input_count"]}`
- GitHub upload performed: `false`
- App reinstall performed: `false`
"""
    risk_register = """# Risk Register

- R1: Readiness evidence can be mistaken for resolution application.
- R2: Missing private owner inputs keep all application and reconciliation gates closed.
- R3: Raw-to-processed consistency is still unverified until a later explicit comparison phase.
"""
    rollback_plan = """# Rollback Plan

No raw inbox, source-map, materialization, reconciliation or active authorization file was mutated. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private readiness output directory if needed.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness.py KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness.py KMFA/tests/test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `git diff --check -- KMFA`

All listed commands must pass before local commit. The raw inbox is not read, listed, parsed, copied, moved, renamed, deleted, overwritten, normalized or mutated by this phase.
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
    event_id = "DEV-KMFA-20260706-V014-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-APPLICATION-READINESS"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-APPLICATION-READINESS",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "private_resolution_item_count": summary["private_resolution_item_count"],
        "missing_owner_input_count": summary["missing_owner_input_count"],
        "valid_owner_input_count": summary["valid_owner_input_count"],
        "resolution_application_ready": False,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Checked 36-item corrected-source or owner-exclusion application readiness and kept application gates closed.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_INPUT_SUMMARY_PATH)
    source_matrix = _read_json(SOURCE_INPUT_MATRIX_PATH)
    template = _read_json(SOURCE_PRIVATE_TEMPLATE_PATH)
    pending_queue = _read_jsonl(SOURCE_PRIVATE_PENDING_QUEUE_PATH)
    items = template.get("items", [])
    if not isinstance(items, list):
        raise ValueError("private template items must be a list")
    if len(items) != 36 or len(pending_queue) != 36:
        raise ValueError(f"expected 36 private items and 36 pending rows, got {len(items)} and {len(pending_queue)}")
    valid_count = sum(1 for item in items if isinstance(item, dict) and _item_has_owner_input(item))
    missing_count = 36 - valid_count
    blocker_queue = _build_blocker_queue([item for item in items if isinstance(item, dict)])
    diagnostic = {
        "schema_version": "kmfa.private.v014_corrected_source_or_owner_exclusion_resolution_application_readiness_diagnostic.v1",
        "classification": "private_corrected_source_or_owner_exclusion_resolution_application_readiness_diagnostic_do_not_commit",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_application_readiness_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_resolution_item_count": len(items),
        "valid_owner_input_count": valid_count,
        "missing_owner_input_count": missing_count,
        "application_blocker_queue_count": len(blocker_queue),
        "resolution_application_ready": False,
        "resolution_application_allowed": False,
        "raw_inbox_accessed": False,
        "raw_boundary": _raw_boundary(),
    }
    private_report = f"""# Private application readiness diagnostic

- phase_id: `{PHASE_ID}`
- private_resolution_item_count: `{len(items)}`
- valid_owner_input_count: `{valid_count}`
- missing_owner_input_count: `{missing_count}`
- resolution_application_ready: `false`

This diagnostic remains private and must not be committed.
"""
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_BLOCKER_QUEUE_PATH, blocker_queue)
    _write_text(PRIVATE_REPORT_PATH, private_report)

    matrix = _build_matrix(timestamp, source_summary, len(items), valid_count)
    summary = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_application_readiness_summary.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_application_readiness_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_input_phase_id": source_summary["phase_id"],
        "source_input_decision": source_summary["decision"],
        "source_input_matrix_fail_count": source_matrix["decision_fail_count"],
        "source_private_resolution_item_count": source_summary["private_resolution_item_count"],
        "source_owner_resolution_input_present": source_summary["owner_resolution_input_present"],
        "source_all_36_unlinked_blockers_resolved": source_summary["all_36_unlinked_blockers_resolved"],
        "source_resolution_application_allowed": source_summary["resolution_application_allowed"],
        "private_resolution_item_count": len(items),
        "private_pending_queue_count": len(pending_queue),
        "valid_owner_input_count": valid_count,
        "missing_owner_input_count": missing_count,
        "application_blocker_queue_count": len(blocker_queue),
        "owner_resolution_input_present": valid_count > 0,
        "all_36_inputs_valid": valid_count == 36,
        "all_36_unlinked_blockers_resolved": False,
        "resolution_application_ready": False,
        "resolution_application_allowed": False,
        "resolution_application_performed_by_this_phase": False,
        "source_map_mutation_performed_by_this_phase": False,
        "source_map_records_applied_count": 0,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_blocker_queue_written": True,
        "private_blocker_queue_gitignored": _git_check_ignored(PRIVATE_BLOCKER_QUEUE_PATH),
        "private_report_written": True,
        "private_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_application_readiness_go_no_go.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_application_readiness_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "blocked_until": NEXT_REQUIRED_INPUT,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_resolution_item_count": len(items),
        "valid_owner_input_count": valid_count,
        "resolution_application_ready": False,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_application_readiness_manifest.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_application_readiness_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "git_head_at_generation": _git_output(["rev-parse", "HEAD"]),
        "source_artifacts": [
            SOURCE_INPUT_SUMMARY_PATH.as_posix(),
            SOURCE_INPUT_MATRIX_PATH.as_posix(),
            "private:corrected_source_or_owner_exclusion_resolution_input_template",
            "private:corrected_source_or_owner_exclusion_pending_queue",
        ],
        "public_artifacts": [path.as_posix() for path in (
            SUMMARY_PATH,
            MANIFEST_PATH,
            GO_NO_GO_PATH,
            MATRIX_PATH,
            REPORT_PATH,
            GO_NO_GO_RECORD_PATH,
            TEST_RESULTS_PATH,
            RISK_REGISTER_PATH,
            ROLLBACK_PATH,
            METADATA_SUMMARY_PATH,
            METADATA_MANIFEST_PATH,
            METADATA_GO_NO_GO_PATH,
            METADATA_MATRIX_PATH,
        )],
        "private_artifact_refs": [
            "private:corrected_source_or_owner_exclusion_resolution_application_readiness_diagnostic",
            "private:corrected_source_or_owner_exclusion_resolution_application_blocker_queue",
            "private:corrected_source_or_owner_exclusion_resolution_application_readiness_report",
        ],
        "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness.py --require-private-diagnostic",
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
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
    _append_development_event(timestamp, summary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 corrected-source or owner-exclusion application readiness generated "
        f"(decision={summary['decision']}, valid_inputs={summary['valid_owner_input_count']}, "
        f"missing_inputs={summary['missing_owner_input_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
