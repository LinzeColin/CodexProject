#!/usr/bin/env python3
"""Recheck KMFA v0.1.4 processed value source-map completion readiness.

This phase is intentionally narrow: it rereads the git-ignored private
completion template and the previous public application summary, then records
whether source-map completion can be safely reapplied. It does not read or
mutate the raw inbox, does not write source-map records, does not materialize
processed values, and does not compare raw and processed values.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_READINESS_RECHECK"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-READINESS-RECHECK-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-READINESS-RECHECK"
VERSION = "0.1.4-processed-value-source-map-completion-readiness-recheck"
STATUS = "completed_validated_local_only_no_go_private_completion_template_still_unfilled"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_fills_private_completion_template_with_authorized_processed_value_sources"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_readiness_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_readiness_recheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_readiness_recheck_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_readiness_recheck_report.md"
OWNER_PACKET_PATH = HUMAN_DIR / "owner_agent_readiness_recheck_packet.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_readiness_recheck_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_readiness_recheck_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_readiness_recheck_go_no_go_report.json"

APPLICATION_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_APPLICATION/machine/processed_value_source_map_completion_application_summary.json"
)
PRIVATE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_input_kit/owner_authorized_processed_value_source_map_completion_template.json"
)
PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_readiness_recheck"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_readiness_recheck_diagnostic.json"

PENDING_VALUE = "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT"
ACTION_KEEP_PENDING = "keep_pending"
ACTION_SUPPLY = "supply_authorized_processed_value_fingerprint"
ACTION_SIBLING = "map_existing_metadata_hash_sibling"


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
        "raw_data_root_readonly_policy_active": True,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_digest_or_value_fingerprint_performed_by_this_phase": False,
        "raw_inbox_write_performed_by_this_phase": False,
        "raw_inbox_delete_performed_by_this_phase": False,
        "raw_inbox_move_performed_by_this_phase": False,
        "raw_inbox_rename_performed_by_this_phase": False,
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


def _classify_items(template: dict[str, Any]) -> tuple[dict[str, int], list[dict[str, Any]]]:
    items = template.get("completion_items", [])
    if not isinstance(items, list):
        raise ValueError("completion_items must be a list")
    counts = {
        "template_item_count": len(items),
        "unique_target_slot_count": 0,
        "pending_selected_action_count": 0,
        "selected_keep_pending_count": 0,
        "selected_supply_fingerprint_count": 0,
        "selected_sibling_mapping_count": 0,
        "valid_supply_fingerprint_count": 0,
        "valid_sibling_mapping_count": 0,
        "valid_completion_item_count": 0,
        "invalid_or_pending_completion_item_count": 0,
    }
    target_ids: set[str] = set()
    private_item_statuses: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("completion item must be an object")
        target_slot_id = item.get("target_slot_id")
        if not isinstance(target_slot_id, str) or not target_slot_id:
            raise ValueError("completion item missing target_slot_id")
        target_ids.add(target_slot_id)
        action = item.get("selected_action_code")
        status = "pending_owner_or_authorized_delegate_input"
        if action == PENDING_VALUE:
            counts["pending_selected_action_count"] += 1
        elif action == ACTION_KEEP_PENDING:
            counts["selected_keep_pending_count"] += 1
            status = "explicit_keep_pending"
        elif action == ACTION_SUPPLY:
            counts["selected_supply_fingerprint_count"] += 1
            if item.get("authorized_processed_value_fingerprint") not in {None, "", PENDING_VALUE} and item.get(
                "authorized_source_basis_reference"
            ) not in {None, "", PENDING_VALUE}:
                counts["valid_supply_fingerprint_count"] += 1
                status = "valid_supply_fingerprint"
            else:
                status = "invalid_supply_fingerprint_missing_required_fields"
        elif action == ACTION_SIBLING:
            counts["selected_sibling_mapping_count"] += 1
            if item.get("authorized_metadata_hash_sibling_ref") not in {None, "", PENDING_VALUE} and item.get(
                "authorized_source_basis_reference"
            ) not in {None, "", PENDING_VALUE}:
                counts["valid_sibling_mapping_count"] += 1
                status = "valid_sibling_mapping"
            else:
                status = "invalid_sibling_mapping_missing_required_fields"
        else:
            status = "invalid_or_unknown_action_code"
        private_item_statuses.append(
            {
                "target_slot_id": target_slot_id,
                "selected_action_code": action,
                "readiness_status": status,
            }
        )
    counts["unique_target_slot_count"] = len(target_ids)
    counts["valid_completion_item_count"] = counts["valid_supply_fingerprint_count"] + counts["valid_sibling_mapping_count"]
    counts["invalid_or_pending_completion_item_count"] = counts["template_item_count"] - counts["valid_completion_item_count"]
    return counts, private_item_statuses


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    application_summary = _read_json(APPLICATION_SUMMARY_PATH)
    private_template = _read_json(PRIVATE_TEMPLATE_PATH)
    counts, private_item_statuses = _classify_items(private_template)
    private_template_gitignored = _git_check_ignored(PRIVATE_TEMPLATE_PATH)

    reapplication_ready = counts["valid_completion_item_count"] > 0 and counts["invalid_or_pending_completion_item_count"] == 0
    decision = "GO" if reapplication_ready else "NO_GO"
    status = "ready_for_separate_reapplication_phase" if reapplication_ready else STATUS
    diagnostic_conclusion = (
        "authorized_completion_items_supplied_ready_for_separate_reapplication"
        if reapplication_ready
        else "private_completion_template_still_unfilled_authorized_sources_not_supplied"
    )

    private_diagnostic = {
        "schema_version": "kmfa.private.v014_processed_value_source_map_completion_readiness_recheck.v1",
        "classification": "private_readiness_recheck_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_readiness_recheck_private_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "private_template_ref": "private_runtime_only",
        "item_statuses": private_item_statuses,
        "counts": counts,
        "reapplication_ready": reapplication_ready,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    private_diagnostic_gitignored = _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH)

    summary = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_readiness_recheck_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_readiness_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": status,
        "generated_at": timestamp,
        "source_application_phase_id": application_summary.get("phase_id"),
        "source_application_decision": application_summary.get("decision"),
        "source_application_valid_completion_item_count": application_summary.get("valid_completion_item_count"),
        "source_application_source_map_records_applied_count": application_summary.get("source_map_records_applied_count"),
        "private_template_gitignored": private_template_gitignored,
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": private_diagnostic_gitignored,
        "completion_template_item_count": counts["template_item_count"],
        "completion_template_unique_target_slot_count": counts["unique_target_slot_count"],
        "pending_selected_action_count": counts["pending_selected_action_count"],
        "selected_keep_pending_count": counts["selected_keep_pending_count"],
        "selected_supply_fingerprint_count": counts["selected_supply_fingerprint_count"],
        "selected_sibling_mapping_count": counts["selected_sibling_mapping_count"],
        "valid_supply_fingerprint_count": counts["valid_supply_fingerprint_count"],
        "valid_sibling_mapping_count": counts["valid_sibling_mapping_count"],
        "valid_completion_item_count": counts["valid_completion_item_count"],
        "invalid_or_pending_completion_item_count": counts["invalid_or_pending_completion_item_count"],
        "authorized_completion_record_supplied": counts["valid_completion_item_count"] > 0,
        "authorized_processed_value_fingerprint_count": counts["valid_supply_fingerprint_count"],
        "source_map_completion_reapplication_ready": reapplication_ready,
        "source_map_completion_reapplication_performed": False,
        "source_map_records_applied_count": 0,
        "processed_value_materialization_replay_ready": False,
        "processed_value_materialization_replay_performed": False,
        "staged_processed_value_fingerprint_count": 0,
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
        "decision": decision,
        "diagnostic_conclusion": diagnostic_conclusion,
        "next_required_input": NEXT_REQUIRED_INPUT if not reapplication_ready else "run_separate_source_map_completion_reapplication_phase",
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_readiness_recheck_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_readiness_recheck_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": decision,
        "status": status,
        "diagnostic_conclusion": diagnostic_conclusion,
        "completion_template_item_count": summary["completion_template_item_count"],
        "pending_selected_action_count": summary["pending_selected_action_count"],
        "valid_completion_item_count": summary["valid_completion_item_count"],
        "source_map_completion_reapplication_ready": reapplication_ready,
        "source_map_completion_reapplication_performed": False,
        "source_map_records_applied_count": 0,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "raw_to_processed_value_comparison_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": summary["next_required_input"],
        "blocked_until": "authorized_processed_value_sources_supplied_and_validated" if not reapplication_ready else "separate_reapplication_phase",
    }
    manifest = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_readiness_recheck_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_readiness_recheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": status,
        "generated_at": timestamp,
        "source_commit": _git_output(["rev-parse", "HEAD"]),
        "source_refs": {
            "application_summary": APPLICATION_SUMMARY_PATH.as_posix(),
            "private_completion_template": "gitignored_private_runtime_only",
            "private_readiness_recheck_diagnostic": "gitignored_private_runtime_only",
        },
        "summary": summary,
        "go_no_go": go_no_go,
        "validation": {
            "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_readiness_recheck.py --require-private-diagnostic",
            "focused_unit_test": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_readiness_recheck -q",
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
                "# KMFA v0.1.4 Processed Value Source-map Completion Readiness Recheck",
                "",
                f"- task_id: `{TASK_ID}`",
                f"- status: `{status}`",
                f"- decision: `{decision}`",
                f"- completion_template_item_count: `{summary['completion_template_item_count']}`",
                f"- pending_selected_action_count: `{summary['pending_selected_action_count']}`",
                f"- valid_completion_item_count: `{summary['valid_completion_item_count']}`",
                f"- source_map_completion_reapplication_ready: `{str(reapplication_ready).lower()}`",
                f"- source_map_completion_reapplication_performed: `false`",
                f"- source_map_records_applied_count: `0`",
                f"- comparable_value_pair_count: `0`",
                f"- business_value_consistency_verified: `false`",
                f"- next_required_input: `{summary['next_required_input']}`",
                "",
                "This phase rechecks the ignored private completion template only. It does not read, list, hash, copy, modify, delete, move, rename or normalize the raw inbox.",
            ]
        )
        + "\n",
    )
    _write_text(
        OWNER_PACKET_PATH,
        "\n".join(
            [
                "# Owner / Agent Readiness Recheck Packet",
                "",
                "- current_result: private completion template still has no valid authorized processed value source evidence.",
                "- required_action: fill the private completion template with one allowed action per target slot.",
                "- allowed_actions_source: use the git-ignored private template; do not copy private action payloads into public evidence.",
                "- public_safety: keep source names, workbook names, tab names, field/header plaintext, row/cell values and business values out of public evidence.",
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
                f"- decision: `{decision}`",
                f"- reason: `{diagnostic_conclusion}`",
                "- blocked_next_steps: `source-map reapplication; materialization replay; raw-to-processed comparison; reconciliation; lineage; formal report; GitHub upload; app reinstall; business execution`",
            ]
        )
        + "\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Processed Value Source-map Completion Readiness Recheck Test Results",
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
                "| Readiness recheck could be mistaken for source-map completion. | Go/No-Go remains NO_GO and reapplication_performed=false. | controlled |",
                "| Private template details could leak into public evidence. | Public artifacts contain aggregate counts and refs only; private diagnostic remains git-ignored. | controlled |",
                "| Raw/private data could be modified. | Raw inbox access and mutation flags remain false; this phase does not touch raw data. | controlled |",
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
                "2. Remove ignored private readiness recheck diagnostic if desired.",
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
        "Generated KMFA v0.1.4 processed value source-map completion readiness recheck "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"valid_items={manifest['summary']['valid_completion_item_count']}, "
        f"reapplication_ready={manifest['summary']['source_map_completion_reapplication_ready']})"
    )


if __name__ == "__main__":
    main()
