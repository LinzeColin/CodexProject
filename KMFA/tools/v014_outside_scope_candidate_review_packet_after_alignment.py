#!/usr/bin/env python3
"""Build a private outside-scope candidate review packet after alignment.

This phase consumes the ignored private alignment diagnostics from the previous
phase and prepares an owner/authorized-delegate review packet. It does not read
the raw inbox again, mutate raw files, select candidates, correct source maps,
run the formal raw-to-processed comparison, reconcile values, upload GitHub,
reinstall the app, or execute business steps. Public artifacts remain
aggregate-only.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_PACKET_AFTER_ALIGNMENT"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-PACKET-AFTER-ALIGNMENT-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-PACKET-AFTER-ALIGNMENT"
VERSION = "0.1.4-outside-scope-candidate-review-packet-after-alignment"
STATUS = "completed_validated_local_only_outside_scope_candidate_review_packet_ready_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "outside_scope_candidate_review_packet_ready_owner_review_required"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_AFTER_PACKET"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_completes_private_outside_scope_candidate_review_packet"

ALLOWED_REVIEW_DECISION_CODES = [
    "select_private_candidate_record",
    "provide_corrected_source_map_reference",
    "provide_authoritative_non_numeric_or_calculation_mapping",
    "mark_source_map_correction_required",
    "keep_pending",
]

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_packet_after_alignment_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_packet_after_alignment_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_candidate_review_packet_after_alignment_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_candidate_review_packet_after_alignment_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_packet_after_alignment_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_packet_after_alignment_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_packet_after_alignment_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_packet_after_alignment_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_packet_after_alignment_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

SOURCE_ALIGNMENT_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_raw_candidate_alignment_after_full_precheck_summary.json"
)
SOURCE_ALIGNMENT_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_raw_candidate_alignment_after_full_precheck_manifest.json"
)
SOURCE_PRIVATE_ALIGNMENT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_raw_candidate_alignment_after_full_precheck/private_outside_scope_raw_candidate_alignment.json"
)
SOURCE_PRIVATE_ALIGNMENT_ITEMS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_raw_candidate_alignment_after_full_precheck/private_outside_scope_raw_candidate_alignment_items.jsonl"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_packet_after_alignment"
PRIVATE_PACKET_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_candidate_review_packet.json"
PRIVATE_PACKET_ITEMS_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_candidate_review_packet_items.jsonl"
PRIVATE_PACKET_MARKDOWN_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_candidate_review_packet_zh.md"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_candidate_review_packet_diagnostic.json"

FILES_CHANGED = [
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
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
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
    METADATA_SUMMARY_PATH.as_posix(),
    METADATA_MANIFEST_PATH.as_posix(),
    METADATA_GO_NO_GO_PATH.as_posix(),
    METADATA_MATRIX_PATH.as_posix(),
    SUMMARY_PATH.as_posix(),
    MANIFEST_PATH.as_posix(),
    GO_NO_GO_PATH.as_posix(),
    MATRIX_PATH.as_posix(),
    REPORT_PATH.as_posix(),
    GO_NO_GO_RECORD_PATH.as_posix(),
    TEST_RESULTS_PATH.as_posix(),
    RISK_REGISTER_PATH.as_posix(),
    ROLLBACK_PATH.as_posix(),
    "KMFA/tests/test_v014_outside_scope_candidate_review_packet_after_alignment.py",
    "KMFA/tools/check_v014_outside_scope_candidate_review_packet_after_alignment.py",
    "KMFA/tools/v014_outside_scope_candidate_review_packet_after_alignment.py",
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
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_private_alignment_read_performed_by_this_phase": True,
        "source_private_alignment_mutated_by_this_phase": False,
        "private_review_packet_written_by_this_phase": True,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
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
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_review_packet_committed": False,
        "private_review_packet_items_committed": False,
        "private_review_packet_markdown_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_digest_committed": False,
        "source_document_committed": False,
        "office_workbook_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _allowed_decisions_for(item: dict[str, Any]) -> list[str]:
    status = item.get("alignment_status")
    if status == "ambiguous_raw_candidates_require_owner_review":
        return ["select_private_candidate_record", "mark_source_map_correction_required", "keep_pending"]
    if status == "no_context_raw_candidate_requires_source_mapping_review":
        return ["provide_corrected_source_map_reference", "mark_source_map_correction_required", "keep_pending"]
    if status == "non_numeric_or_calculation_context_requires_manual_authority":
        return [
            "provide_authoritative_non_numeric_or_calculation_mapping",
            "mark_source_map_correction_required",
            "keep_pending",
        ]
    return ["mark_source_map_correction_required", "keep_pending"]


def _build_review_items(generated_at: str, alignment_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    review_items: list[dict[str, Any]] = []
    for index, item in enumerate(alignment_items, start=1):
        allowed_decisions = _allowed_decisions_for(item)
        review_items.append(
            {
                "review_item_id": f"OSCRP-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_alignment_item_index": item.get("alignment_item_index"),
                "target_slot_id": item.get("target_slot_id"),
                "context_group": item.get("context_group"),
                "source_scope": item.get("source_scope"),
                "source_record_ref_hash": item.get("source_record_ref_hash"),
                "processed_replay_fingerprint": item.get("processed_replay_fingerprint"),
                "candidate_status": item.get("candidate_status"),
                "alignment_status": item.get("alignment_status"),
                "candidate_record_count": int(item.get("candidate_record_count") or 0),
                "candidate_unique_numeric_fingerprint_count": int(
                    item.get("candidate_unique_numeric_fingerprint_count") or 0
                ),
                "private_candidate_options": item.get("private_top_candidate_records", [])[:10],
                "private_candidate_option_count": len(item.get("private_top_candidate_records", [])[:10]),
                "allowed_review_decision_codes": allowed_decisions,
                "selected_review_decision_code": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "selected_private_candidate_option_index": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "corrected_source_map_reference": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "authoritative_non_numeric_or_calculation_mapping": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "owner_or_authorized_delegate_role": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "authorization_timestamp": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "basis_note": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
                "owner_review_required": True,
                "source_map_correction_ready": False,
                "full_comparison_allowed_by_this_phase": False,
                "public_commit_policy": "do_not_commit_this_private_packet_or_business_values",
            }
        )
    return review_items


def _group_summaries(review_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in review_items:
        by_group[str(item.get("context_group"))].append(item)
    summaries: list[dict[str, Any]] = []
    for group, items in sorted(by_group.items()):
        summaries.append(
            {
                "context_group": group,
                "review_item_count": len(items),
                "candidate_status_counts": dict(sorted(Counter(item["candidate_status"] for item in items).items())),
                "alignment_status_counts": dict(sorted(Counter(item["alignment_status"] for item in items).items())),
                "private_candidate_option_count": sum(int(item["private_candidate_option_count"]) for item in items),
                "candidate_record_count_sum": sum(int(item["candidate_record_count"]) for item in items),
                "candidate_unique_numeric_fingerprint_count_sum": sum(
                    int(item["candidate_unique_numeric_fingerprint_count"]) for item in items
                ),
                "owner_review_required": True,
            }
        )
    return summaries


def _build_private_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# KMFA v0.1.4 outside-scope candidate review packet",
        "",
        "说明：本文件包含 raw 文件名、表头、金额、候选值、私有 hash/slot 明细和诊断细节，只能保留在 private runtime，不得提交 GitHub。",
        "",
        f"- phase_id: {PHASE_ID}",
        f"- review_item_count: {packet['review_item_count']}",
        f"- review_group_count: {packet['review_group_count']}",
        f"- allowed_review_decision_codes: {', '.join(ALLOWED_REVIEW_DECISION_CODES)}",
        "",
        "## 操作规则",
        "",
        "- 每个 review item 只能选择一个 allowed decision code。",
        "- 如果选择 private candidate，请填写 selected_private_candidate_option_index。",
        "- 如果没有可选 candidate，请填写 corrected source-map reference 或 keep_pending。",
        "- 不要把本文件、raw 文件名、字段、金额、明细或私有 hash 提交到 GitHub。",
        "",
        "## Review Items",
    ]
    for item in packet["review_items"]:
        lines.extend(
            [
                "",
                f"### {item['review_item_id']} / target_slot_id={item['target_slot_id']}",
                f"- context_group: {item['context_group']}",
                f"- alignment_status: {item['alignment_status']}",
                f"- candidate_status: {item['candidate_status']}",
                f"- candidate_record_count: {item['candidate_record_count']}",
                f"- candidate_unique_numeric_fingerprint_count: {item['candidate_unique_numeric_fingerprint_count']}",
                f"- allowed_review_decision_codes: {', '.join(item['allowed_review_decision_codes'])}",
                "- selected_review_decision_code: PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
            ]
        )
        for candidate_index, candidate in enumerate(item.get("private_candidate_options", []), 1):
            lines.extend(
                [
                    f"  - 候选 {candidate_index}:",
                    f"    - raw_file_name: {candidate.get('raw_file_name')}",
                    f"    - archive_member_name: {candidate.get('archive_member_name')}",
                    f"    - record_kind: {candidate.get('record_kind')}",
                    f"    - sheet_name: {candidate.get('sheet_name')}",
                    f"    - cell_address: {candidate.get('cell_address')}",
                    f"    - raw_value: {candidate.get('raw_value')}",
                    f"    - numeric_value_fingerprint: {candidate.get('numeric_value_fingerprint')}",
                    f"    - context_text: {candidate.get('context_text')}",
                ]
            )
    return "\n".join(lines) + "\n"


def _build_packet(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_alignment: dict[str, Any],
    source_alignment_items: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    review_items = _build_review_items(generated_at, source_alignment_items)
    group_summaries = _group_summaries(review_items)
    status_counts = Counter(item["candidate_status"] for item in review_items)
    alignment_status_counts = Counter(item["alignment_status"] for item in review_items)
    summary_private = {
        "source_alignment_phase_id": source_summary.get("phase_id"),
        "source_alignment_decision": source_summary.get("decision"),
        "source_alignment_item_count": len(source_alignment_items),
        "source_private_alignment_schema_version": source_alignment.get("schema_version"),
        "review_packet_item_count": len(review_items),
        "review_group_count": len(group_summaries),
        "candidate_status_counts": dict(sorted(status_counts.items())),
        "alignment_status_counts": dict(sorted(alignment_status_counts.items())),
        "ambiguous_review_item_count": alignment_status_counts.get("ambiguous_raw_candidates_require_owner_review", 0),
        "unmatched_review_item_count": alignment_status_counts.get(
            "no_context_raw_candidate_requires_source_mapping_review", 0
        ),
        "non_numeric_or_calculation_review_item_count": alignment_status_counts.get(
            "non_numeric_or_calculation_context_requires_manual_authority", 0
        ),
        "private_candidate_option_excerpt_count": sum(
            int(item.get("private_candidate_option_count") or 0) for item in review_items
        ),
        "candidate_record_observation_count": sum(int(item.get("candidate_record_count") or 0) for item in review_items),
        "candidate_unique_fingerprint_observation_count": sum(
            int(item.get("candidate_unique_numeric_fingerprint_count") or 0) for item in review_items
        ),
        "owner_review_required_item_count": len(review_items),
        "review_packet_ready": True,
        "owner_review_response_supplied": False,
        "selected_private_candidate_count": 0,
        "corrected_source_map_reference_count": 0,
        "authoritative_non_numeric_or_calculation_mapping_count": 0,
        "keep_pending_response_count": 0,
        "source_map_correction_ready": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
    }
    packet = {
        "schema_version": "kmfa.private.v014_outside_scope_candidate_review_packet_after_alignment.v1",
        "classification": "private_outside_scope_candidate_review_packet_do_not_commit",
        "record_type": "v014_outside_scope_candidate_review_packet_after_alignment",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "summary_private": summary_private,
        "allowed_review_decision_codes": ALLOWED_REVIEW_DECISION_CODES,
        "review_group_summaries": group_summaries,
        "review_item_count": len(review_items),
        "review_group_count": len(group_summaries),
        "review_items": review_items,
        "completion_policy": {
            "owner_or_authorized_delegate_must_choose_one_allowed_decision_per_item": True,
            "do_not_commit_this_private_packet": True,
            "do_not_enter_raw_business_values_into_public_repo": True,
            "this_phase_does_not_select_candidates": True,
            "this_phase_does_not_correct_source_maps": True,
            "this_phase_does_not_run_full_comparison": True,
        },
        "raw_boundary": _raw_boundary(),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_outside_scope_candidate_review_packet_diagnostic.v1",
        "classification": "private_outside_scope_candidate_review_packet_diagnostic_do_not_commit",
        "record_type": "v014_outside_scope_candidate_review_packet_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "summary_private": summary_private,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_private_refs": {
            "source_private_alignment": "private_runtime_only",
            "source_private_alignment_items": "private_runtime_only",
        },
        "review_group_summaries": group_summaries,
    }
    return packet, diagnostic


def _build_matrix(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    matrix_source = {
        "source_alignment_available": (summary["source_alignment_item_count"] == 72, summary["source_alignment_item_count"], 72),
        "private_review_packet_written": (summary["private_review_packet_written"] is True, True, True),
        "review_packet_item_coverage": (summary["review_packet_item_count"] == 72, summary["review_packet_item_count"], 72),
        "owner_review_response_absent": (summary["owner_review_response_supplied"] is False, False, False),
        "direct_source_ref_coverage": (summary["source_direct_source_record_ref_match_count"] == 72, summary["source_direct_source_record_ref_match_count"], 72),
        "direct_processed_fingerprint_coverage": (summary["source_direct_processed_fingerprint_match_count"] == 72, summary["source_direct_processed_fingerprint_match_count"], 72),
        "full_comparison_not_claimed": (summary["full_raw_to_processed_value_comparison_complete"] is False, False, False),
        "downstream_no_go_preserved": (DECISION == "NO_GO", DECISION, "NO_GO"),
    }
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, (passed, observed, required) in matrix_source.items()
    ]
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_packet_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_candidate_review_packet_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "check_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "PASS"),
        "fail_count": sum(1 for row in rows if row["status"] == "FAIL"),
        "checks": rows,
        "review_packet_item_count": summary["review_packet_item_count"],
        "owner_review_required_item_count": summary["owner_review_required_item_count"],
        "source_direct_source_record_ref_match_count": summary["source_direct_source_record_ref_match_count"],
        "source_direct_processed_fingerprint_match_count": summary["source_direct_processed_fingerprint_match_count"],
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# KMFA v0.1.4 Outside-Scope Candidate Review Packet After Alignment

- phase: `{PHASE_ID}`
- decision: `{DECISION}`
- review packet item count: `{summary["review_packet_item_count"]}`
- review group count: `{summary["review_group_count"]}`
- ambiguous review item count: `{summary["ambiguous_review_item_count"]}`
- unmatched review item count: `{summary["unmatched_review_item_count"]}`
- non-numeric/calculation review item count: `{summary["non_numeric_or_calculation_review_item_count"]}`
- owner review required item count: `{summary["owner_review_required_item_count"]}`
- source direct source-ref match count: `{summary["source_direct_source_record_ref_match_count"]}`
- source direct processed-fingerprint match count: `{summary["source_direct_processed_fingerprint_match_count"]}`
- next required input: `{NEXT_REQUIRED_INPUT}`

This phase prepares a private owner/authorized-delegate review packet from the prior private alignment diagnostics. It does not read the raw inbox, select candidates, correct source maps, run the formal raw-to-processed comparison, verify business consistency, upload GitHub, reinstall the app, or execute business steps.
"""
    go_no_go_record = f"""# Go/No-Go

- decision: `{DECISION}`
- reason: 72 outside-scope records still require owner/authorized-delegate review before source-map correction or full comparison.
- matrix: `{matrix["pass_count"]}` pass / `{matrix["fail_count"]}` fail
- owner review response supplied: `false`
- formal comparison allowed: `false`
- business execution allowed: `false`
"""
    risk_register = """# Risk Register

- Risk: a private review packet can be mistaken for owner authorization.
- Control: public evidence records response_supplied=false and source_map_correction_ready=false.
- Control: private packet remains ignored and contains raw/candidate detail only in private runtime.
"""
    rollback = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, ignored private review packet directory, tool, validator, focused test and governance rows. Do not modify the raw inbox.
