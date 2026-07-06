#!/usr/bin/env python3
"""Register the next corrected-source or private raw-scope intake for KMFA v0.1.4.

This phase records that no corrected source package was supplied in this run and
that the owner objective authorizes a tightly scoped private raw-comparison
preflight as the next phase. It only checks that the private raw root exists as
a directory. It does not list, read, fingerprint, copy, normalize, or mutate any
raw source file and does not run value comparison.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_RAW_SCOPE_INTAKE"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-RAW-SCOPE-INTAKE-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-RAW-SCOPE-INTAKE"
VERSION = "0.1.4-corrected-source-or-raw-scope-intake"
STATUS = "completed_validated_local_only_corrected_source_or_raw_scope_intake_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_raw_comparison_scope_registered_delivery_still_blocked"
PREVIOUS_REQUIRED_INPUT = "corrected_source_package_or_owner_authorized_private_raw_comparison_scope"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_RAW_COMPARISON_PREFLIGHT"
NEXT_REQUIRED_INPUT = "private_raw_comparison_preflight_before_any_raw_value_matching_or_delivery_claim"
RAW_ROOT = Path("/Users/linzezhang/Downloads/KMFA_MetaData")

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_raw_scope_intake_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_raw_scope_intake_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_raw_scope_intake_go_no_go_report.json"
SCOPE_MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_raw_scope_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_corrected_source_or_raw_scope_intake_report.md"
SCOPE_RECORD_PATH = HUMAN_DIR / "raw_scope_intake_public_safe.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_raw_scope_intake_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_raw_scope_intake_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_raw_scope_intake_go_no_go_report.json"
METADATA_SCOPE_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_raw_scope_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_RESIDUAL_GAP_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_RESIDUAL_GAP_REPORT_PREP/machine/processed_value_source_map_completion_residual_gap_report_prep_summary.json"
)
SOURCE_RESIDUAL_GAP_MATRIX_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_RESIDUAL_GAP_REPORT_PREP/machine/processed_value_source_map_completion_residual_gap_matrix_public_safe.json"
)
SOURCE_PRIVATE_GAP_REPORT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_residual_gap_report_prep/private_residual_gap_report.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_raw_scope_intake"
PRIVATE_SCOPE_RECORD_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_raw_scope_intake.json"
PRIVATE_SCOPE_MARKDOWN_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_raw_scope_intake.md"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_raw_scope_intake_diagnostic.json"


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
        "raw_root_existence_stat_performed_by_this_phase": True,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_file_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
        "raw_inbox_parse_performed_by_this_phase": False,
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
        "private_source_gap_report_committed": False,
        "private_raw_scope_record_committed": False,
        "private_raw_scope_markdown_committed": False,
        "private_diagnostic_committed": False,
        "raw_root_path_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "processed_value_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _scope_matrix() -> dict[str, Any]:
    scope_items = [
        {
            "scope_code": "RAW_ROOT_EXISTENCE_PRECHECK",
            "public_description": "仅确认私有 raw 根目录存在且为目录。",
            "allowed_this_phase": True,
            "performed_this_phase": True,
            "raw_content_access": False,
        },
        {
            "scope_code": "RAW_FILE_LISTING",
            "public_description": "列出 raw 文件名或目录树。",
            "allowed_this_phase": False,
            "performed_this_phase": False,
            "raw_content_access": False,
        },
        {
            "scope_code": "RAW_FILE_HASHING_OR_PARSE",
            "public_description": "对 raw 文件做 hash、解析、字段读取或值抽取。",
            "allowed_this_phase": False,
            "performed_this_phase": False,
            "raw_content_access": True,
        },
        {
            "scope_code": "RAW_TO_PROCESSED_COMPARISON",
            "public_description": "执行 raw-to-processed value comparison。",
            "allowed_this_phase": False,
            "performed_this_phase": False,
            "raw_content_access": True,
        },
        {
            "scope_code": "CORRECTED_SOURCE_PACKAGE_REGISTRATION",
            "public_description": "登记新的修正源包。",
            "allowed_this_phase": True,
            "performed_this_phase": False,
            "raw_content_access": False,
        },
    ]
    return {
        "schema_version": "kmfa.v014_raw_scope_matrix_public_safe.v1",
        "record_type": "v014_raw_scope_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "scope_item_count": len(scope_items),
        "allowed_next_phase": NEXT_RECOMMENDED_PHASE,
        "scope_items": scope_items,
    }


def _build_private_scope(
    *,
    generated_at: str,
    residual_gap_summary: dict[str, Any],
    private_gap_report: dict[str, Any],
    raw_root_exists: bool,
    raw_root_is_dir: bool,
    scope_matrix: dict[str, Any],
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    private_scope = {
        "schema_version": "kmfa.private.v014_corrected_source_or_raw_scope_intake.v1",
        "classification": "private_corrected_source_or_raw_scope_intake_do_not_commit",
        "record_type": "v014_corrected_source_or_raw_scope_intake",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision": DECISION,
        "source_residual_gap_phase_id": residual_gap_summary.get("phase_id"),
        "source_private_gap_report_phase_id": private_gap_report.get("phase_id"),
        "previous_required_input": PREVIOUS_REQUIRED_INPUT,
        "previous_required_input_resolved_by_this_phase": True,
        "corrected_source_package_supplied": False,
        "owner_authorized_private_raw_comparison_scope_registered": True,
        "raw_root_path": RAW_ROOT.as_posix(),
        "raw_root_exists": raw_root_exists,
        "raw_root_is_directory": raw_root_is_dir,
        "raw_root_existence_stat_performed_by_this_phase": True,
        "raw_file_listing_allowed_by_this_phase": False,
        "raw_file_listing_performed_by_this_phase": False,
        "raw_file_hash_or_parse_allowed_by_this_phase": False,
        "raw_to_processed_comparison_allowed_by_this_phase": False,
        "private_raw_comparison_preflight_ready": raw_root_exists and raw_root_is_dir,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "public_scope_matrix": scope_matrix,
        "raw_boundary": _raw_boundary(),
    }
    markdown = f"""# Private Corrected Source Or Raw Scope Intake

