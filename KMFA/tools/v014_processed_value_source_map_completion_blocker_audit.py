#!/usr/bin/env python3
"""Audit the repeated KMFA v0.1.4 processed value source-map blocker.

This phase records the third consecutive observation that the git-ignored
completion template has no valid owner/authorized-delegate source evidence. It
does not read or mutate the raw inbox, reapply a source map, materialize
processed values, compare values, upload, reinstall, or execute business steps.
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

from KMFA.tools.v014_processed_value_source_map_completion_readiness_recheck import (  # noqa: E402
    PRIVATE_TEMPLATE_PATH,
    _classify_items,
)


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_BLOCKER_AUDIT"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-BLOCKER-AUDIT-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-BLOCKER-AUDIT"
VERSION = "0.1.4-processed-value-source-map-completion-blocker-audit"
STATUS = "completed_validated_local_only_goal_blocked_audit"
BLOCKER = "private_completion_template_unfilled_authorized_sources_not_supplied"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_fills_private_completion_template_with_authorized_processed_value_sources"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_blocker_audit_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_blocker_audit_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_blocker_audit_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_blocker_audit_report.md"
OWNER_PACKET_PATH = HUMAN_DIR / "owner_agent_blocker_packet.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_blocker_audit_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_blocker_audit_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_blocker_audit_go_no_go_report.json"

APPLICATION_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_APPLICATION/machine/processed_value_source_map_completion_application_summary.json"
)
READINESS_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_READINESS_RECHECK/machine/processed_value_source_map_completion_readiness_recheck_summary.json"
)
PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_blocker_audit"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_blocker_audit_diagnostic.json"


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
    if result.returncode != 0:
        return "UNKNOWN"
    return result.stdout.strip()


def _git_check_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_readonly_policy_active": True,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_fingerprint_performed_by_this_phase": False,
        "raw_inbox_write_performed_by_this_phase": False,
        "raw_inbox_delete_performed_by_this_phase": False,
        "raw_inbox_move_performed_by_this_phase": False,
        "raw_inbox_rename_performed_by_this_phase": False,
        "raw_inbox_copy_performed_by_this_phase": False,
        "raw_inbox_normalize_performed_by_this_phase": False,
        "raw_inbox_mutation_performed_by_this_phase": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_template_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_digest_committed": False,
        "source_document_committed": False,
        "office_workbook_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "credential_or_secret_committed": False,
    }


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    application_summary = _read_json(APPLICATION_SUMMARY_PATH)
    readiness_summary = _read_json(READINESS_SUMMARY_PATH)
    private_template = _read_json(PRIVATE_TEMPLATE_PATH)
    counts, private_item_statuses = _classify_items(private_template)
    private_template_gitignored = _git_check_ignored(PRIVATE_TEMPLATE_PATH)

    repeated_observations = [
        {
            "phase_id": application_summary.get("phase_id"),
            "diagnostic_conclusion": application_summary.get("diagnostic_conclusion"),
            "valid_completion_item_count": application_summary.get("valid_completion_item_count"),
            "decision": application_summary.get("decision"),
        },
        {
            "phase_id": readiness_summary.get("phase_id"),
            "diagnostic_conclusion": readiness_summary.get("diagnostic_conclusion"),
            "valid_completion_item_count": readiness_summary.get("valid_completion_item_count"),
            "decision": readiness_summary.get("decision"),
        },
        {
            "phase_id": PHASE_ID,
            "diagnostic_conclusion": BLOCKER,
            "valid_completion_item_count": counts["valid_completion_item_count"],
            "decision": "NO_GO",
        },
    ]
    repeated_blocker_count = sum(
        1
        for item in repeated_observations
        if item["decision"] == "NO_GO" and item["valid_completion_item_count"] == 0
    )
    blocked_threshold_met = repeated_blocker_count >= 3

    private_diagnostic = {
        "schema_version": "kmfa.private.v014_processed_value_source_map_completion_blocker_audit.v1",
        "classification": "private_blocker_audit_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_blocker_audit_private_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "private_template_ref": "private_runtime_only",
        "item_statuses": private_item_statuses,
        "counts": counts,
        "repeated_blocker_count": repeated_blocker_count,
        "blocked_threshold_met": blocked_threshold_met,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    private_diagnostic_gitignored = _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH)

    summary = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_blocker_audit_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_blocker_audit_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "blocker_condition": BLOCKER,
        "consecutive_goal_turn_blocker_count": repeated_blocker_count,
        "blocked_audit_threshold_met": blocked_threshold_met,
        "goal_status_recommendation": "blocked" if blocked_threshold_met else "continue",
        "prior_application_phase_id": application_summary.get("phase_id"),
        "prior_application_decision": application_summary.get("decision"),
        "prior_application_valid_completion_item_count": application_summary.get("valid_completion_item_count"),
        "prior_readiness_phase_id": readiness_summary.get("phase_id"),
        "prior_readiness_decision": readiness_summary.get("decision"),
        "prior_readiness_valid_completion_item_count": readiness_summary.get("valid_completion_item_count"),
        "private_template_gitignored": private_template_gitignored,
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": private_diagnostic_gitignored,
        "completion_template_item_count": counts["template_item_count"],
        "completion_template_unique_target_slot_count": counts["unique_target_slot_count"],
        "pending_selected_action_count": counts["pending_selected_action_count"],
        "valid_completion_item_count": counts["valid_completion_item_count"],
        "invalid_or_pending_completion_item_count": counts["invalid_or_pending_completion_item_count"],
        "authorized_completion_record_supplied": False,
        "authorized_processed_value_fingerprint_count": 0,
        "source_map_completion_reapplication_ready": False,
        "source_map_completion_reapplication_performed": False,
        "source_map_records_applied_count": 0,
        "processed_value_materialization_replay_ready": False,
        "processed_value_materialization_replay_performed": False,
        "raw_processed_structural_key_intersection_count": 0,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "processed_data_reconciliation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "NO_GO",
        "diagnostic_conclusion": BLOCKER,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_blocker_audit_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_blocker_audit_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": "NO_GO",
        "status": STATUS,
        "diagnostic_conclusion": BLOCKER,
        "consecutive_goal_turn_blocker_count": repeated_blocker_count,
        "blocked_audit_threshold_met": blocked_threshold_met,
        "completion_template_item_count": summary["completion_template_item_count"],
        "pending_selected_action_count": summary["pending_selected_action_count"],
        "valid_completion_item_count": 0,
        "source_map_completion_reapplication_ready": False,
        "source_map_completion_reapplication_performed": False,
        "source_map_records_applied_count": 0,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "raw_to_processed_value_comparison_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "blocked_until": "authorized_processed_value_sources_supplied_and_validated",
    }
    manifest = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_blocker_audit_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_blocker_audit_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_commit": _git_output(["rev-parse", "HEAD"]),
        "source_refs": {
            "application_summary": APPLICATION_SUMMARY_PATH.as_posix(),
            "readiness_summary": READINESS_SUMMARY_PATH.as_posix(),
            "private_completion_template": "gitignored_private_runtime_only",
            "private_blocker_audit_diagnostic": "gitignored_private_runtime_only",
        },
        "summary": summary,
        "go_no_go": go_no_go,
        "validation": {
            "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_blocker_audit.py --require-private-diagnostic",
            "focused_unit_test": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_blocker_audit -q",
        },
    }

    for path, payload in [
        (SUMMARY_PATH, summary),
        (GO_NO_GO_PATH, go_no_go),
        (MANIFEST_PATH, manifest),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MANIFEST_PATH, manifest),
    ]:
        _write_json(path, payload)

    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Processed Value Source-map Completion Blocker Audit",
                "",
                f"- task_id: `{TASK_ID}`",
                f"- status: `{STATUS}`",
                "- decision: `NO_GO`",
                f"- blocker_condition: `{BLOCKER}`",
                f"- consecutive_goal_turn_blocker_count: `{repeated_blocker_count}`",
                f"- blocked_audit_threshold_met: `{str(blocked_threshold_met).lower()}`",
                f"- completion_template_item_count: `{summary['completion_template_item_count']}`",
                f"- pending_selected_action_count: `{summary['pending_selected_action_count']}`",
                f"- valid_completion_item_count: `{summary['valid_completion_item_count']}`",
                "- source_map_completion_reapplication_ready: `false`",
                "- source_map_records_applied_count: `0`",
                "- comparable_value_pair_count: `0`",
                "- business_value_consistency_verified: `false`",
                f"- next_required_input: `{NEXT_REQUIRED_INPUT}`",
                "",
                "This audit records a repeated authorization blocker only. It does not access, transform, compare, upload, reinstall or execute business data.",
            ]
        )
        + "\n",
    )
    _write_text(
        OWNER_PACKET_PATH,
        "\n".join(
            [
                "# Owner / Agent Blocker Packet",
                "",
                "- current_result: the private completion template still has no valid authorized processed value source evidence.",
                "- required_action: an owner or authorized delegate must fill the private completion template with allowed source evidence for each target slot.",
                "- codex_boundary: Codex cannot invent or infer those source records from public evidence.",
                "- public_safety: do not paste private source names, workbook names, tab names, field/header plaintext, row/cell values or business values into public artifacts.",
                "- next_codex_phase_after_valid_fill: source-map completion reapplication as a separate one-phase run.",
            ]
        )
        + "\n",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go / No-Go",
                "",
                "- decision: `NO_GO`",
                f"- reason: `{BLOCKER}`",
                f"- blocked_audit_threshold_met: `{str(blocked_threshold_met).lower()}`",
                "- blocked_next_steps: `source-map reapplication; materialization replay; raw-to-processed comparison; reconciliation; lineage; formal report; GitHub upload; app reinstall; business execution`",
            ]
        )
        + "\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Processed Value Source-map Completion Blocker Audit Test Results",
                "",
                "- status: `pending_final_validation`",
                f"- task_id: `{TASK_ID}`",
                "- validator: `pending_final_validation`",
                "- focused_unit_test: `pending_final_validation`",
                "- governance_validator: `pending_final_validation`",
                "- raw_private_scan: `pending_final_validation`",
                "- secret_scan: `pending_final_validation`",
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
                "| Risk | Control | Status |",
                "|---|---|---|",
                "| Blocker audit could be mistaken for data alignment completion. | Go/No-Go remains NO_GO and all downstream execution flags remain false. | controlled |",
                "| Private template details could leak into public evidence. | Public artifacts contain aggregate counts and refs only; private diagnostic remains ignored. | controlled |",
                "| Raw/private data could be modified. | Raw access and mutation flags remain false; this phase does not touch raw data. | controlled |",
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
                "1. Revert this phase commit.",
                "2. Remove ignored private blocker audit diagnostic if desired.",
                "3. Do not modify, move, delete, normalize or copy raw source files as part of rollback.",
            ]
        )
        + "\n",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    print(
        "Generated KMFA v0.1.4 processed value source-map completion blocker audit "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"valid_items={manifest['summary']['valid_completion_item_count']}, "
        f"blocked_threshold_met={manifest['summary']['blocked_audit_threshold_met']})"
    )


if __name__ == "__main__":
    main()
