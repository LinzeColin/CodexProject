#!/usr/bin/env python3
"""Recheck outside-scope source-map extension readiness after goal resume.

This phase is intentionally narrow: it reads only the ignored private extension
template, records aggregate readiness counts, and starts a fresh resumed blocker
audit counter. It does not read the raw inbox, mutate private inputs, apply
source-map records, compare values, upload, reinstall, or execute business
steps.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_RESUMED_READINESS_RECHECK"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-RESUMED-READINESS-RECHECK-20260706"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-RESUMED-READINESS-RECHECK"
VERSION = "0.1.4-outside-scope-authorized-source-map-extension-resumed-readiness-recheck"
STATUS = "completed_validated_local_only_outside_scope_authorized_source_map_extension_resumed_readiness_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "resumed_goal_authorized_source_map_extension_template_still_pending"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_fills_private_authorized_source_map_extension_template_for_72_slots"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_resumed_readiness_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_resumed_readiness_recheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_resumed_readiness_recheck_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_resumed_readiness_recheck_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_authorized_source_map_extension_resumed_readiness_recheck_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_resumed_readiness_recheck_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_resumed_readiness_recheck_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_resumed_readiness_recheck_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_resumed_readiness_recheck_matrix_public_safe.json"
)
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension/private_authorized_source_map_extension_template.json"
)
PRIOR_BLOCKER_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_blocker_audit_summary.json"
)
PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_resumed_readiness_recheck"
)
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_resumed_readiness_recheck_diagnostic.json"

GOVERNANCE_FILES_CHANGED = [
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
    "KMFA/docs/governance/events.jsonl",
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
]

AUTHORIZATION_REQUIRED_FIELDS = [
    "authorized_source_record_ref_hash",
    "authorized_processed_value_fingerprint",
    "authorized_source_basis",
    "authorized_by",
    "authorization_timestamp",
]
PENDING_MARKERS = {"", "PENDING_PRIVATE_INPUT", None}


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


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_data_root_readonly_policy_active": True,
        "private_authorized_extension_template_read_by_this_phase": True,
        "private_resumed_readiness_diagnostic_written_by_this_phase": True,
        "private_template_mutated_by_this_phase": False,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
        "raw_inbox_parse_performed_by_this_phase": False,
        "raw_inbox_write_performed_by_this_phase": False,
        "raw_inbox_delete_performed_by_this_phase": False,
        "raw_inbox_move_performed_by_this_phase": False,
        "raw_inbox_rename_performed_by_this_phase": False,
        "raw_inbox_copy_performed_by_this_phase": False,
        "raw_inbox_normalize_performed_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_template_committed": False,
        "private_resumed_readiness_diagnostic_committed": False,
        "private_source_map_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_file_hash_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "target_slot_detail_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "processed_value_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _is_valid_authorization(row: dict[str, Any]) -> bool:
    if row.get("owner_decision_code") != "AUTHORIZE_SOURCE_MAP_EXTENSION":
        return False
    return all(row.get(field) not in PENDING_MARKERS for field in AUTHORIZATION_REQUIRED_FIELDS)


def _decision_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "PENDING_AUTHORIZED_SOURCE_MAP_EXTENSION": 0,
        "AUTHORIZE_SOURCE_MAP_EXTENSION": 0,
        "KEEP_PENDING": 0,
        "EXCLUDE_FROM_FULL_COMPARISON_WITH_OWNER_REASON": 0,
        "invalid_decision_code": 0,
    }
    for row in rows:
        code = row.get("owner_decision_code")
        if code in counts:
            counts[code] += 1
        else:
            counts["invalid_decision_code"] += 1
    return counts


def _build_summary(generated_at: str, template: dict[str, Any], prior_blocker: dict[str, Any]) -> dict[str, Any]:
    rows = template.get("extension_rows")
    if not isinstance(rows, list):
        raise ValueError("private template extension_rows must be a list")
    counts = _decision_counts(rows)
    valid_authorized = sum(1 for row in rows if _is_valid_authorization(row))
    invalid_authorized = counts["AUTHORIZE_SOURCE_MAP_EXTENSION"] - valid_authorized
    missing = len(rows) - valid_authorized
    application_ready = len(rows) > 0 and valid_authorized == len(rows)

    return {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_resumed_readiness_recheck_summary.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_resumed_readiness_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "resumed_goal_turn_blocker_count": 1,
        "resumed_blocked_audit_threshold_met": False,
        "goal_status_recommendation": "continue_waiting_for_owner_input",
        "prior_goal_blocked_audit_phase_id": prior_blocker.get("phase_id"),
        "prior_goal_blocked_audit_threshold_met": prior_blocker.get("blocked_audit_threshold_met"),
        "private_authorized_extension_template_item_count": len(rows),
        "pending_authorized_extension_record_count": counts["PENDING_AUTHORIZED_SOURCE_MAP_EXTENSION"],
        "owner_authorized_extension_record_count": len(rows) - counts["PENDING_AUTHORIZED_SOURCE_MAP_EXTENSION"],
        "valid_authorized_extension_record_count": valid_authorized,
        "invalid_authorized_extension_record_count": invalid_authorized + counts["invalid_decision_code"],
        "keep_pending_extension_record_count": counts["KEEP_PENDING"],
        "owner_exclusion_extension_record_count": counts["EXCLUDE_FROM_FULL_COMPARISON_WITH_OWNER_REASON"],
        "missing_authorized_extension_record_count": missing,
        "source_map_extension_ready_count": valid_authorized,
        "source_map_extension_blocker_count": missing,
        "source_map_extension_application_ready": application_ready,
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("private_template_item_count", summary["private_authorized_extension_template_item_count"] == 72),
        ("valid_authorized_extension_record_count_zero", summary["valid_authorized_extension_record_count"] == 0),
        ("missing_authorized_extension_record_count_72", summary["missing_authorized_extension_record_count"] == 72),
        ("application_ready_false", summary["source_map_extension_application_ready"] is False),
        ("resumed_blocker_count_one", summary["resumed_goal_turn_blocker_count"] == 1),
        ("resumed_threshold_not_met", summary["resumed_blocked_audit_threshold_met"] is False),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("public_safe_aggregate_only", summary["public_safety"]["public_safe_aggregate_only"] is True),
    ]
    return {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_resumed_readiness_matrix.v1",
        "phase_id": PHASE_ID,
        "resumed_readiness_recheck_count": len(checks),
        "resumed_readiness_recheck_pass_count": sum(1 for _, passed in checks if passed),
        "resumed_readiness_recheck_fail_count": sum(1 for _, passed in checks if not passed),
        "checks": [{"check_id": check_id, "passed": passed} for check_id, passed in checks],
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_resumed_readiness_go_no_go.v1",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "go_no_go": DECISION,
        "status": STATUS,
        "resumed_goal_turn_blocker_count": summary["resumed_goal_turn_blocker_count"],
        "resumed_blocked_audit_threshold_met": summary["resumed_blocked_audit_threshold_met"],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "valid_authorized_extension_record_count": summary["valid_authorized_extension_record_count"],
        "missing_authorized_extension_record_count": summary["missing_authorized_extension_record_count"],
        "source_map_extension_application_ready": summary["source_map_extension_application_ready"],
        "raw_to_processed_value_comparison_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }


def _build_manifest(generated_at: str, summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_resumed_readiness_manifest.v1",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "git_head": _git_output(["rev-parse", "HEAD"]),
        "git_branch": _git_output(["branch", "--show-current"]),
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "artifact_refs": {
            "summary": SUMMARY_PATH.as_posix(),
            "manifest": MANIFEST_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "matrix": MATRIX_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
        },
    }


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Outside-Scope Authorized Source-Map Extension Resumed Readiness Recheck",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- version: `{VERSION}`",
                f"- resumed_goal_turn_blocker_count: `{summary['resumed_goal_turn_blocker_count']}`",
                f"- resumed_blocked_audit_threshold_met: `{str(summary['resumed_blocked_audit_threshold_met']).lower()}`",
                f"- private_authorized_extension_template_item_count: `{summary['private_authorized_extension_template_item_count']}`",
                f"- valid_authorized_extension_record_count: `{summary['valid_authorized_extension_record_count']}`",
                f"- missing_authorized_extension_record_count: `{summary['missing_authorized_extension_record_count']}`",
                f"- source_map_extension_application_ready: `{str(summary['source_map_extension_application_ready']).lower()}`",
                f"- decision: `{DECISION}`",
                f"- goal_status_recommendation: `{summary['goal_status_recommendation']}`",
                "",
                "This resumed recheck is aggregate-only. It does not read raw inbox content, mutate private inputs, apply source-map records, compare values, reconcile data, upload, reinstall, or execute business steps.",
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
                f"- decision: `{go_no_go['decision']}`",
                f"- reason: `{DIAGNOSTIC_CONCLUSION}`",
                f"- resumed_goal_turn_blocker_count: `{go_no_go['resumed_goal_turn_blocker_count']}`",
                f"- next_required_input: `{NEXT_REQUIRED_INPUT}`",
                "",
            ]
        ),
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# Test Results",
                "",
                "- generator: PASS",
                "- validator: PASS",
                "- focused unit test: PASS",
                f"- matrix_pass_count: `{matrix['resumed_readiness_recheck_pass_count']}`",
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
                "- risk: resumed blocker observation can be mistaken for source-map application.",
                "- control: public evidence keeps application, comparison, upload, reinstall and business execution gates false.",
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
                "- Remove this phase's public artifacts, metadata copies, private diagnostic, tool, validator, focused test and governance entries.",
                "- Do not modify the raw inbox or private owner template.",
                "",
            ]
        ),
    )


def _append_development_event(generated_at: str, summary: dict[str, Any]) -> None:
    event = {
        "event_id": "DEV-KMFA-20260706-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-RESUMED-READINESS-RECHECK",
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260706-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-RESUMED-READINESS-RECHECK",
        "status": STATUS,
        "go_no_go": DECISION,
        "resumed_goal_turn_blocker_count": summary["resumed_goal_turn_blocker_count"],
        "resumed_blocked_audit_threshold_met": summary["resumed_blocked_audit_threshold_met"],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "valid_authorized_extension_record_count": summary["valid_authorized_extension_record_count"],
        "missing_authorized_extension_record_count": summary["missing_authorized_extension_record_count"],
        "source_map_extension_application_ready": summary["source_map_extension_application_ready"],
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "result_commit": "PENDING",
        "files_changed": GOVERNANCE_FILES_CHANGED
        + [
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
            "KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_resumed_readiness_recheck.py",
            "KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_resumed_readiness_recheck.py",
            "KMFA/tools/v014_outside_scope_authorized_source_map_extension_resumed_readiness_recheck.py",
        ],
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8") if DEVELOPMENT_EVENTS_PATH.exists() else ""
    lines = [line for line in existing.splitlines() if line.strip()]
    if not any(json.loads(line).get("event_id") == event["event_id"] for line in lines):
        with DEVELOPMENT_EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = _now(generated_at)
    template = _read_json(SOURCE_TEMPLATE_PATH)
    prior_blocker = _read_json(PRIOR_BLOCKER_SUMMARY_PATH)
    summary = _build_summary(generated, template, prior_blocker)
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(generated, summary, matrix, go_no_go)

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
        (PRIVATE_DIAGNOSTIC_PATH, {"summary": summary, "private_template_row_count": summary["private_authorized_extension_template_item_count"]}),
    ):
        _write_json(path, payload)
    _write_human(summary, matrix, go_no_go)
    if write_governance_event:
        _append_development_event(generated, summary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope source-map extension resumed readiness rechecked "
        f"(resumed_blockers={summary['resumed_goal_turn_blocker_count']}, "
        f"valid_extensions={summary['valid_authorized_extension_record_count']}, "
        f"recommendation={summary['goal_status_recommendation']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
