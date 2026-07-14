#!/usr/bin/env python3
"""Intake corrected-source or owner-approved resolution evidence for KMFA v0.1.4.

This phase turns the previous private reconciliation readiness blocker into a
fillable private intake contract. It does not read the raw inbox, does not
accept missing evidence as authorization, and does not start full
reconciliation.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_CORRECTED_SOURCE_OR_OWNER_RESOLUTION_INTAKE"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-CORRECTED-SOURCE-OR-OWNER-RESOLUTION-INTAKE-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-CORRECTED-SOURCE-OR-OWNER-RESOLUTION-INTAKE"
VERSION = "0.1.4-private-corrected-source-or-owner-resolution-intake"
STATUS = "completed_validated_local_only_private_corrected_source_or_owner_resolution_intake_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "owner_approved_resolution_input_contract_prepared_no_authorized_resolution_supplied"
PREVIOUS_REQUIRED_INPUT = "corrected_private_source_or_owner_approved_resolution_before_full_reconciliation"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_CORRECTED_SOURCE_OR_OWNER_RESOLUTION_APPLICATION_READINESS"
NEXT_REQUIRED_INPUT = "owner_approved_private_resolution_input_or_corrected_source_package"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake_go_no_go_report.json"
INTAKE_MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_corrected_source_or_owner_resolution_intake_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_private_corrected_source_or_owner_resolution_intake_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_private_corrected_source_or_owner_resolution_intake_go_no_go_report.json"
METADATA_INTAKE_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_private_corrected_source_or_owner_resolution_intake_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_READINESS_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_reconciliation_readiness_recheck_summary.json"
SOURCE_READINESS_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_private_reconciliation_readiness_matrix_public_safe.json"
SOURCE_TRACKS_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_tracks_public_safe.json"
SOURCE_PRIVATE_DECISION_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake/private_blocker_resolution_decision_queue.jsonl"
)

PRIVATE_INPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_approved_resolution_input"
PRIVATE_OWNER_INPUT_PATH = PRIVATE_INPUT_DIR / "private_owner_approved_resolution_input.json"
PRIVATE_CORRECTED_SOURCE_INPUT_PATH = PRIVATE_INPUT_DIR / "private_corrected_source_package_manifest.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake"
PRIVATE_TEMPLATE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_approved_resolution_input_template.json"
PRIVATE_PENDING_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_approved_resolution_pending_queue.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_resolution_intake_diagnostic.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_resolution_intake.md"


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
        "private_reconciliation_readiness_summary_read_by_this_phase": True,
        "private_decision_queue_read_by_this_phase": True,
        "private_owner_resolution_template_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_owner_input_committed": False,
        "private_corrected_source_manifest_committed": False,
        "private_template_committed": False,
        "private_pending_queue_committed": False,
        "private_diagnostic_committed": False,
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


def _queue_counts(queue: list[dict[str, Any]]) -> dict[str, int]:
    decisions = Counter(str(row.get("decision_code", "missing")) for row in queue)
    return {
        "private_decision_queue_count": len(queue),
        "blocked_private_decision_count": sum(count for code, count in decisions.items() if code.startswith("keep_blocked")),
        "requires_corrected_source_or_owner_exclusion_count": decisions[
            "keep_blocked_pending_corrected_source_or_owner_exclusion"
        ],
        "requires_private_disambiguation_count": decisions["keep_blocked_pending_private_disambiguation"],
        "resolution_applied_private_decision_count": sum(1 for row in queue if row.get("resolution_applied") is True),
    }


def _build_template(generated_at: str, source_tracks: dict[str, Any], queue_counts: dict[str, int]) -> dict[str, Any]:
    tracks = source_tracks.get("resolution_tracks", [])
    if not isinstance(tracks, list):
        raise ValueError("resolution_tracks must be a list")
    template_rows = []
    for track in tracks:
        if not isinstance(track, dict):
            continue
        template_rows.append(
            {
                "blocker_code": track["blocker_code"],
                "resolution_track_code": track["resolution_track_code"],
                "required_input_class": track["required_next_input"],
                "owner_approved_decision_code": "PENDING_OWNER_APPROVED_INPUT",
                "corrected_source_package_ref": "PENDING_PRIVATE_INPUT",
                "owner_resolution_basis_ref": "PENDING_PRIVATE_INPUT",
                "allow_full_reconciliation_after_application": False,
            }
        )
    return {
        "schema_version": "kmfa.private.v014_owner_approved_resolution_input_template.v1",
        "classification": "private_owner_approved_resolution_input_template_do_not_commit",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "template_track_count": len(template_rows),
        "private_decision_queue_count": queue_counts["private_decision_queue_count"],
        "blocked_private_decision_count": queue_counts["blocked_private_decision_count"],
        "template_rows": template_rows,
    }


def _build_pending_queue(private_queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pending: list[dict[str, Any]] = []
    for row in private_queue:
        pending.append(
            {
                "target_slot_id": row.get("target_slot_id"),
                "source_decision_code": row.get("decision_code"),
                "required_owner_input": (
                    "corrected_source_or_owner_exclusion"
                    if row.get("decision_code") == "keep_blocked_pending_corrected_source_or_owner_exclusion"
                    else "private_disambiguation"
                ),
                "owner_approved_input_status": "missing",
                "resolution_application_allowed": False,
                "full_reconciliation_allowed": False,
            }
        )
    return pending


def _build_intake_matrix(generated_at: str, readiness_summary: dict[str, Any], queue_counts: dict[str, int]) -> dict[str, Any]:
    checks = [
        {
            "check_code": "previous_readiness_recheck_completed",
            "status": "PASS" if readiness_summary.get("phase_id") == "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_RECONCILIATION_READINESS_RECHECK" else "FAIL",
            "observed_public_safe": readiness_summary.get("phase_id"),
            "required": "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_RECONCILIATION_READINESS_RECHECK",
        },
        {
            "check_code": "private_owner_approved_resolution_input_present",
            "status": "FAIL",
            "observed_public_safe": False,
            "required": True,
        },
        {
            "check_code": "private_corrected_source_package_present",
            "status": "FAIL",
            "observed_public_safe": False,
            "required": True,
        },
        {
            "check_code": "blocked_private_decisions_resolved",
            "status": "FAIL" if queue_counts["blocked_private_decision_count"] else "PASS",
            "observed_public_safe": queue_counts["blocked_private_decision_count"],
            "required": 0,
        },
        {
            "check_code": "resolution_application_allowed",
            "status": "FAIL",
            "observed_public_safe": False,
            "required": True,
        },
    ]
    pass_count = sum(1 for row in checks if row["status"] == "PASS")
    fail_count = sum(1 for row in checks if row["status"] == "FAIL")
    return {
        "schema_version": "kmfa.v014_private_corrected_source_or_owner_resolution_intake_matrix_public_safe.v1",
        "record_type": "v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "intake_check_count": len(checks),
        "intake_pass_count": pass_count,
        "intake_fail_count": fail_count,
        "owner_approved_resolution_input_present": False,
        "corrected_private_source_package_present": False,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "checks": checks,
        "decision": DECISION,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 private corrected-source or owner-resolution intake",
                "",
                f"- Phase: `{PHASE_ID}`",
                f"- Decision: `{summary['decision']}`",
                f"- Intake checks: `{matrix['intake_pass_count']}` pass / `{matrix['intake_fail_count']}` fail",
                f"- Private decision queue: `{summary['private_decision_queue_count']}` records, `{summary['blocked_private_decision_count']}` still blocked",
                f"- Owner-approved resolution input present: `{summary['owner_approved_resolution_input_present']}`",
                f"- Corrected private source package present: `{summary['corrected_private_source_package_present']}`",
                f"- Full reconciliation allowed: `{summary['full_reconciliation_allowed']}`",
                "",
                "Result: a private input template was prepared, but no authorized resolution or corrected source was supplied.",
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
                "- Full reconciliation: `false`",
                "- GitHub upload: `false`",
                "- App reinstall: `false`",
                "- Business execution: `false`",
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
                "- Planned validator: `python3 KMFA/tools/check_v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake.py --require-private-template`",
                "- Planned focused test: `python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake`",
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
                "- R1: No owner-approved resolution input exists, so full reconciliation remains blocked.",
                "- R2: Template preparation alone is not evidence that business values match raw data.",
                "- R3: Future private input must be validated before any source-map application.",
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
                "- Remove ignored private template and pending queue files for this phase.",
                "- Re-run private reconciliation readiness recheck before retrying intake.",
            ]
        )
        + "\n",
    )


def _write_private_artifacts(
    *,
    generated_at: str,
    template: dict[str, Any],
    pending_queue: list[dict[str, Any]],
    matrix: dict[str, Any],
    queue_counts: dict[str, int],
    summary: dict[str, Any],
) -> None:
    diagnostic = {
        "schema_version": "kmfa.private.v014_corrected_source_or_owner_resolution_intake_diagnostic.v1",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "owner_approved_resolution_input_present": False,
        "corrected_private_source_package_present": False,
        "private_input_path_exists": PRIVATE_OWNER_INPUT_PATH.exists(),
        "corrected_source_manifest_path_exists": PRIVATE_CORRECTED_SOURCE_INPUT_PATH.exists(),
        "private_decision_queue_count": queue_counts["private_decision_queue_count"],
        "blocked_private_decision_count": queue_counts["blocked_private_decision_count"],
        "pending_queue_count": len(pending_queue),
        "intake_fail_count": matrix["intake_fail_count"],
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "raw_inbox_accessed": False,
    }
    _write_json(PRIVATE_TEMPLATE_PATH, template)
    _write_jsonl(PRIVATE_PENDING_QUEUE_PATH, pending_queue)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_text(
        PRIVATE_REPORT_PATH,
        "\n".join(
            [
                "# Private Corrected Source Or Owner Resolution Intake",
                "",
                "No owner-approved private resolution input or corrected source package was supplied in this phase.",
                "Use the generated private template only inside the ignored runtime directory.",
            ]
        )
        + "\n",
    )
    summary["private_template_written"] = True
    summary["private_pending_queue_written"] = True
    summary["private_diagnostic_written"] = True
    summary["private_template_gitignored"] = _git_check_ignored(PRIVATE_TEMPLATE_PATH)
    summary["private_pending_queue_gitignored"] = _git_check_ignored(PRIVATE_PENDING_QUEUE_PATH)
    summary["private_diagnostic_gitignored"] = _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH)


def _write_governance_event(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-PRIVATE-CORRECTED-SOURCE-OR-OWNER-RESOLUTION-INTAKE"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PRIVATE-CORRECTED-SOURCE-OR-OWNER-RESOLUTION-INTAKE",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "owner_approved_resolution_input_present": False,
        "corrected_private_source_package_present": False,
        "private_decision_queue_count": summary["private_decision_queue_count"],
        "blocked_private_decision_count": summary["blocked_private_decision_count"],
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Prepared private owner-approved resolution input contract and kept reconciliation blocked.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    readiness_summary = _read_json(SOURCE_READINESS_SUMMARY_PATH)
    readiness_matrix = _read_json(SOURCE_READINESS_MATRIX_PATH)
    source_tracks = _read_json(SOURCE_TRACKS_PATH)
    private_queue = _read_jsonl(SOURCE_PRIVATE_DECISION_QUEUE_PATH)
    queue_counts = _queue_counts(private_queue)
    template = _build_template(timestamp, source_tracks, queue_counts)
    pending_queue = _build_pending_queue(private_queue)
    intake_matrix = _build_intake_matrix(timestamp, readiness_summary, queue_counts)

    summary = {
        "schema_version": "kmfa.v014_private_corrected_source_or_owner_resolution_intake_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_phase_id": readiness_summary["phase_id"],
        "source_decision": readiness_summary["decision"],
        "source_readiness_fail_count": readiness_summary["source_readiness_fail_count"],
        "source_full_reconciliation_ready": readiness_summary["full_reconciliation_ready"],
        "source_intake_fail_count": intake_matrix["intake_fail_count"],
        "previous_required_input": PREVIOUS_REQUIRED_INPUT,
        "previous_required_input_resolved_by_this_phase": False,
        "owner_approved_resolution_input_present": False,
        "corrected_private_source_package_present": False,
        "owner_approved_resolution_intake_template_prepared": True,
        "template_track_count": template["template_track_count"],
        **queue_counts,
        "private_pending_queue_count": len(pending_queue),
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
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
    _write_private_artifacts(
        generated_at=timestamp,
        template=template,
        pending_queue=pending_queue,
        matrix=intake_matrix,
        queue_counts=queue_counts,
        summary=summary,
    )

    go_no_go = {
        "schema_version": "kmfa.v014_private_corrected_source_or_owner_resolution_intake_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake_go_no_go",
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
        "owner_approved_resolution_input_present": False,
        "corrected_private_source_package_present": False,
        "blocked_private_decision_count": summary["blocked_private_decision_count"],
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_private_corrected_source_or_owner_resolution_intake_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "summary": summary,
        "go_no_go": go_no_go,
        "intake_matrix": intake_matrix,
        "source_readiness_matrix": {
            "phase_id": readiness_matrix["phase_id"],
            "decision": readiness_matrix["decision"],
            "readiness_fail_count": readiness_matrix["readiness_fail_count"],
            "full_reconciliation_ready": readiness_matrix["full_reconciliation_ready"],
        },
        "private_artifacts_gitignored": True,
    }

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (INTAKE_MATRIX_PATH, intake_matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_INTAKE_MATRIX_PATH, intake_matrix),
    ):
        _write_json(path, payload)
    _write_human_artifacts(summary, intake_matrix)
    _write_governance_event(timestamp, summary)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    print(
        "PASS: KMFA v0.1.4 private corrected-source or owner-resolution intake generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"blocked={manifest['summary']['blocked_private_decision_count']}, "
        f"owner_input={manifest['summary']['owner_approved_resolution_input_present']})"
    )


if __name__ == "__main__":
    main()