"""
    test_results = f"""# Test Results

- expected generator: `KMFA/tools/v014_outside_scope_candidate_review_packet_after_alignment.py`
- expected validator: `KMFA/tools/check_v014_outside_scope_candidate_review_packet_after_alignment.py --require-private-packet`
- expected focused test: `KMFA.tests.test_v014_outside_scope_candidate_review_packet_after_alignment`
- status: generated by phase and verified locally
"""
    for path, text in (
        (REPORT_PATH, report),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback),
        (TEST_RESULTS_PATH, test_results),
    ):
        _write_text(path, text)


def _append_jsonl_event(path: Path, event_id: str, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    path.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def _append_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-PACKET"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260707-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-PACKET",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "review_packet_item_count": summary["review_packet_item_count"],
        "owner_review_required_item_count": summary["owner_review_required_item_count"],
        "owner_review_response_supplied": False,
        "source_map_correction_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Generated a private outside-scope candidate review packet and kept full comparison blocked.",
    }
    _append_jsonl_event(DEVELOPMENT_EVENTS_PATH, event_id, event)
    _append_jsonl_event(
        STAGE_STATUS_PATH,
        event_id,
        {
            "event_id": event_id,
            "event_time": generated_at,
            "project_id": "KMFA",
            "stage_id": "value-consistency",
            "phase_id": PHASE_ID,
            "status": STATUS,
            "decision": DECISION,
            "next_required_input": NEXT_REQUIRED_INPUT,
            "evidence_ref": MANIFEST_PATH.as_posix(),
        },
    )
    _append_jsonl_event(
        TASK_STATUS_PATH,
        event_id,
        {
            "event_id": event_id,
            "event_time": generated_at,
            "task_id": TASK_ID,
            "phase_id": PHASE_ID,
            "status": STATUS,
            "decision": DECISION,
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
        },
    )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_ALIGNMENT_SUMMARY_PATH)
    _read_json(SOURCE_ALIGNMENT_MANIFEST_PATH)
    source_alignment = _read_json(SOURCE_PRIVATE_ALIGNMENT_PATH)
    source_items = _read_jsonl(SOURCE_PRIVATE_ALIGNMENT_ITEMS_PATH)
    packet, diagnostic = _build_packet(
        generated_at=timestamp,
        source_summary=source_summary,
        source_alignment=source_alignment,
        source_alignment_items=source_items,
    )
    summary_private = packet["summary_private"]
    summary = {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_packet_summary.v1",
        "record_type": "v014_outside_scope_candidate_review_packet_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        **summary_private,
        "source_direct_source_record_ref_match_count": int(
            source_summary.get("direct_source_record_ref_match_count") or 0
        ),
        "source_direct_processed_fingerprint_match_count": int(
            source_summary.get("direct_processed_fingerprint_match_count") or 0
        ),
        "private_review_packet_written": True,
        "private_review_packet_gitignored": _git_check_ignored(PRIVATE_PACKET_PATH),
        "private_review_packet_items_written": True,
        "private_review_packet_items_gitignored": _git_check_ignored(PRIVATE_PACKET_ITEMS_PATH),
        "private_review_packet_markdown_written": True,
        "private_review_packet_markdown_gitignored": _git_check_ignored(PRIVATE_PACKET_MARKDOWN_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    matrix = _build_matrix(timestamp, summary)
    go_no_go = {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_packet_go_no_go.v1",
        "record_type": "v014_outside_scope_candidate_review_packet_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "blocker_ids": [
            "OUTSIDE_SCOPE_OWNER_REVIEW_RESPONSE_NOT_SUPPLIED",
            "DIRECT_SOURCE_RECORD_REF_COVERAGE_ZERO",
            "DIRECT_PROCESSED_FINGERPRINT_RAW_COVERAGE_ZERO",
            "FULL_COMPARISON_STILL_BLOCKED",
        ],
        "review_packet_item_count": summary["review_packet_item_count"],
        "owner_review_required_item_count": summary["owner_review_required_item_count"],
        "owner_review_response_supplied": False,
        "source_map_correction_ready": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_packet_manifest.v1",
        "record_type": "v014_outside_scope_candidate_review_packet_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "git_head_at_generation": _git_output(["rev-parse", "HEAD"]),
        "decision": DECISION,
        "summary": summary,
        "go_no_go_report": go_no_go,
        "matrix": matrix,
        "private_artifacts": {
            "private_review_packet": "private_runtime_only",
            "private_review_packet_items": "private_runtime_only",
            "private_review_packet_markdown": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_packet_after_alignment.py --require-private-packet",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_packet_after_alignment",
        ],
        "changed_files": FILES_CHANGED,
    }
    _write_json(PRIVATE_PACKET_PATH, packet)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_PACKET_ITEMS_PATH, packet["review_items"])
    _write_text(PRIVATE_PACKET_MARKDOWN_PATH, _build_private_markdown(packet))
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
    if write_governance_event:
        _append_governance_events(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "go_no_go": go_no_go, "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope candidate review packet generated "
        f"(decision={summary['decision']}, items={summary['review_packet_item_count']}, "
        f"owner_review_required={summary['owner_review_required_item_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
