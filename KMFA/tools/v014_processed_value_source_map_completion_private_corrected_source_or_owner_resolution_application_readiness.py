#!/usr/bin/env python3
"""Check application readiness for private corrected-source or owner resolutions.

This phase consumes the previous private intake contract and determines whether
resolution application may start. Missing owner-approved input keeps all
application, reconciliation, report, upload, and business-execution gates
closed.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_CORRECTED_SOURCE_OR_OWNER_RESOLUTION_APPLICATION_READINESS"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-CORRECTED-SOURCE-OR-OWNER-RESOLUTION-APPLICATION-READINESS-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-CORRECTED-SOURCE-OR-OWNER-RESOLUTION-APPLICATION-READINESS"
VERSION = "0.1.4-private-corrected-source-or-owner-resolution-application-readiness"
STATUS = "completed_validated_local_only_private_corrected_source_or_owner_resolution_application_readiness_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "resolution_application_not_ready_missing_owner_approved_private_input"
PREVIOUS_REQUIRED_INPUT = "owner_approved_private_resolution_input_or_corrected_source_package"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_CORRECTED_SOURCE_OR_OWNER_RESOLUTION_RETRY_INPUT"
NEXT_REQUIRED_INPUT = "owner_approved_private_resolution_input_or_corrected_source_package"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness_go_no_go_report.json"
READINESS_MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_corrected_source_or_owner_resolution_application_readiness_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_private_corrected_source_or_owner_resolution_application_readiness_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_private_corrected_source_or_owner_resolution_application_readiness_go_no_go_report.json"
METADATA_READINESS_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_private_corrected_source_or_owner_resolution_application_readiness_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_INTAKE_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_corrected_source_or_owner_resolution_intake_summary.json"
SOURCE_INTAKE_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_private_corrected_source_or_owner_resolution_intake_matrix_public_safe.json"
SOURCE_PRIVATE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake/private_owner_approved_resolution_input_template.json"
)
SOURCE_PRIVATE_PENDING_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake/private_owner_approved_resolution_pending_queue.jsonl"
)
SOURCE_PRIVATE_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake/private_corrected_source_or_owner_resolution_intake_diagnostic.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness"
)
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_resolution_application_readiness_diagnostic.json"
PRIVATE_BLOCKER_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_resolution_application_blocker_queue.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_resolution_application_readiness.md"


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
        "private_intake_summary_read_by_this_phase": True,
        "private_intake_template_read_by_this_phase": True,
        "private_pending_queue_read_by_this_phase": True,
        "private_application_readiness_diagnostic_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_intake_template_committed": False,
        "private_pending_queue_committed": False,
        "private_application_diagnostic_committed": False,
        "private_application_blocker_queue_committed": False,
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


def _queue_counts(pending_queue: list[dict[str, Any]]) -> dict[str, int]:
    status_counts = Counter(str(row.get("owner_approved_input_status", "missing")) for row in pending_queue)
    app_counts = Counter(str(row.get("resolution_application_allowed")) for row in pending_queue)
    reconciliation_counts = Counter(str(row.get("full_reconciliation_allowed")) for row in pending_queue)
    return {
        "private_pending_queue_count": len(pending_queue),
        "missing_owner_input_count": status_counts["missing"],
        "valid_owner_input_count": status_counts["valid"],
        "resolution_application_allowed_row_count": app_counts["True"],
        "full_reconciliation_allowed_row_count": reconciliation_counts["True"],
    }


def _build_blocker_queue(pending_queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for row in pending_queue:
        if row.get("owner_approved_input_status") == "missing":
            blockers.append(
                {
                    "target_slot_id": row.get("target_slot_id"),
                    "source_decision_code": row.get("source_decision_code"),
                    "required_owner_input": row.get("required_owner_input"),
                    "application_blocker_code": "missing_owner_approved_private_input",
                    "resolution_application_allowed": False,
                    "full_reconciliation_allowed": False,
                }
            )
    return blockers


def _readiness_matrix(
    generated_at: str,
    intake_summary: dict[str, Any],
    intake_matrix: dict[str, Any],
    template: dict[str, Any],
    queue_counts: dict[str, int],
) -> dict[str, Any]:
    checks = [
        {
            "check_code": "source_intake_completed",
            "status": "PASS" if intake_summary.get("phase_id") == "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_CORRECTED_SOURCE_OR_OWNER_RESOLUTION_INTAKE" else "FAIL",
            "observed_public_safe": intake_summary.get("phase_id"),
            "required": "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_CORRECTED_SOURCE_OR_OWNER_RESOLUTION_INTAKE",
        },
        {
            "check_code": "source_intake_go",
            "status": "FAIL" if intake_summary.get("decision") != "GO" else "PASS",
            "observed_public_safe": intake_summary.get("decision"),
            "required": "GO",
        },
        {
            "check_code": "owner_approved_input_present",
            "status": "FAIL" if intake_summary.get("owner_approved_resolution_input_present") is not True else "PASS",
            "observed_public_safe": bool(intake_summary.get("owner_approved_resolution_input_present")),
            "required": True,
        },
        {
            "check_code": "corrected_source_or_owner_input_present",
            "status": "FAIL"
            if not (
                intake_summary.get("owner_approved_resolution_input_present") is True
                or intake_summary.get("corrected_private_source_package_present") is True
            )
            else "PASS",
            "observed_public_safe": False,
            "required": True,
        },
        {
            "check_code": "all_pending_rows_have_valid_owner_input",
            "status": "FAIL" if queue_counts["missing_owner_input_count"] else "PASS",
            "observed_public_safe": queue_counts["missing_owner_input_count"],
            "required": 0,
        },
        {
            "check_code": "application_rows_allowed",
            "status": "FAIL" if queue_counts["resolution_application_allowed_row_count"] == 0 else "PASS",
            "observed_public_safe": queue_counts["resolution_application_allowed_row_count"],
            "required": "all_required_rows_true",
        },
        {
            "check_code": "source_intake_allowed_application",
            "status": "FAIL" if intake_summary.get("resolution_application_allowed") is not True else "PASS",
            "observed_public_safe": bool(intake_summary.get("resolution_application_allowed")),
            "required": True,
        },
    ]
    pass_count = sum(1 for row in checks if row["status"] == "PASS")
    fail_count = sum(1 for row in checks if row["status"] == "FAIL")
    return {
        "schema_version": "kmfa.v014_private_corrected_source_or_owner_resolution_application_readiness_matrix_public_safe.v1",
        "record_type": "v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_intake_matrix_fail_count": intake_matrix["intake_fail_count"],
        "template_track_count": template["template_track_count"],
        "application_readiness_check_count": len(checks),
        "application_readiness_pass_count": pass_count,
        "application_readiness_fail_count": fail_count,
        "resolution_application_ready": fail_count == 0,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed_after_application": False,
        "checks": checks,
        "decision": DECISION,
    }


def _write_private_artifacts(
    generated_at: str,
    summary: dict[str, Any],
    matrix: dict[str, Any],
    blocker_queue: list[dict[str, Any]],
) -> None:
    diagnostic = {
        "schema_version": "kmfa.private.v014_corrected_source_or_owner_resolution_application_readiness_diagnostic.v1",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "owner_approved_resolution_input_present": False,
        "corrected_private_source_package_present": False,
        "private_pending_queue_count": summary["private_pending_queue_count"],
        "application_blocker_queue_count": len(blocker_queue),
        "application_readiness_fail_count": matrix["application_readiness_fail_count"],
        "resolution_application_ready": False,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed_after_application": False,
        "raw_inbox_accessed": False,
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_BLOCKER_QUEUE_PATH, blocker_queue)
    _write_text(
        PRIVATE_REPORT_PATH,
        "\n".join(
            [
                "# Private Corrected Source Or Owner Resolution Application Readiness",
                "",
                "Resolution application is not ready because owner-approved private input is missing.",
                "No source-map, raw comparison, or reconciliation operation was performed.",
            ]
        )
        + "\n",
    )
    summary["private_diagnostic_written"] = True
    summary["private_application_blocker_queue_written"] = True
    summary["private_diagnostic_gitignored"] = _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH)
    summary["private_application_blocker_queue_gitignored"] = _git_check_ignored(PRIVATE_BLOCKER_QUEUE_PATH)


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 private corrected-source or owner-resolution application readiness",
                "",
                f"- Phase: `{PHASE_ID}`",
                f"- Decision: `{summary['decision']}`",
                f"- Readiness checks: `{matrix['application_readiness_pass_count']}` pass / `{matrix['application_readiness_fail_count']}` fail",
                f"- Missing owner input rows: `{summary['missing_owner_input_count']}`",
                f"- Resolution application ready: `{summary['resolution_application_ready']}`",
                f"- Full reconciliation allowed: `{summary['full_reconciliation_allowed']}`",
                "",
                "Result: application remains blocked until owner-approved private input or corrected source package is supplied.",
            ]
        )
        + "\n",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go/No-Go",
                "",
                f"- Decision: `{DECISION}`",
                f"- Blocked until: `{NEXT_REQUIRED_INPUT}`",
                "- Resolution application: `false`",
                "- Full reconciliation: `false`",
                "- GitHub upload: `false`",
                "- App reinstall: `false`",
            ]
        )
        + "\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# Test Results",
                "",
                "- Planned validator: `python3 KMFA/tools/check_v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness.py --require-private-diagnostic`",
                "- Planned focused test: `python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness`",
                "- Raw inbox access: `false`",
            ]
        )
        + "\n",
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# Risk Register",
                "",
                "- R1: Missing owner-approved input keeps application blocked.",
                "- R2: Application readiness does not prove raw-to-processed value consistency.",
                "- R3: A later application phase must validate private input before mutating source-map state.",
            ]
        )
        + "\n",
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# Rollback Plan",
                "",
                "- Remove this phase's public artifacts and metadata copies.",
                "- Remove ignored private diagnostic and blocker queue outputs.",
                "- Re-run the prior intake validator before retrying application readiness.",
            ]
        )
        + "\n",
    )


def _write_governance_event(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-PRIVATE-CORRECTED-SOURCE-OR-OWNER-RESOLUTION-APPLICATION-READINESS"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PRIVATE-CORRECTED-SOURCE-OR-OWNER-RESOLUTION-APPLICATION-READINESS",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "private_pending_queue_count": summary["private_pending_queue_count"],
        "missing_owner_input_count": summary["missing_owner_input_count"],
        "resolution_application_ready": False,
        "resolution_application_performed": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Checked private corrected-source owner-resolution application readiness and kept application blocked.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    intake_summary = _read_json(SOURCE_INTAKE_SUMMARY_PATH)
    intake_matrix = _read_json(SOURCE_INTAKE_MATRIX_PATH)
    template = _read_json(SOURCE_PRIVATE_TEMPLATE_PATH)
    pending_queue = _read_jsonl(SOURCE_PRIVATE_PENDING_QUEUE_PATH)
    source_private_diagnostic = _read_json(SOURCE_PRIVATE_DIAGNOSTIC_PATH)
    queue_counts = _queue_counts(pending_queue)
    blocker_queue = _build_blocker_queue(pending_queue)
    readiness_matrix = _readiness_matrix(timestamp, intake_summary, intake_matrix, template, queue_counts)

    summary = {
        "schema_version": "kmfa.v014_private_corrected_source_or_owner_resolution_application_readiness_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_phase_id": intake_summary["phase_id"],
        "source_decision": intake_summary["decision"],
        "source_owner_approved_resolution_input_present": intake_summary["owner_approved_resolution_input_present"],
        "source_corrected_private_source_package_present": intake_summary["corrected_private_source_package_present"],
        "source_resolution_application_allowed": intake_summary["resolution_application_allowed"],
        "source_intake_fail_count": intake_matrix["intake_fail_count"],
        "source_private_diagnostic_decision": source_private_diagnostic["decision"],
        "previous_required_input": PREVIOUS_REQUIRED_INPUT,
        "previous_required_input_resolved_by_this_phase": False,
        "owner_approved_resolution_input_present": False,
        "corrected_private_source_package_present": False,
        "template_track_count": template["template_track_count"],
        **queue_counts,
        "application_blocker_queue_count": len(blocker_queue),
        "resolution_application_ready": False,
        "resolution_application_allowed": False,
        "resolution_application_performed_by_this_phase": False,
        "source_map_mutation_performed_by_this_phase": False,
        "source_map_records_applied_count": 0,
        "full_reconciliation_allowed": False,
        "full_reconciliation_allowed_after_application": False,
        "full_raw_to_processed_reconciliation_performed_by_this_phase": False,
        "full_raw_to_processed_reconciliation_complete": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "processed_data_reconciliation_performed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    _write_private_artifacts(timestamp, summary, readiness_matrix, blocker_queue)

    go_no_go = {
        "schema_version": "kmfa.v014_private_corrected_source_or_owner_resolution_application_readiness_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "blocked_until": NEXT_REQUIRED_INPUT,
        "missing_owner_input_count": summary["missing_owner_input_count"],
        "resolution_application_ready": False,
        "resolution_application_performed": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_private_corrected_source_or_owner_resolution_application_readiness_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "summary": summary,
        "go_no_go": go_no_go,
        "readiness_matrix": readiness_matrix,
        "private_artifacts_gitignored": True,
    }

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (READINESS_MATRIX_PATH, readiness_matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_READINESS_MATRIX_PATH, readiness_matrix),
    ):
        _write_json(path, payload)
    _write_human_artifacts(summary, readiness_matrix)
    _write_governance_event(timestamp, summary)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    print(
        "PASS: KMFA v0.1.4 private corrected-source owner-resolution application readiness generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"missing_owner_input={manifest['summary']['missing_owner_input_count']}, "
        f"ready={manifest['summary']['resolution_application_ready']})"
    )


if __name__ == "__main__":
    main()
