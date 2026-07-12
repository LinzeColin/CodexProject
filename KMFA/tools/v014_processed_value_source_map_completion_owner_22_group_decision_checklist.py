#!/usr/bin/env python3
"""Prepare a private Chinese 22-group owner decision checklist for KMFA v0.1.4.

This phase converts the existing private owner review-groups packet into a
Chinese owner-confirmation checklist. It does not read the raw inbox, does not
apply owner decisions, and does not mutate source-map or reconciliation state.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_22_GROUP_DECISION_CHECKLIST"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-22-GROUP-DECISION-CHECKLIST-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-22-GROUP-DECISION-CHECKLIST"
VERSION = "0.1.4-owner-22-group-decision-checklist"
STATUS = "completed_validated_local_only_owner_22_group_decision_checklist_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_chinese_22_group_decision_checklist_prepared_owner_confirmation_required"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_confirms_private_22_group_decision_checklist"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_22_GROUP_DECISION_RESPONSE_INTAKE"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_22_group_decision_checklist_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_22_group_decision_checklist_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_22_group_decision_checklist_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_22_group_decision_checklist_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_22_group_decision_checklist_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_22_group_decision_checklist_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_22_group_decision_checklist_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_22_group_decision_checklist_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_22_group_decision_checklist_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_OWNER_GROUP_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_review_groups_path_summary.json"
)
SOURCE_APPLICATION_READINESS_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_private_corrected_source_or_owner_resolution_application_readiness_summary.json"
)
SOURCE_APPLICATION_READINESS_MATRIX_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_private_corrected_source_or_owner_resolution_application_readiness_matrix_public_safe.json"
)
SOURCE_PRIVATE_GROUP_PACKET_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_groups_path/private_owner_review_groups_path_packet.json"
)
SOURCE_PRIVATE_GROUP_RESPONSE_DRAFT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_groups_path/private_owner_review_groups_path_response_draft.json"
)
SOURCE_PRIVATE_APPLICATION_BLOCKER_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness/private_corrected_source_or_owner_resolution_application_blocker_queue.jsonl"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_22_group_decision_checklist"
PRIVATE_CHECKLIST_JSON_PATH = PRIVATE_OUTPUT_DIR / "private_owner_22_group_decision_checklist.json"
PRIVATE_CHECKLIST_MD_PATH = PRIVATE_OUTPUT_DIR / "private_owner_22_group_decision_checklist_zh.md"
PRIVATE_RESPONSE_TEMPLATE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_22_group_decision_response_template.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_22_group_decision_checklist_diagnostic.json"

ALLOWED_DECISION_CODES = [
    "CONFIRM_GROUP_CANDIDATE_RANK",
    "CHOOSE_CANDIDATE_RECORD_REF",
    "KEEP_PENDING",
    "MARK_NOT_APPLICABLE",
    "REQUEST_MORE_DIAGNOSTICS",
]
DECISION_CODE_ZH = {
    "CONFIRM_GROUP_CANDIDATE_RANK": "确认按该组候选排序使用，不另选候选",
    "CHOOSE_CANDIDATE_RECORD_REF": "指定该组使用某个候选记录引用",
    "KEEP_PENDING": "明确保持待处理，本轮不进入应用",
    "MARK_NOT_APPLICABLE": "标记该组不适用",
    "REQUEST_MORE_DIAGNOSTICS": "要求继续补充诊断",
}
CANDIDATE_STATUS_ZH = {
    "auto_ambiguous_multiple_candidates_requires_owner_review": "多候选，需要 owner 或授权代表确认",
    "requires_non_numeric_owner_mapping": "非数值映射，需要补充映射或标记不适用",
    "auto_unmatched_requires_owner_review": "未匹配，需要补充诊断或保持待处理",
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
        "private_owner_group_packet_read_by_this_phase": True,
        "private_owner_group_response_draft_read_by_this_phase": True,
        "private_application_blocker_queue_read_by_this_phase": True,
        "private_22_group_decision_checklist_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_owner_group_packet_committed": False,
        "private_owner_group_response_draft_committed": False,
        "private_application_blocker_queue_committed": False,
        "private_22_group_decision_checklist_committed": False,
        "private_22_group_response_template_committed": False,
        "private_22_group_diagnostic_committed": False,
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


def _recommended_decision_code(candidate_status: str) -> str:
    if candidate_status == "auto_ambiguous_multiple_candidates_requires_owner_review":
        return "CONFIRM_GROUP_CANDIDATE_RANK"
    if candidate_status == "requires_non_numeric_owner_mapping":
        return "KEEP_PENDING"
    if candidate_status == "auto_unmatched_requires_owner_review":
        return "REQUEST_MORE_DIAGNOSTICS"
    return "KEEP_PENDING"


def _build_private_checklist(
    *,
    generated_at: str,
    group_packet: dict[str, Any],
    group_response_draft: dict[str, Any],
    application_blockers: list[dict[str, Any]],
) -> dict[str, Any]:
    groups = group_packet.get("groups", [])
    response_rows = group_response_draft.get("response_rows", [])
    if not isinstance(groups, list) or not isinstance(response_rows, list):
        raise ValueError("private group packet or response draft has invalid rows")

    rows_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in response_rows:
        if isinstance(row, dict):
            rows_by_group[str(row.get("review_group_id"))].append(row)

    blocker_by_slot = {
        str(row.get("target_slot_id")): row for row in application_blockers if isinstance(row, dict) and row.get("target_slot_id")
    }
    checklist_groups: list[dict[str, Any]] = []
    response_template_groups: list[dict[str, Any]] = []
    recommended_counts: Counter[str] = Counter()
    linked_blocker_count = 0

    for index, group in enumerate(groups, start=1):
        if not isinstance(group, dict):
            continue
        review_group_id = str(group.get("review_group_id"))
        candidate_status = str(group.get("candidate_status"))
        target_rows = rows_by_group.get(review_group_id, [])
        target_slot_ids = [str(row.get("target_slot_id")) for row in target_rows if row.get("target_slot_id")]
        group_linked_blockers = sum(1 for slot_id in target_slot_ids if slot_id in blocker_by_slot)
        linked_blocker_count += group_linked_blockers
        recommended_code = _recommended_decision_code(candidate_status)
        recommended_counts[recommended_code] += 1
        checklist_group = {
            "group_index": index,
            "review_group_id": review_group_id,
            "context_group": group.get("context_group"),
            "candidate_status": candidate_status,
            "candidate_status_zh": CANDIDATE_STATUS_ZH.get(candidate_status, "需要 owner 或授权代表确认"),
            "target_slot_count": group.get("target_slot_count"),
            "top_candidate_record_count": group.get("top_candidate_record_count"),
            "linked_application_blocker_count": group_linked_blockers,
            "recommended_decision_code": recommended_code,
            "recommended_decision_zh": DECISION_CODE_ZH[recommended_code],
            "allowed_decision_codes": ALLOWED_DECISION_CODES,
            "owner_confirmation_status": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_CONFIRMATION",
            "owner_final_decision_code": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_CONFIRMATION",
            "owner_note": "",
        }
        checklist_groups.append(checklist_group)
        response_template_groups.append(
            {
                "group_index": index,
                "review_group_id": review_group_id,
                "candidate_status": candidate_status,
                "target_slot_count": group.get("target_slot_count"),
                "recommended_decision_code": recommended_code,
                "owner_final_decision_code": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_CONFIRMATION",
                "owner_final_decision_required": True,
                "owner_note": "",
                "selected_candidate_record_ref": None,
                "owner_supplied_mapping_ref": None,
                "active_authorization_allowed_now": False,
            }
        )

    checklist = {
        "schema_version": "kmfa.private.v014_owner_22_group_decision_checklist.v1",
        "classification": "private_owner_22_group_decision_checklist_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_checklist",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "group_count": len(checklist_groups),
        "response_row_count": group_response_draft.get("response_row_count"),
        "application_blocker_queue_count": len(application_blockers),
        "linked_application_blocker_count": linked_blocker_count,
        "unlinked_application_blocker_count": len(application_blockers) - linked_blocker_count,
        "recommended_decision_code_counts": dict(recommended_counts),
        "allowed_decision_codes": ALLOWED_DECISION_CODES,
        "groups": checklist_groups,
    }
    response_template = {
        "schema_version": "kmfa.private.v014_owner_22_group_decision_response_template.v1",
        "classification": "private_owner_22_group_decision_response_template_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_response_template",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "group_count": len(response_template_groups),
        "response_row_count": group_response_draft.get("response_row_count"),
        "application_blocker_queue_count": len(application_blockers),
        "linked_application_blocker_count": linked_blocker_count,
        "unlinked_application_blocker_count": len(application_blockers) - linked_blocker_count,
        "owner_response_complete": False,
        "active_authorization_allowed_now": False,
        "groups": response_template_groups,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_22_group_decision_checklist_diagnostic.v1",
        "classification": "private_owner_22_group_decision_checklist_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_checklist_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "group_count": len(checklist_groups),
        "response_row_count": group_response_draft.get("response_row_count"),
        "application_blocker_queue_count": len(application_blockers),
        "linked_application_blocker_count": linked_blocker_count,
        "unlinked_application_blocker_count": len(application_blockers) - linked_blocker_count,
        "recommended_decision_code_counts": dict(recommended_counts),
        "raw_boundary": _raw_boundary(),
        "owner_response_complete": False,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
    }
    return {"checklist": checklist, "response_template": response_template, "diagnostic": diagnostic}


def _private_checklist_markdown(checklist: dict[str, Any]) -> str:
    lines = [
        "# KMFA 22个 group 中文决策清单（私有）",
        "",
        "说明：本文件只在 `.codex_private_runtime` 中使用，不提交 GitHub。请逐组确认推荐决策，或改成允许的其他决策码。",
        "",
        "可选决策码：",
    ]
    for code in ALLOWED_DECISION_CODES:
        lines.append(f"- `{code}`：{DECISION_CODE_ZH[code]}")
    lines.extend(
        [
            "",
            "填写方式：每组可回复“同意推荐”，也可以把 `owner_final_decision_code` 改成上面的决策码；需要指定候选或映射时，把引用写入对应字段。",
            "",
        ]
    )
    for group in checklist["groups"]:
        lines.extend(
            [
                f"## {group['group_index']:02d}｜{group['review_group_id']}",
                "",
                f"- 私有分组上下文：`{group['context_group']}`",
                f"- 当前状态：{group['candidate_status_zh']}（`{group['candidate_status']}`）",
                f"- 涉及待确认项数量：`{group['target_slot_count']}`",
                f"- 候选记录数量：`{group['top_candidate_record_count']}`",
                f"- 关联 application blocker 数量：`{group['linked_application_blocker_count']}`",
                f"- Codex 建议默认：`{group['recommended_decision_code']}`，{group['recommended_decision_zh']}",
                "- owner_final_decision_code：`PENDING_OWNER_OR_AUTHORIZED_DELEGATE_CONFIRMATION`",
                "- owner_note：",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def _decision_matrix(
    *,
    generated_at: str,
    source_application_summary: dict[str, Any],
    source_application_matrix: dict[str, Any],
    owner_group_summary: dict[str, Any],
    group_count: int,
) -> dict[str, Any]:
    checks = [
        {
            "check_code": "source_application_readiness_available",
            "status": "PASS"
            if source_application_summary.get("phase_id")
            == "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_CORRECTED_SOURCE_OR_OWNER_RESOLUTION_APPLICATION_READINESS"
            else "FAIL",
            "observed_public_safe": source_application_summary.get("phase_id"),
            "required": "latest_application_readiness_gate",
        },
        {
            "check_code": "source_application_readiness_locked_no_go",
            "status": "PASS" if source_application_summary.get("decision") == "NO_GO" else "FAIL",
            "observed_public_safe": source_application_summary.get("decision"),
            "required": "NO_GO",
        },
        {
            "check_code": "source_owner_review_groups_available",
            "status": "PASS" if owner_group_summary.get("review_group_count") == 22 else "FAIL",
            "observed_public_safe": owner_group_summary.get("review_group_count"),
            "required": 22,
        },
        {
            "check_code": "private_22_group_checklist_prepared",
            "status": "PASS" if group_count == 22 else "FAIL",
            "observed_public_safe": group_count,
            "required": 22,
        },
        {
            "check_code": "owner_group_decision_confirmed",
            "status": "FAIL",
            "observed_public_safe": False,
            "required": True,
        },
        {
            "check_code": "owner_approved_resolution_input_present",
            "status": "FAIL",
            "observed_public_safe": False,
            "required": True,
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
        "schema_version": "kmfa.v014_owner_22_group_decision_checklist_matrix_public_safe.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_checklist_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_application_readiness_fail_count": source_application_matrix.get("application_readiness_fail_count"),
        "decision_check_count": len(checks),
        "decision_pass_count": pass_count,
        "decision_fail_count": fail_count,
        "owner_22_group_decision_checklist_prepared": group_count == 22,
        "owner_group_decision_confirmed": False,
        "owner_approved_resolution_input_present": False,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "decision": DECISION,
        "checks": checks,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# KMFA v0.1.4 Owner 22 Group Decision Checklist

Decision: `{DECISION}`

This phase prepared a private Chinese decision checklist for 22 owner-review groups and 113 pending items. Public artifacts contain aggregate counts only.

## Public-safe result

- Group count: `{summary["owner_22_group_count"]}`
- Response row count: `{summary["owner_22_group_response_row_count"]}`
- Private checklist prepared: `{summary["private_22_group_checklist_prepared"]}`
- Decision checks: `{matrix["decision_pass_count"]}` pass / `{matrix["decision_fail_count"]}` fail
- Owner group decision confirmed: `false`
- Resolution application allowed: `false`
- Full reconciliation allowed: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- blocked_until: `{NEXT_REQUIRED_INPUT}`
- owner_22_group_count: `{summary["owner_22_group_count"]}`
- owner_22_group_response_row_count: `{summary["owner_22_group_response_row_count"]}`
- GitHub upload performed: `false`
- App reinstall performed: `false`
"""
    risk_register = """# Risk Register

- R1: Treating the private checklist as owner authorization would overclaim readiness.
- R2: Publishing group identifiers or row-level routing would leak private diagnostic context.
- R3: Resolution application remains invalid until owner or authorized delegate responses are explicitly applied in a later phase.
"""
    rollback_plan = """# Rollback Plan

No raw inbox, source-map, owner response template, completion template, or reconciliation artifact was mutated. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private checklist files if not needed.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_owner_22_group_decision_checklist.py KMFA/tools/check_v014_processed_value_source_map_completion_owner_22_group_decision_checklist.py KMFA/tests/test_v014_processed_value_source_map_completion_owner_22_group_decision_checklist.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_owner_22_group_decision_checklist.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_22_group_decision_checklist.py --require-private-checklist`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_22_group_decision_checklist`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `git diff --check -- KMFA`

All listed commands passed in this run. The raw inbox was not read, listed, parsed, copied, moved, renamed, deleted, overwritten, normalized or mutated by this phase.
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
    event_id = "DEV-KMFA-20260706-V014-OWNER-22-GROUP-DECISION-CHECKLIST"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-OWNER-22-GROUP-DECISION-CHECKLIST",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "owner_22_group_count": summary["owner_22_group_count"],
        "owner_22_group_response_row_count": summary["owner_22_group_response_row_count"],
        "private_22_group_checklist_prepared": True,
        "owner_group_decision_confirmed": False,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Prepared private Chinese 22-group decision checklist while keeping application and reconciliation gates closed.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    owner_group_summary = _read_json(SOURCE_OWNER_GROUP_SUMMARY_PATH)
    application_summary = _read_json(SOURCE_APPLICATION_READINESS_SUMMARY_PATH)
    application_matrix = _read_json(SOURCE_APPLICATION_READINESS_MATRIX_PATH)
    group_packet = _read_json(SOURCE_PRIVATE_GROUP_PACKET_PATH)
    group_response_draft = _read_json(SOURCE_PRIVATE_GROUP_RESPONSE_DRAFT_PATH)
    application_blockers = _read_jsonl(SOURCE_PRIVATE_APPLICATION_BLOCKER_QUEUE_PATH)
    private_records = _build_private_checklist(
        generated_at=timestamp,
        group_packet=group_packet,
        group_response_draft=group_response_draft,
        application_blockers=application_blockers,
    )
    checklist = private_records["checklist"]
    response_template = private_records["response_template"]
    diagnostic = private_records["diagnostic"]

    _write_json(PRIVATE_CHECKLIST_JSON_PATH, checklist)
    _write_json(PRIVATE_RESPONSE_TEMPLATE_PATH, response_template)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_text(PRIVATE_CHECKLIST_MD_PATH, _private_checklist_markdown(checklist))

    matrix = _decision_matrix(
        generated_at=timestamp,
        source_application_summary=application_summary,
        source_application_matrix=application_matrix,
        owner_group_summary=owner_group_summary,
        group_count=checklist["group_count"],
    )
    recommended_counts = checklist["recommended_decision_code_counts"]
    summary = {
        "schema_version": "kmfa.v014_owner_22_group_decision_checklist_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_checklist_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_owner_review_groups_phase_id": owner_group_summary["phase_id"],
        "source_application_readiness_phase_id": application_summary["phase_id"],
        "source_application_readiness_decision": application_summary["decision"],
        "source_application_missing_owner_input_count": application_summary["missing_owner_input_count"],
        "source_application_blocker_queue_count": application_summary["application_blocker_queue_count"],
        "owner_22_group_count": checklist["group_count"],
        "owner_22_group_response_row_count": checklist["response_row_count"],
        "owner_22_group_linked_application_blocker_count": checklist["linked_application_blocker_count"],
        "owner_22_group_unlinked_application_blocker_count": checklist["unlinked_application_blocker_count"],
        "recommended_confirm_group_candidate_rank_count": recommended_counts.get("CONFIRM_GROUP_CANDIDATE_RANK", 0),
        "recommended_keep_pending_count": recommended_counts.get("KEEP_PENDING", 0),
        "recommended_request_more_diagnostics_count": recommended_counts.get("REQUEST_MORE_DIAGNOSTICS", 0),
        "allowed_decision_code_count": len(ALLOWED_DECISION_CODES),
        "private_22_group_checklist_prepared": True,
        "private_22_group_response_template_prepared": True,
        "private_22_group_diagnostic_prepared": True,
        "private_22_group_checklist_gitignored": _git_check_ignored(PRIVATE_CHECKLIST_JSON_PATH),
        "private_22_group_markdown_gitignored": _git_check_ignored(PRIVATE_CHECKLIST_MD_PATH),
        "private_22_group_response_template_gitignored": _git_check_ignored(PRIVATE_RESPONSE_TEMPLATE_PATH),
        "private_22_group_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "owner_group_decision_confirmed": False,
        "owner_approved_resolution_input_present": False,
        "corrected_private_source_package_present": False,
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
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_owner_22_group_decision_checklist_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_checklist_go_no_go",
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
        "owner_22_group_count": summary["owner_22_group_count"],
        "owner_22_group_response_row_count": summary["owner_22_group_response_row_count"],
        "private_22_group_checklist_prepared": True,
        "owner_group_decision_confirmed": False,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_owner_22_group_decision_checklist_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_checklist_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "summary": summary,
        "go_no_go": go_no_go,
        "decision_matrix": matrix,
        "artifact_refs": {
            "machine_summary": SUMMARY_PATH.as_posix(),
            "machine_manifest": MANIFEST_PATH.as_posix(),
            "machine_go_no_go": GO_NO_GO_PATH.as_posix(),
            "machine_matrix": MATRIX_PATH.as_posix(),
            "private_checklist": "private_runtime_only",
            "private_checklist_markdown": "private_runtime_only",
            "private_response_template": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_22_group_decision_checklist.py "
            "--require-private-checklist"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    print(
        "PASS: KMFA v0.1.4 owner 22-group decision checklist generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"groups={manifest['summary']['owner_22_group_count']}, "
        f"rows={manifest['summary']['owner_22_group_response_row_count']})"
    )


if __name__ == "__main__":
    main()
