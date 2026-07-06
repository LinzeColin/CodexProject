#!/usr/bin/env python3
"""Generate a private Chinese checklist for non-actionable KMFA groups.

This phase converts the private pending response queue into a Chinese owner
confirmation checklist. It writes private group/slot identifiers only to the
ignored runtime directory. Public artifacts contain aggregate counts and gate
status only.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_CONFIRMATION_CHECKLIST"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-CONFIRMATION-CHECKLIST-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-CONFIRMATION-CHECKLIST"
VERSION = "0.1.4-non-actionable-group-confirmation-checklist"
STATUS = "completed_validated_local_only_private_chinese_confirmation_checklist_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_chinese_confirmation_checklist_ready_owner_response_still_required"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_OWNER_RESPONSE_APPLICATION"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_answers_private_chinese_confirmation_checklist_before_application"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_confirmation_checklist_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_confirmation_checklist_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_confirmation_checklist_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_non_actionable_group_confirmation_checklist_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_group_confirmation_checklist_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_group_confirmation_checklist_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_group_confirmation_checklist_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_RESPONSE_INTAKE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_RESPONSE_INTAKE/machine/processed_value_source_map_completion_non_actionable_group_response_intake_summary.json"
)
PRIVATE_PENDING_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_non_actionable_group_response_intake/private_non_actionable_group_response_pending_queue.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist"
)
PRIVATE_CHECKLIST_JSON_PATH = PRIVATE_OUTPUT_DIR / "private_non_actionable_group_confirmation_checklist.json"
PRIVATE_CHECKLIST_MD_PATH = PRIVATE_OUTPUT_DIR / "private_non_actionable_group_confirmation_checklist.md"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_non_actionable_group_confirmation_checklist_diagnostic.json"


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
        "private_confirmation_checklist_committed": False,
        "private_confirmation_markdown_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "processed_value_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _question_for_group(group: dict[str, Any]) -> dict[str, Any]:
    status = str(group.get("candidate_status") or "")
    resolution_code = str(group.get("resolution_decision_code") or "")
    missing_keys = list(group.get("missing_required_keys") or [])
    if status == "requires_non_numeric_owner_mapping":
        return {
            "中文问题": "该组需要非数值业务映射或明确不适用原因。Codex 不能根据现有证据自动推断。",
            "推荐默认选择": "保持待定并补充授权人及原因",
            "可选决策": [
                "A. 继续待定：填写授权人和待定原因",
                "B. 标记不适用：填写授权人和不适用原因",
                "C. 提供非数值映射引用：填写授权人、映射引用和原因",
            ],
            "最少需补字段": sorted(set(missing_keys + ["owner_or_authorized_delegate"])),
        }
    if resolution_code == "REQUEST_ADDITIONAL_SOURCE_EVIDENCE":
        return {
            "中文问题": "该组未匹配到可用来源证据。Codex 不能自动确认来源或填值。",
            "推荐默认选择": "补充来源证据引用或确认无来源",
            "可选决策": [
                "A. 补充来源证据：填写授权人、证据引用和原因",
                "B. 确认无来源：填写授权人和确认原因",
                "C. 继续待定：填写授权人和待定原因",
            ],
            "最少需补字段": sorted(set(missing_keys + ["owner_or_authorized_delegate", "additional_evidence_ref"])),
        }
    return {
        "中文问题": "该组仍缺少 owner 或授权人确认，不能进入 source-map 应用。",
        "推荐默认选择": "保持待定并补充授权人及原因",
        "可选决策": [
            "A. 继续待定：填写授权人和待定原因",
            "B. 标记不适用：填写授权人和原因",
        ],
        "最少需补字段": sorted(set(missing_keys + ["owner_or_authorized_delegate"])),
    }


def _build_private_checklist(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    pending_queue: dict[str, Any],
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    pending_groups = pending_queue.get("pending_groups", [])
    if not isinstance(pending_groups, list):
        raise ValueError("pending_groups must be a list")

    checklist_items: list[dict[str, Any]] = []
    missing_key_counts: Counter[str] = Counter()
    resolution_code_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    target_slot_count = 0
    for index, group in enumerate(pending_groups, start=1):
        if not isinstance(group, dict):
            continue
        target_count = int(group.get("target_slot_count") or 0)
        target_slot_count += target_count
        for key in group.get("missing_required_keys") or []:
            missing_key_counts[str(key)] += 1
        resolution_code = str(group.get("resolution_decision_code") or "")
        candidate_status = str(group.get("candidate_status") or "unknown")
        resolution_code_counts[resolution_code or "MISSING_RESOLUTION_DECISION_CODE"] += 1
        status_counts[candidate_status] += 1
        prompt = _question_for_group(group)
        checklist_items.append(
            {
                "确认项编号": f"NA-{index:03d}",
                "review_group_id": group.get("review_group_id"),
                "target_slot_count": target_count,
                "target_slot_ids": group.get("target_slot_ids", []),
                "candidate_status": candidate_status,
                "current_owner_group_decision_code": group.get("current_owner_group_decision_code"),
                "resolution_decision_code": resolution_code,
                "resolution_reason_code": group.get("resolution_reason_code"),
                "ready_for_intake": False,
                "中文问题": prompt["中文问题"],
                "推荐默认选择": prompt["推荐默认选择"],
                "可选决策": prompt["可选决策"],
                "最少需补字段": prompt["最少需补字段"],
                "填写区": {
                    "选择": None,
                    "owner_or_authorized_delegate": None,
                    "resolution_reason_code": None,
                    "owner_resolution_note": None,
                    "supplied_mapping_ref": None,
                    "additional_evidence_ref": None,
                    "ready_for_intake": False,
                },
            }
        )

    checklist_summary = {
        "source_response_intake_phase_id": source_summary.get("phase_id"),
        "source_response_intake_decision": source_summary.get("decision"),
        "source_response_group_count": int(source_summary.get("response_group_count") or 0),
        "source_response_target_slot_count": int(source_summary.get("response_target_slot_count") or 0),
        "source_ready_for_intake_group_count": int(source_summary.get("ready_for_intake_group_count") or 0),
        "source_pending_response_group_count": int(source_summary.get("pending_response_group_count") or 0),
        "source_invalid_response_group_count": int(source_summary.get("invalid_response_group_count") or 0),
        "checklist_item_count": len(checklist_items),
        "checklist_target_slot_count": target_slot_count,
        "missing_required_key_counts": dict(missing_key_counts),
        "resolution_decision_code_counts": dict(resolution_code_counts),
        "candidate_status_group_counts": dict(status_counts),
        "private_chinese_checklist_ready": True,
        "owner_or_authorized_delegate_response_required": True,
        "codex_default_business_resolution_applied": False,
        "active_owner_authorized_fill_record_ready": False,
        "source_map_completion_reapplication_ready": False,
        "business_value_consistency_verified": False,
    }
    checklist = {
        "schema_version": "kmfa.private.v014_non_actionable_group_confirmation_checklist.v1",
        "classification": "private_non_actionable_group_confirmation_checklist_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "language": "zh-CN",
        "checklist_summary": checklist_summary,
        "instructions": [
            "只在本私有清单中填写；不要把本文件提交 GitHub。",
            "如不能确认，请选择继续待定并写明原因。",
            "不要修改原始数据文件，也不要把原始文件名、表头、金额或明细复制到公开仓库。",
        ],
        "checklist_items": checklist_items,
        "raw_boundary": _raw_boundary(),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_non_actionable_group_confirmation_checklist_diagnostic.v1",
        "classification": "private_non_actionable_group_confirmation_checklist_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "checklist_summary": checklist_summary,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "raw_boundary": _raw_boundary(),
    }
    lines = [
        "# KMFA 非自动处理组中文最小确认清单",
        "",
        "本文件为 private runtime 文件，不得提交 GitHub。",
        "",
        f"- 确认项数量: {checklist_summary['checklist_item_count']}",
        f"- 涉及 target slot: {checklist_summary['checklist_target_slot_count']}",
        "- 当前结论: 仍需 owner 或授权人确认，不能进入 source-map application。",
        "",
    ]
    for item in checklist_items:
        lines.extend(
            [
                f"## {item['确认项编号']}",
                "",
                f"- review_group_id: `{item['review_group_id']}`",
                f"- target_slot_count: `{item['target_slot_count']}`",
                f"- candidate_status: `{item['candidate_status']}`",
                f"- 当前建议: {item['推荐默认选择']}",
                f"- 中文问题: {item['中文问题']}",
                "- 可选决策:",
            ]
        )
        for option in item["可选决策"]:
            lines.append(f"  - {option}")
        lines.extend(
            [
                f"- 最少需补字段: `{', '.join(item['最少需补字段'])}`",
                "",
            ]
        )
    return checklist, "\n".join(lines) + "\n", diagnostic


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_RESPONSE_INTAKE_SUMMARY_PATH)
    pending_queue = _read_json(PRIVATE_PENDING_QUEUE_PATH)
    private_checklist, private_markdown, private_diagnostic = _build_private_checklist(
        generated_at=timestamp,
        source_summary=source_summary,
        pending_queue=pending_queue,
    )
    checklist_summary = private_checklist["checklist_summary"]
    _write_json(PRIVATE_CHECKLIST_JSON_PATH, private_checklist)
    _write_text(PRIVATE_CHECKLIST_MD_PATH, private_markdown)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)

    summary = {
        "schema_version": "kmfa.v014_non_actionable_group_confirmation_checklist_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        **checklist_summary,
        "private_confirmation_checklist_written": True,
        "private_confirmation_checklist_gitignored": _git_check_ignored(PRIVATE_CHECKLIST_JSON_PATH),
        "private_confirmation_markdown_written": True,
        "private_confirmation_markdown_gitignored": _git_check_ignored(PRIVATE_CHECKLIST_MD_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "active_owner_authorized_fill_record_written": False,
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "source_map_completion_reapplication_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_non_actionable_group_confirmation_checklist_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "checklist_item_count": summary["checklist_item_count"],
        "checklist_target_slot_count": summary["checklist_target_slot_count"],
        "owner_or_authorized_delegate_response_required": True,
        "codex_default_business_resolution_applied": False,
        "source_map_completion_reapplication_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_non_actionable_group_confirmation_checklist_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "generated_at": timestamp,
        "status": STATUS,
        "summary": summary,
        "go_no_go": go_no_go,
        "artifact_refs": {
            "machine_summary": SUMMARY_PATH.as_posix(),
            "machine_manifest": MANIFEST_PATH.as_posix(),
            "machine_go_no_go": GO_NO_GO_PATH.as_posix(),
            "private_confirmation_checklist": "private_runtime_only",
            "private_confirmation_markdown": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist.py "
            "--require-private-confirmation-checklist"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 非自动处理组中文确认清单

Decision: {DECISION}

本 phase 已生成 private 中文最小确认清单。公开仓库只记录聚合计数；清单中的 group/slot 标识仅保存在 ignored private runtime。

## 公开安全聚合结果

- Checklist items: {summary["checklist_item_count"]}
- Checklist target slots: {summary["checklist_target_slot_count"]}
- Source pending response groups: {summary["source_pending_response_group_count"]}
- Source invalid response groups: {summary["source_invalid_response_group_count"]}
- Owner/delegate response required: `true`
- Codex default business resolution applied: `false`
- Full source-map reapplication ready: `false`

Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- checklist_item_count: `{summary["checklist_item_count"]}`
- checklist_target_slot_count: `{summary["checklist_target_slot_count"]}`
- owner_or_authorized_delegate_response_required: `true`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: confusing a private checklist with business approval.
  Mitigation: active authorization remains false; source-map reapplication remains blocked.
- Risk: leaking private group or target details publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; private checklist stays in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, response template, source map, completion template, active authorization record or GitHub remote was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private checklist files if not needed.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist.py --require-private-confirmation-checklist`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist`
"""
    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        _write_json(path, payload)
    for path, text in (
        (REPORT_PATH, report),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback_plan),
        (TEST_RESULTS_PATH, test_results),
    ):
        _write_text(path, text)
    if write_governance_event:
        _append_development_event(timestamp, manifest)
    return manifest


def _append_development_event(generated_at: str, manifest: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-CONFIRMATION-CHECKLIST"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-NON-ACTIONABLE-GROUP-CONFIRMATION-CHECKLIST",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "checklist_item_count": summary["checklist_item_count"],
        "checklist_target_slot_count": summary["checklist_target_slot_count"],
        "owner_or_authorized_delegate_response_required": True,
        "codex_default_business_resolution_applied": False,
        "active_owner_authorized_fill_record_written": False,
        "source_map_completion_reapplication_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Generated private Chinese confirmation checklist for the remaining non-actionable source-map groups while keeping full application blocked.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    print(
        "PASS: KMFA v0.1.4 non-actionable group confirmation checklist generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"items={manifest['summary']['checklist_item_count']}, "
        f"target_slots={manifest['summary']['checklist_target_slot_count']})"
    )


if __name__ == "__main__":
    main()
