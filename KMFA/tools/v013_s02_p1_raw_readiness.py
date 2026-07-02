#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S02-P1 raw data readiness evidence.

This tool is intentionally read-only against the user-owned raw metadata
directory. Private inventory output stays under KMFA/.codex_private_runtime/
and must never be committed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


RAW_DIR = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v013_s02_p1_raw_inventory")
PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S02_P1_RAW_READINESS")
PRIVATE_INVENTORY_PATH = PRIVATE_OUTPUT_DIR / "private_inventory.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "local_diagnostic_report.md"
PUBLIC_MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/raw_readiness_manifest.json"
PUBLIC_REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/raw_readiness_report.md"

SCHEMA_VERSION = "kmfa.v013_s02_p1_raw_readiness.v1"
TASK_ID = "KMFA-V013-S02-P1-RAW-READINESS-20260702"
PHASE_SCOPE = "raw_data_read_only_inventory_readiness"
NEXT_REQUIRED_STEP = (
    "S02-P2 raw mapping/value matching readiness; no GitHub upload until overall completion upload gate."
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_raw_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists() or not raw_dir.is_dir():
        return []
    return sorted(path for path in raw_dir.rglob("*") if path.is_file())


def git_check_ignored(path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


def build_private_inventory(raw_dir: Path) -> dict[str, Any]:
    files = iter_raw_files(raw_dir)
    records: list[dict[str, Any]] = []
    for path in files:
        stat = path.stat()
        records.append(
            {
                "relative_path": path.relative_to(raw_dir).as_posix(),
                "suffix": path.suffix.lower() or "<none>",
                "size_bytes": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": sha256_file(path),
            }
        )

    extension_counts = Counter(record["suffix"] for record in records)
    return {
        "schema_version": "kmfa.v013_s02_p1_private_inventory.v1",
        "task_id": TASK_ID,
        "raw_dir": str(raw_dir),
        "raw_dir_exists": raw_dir.exists(),
        "raw_dir_readable": raw_dir.exists() and raw_dir.is_dir(),
        "raw_dir_mutation_performed": False,
        "file_count": len(records),
        "total_bytes": sum(record["size_bytes"] for record in records),
        "extension_counts": dict(sorted(extension_counts.items())),
        "records": records,
        "public_commit_allowed": False,
    }


def build_public_manifest(
    raw_dir: Path,
    private_inventory: dict[str, Any],
    private_inventory_path: Path,
    private_report_path: Path,
) -> dict[str, Any]:
    private_outputs_ignored = git_check_ignored(private_inventory_path) and git_check_ignored(private_report_path)
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S02",
        "phase_id": "S02-P1",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "raw_dir": str(raw_dir),
        "raw_dir_exists": private_inventory["raw_dir_exists"],
        "raw_dir_readable": private_inventory["raw_dir_readable"],
        "raw_dir_mutation_allowed": False,
        "raw_dir_mutation_performed": False,
        "raw_dir_delete_allowed": False,
        "raw_dir_move_allowed": False,
        "raw_dir_github_commit_allowed": False,
        "file_count": private_inventory["file_count"],
        "total_bytes": private_inventory["total_bytes"],
        "extension_counts": private_inventory["extension_counts"],
        "private_inventory_ref": private_inventory_path.as_posix(),
        "private_diagnostic_report_ref": private_report_path.as_posix(),
        "private_inventory_written": private_inventory_path.exists(),
        "private_diagnostic_report_written": private_report_path.exists(),
        "private_outputs_git_ignored": private_outputs_ignored,
        "public_manifest_contains_raw_file_records": False,
        "public_manifest_contains_raw_filenames": False,
        "public_manifest_contains_raw_values": False,
        "public_report_contains_raw_filenames": False,
        "public_report_contains_raw_values": False,
        "raw_value_matching_performed": False,
        "raw_value_matching_blocked_reason": (
            "S02-P1 is inventory/readiness only; value-level matching requires a later authorized parser "
            "and mapping phase."
        ),
        "github_upload_performed": False,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_execution_allowed": False,
        "public_repo_safety": {
            "raw_business_data_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "field_plaintext_committed": False,
            "raw_file_names_committed": False,
            "raw_file_hashes_committed": False,
            "raw_business_values_committed": False,
        },
        "evidence_refs": [
            PUBLIC_MANIFEST_PATH.as_posix(),
            PUBLIC_REPORT_PATH.as_posix(),
            private_inventory_path.as_posix(),
            private_report_path.as_posix(),
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_private_report(path: Path, private_inventory: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    extension_counts = json.dumps(private_inventory["extension_counts"], ensure_ascii=False, sort_keys=True)
    lines = [
        "# KMFA v0.1.3 S02-P1 Local Private Raw Inventory Diagnostic",
        "",
        "This file is local-only and git-ignored. It may contain user raw file names and hashes.",
        "",
        f"- task_id: `{TASK_ID}`",
        f"- raw_dir: `{private_inventory['raw_dir']}`",
        f"- raw_dir_exists: `{str(private_inventory['raw_dir_exists']).lower()}`",
        f"- raw_dir_readable: `{str(private_inventory['raw_dir_readable']).lower()}`",
        f"- raw_dir_mutation_performed: `{str(private_inventory['raw_dir_mutation_performed']).lower()}`",
        f"- file_count: `{private_inventory['file_count']}`",
        f"- total_bytes: `{private_inventory['total_bytes']}`",
        f"- extension_counts: `{extension_counts}`",
        "",
        "## Diagnostic Scope",
        "",
        "- Read-only metadata inventory and file hashing only.",
        "- No workbook/PDF/ZIP content extraction.",
        "- No raw field value, worksheet value, business amount, contract text, payroll, tax filing, or bank statement parsing.",
        "- Value-level matching is intentionally deferred to a later authorized parser/mapping phase.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_public_report(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    extension_counts = json.dumps(manifest["extension_counts"], ensure_ascii=False, sort_keys=True)
    lines = [
        "# KMFA v0.1.3 S02-P1 Raw Readiness Report",
        "",
        "## Public-Safe Summary",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- stage_phase: `{manifest['stage_id']}-{manifest['phase_id']}`",
        f"- raw_dir: `{manifest['raw_dir']}`",
        f"- raw_dir_exists: `{str(manifest['raw_dir_exists']).lower()}`",
        f"- raw_dir_readable: `{str(manifest['raw_dir_readable']).lower()}`",
        f"- file_count: `{manifest['file_count']}`",
        f"- total_bytes: `{manifest['total_bytes']}`",
        f"- extension_counts: `{extension_counts}`",
        f"- raw_dir_mutation_performed: `{str(manifest['raw_dir_mutation_performed']).lower()}`",
        f"- raw_value_matching_performed: `{str(manifest['raw_value_matching_performed']).lower()}`",
        f"- github_upload_performed: `{str(manifest['github_upload_performed']).lower()}`",
        f"- delivery_allowed: `{str(manifest['delivery_allowed']).lower()}`",
        "",
        "## Public Repository Boundary",
        "",
        "- This public evidence intentionally omits raw file names, raw file hashes, worksheet names, field headers, row values, amounts, contracts, payroll, tax filings, and bank statement content.",
        "- Full local inventory stays in the git-ignored private runtime directory.",
        "- No raw ZIP, Excel, PDF, private CSV, SQLite/database, credentials, or business source files are committed.",
        "",
        "## Local Private Evidence",
        "",
        f"- private_inventory_ref: `{manifest['private_inventory_ref']}`",
        f"- private_diagnostic_report_ref: `{manifest['private_diagnostic_report_ref']}`",
        f"- private_outputs_git_ignored: `{str(manifest['private_outputs_git_ignored']).lower()}`",
        "",
        "## Not Performed In This Phase",
        "",
        "- No raw value reconciliation or report matching was performed in S02-P1.",
        "- No Stage 2 review, GitHub upload, formal report release, lineage full check, live connector, or business execution was performed.",
        "",
        f"Next required step: {manifest['next_required_step']}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_raw_readiness_evidence(
    raw_dir: Path = RAW_DIR,
    private_output_dir: Path = PRIVATE_OUTPUT_DIR,
    public_output_dir: Path = PUBLIC_OUTPUT_DIR,
) -> dict[str, Any]:
    private_inventory_path = private_output_dir / PRIVATE_INVENTORY_PATH.name
    private_report_path = private_output_dir / PRIVATE_REPORT_PATH.name
    public_manifest_path = public_output_dir / "machine" / PUBLIC_MANIFEST_PATH.name
    public_report_path = public_output_dir / "human" / PUBLIC_REPORT_PATH.name

    private_inventory = build_private_inventory(raw_dir)
    write_json(private_inventory_path, private_inventory)
    write_private_report(private_report_path, private_inventory)

    public_manifest = build_public_manifest(raw_dir, private_inventory, private_inventory_path, private_report_path)
    write_json(public_manifest_path, public_manifest)
    write_public_report(public_report_path, public_manifest)
    return public_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA v0.1.3 S02-P1 raw readiness evidence.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--private-output-dir", type=Path, default=PRIVATE_OUTPUT_DIR)
    parser.add_argument("--public-output-dir", type=Path, default=PUBLIC_OUTPUT_DIR)
    args = parser.parse_args()
    manifest = generate_raw_readiness_evidence(args.raw_dir, args.private_output_dir, args.public_output_dir)
    print(
        "PASS: KMFA v0.1.3 S02-P1 raw readiness evidence generated "
        f"(files={manifest['file_count']}, raw_dir_readable={str(manifest['raw_dir_readable']).lower()}, "
        f"private_ignored={str(manifest['private_outputs_git_ignored']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
