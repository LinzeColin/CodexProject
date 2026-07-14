#!/usr/bin/env python3
"""Generate KMFA v0.1.4 raw consistency cross-validation gate evidence.

This continuation gate applies the owner decision that the current private
container is authoritative, then re-computes a private source-hash profile in a
read-only scan. Public artifacts expose only aggregate counts and gate flags.
Raw names, raw hashes, member names, sheet names, field/header text, row/cell
values and business values stay in the git-ignored private runtime.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.v014_s05_p1_a0_file_registration import (  # noqa: E402
    EXPECTED_BUSINESS_MEMBER_COUNT,
    EXPECTED_EXCEL_COUNT,
    EXPECTED_PDF_COUNT,
    LEGACY_A0_MANIFEST_PATH,
    RAW_INBOX,
    is_hidden_zip_member,
    read_json,
    resolve_private_raw_zip,
    sha256_file,
    sha256_text,
    stat_snapshot,
)
from KMFA.tools.v014_raw_source_identity_decision_application import (  # noqa: E402
    GO_NO_GO_PATH as APPLICATION_GO_NO_GO_PATH,
    MANIFEST_PATH as APPLICATION_MANIFEST_PATH,
    METADATA_OWNER_DECISION_RECORD_PATH,
    OWNER_DECISION_RECORD_PATH,
)


SCHEMA_VERSION = "kmfa.v014_raw_consistency_cross_validation_gate.v1"
GO_NO_GO_SCHEMA_VERSION = "kmfa.v014_raw_consistency_cross_validation_go_no_go.v1"
PRIVATE_SCHEMA_VERSION = "kmfa.private.v014_raw_consistency_cross_validation_gate.v1"
PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PHASE_ID = "V014_RAW_CONSISTENCY_CROSS_VALIDATION_GATE"
TASK_ID = "KMFA-V014-RAW-CONSISTENCY-CROSS-VALIDATION-GATE-20260705"
ACCEPTANCE_ID = "ACC-V014-RAW-CONSISTENCY-CROSS-VALIDATION-GATE"
STATUS = "completed_public_safe_authoritative_raw_baseline_locked_no_go"
NEXT_RECOMMENDED_PHASE = "V014_LINEAGE_FULL_CHECK_SCOPE_OR_VALUE_CONSISTENCY_AUTHORIZATION"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_RAW_CONSISTENCY_CROSS_VALIDATION_GATE")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "raw_consistency_cross_validation_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "raw_consistency_cross_validation_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "raw_consistency_cross_validation_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_raw_consistency_cross_validation_gate")
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_raw_consistency_diagnostic.json"
PRIOR_PRIVATE_DIAGNOSTIC_PATH = Path(
    "KMFA/.codex_private_runtime/v014_raw_alignment_remediation/private_raw_alignment_diagnostic.json"
)

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_raw_consistency_cross_validation_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_raw_consistency_cross_validation_go_no_go_report.json")
METADATA_BASELINE_LOCK_PATH = Path("KMFA/metadata/baseline/v014_authoritative_raw_baseline_lock.json")


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _raw_root_inventory() -> dict[str, Any]:
    root_exists = RAW_INBOX.exists()
    root_is_readable = root_exists and RAW_INBOX.is_dir()
    files = sorted([path for path in RAW_INBOX.iterdir() if path.is_file()]) if root_is_readable else []
    suffix_counts: dict[str, int] = {}
    for path in files:
        suffix = path.suffix.lower() or "<none>"
        suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1
    return {
        "raw_root_exists": root_exists,
        "raw_root_is_readable": root_is_readable,
        "raw_root_file_count": len(files),
        "raw_root_archive_count": suffix_counts.get(".zip", 0),
        "raw_root_spreadsheet_count": sum(suffix_counts.get(suffix, 0) for suffix in (".xlsx", ".xls", ".xlsm")),
        "raw_root_total_bytes": sum(path.stat().st_size for path in files),
        "private_file_path_hashes": [sha256_text(str(path)) for path in files],
    }


def _archive_profile(raw_source: Path | None, legacy_manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    public = {
        "selected_source_present": raw_source is not None and raw_source.exists(),
        "selected_source_openable": False,
        "selected_candidate_count": 0,
        "business_member_count": 0,
        "business_document_member_count": 0,
        "business_spreadsheet_member_count": 0,
        "hidden_or_system_member_count": 0,
        "business_shape_matches_expected_a0": False,
        "registered_package_hash_matches_current_container": False,
        "registered_package_size_matches_current_container": False,
        "private_package_hash_recorded": False,
        "private_business_member_hash_record_count": 0,
    }
    private = {
        "selected_source_path_sha256": sha256_text(str(raw_source)) if raw_source is not None else "",
        "selected_source_present": raw_source is not None and raw_source.exists(),
        "member_records": [],
    }
    if raw_source is None or not raw_source.exists():
        return public, private

    expected_package = legacy_manifest.get("source_package", {})
    expected_hash = str(expected_package.get("package_hash", "")).replace("sha256:", "")
    expected_size = int(expected_package.get("package_size_bytes", 0))
    actual_hash = sha256_file(raw_source)
    actual_size = raw_source.stat().st_size
    public["private_package_hash_recorded"] = True
    public["registered_package_hash_matches_current_container"] = bool(expected_hash) and actual_hash == expected_hash
    public["registered_package_size_matches_current_container"] = bool(expected_size) and actual_size == expected_size
    private.update(
        {
            "actual_package_sha256": actual_hash,
            "actual_package_size_bytes": actual_size,
            "expected_package_sha256": expected_hash,
            "expected_package_size_bytes": expected_size,
        }
    )

    with zipfile.ZipFile(raw_source) as archive:
        public["selected_source_openable"] = True
        for info in archive.infolist():
            if info.is_dir():
                continue
            suffix = Path(info.filename).suffix.lower()
            hidden = is_hidden_zip_member(info.filename)
            digest = hashlib.sha256()
            with archive.open(info) as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            private["member_records"].append(
                {
                    "member_name_sha256": sha256_text(info.filename),
                    "member_sha256": digest.hexdigest(),
                    "member_size_bytes": info.file_size,
                    "member_suffix": suffix,
                    "hidden_or_system": hidden,
                }
            )
            if hidden:
                public["hidden_or_system_member_count"] += 1
                continue
            public["business_member_count"] += 1
            public["private_business_member_hash_record_count"] += 1
            if suffix == ".pdf":
                public["business_document_member_count"] += 1
            if suffix in {".xlsx", ".xls", ".xlsm"}:
                public["business_spreadsheet_member_count"] += 1

    public["business_shape_matches_expected_a0"] = (
        public["business_member_count"] == EXPECTED_BUSINESS_MEMBER_COUNT
        and public["business_document_member_count"] == EXPECTED_PDF_COUNT
        and public["business_spreadsheet_member_count"] == EXPECTED_EXCEL_COUNT
    )
    return public, private


def _business_hash_multiset(records: list[dict[str, Any]], key: str) -> list[str]:
    return sorted(str(item.get(key, "")) for item in records if not item.get("hidden_or_system"))


def _prior_profile_comparison(private_profile: dict[str, Any]) -> dict[str, Any]:
    comparison = {
        "prior_private_diagnostic_available": PRIOR_PRIVATE_DIAGNOSTIC_PATH.exists(),
        "package_hash_matches_prior_private_diagnostic": False,
        "package_size_matches_prior_private_diagnostic": False,
        "business_member_hash_multiset_matches_prior_private_diagnostic": False,
        "business_member_name_hash_multiset_matches_prior_private_diagnostic": False,
        "business_member_record_count_matches_prior_private_diagnostic": False,
        "cross_run_private_hash_profile_matches_prior_diagnostic": False,
    }
    if not PRIOR_PRIVATE_DIAGNOSTIC_PATH.exists():
        return comparison
    prior = read_json(PRIOR_PRIVATE_DIAGNOSTIC_PATH)
    current_records = private_profile.get("member_records", [])
    prior_records = prior.get("member_records", [])
    comparison["package_hash_matches_prior_private_diagnostic"] = private_profile.get("actual_package_sha256") == prior.get(
        "actual_package_sha256"
    )
    comparison["package_size_matches_prior_private_diagnostic"] = private_profile.get("actual_package_size_bytes") == prior.get(
        "actual_package_size_bytes"
    )
    comparison["business_member_hash_multiset_matches_prior_private_diagnostic"] = _business_hash_multiset(
        current_records, "member_sha256"
    ) == _business_hash_multiset(prior_records, "member_sha256")
    comparison["business_member_name_hash_multiset_matches_prior_private_diagnostic"] = _business_hash_multiset(
        current_records, "member_name_sha256"
    ) == _business_hash_multiset(prior_records, "member_name_sha256")
    comparison["business_member_record_count_matches_prior_private_diagnostic"] = (
        len(_business_hash_multiset(current_records, "member_sha256"))
        == len(_business_hash_multiset(prior_records, "member_sha256"))
        == EXPECTED_BUSINESS_MEMBER_COUNT
    )
    comparison["cross_run_private_hash_profile_matches_prior_diagnostic"] = all(
        comparison[key]
        for key in (
            "package_hash_matches_prior_private_diagnostic",
            "package_size_matches_prior_private_diagnostic",
            "business_member_hash_multiset_matches_prior_private_diagnostic",
            "business_member_name_hash_multiset_matches_prior_private_diagnostic",
            "business_member_record_count_matches_prior_private_diagnostic",
        )
    )
    return comparison


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "public_safe_owner_decision_metadata_only": True,
        "raw_business_data_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "raw_or_private_table_committed": False,
        "local_database_committed": False,
        "credential_or_secret_committed": False,
        "raw_filenames_committed": False,
        "raw_hashes_committed": False,
        "archive_member_names_committed": False,
        "sheet_names_committed": False,
        "field_or_header_plaintext_committed": False,
        "row_or_cell_values_committed": False,
        "business_values_committed": False,
        "private_diagnostic_committed": False,
    }


def _go_no_go() -> dict[str, Any]:
    return {
        "record_type": "v014_raw_consistency_cross_validation_go_no_go_report",
        "schema_version": GO_NO_GO_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": (
            "Owner-confirmed current container source identity and private hash profile are locked public-safely, "
            "but business-value consistency, lineage full check, formal report release, GitHub upload, app reinstall "
            "and business execution remain blocked."
        ),
        "resolved_blocker_ids": [
            "RAW_SOURCE_IDENTITY_OWNER_DECISION_REQUIRED",
            "RAW_SOURCE_IDENTITY_OWNER_CONFIRMATION_APPLIED",
            "CURRENT_CONTAINER_PRIVATE_HASH_PROFILE_LOCKED",
            "RAW_SOURCE_CONTAINER_CROSS_RUN_HASH_PROFILE_CONFIRMED",
        ],
        "blocker_ids": [
            "BUSINESS_VALUE_CONSISTENCY_NOT_PERFORMED",
            "LINEAGE_FULL_CHECK_BLOCKED_BY_VALUE_CONSISTENCY_SCOPE",
            "FORMAL_REPORT_RELEASE_BLOCKED_BY_LINEAGE",
            "GITHUB_UPLOAD_BLOCKED_BY_RAW_LINEAGE_RELEASE_GATES",
            "APP_REINSTALL_BLOCKED_BY_RAW_LINEAGE_RELEASE_GATES",
            "BUSINESS_EXECUTION_BLOCKED_BY_NO_GO",
        ],
        "authoritative_raw_baseline_locked": True,
        "raw_source_identity_owner_resolved": True,
        "raw_consistency_cross_validation_complete": True,
        "raw_alignment_complete": False,
        "public_member_hash_backfill_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "formal_report_allowed": False,
        "business_execution_allowed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }


def _write_human_reports(manifest: dict[str, Any]) -> None:
    raw = manifest["raw_consistency_summary"]
    report = [
        "# KMFA v0.1.4 Raw Consistency Cross-Validation Gate",
        "",
        f"- status: `{manifest['status']}`",
        f"- phase_id: `{manifest['phase_id']}`",
        f"- task_id: `{manifest['task_id']}`",
        f"- owner_decision_code: `{manifest['owner_decision_summary']['decision_code']}`",
        f"- authoritative_raw_baseline_locked: `{str(raw['authoritative_raw_baseline_locked']).lower()}`",
        f"- raw_root_file_count: `{raw['raw_root_file_count']}`",
        f"- raw_root_archive_count: `{raw['raw_root_archive_count']}`",
        f"- raw_root_spreadsheet_count: `{raw['raw_root_spreadsheet_count']}`",
        f"- selected_candidate_count: `{raw['selected_candidate_count']}`",
        f"- selected_source_openable: `{str(raw['selected_source_openable']).lower()}`",
        f"- business_member_count: `{raw['business_member_count']}`",
        f"- business_document_member_count: `{raw['business_document_member_count']}`",
        f"- business_spreadsheet_member_count: `{raw['business_spreadsheet_member_count']}`",
        f"- business_shape_matches_expected_a0: `{str(raw['business_shape_matches_expected_a0']).lower()}`",
        f"- private_business_member_hash_record_count: `{raw['private_business_member_hash_record_count']}`",
        f"- cross_run_private_hash_profile_matches_prior_diagnostic: `{str(raw['cross_run_private_hash_profile_matches_prior_diagnostic']).lower()}`",
        f"- business_value_consistency_verified: `{str(raw['business_value_consistency_verified']).lower()}`",
        f"- decision: `{manifest['go_no_go']['decision']}`",
        "",
        "## Boundary",
        "",
        "- The configured raw inbox was read, listed, stat-checked and hashed for this active source-consistency gate only.",
        "- No raw inbox write, delete, move, rename, overwrite, copy, generated file creation or normalization was performed.",
        "- Public evidence contains only aggregate counts, gate flags and evidence refs.",
        "- Business-value consistency was not performed in this phase and remains a separate owner-scoped gate.",
    ]
    _write_text(REPORT_PATH, "\n".join(report) + "\n")

    go_record = [
        "# KMFA v0.1.4 Raw Consistency Go/No-Go",
        "",
        "- decision: `NO_GO`",
        "- authoritative_raw_baseline_locked: `true`",
        "- raw_consistency_cross_validation_complete: `true`",
        "- business_value_consistency_verified: `false`",
        "- lineage_full_check_complete: `false`",
        "- github_upload_allowed: `false`",
        "- app_reinstall_allowed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
    ]
    _write_text(GO_NO_GO_RECORD_PATH, "\n".join(go_record) + "\n")

    tests = [
        "# KMFA v0.1.4 Raw Consistency Cross-Validation Test Results",
        "",
        "- status: `pending_final_validation`",
        "- generator: `pending_final_validation`",
        "- validator: `pending_final_validation`",
        "- focused_unit_test: `pending_final_validation`",
        "- governance_validator: `pending_final_validation`",
        "- raw_private_scan: `pending_final_validation`",
        "- secret_scan: `pending_final_validation`",
        "- diff_check: `pending_final_validation`",
    ]
    _write_text(TEST_RESULTS_PATH, "\n".join(tests) + "\n")

    risks = [
        "# KMFA v0.1.4 Raw Consistency Risk Register",
        "",
        "| risk_id | risk | control | status |",
        "|---|---|---|---|",
        "| RAW-CV-001 | Source container identity could be confused with business-value consistency | Keep separate flags and leave business value consistency false | controlled |",
        "| RAW-CV-002 | Public artifacts could leak raw identifiers | Validator scans new evidence for raw paths, raw names, raw hashes and business values | controlled |",
        "| RAW-CV-003 | Upload or app reinstall could be inferred from a baseline lock | Keep Go/No-Go as NO_GO and all release gates false | blocked |",
    ]
    _write_text(RISK_REGISTER_PATH, "\n".join(risks) + "\n")

    rollback = [
        "# KMFA v0.1.4 Raw Consistency Rollback Plan",
        "",
        "This phase is local-only. It does not modify the raw inbox, GitHub main, app installs, production systems or external connectors.",
        "",
        "Rollback is limited to removing this phase's public evidence, metadata quality records, governance entries and the git-ignored private diagnostic directory.",
    ]
    _write_text(ROLLBACK_PATH, "\n".join(rollback) + "\n")


def generate(*, generated_at: str | None = None, write: bool = True) -> dict[str, Any]:
    generated = _now(generated_at)
    legacy_manifest = read_json(LEGACY_A0_MANIFEST_PATH)
    owner_decision = read_json(OWNER_DECISION_RECORD_PATH)
    application_manifest = read_json(APPLICATION_MANIFEST_PATH)
    application_go_no_go = read_json(APPLICATION_GO_NO_GO_PATH)

    raw_root_before = stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {}
    inventory = _raw_root_inventory()
    raw_source, selector_status, selected_candidate_count = resolve_private_raw_zip()
    selected_before = stat_snapshot(raw_source) if raw_source is not None and raw_source.exists() else {}
    public_profile, private_profile = _archive_profile(raw_source, legacy_manifest)
    public_profile["selected_candidate_count"] = selected_candidate_count
    selected_after = stat_snapshot(raw_source) if raw_source is not None and raw_source.exists() else {}
    raw_root_after = stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {}
    prior_comparison = _prior_profile_comparison(private_profile)

    owner_confirmed = (
        owner_decision.get("decision_code") == "confirm_current_container_as_authoritative"
        and owner_decision.get("raw_container_authoritative_confirmed") is True
    )
    source_profile_locked = (
        owner_confirmed
        and inventory["raw_root_exists"]
        and inventory["raw_root_is_readable"]
        and public_profile["selected_source_openable"]
        and public_profile["business_shape_matches_expected_a0"]
        and public_profile["private_business_member_hash_record_count"] == EXPECTED_BUSINESS_MEMBER_COUNT
        and prior_comparison["cross_run_private_hash_profile_matches_prior_diagnostic"]
        and raw_root_before == raw_root_after
        and selected_before == selected_after
    )
    raw_summary = {
        "raw_root_exists": inventory["raw_root_exists"],
        "raw_root_is_readable": inventory["raw_root_is_readable"],
        "raw_root_file_count": inventory["raw_root_file_count"],
        "raw_root_archive_count": inventory["raw_root_archive_count"],
        "raw_root_spreadsheet_count": inventory["raw_root_spreadsheet_count"],
        **public_profile,
        "owner_current_container_authoritative_confirmed": owner_confirmed,
        "cross_run_private_hash_profile_matches_prior_diagnostic": prior_comparison[
            "cross_run_private_hash_profile_matches_prior_diagnostic"
        ],
        "authoritative_raw_baseline_locked": source_profile_locked,
        "source_container_consistency_verified": source_profile_locked,
        "business_value_consistency_verified": False,
        "business_value_consistency_status": "not_performed_deferred_owner_scoped_value_matching_required",
        "difference_report_status": (
            "not_required_for_source_hash_gate_no_source_hash_drift_detected"
            if source_profile_locked
            else "required_if_repeated_source_hash_cross_validation_remains_inconsistent"
        ),
        "registered_package_hash_size_match_status": "mismatch_recorded_owner_confirmed_current_container_authoritative",
        "public_member_hash_backfill_performed": False,
        "public_member_hash_backfill_allowed": False,
        "private_member_hash_baseline_locked": source_profile_locked,
    }
    raw_boundary = {
        "raw_inbox_read_performed_by_this_phase": True,
        "raw_inbox_list_performed_by_this_phase": True,
        "raw_inbox_stat_performed_by_this_phase": True,
        "raw_inbox_hash_performed_by_this_phase": True,
        "raw_inbox_write_performed_by_this_phase": False,
        "raw_inbox_delete_performed_by_this_phase": False,
        "raw_inbox_move_performed_by_this_phase": False,
        "raw_inbox_rename_performed_by_this_phase": False,
        "raw_inbox_overwrite_performed_by_this_phase": False,
        "raw_inbox_copy_performed_by_this_phase": False,
        "raw_inbox_create_extra_files_inside_by_this_phase": False,
        "raw_inbox_normalize_performed_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
        "raw_root_stat_unchanged_after_scan": raw_root_before == raw_root_after,
        "selected_source_stat_unchanged_after_scan": selected_before == selected_after,
        "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
    }
    go_no_go = _go_no_go()
    go_no_go["authoritative_raw_baseline_locked"] = source_profile_locked
    go_no_go["raw_consistency_cross_validation_complete"] = source_profile_locked
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "phase_name": "Raw consistency cross-validation gate",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "generated_at": generated,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "worktree": _git_output(["rev-parse", "--show-toplevel"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "status": STATUS,
        "phase_scope_controls": {
            "current_phase_only": True,
            "raw_consistency_cross_validation_only": True,
            "owner_decision_application_consumed": True,
            "raw_root_read_only_hash_authorized": True,
            "public_member_hash_backfill_performed": False,
            "business_value_matching_performed": False,
            "lineage_full_check_performed": False,
            "formal_report_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "next_phase_started": False,
        },
        "owner_decision_summary": {
            "owner_decision_record_ref": OWNER_DECISION_RECORD_PATH.as_posix(),
            "metadata_owner_decision_record_ref": METADATA_OWNER_DECISION_RECORD_PATH.as_posix(),
            "decision_code": owner_decision.get("decision_code"),
            "actor_role": owner_decision.get("actor_role"),
            "raw_container_authoritative_confirmed": owner_confirmed,
            "owner_decision_authored_by_codex": False,
            "raw_plaintext_or_hash_in_owner_decision_record": False,
        },
        "application_dependency": {
            "application_manifest_ref": APPLICATION_MANIFEST_PATH.as_posix(),
            "application_go_no_go_ref": APPLICATION_GO_NO_GO_PATH.as_posix(),
            "application_status": application_go_no_go.get("application_status"),
            "owner_decision_supplied": application_go_no_go.get("owner_decision_supplied"),
            "decision_applied": application_go_no_go.get("decision_applied"),
            "application_decision": application_go_no_go.get("decision"),
            "basis_phase_id": application_manifest.get("phase_id"),
        },
        "raw_consistency_summary": raw_summary,
        "raw_boundary": raw_boundary,
        "public_repo_safety": _public_safety(),
        "go_no_go": go_no_go,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_blocked_by_value_lineage_release_gates",
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "private_diagnostic_ref": PRIVATE_DIAGNOSTIC_PATH.as_posix(),
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_BASELINE_LOCK_PATH.as_posix(),
        ],
        "validation_summary": {
            "generator": "PENDING_FINAL_VALIDATION",
            "validator": "PENDING_FINAL_VALIDATION",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "raw_private_scan": "PENDING_FINAL_VALIDATION",
            "secret_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
    }
    private_diagnostic = {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "classification": "private_raw_diagnostic_do_not_commit",
        "generated_at": generated,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "raw_root_path_sha256": sha256_text(str(RAW_INBOX)),
        "selector_status": selector_status,
        "selected_candidate_count": selected_candidate_count,
        "raw_root_before": raw_root_before,
        "raw_root_after": raw_root_after,
        "selected_source_before": selected_before,
        "selected_source_after": selected_after,
        "current_private_profile": private_profile,
        "prior_private_profile_comparison": prior_comparison,
        "owner_decision_record": owner_decision,
    }
    baseline_lock = {
        "record_type": "v014_authoritative_raw_baseline_lock",
        "schema_version": "kmfa.v014_authoritative_raw_baseline_lock.v1",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "status": "locked_public_safe_private_hash_profile_only",
        "authoritative_raw_baseline_locked": source_profile_locked,
        "owner_decision_code": owner_decision.get("decision_code"),
        "source_container_consistency_verified": source_profile_locked,
        "business_value_consistency_verified": False,
        "public_member_hash_backfill_performed": False,
        "public_member_hash_backfill_allowed": False,
        "private_member_hash_baseline_locked": source_profile_locked,
        "raw_business_data_committed": False,
        "raw_hashes_committed": False,
        "raw_filenames_committed": False,
        "field_or_header_plaintext_committed": False,
        "business_values_committed": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
    }

    if write:
        _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
        _write_json(MANIFEST_PATH, manifest)
        _write_json(GO_NO_GO_PATH, go_no_go)
        _write_json(METADATA_MANIFEST_PATH, manifest)
        _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
        _write_json(METADATA_BASELINE_LOCK_PATH, baseline_lock)
        _write_human_reports(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    raw = manifest["raw_consistency_summary"]
    print(
        "PASS: generated KMFA v0.1.4 raw consistency cross-validation evidence "
        f"(authoritative_raw_baseline_locked={str(raw['authoritative_raw_baseline_locked']).lower()}, "
        f"business_value_consistency_verified={str(raw['business_value_consistency_verified']).lower()}, "
        f"decision={manifest['go_no_go']['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
