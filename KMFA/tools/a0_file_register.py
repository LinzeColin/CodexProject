#!/usr/bin/env python3
"""Build the public-safe A0 source registration projection.

The v2 public projection deliberately contains no source package name, source
package/member digest, source member path, filename-derived identifier, size,
CRC, or candidate label.  When a private source ZIP is supplied, the binding
evidence is written only to an explicitly supplied private receipt path; it is
never copied into the returned public objects.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
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
DEFAULT_PRIVATE_RECEIPT = (
    ROOT / ".codex_private_runtime" / "a0_public_projection_v2" / "a0_source_private_binding_receipt.json"
)

PACKAGE_NAME = "PRIVATE_RAW_SOURCE_005.zip"
PACKAGE_LABEL = "销售绩效考核"
EXPECTED_PDF_COUNT = 8
EXPECTED_EXCEL_COUNT = 1
PUBLIC_SCHEMA = "kmfa.a0_file_registration.public_projection.v2"
PUBLIC_FILE_SCHEMA = "kmfa.a0_source_file.public_projection.v2"
PUBLIC_CANDIDATE_SCHEMA = "kmfa.a0_project_candidate.public_projection.v2"
PRIVATE_RECEIPT_SCHEMA = "kmfa.private.a0_source_binding_receipt.v2"
SOURCE_PACKAGE_REF = "A0-SOURCE-PACKAGE-PUB-V2"
OPAQUE_FILE_RE = re.compile(r"^A0-FILE-PUB-V2-\d{3}$")
OPAQUE_SOURCE_RE = re.compile(r"^A0-SOURCE-FILE-PUB-V2-\d{3}$")
OPAQUE_CANDIDATE_RE = re.compile(r"^A0-CAND-PUB-V2-\d{3}$")
HEX_DIGEST_RE = re.compile(r"(?i)(?:sha(?:-?256)?[:=])?[a-f0-9]{64}")
FORBIDDEN_PUBLIC_KEYS = {
    "candidate_label",
    "candidate_label_hash",
    "legacy_inventory_fingerprint",
    "member_path",
    "member_path_hash",
    "member_sha256",
    "member_size_bytes",
    "package_hash",
    "package_name",
    "package_size_bytes",
    "plaintext_content",
    "public_inventory_path",
    "raw_file_bytes",
    "raw_value",
    "normalized_value",
    "source_package_hash",
    "source_package_name",
}


@dataclass(frozen=True)
class SourcePackage:
    name: str
    size_bytes: int
    sha256: str
    rule: str


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _private_receipt_destination(path: Path) -> Path:
    """Return a no-follow private destination and reject tracked workspace paths."""

    candidate = Path(os.path.abspath(path))
    if candidate.exists() and (candidate.is_symlink() or not candidate.is_file()):
        raise ValueError("private receipt destination must be a regular file or a new path")
    if candidate.parent.exists() and candidate.parent.is_symlink():
        raise ValueError("private receipt parent must not be a symlink")

    if _is_relative_to(candidate, REPO_ROOT):
        allowed_bases = (ROOT / ".codex_private_runtime", ROOT / "local_runtime")
        base = next((item for item in allowed_bases if _is_relative_to(candidate, item)), None)
        if base is None:
            raise ValueError("private receipt inside the repository must stay in an approved private runtime")
        current = candidate.parent
        while _is_relative_to(current, base):
            if current.exists() and (current.is_symlink() or not current.is_dir()):
                raise ValueError("private receipt directory chain must contain only real directories")
            if current == base:
                break
            current = current.parent
        candidate.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not _is_relative_to(candidate.parent.resolve(strict=True), base.resolve(strict=True)):
            raise ValueError("private receipt destination escaped the approved private runtime")
        ignored = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", "--", str(candidate)],
            cwd=REPO_ROOT,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if ignored.returncode != 0:
            raise ValueError("private receipt destination is not git-ignored")
    else:
        candidate.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    os.chmod(candidate.parent, 0o700)
    return candidate


def write_private_json_receipt(path: Path, payload: dict[str, Any]) -> None:
    destination = _private_receipt_destination(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(destination, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    mode = stat.S_IMODE(os.lstat(destination).st_mode)
    if mode != 0o600:
        os.chmod(destination, 0o600)


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
    raise ValueError(f"missing configured A0 source package in {path}")


def classify_file_type(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "pdf":
        return "pdf"
    if normalized.startswith("excel"):
        return "xlsx"
    raise ValueError(f"unsupported A0 source file type: {value!r}")


def inventory_rows(path: Path) -> list[dict[str, str]]:
    rows = [row for row in read_csv(path) if (row.get("数据包") or "").strip() == PACKAGE_LABEL]
    if not rows:
        raise ValueError(f"missing configured A0 inventory rows in {path}")
    return rows


def _private_member_bindings(zip_path: Path, expected: SourcePackage) -> list[dict[str, Any]]:
    actual_hash = sha256_file(zip_path)
    actual_size = zip_path.stat().st_size
    if actual_hash != expected.sha256 or actual_size != expected.size_bytes:
        raise ValueError("private source ZIP does not match the configured private source manifest")

    bindings: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir() or Path(info.filename).name.startswith(".") or "__MACOSX/" in info.filename:
                continue
            digest = hashlib.sha256()
            with archive.open(info) as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            bindings.append(
                {
                    "member_path": info.filename,
                    "member_size_bytes": info.file_size,
                    "member_sha256": digest.hexdigest(),
                }
            )
    return bindings


def _write_private_receipt(
    path: Path,
    *,
    source_package: SourcePackage,
    source_zip: Path,
    rows: list[dict[str, str]],
    generated_at: str,
) -> None:
    bindings = _private_member_bindings(source_zip, source_package)
    by_path = {item["member_path"]: item for item in bindings}
    expected_paths = [row["文件路径"].strip() for row in rows]
    if set(by_path) != set(expected_paths):
        raise ValueError("private source ZIP members do not match the configured private inventory")
    ordered = []
    for index, member_path in enumerate(expected_paths, start=1):
        ordered.append(
            {
                "a0_file_id": f"A0-FILE-PUB-V2-{index:03d}",
                "source_file_ref": f"A0-SOURCE-FILE-PUB-V2-{index:03d}",
                **by_path[member_path],
            }
        )
    payload = {
        "record_type": "a0_source_private_binding_receipt",
        "schema_version": PRIVATE_RECEIPT_SCHEMA,
        "classification": "private_sensitive_do_not_commit",
        "generated_at": generated_at,
        "source_package_ref": SOURCE_PACKAGE_REF,
        "source_package_name": source_package.name,
        "source_package_size_bytes": source_package.size_bytes,
        "source_package_sha256": source_package.sha256,
        "source_zip_path": str(source_zip.resolve()),
        "member_bindings": ordered,
    }
    write_private_json_receipt(path, payload)


def _walk_public(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise ValueError(f"forbidden public A0 key {key!r} at {path}")
            _walk_public(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_public(child, f"{path}[{index}]")
    elif isinstance(value, str) and HEX_DIGEST_RE.search(value):
        raise ValueError(f"digest-like value is forbidden in public A0 projection at {path}")


def build_a0_registration(
    *,
    inventory_csv: Path = DEFAULT_INVENTORY,
    source_manifest_csv: Path = DEFAULT_SOURCE_MANIFEST,
    source_zip: Path | None = None,
    private_receipt_path: Path | None = None,
    generated_at: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_package = load_source_package(source_manifest_csv)
    rows = inventory_rows(inventory_csv)
    generated_timestamp = generated_at or datetime.now(timezone.utc).isoformat()
    private_binding_status = "required_not_verified"
    if source_zip is not None:
        if private_receipt_path is None:
            raise ValueError("private_receipt_path is required when a private source ZIP is supplied")
        _write_private_receipt(
            private_receipt_path,
            source_package=source_package,
            source_zip=source_zip,
            rows=rows,
            generated_at=generated_timestamp,
        )
        private_binding_status = "verified_private_receipt"

    files: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        file_format = classify_file_type(row["文件类型"])
        file_id = f"A0-FILE-PUB-V2-{index:03d}"
        source_file_ref = f"A0-SOURCE-FILE-PUB-V2-{index:03d}"
        files.append(
            {
                "record_type": "a0_source_file_public_projection",
                "schema_version": PUBLIC_FILE_SCHEMA,
                "a0_file_id": file_id,
                "source_package_ref": SOURCE_PACKAGE_REF,
                "source_file_ref": source_file_ref,
                "source_file_order": index,
                "file_format": file_format,
                "file_role": "a0_project_cost_workbook" if file_format == "xlsx" else "a0_supporting_pdf",
                "private_binding_required": True,
                "private_binding_receipt_status": private_binding_status,
                "raw_file_committed": False,
                "raw_content_committed": False,
                "field_extraction_allowed_in_s05p1": False,
            }
        )
        candidates.append(
            {
                "record_type": "a0_project_candidate_public_projection",
                "schema_version": PUBLIC_CANDIDATE_SCHEMA,
                "candidate_id": f"A0-CAND-PUB-V2-{index:03d}",
                "a0_file_id": file_id,
                "source_file_ref": source_file_ref,
                "candidate_order": index,
                "display_name_status": "private_only_not_committed",
                "private_binding_required": True,
                "private_binding_receipt_status": private_binding_status,
                "machine_candidate_quality_grade": "Q3",
                "q4_human_locked": False,
                "q5_calculation_baseline_allowed": False,
                "q5_formal_report_allowed": False,
                "raw_business_values_committed": False,
                "next_required_phase": "S05-P2 field-level golden baseline",
            }
        )

    manifest = {
        "record_type": "a0_file_registration_public_projection",
        "schema_version": PUBLIC_SCHEMA,
        "project_id": "KMFA",
        "stage_phase": "S05-P1",
        "generated_at": generated_timestamp,
        "source_package": {
            "source_package_ref": SOURCE_PACKAGE_REF,
            "package_format": "zip",
            "package_role": "a0_private_source_bundle",
            "private_binding_required": True,
            "private_binding_receipt_status": private_binding_status,
            "raw_package_committed": False,
            "public_repo_raw_allowed": False,
        },
        "file_summary": {
            "total_files": len(files),
            "pdf_files": sum(1 for item in files if item["file_format"] == "pdf"),
            "excel_files": sum(1 for item in files if item["file_format"] == "xlsx"),
            "private_binding_verified_count": len(files) if private_binding_status == "verified_private_receipt" else 0,
            "private_binding_required_count": len(files),
        },
        "quality_policy": {
            "q3_meaning": "machine candidate from public format and role projection only",
            "q4_requires": "private binding receipt plus human confirmation",
            "q5_requires": "private binding receipt and later zero-delta validation",
            "formal_report_allowed": False,
        },
        "public_repo_safety": {
            "raw_file_bytes_committed": False,
            "raw_business_values_committed": False,
            "raw_filename_or_digest_committed": False,
            "private_binding_may_not_be_claimed_without_private_receipt": True,
        },
        "files": files,
    }
    validate_a0_registration(manifest, candidates)
    return manifest, candidates


def validate_private_binding_receipt(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != PRIVATE_RECEIPT_SCHEMA:
        raise ValueError("invalid private A0 source binding receipt schema")
    if payload.get("classification") != "private_sensitive_do_not_commit":
        raise ValueError("private A0 source binding receipt classification is invalid")
    bindings = payload.get("member_bindings")
    if not isinstance(bindings, list) or len(bindings) != EXPECTED_PDF_COUNT + EXPECTED_EXCEL_COUNT:
        raise ValueError("private A0 source binding receipt must contain exactly 9 member bindings")
    if any(not re.fullmatch(r"[a-f0-9]{64}", str(item.get("member_sha256", ""))) for item in bindings):
        raise ValueError("private A0 source binding receipt contains invalid member digest")
    return payload


def validate_a0_registration(
    manifest: dict[str, Any],
    candidates: list[dict[str, Any]],
    *,
    require_member_sha256: bool = False,
    private_receipt_path: Path | None = None,
) -> None:
    _walk_public(manifest)
    _walk_public(candidates)
    if manifest.get("schema_version") != PUBLIC_SCHEMA:
        raise ValueError("invalid A0 public projection schema_version")
    source_package = manifest.get("source_package") or {}
    if source_package.get("source_package_ref") != SOURCE_PACKAGE_REF:
        raise ValueError("invalid opaque source package reference")
    if source_package.get("raw_package_committed") is not False:
        raise ValueError("raw package must not be committed")

    files = manifest.get("files")
    if not isinstance(files, list):
        raise ValueError("manifest files must be a list")
    if len(files) != EXPECTED_PDF_COUNT + EXPECTED_EXCEL_COUNT:
        raise ValueError("A0 registration must contain exactly 9 files")
    if sum(item.get("file_format") == "pdf" for item in files) != EXPECTED_PDF_COUNT:
        raise ValueError("A0 registration must contain exactly 8 PDF files")
    if sum(item.get("file_format") == "xlsx" for item in files) != EXPECTED_EXCEL_COUNT:
        raise ValueError("A0 registration must contain exactly 1 Excel file")
    for index, item in enumerate(files, start=1):
        if item.get("schema_version") != PUBLIC_FILE_SCHEMA:
            raise ValueError("invalid A0 source file public projection schema")
        if item.get("a0_file_id") != f"A0-FILE-PUB-V2-{index:03d}" or not OPAQUE_FILE_RE.fullmatch(str(item.get("a0_file_id", ""))):
            raise ValueError("A0 file IDs must be order-only v2 opaque references")
        if item.get("source_file_ref") != f"A0-SOURCE-FILE-PUB-V2-{index:03d}" or not OPAQUE_SOURCE_RE.fullmatch(str(item.get("source_file_ref", ""))):
            raise ValueError("A0 source file refs must be order-only v2 opaque references")
        if item.get("raw_file_committed") is not False or item.get("raw_content_committed") is not False:
            raise ValueError("A0 file records must not commit raw files or content")

    if len(candidates) != len(files):
        raise ValueError("candidate list must align 1:1 with A0 files")
    for index, candidate in enumerate(candidates, start=1):
        if candidate.get("schema_version") != PUBLIC_CANDIDATE_SCHEMA:
            raise ValueError("invalid A0 candidate public projection schema")
        if candidate.get("candidate_id") != f"A0-CAND-PUB-V2-{index:03d}" or not OPAQUE_CANDIDATE_RE.fullmatch(str(candidate.get("candidate_id", ""))):
            raise ValueError("A0 candidate IDs must be order-only v2 opaque references")
        if candidate.get("a0_file_id") != files[index - 1]["a0_file_id"]:
            raise ValueError("candidate references unknown A0 file")
        if candidate.get("q4_human_locked") is not False or candidate.get("q5_calculation_baseline_allowed") is not False:
            raise ValueError("public projection without private receipt cannot claim Q4/Q5 authority")
        if candidate.get("q5_formal_report_allowed") is not False:
            raise ValueError("A0 public candidates must not allow formal reports")

    if require_member_sha256:
        if private_receipt_path is None:
            raise ValueError("private receipt is required for a private binding claim")
        validate_private_binding_receipt(private_receipt_path)
        if source_package.get("private_binding_receipt_status") != "verified_private_receipt":
            raise ValueError("public projection does not record a verified private receipt status")


def write_outputs(
    manifest: dict[str, Any], candidates: list[dict[str, Any]], output_manifest: Path, output_candidates: Path
) -> None:
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_candidates.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_candidates.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in candidates) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA public-safe A0 source registration projection v2.")
    parser.add_argument("--inventory-csv", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--source-manifest-csv", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--source-zip", type=Path)
    parser.add_argument("--private-receipt", type=Path, default=DEFAULT_PRIVATE_RECEIPT)
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
        private_receipt_path=args.private_receipt if args.source_zip else None,
        generated_at=args.generated_at,
    )
    validate_a0_registration(
        manifest,
        candidates,
        require_member_sha256=args.require_member_sha256,
        private_receipt_path=args.private_receipt if args.source_zip else None,
    )
    if not args.check_only:
        write_outputs(manifest, candidates, args.output_manifest, args.output_candidates)
    summary = manifest["file_summary"]
    print(
        "PASS: A0 public projection v2 built "
        f"(files={summary['total_files']}, pdf={summary['pdf_files']}, excel={summary['excel_files']}, "
        f"private_binding_verified={summary['private_binding_verified_count']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
