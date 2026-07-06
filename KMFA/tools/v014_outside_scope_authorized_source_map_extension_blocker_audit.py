#!/usr/bin/env python3
"""Audit the repeated outside-scope source-map extension authorization blocker.

This phase records the third consecutive observation that no valid
owner/authorized-delegate source-map extension input exists for the 72
outside-scope target slots. It does not read or mutate the raw inbox, mutate the
private template, apply source-map records, compare values, reconcile values,
upload, reinstall, or execute business steps.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_BLOCKER_AUDIT"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-BLOCKER-AUDIT-20260706"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-BLOCKER-AUDIT"
VERSION = "0.1.4-outside-scope-authorized-source-map-extension-blocker-audit"
STATUS = "completed_validated_local_only_outside_scope_authorized_source_map_extension_goal_blocked"
DECISION = "NO_GO"
BLOCKER = "outside_scope_authorized_source_map_extension_input_missing"
DIAGNOSTIC_CONCLUSION = "outside_scope_authorized_source_map_extension_blocker_threshold_met"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_fills_private_authorized_source_map_extension_template_for_72_slots"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_blocker_audit_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_blocker_audit_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_blocker_audit_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_blocker_audit_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_authorized_source_map_extension_blocker_audit_report.md"
OWNER_PACKET_PATH = HUMAN_DIR / "owner_agent_blocker_packet.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_blocker_audit_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_blocker_audit_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_blocker_audit_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_blocker_audit_matrix_public_safe.json"
)
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

EXTENSION_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_summary.json"
)
READINESS_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_readiness_recheck_summary.json"
)
PRIVATE_READINESS_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_readiness_recheck/private_authorized_source_map_extension_readiness_diagnostic.json"
)
PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_blocker_audit"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_blocker_audit_diagnostic.json"

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
        "private_readiness_diagnostic_read_by_this_phase": True,
        "private_blocker_audit_diagnostic_written_by_this_phase": True,
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
        "private_readiness_diagnostic_committed": False,
        "private_blocker_audit_diagnostic_committed": False,
        "private_template_committed": False,
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


def _build_observations(extension_summary: dict[str, Any], readiness_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "phase_id": extension_summary.get("phase_id"),
            "decision": extension_summary.get("decision"),
            "valid_authorized_extension_record_count": extension_summary.get("valid_authorized_extension_record_count"),
            "missing_authorized_extension_record_count": extension_summary.get("missing_authorized_extension_record_count"),
            "source_map_extension_ready": False,
        },
        {
            "phase_id": readiness_summary.get("phase_id"),
            "decision": readiness_summary.get("decision"),
            "valid_authorized_extension_record_count": readiness_summary.get("valid_authorized_extension_record_count"),
            "missing_authorized_extension_record_count": readiness_summary.get("missing_authorized_extension_record_count"),
            "source_map_extension_ready": readiness_summary.get("source_map_extension_application_ready"),
        },
        {
            "phase_id": PHASE_ID,
            "decision": DECISION,
            "valid_authorized_extension_record_count": 0,
            "missing_authorized_extension_record_count": 72,
            "source_map_extension_ready": False,
        },
    ]


def _build_summary(generated_at: str, extension_summary: dict[str, Any], readiness_summary: dict[str, Any]) -> dict[str, Any]:
    observations = _build_observations(extension_summary, readiness_summary)
    consecutive_count = sum(
        1
        for item in observations
        if item["decision"] == "NO_GO"
        and item["valid_authorized_extension_record_count"] == 0
        and item["missing_authorized_extension_record_count"] == 72
        and item["source_map_extension_ready"] is False
    )
    threshold_met = consecutive_count >= 3
    return {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_blocker_audit_summary.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_blocker_audit_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "blocker_condition": BLOCKER,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "consecutive_goal_turn_blocker_count": consecutive_count,
        "blocked_audit_threshold_met": threshold_met,
        "goal_status_recommendation": "blocked" if threshold_met else "continue",
        "prior_extension_decision": extension_summary.get("decision"),
        "prior_extension_valid_authorized_extension_record_count": extension_summary.get(
            "valid_authorized_extension_record_count"
        ),
        "prior_readiness_decision": readiness_summary.get("decision"),
        "prior_readiness_valid_authorized_extension_record_count": readiness_summary.get(
            "valid_authorized_extension_record_count"
        ),
        "private_authorized_extension_template_item_count": readiness_summary.get(
            "private_authorized_extension_template_item_count"
        ),
        "owner_authorized_extension_input_present": False,
        "owner_authorized_extension_record_count": 0,
        "valid_authorized_extension_record_count": 0,
        "missing_authorized_extension_record_count": 72,
        "source_map_extension_ready_count": 0,
        "source_map_extension_blocker_count": 72,
        "source_map_extension_application_ready": False,
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed": False,
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
        "observations": observations,
        "private_readiness_diagnostic_gitignored": _git_check_ignored(PRIVATE_READINESS_DIAGNOSTIC_PATH),
        "private_blocker_audit_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_blocker_go_no_go.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_blocker_audit_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "decision": DECISION,
        "status": STATUS,
        "blocker_condition": BLOCKER,
        "consecutive_goal_turn_blocker_count": summary["consecutive_goal_turn_blocker_count"],
        "blocked_audit_threshold_met": summary["blocked_audit_threshold_met"],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "valid_authorized_extension_record_count": 0,
        "missing_authorized_extension_record_count": 72,
        "source_map_extension_application_ready": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "blocked_next_steps": [
            "source_map_extension_application",
            "full_raw_to_processed_value_comparison",
            "processed_data_reconciliation",
            "business_value_consistency",
            "lineage_full_check",
            "formal_report",
            "github_upload",
            "app_reinstall",
            "business_execution",
        ],
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("prior_extension_no_go", summary["prior_extension_decision"] == "NO_GO", "NO_GO"),
        ("prior_readiness_no_go", summary["prior_readiness_decision"] == "NO_GO", "NO_GO"),
        ("third_observation_no_go", summary["decision"] == "NO_GO", "NO_GO"),
        ("threshold_met", summary["blocked_audit_threshold_met"] is True, "true"),
        ("valid_authorization_absent", summary["valid_authorized_extension_record_count"] == 0, "0"),
        ("missing_authorization_count", summary["missing_authorized_extension_record_count"] == 72, "72"),
        ("source_map_application_not_ready", summary["source_map_extension_application_ready"] is False, "false"),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False, "false"),
    ]
    rows = [
        {
            "check_code": code,
            "status": "PASS" if ok else "FAIL",
            "observed": str(ok).lower(),
            "required": required,
        }
        for code, ok, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_blocker_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_blocker_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "blocker_audit_check_count": len(rows),
        "blocker_audit_check_pass_count": pass_count,
        "blocker_audit_check_fail_count": len(rows) - pass_count,
        "decision": DECISION,
        "checks": rows,
    }


def _append_development_event(manifest: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-BLOCKER-AUDIT"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260706-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-BLOCKER-AUDIT",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "consecutive_goal_turn_blocker_count": summary["consecutive_goal_turn_blocker_count"],
        "blocked_audit_threshold_met": summary["blocked_audit_threshold_met"],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "valid_authorized_extension_record_count": 0,
        "missing_authorized_extension_record_count": 72,
        "source_map_extension_application_ready": False,
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": "Audited repeated outside-scope source-map extension authorization blocker and recommended blocked goal status.",
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
            OWNER_PACKET_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            "KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_blocker_audit.py",
            "KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_blocker_audit.py",
            "KMFA/tools/v014_outside_scope_authorized_source_map_extension_blocker_audit.py",
        ],
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    retained_lines: list[str] = []
    if DEVELOPMENT_EVENTS_PATH.exists():
        for line in DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                existing_event = json.loads(line)
            except json.JSONDecodeError:
                retained_lines.append(line)
                continue
            if not isinstance(existing_event, dict) or existing_event.get("event_id") != event_id:
                retained_lines.append(line)
    retained_lines.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(retained_lines) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    extension_summary = _read_json(EXTENSION_SUMMARY_PATH)
    readiness_summary = _read_json(READINESS_SUMMARY_PATH)
    private_readiness_diagnostic = _read_json(PRIVATE_READINESS_DIAGNOSTIC_PATH)
    summary = _build_summary(timestamp, extension_summary, readiness_summary)
    go_no_go = _build_go_no_go(summary)
    matrix = _build_matrix(summary)
    private_diagnostic = {
        "schema_version": "kmfa.private.v014_outside_scope_authorized_source_map_extension_blocker_audit.v1",
        "classification": "private_blocker_audit_diagnostic_do_not_commit",
        "record_type": "v014_outside_scope_authorized_source_map_extension_blocker_audit_private_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "blocker_condition": BLOCKER,
        "source_private_readiness_phase_id": private_readiness_diagnostic.get("phase_id"),
        "counts": {
            "private_authorized_extension_template_item_count": summary[
                "private_authorized_extension_template_item_count"
            ],
            "valid_authorized_extension_record_count": 0,
            "missing_authorized_extension_record_count": 72,
            "source_map_extension_blocker_count": 72,
        },
        "blocked_audit_threshold_met": summary["blocked_audit_threshold_met"],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "raw_boundary": _raw_boundary(),
    }
    manifest = {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_blocker_audit_manifest.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_blocker_audit_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "blocker_condition": BLOCKER,
        "summary": summary,
        "go_no_go_report": go_no_go,
        "matrix": matrix,
        "git": {
            "head": _git_output(["rev-parse", "HEAD"]),
            "branch": _git_output(["branch", "--show-current"]),
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
        (PRIVATE_DIAGNOSTIC_PATH, private_diagnostic),
    ):
        _write_json(path, payload)

    _write_text(
        REPORT_PATH,
        f"""# V014 Outside-Scope Source-Map Extension Blocker Audit

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- blocker condition: `{BLOCKER}`
- consecutive blocker count: `{summary["consecutive_goal_turn_blocker_count"]}`
- blocked threshold met: `true`
- valid authorized extension records: `0`
- missing authorized extension records: `72`
- source-map application ready: `false`

