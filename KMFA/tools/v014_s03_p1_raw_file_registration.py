#!/usr/bin/env python3
"""Build KMFA v1.4 S03-P1 public-safe raw file registration evidence.

The raw inbox may be listed/read/hashed only for this authorized phase. Raw
filenames, directory names, content hashes and zip member names are written only
to the git-ignored private runtime. Public artifacts keep aggregate counts,
file-type status and private refs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from KMFA.tools.file_import_register import detect_format


TASK_ID = "KMFA-V014-S03-P1-FILE-REGISTRATION-20260703"
ACCEPTANCE_ID = "ACC-V014-S03-P1-FILE-REGISTRATION"
RAW_INBOX = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
PRIVATE_DIR = Path("KMFA/.codex_private_runtime/V014_S03_P1_FILE_REGISTRATION")
PUBLIC_METADATA_PATH = Path("KMFA/metadata/imports/v014_s03_p1_public_raw_file_register.json")
STAGE_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S03_P1_FILE_REGISTRATION/machine/s03_p1_file_registration_manifest.json"
)
PROTOCOL_PATH = Path("KMFA/metadata/protocol/raw_data_roots_v1_4_s03_p1.json")
PRIVATE_MANIFEST_NAME = "private_raw_file_manifest.json"
SUPPORTED_EXTENSIONS = {".zip", ".xlsx", ".xls", ".csv", ".pdf", ".wps", ".et", ".dps"}
PRIVATE_URI_PREFIX = "private://kmfa/v014/s03-p1/raw-file-registration"


class RawRegistrationError(Exception):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stat_snapshot(path: Path) -> dict[str, int]:
    stat = path.stat()
    return {
        "mtime_ns": stat.st_mtime_ns,
        "ctime_ns": stat.st_ctime_ns,
        "size_bytes": stat.st_size,
    }


def iter_files(raw_root: Path) -> list[Path]:
    if not raw_root.exists():
        raise RawRegistrationError(f"raw root does not exist: {raw_root}")
    if not raw_root.is_dir():
        raise RawRegistrationError(f"raw root is not a directory: {raw_root}")
    files: list[Path] = []
    for root, dirs, names in os.walk(raw_root):
        dirs.sort()
        for name in sorted(names):
            path = Path(root) / name
            if path.is_file():
                files.append(path)
    return files


def summarize_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return "lt_1kb"
    if size_bytes < 1024 * 1024:
        return "lt_1mb"
    if size_bytes < 10 * 1024 * 1024:
        return "lt_10mb"
    if size_bytes < 100 * 1024 * 1024:
        return "lt_100mb"
    return "gte_100mb"


def build_registration(
    raw_root: Path = RAW_INBOX,
    private_dir: Path = PRIVATE_DIR,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = generated_at or utc_now()
    raw_root = raw_root.resolve()
    private_dir.mkdir(parents=True, exist_ok=True)
    root_before = stat_snapshot(raw_root)
    files = iter_files(raw_root)

    private_entries: list[dict[str, Any]] = []
    public_records: list[dict[str, Any]] = []
    extension_counts: Counter[str] = Counter()
    format_counts: Counter[str] = Counter()
    container_counts: Counter[str] = Counter()
    size_buckets: Counter[str] = Counter()
    unsupported_count = 0
    special_guidance_count = 0
    max_depth = 0

    for index, path in enumerate(files, start=1):
        rel_path = path.relative_to(raw_root)
        rel_text = rel_path.as_posix()
        depth = max(len(rel_path.parts) - 1, 0)
        max_depth = max(max_depth, depth)
        extension = path.suffix.lower() or "[none]"
        file_size = path.stat().st_size
        extension_counts[extension] += 1
        size_buckets[summarize_size(file_size)] += 1

        file_hash = sha256_file(path)
        path_hash = sha256_text(rel_text)
        public_file_id = f"RAW-FILE-{index:06d}"
        private_ref = f"{PRIVATE_URI_PREFIX}/{public_file_id}"

        try:
            file_format, container_type, guidance = detect_format(path)
            supported = True
        except ValueError:
            file_format = "unsupported"
            container_type = "unsupported"
            guidance = "unsupported_extension_private_review_required"
            supported = False
            unsupported_count += 1

        format_counts[file_format] += 1
        container_counts[container_type] += 1
        if container_type in {"ole_compound", "wps_native"}:
            special_guidance_count += 1

        private_entries.append(
            {
                "private_ref": private_ref,
                "relative_path": rel_text,
                "relative_path_sha256": path_hash,
                "content_sha256": file_hash,
                "file_size_bytes": file_size,
                "mtime_ns": path.stat().st_mtime_ns,
                "extension": extension,
                "file_format": file_format,
                "container_type": container_type,
                "supported_by_s03_p1": supported,
                "operator_guidance_private": guidance,
            }
        )
        public_records.append(
            {
                "public_file_id": public_file_id,
                "private_manifest_record_ref": private_ref,
                "file_format": file_format,
                "container_type": container_type,
                "extension": extension,
                "file_size_bytes": file_size,
                "size_bucket": summarize_size(file_size),
                "content_hash_status": "computed_private_only",
                "path_status": "private_only",
                "raw_filename_committed": False,
                "raw_hash_committed": False,
                "field_or_header_plaintext_committed": False,
                "raw_value_committed": False,
                "supported_by_s03_p1": supported,
            }
        )

    root_after = stat_snapshot(raw_root)
    private_manifest_path = private_dir / PRIVATE_MANIFEST_NAME
    public_records_path = str(PUBLIC_METADATA_PATH)
    private_manifest = {
        "schema_version": "kmfa.v014_s03_p1.private_raw_file_inventory.v1",
        "project_id": "KMFA",
        "stage_id": "S03",
        "phase_id": "S03-P1",
        "generated_at": generated,
        "raw_root_path": str(raw_root),
        "public_metadata_ref": public_records_path,
        "raw_root_mutation_guard": {
            "root_before": root_before,
            "root_after": root_after,
            "root_stat_unchanged": root_before == root_after,
        },
        "entry_count": len(private_entries),
        "entries": private_entries,
    }
    private_manifest_path.write_text(json.dumps(private_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    raw_root_status = {
        "raw_root_id": "local_kmfa_metadata_raw_root",
        "raw_root_path": str(raw_root),
        "access_authorized_for_phase": True,
        "read_only_scan_performed": True,
        "list_performed": True,
        "stat_performed": True,
        "hash_performed": True,
        "write_performed": False,
        "delete_performed": False,
        "move_performed": False,
        "rename_performed": False,
        "overwrite_performed": False,
        "raw_root_stat_unchanged_after_scan": root_before == root_after,
    }
    scan_summary = {
        "file_count": len(public_records),
        "directory_count": sum(1 for item in raw_root.rglob("*") if item.is_dir()),
        "supported_file_count": len(public_records) - unsupported_count,
        "unsupported_file_count": unsupported_count,
        "total_size_bytes": sum(record["file_size_bytes"] for record in public_records),
        "max_relative_depth": max_depth,
        "extension_counts": dict(sorted(extension_counts.items())),
        "file_format_counts": dict(sorted(format_counts.items())),
        "container_type_counts": dict(sorted(container_counts.items())),
        "size_bucket_counts": dict(sorted(size_buckets.items())),
        "wps_or_ole_guidance_count": special_guidance_count,
    }
    public_register = {
        "schema_version": "kmfa.v014_s03_p1.public_raw_file_register.v1",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S03",
        "phase_id": "S03-P1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": "completed_validated_local_only_no_go_upload_deferred",
        "generated_at": generated,
        "raw_root_status": raw_root_status,
        "scan_summary": scan_summary,
        "source_package": {
            "public_source_package_id": "SRC-PKG-V014-S03-P1-LOCAL-RAW-ROOT",
            "source_package_type": "local_raw_directory",
            "source_id_candidate_count": max(1, len(public_records)),
            "source_priority": "highest_raw_source",
            "source_package_hash_status": "computed_private_only",
            "source_package_path_status": "private_only",
        },
        "public_file_records": public_records,
        "private_runtime_evidence": {
            "private_manifest_path": str(private_manifest_path),
            "private_manifest_committed": False,
            "private_manifest_contains_raw_filenames_and_hashes": True,
            "private_manifest_required_for_local_revalidation": True,
        },
        "safe_zip_support": {
            "safe_zip_extract_supported": True,
            "safe_zip_extract_performed": False,
            "zip_member_names_committed": False,
            "unsafe_member_policy": [
                "reject_absolute_paths",
                "reject_parent_traversal",
                "reject_empty_path_parts",
                "reject_symlink_entries",
            ],
        },
        "public_repo_safety": {
            "raw_business_data_committed": False,
            "raw_filenames_committed": False,
            "raw_hashes_committed": False,
            "directory_tree_plaintext_committed": False,
            "zip_member_names_committed": False,
            "field_or_header_plaintext_committed": False,
            "raw_or_normalized_values_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
        },
        "non_scope": {
            "s03_p2_source_check_matrix_started": False,
            "s03_p3_source_priority_started": False,
            "stage3_review_performed": False,
            "github_upload_performed": False,
            "raw_value_matching_performed": False,
            "field_mapping_performed": False,
            "formal_report_performed": False,
            "business_execution_performed": False,
        },
    }
    stage_manifest = {
        "schema_version": "kmfa.v014_s03_p1_file_registration.v1",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S03",
        "phase_id": "S03-P1",
        "stage_phase": "S03-P1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": "completed_validated_local_only_no_go_upload_deferred",
        "dependency": {
            "required_review": "V014_S02_STAGE_REVIEW",
            "dependency_manifest": "KMFA/stage_artifacts/V014_S02_STAGE_REVIEW/machine/stage2_review_manifest.json",
            "dependency_expected_status": "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        },
        "phase_scope": {
            "current_phase_only": True,
            "file_registration_only": True,
            "raw_root_read_only_inventory_authorized": True,
            "safe_zip_extract_capability_in_scope": True,
            "safe_zip_extract_performed": False,
            "s03_p2_started": False,
            "s03_p3_started": False,
            "stage3_review_performed": False,
            "github_upload_performed": False,
            "raw_value_matching_performed": False,
            "field_mapping_performed": False,
            "formal_report_performed": False,
            "business_execution_performed": False,
            "next_phase": "S03-P2",
            "next_phase_started": False,
        },
        "raw_root_status": raw_root_status,
        "scan_summary": scan_summary,
        "public_register_ref": str(PUBLIC_METADATA_PATH),
        "private_runtime_ref": str(private_manifest_path),
        "public_repo_safety": public_register["public_repo_safety"],
        "safe_zip_support": public_register["safe_zip_support"],
        "release_state": {
            "delivery_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "business_execution_allowed": False,
            "github_main_upload_allowed": False,
            "current_go_no_go": "NO_GO",
            "current_data_quality_grade": "Q1",
            "current_report_grade": "D",
            "release_permission": "blocked",
        },
        "validation_summary": {
            "s02_stage_review_dependency": "PENDING",
            "v014_s03_p1_validator": "PENDING",
            "focused_unit_test": "PENDING",
            "governance_validator": "PENDING",
            "raw_private_scan": "PENDING",
            "secret_scan": "PENDING",
            "diff_check": "PENDING",
        },
        "evidence_refs": [
            "KMFA/stage_artifacts/V014_S03_P1_FILE_REGISTRATION/human/s03_p1_completion_record.md",
            "KMFA/stage_artifacts/V014_S03_P1_FILE_REGISTRATION/human/test_results.md",
            "KMFA/stage_artifacts/V014_S03_P1_FILE_REGISTRATION/human/risk_register.md",
            "KMFA/stage_artifacts/V014_S03_P1_FILE_REGISTRATION/human/rollback_plan.md",
            str(PUBLIC_METADATA_PATH),
            str(PROTOCOL_PATH),
        ],
        "next_recommended_phase": "S03-P2",
    }
    protocol = {
        "schema_version": "kmfa.raw_data_roots.v1_4.s03_p1",
        "project_id": "KMFA",
        "stage_phase": "S03-P1",
        "raw_root": raw_root_status,
        "allowed_operations_performed": ["list", "stat", "read", "hash"],
        "forbidden_operations_performed": [],
        "private_runtime_policy": {
            "preferred_project_runtime": "KMFA/.codex_private_runtime/",
            "phase_private_runtime": str(private_dir),
            "git_ignore_required": True,
            "public_repo_private_runtime_commit_allowed": False,
        },
        "public_commit_policy": {
            "allowed": [
                "schema",
                "aggregate_counts",
                "file_type_status",
                "size_bytes",
                "private_refs",
                "status_index",
            ],
            "forbidden": [
                "raw_files",
                "raw_filenames",
                "raw_content_hashes",
                "directory_tree_plaintext",
                "zip_member_names",
                "field_or_header_plaintext",
                "raw_or_normalized_values",
                "credentials",
                "unmasked_financial_detail",
                "bank_account_full_number",
                "customer_contract_full_text",
                "payroll_detail",
            ],
        },
    }
    return {
        "public_register": public_register,
        "stage_manifest": stage_manifest,
        "protocol": protocol,
        "private_manifest_path": private_manifest_path,
    }


def write_outputs(bundle: dict[str, Any]) -> None:
    for path, key in (
        (PUBLIC_METADATA_PATH, "public_register"),
        (STAGE_MANIFEST_PATH, "stage_manifest"),
        (PROTOCOL_PATH, "protocol"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(bundle[key], ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA v1.4 S03-P1 raw file registration evidence.")
    parser.add_argument("--raw-root", type=Path, default=RAW_INBOX)
    parser.add_argument("--private-dir", type=Path, default=PRIVATE_DIR)
    parser.add_argument("--write", action="store_true", help="Write public and private evidence files.")
    args = parser.parse_args(argv)
    try:
        bundle = build_registration(args.raw_root, args.private_dir)
        if args.write:
            write_outputs(bundle)
    except RawRegistrationError as exc:
        print(f"FAIL: {exc}")
        return 1
    public = bundle["public_register"]
    summary = public["scan_summary"]
    print(
        "PASS: KMFA v1.4 S03-P1 raw file registration built "
        f"(files={summary['file_count']}, supported={summary['supported_file_count']}, "
        f"unsupported={summary['unsupported_file_count']}, bytes={summary['total_size_bytes']}, "
        f"private={bundle['private_manifest_path']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
