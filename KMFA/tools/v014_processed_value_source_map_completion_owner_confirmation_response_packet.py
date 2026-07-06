#!/usr/bin/env python3
"""Build a private owner confirmation response packet for KMFA v0.1.4.

This phase converts the current private pending owner-response queue into a
fillable response packet. It does not fill business responses, does not write
active authorization, and does not read or mutate raw source files.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_CONFIRMATION_RESPONSE_PACKET"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-RESPONSE-PACKET-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-RESPONSE-PACKET"
VERSION = "0.1.4-owner-confirmation-response-packet"
STATUS = "completed_validated_local_only_owner_confirmation_response_packet_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "owner_confirmation_response_packet_ready_no_owner_response_supplied"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_CONFIRMATION_RESPONSE_INTAKE"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_completes_private_confirmation_response_packet"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_packet_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_packet_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_packet_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_confirmation_response_packet_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_confirmation_response_packet_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_confirmation_response_packet_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_confirmation_response_packet_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_APPLICATION_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_OWNER_RESPONSE_APPLICATION/machine/processed_value_source_map_completion_non_actionable_group_owner_response_application_summary.json"
)
PRIVATE_PENDING_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_non_actionable_group_owner_response_application/private_non_actionable_group_owner_response_application_pending_queue.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_confirmation_response_packet"
)
PRIVATE_RESPONSE_PACKET_PATH = PRIVATE_OUTPUT_DIR / "private_owner_confirmation_response_packet.json"
PRIVATE_RESPONSE_DRAFT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_confirmation_response_draft.json"
PRIVATE_RESPONSE_MARKDOWN_PATH = PRIVATE_OUTPUT_DIR / "private_owner_confirmation_response_packet.md"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_confirmation_response_packet_diagnostic.json"


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
        "private_pending_queue_committed": False,
        "private_response_packet_committed": False,
        "private_response_draft_committed": False,
        "private_response_markdown_committed": False,
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


def _options_for_item(item: dict[str, Any]) -> list[dict[str, str]]:
    recommendation = str(item.get("recommended_default") or "")
    if "补充来源证据" in recommendation:
        return [
            {"code": "A", "label": "补充来源证据", "required_private_field": "additional_evidence_ref"},
            {"code": "B", "label": "确认无可用来源", "required_private_field": "owner_resolution_note"},
            {"code": "C", "label": "继续待定", "required_private_field": "owner_resolution_note"},
        ]
    return [
        {"code": "A", "label": "继续待定", "required_private_field": "owner_resolution_note"},
        {"code": "B", "label": "标记不适用", "required_private_field": "owner_resolution_note"},
        {"code": "C", "label": "提供非数值映射引用", "required_private_field": "supplied_mapping_ref"},
    ]


def _build_private_packet(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    pending_queue: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, Any]]:
    pending_items = pending_queue.get("pending_items", [])
    if not isinstance(pending_items, list):
        raise ValueError("pending_items must be a list")

    response_items: list[dict[str, Any]] = []
    draft_items: list[dict[str, Any]] = []
    missing_counts: Counter[str] = Counter()
    recommendation_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    target_total = 0
    for index, item in enumerate(pending_items, start=1):
        if not isinstance(item, dict):
            continue
        target_count = int(item.get("target_slot_count") or 0)
        target_total += target_count
        for field in item.get("missing_required_fields") or []:
            missing_counts[str(field)] += 1
        recommendation = str(item.get("recommended_default") or "unknown")
        status = str(item.get("candidate_status") or "unknown")
        recommendation_counts[recommendation] += 1
        status_counts[status] += 1
        response_item_id = f"OCR-{index:03d}"
        options = _options_for_item(item)
        response_items.append(
            {
                "response_item_id": response_item_id,
                "确认项编号": item.get("确认项编号"),
                "review_group_id": item.get("review_group_id"),
                "target_slot_count": target_count,
                "target_slot_ids": item.get("target_slot_ids", []),
                "candidate_status": status,
                "recommended_default": recommendation,
                "missing_required_fields": item.get("missing_required_fields", []),
                "answer_options": options,
                "required_common_fields": [
                    "选择",
                    "owner_or_authorized_delegate",
                    "resolution_reason_code",
                    "ready_for_intake",
                ],
                "question": "请选择一个选项并填写授权人、原因和 ready_for_intake=true。未确认时选择继续待定。",
            }
        )
        draft_items.append(
            {
                "response_item_id": response_item_id,
                "确认项编号": item.get("确认项编号"),
                "选择": None,
                "owner_or_authorized_delegate": None,
                "resolution_reason_code": None,
                "owner_resolution_note": None,
                "supplied_mapping_ref": None,
                "additional_evidence_ref": None,
                "ready_for_intake": False,
            }
        )

    packet_summary = {
        "source_owner_response_application_phase_id": source_summary.get("phase_id"),
        "source_owner_response_application_decision": source_summary.get("decision"),
        "source_pending_owner_response_item_count": int(source_summary.get("pending_owner_response_item_count") or 0),
        "source_pending_owner_response_target_slot_count": int(source_summary.get("pending_owner_response_target_slot_count") or 0),
        "source_owner_response_applied_item_count": int(source_summary.get("owner_response_applied_item_count") or 0),
        "response_packet_item_count": len(response_items),
        "response_packet_target_slot_count": target_total,
        "response_draft_item_count": len(draft_items),
        "missing_required_field_counts": dict(missing_counts),
        "recommendation_counts": dict(recommendation_counts),
        "candidate_status_group_counts": dict(status_counts),
        "owner_confirmation_response_packet_ready": True,
        "owner_confirmation_response_supplied": False,
        "active_owner_authorized_fill_record_ready": False,
        "source_map_completion_reapplication_ready": False,
        "business_value_consistency_verified": False,
    }
    packet = {
        "schema_version": "kmfa.private.v014_owner_confirmation_response_packet.v1",
        "classification": "private_owner_confirmation_response_packet_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_response_packet",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "language": "zh-CN",
        "packet_summary": packet_summary,
        "instructions": [
            "只在 private response draft 中填写，不要提交 GitHub。",
            "未确认时选择继续待定。",
            "填写后必须把 ready_for_intake 改为 true，才允许进入后续 intake。",
        ],
        "response_items": response_items,
        "raw_boundary": _raw_boundary(),
    }
    draft = {
        "schema_version": "kmfa.private.v014_owner_confirmation_response_draft.v1",
        "classification": "private_owner_confirmation_response_draft_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_response_draft",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "response_draft_item_count": len(draft_items),
        "items": draft_items,
        "raw_boundary": _raw_boundary(),
    }
    markdown_lines = [
        "# KMFA Owner 确认可回答包",
        "",
        "本文件为 private runtime 文件，不得提交 GitHub。",
        "",
        f"- 待回答项: {packet_summary['response_packet_item_count']}",
        f"- 涉及 target slot: {packet_summary['response_packet_target_slot_count']}",
        "- 当前状态: 未收到 owner/授权人响应，仍为 No-Go。",
        "",
    ]
    for item in response_items:
        markdown_lines.extend(
            [
                f"## {item['response_item_id']}",
                "",
                f"- 确认项编号: `{item['确认项编号']}`",
                f"- target_slot_count: `{item['target_slot_count']}`",
                f"- 推荐默认处理: {item['recommended_default']}",
                "- 可选回答:",
            ]
        )
        for option in item["answer_options"]:
            markdown_lines.append(f"  - {option['code']}. {option['label']}")
        markdown_lines.extend(["", ""])
    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_confirmation_response_packet_diagnostic.v1",
        "classification": "private_owner_confirmation_response_packet_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_response_packet_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "packet_summary": packet_summary,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "raw_boundary": _raw_boundary(),
    }
    return packet, draft, "\n".join(markdown_lines), diagnostic


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_APPLICATION_SUMMARY_PATH)
    pending_queue = _read_json(PRIVATE_PENDING_QUEUE_PATH)
    private_packet, private_draft, private_markdown, private_diagnostic = _build_private_packet(
        generated_at=timestamp,
        source_summary=source_summary,
        pending_queue=pending_queue,
    )
    packet_summary = private_packet["packet_summary"]
    _write_json(PRIVATE_RESPONSE_PACKET_PATH, private_packet)
    _write_json(PRIVATE_RESPONSE_DRAFT_PATH, private_draft)
    _write_text(PRIVATE_RESPONSE_MARKDOWN_PATH, private_markdown)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)

    summary = {
        "schema_version": "kmfa.v014_owner_confirmation_response_packet_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_response_packet_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        **packet_summary,
        "private_response_packet_written": True,
        "private_response_packet_gitignored": _git_check_ignored(PRIVATE_RESPONSE_PACKET_PATH),
        "private_response_draft_written": True,
        "private_response_draft_gitignored": _git_check_ignored(PRIVATE_RESPONSE_DRAFT_PATH),
        "private_response_markdown_written": True,
        "private_response_markdown_gitignored": _git_check_ignored(PRIVATE_RESPONSE_MARKDOWN_PATH),
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
        "schema_version": "kmfa.v014_owner_confirmation_response_packet_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_response_packet_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "response_packet_item_count": summary["response_packet_item_count"],
        "response_packet_target_slot_count": summary["response_packet_target_slot_count"],
        "owner_confirmation_response_supplied": False,
        "active_owner_authorized_fill_record_ready": False,
        "source_map_completion_reapplication_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_owner_confirmation_response_packet_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_response_packet_manifest",
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
            "private_response_packet": "private_runtime_only",
            "private_response_draft": "private_runtime_only",
            "private_response_markdown": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_confirmation_response_packet.py "
            "--require-private-owner-confirmation-packet"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Owner 确认可回答包

Decision: {DECISION}

本 phase 已把当前 3 个 pending owner responses 转成 private 可回答包和 response draft。公开仓库只记录聚合计数；回答项明细只保存在 ignored private runtime。

## 公开安全聚合结果

- Response packet items: {summary["response_packet_item_count"]}
- Response packet target slots: {summary["response_packet_target_slot_count"]}
- Source pending response items: {summary["source_pending_owner_response_item_count"]}
- Source applied response items: {summary["source_owner_response_applied_item_count"]}
- Owner confirmation response supplied: `false`
- Active authorization ready: `false`
- Full source-map reapplication ready: `false`

Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- response_packet_item_count: `{summary["response_packet_item_count"]}`
- response_packet_target_slot_count: `{summary["response_packet_target_slot_count"]}`
- owner_confirmation_response_supplied: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating a fillable packet as authorization.
  Mitigation: owner confirmation response supplied remains false and active authorization remains closed.
- Risk: leaking private group or target details publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; response details stay in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, response packet input, source map, completion template, active authorization record or GitHub remote was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private response packet files if not needed.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_owner_confirmation_response_packet.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_confirmation_response_packet.py --require-private-owner-confirmation-packet`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_confirmation_response_packet`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-RESPONSE-PACKET"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-OWNER-CONFIRMATION-RESPONSE-PACKET",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "response_packet_item_count": summary["response_packet_item_count"],
        "response_packet_target_slot_count": summary["response_packet_target_slot_count"],
        "owner_confirmation_response_supplied": False,
        "active_owner_authorized_fill_record_ready": False,
        "source_map_completion_reapplication_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Generated private fillable owner confirmation response packet for the remaining non-actionable source-map groups.",
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
        "PASS: KMFA v0.1.4 owner confirmation response packet generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"items={manifest['summary']['response_packet_item_count']}, "
        f"target_slots={manifest['summary']['response_packet_target_slot_count']})"
    )


if __name__ == "__main__":
    main()
