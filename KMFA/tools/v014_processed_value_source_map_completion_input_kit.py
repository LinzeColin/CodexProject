#!/usr/bin/env python3
"""Generate KMFA v0.1.4 processed value source-map completion input kit.

This phase prepares a private-only template for the 113 keep-pending target
slots that still need owner/authorized-delegate processed value source evidence.
It publishes only aggregate public evidence. It does not read or mutate the raw
inbox, does not materialize processed values, and does not compare raw and
processed values.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_INPUT_KIT"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-INPUT-KIT-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-INPUT-KIT"
VERSION = "0.1.4-processed-value-source-map-completion-input-kit"
STATUS = "completed_validated_local_only_no_go_completion_input_kit_ready"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_fills_private_completion_template_with_authorized_processed_value_sources"

ALLOWED_ACTION_CODES = [
    "supply_authorized_processed_value_fingerprint",
    "map_existing_metadata_hash_sibling",
    "keep_pending",
]

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_input_kit_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_input_kit_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_input_kit_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_input_kit_report.md"
DIAGNOSTIC_PACKET_PATH = HUMAN_DIR / "owner_agent_completion_packet.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_input_kit_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_input_kit_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_input_kit_go_no_go_report.json"

BLOCKER_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_RAW_PROCESSED_ALIGNMENT_BLOCKER_REPORT/machine/raw_processed_alignment_blocker_summary.json"
)
WORKLIST_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_private_processed_value_source_map_gap_resolution/private_owner_authorized_fill_worklist.json"
)
ACTIVE_RECORD_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_private_processed_value_source_map_owner_authorized_fill_application/active_owner_authorized_fill_record.json"
)
PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_input_kit"
PRIVATE_TEMPLATE_PATH = PRIVATE_OUTPUT_DIR / "owner_authorized_processed_value_source_map_completion_template.json"


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
        "private_completion_template_committed": False,
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


def _active_keep_pending_count(active_record: dict[str, Any]) -> int:
    items = active_record.get("fill_items", [])
    if not isinstance(items, list):
        raise ValueError("active fill record fill_items must be a list")
    return sum(1 for item in items if isinstance(item, dict) and item.get("action_code") == "keep_pending")


def _build_completion_items(worklist: dict[str, Any], active_record: dict[str, Any]) -> list[dict[str, Any]]:
    worklist_items = worklist.get("owner_worklist_items", [])
    active_items = active_record.get("fill_items", [])
    if not isinstance(worklist_items, list):
        raise ValueError("owner worklist items must be a list")
    if not isinstance(active_items, list):
        raise ValueError("active fill record items must be a list")
    active_by_slot = {
        item.get("target_slot_id"): item
        for item in active_items
        if isinstance(item, dict) and isinstance(item.get("target_slot_id"), str)
    }
    completion_items: list[dict[str, Any]] = []
    for item in worklist_items:
        if not isinstance(item, dict):
            raise ValueError("owner worklist item must be an object")
        target_slot_id = item.get("target_slot_id")
        if not isinstance(target_slot_id, str) or not target_slot_id:
            raise ValueError("owner worklist item missing target_slot_id")
        active_item = active_by_slot.get(target_slot_id, {})
        completion_items.append(
            {
                "target_slot_id": target_slot_id,
                "current_active_action_code": active_item.get("action_code", "missing_active_record_item"),
                "current_fill_status": item.get("fill_status"),
                "context_group": item.get("context_group"),
                "source_root_id": item.get("source_root_id"),
                "record_ref_hash": item.get("record_ref_hash"),
                "target_key_ref_hash": item.get("target_key_ref_hash"),
                "source_artifact_ref_hash": item.get("source_artifact_ref_hash"),
                "private_processed_ref_hash": item.get("private_processed_ref_hash"),
                "private_processed_ref_shape_hash": item.get("private_processed_ref_shape_hash"),
                "allowed_action_codes": ALLOWED_ACTION_CODES,
                "selected_action_code": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "authorized_processed_value_fingerprint": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "authorized_metadata_hash_sibling_ref": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "authorized_source_basis_reference": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "owner_or_authorized_delegate_role": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "authorization_timestamp": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "basis_note": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "public_commit_policy": "do_not_commit_this_private_template_or_business_values",
            }
        )
    return completion_items


def _build_private_template(
    *,
    generated_at: str,
    blocker_summary: dict[str, Any],
    worklist: dict[str, Any],
    active_record: dict[str, Any],
) -> dict[str, Any]:
    completion_items = _build_completion_items(worklist, active_record)
    return {
        "schema_version": "kmfa.private.v014_processed_value_source_map_completion_input_kit.v1",
        "classification": "private_owner_authorized_processed_value_source_map_completion_template_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_input_template",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_blocker_phase_id": blocker_summary.get("phase_id"),
        "source_blocker_decision": blocker_summary.get("decision"),
        "allowed_action_codes": ALLOWED_ACTION_CODES,
        "required_output_after_fill": "owner_or_authorized_delegate_active_fill_record_with_authorized_processed_value_sources",
        "completion_policy": {
            "owner_or_authorized_delegate_must_choose_one_allowed_action_per_item": True,
            "do_not_commit_this_private_template": True,
            "do_not_enter_raw_business_values_into_public_repo": True,
            "do_not_modify_raw_source_files": True,
            "materialization_requires_separate_validated_phase_after_fill": True,
        },
        "completion_item_count": len(completion_items),
        "completion_items": completion_items,
    }


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    blocker_summary = _read_json(BLOCKER_SUMMARY_PATH)
    worklist = _read_json(WORKLIST_PATH)
    active_record = _read_json(ACTIVE_RECORD_PATH)

    private_template = _build_private_template(
        generated_at=timestamp,
        blocker_summary=blocker_summary,
        worklist=worklist,
        active_record=active_record,
    )
    _write_json(PRIVATE_TEMPLATE_PATH, private_template)

    completion_items = private_template["completion_items"]
    target_slot_ids = [item["target_slot_id"] for item in completion_items]
    private_template_gitignored = _git_check_ignored(PRIVATE_TEMPLATE_PATH)
    active_keep_pending_count = _active_keep_pending_count(active_record)

    summary = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_input_kit_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_input_kit_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_blocker_phase_id": blocker_summary.get("phase_id"),
        "source_blocker_decision": blocker_summary.get("decision"),
        "source_blocker_comparable_value_pair_count": blocker_summary.get("comparable_value_pair_count"),
        "source_blocker_next_required_input": blocker_summary.get("next_required_input"),
        "source_worklist_item_count": len(worklist.get("owner_worklist_items", [])),
        "active_fill_record_item_count": len(active_record.get("fill_items", [])),
        "active_keep_pending_item_count": active_keep_pending_count,
        "private_completion_template_written": True,
        "private_completion_template_gitignored": private_template_gitignored,
        "private_completion_template_item_count": len(completion_items),
        "private_completion_template_unique_target_slot_count": len(set(target_slot_ids)),
        "allowed_completion_action_count": len(ALLOWED_ACTION_CODES),
        "completion_ready_for_owner_or_agent_fill": True,
        "authorized_completion_record_supplied": False,
        "authorized_processed_value_fingerprint_count": 0,
        "metadata_digest_sibling_mapping_count": 0,
        "source_map_records_applied_count": 0,
        "staged_processed_value_fingerprint_count": 0,
        "raw_processed_structural_key_intersection_count": 0,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "processed_data_reconciliation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "processed_value_materialization_replay_performed": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "NO_GO",
        "diagnostic_conclusion": "completion_input_template_ready_authorized_sources_not_supplied",
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }

    go_no_go = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_input_kit_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_input_kit_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": "NO_GO",
        "decision_reason": "private completion template is ready but authorized processed value sources have not been supplied",
        "completion_ready_for_owner_or_agent_fill": True,
        "private_completion_template_written": True,
        "private_completion_template_gitignored": private_template_gitignored,
        "private_completion_template_item_count": len(completion_items),
        "authorized_processed_value_fingerprint_count": 0,
        "source_map_records_applied_count": 0,
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
        "schema_version": "kmfa.v014_processed_value_source_map_completion_input_kit_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_input_kit_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_commit": _git_output(["rev-parse", "HEAD"]),
        "source_refs": {
            "blocker_summary": BLOCKER_SUMMARY_PATH.as_posix(),
            "private_owner_worklist": "private_runtime_only_not_committed",
            "private_active_keep_pending_record": "private_runtime_only_not_committed",
            "private_completion_template": "private_runtime_only_not_committed",
        },
        "summary": summary,
        "go_no_go": go_no_go,
        "validation": {
            "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_input_kit.py --require-private-template",
            "focused_test": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_input_kit -q",
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
                "# KMFA v0.1.4 Processed Value Source-map Completion Input Kit",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- task_id: `{TASK_ID}`",
                "- decision: `NO_GO`",
                f"- source_worklist_item_count: `{summary['source_worklist_item_count']}`",
                f"- active_keep_pending_item_count: `{summary['active_keep_pending_item_count']}`",
                f"- private_completion_template_item_count: `{summary['private_completion_template_item_count']}`",
                f"- private_completion_template_gitignored: `{str(private_template_gitignored).lower()}`",
                "- authorized_processed_value_fingerprint_count: `0`",
                "- comparable_value_pair_count: `0`",
                "",
                "## 当前结论",
                "",
                "private-only completion template 已生成，供 owner/authorized delegate 或其他 agent 按固定结构补齐授权 processed value source evidence。当前仍未提供授权 fingerprint 或 sibling mapping，因此不能执行 materialization、raw-to-processed comparison、lineage full check、formal report、GitHub upload、app reinstall 或业务执行。",
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
                "# 可转发补齐包：KMFA processed value source-map completion",
                "",
                "## 可公开事实",
                "",
                "- 当前有 `113` 个 keep-pending target slots。",
                "- private-only completion template 已在本机 git-ignored runtime 生成。",
                "- public evidence 只包含 counts/status/gate，不包含原始文件、字段、表名、行列或业务值。",
                "",
                "## 填写规则",
                "",
                "- 每个 target slot 必须选择一个 allowed action code。",
                "- 若选择 `supply_authorized_processed_value_fingerprint`，必须提供授权 processed value fingerprint 和依据 ref。",
                "- 若选择 sibling mapping，必须提供可复核的 private sibling ref。",
                "- 若无法授权，继续 `keep_pending`，不得伪造值。",
                "",
                "## 禁止事项",
                "",
                "- 不要把 raw 文件、Excel/PDF/zip、字段明文、表名、行列坐标或业务值放入公开仓库。",
                "- 不要把本补齐包解释为已经完成 raw-to-processed comparison。",
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
                "# KMFA v0.1.4 Processed Value Source-map Completion Input Kit Test Results",
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
                "- risk: Owner or authorized delegate may still not supply value-source evidence; mitigation: keep all downstream gates NO_GO.",
                "- risk: A filled private template may include raw/plaintext values; mitigation: validator must reject public artifacts and private template remains git-ignored.",
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
                "- Remove the git-ignored private completion template if it should be regenerated.",
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
        "Generated KMFA v0.1.4 processed value source-map completion input kit "
        f"(decision={summary['decision']}, template_items={summary['private_completion_template_item_count']}, "
        f"next_required_input={summary['next_required_input']})"
    )


if __name__ == "__main__":
    main()
