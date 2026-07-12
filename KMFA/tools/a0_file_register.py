#!/usr/bin/env python3
"""Build KMFA S05-P1 A0 file registration metadata.

The public repository may keep hashes, inventory metadata, quality status, and
candidate references. It must not keep raw PDF/Excel bytes or extracted business
values. When the private source zip is available, this tool can calculate member
SHA-256 values; otherwise it records the existing public inventory fingerprints
without pretending they are SHA-256 hashes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = (
    ROOT
    / "taskpack"
    / "v1_2"
    / "91_前序散件归档"
    / "kmfa_stage1_v4"
    / "KMFA_Uploaded_Data_Source_Inventory_v0_1.csv"
)
DEFAULT_SOURCE_MANIFEST = ROOT / "taskpack" / "v1_2" / "source_manifests" / "用户原始上传数据_SHA256_v1_2.csv"
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "baseline" / "a0_file_manifest.json"
DEFAULT_OUTPUT_CANDIDATES = ROOT / "metadata" / "baseline" / "a0_project_candidates.jsonl"

PACKAGE_NAME = "PRIVATE_RAW_SOURCE_005.zip"
PACKAGE_LABEL = "销售绩效考核"
EXPECTED_PDF_COUNT = 8
EXPECTED_EXCEL_COUNT = 1
HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
FORBIDDEN_KEYS = {
    "raw_value",
    "normalized_value",
    "plaintext_content",
    "full_file_text",
    "raw_file_bytes",
    "bank_account_number",
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
}


@dataclass(frozen=True)
class SourcePackage:
    name: str
    size_bytes: int
    sha256: str
    rule: str


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_source_package(path: Path, package_name: str = PACKAGE_NAME) -> SourcePackage:
    for row in read_csv(path):
        if (row.get("file") or "").strip() == package_name:
            return SourcePackage(
                name=package_name,
                size_bytes=int(row["bytes"]),
                sha256=row["sha256"].strip().lower(),
                rule=row["rule"].strip(),
            )
    raise ValueError(f"missing source package {package_name!r} in {path}")


def classify_file_type(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "pdf":
        return "pdf"
    if normalized.startswith("excel"):
        return "xlsx"
    raise ValueError(f"unsupported A0 source file type: {value!r}")


def candidate_label_from_path(member_path: str) -> str:
    name = Path(member_path).name
    stem = re.sub(r"\.[^.]+$", "", name)
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem or "unnamed-a0-candidate"


def stable_file_id(member_path: str) -> str:
    return f"A0-FILE-{sha256_text(member_path)[:12].upper()}"


def stable_candidate_id(member_path: str) -> str:
    return f"A0-CAND-{sha256_text('candidate:' + member_path)[:12].upper()}"


def inventory_rows(path: Path) -> list[dict[str, str]]:
    rows = [row for row in read_csv(path) if (row.get("数据包") or "").strip() == PACKAGE_LABEL]
    if not rows:
        raise ValueError(f"missing {PACKAGE_LABEL} inventory rows in {path}")
    return rows


def compute_zip_member_hashes(zip_path: Path, expected_package: SourcePackage) -> dict[str, dict[str, Any]]:
    actual_hash = sha256_file(zip_path)
    if actual_hash != expected_package.sha256:
        raise ValueError(
            f"source zip hash mismatch: expected {expected_package.sha256}, got {actual_hash}"
        )

    members: dict[str, dict[str, Any]] = {}
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            member_path = info.filename
            if Path(member_path).name.startswith(".") or "__MACOSX/" in member_path:
                continue
            digest = hashlib.sha256()
            size = 0
            with archive.open(info) as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
                    size += len(chunk)
            members[member_path] = {
                "member_sha256": f"sha256:{digest.hexdigest()}",
                "member_size_bytes": size,
            }
    return members


def build_a0_registration(
    *,
    inventory_csv: Path = DEFAULT_INVENTORY,
    source_manifest_csv: Path = DEFAULT_SOURCE_MANIFEST,
    source_zip: Path | None = None,
    generated_at: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_package = load_source_package(source_manifest_csv)
    rows = inventory_rows(inventory_csv)
    member_hashes = compute_zip_member_hashes(source_zip, source_package) if source_zip else {}
    generated_timestamp = generated_at or datetime.now(timezone.utc).isoformat()

    files: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        member_path = row["文件路径"].strip()
        file_format = classify_file_type(row["文件类型"])
        member_info = member_hashes.get(member_path)
        legacy_fingerprint = row["指纹/CRC"].strip()
        member_sha256 = member_info["member_sha256"] if member_info else None
        member_size_bytes = member_info["member_size_bytes"] if member_info else None
        file_id = stable_file_id(member_path)
        candidate_id = stable_candidate_id(member_path)
        candidate_label = candidate_label_from_path(member_path)

        files.append(
            {
                "record_type": "a0_source_file",
                "schema_version": "kmfa.a0_source_file.v1",
                "a0_file_id": file_id,
                "source_package_name": source_package.name,
                "source_package_hash": f"sha256:{source_package.sha256}",
                "public_inventory_path": member_path,
                "member_path_hash": f"sha256:{sha256_text(member_path)}",
                "file_format": file_format,
                "file_role": "a0_project_cost_workbook" if file_format == "xlsx" else "a0_supporting_pdf",
                "inventory_size_kb": row["大小KB"].strip(),
                "member_size_bytes": member_size_bytes,
                "member_sha256": member_sha256,
                "member_sha256_status": "recorded_from_private_zip" if member_sha256 else "pending_private_zip_unavailable",
                "legacy_inventory_fingerprint": legacy_fingerprint,
                "legacy_fingerprint_kind": "source_inventory_crc_or_fingerprint",
                "raw_file_committed": False,
                "raw_content_committed": False,
                "field_extraction_allowed_in_s05p1": False,
                "evidence_ref": "KMFA/taskpack/v1_2/91_前序散件归档/kmfa_stage1_v4/KMFA_Uploaded_Data_Source_Inventory_v0_1.csv",
            }
        )
        candidates.append(
            {
                "record_type": "a0_project_candidate",
                "schema_version": "kmfa.a0_project_candidate.v1",
                "candidate_id": candidate_id,
                "a0_file_id": file_id,
                "candidate_label": candidate_label,
                "candidate_label_source": "public_inventory_path_stem",
                "candidate_label_hash": f"sha256:{sha256_text(candidate_label)}",
                "candidate_order": index,
                "machine_candidate_quality_grade": "Q3",
                "q3_status": "machine_candidate_from_public_inventory",
                "q4_human_lock_status": "not_locked_pending_human_confirmation",
                "q4_human_locked": False,
                "q5_formal_report_allowed": False,
                "raw_business_values_committed": False,
                "next_required_phase": "S05-P2 field-level golden baseline",
            }
        )

    manifest = {
        "record_type": "a0_file_registration_manifest",
        "schema_version": "kmfa.a0_file_registration.v1",
        "project_id": "KMFA",
        "stage_phase": "S05-P1",
        "generated_at": generated_timestamp,
        "source_package": {
            "package_name": source_package.name,
            "package_size_bytes": source_package.size_bytes,
            "package_hash": f"sha256:{source_package.sha256}",
            "package_rule": source_package.rule,
            "raw_package_committed": False,
            "public_repo_raw_allowed": False,
        },
        "file_summary": {
            "total_files": len(files),
            "pdf_files": sum(1 for item in files if item["file_format"] == "pdf"),
            "excel_files": sum(1 for item in files if item["file_format"] == "xlsx"),
            "member_sha256_recorded_count": sum(1 for item in files if item["member_sha256"]),
            "member_sha256_pending_count": sum(1 for item in files if not item["member_sha256"]),
            "legacy_fingerprint_recorded_count": sum(1 for item in files if item["legacy_inventory_fingerprint"]),
        },
        "quality_policy": {
            "q3_meaning": "machine candidate structured from public-safe inventory only",
            "q4_requires": "human confirmation of field-level golden values in S05-P2/S05-P3",
            "q5_requires": "zero-delta validation and complete lineage in later stages",
            "formal_report_allowed": False,
        },
        "public_repo_safety": {
            "raw_file_bytes_committed": False,
            "raw_business_values_committed": False,
            "member_sha256_may_be_pending_without_private_zip": True,
        },
        "files": files,
    }
    validate_a0_registration(manifest, candidates)
    return manifest, candidates


def walk_json(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                raise ValueError(f"forbidden key {key!r} at {path}")
            walk_json(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_json(child, f"{path}[{index}]")


def validate_a0_registration(
    manifest: dict[str, Any],
    candidates: list[dict[str, Any]],
    *,
    require_member_sha256: bool = False,
) -> None:
    walk_json(manifest)
    walk_json(candidates)

    if manifest.get("schema_version") != "kmfa.a0_file_registration.v1":
        raise ValueError("invalid A0 manifest schema_version")
    source_package = manifest.get("source_package") or {}
    if not HASH_RE.match(str(source_package.get("package_hash", ""))):
        raise ValueError("source package hash must be sha256:<64 hex>")
    if source_package.get("raw_package_committed") is not False:
        raise ValueError("raw package must not be committed")

    files = manifest.get("files")
    if not isinstance(files, list):
        raise ValueError("manifest files must be a list")
    pdf_count = sum(1 for item in files if item.get("file_format") == "pdf")
    excel_count = sum(1 for item in files if item.get("file_format") == "xlsx")
    if len(files) != EXPECTED_PDF_COUNT + EXPECTED_EXCEL_COUNT:
        raise ValueError("A0 registration must contain exactly 9 files")
    if pdf_count != EXPECTED_PDF_COUNT or excel_count != EXPECTED_EXCEL_COUNT:
        raise ValueError("A0 registration must contain exactly 8 PDF files and 1 Excel file")

    for item in files:
        if item.get("raw_file_committed") is not False or item.get("raw_content_committed") is not False:
            raise ValueError("A0 file records must not commit raw files or content")
        member_sha256 = item.get("member_sha256")
        if member_sha256 and not HASH_RE.match(str(member_sha256)):
            raise ValueError(f"invalid member_sha256 for {item.get('a0_file_id')}")
        if require_member_sha256 and not member_sha256:
            raise ValueError(f"missing member_sha256 for {item.get('a0_file_id')}")
        if not member_sha256 and item.get("member_sha256_status") != "pending_private_zip_unavailable":
            raise ValueError(f"missing member hash must be explicitly pending for {item.get('a0_file_id')}")
        if not item.get("legacy_inventory_fingerprint"):
            raise ValueError(f"missing legacy inventory fingerprint for {item.get('a0_file_id')}")

    if len(candidates) != len(files):
        raise ValueError("candidate list must align 1:1 with A0 files in S05-P1")
    file_ids = {item["a0_file_id"] for item in files}
    for candidate in candidates:
        if candidate.get("a0_file_id") not in file_ids:
            raise ValueError(f"candidate references unknown file: {candidate.get('candidate_id')}")
        if candidate.get("machine_candidate_quality_grade") != "Q3":
            raise ValueError("S05-P1 candidates must be marked Q3 machine candidates")
        if candidate.get("q4_human_locked") is not False:
            raise ValueError("S05-P1 must not mark Q4 human lock as complete")
        if candidate.get("q5_formal_report_allowed") is not False:
            raise ValueError("S05-P1 candidates must not allow formal reports")
        if candidate.get("raw_business_values_committed") is not False:
            raise ValueError("candidate records must not contain raw business values")


def write_outputs(manifest: dict[str, Any], candidates: list[dict[str, Any]], output_manifest: Path, output_candidates: Path) -> None:
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_candidates.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    candidate_lines = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in candidates]
    output_candidates.write_text("\n".join(candidate_lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S05-P1 A0 file registration metadata.")
    parser.add_argument("--inventory-csv", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--source-manifest-csv", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--source-zip", type=Path)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-candidates", type=Path, default=DEFAULT_OUTPUT_CANDIDATES)
    parser.add_argument("--generated-at")
    parser.add_argument("--require-member-sha256", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    manifest, candidates = build_a0_registration(
        inventory_csv=args.inventory_csv,
        source_manifest_csv=args.source_manifest_csv,
        source_zip=args.source_zip,
        generated_at=args.generated_at,
    )
    validate_a0_registration(manifest, candidates, require_member_sha256=args.require_member_sha256)
    if not args.check_only:
        write_outputs(manifest, candidates, args.output_manifest, args.output_candidates)
    print(
        "PASS: A0 registration built "
        f"(files={len(manifest['files'])}, pdf={manifest['file_summary']['pdf_files']}, "
        f"excel={manifest['file_summary']['excel_files']}, "
        f"member_sha256_recorded={manifest['file_summary']['member_sha256_recorded_count']}, "
        f"member_sha256_pending={manifest['file_summary']['member_sha256_pending_count']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
