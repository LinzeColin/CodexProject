#!/usr/bin/env python3
"""Prepare non-active owner response decision options for KMFA v0.1.4.

This phase reduces the owner confirmation surface after the response readiness
gate proved that all 113 rows are still pending. It creates private-only
confirmation codes and non-active response drafts. It does not read raw data,
does not modify the owner response template, and does not create an active
authorization record.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_RESPONSE_DECISION_OPTIONS"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-RESPONSE-DECISION-OPTIONS-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-RESPONSE-DECISION-OPTIONS"
VERSION = "0.1.4-processed-value-source-map-completion-owner-response-decision-options"
STATUS = "completed_validated_local_only_no_go_owner_decision_options_ready"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_confirms_private_decision_option_or_fills_response_template"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_response_decision_options_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_response_decision_options_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_response_decision_options_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_response_decision_options_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_response_decision_options_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_response_decision_options_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_response_decision_options_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_RESPONSE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_intake_prep/private_owner_review_response_template.json"
)
SOURCE_GROUPED_REVIEW_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_intake_prep/private_grouped_owner_review_intake.json"
)
SOURCE_READINESS_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_response_readiness_recheck/private_owner_response_readiness_diagnostic.json"
)
PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_response_decision_options"
PRIVATE_OPTIONS_PATH = PRIVATE_OUTPUT_DIR / "private_owner_response_decision_options.json"
PRIVATE_CONFIRMATION_CODES_PATH = PRIVATE_OUTPUT_DIR / "private_owner_response_confirmation_codes_zh.md"
PRIVATE_NON_ACTIVE_DRAFT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_response_non_active_draft.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_response_decision_options_diagnostic.json"


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
        "private_decision_options_committed": False,
        "private_confirmation_codes_committed": False,
        "private_non_active_draft_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_private_outputs(
    *, generated_at: str, response_template: dict[str, Any], grouped_review: dict[str, Any], readiness: dict[str, Any]
) -> tuple[dict[str, Any], str, dict[str, Any], dict[str, Any]]:
    rows = response_template.get("response_rows", [])
    groups = grouped_review.get("review_groups", [])
    counts = readiness.get("counts", {})
    if not isinstance(rows, list) or not isinstance(groups, list):
        raise ValueError("source private response/group files have invalid shape")

    options = [
        {
            "confirmation_code": "KMFA_ORR_OPTION_REVIEW_GROUPS",
            "label_zh": "逐组审阅 22 个 review group 后再填 response template",
            "recommended": True,
            "active_authorization_record_generated": False,
            "proposed_response_effect": "no_template_change_review_groups_first",
            "target_row_count": len(rows),
        },
        {
            "confirmation_code": "KMFA_ORR_OPTION_KEEP_PENDING_ALL",
            "label_zh": "全部保持 keep_pending，作为 owner 明确暂缓记录",
            "recommended": False,
            "active_authorization_record_generated": False,
            "proposed_response_effect": "non_active_draft_sets_keep_pending_all",
            "target_row_count": len(rows),
        },
        {
            "confirmation_code": "KMFA_ORR_OPTION_REQUEST_MORE_DIAGNOSTICS_ALL",
            "label_zh": "全部要求更多诊断，不进入应用",
            "recommended": False,
            "active_authorization_record_generated": False,
            "proposed_response_effect": "non_active_draft_sets_request_more_diagnostics_all",
            "target_row_count": len(rows),
        },
    ]
    non_active_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        non_active_rows.append(
            {
                "target_slot_id": row.get("target_slot_id"),
                "context_group": row.get("context_group"),
                "review_group_id": row.get("review_group_id"),
                "current_owner_decision_code": row.get("owner_decision_code"),
                "proposed_default_decision_code": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_REVIEW",
                "alternative_keep_pending_code": "keep_pending",
                "alternative_request_more_diagnostics_code": "request_more_diagnostics",
                "draft_only_not_active_authorization": True,
            }
        )
    private_options = {
        "schema_version": "kmfa.private.v014_owner_response_decision_options.v1",
        "classification": "private_owner_response_decision_options_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_response_decision_options",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_response_row_count": len(rows),
        "source_review_group_count": len(groups),
        "source_pending_owner_decision_count": counts.get("pending_owner_decision_count"),
        "decision_option_count": len(options),
        "default_recommended_confirmation_code": "KMFA_ORR_OPTION_REVIEW_GROUPS",
        "decision_options": options,
    }
    non_active_draft = {
        "schema_version": "kmfa.private.v014_owner_response_non_active_draft.v1",
        "classification": "private_owner_response_non_active_draft_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_response_non_active_draft",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "draft_is_active_authorization_record": False,
        "completion_template_overwritten": False,
        "active_owner_authorized_fill_record_written": False,
        "response_row_count": len(non_active_rows),
        "response_rows": non_active_rows,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_response_decision_options_diagnostic.v1",
        "classification": "private_owner_response_decision_options_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_response_decision_options_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_counts": counts,
        "decision_option_count": len(options),
        "non_active_draft_row_count": len(non_active_rows),
        "raw_boundary": _raw_boundary(),
    }
    lines = [
        "# KMFA owner response 确认码",
        "",
        "说明：本文件是 private-only 辅助确认包，不会自动生成 active authorization record。",
        "",
        "请在下一轮只回复一个 confirmation_code，或明确要求逐组修改 private response template。",
        "",
    ]
    for option in options:
        lines.extend(
            [
                f"## {option['confirmation_code']}",
                f"- 含义：{option['label_zh']}",
                f"- 推荐：{str(option['recommended']).lower()}",
                f"- 影响：{option['proposed_response_effect']}",
                f"- 覆盖行数：{option['target_row_count']}",
                "",
            ]
        )
    return private_options, "\n".join(lines), non_active_draft, diagnostic


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    response_template = _read_json(SOURCE_RESPONSE_TEMPLATE_PATH)
    grouped_review = _read_json(SOURCE_GROUPED_REVIEW_PATH)
    readiness = _read_json(SOURCE_READINESS_DIAGNOSTIC_PATH)
    private_options, confirmation_text, non_active_draft, diagnostic = _build_private_outputs(
        generated_at=timestamp,
        response_template=response_template,
        grouped_review=grouped_review,
        readiness=readiness,
    )
    _write_json(PRIVATE_OPTIONS_PATH, private_options)
    _write_text(PRIVATE_CONFIRMATION_CODES_PATH, confirmation_text)
    _write_json(PRIVATE_NON_ACTIVE_DRAFT_PATH, non_active_draft)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)

    summary = {
        "schema_version": "kmfa.v014_owner_response_decision_options_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_response_decision_options_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_response_row_count": private_options["source_response_row_count"],
        "source_review_group_count": private_options["source_review_group_count"],
        "source_pending_owner_decision_count": private_options["source_pending_owner_decision_count"],
        "decision_option_count": private_options["decision_option_count"],
        "non_active_draft_row_count": non_active_draft["response_row_count"],
        "private_decision_options_written": True,
        "private_confirmation_codes_written": True,
        "private_non_active_draft_written": True,
        "private_diagnostic_written": True,
        "private_decision_options_gitignored": _git_check_ignored(PRIVATE_OPTIONS_PATH),
        "private_confirmation_codes_gitignored": _git_check_ignored(PRIVATE_CONFIRMATION_CODES_PATH),
        "private_non_active_draft_gitignored": _git_check_ignored(PRIVATE_NON_ACTIVE_DRAFT_PATH),
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "active_owner_authorized_fill_record_ready": False,
        "active_owner_authorized_fill_record_written": False,
        "completion_template_overwritten": False,
        "authorized_completion_record_supplied": False,
        "source_map_completion_reapplication_ready": False,
        "source_map_completion_reapplication_performed": False,
        "source_map_records_applied_count": 0,
        "processed_value_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "NO_GO",
        "diagnostic_conclusion": "private_owner_response_decision_options_ready_owner_confirmation_required",
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_owner_response_decision_options_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_response_decision_options_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": "NO_GO",
        "status": STATUS,
        "diagnostic_conclusion": summary["diagnostic_conclusion"],
        "decision_option_count": summary["decision_option_count"],
        "source_pending_owner_decision_count": summary["source_pending_owner_decision_count"],
        "source_map_completion_reapplication_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_owner_response_decision_options_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_response_decision_options_manifest",
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
            "private_decision_options": "private_runtime_only",
            "private_confirmation_codes": "private_runtime_only",
            "private_non_active_draft": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_response_decision_options.py "
            "--require-private-options"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Processed Value Source-map Completion Owner Response Decision Options

Decision: NO_GO

This phase prepared private confirmation options only. It did not read raw data, did not fill owner decisions, did not create an active authorization record, and did not apply source-map changes.

## Public-safe aggregate result

- Source response rows: {summary["source_response_row_count"]}
- Source pending owner decisions: {summary["source_pending_owner_decision_count"]}
- Decision options: {summary["decision_option_count"]}
- Non-active draft rows: {summary["non_active_draft_row_count"]}

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `NO_GO`
- reason: decision options are ready, but owner/authorized-delegate confirmation has not been supplied.
- active owner-authorized fill record ready: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating private decision options as owner authorization.
  Mitigation: all generated drafts are explicitly non-active and validators require downstream gates to remain closed.
- Risk: private review details leaking publicly.
  Mitigation: public artifacts contain only aggregate counts and evidence refs.
"""
    rollback_plan = """# Rollback Plan

No raw file, response template, completion template, active authorization record or source-map file was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private decision-options directory if not needed.
"""
    test_results = """# Test Results

Pending until validator and focused tests are run after artifact generation.

Expected validator:
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_response_decision_options.py --require-private-options`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-RESPONSE-DECISION-OPTIONS"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-RESPONSE-DECISION-OPTIONS",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "decision_option_count": manifest["summary"]["decision_option_count"],
        "source_pending_owner_decision_count": manifest["summary"]["source_pending_owner_decision_count"],
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": (
            "Prepared private non-active owner response decision options and confirmation codes. "
            "Downstream authorization, source-map application and reconciliation remain blocked until owner confirmation."
        ),
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
        "PASS: KMFA v0.1.4 owner response decision options generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"options={manifest['summary']['decision_option_count']}, "
        f"pending={manifest['summary']['source_pending_owner_decision_count']})"
    )


if __name__ == "__main__":
    main()