- decision: `{DECISION}`
- corrected source package supplied: `false`
- owner-authorized private raw comparison scope registered: `true`
- raw root exists: `{str(raw_root_exists).lower()}`
- raw root is directory: `{str(raw_root_is_dir).lower()}`
- raw file listing performed: `false`
- raw file hashing/parsing performed: `false`
- raw-to-processed comparison performed: `false`
- private raw comparison preflight ready: `{str(private_scope["private_raw_comparison_preflight_ready"]).lower()}`

The raw root path is private and must not be committed. The next phase may only
perform a private preflight; full value matching still requires a separate
phase and validation.
"""
    diagnostic = {
        "schema_version": "kmfa.private.v014_corrected_source_or_raw_scope_intake_diagnostic.v1",
        "classification": "private_corrected_source_or_raw_scope_intake_diagnostic_do_not_commit",
        "record_type": "v014_corrected_source_or_raw_scope_intake_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "raw_scope_registered": True,
        "raw_root_exists": raw_root_exists,
        "raw_root_is_directory": raw_root_is_dir,
        "private_raw_comparison_preflight_ready": raw_root_exists and raw_root_is_dir,
        "raw_boundary": _raw_boundary(),
    }
    return private_scope, markdown, diagnostic


def generate(generated_at: str | None = None, *, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    residual_gap_summary = _read_json(SOURCE_RESIDUAL_GAP_SUMMARY_PATH)
    residual_gap_matrix = _read_json(SOURCE_RESIDUAL_GAP_MATRIX_PATH)
    private_gap_report = _read_json(SOURCE_PRIVATE_GAP_REPORT_PATH)
    raw_root_exists = RAW_ROOT.exists()
    raw_root_is_dir = RAW_ROOT.is_dir()
    scope_matrix = _scope_matrix()
    private_scope, private_markdown, private_diagnostic = _build_private_scope(
        generated_at=timestamp,
        residual_gap_summary=residual_gap_summary,
        private_gap_report=private_gap_report,
        raw_root_exists=raw_root_exists,
        raw_root_is_dir=raw_root_is_dir,
        scope_matrix=scope_matrix,
    )
    _write_json(PRIVATE_SCOPE_RECORD_PATH, private_scope)
    _write_text(PRIVATE_SCOPE_MARKDOWN_PATH, private_markdown)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)

    private_preflight_ready = raw_root_exists and raw_root_is_dir
    summary = {
        "schema_version": "kmfa.v014_corrected_source_or_raw_scope_intake_summary.v1",
        "record_type": "v014_corrected_source_or_raw_scope_intake_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_residual_gap_phase_id": residual_gap_summary.get("phase_id"),
        "source_residual_gap_decision": residual_gap_summary.get("decision"),
        "source_residual_gap_matrix_category_count": residual_gap_matrix.get("gap_category_count"),
        "source_private_gap_report_read_performed_by_this_phase": True,
        "previous_required_input": PREVIOUS_REQUIRED_INPUT,
        "previous_required_input_resolved_by_this_phase": True,
        "corrected_source_package_supplied": False,
        "owner_authorized_private_raw_comparison_scope_registered": True,
        "raw_root_exists_private": raw_root_exists,
        "raw_root_is_directory_private": raw_root_is_dir,
        "raw_root_existence_stat_performed_by_this_phase": True,
        "raw_file_listing_performed_by_this_phase": False,
        "raw_file_hash_or_parse_performed_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "private_raw_comparison_preflight_ready": private_preflight_ready,
        "scope_item_count": scope_matrix["scope_item_count"],
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_allowed": False,
        "app_reinstall_performed": False,
        "business_execution_allowed": False,
        "business_execution_performed": False,
        "full_source_map_completion_reapplication_ready": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "business_value_consistency_verified": False,
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "private_scope_record_written": PRIVATE_SCOPE_RECORD_PATH.exists(),
        "private_scope_record_gitignored": _git_check_ignored(PRIVATE_SCOPE_RECORD_PATH),
        "private_scope_markdown_written": PRIVATE_SCOPE_MARKDOWN_PATH.exists(),
        "private_scope_markdown_gitignored": _git_check_ignored(PRIVATE_SCOPE_MARKDOWN_PATH),
        "private_diagnostic_written": PRIVATE_DIAGNOSTIC_PATH.exists(),
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "public_safety": _public_safety(),
        "raw_boundary": _raw_boundary(),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }
    go_no_go = {
        "schema_version": "kmfa.v014_corrected_source_or_raw_scope_intake_go_no_go.v1",
        "record_type": "v014_corrected_source_or_raw_scope_intake_go_no_go_report",
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
        "corrected_source_package_supplied": False,
        "private_raw_comparison_preflight_ready": private_preflight_ready,
        "delivery_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_corrected_source_or_raw_scope_intake_manifest.v1",
        "record_type": "v014_corrected_source_or_raw_scope_intake_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "git_head": _git_output(["rev-parse", "HEAD"]),
        "git_branch": _git_output(["branch", "--show-current"]),
        "source_artifacts": [
            SOURCE_RESIDUAL_GAP_SUMMARY_PATH.as_posix(),
            SOURCE_RESIDUAL_GAP_MATRIX_PATH.as_posix(),
            "private:residual_gap_report",
        ],
        "public_outputs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            SCOPE_MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            SCOPE_RECORD_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_SCOPE_MATRIX_PATH.as_posix(),
        ],
        "private_outputs": [
            "private:corrected_source_or_raw_scope_intake",
            "private:corrected_source_or_raw_scope_intake_markdown",
            "private:corrected_source_or_raw_scope_intake_diagnostic",
        ],
        "summary": summary,
        "go_no_go": go_no_go,
        "scope_matrix": scope_matrix,
    }
    report = f"""# Corrected Source Or Raw Scope Intake

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- corrected source package supplied: `false`
- private raw comparison scope registered: `true`
- private raw comparison preflight ready: `{str(private_preflight_ready).lower()}`
- scope items: `{scope_matrix["scope_item_count"]}`
- raw file listing performed: `false`
- raw file hashing/parsing performed: `false`
- raw-to-processed comparison performed: `false`
- delivery allowed: `false`

