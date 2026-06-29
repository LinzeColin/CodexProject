#!/usr/bin/env python3
"""Register local files for KMFA S03-P1 without committing raw data.

The tool emits metadata records only: hashes, sizes, source/import ids,
container hints, and operator guidance. Raw file bytes and plaintext content
must stay in local/private storage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


SUPPORTED_EXTENSIONS = {".zip", ".xlsx", ".xls", ".csv", ".pdf", ".wps", ".et", ".dps"}
OLE_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
ZIP_MAGIC = b"PK\x03\x04"
PDF_MAGIC = b"%PDF"


class UnsafeArchiveError(ValueError):
    """Raised when a zip archive member would escape the target directory."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    if len(slug) < 3:
        raise ValueError(f"slug must contain at least 3 ASCII letters or digits: {value!r}")
    return slug[:40]


def parse_received_at(value: str | None) -> datetime:
    if value:
        return datetime.fromisoformat(value)
    return datetime.now(timezone.utc)


def read_magic(path: Path, size: int = 8) -> bytes:
    with path.open("rb") as handle:
        return handle.read(size)


def detect_format(path: Path) -> tuple[str, str, str]:
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"unsupported file extension for S03-P1 registration: {extension}")

    magic = read_magic(path)
    if extension == ".csv":
        return "csv", "flat_text", "登记完成；字段解析和金额标准化属于后续 Stage。"
    if extension == ".pdf":
        container = "pdf" if magic.startswith(PDF_MAGIC) else "pdf_unknown_magic"
        return "pdf", container, "登记完成；PDF 文本抽取和字段确认属于后续 Stage。"
    if extension == ".zip":
        container = "zip_archive" if magic.startswith(ZIP_MAGIC) else "zip_unknown_magic"
        return "zip", container, "登记完成；可使用安全解包输出到本地私有目录。"
    if extension == ".xlsx":
        container = "office_open_xml_zip" if magic.startswith(ZIP_MAGIC) else "xlsx_unknown_magic"
        return "xlsx", container, "登记完成；Excel 字段映射属于后续 Stage。"
    if extension == ".xls":
        if magic.startswith(OLE_MAGIC):
            return "xls", "ole_compound", "识别为 OLE 旧版 Excel；建议先转换为 .xlsx 或 .csv 后再进入字段解析。"
        return "xls", "xls_unknown_magic", "旧版 Excel 魔数不标准；建议重新导出为 .xlsx 或 .csv。"
    return "wps", "wps_native", "识别为 WPS 原生格式；请先用 WPS 导出为 .xlsx 或 .csv，再进入字段解析。"


def build_ids(file_hash: str, batch_slug: str, source_slug: str, received_at: datetime) -> tuple[str, str]:
    batch = slugify(batch_slug)
    source = slugify(source_slug)
    stamp = received_at.strftime("%Y%m%d-%H%M%S")
    import_suffix = sha256_bytes(f"{file_hash}:{batch}:{stamp}".encode("utf-8"))[:8]
    source_suffix = sha256_bytes(source.encode("utf-8"))[:8]
    return f"IMP-{stamp}-{batch}-{import_suffix}", f"SRC-{source}-{source_suffix}"


