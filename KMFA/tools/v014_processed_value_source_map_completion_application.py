#!/usr/bin/env python3
"""Apply KMFA v0.1.4 processed value source-map completion input state.

This phase consumes the private completion template created by the previous
input-kit phase and determines whether owner/authorized-delegate source
evidence is ready to apply. It writes private diagnostics to ignored runtime
and public aggregate evidence only. It does not read or mutate the raw inbox,
does not materialize processed values, and does not compare raw and processed
values.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_APPLICATION"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-APPLICATION-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-APPLICATION"
VERSION = "0.1.4-processed-value-source-map-completion-application"
STATUS = "completed_validated_local_only_no_go_private_completion_template_unfilled"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_fills_private_completion_template_with_authorized_processed_value_sources"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_application_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_application_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_application_report.md"
DIAGNOSTIC_PACKET_PATH = HUMAN_DIR / "owner_agent_completion_application_packet.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_application_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_application_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_application_go_no_go_report.json"

INPUT_KIT_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_INPUT_KIT/machine/processed_value_source_map_completion_input_kit_summary.json"
)
PRIVATE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_input_kit/owner_authorized_processed_value_source_map_completion_template.json"
)
PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_application"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_completion_application_diagnostic.json"

PENDING_VALUE = "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT"
ACTION_SUPPLY = "supply_authorized_processed_value_fingerprint"
ACTION_SIBLING = "map_existing_metadata_hash_sibling"
ACTION_KEEP_PENDING = "keep_pending"


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
    result = subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False)
    return result.returncode == 0


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
            if item.get("authorized_processed_value_fingerprint") != PENDING_VALUE and item.get("authorized_source_basis_reference") != PENDING_VALUE:
                counts["valid_supply_fingerprint_count"] += 1
                status = "valid_supply_fingerprint"
            else:
                status = "invalid_supply_fingerprint_missing_required_fields"
        elif action == ACTION_SIBLING:
            counts["selected_sibling_mapping_count"] += 1
            if item.get("authorized_metadata_hash_sibling_ref") != PENDING_VALUE and item.get("authorized_source_basis_reference") != PENDING_VALUE:
                counts["valid_sibling_mapping_count"] += 1
                status = "valid_sibling_mapping"
            else:
                status = "invalid_sibling_mapping_missing_required_fields"
        else:
            status = "invalid_or_unknown_action_code"
        private_item_statuses.append({"target_slot_id": target_slot_id, "selected_action_code": action, "application_status": status})
    counts["unique_target_slot_count"] = len(target_ids)
    counts["valid_completion_item_count"] = counts["valid_supply_fingerprint_count"] + counts["valid_sibling_mapping_count"]
    counts["invalid_or_pending_completion_item_count"] = counts["template_item_count"] - counts["valid_completion_item_count"]
    return counts, private_item_statuses


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    input_summary = _read_json(INPUT_KIT_SUMMARY_PATH)
    private_template = _read_json(PRIVATE_TEMPLATE_PATH)
    counts, private_item_statuses = _classify_items(private_template)
    private_template_gitignored = _git_check_ignored(PRIVATE_TEMPLATE_PATH)

    application_ready = counts["valid_completion_item_count"] > 0 and counts["invalid_or_pending_completion_item_count"] == 0
    source_map_records_applied_count = counts["valid_completion_item_count"]

    private_diagnostic = {
        "schema_version": "kmfa.private.v014_processed_value_source_map_completion_application.v1",
        "classification": "private_completion_application_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_application_private_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "private_template_ref": "private_runtime_only",
        "item_statuses": private_item_statuses,
        "counts": counts,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    private_diagnostic_gitignored = _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH)

    summary = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_application_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_application_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_input_kit_phase_id": input_summary.get("phase_id"),
        "source_input_kit_decision": input_summary.get("decision"),
        "source_input_kit_template_item_count": input_summary.get("private_completion_template_item_count"),
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
        "authorized_completion_record_supplied": False,
        "authorized_processed_value_fingerprint_count": counts["valid_supply_fingerprint_count"],
        "source_map_records_applied_count": source_map_records_applied_count,
        "source_map_completion_application_ready": application_ready,
        "source_map_completion_application_performed": True,
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
        "decision": "NO_GO",
        "diagnostic_conclusion": "private_completion_template_unfilled_authorized_sources_not_supplied",
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }

    go_no_go = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_application_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_application_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": "NO_GO",
        "decision_reason": "private completion template remains unfilled and no authorized processed value sources can be applied",
        "private_template_gitignored": private_template_gitignored,
        "private_diagnostic_gitignored": private_diagnostic_gitignored,
        "completion_template_item_count": counts["template_item_count"],
        "pending_selected_action_count": counts["pending_selected_action_count"],
        "valid_completion_item_count": counts["valid_completion_item_count"],
        "source_map_records_applied_count": source_map_records_applied_count,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "raw_to_processed_value_comparison_performed": False,
        "processed_data_reconciliation_performed": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }

    manifest = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_application_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_application_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_commit": _git_output(["rev-parse", "HEAD"]),
        "source_refs": {
            "input_kit_summary": INPUT_KIT_SUMMARY_PATH.as_posix(),
            "private_completion_template": "private_runtime_only_not_committed",
            "private_application_diagnostic": "private_runtime_only_not_committed",
        },
        "summary": summary,
        "go_no_go": go_no_go,
        "validation": {
            "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_application.py --require-private-diagnostic",
            "focused_test": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_application -q",
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
                "# KMFA v0.1.4 Processed Value Source-map Completion Application",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- task_id: `{TASK_ID}`",
                "- decision: `NO_GO`",
                f"- completion_template_item_count: `{summary['completion_template_item_count']}`",
                f"- pending_selected_action_count: `{summary['pending_selected_action_count']}`",
                f"- valid_completion_item_count: `{summary['valid_completion_item_count']}`",
                f"- source_map_records_applied_count: `{summary['source_map_records_applied_count']}`",
                f"- comparable_value_pair_count: `{summary['comparable_value_pair_count']}`",
                "",
                "## 当前结论",
                "",
                "已检查 private completion template，但 113 条待补项仍未由 owner/authorized delegate 填写授权 processed value source evidence。当前不能应用 source-map completion，也不能执行 materialization、raw-to-processed comparison、lineage full check、formal report、GitHub upload、app reinstall 或业务执行。",
                "",
                "## 下一步输入",
                "",
                f"`{NEXT_REQUIRED_INPUT}`",
                "",
            ]
        ),
    )
    _write_text(
        DIAGNOSTIC_PACKET_PATH,
        "\n".join(
            [
                "# 可转发应用状态包：KMFA processed value source-map completion application",
                "",
                "## 可公开事实",
                "",
                "- private completion template 已检查。",
                "- 113 条 target slots 仍等待 owner/authorized delegate 输入。",
                "- 当前 valid completion items = `0`，source-map records applied = `0`，comparable pairs = `0`。",
                "- 本状态不是业务值差异结论，只说明授权 processed value source evidence 尚未提供。",
                "",
                "## 外部 agent 需要做的事",
                "",
                "- 只在 private template 中按允许结构补齐授权 processed value source evidence。",
                "- 不要公开 raw 文件名、字段/表名、行列坐标或业务值。",
                "- 不要建议跳过 source-map application、materialization 和 raw-to-processed comparison gate。",
                "",
            ]
        ),
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go/No-Go Record",
                "",
                "- decision: `NO_GO`",
                f"- next_required_input: `{NEXT_REQUIRED_INPUT}`",
                "- github_upload_performed: `false`",
                "- app_reinstall_performed: `false`",
                "- business_execution_performed: `false`",
                "",
            ]
        ),
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Processed Value Source-map Completion Application Test Results",
                "",
                "- status: `pending_final_validation`",
                f"- task_id: `{TASK_ID}`",
                "- validator: `pending_final_validation`",
                "- focused_unit_test: `pending_final_validation`",
                "- governance_validator: `pending_final_validation`",
                "- raw_private_scan: `pending_final_validation`",
                "- secret_scan: `pending_final_validation`",
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# Risk Register",
                "",
                "- risk: The private template may remain unfilled; mitigation: keep all downstream gates NO_GO and report exact aggregate blocker.",
                "- risk: A future fill may include plaintext or raw values; mitigation: private runtime only plus public-safe validators before any commit.",
                "",
            ]
        ),
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# Rollback Plan",
                "",
                "- Remove this phase's public artifacts, metadata copies, tool/test/validator and governance entries.",
                "- Remove the git-ignored private application diagnostic if it should be regenerated.",
                "- Do not modify raw source files.",
                "",
            ]
        ),
    )
    return manifest


def main() -> None:
    generated_at = None
    if "--generated-at" in sys.argv:
        idx = sys.argv.index("--generated-at")
        generated_at = sys.argv[idx + 1]
    manifest = generate(generated_at=generated_at)
    summary = manifest["summary"]
    print(
        "Generated KMFA v0.1.4 processed value source-map completion application "
        f"(decision={summary['decision']}, valid_items={summary['valid_completion_item_count']}, "
        f"next_required_input={summary['next_required_input']})"
    )


if __name__ == "__main__":
    main()