This phase only checks whether the private raw root exists as a directory and
records the next private preflight scope. It does not expose the raw path in
public artifacts.
"""
    scope_record = f"""# Public-Safe Raw Scope Intake

## Scope

- Corrected source package supplied: `false`
- Private raw comparison scope registered: `true`
- Private raw comparison preflight ready: `{str(private_preflight_ready).lower()}`
- Scope item count: `{scope_matrix["scope_item_count"]}`

## Not Performed

- Raw file listing: `false`
- Raw file hashing/parsing: `false`
- Raw-to-processed comparison: `false`
- Source-map reapplication: `false`
- Delivery / GitHub upload / app reinstall / business execution: `false`
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- private_raw_comparison_preflight_ready: `{str(private_preflight_ready).lower()}`
- delivery_allowed: `false`
- github_upload_allowed: `false`
- app_reinstall_allowed: `false`
- business_execution_allowed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating scope registration as value matching.
  Mitigation: raw file listing, parsing, hashing and comparison remain blocked.
- Risk: leaking raw path or filenames publicly.
  Mitigation: public artifacts contain only booleans and scope codes; private path stays ignored.
"""
    rollback_plan = """# Rollback Plan

No raw file, source-map file, corrected source package, comparison result, report release artifact or business output was modified. To roll back, remove this phase's public artifacts and ignored private scope outputs.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_raw_scope_intake.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_raw_scope_intake.py --require-private-scope`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_corrected_source_or_raw_scope_intake`
"""
    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (SCOPE_MATRIX_PATH, scope_matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_SCOPE_MATRIX_PATH, scope_matrix),
    ):
        _write_json(path, payload)
    for path, text in (
        (REPORT_PATH, report),
        (SCOPE_RECORD_PATH, scope_record),
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-RAW-SCOPE-INTAKE"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-CORRECTED-SOURCE-OR-RAW-SCOPE-INTAKE",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "corrected_source_package_supplied": False,
        "private_raw_comparison_preflight_ready": summary["private_raw_comparison_preflight_ready"],
        "delivery_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "raw_root_existence_stat_performed": True,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "result_commit": "PENDING",
        "summary": "Registered private raw comparison preflight scope without listing, reading, hashing, parsing, or mutating raw files.",
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
        "PASS: KMFA v0.1.4 corrected source or raw scope intake generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"preflight={manifest['summary']['private_raw_comparison_preflight_ready']}, "
        f"scope_items={manifest['summary']['scope_item_count']})"
    )


if __name__ == "__main__":
    main()
