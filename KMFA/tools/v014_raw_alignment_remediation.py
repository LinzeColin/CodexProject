#!/usr/bin/env python3
"""Generate KMFA v0.1.4 raw alignment remediation evidence.

This phase is intentionally a NO-GO remediation/reporting phase. It may read,
list, stat and hash the configured raw inbox to explain the local A0 source
identity mismatch, but public artifacts keep only aggregate counts and status
flags. Package hashes, member hashes and raw source identifiers stay in the
git-ignored private runtime.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.v014_s05_p1_a0_file_registration import (
    EXPECTED_BUSINESS_MEMBER_COUNT,
    EXPECTED_EXCEL_COUNT,
    EXPECTED_PDF_COUNT,
    LEGACY_A0_MANIFEST_PATH,
    RAW_INBOX,
    git_output,
    is_hidden_zip_member,
    read_json,
    resolve_private_raw_zip,
    sha256_file,
    sha256_text,
    stat_snapshot,
)


SCHEMA_VERSION = "kmfa.v014_raw_alignment_remediation.v1"
PRIVATE_SCHEMA_VERSION = "kmfa.private.v014_raw_alignment_remediation.v1"
TASK_ID = "KMFA-V014-RAW-ALIGNMENT-REMEDIATION-20260705"
ACCEPTANCE_ID = "ACC-V014-RAW-ALIGNMENT-REMEDIATION"
PHASE_ID = "V014_RAW_ALIGNMENT_REMEDIATION"
STATUS = "raw_alignment_remediation_reported_no_go_owner_source_identity_required"
NEXT_PHASE = "V014_OWNER_RAW_SOURCE_IDENTITY_DECISION"
PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_raw_alignment_remediation")
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_raw_alignment_diagnostic.json"
OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_RAW_ALIGNMENT_REMEDIATION")
MANIFEST_PATH = OUTPUT_DIR / "machine/raw_alignment_remediation_manifest.json"
GO_NO_GO_PATH = OUTPUT_DIR / "machine/raw_alignment_go_no_go_report.json"
REPORT_PATH = OUTPUT_DIR / "human/raw_alignment_remediation_report.md"
GO_NO_GO_RECORD_PATH = OUTPUT_DIR / "human/go_no_go_record.md"
TEST_RESULTS_PATH = OUTPUT_DIR / "human/test_results.md"
RISK_REGISTER_PATH = OUTPUT_DIR / "human/risk_register.md"
ROLLBACK_PATH = OUTPUT_DIR / "human/rollback_plan.md"
METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_raw_alignment_remediation_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_raw_alignment_go_no_go_report.json")


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
        "suffix_counts": suffix_counts,
        "private_file_path_hashes": [sha256_text(str(path)) for path in files],
    }


def _inspect_selected_archive(raw_zip: Path | None, legacy_manifest: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "selected_archive_openable": False,
        "business_member_count": 0,
        "business_document_member_count": 0,
        "business_spreadsheet_member_count": 0,
        "hidden_or_system_member_count": 0,
        "business_shape_matches_expected_a0": False,
        "package_hash_matches_registered": False,
        "package_size_matches_registered": False,
        "private_member_hashes_recorded": False,
        "public_member_hash_backfill_allowed": False,
        "raw_alignment_complete": False,
        "remediation_status": "raw_candidate_missing_owner_source_identity_decision_required",
    }
    private_details: dict[str, Any] = {
        "selected_raw_path_sha256": sha256_text(str(raw_zip)) if raw_zip is not None else "",
        "selected_raw_package_present": raw_zip is not None and raw_zip.exists(),
        "member_records": [],
    }
    if raw_zip is None or not raw_zip.exists():
        return {"summary": summary, "private_details": private_details}

    expected_package = legacy_manifest.get("source_package", {})
    expected_hash = str(expected_package.get("package_hash", "")).replace("sha256:", "")
    expected_size = int(expected_package.get("package_size_bytes", 0))
    actual_hash = sha256_file(raw_zip)
    actual_size = raw_zip.stat().st_size
    private_details.update(
        {
            "actual_package_sha256": actual_hash,
            "actual_package_size_bytes": actual_size,
            "expected_package_sha256": expected_hash,
            "expected_package_size_bytes": expected_size,
        }
    )
    summary["package_hash_matches_registered"] = bool(expected_hash) and actual_hash == expected_hash
    summary["package_size_matches_registered"] = bool(expected_size) and actual_size == expected_size

    with zipfile.ZipFile(raw_zip) as archive:
        summary["selected_archive_openable"] = True
        for info in archive.infolist():
            if info.is_dir():
                continue
            suffix = Path(info.filename).suffix.lower()
            hidden = is_hidden_zip_member(info.filename)
            digest = hashlib.sha256()
            with archive.open(info) as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            private_details["member_records"].append(
                {
                    "member_name_sha256": sha256_text(info.filename),
                    "member_sha256": digest.hexdigest(),
                    "member_size_bytes": info.file_size,
                    "member_suffix": suffix,
                    "hidden_or_system": hidden,
                }
            )
            if hidden:
                summary["hidden_or_system_member_count"] += 1
                continue
            summary["business_member_count"] += 1
            if suffix == ".pdf":
                summary["business_document_member_count"] += 1
            if suffix in {".xlsx", ".xls", ".xlsm"}:
                summary["business_spreadsheet_member_count"] += 1

    summary["business_shape_matches_expected_a0"] = (
        summary["business_member_count"] == EXPECTED_BUSINESS_MEMBER_COUNT
        and summary["business_document_member_count"] == EXPECTED_PDF_COUNT
        and summary["business_spreadsheet_member_count"] == EXPECTED_EXCEL_COUNT
    )
    summary["private_member_hashes_recorded"] = (
        sum(1 for item in private_details["member_records"] if not item["hidden_or_system"])
        == EXPECTED_BUSINESS_MEMBER_COUNT
    )
    summary["raw_alignment_complete"] = (
        summary["business_shape_matches_expected_a0"]
        and summary["package_hash_matches_registered"]
        and summary["package_size_matches_registered"]
    )
    summary["public_member_hash_backfill_allowed"] = summary["raw_alignment_complete"]
    if summary["business_shape_matches_expected_a0"] and not summary["raw_alignment_complete"]:
        summary["remediation_status"] = (
            "container_mismatch_business_shape_match_private_only_owner_identity_decision_required"
        )
    elif summary["raw_alignment_complete"]:
        summary["remediation_status"] = "raw_alignment_complete_not_expected_for_this_phase"
    return {"summary": summary, "private_details": private_details}


def _private_diagnostic(
    *,
    generated_at: str,
    inventory: dict[str, Any],
    selector_status: str,
    selected_candidate_count: int,
    archive_private_details: dict[str, Any],
    raw_root_before: dict[str, int],
    raw_root_after: dict[str, int],
    selected_before: dict[str, int],
    selected_after: dict[str, int],
) -> dict[str, Any]:
    return {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "classification": "private_raw_diagnostic_do_not_commit",
        "generated_at": generated_at,
        "task_id": TASK_ID,
        "phase_id": PHASE_ID,
        "raw_root_path_sha256": sha256_text(str(RAW_INBOX)),
        "raw_root_file_count": inventory["raw_root_file_count"],
        "raw_root_archive_count": inventory["raw_root_archive_count"],
        "raw_root_spreadsheet_count": inventory["raw_root_spreadsheet_count"],
        "private_file_path_hashes": inventory["private_file_path_hashes"],
        "selector_status": selector_status,
        "selected_candidate_count": selected_candidate_count,
        "raw_root_before": raw_root_before,
        "raw_root_after": raw_root_after,
        "selected_source_before": selected_before,
        "selected_source_after": selected_after,
        **archive_private_details,
    }


def _go_no_go() -> dict[str, Any]:
    return {
        "record_type": "v014_raw_alignment_go_no_go_report",
        "project_id": "KMFA",
        "version": "0.1.4",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": (
            "Local raw archive business shape matches the public A0 expectation, but the container hash and size do "
            "not match the registered source package. Owner source identity confirmation is required before public "
            "hash backfill, lineage closure, report release, GitHub upload or app reinstall."
        ),
        "blocker_ids": [
            "RAW_CONTAINER_HASH_SIZE_MISMATCH",
            "RAW_SOURCE_IDENTITY_OWNER_DECISION_REQUIRED",
            "PUBLIC_MEMBER_HASH_BACKFILL_BLOCKED",
            "LINEAGE_FULL_CHECK_BLOCKED_BY_RAW_IDENTITY",
            "GITHUB_UPLOAD_BLOCKED_BY_RAW_ALIGNMENT",
            "APP_REINSTALL_BLOCKED_BY_RAW_ALIGNMENT",
        ],
        "resolved_blocker_ids": [],
        "raw_alignment_complete": False,
        "lineage_full_check_complete": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "formal_report_allowed": False,
        "business_execution_allowed": False,
        "next_required_phase": NEXT_PHASE,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "raw_business_data_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "raw_or_private_table_committed": False,
        "local_database_committed": False,
        "credential_or_secret_committed": False,
        "raw_filenames_committed": False,
        "raw_hashes_committed": False,
        "directory_tree_plaintext_committed": False,
        "zip_member_names_committed": False,
        "sheet_names_committed": False,
        "field_or_header_plaintext_committed": False,
        "row_or_cell_values_committed": False,
        "business_values_committed": False,
    }


def _write_human_reports(manifest: dict[str, Any]) -> None:
    raw = manifest["raw_source_identity_summary"]
    safety = manifest["public_repo_safety"]
    report_lines = [
        "# KMFA v0.1.4 Raw Alignment Remediation",
        "",
        f"- status: `{manifest['status']}`",
        f"- task_id: `{manifest['task_id']}`",
        f"- phase_id: `{manifest['phase_id']}`",
        f"- raw_root_file_count: `{raw['raw_root_file_count']}`",
        f"- raw_root_archive_count: `{raw['raw_root_archive_count']}`",
        f"- raw_root_spreadsheet_count: `{raw['raw_root_spreadsheet_count']}`",
        f"- selected_candidate_count: `{raw['selected_candidate_count']}`",
        f"- selected_archive_openable: `{str(raw['selected_archive_openable']).lower()}`",
        f"- business_member_count: `{raw['business_member_count']}`",
        f"- business_document_member_count: `{raw['business_document_member_count']}`",
        f"- business_spreadsheet_member_count: `{raw['business_spreadsheet_member_count']}`",
        f"- hidden_or_system_member_count: `{raw['hidden_or_system_member_count']}`",
        f"- business_shape_matches_expected_a0: `{str(raw['business_shape_matches_expected_a0']).lower()}`",
        f"- package_hash_matches_registered: `{str(raw['package_hash_matches_registered']).lower()}`",
        f"- package_size_matches_registered: `{str(raw['package_size_matches_registered']).lower()}`",
        f"- private_member_hashes_recorded: `{str(raw['private_member_hashes_recorded']).lower()}`",
        f"- public_member_hash_backfill_allowed: `{str(raw['public_member_hash_backfill_allowed']).lower()}`",
        f"- raw_alignment_complete: `{str(raw['raw_alignment_complete']).lower()}`",
        f"- decision: `{manifest['go_no_go']['decision']}`",
        "",
        "## Boundary",
        "",
        "- This phase read, listed, stat-checked and hashed the configured raw inbox because the active goal explicitly requires raw evidence alignment diagnostics.",
        "- No raw inbox mutation, deletion, move, rename, overwrite or generated file creation was performed.",
        "- Public evidence is aggregate-only and does not include raw names, raw hashes, archive member names, sheet names, field/header text, row/cell values or business values.",
        f"- public_safe_aggregate_only: `{str(safety['public_safe_aggregate_only']).lower()}`",
        "",
        "## Decision",
        "",
        "- The local container does not match the registered source package by hash/size, even though the public-safe business shape matches the expected A0 package shape.",
        "- The correct stop line is owner source identity confirmation before public hash backfill, lineage closure, report release, GitHub upload or app reinstall.",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    go_lines = [
        "# KMFA v0.1.4 Raw Alignment Go/No-Go",
        "",
        "- decision: `NO_GO`",
        "- raw_alignment_complete: `false`",
        "- github_upload_allowed: `false`",
        "- app_reinstall_allowed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        f"- next_required_phase: `{NEXT_PHASE}`",
    ]
    GO_NO_GO_RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)
    GO_NO_GO_RECORD_PATH.write_text("\n".join(go_lines) + "\n", encoding="utf-8")

    test_lines = [
        "# KMFA v0.1.4 Raw Alignment Remediation Test Results",
        "",
        "- status: `pending_final_validation`",
        f"- task_id: `{manifest['task_id']}`",
        "- focused_unit_test: `pending_final_validation`",
        "- raw_alignment_validator: `pending_final_validation`",
        "- governance_validator: `pending_final_validation`",
        "- raw_private_scan: `pending_final_validation`",
        "- secret_scan: `pending_final_validation`",
    ]
    TEST_RESULTS_PATH.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

    risk_lines = [
        "# KMFA v0.1.4 Raw Alignment Remediation Risk Register",
        "",
        "| risk_id | risk | control | status |",
        "|---|---|---|---|",
        "| RAW-ID-001 | Local raw container hash/size does not match registered source package | Keep NO_GO and require owner source identity decision | open |",
        "| RAW-ID-002 | Public artifacts could leak raw identifiers | Validator scans evidence for raw/private tokens and raw extensions | controlled |",
        "| RAW-ID-003 | Lineage closure could proceed from unconfirmed raw identity | Gate lineage full check behind owner source identity confirmation | blocked |",
    ]
    RISK_REGISTER_PATH.write_text("\n".join(risk_lines) + "\n", encoding="utf-8")

    rollback_lines = [
        "# KMFA v0.1.4 Raw Alignment Remediation Rollback Plan",
        "",
        "This phase is local-only and does not modify the raw inbox, GitHub main, app installs, production systems or external connectors.",
        "",
        "Rollback is limited to removing this phase's public evidence files, metadata quality records, governance entries and the git-ignored private diagnostic directory.",
    ]
    ROLLBACK_PATH.write_text("\n".join(rollback_lines) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    generated = _now(generated_at)
    legacy_manifest = read_json(LEGACY_A0_MANIFEST_PATH)
    raw_root_before = stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {}
    inventory = _raw_root_inventory()
    raw_zip, selector_status, selected_candidate_count = resolve_private_raw_zip()
    selected_before = stat_snapshot(raw_zip) if raw_zip is not None and raw_zip.exists() else {}
    archive_result = _inspect_selected_archive(raw_zip, legacy_manifest)
    selected_after = stat_snapshot(raw_zip) if raw_zip is not None and raw_zip.exists() else {}
    raw_root_after = stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {}

    raw_summary = {
        "raw_root_exists": inventory["raw_root_exists"],
        "raw_root_is_readable": inventory["raw_root_is_readable"],
        "raw_root_file_count": inventory["raw_root_file_count"],
        "raw_root_archive_count": inventory["raw_root_archive_count"],
        "raw_root_spreadsheet_count": inventory["raw_root_spreadsheet_count"],
        "selected_candidate_count": selected_candidate_count,
        **archive_result["summary"],
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
        "raw_inbox_create_extra_files_inside_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
        "raw_root_stat_unchanged_after_scan": raw_root_before == raw_root_after,
        "selected_source_stat_unchanged_after_scan": selected_before == selected_after,
        "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
    }
    go_no_go = _go_no_go()
    public_safety = _public_safety()
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "phase_id": PHASE_ID,
        "phase_name": "Raw alignment remediation",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "generated_at": generated,
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": STATUS,
        "phase_scope_controls": {
            "current_phase_only": True,
            "raw_source_identity_remediation_only": True,
            "raw_root_read_only_hash_authorized": True,
            "public_hash_backfill_performed": False,
            "lineage_full_check_performed": False,
            "formal_report_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "next_phase_started": False,
        },
        "raw_source_identity_summary": raw_summary,
        "raw_boundary": raw_boundary,
        "public_repo_safety": public_safety,
        "go_no_go": go_no_go,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete_and_raw_lineage_release_gates_pass",
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": (
            "Collect owner source identity decision or corrected registered source package before public member hash "
            "backfill, lineage completeness closure, official report release, GitHub main upload or app reinstall."
        ),
        "private_diagnostic_ref": str(PRIVATE_DIAGNOSTIC_PATH),
        "evidence_refs": [
            str(REPORT_PATH),
            str(GO_NO_GO_RECORD_PATH),
            str(TEST_RESULTS_PATH),
            str(RISK_REGISTER_PATH),
            str(ROLLBACK_PATH),
            str(MANIFEST_PATH),
            str(GO_NO_GO_PATH),
            str(METADATA_MANIFEST_PATH),
            str(METADATA_GO_NO_GO_PATH),
        ],
        "validation_summary": {
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "raw_alignment_remediation_validator": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "no_float_money_check": "PENDING_FINAL_VALIDATION",
            "no_omission_check": "PENDING_FINAL_VALIDATION",
            "raw_private_scan": "PENDING_FINAL_VALIDATION",
            "secret_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
    }
    private_diagnostic = _private_diagnostic(
        generated_at=generated,
        inventory=inventory,
        selector_status=selector_status,
        selected_candidate_count=selected_candidate_count,
        archive_private_details=archive_result["private_details"],
        raw_root_before=raw_root_before,
        raw_root_after=raw_root_after,
        selected_before=selected_before,
        selected_after=selected_after,
    )

    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_json(MANIFEST_PATH, manifest)
    _write_json(GO_NO_GO_PATH, go_no_go)
    _write_json(METADATA_MANIFEST_PATH, manifest)
    _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    _write_human_reports(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "PASS: generated KMFA v0.1.4 raw alignment remediation evidence "
        f"(decision={manifest['go_no_go']['decision']}, raw_alignment_complete="
        f"{str(manifest['raw_source_identity_summary']['raw_alignment_complete']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