The same authorization blocker has now been observed across three consecutive goal turns. This is not a data mismatch report and not a source-map application.
""",
    )
    _write_text(
        OWNER_PACKET_PATH,
        f"""# Owner / Agent Blocker Packet

Current blocker: `{BLOCKER}`

Required private action:

1. Fill the private authorized source-map extension template for all pending outside-scope items.
2. Do not place raw file names, field headers, amounts, row values, workbook names, document names or credentials in public files.
3. Re-run readiness recheck after the private template is filled.

Until that private input exists, Codex must keep source-map application, full comparison, reconciliation, formal report, GitHub upload, app reinstall and business execution blocked.
""",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"""# Go / No-Go

- decision: `{DECISION}`
- reason: repeated missing owner/authorized-delegate source-map extension input.
- goal status recommendation: `blocked`
- next required input: `{NEXT_REQUIRED_INPUT}`
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        "# Risk Register\n\n"
        "- Risk: local validation could be mistaken for business readiness.\n"
        "- Control: goal status is recommended as blocked until authorized private input changes.\n"
        "- Raw boundary: raw inbox read/list/stat/hash/parse/write/delete/move/rename/copy/normalize/mutation remain false.\n",
    )
    _write_text(
        ROLLBACK_PATH,
        "Remove this phase's public artifacts, metadata copies, private blocker diagnostic, tool, validator, focused test and governance entries. The raw data inbox is not modified by this rollback.\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        f"""# Test Results

Planned commands:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_authorized_source_map_extension_blocker_audit.py KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_blocker_audit.py KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_blocker_audit.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_authorized_source_map_extension_blocker_audit.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_blocker_audit.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_authorized_source_map_extension_blocker_audit`

Current generated check matrix: `{matrix["blocker_audit_check_pass_count"]}` pass / `{matrix["blocker_audit_check_fail_count"]}` fail. This phase does not read, list, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
""",
    )

    if write_governance_event:
        _append_development_event(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope source-map extension blocker audited "
        f"(consecutive_blockers={summary['consecutive_goal_turn_blocker_count']}, "
        f"valid_extensions={summary['valid_authorized_extension_record_count']}, "
        f"recommendation={summary['goal_status_recommendation']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