def build_import_registration(
    input_path: str | Path,
    *,
    batch_slug: str,
    source_slug: str,
    received_at: str | None = None,
) -> dict[str, Any]:
    path = Path(input_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    timestamp = parse_received_at(received_at)
    file_hash = sha256_file(path)
    filename_hash = sha256_bytes(path.name.encode("utf-8"))
    file_format, container_type, guidance = detect_format(path)
    import_run_id, source_id = build_ids(file_hash, batch_slug, source_slug, timestamp)
    storage_ref = f"private://imports/{import_run_id}/sha256-{filename_hash}"

    source_package_ref = {
        "source_id": source_id,
        "source_package_hash": f"sha256:{file_hash}",
        "source_package_size_bytes": path.stat().st_size,
        "source_package_storage_ref": storage_ref,
    }

    manifest = {
        "record_type": "raw_file_manifest",
        "schema_version": "kmfa.raw_file_manifest.v1",
        "import_run_id": import_run_id,
        "source_id": source_id,
        "file_hash": f"sha256:{file_hash}",
        "file_size_bytes": path.stat().st_size,
        "storage_ref": storage_ref,
        "original_filename_hash": f"sha256:{filename_hash}",
        "file_format": file_format,
        "container_type": container_type,
        "received_at": timestamp.isoformat(),
        "manifest_status": "registered",
        "source_package_ref": source_package_ref,
        "evidence_ref": "local_private_file_registration_only",
    }
    import_run = {
        "record_type": "import_run",
        "schema_version": "kmfa.import_run.v1",
        "import_run_id": import_run_id,
        "source_id": source_id,
        "batch_slug": slugify(batch_slug),
        "received_at": timestamp.isoformat(),
        "status": "registered",
        "raw_file_count": 1,
        "source_package_ref": source_package_ref,
    }
    source = {
        "record_type": "source_registry_entry",
        "schema_version": "kmfa.source_registry.v1",
        "source_id": source_id,
        "source_category": "local_file_upload",
        "source_label": slugify(source_slug),
        "owner_role": "owner",
        "status": "registered",
        "evidence_ref": "local_private_file_registration_only",
    }
    return {
        "record_type": "file_import_registration_bundle",
        "schema_version": "kmfa.s03p1.file_import_registration.v1",
        "operator_guidance": guidance,
        "import_run": import_run,
        "source": source,
        "raw_file_manifest": manifest,
    }


def ensure_safe_member(member: zipfile.ZipInfo) -> PurePosixPath:
    name = member.filename
    pure = PurePosixPath(name)
    if pure.is_absolute() or any(part in {"..", ""} for part in pure.parts):
        raise UnsafeArchiveError(f"unsafe zip member path: {name}")
    mode = member.external_attr >> 16
    if mode & 0o170000 == 0o120000:
        raise UnsafeArchiveError(f"refusing to extract symlink member: {name}")
    return pure


def safe_extract_zip(zip_path: str | Path, extract_dir: str | Path) -> list[dict[str, Any]]:
    archive_path = Path(zip_path)
    target_root = Path(extract_dir).resolve()
    target_root.mkdir(parents=True, exist_ok=True)
    extracted: list[dict[str, Any]] = []

    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            pure = ensure_safe_member(member)
            if member.is_dir():
                (target_root / pure.as_posix()).mkdir(parents=True, exist_ok=True)
                continue

            destination = (target_root / pure.as_posix()).resolve()
            if os.path.commonpath([target_root, destination]) != str(target_root):
                raise UnsafeArchiveError(f"unsafe zip destination: {member.filename}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            size = 0
            with archive.open(member) as source, destination.open("wb") as output:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
                    size += len(chunk)
                    output.write(chunk)
            extracted.append(
                {
                    "member_path": pure.as_posix(),
                    "file_size_bytes": size,
                    "file_hash": f"sha256:{digest.hexdigest()}",
                    "storage_ref": f"private://zip-extract/{archive_path.stem}/{sha256_bytes(pure.as_posix().encode('utf-8'))}",
                }
            )
    return extracted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register a KMFA S03-P1 local file import.")
    parser.add_argument("--input", required=True, help="Local private file path to register.")
    parser.add_argument("--batch-slug", required=True)
    parser.add_argument("--source-slug", required=True)
    parser.add_argument("--received-at")
    parser.add_argument("--extract-dir", help="Optional private directory for safe zip extraction.")
    args = parser.parse_args(argv)

    bundle = build_import_registration(
        args.input,
        batch_slug=args.batch_slug,
        source_slug=args.source_slug,
        received_at=args.received_at,
    )
    if args.extract_dir:
        input_path = Path(args.input)
        if input_path.suffix.lower() != ".zip":
            raise SystemExit("--extract-dir is only valid for .zip inputs")
        bundle["zip_extract_result"] = safe_extract_zip(input_path, args.extract_dir)
    print(json.dumps(bundle, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
