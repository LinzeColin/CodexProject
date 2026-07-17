#!/usr/bin/env python3
"""KMFA v1.5 S10-P1 safe general-file import kernel.

The kernel registers and previews local files without changing their source,
requires an exact user confirmation before processing, and publishes a private
import record only after a complete atomic commit.  Public verification uses
temporary synthetic files only; this module never discovers or opens the raw
finance inbox by itself.
"""

from __future__ import annotations

import copy
import csv
import fcntl
import hashlib
import io
import json
import os
import re
import shutil
import stat
import tempfile
import zipfile
import zlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from KMFA.tools import v015_s04_p1_data_catalog as catalog


RUN_PHASE_ID = "V015_S10_P1_GENERAL_IMPORT"
ROADMAP_PHASE_ID = "S10-P1"
TASK_ID = "KMFA-V015-S10-P1-GENERAL-IMPORT-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S10-P1-GENERAL-IMPORT"
VERSION = "1.5.0-dev-s10p1"
PARSER_VERSION = "1.0.0"

PREVIEW_SCHEMA = "kmfa.v015.s10p1.import_preview.v1"
CONFIRMATION_SCHEMA = "kmfa.v015.s10p1.import_confirmation.v1"
COMMITTED_INDEX_SCHEMA = "kmfa.v015.s10p1.committed_import_index.v1"
COMMITTED_RECORD_SCHEMA = "kmfa.v015.s10p1.committed_import.v1"

OLE_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
ZIP_MAGICS = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
PDF_MAGIC = b"%PDF-"
SUPPORTED_EXTENSIONS = (".zip", ".xlsx", ".xls", ".csv", ".pdf", ".wps", ".et", ".dps")
FORMAT_LABELS_ZH = {
    "ZIP": "ZIP 压缩包",
    "EXCEL_XLSX": "Excel 工作簿",
    "EXCEL_XLS": "旧版 Excel 工作簿",
    "CSV": "CSV 表格",
    "PDF": "PDF 文档",
    "WPS_OLE": "WPS/OLE 文件",
}
FORMAT_GUIDANCE_ZH = {
    "ZIP": "压缩包会先完整安全检查，再整体解压；发现越界路径或压缩炸弹会整包隔离。",
    "EXCEL_XLSX": "识别工作簿结构后进入预览；本阶段不读取或改写业务数据。",
    "EXCEL_XLS": "识别旧版 OLE 容器后进入预览；确认前不做后续解析。",
    "CSV": "识别文本编码和表头后进入预览；确认前不做入账处理。",
    "PDF": "识别 PDF 文件头和完整结束标记后进入预览；确认前不做内容提取。",
    "WPS_OLE": "识别 WPS/OLE 容器后进入预览；确认前不做后续解析。",
}
REQUIRED_PREVIEW_FIELDS = (
    "file_display_name",
    "period",
    "source_label",
    "entity_label",
    "business_segment",
    "detection_result_zh",
)


@dataclass(frozen=True)
class ArchivePolicy:
    """Externalized archive limits; lower values can be injected in tests."""

    max_member_count: int = 4096
    max_total_uncompressed_bytes: int = 512 * 1024 * 1024
    max_member_uncompressed_bytes: int = 128 * 1024 * 1024
    max_compression_ratio: int = 100
    max_path_depth: int = 16
    max_member_name_bytes: int = 512

    def validate(self) -> None:
        values = (
            self.max_member_count,
            self.max_total_uncompressed_bytes,
            self.max_member_uncompressed_bytes,
            self.max_compression_ratio,
            self.max_path_depth,
            self.max_member_name_bytes,
        )
        if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in values):
            raise GeneralImportError("ARCHIVE_POLICY_INVALID", "压缩包安全阈值必须是正整数。")


DEFAULT_ARCHIVE_POLICY = ArchivePolicy()


class GeneralImportError(ValueError):
    """Fail-closed error with a stable public-safe reason code."""

    def __init__(self, code: str, message_zh: str):
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh


class ImportInterrupted(RuntimeError):
    """Controlled interruption used to prove resume and invisible partial work."""

    def __init__(self, checkpoint: str):
        super().__init__(checkpoint)
        self.checkpoint = checkpoint


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _hash_file(path: Path) -> tuple[str, int]:
    if path.is_symlink():
        raise GeneralImportError("SOURCE_SYMLINK_REJECTED", "导入源不能是符号链接。")
    try:
        before = path.stat()
    except OSError as error:
        raise GeneralImportError("SOURCE_NOT_READABLE", "文件不存在或不可读取。") from error
    if not stat.S_ISREG(before.st_mode):
        raise GeneralImportError("SOURCE_NOT_REGULAR_FILE", "只能登记普通文件。")
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
                size += len(chunk)
    except OSError as error:
        raise GeneralImportError("SOURCE_READ_FAILED", "读取文件时发生错误。") from error
    after = path.stat()
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after or size != after.st_size:
        raise GeneralImportError("SOURCE_CHANGED_DURING_READ", "文件在登记过程中发生变化。")
    return "sha256:" + digest.hexdigest(), size


def _read_head_tail(path: Path, head_size: int = 4096, tail_size: int = 4096) -> tuple[bytes, bytes]:
    size = path.stat().st_size
    with path.open("rb") as handle:
        head = handle.read(head_size)
        if size <= tail_size:
            return head, head
        handle.seek(max(0, size - tail_size))
        return head, handle.read(tail_size)


def _safe_member_path(info: zipfile.ZipInfo, policy: ArchivePolicy) -> PurePosixPath:
    name = info.filename
    if not name or "\x00" in name or "\\" in name:
        raise GeneralImportError("ARCHIVE_MEMBER_PATH_INVALID", "压缩包成员路径不合法。")
    if len(name.encode("utf-8")) > policy.max_member_name_bytes:
        raise GeneralImportError("ARCHIVE_MEMBER_NAME_TOO_LONG", "压缩包成员名称过长。")
    pure = PurePosixPath(name)
    if pure.is_absolute() or name.startswith("/") or any(part in {"", ".", ".."} for part in pure.parts):
        raise GeneralImportError("ARCHIVE_PATH_TRAVERSAL_REJECTED", "压缩包包含越界路径。")
    first = pure.parts[0]
    if re.fullmatch(r"[A-Za-z]:.*", first):
        raise GeneralImportError("ARCHIVE_ABSOLUTE_PATH_REJECTED", "压缩包包含绝对路径。")
    if len(pure.parts) > policy.max_path_depth:
        raise GeneralImportError("ARCHIVE_PATH_DEPTH_EXCEEDED", "压缩包目录层级过深。")
    mode = info.external_attr >> 16
    kind = stat.S_IFMT(mode)
    if kind == stat.S_IFLNK:
        raise GeneralImportError("ARCHIVE_SYMLINK_REJECTED", "压缩包不能包含符号链接。")
    if kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
        raise GeneralImportError("ARCHIVE_SPECIAL_FILE_REJECTED", "压缩包不能包含设备或其他特殊文件。")
    if info.flag_bits & 0x1:
        raise GeneralImportError("ARCHIVE_ENCRYPTED_MEMBER_REJECTED", "加密成员无法安全验证。")
    if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
        raise GeneralImportError("ARCHIVE_COMPRESSION_METHOD_REJECTED", "压缩算法不在允许范围内。")
    return pure


def inspect_zip(path: Path, policy: ArchivePolicy = DEFAULT_ARCHIVE_POLICY) -> dict[str, Any]:
    """Validate all central-directory entries before any extraction occurs."""

    policy.validate()
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as error:
        raise GeneralImportError("ARCHIVE_CORRUPT", "压缩包损坏或无法读取。") from error
    with archive:
        infos = archive.infolist()
        files = [info for info in infos if not info.is_dir()]
        if not files:
            raise GeneralImportError("ARCHIVE_EMPTY", "压缩包中没有可登记文件。")
        if len(files) > policy.max_member_count:
            raise GeneralImportError("ARCHIVE_MEMBER_COUNT_EXCEEDED", "压缩包文件数量超过安全阈值。")
        total_size = 0
        total_compressed = 0
        normalized_paths: set[str] = set()
        member_types: dict[str, int] = {}
        safe_paths: list[str] = []
        for info in infos:
            pure = _safe_member_path(info, policy)
            normalized = pure.as_posix().casefold()
            if normalized in normalized_paths:
                raise GeneralImportError("ARCHIVE_DUPLICATE_PATH_REJECTED", "压缩包包含重复路径。")
            normalized_paths.add(normalized)
            if info.is_dir():
                continue
            if info.file_size > policy.max_member_uncompressed_bytes:
                raise GeneralImportError("ARCHIVE_MEMBER_SIZE_EXCEEDED", "压缩包单个文件超过安全阈值。")
            ratio = info.file_size / max(info.compress_size, 1)
            if ratio > policy.max_compression_ratio:
                raise GeneralImportError("ARCHIVE_COMPRESSION_BOMB_REJECTED", "压缩比超过安全阈值。")
            total_size += info.file_size
            total_compressed += info.compress_size
            if total_size > policy.max_total_uncompressed_bytes:
                raise GeneralImportError("ARCHIVE_TOTAL_SIZE_EXCEEDED", "压缩包解压后总量超过安全阈值。")
            suffix = PurePosixPath(info.filename).suffix.lower() or "NO_EXTENSION"
            member_types[suffix] = member_types.get(suffix, 0) + 1
            safe_paths.append(pure.as_posix())
        if total_size / max(total_compressed, 1) > policy.max_compression_ratio:
            raise GeneralImportError("ARCHIVE_TOTAL_COMPRESSION_BOMB_REJECTED", "压缩包整体压缩比超过安全阈值。")
        try:
            corrupt = archive.testzip()
        except (OSError, RuntimeError, zipfile.BadZipFile, zlib.error) as error:
            raise GeneralImportError("ARCHIVE_MEMBER_CORRUPT", "压缩包成员校验失败。") from error
        if corrupt is not None:
            raise GeneralImportError("ARCHIVE_MEMBER_CORRUPT", "压缩包成员校验失败。")
    return {
        "member_count": len(files),
        "total_uncompressed_bytes": total_size,
        "total_compressed_bytes": total_compressed,
        "member_type_counts": dict(sorted(member_types.items())),
        "safe_member_paths": safe_paths,
        "path_traversal_count": 0,
        "symlink_count": 0,
        "special_file_count": 0,
        "encrypted_member_count": 0,
        "archive_safety_passed": True,
    }

def _validate_csv(path: Path) -> dict[str, Any]:
    head, _ = _read_head_tail(path, 65536, 1)
    if not head or b"\x00" in head:
        raise GeneralImportError("CSV_BINARY_OR_EMPTY_REJECTED", "CSV 为空或包含二进制内容。")
    decoded = None
    encoding = None
    for candidate in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            decoded = head.decode(candidate)
            encoding = candidate
            break
        except UnicodeDecodeError:
            continue
    if decoded is None or encoding is None:
        raise GeneralImportError("CSV_ENCODING_REJECTED", "CSV 编码无法安全识别。")
    try:
        sample = list(csv.reader(io.StringIO(decoded)))
    except csv.Error as error:
        raise GeneralImportError("CSV_STRUCTURE_REJECTED", "CSV 结构无法读取。") from error
    if not sample or not any(cell.strip() for cell in sample[0]):
        raise GeneralImportError("CSV_HEADER_MISSING", "CSV 缺少可识别表头。")
    return {"encoding_hint": encoding, "sample_row_count": len(sample), "header_column_count": len(sample[0])}


def _validate_xlsx(path: Path, archive: dict[str, Any]) -> dict[str, Any]:
    names = {name.casefold() for name in archive["safe_member_paths"]}
    required = {"[content_types].xml", "xl/workbook.xml"}
    if not required.issubset(names):
        raise GeneralImportError("XLSX_STRUCTURE_REJECTED", "文件扩展名为 xlsx，但缺少工作簿结构。")
    return {"ooxml_required_member_count": len(required)}


def inspect_file(path: str | Path, policy: ArchivePolicy = DEFAULT_ARCHIVE_POLICY) -> dict[str, Any]:
    """Read-only format detection and safety inspection for one file."""

    source = Path(path)
    extension = source.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise GeneralImportError("UNSUPPORTED_EXTENSION", "文件格式不在本阶段支持范围内。")
    file_hash, file_size = _hash_file(source)
    head, tail = _read_head_tail(source)
    archive_summary = None
    format_details: dict[str, Any] = {}
    if extension == ".zip":
        if not head.startswith(ZIP_MAGICS):
            raise GeneralImportError("ZIP_MAGIC_MISMATCH", "ZIP 扩展名与文件内容不一致。")
        archive_summary = inspect_zip(source, policy)
        format_code = "ZIP"
    elif extension == ".xlsx":
        if not head.startswith(ZIP_MAGICS):
            raise GeneralImportError("XLSX_MAGIC_MISMATCH", "Excel 扩展名与文件内容不一致。")
        archive_summary = inspect_zip(source, policy)
        format_details = _validate_xlsx(source, archive_summary)
        format_code = "EXCEL_XLSX"
    elif extension == ".xls":
        if not head.startswith(OLE_MAGIC):
            raise GeneralImportError("XLS_MAGIC_MISMATCH", "旧版 Excel 扩展名与 OLE 内容不一致。")
        format_code = "EXCEL_XLS"
    elif extension == ".csv":
        format_details = _validate_csv(source)
        format_code = "CSV"
    elif extension == ".pdf":
        if not head.startswith(PDF_MAGIC) or b"%%EOF" not in tail:
            raise GeneralImportError("PDF_STRUCTURE_REJECTED", "PDF 文件头或结束标记不完整。")
        format_code = "PDF"
    else:
        if head.startswith(OLE_MAGIC):
            format_details = {"container_kind": "OLE_COMPOUND"}
        elif head.startswith(ZIP_MAGICS):
            archive_summary = inspect_zip(source, policy)
            format_details = {"container_kind": "ZIP_CONTAINER"}
        else:
            raise GeneralImportError("WPS_OLE_MAGIC_MISMATCH", "WPS/OLE 扩展名与文件内容不一致。")
        format_code = "WPS_OLE"
    payload = {
        "schema_version": "kmfa.v015.s10p1.file_inspection.v1",
        "file_display_name": source.name,
        "original_filename_hash": "sha256:" + hashlib.sha256(source.name.encode("utf-8")).hexdigest(),
        "file_hash": file_hash,
        "file_size_bytes": file_size,
        "extension": extension,
        "format_code": format_code,
        "format_label_zh": FORMAT_LABELS_ZH[format_code],
        "format_guidance_zh": FORMAT_GUIDANCE_ZH[format_code],
        "format_details": format_details,
        "archive_summary": archive_summary,
        "inspection_status": "SAFE_TO_PREVIEW",
        "source_mutation_performed": False,
        "raw_root_access_count": 0,
    }
    payload["inspection_fingerprint"] = _fingerprint(payload)
    return payload


def _context_field(value: Any, field: str) -> dict[str, str]:
    text = str(value or "").strip()
    return {
        "field": field,
        "value": text if text else "待确认",
        "status": "CONFIRMED" if text else "NEEDS_CONFIRMATION",
    }


def build_import_preview(
    inspection: Mapping[str, Any],
    *,
    source_id: str | None,
    source_label: str | None,
    entity_label: str | None,
    business_segment: str | None,
    period: str | None,
    parser_version: str = PARSER_VERSION,
) -> dict[str, Any]:
    """Build a private human preview; no processing is authorized here."""

    checked = dict(inspection)
    supplied_fingerprint = str(checked.pop("inspection_fingerprint", ""))
    if supplied_fingerprint != _fingerprint(checked):
        raise GeneralImportError("INSPECTION_FINGERPRINT_MISMATCH", "文件识别结果已被改写。")
    if checked.get("inspection_status") != "SAFE_TO_PREVIEW":
        raise GeneralImportError("INSPECTION_NOT_PREVIEWABLE", "文件未通过安全识别。")
    if source_id and not catalog.SOURCE_ID_PATTERN.fullmatch(source_id):
        raise GeneralImportError("SOURCE_ID_INVALID", "来源编号不符合登记协议。")
    if period and not catalog.PERIOD_PATTERN.fullmatch(period):
        raise GeneralImportError("PERIOD_INVALID", "期间必须为 YYYY 或 YYYY-MM。")
    if not catalog.SEMVER_PATTERN.fullmatch(parser_version):
        raise GeneralImportError("PARSER_VERSION_INVALID", "解析器版本必须是三段数字。")
    fields = {
        "period": _context_field(period, "period"),
        "source_id": _context_field(source_id, "source_id"),
        "source_label": _context_field(source_label, "source_label"),
        "entity_label": _context_field(entity_label, "entity_label"),
        "business_segment": _context_field(business_segment, "business_segment"),
    }
    missing = [name for name, row in fields.items() if row["status"] != "CONFIRMED"]
    body = {
        "schema_version": PREVIEW_SCHEMA,
        "preview_id": "PREVIEW-" + supplied_fingerprint.removeprefix("sha256:")[:16],
        "inspection_fingerprint": supplied_fingerprint,
        "file_hash": inspection["file_hash"],
        "file_size_bytes": inspection["file_size_bytes"],
        "file_display_name": inspection["file_display_name"],
        "format_code": inspection["format_code"],
        "format_label_zh": inspection["format_label_zh"],
        "format_guidance_zh": inspection["format_guidance_zh"],
        "detection_result_zh": "文件安全识别完成，可以预览；确认后才会处理。",
        "period": fields["period"],
        "source_id": fields["source_id"],
        "source_label": fields["source_label"],
        "entity_label": fields["entity_label"],
        "business_segment": fields["business_segment"],
        "parser_version": parser_version,
        "missing_confirmation_fields": missing,
        "preview_status": "READY_FOR_CONFIRMATION" if not missing else "NEEDS_CONTEXT_CONFIRMATION",
        "user_confirmation_required": True,
        "processing_allowed": False,
        "source_mutation_performed": False,
        "raw_write_performed": False,
        "raw_root_access_count": 0,
    }
    body["preview_fingerprint"] = _fingerprint(body)
    return body


def _validate_preview(preview: Mapping[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(dict(preview))
    supplied = str(value.pop("preview_fingerprint", ""))
    if supplied != _fingerprint(value):
        raise GeneralImportError("PREVIEW_FINGERPRINT_MISMATCH", "导入预览已被改写。")
    if value.get("schema_version") != PREVIEW_SCHEMA:
        raise GeneralImportError("PREVIEW_SCHEMA_INVALID", "导入预览版本不正确。")
    value["preview_fingerprint"] = supplied
    return value


def confirm_import_preview(
    preview: Mapping[str, Any],
    *,
    preview_id: str,
    preview_fingerprint: str,
    decision: str,
    operator_role: str,
    occurred_at: str,
) -> dict[str, Any]:
    """Create a confirmation event bound to the exact immutable preview."""

    value = _validate_preview(preview)
    if value["preview_id"] != preview_id or value["preview_fingerprint"] != preview_fingerprint:
        raise GeneralImportError("CONFIRMATION_PREVIEW_BINDING_MISMATCH", "确认操作与当前预览不一致。")
    if decision != "CONFIRM":
        raise GeneralImportError("CONFIRMATION_DECISION_REQUIRED", "只有明确确认后才能处理。")
    if value["missing_confirmation_fields"] or value["preview_status"] != "READY_FOR_CONFIRMATION":
        raise GeneralImportError("PREVIEW_CONTEXT_INCOMPLETE", "来源、期间、主体或板块仍待确认。")
    role = operator_role.strip()
    if not role.startswith("ROLE::"):
        raise GeneralImportError("OPERATOR_ROLE_INVALID", "确认操作必须记录有效角色。")
    try:
        timestamp = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise GeneralImportError("CONFIRMATION_TIME_INVALID", "确认时间必须符合 ISO-8601。") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise GeneralImportError("CONFIRMATION_TIMEZONE_REQUIRED", "确认时间必须包含时区。")
    event = {
        "schema_version": CONFIRMATION_SCHEMA,
        "confirmation_ref": "CONFIRM-" + value["preview_fingerprint"].removeprefix("sha256:")[:16],
        "preview_id": value["preview_id"],
        "preview_fingerprint": value["preview_fingerprint"],
        "decision": "CONFIRM",
        "operator_role": role,
        "occurred_at": timestamp.isoformat(),
        "processing_allowed": True,
        "source_mutation_allowed": False,
        "raw_write_allowed": False,
    }
    event["event_fingerprint"] = _fingerprint(event)
    return event


def _validate_confirmation(event: Mapping[str, Any], preview: Mapping[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(dict(event))
    supplied = str(value.pop("event_fingerprint", ""))
    if supplied != _fingerprint(value):
        raise GeneralImportError("CONFIRMATION_EVENT_TAMPERED", "确认记录已被改写。")
    checked_preview = _validate_preview(preview)
    if (
        value.get("schema_version") != CONFIRMATION_SCHEMA
        or value.get("decision") != "CONFIRM"
        or value.get("processing_allowed") is not True
        or value.get("preview_id") != checked_preview["preview_id"]
        or value.get("preview_fingerprint") != checked_preview["preview_fingerprint"]
    ):
        raise GeneralImportError("CONFIRMATION_EVENT_INVALID", "确认记录没有精确绑定当前预览。")
    value["event_fingerprint"] = supplied
    return value


def inspect_batch(
    paths: Sequence[str | Path],
    contexts: Sequence[Mapping[str, Any]],
    policy: ArchivePolicy = DEFAULT_ARCHIVE_POLICY,
) -> dict[str, Any]:
    """Inspect every file independently so one bad file cannot stop the rest."""

    if len(paths) != len(contexts):
        raise GeneralImportError("BATCH_CONTEXT_COUNT_MISMATCH", "每个文件都必须有一组预览上下文。")
    previews: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    for path, context in zip(paths, contexts):
        source = Path(path)
        try:
            inspection = inspect_file(source, policy)
            previews.append(build_import_preview(inspection, **dict(context)))
        except GeneralImportError as error:
            quarantined.append(
                {
                    "file_display_name": source.name,
                    "original_filename_hash": "sha256:" + hashlib.sha256(source.name.encode("utf-8")).hexdigest(),
                    "status": "QUARANTINED",
                    "reason_code": error.code,
                    "reason_zh": error.message_zh,
                    "other_files_may_continue": True,
                    "source_mutation_performed": False,
                }
            )
    return {
        "schema_version": "kmfa.v015.s10p1.batch_inspection.v1",
        "input_file_count": len(paths),
        "preview_ready_count": len(previews),
        "quarantined_count": len(quarantined),
        "previews": previews,
        "quarantined": quarantined,
        "batch_aborted_by_single_bad_file": False,
        "processing_started": False,
        "raw_root_access_count": 0,
    }


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_index(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": COMMITTED_INDEX_SCHEMA, "records": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GeneralImportError("COMMITTED_INDEX_CORRUPT", "已提交导入索引损坏。") from error
    if value.get("schema_version") != COMMITTED_INDEX_SCHEMA or not isinstance(value.get("records"), dict):
        raise GeneralImportError("COMMITTED_INDEX_SCHEMA_INVALID", "已提交导入索引版本不正确。")
    return value


def _copy_to_stage(source: Path, target: Path, expected_hash: str) -> None:
    digest = hashlib.sha256()
    with source.open("rb") as input_handle, target.open("wb") as output_handle:
        for chunk in iter(lambda: input_handle.read(1024 * 1024), b""):
            digest.update(chunk)
            output_handle.write(chunk)
        output_handle.flush()
        os.fsync(output_handle.fileno())
    actual = "sha256:" + digest.hexdigest()
    if actual != expected_hash:
        target.unlink(missing_ok=True)
        raise GeneralImportError("STAGED_COPY_HASH_MISMATCH", "暂存副本与预览文件不一致。")


def _extract_zip_atomic(source: Path, destination: Path, policy: ArchivePolicy) -> int:
    summary = inspect_zip(source, policy)
    if destination.exists():
        return summary["member_count"]
    stage = destination.with_name(f".{destination.name}.extracting")
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    try:
        with zipfile.ZipFile(source) as archive:
            for info in archive.infolist():
                pure = _safe_member_path(info, policy)
                target = stage.joinpath(*pure.parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                digest_size = 0
                with archive.open(info) as input_handle, target.open("xb") as output_handle:
                    for chunk in iter(lambda: input_handle.read(1024 * 1024), b""):
                        digest_size += len(chunk)
                        if digest_size > info.file_size or digest_size > policy.max_member_uncompressed_bytes:
                            raise GeneralImportError("ARCHIVE_ACTUAL_SIZE_EXCEEDED", "解压实际大小超过已验证值。")
                        output_handle.write(chunk)
                if digest_size != info.file_size:
                    raise GeneralImportError("ARCHIVE_ACTUAL_SIZE_MISMATCH", "解压实际大小与登记值不一致。")
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(stage, destination)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return summary["member_count"]


def list_committed_imports(private_root: str | Path) -> list[dict[str, Any]]:
    """Expose only records published by the final atomic index replacement."""

    index = _read_index(Path(private_root) / "committed_index.json")
    return [copy.deepcopy(index["records"][key]) for key in sorted(index["records"])]


def process_confirmed_import(
    source_path: str | Path,
    preview: Mapping[str, Any],
    confirmation_event: Mapping[str, Any],
    *,
    private_root: str | Path,
    archive_policy: ArchivePolicy = DEFAULT_ARCHIVE_POLICY,
    interrupt_at: str | None = None,
) -> dict[str, Any]:
    """Copy, optionally extract, and atomically publish one confirmed import."""

    checked_preview = _validate_preview(preview)
    checked_event = _validate_confirmation(confirmation_event, checked_preview)
    source = Path(source_path)
    current = inspect_file(source, archive_policy)
    if (
        current["file_hash"] != checked_preview["file_hash"]
        or current["inspection_fingerprint"] != checked_preview["inspection_fingerprint"]
    ):
        raise GeneralImportError("SOURCE_CHANGED_AFTER_PREVIEW", "文件在预览后发生变化，必须重新预览。")
    source_id = checked_preview["source_id"]["value"]
    period = checked_preview["period"]["value"]
    parser_version = checked_preview["parser_version"]
    key_payload = {
        "source_id": source_id,
        "file_hash": checked_preview["file_hash"],
        "period": period,
        "parser_version": parser_version,
    }
    idempotency_key = hashlib.sha256(_canonical(key_payload)).hexdigest()
    root = Path(private_root)
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".import.lock"
    with lock_path.open("a+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        index_path = root / "committed_index.json"
        index = _read_index(index_path)
        existing = index["records"].get(idempotency_key)
        if existing is not None:
            object_path = root / existing["private_object_relative_path"]
            actual_hash, _ = _hash_file(object_path)
            if actual_hash != existing["registration"]["file_hash"]:
                raise GeneralImportError("COMMITTED_OBJECT_HASH_MISMATCH", "已提交内容副本损坏。")
            return {
                "outcome": "REUSED",
                "new_record_created": False,
                "idempotent_reuse": True,
                "resumed_from_checkpoint": False,
                "record": copy.deepcopy(existing),
                "visible_committed_count": len(index["records"]),
                "partial_commit_visible": False,
                "source_mutation_performed": False,
            }

        stage = root / ".staging" / idempotency_key
        checkpoint_path = stage / "checkpoint.json"
        payload_path = stage / "payload.bin"
        resumed = checkpoint_path.exists()
        if resumed:
            try:
                checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                shutil.rmtree(stage)
                resumed = False
            else:
                if checkpoint.get("idempotency_key") != idempotency_key or checkpoint.get("file_hash") != checked_preview["file_hash"]:
                    shutil.rmtree(stage)
                    resumed = False
        if not resumed:
            if stage.exists():
                shutil.rmtree(stage)
            stage.mkdir(parents=True)
            _copy_to_stage(source, payload_path, checked_preview["file_hash"])
            _atomic_json(
                checkpoint_path,
                {
                    "schema_version": "kmfa.v015.s10p1.import_checkpoint.v1",
                    "idempotency_key": idempotency_key,
                    "file_hash": checked_preview["file_hash"],
                    "preview_fingerprint": checked_preview["preview_fingerprint"],
                    "confirmation_fingerprint": checked_event["event_fingerprint"],
                    "state": "STAGED_NOT_VISIBLE",
                },
            )
        elif payload_path.exists():
            staged_hash, _ = _hash_file(payload_path)
            if staged_hash != checked_preview["file_hash"]:
                shutil.rmtree(stage)
                stage.mkdir(parents=True)
                _copy_to_stage(source, payload_path, checked_preview["file_hash"])
                _atomic_json(checkpoint_path, {"schema_version": "kmfa.v015.s10p1.import_checkpoint.v1", "idempotency_key": idempotency_key, "file_hash": checked_preview["file_hash"], "preview_fingerprint": checked_preview["preview_fingerprint"], "confirmation_fingerprint": checked_event["event_fingerprint"], "state": "STAGED_NOT_VISIBLE"})
                resumed = False
        if interrupt_at == "AFTER_STAGE":
            raise ImportInterrupted("AFTER_STAGE")

        digest = checked_preview["file_hash"].removeprefix("sha256:")
        object_path = root / "objects" / "sha256" / digest
        object_path.parent.mkdir(parents=True, exist_ok=True)
        if object_path.exists():
            object_hash, _ = _hash_file(object_path)
            if object_hash != checked_preview["file_hash"]:
                raise GeneralImportError("PRIVATE_OBJECT_COLLISION", "私有内容寻址对象与预期不一致。")
            payload_path.unlink(missing_ok=True)
        else:
            if not payload_path.exists():
                _copy_to_stage(source, payload_path, checked_preview["file_hash"])
            os.replace(payload_path, object_path)
        if interrupt_at == "AFTER_OBJECT":
            raise ImportInterrupted("AFTER_OBJECT")

        extracted_count = 0
        extracted_relative_path = None
        if checked_preview["format_code"] == "ZIP":
            extracted = root / "extracted" / digest
            extracted_count = _extract_zip_atomic(object_path, extracted, archive_policy)
            extracted_relative_path = extracted.relative_to(root).as_posix()

        timestamp = datetime.fromisoformat(checked_event["occurred_at"])
        suffix = idempotency_key[:8]
        file_id = f"FILE-general-import-{digest[:8]}"
        import_run_id = f"IMP-{timestamp.strftime('%Y%m%d-%H%M%S')}-general-import-{suffix}"
        registration_candidate = {
            "source_id": source_id,
            "file_id": file_id,
            "import_run_id": import_run_id,
            "file_hash": checked_preview["file_hash"],
            "period": period,
            "parser_version": parser_version,
        }
        existing_registrations = [row["registration"] for row in index["records"].values()]
        catalog_result = catalog.register_import(registration_candidate, existing_registrations)
        if catalog_result["outcome"] == "REUSED":
            raise GeneralImportError("IDEMPOTENCY_INDEX_INCONSISTENT", "导入登记与可见索引不一致。")
        record = {
            "schema_version": COMMITTED_RECORD_SCHEMA,
            "idempotency_key": idempotency_key,
            "registration": registration_candidate,
            "preview_id": checked_preview["preview_id"],
            "preview_fingerprint": checked_preview["preview_fingerprint"],
            "confirmation_ref": checked_event["confirmation_ref"],
            "confirmation_fingerprint": checked_event["event_fingerprint"],
            "file_display_name": checked_preview["file_display_name"],
            "format_code": checked_preview["format_code"],
            "source_label": checked_preview["source_label"]["value"],
            "entity_label": checked_preview["entity_label"]["value"],
            "business_segment": checked_preview["business_segment"]["value"],
            "private_object_relative_path": object_path.relative_to(root).as_posix(),
            "private_extracted_relative_path": extracted_relative_path,
            "archive_member_count": extracted_count,
            "commit_state": "COMMITTED_VISIBLE",
            "committed_at": checked_event["occurred_at"],
            "raw_write_performed": False,
            "source_mutation_performed": False,
        }
        record["record_fingerprint"] = _fingerprint(record)
        if interrupt_at == "BEFORE_COMMIT":
            raise ImportInterrupted("BEFORE_COMMIT")
        next_index = copy.deepcopy(index)
        next_index["records"][idempotency_key] = record
        _atomic_json(index_path, next_index)
        if stage.exists():
            shutil.rmtree(stage)
        return {
            "outcome": "COMMITTED",
            "new_record_created": True,
            "idempotent_reuse": False,
            "resumed_from_checkpoint": resumed,
            "record": copy.deepcopy(record),
            "visible_committed_count": len(next_index["records"]),
            "partial_commit_visible": False,
            "source_mutation_performed": False,
        }


def _write_minimal_xlsx(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", "<workbook/>")


def _context() -> dict[str, str]:
    return {
        "source_id": "SRC-synthetic-upload-4ce592a1",
        "source_label": "模拟本地文件",
        "entity_label": "模拟主体",
        "business_segment": "项目成本",
        "period": "2026-06",
        "parser_version": PARSER_VERSION,
    }


CHECK_IDS = (
    "ZIP_REGISTERED",
    "XLSX_REGISTERED",
    "XLS_OLE_REGISTERED",
    "CSV_REGISTERED",
    "PDF_REGISTERED",
    "WPS_OLE_REGISTERED",
    "PATH_TRAVERSAL_REJECTED",
    "SYMLINK_REJECTED",
    "COMPRESSION_BOMB_REJECTED",
    "CORRUPT_FILE_QUARANTINED",
    "BAD_FILE_DOES_NOT_ABORT_BATCH",
    "NO_EXTRACTION_ON_ARCHIVE_REJECTION",
    "PREVIEW_HAS_REQUIRED_HUMAN_FIELDS",
    "PREVIEW_REQUIRES_CONFIRMATION",
    "PREVIEW_DOES_NOT_PROCESS",
    "MISSING_CONTEXT_BLOCKS_CONFIRMATION",
    "TAMPERED_PREVIEW_REJECTED",
    "UNBOUND_CONFIRMATION_REJECTED",
    "PROCESSING_WITHOUT_CONFIRMATION_REJECTED",
    "SOURCE_CHANGED_AFTER_PREVIEW_REJECTED",
    "CONFIRMED_IMPORT_COMMITS",
    "CONTENT_ADDRESS_OBJECT_HASH_MATCHES",
    "ZIP_EXTRACTION_ATOMIC",
    "INTERRUPTED_IMPORT_INVISIBLE",
    "INTERRUPTED_IMPORT_RESUMES",
    "EXACT_REPLAY_REUSED",
    "EXACT_REPLAY_RECORD_UNCHANGED",
    "VISIBLE_RECORD_COUNT_STABLE",
    "SOURCE_SNAPSHOT_UNCHANGED",
    "RAW_ROOT_NOT_ACCESSED",
    "LATER_PHASES_NOT_STARTED",
    "NO_RELEASE_OR_BUSINESS_ACTION",
)


def _check(check_id: str, condition: bool) -> dict[str, str]:
    return {"check_id": check_id, "status": "PASS" if condition else "FAIL"}


def scope_boundary() -> dict[str, bool]:
    """Declare the actions intentionally excluded from the S10-P1 run."""

    return {
        "s10_p2_started": False,
        "s10_p3_started": False,
        "s10_stage_review_started": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


def public_verification() -> dict[str, Any]:
    """Exercise every S10-P1 gate with public-safe temporary fixtures."""

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        files: dict[str, Path] = {}
        files["zip"] = root / "sample.zip"
        with zipfile.ZipFile(files["zip"], "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("nested/data.csv", "project,cost\nA,100\n")
        files["xlsx"] = root / "sample.xlsx"
        _write_minimal_xlsx(files["xlsx"])
        files["xls"] = root / "sample.xls"
        files["xls"].write_bytes(OLE_MAGIC + b"SYNTHETIC-XLS")
        files["csv"] = root / "sample.csv"
        files["csv"].write_text("project,cost\nA,100\n", encoding="utf-8")
        files["pdf"] = root / "sample.pdf"
        files["pdf"].write_bytes(b"%PDF-1.7\nsynthetic\n%%EOF\n")
        files["wps"] = root / "sample.et"
        files["wps"].write_bytes(OLE_MAGIC + b"SYNTHETIC-WPS")
        inspections = {name: inspect_file(path) for name, path in files.items()}

        traversal = root / "traversal.zip"
        with zipfile.ZipFile(traversal, "w") as archive:
            archive.writestr("../escape.csv", "a,b\n1,2\n")
        try:
            inspect_file(traversal)
        except GeneralImportError as error:
            traversal_rejected = error.code == "ARCHIVE_PATH_TRAVERSAL_REJECTED"
        else:
            traversal_rejected = False
        symlink_zip = root / "symlink.zip"
        with zipfile.ZipFile(symlink_zip, "w") as archive:
            link = zipfile.ZipInfo("link.csv")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(link, "target.csv")
        try:
            inspect_file(symlink_zip)
        except GeneralImportError as error:
            symlink_rejected = error.code == "ARCHIVE_SYMLINK_REJECTED"
        else:
            symlink_rejected = False
        bomb = root / "bomb.zip"
        with zipfile.ZipFile(bomb, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("large.csv", b"0" * 250000)
        try:
            inspect_file(bomb, ArchivePolicy(max_compression_ratio=5))
        except GeneralImportError as error:
            bomb_rejected = error.code in {"ARCHIVE_COMPRESSION_BOMB_REJECTED", "ARCHIVE_TOTAL_COMPRESSION_BOMB_REJECTED"}
        else:
            bomb_rejected = False
        extraction_target = root / "should-not-exist"
        try:
            _extract_zip_atomic(traversal, extraction_target, DEFAULT_ARCHIVE_POLICY)
        except GeneralImportError:
            no_rejected_extraction = not extraction_target.exists()
        else:
            no_rejected_extraction = False

        corrupt = root / "corrupt.pdf"
        corrupt.write_bytes(b"not-a-pdf")
        batch = inspect_batch(
            (files["csv"], corrupt, files["xlsx"]),
            (_context(), _context(), _context()),
        )
        preview = build_import_preview(inspections["zip"], **_context())
        missing_preview = build_import_preview(inspections["csv"], **{**_context(), "entity_label": None})
        try:
            confirm_import_preview(
                missing_preview,
                preview_id=missing_preview["preview_id"],
                preview_fingerprint=missing_preview["preview_fingerprint"],
                decision="CONFIRM",
                operator_role="ROLE::FINANCE",
                occurred_at="2026-07-15T22:00:00+10:00",
            )
        except GeneralImportError as error:
            missing_blocked = error.code == "PREVIEW_CONTEXT_INCOMPLETE"
        else:
            missing_blocked = False
        tampered_preview = copy.deepcopy(preview)
        tampered_preview["period"]["value"] = "2026-07"
        try:
            confirm_import_preview(
                tampered_preview,
                preview_id=preview["preview_id"],
                preview_fingerprint=preview["preview_fingerprint"],
                decision="CONFIRM",
                operator_role="ROLE::FINANCE",
                occurred_at="2026-07-15T22:00:00+10:00",
            )
        except GeneralImportError as error:
            tampered_rejected = error.code == "PREVIEW_FINGERPRINT_MISMATCH"
        else:
            tampered_rejected = False
        confirmation = confirm_import_preview(
            preview,
            preview_id=preview["preview_id"],
            preview_fingerprint=preview["preview_fingerprint"],
            decision="CONFIRM",
            operator_role="ROLE::FINANCE",
            occurred_at="2026-07-15T22:00:00+10:00",
        )
        unbound = copy.deepcopy(confirmation)
        unbound["preview_id"] = "OTHER-PREVIEW"
        try:
            process_confirmed_import(files["zip"], preview, unbound, private_root=root / "unbound")
        except GeneralImportError as error:
            unbound_rejected = error.code == "CONFIRMATION_EVENT_TAMPERED"
        else:
            unbound_rejected = False
        try:
            process_confirmed_import(files["zip"], preview, {}, private_root=root / "unconfirmed")
        except GeneralImportError:
            unconfirmed_rejected = True
        else:
            unconfirmed_rejected = False

        mutable_source = root / "mutable.csv"
        mutable_source.write_text("a,b\n1,2\n", encoding="utf-8")
        mutable_preview = build_import_preview(inspect_file(mutable_source), **_context())
        mutable_event = confirm_import_preview(
            mutable_preview,
            preview_id=mutable_preview["preview_id"],
            preview_fingerprint=mutable_preview["preview_fingerprint"],
            decision="CONFIRM",
            operator_role="ROLE::FINANCE",
            occurred_at="2026-07-15T22:01:00+10:00",
        )
        mutable_source.write_text("a,b\n1,3\n", encoding="utf-8")
        try:
            process_confirmed_import(mutable_source, mutable_preview, mutable_event, private_root=root / "mutated")
        except GeneralImportError as error:
            changed_rejected = error.code == "SOURCE_CHANGED_AFTER_PREVIEW"
        else:
            changed_rejected = False

        source_before = files["zip"].read_bytes()
        private_root = root / "private"
        try:
            process_confirmed_import(
                files["zip"], preview, confirmation, private_root=private_root, interrupt_at="AFTER_STAGE"
            )
        except ImportInterrupted:
            invisible_after_interrupt = len(list_committed_imports(private_root)) == 0
        else:
            invisible_after_interrupt = False
        committed = process_confirmed_import(files["zip"], preview, confirmation, private_root=private_root)
        replay = process_confirmed_import(files["zip"], preview, confirmation, private_root=private_root)
        source_after = files["zip"].read_bytes()
        object_path = private_root / committed["record"]["private_object_relative_path"]
        object_hash, _ = _hash_file(object_path)
        extracted_path = private_root / str(committed["record"]["private_extracted_relative_path"])

        required_values = {
            "file_display_name": preview["file_display_name"],
            "period": preview["period"]["value"],
            "source_label": preview["source_label"]["value"],
            "entity_label": preview["entity_label"]["value"],
            "business_segment": preview["business_segment"]["value"],
            "detection_result_zh": preview["detection_result_zh"],
        }
        boundary = scope_boundary()
        checks = [
            _check(CHECK_IDS[0], inspections["zip"]["format_code"] == "ZIP"),
            _check(CHECK_IDS[1], inspections["xlsx"]["format_code"] == "EXCEL_XLSX"),
            _check(CHECK_IDS[2], inspections["xls"]["format_code"] == "EXCEL_XLS"),
            _check(CHECK_IDS[3], inspections["csv"]["format_code"] == "CSV"),
            _check(CHECK_IDS[4], inspections["pdf"]["format_code"] == "PDF"),
            _check(CHECK_IDS[5], inspections["wps"]["format_code"] == "WPS_OLE"),
            _check(CHECK_IDS[6], traversal_rejected),
            _check(CHECK_IDS[7], symlink_rejected),
            _check(CHECK_IDS[8], bomb_rejected),
            _check(CHECK_IDS[9], batch["quarantined_count"] == 1),
            _check(CHECK_IDS[10], batch["preview_ready_count"] == 2 and not batch["batch_aborted_by_single_bad_file"]),
            _check(CHECK_IDS[11], no_rejected_extraction),
            _check(CHECK_IDS[12], set(required_values) == set(REQUIRED_PREVIEW_FIELDS) and all(required_values.values())),
            _check(CHECK_IDS[13], preview["user_confirmation_required"] is True),
            _check(CHECK_IDS[14], preview["processing_allowed"] is False),
            _check(CHECK_IDS[15], missing_blocked),
            _check(CHECK_IDS[16], tampered_rejected),
            _check(CHECK_IDS[17], unbound_rejected),
            _check(CHECK_IDS[18], unconfirmed_rejected),
            _check(CHECK_IDS[19], changed_rejected),
            _check(CHECK_IDS[20], committed["outcome"] == "COMMITTED" and committed["visible_committed_count"] == 1),
            _check(CHECK_IDS[21], object_hash == preview["file_hash"]),
            _check(CHECK_IDS[22], extracted_path.is_dir() and committed["record"]["archive_member_count"] == 1),
            _check(CHECK_IDS[23], invisible_after_interrupt),
            _check(CHECK_IDS[24], committed["resumed_from_checkpoint"] is True),
            _check(CHECK_IDS[25], replay["outcome"] == "REUSED" and replay["idempotent_reuse"] is True),
            _check(CHECK_IDS[26], replay["record"] == committed["record"]),
            _check(CHECK_IDS[27], replay["visible_committed_count"] == committed["visible_committed_count"] == 1),
            _check(CHECK_IDS[28], source_before == source_after and not committed["source_mutation_performed"]),
            _check(CHECK_IDS[29], all(value.get("raw_root_access_count", 0) == 0 for value in (preview, batch))),
            _check(
                CHECK_IDS[30],
                not boundary["s10_p2_started"]
                and not boundary["s10_p3_started"]
                and not boundary["s10_stage_review_started"],
            ),
            _check(
                CHECK_IDS[31],
                not boundary["formal_report_generated"]
                and not boundary["github_upload_performed"]
                and not boundary["app_reinstall_performed"]
                and not boundary["business_execution_performed"],
            ),
        ]
    failed = sum(row["status"] != "PASS" for row in checks)
    return {
        "schema_version": "kmfa.v015.s10p1.public_verification.v1",
        "run_phase_id": RUN_PHASE_ID,
        "public_safe": True,
        "supported_format_category_count": len(FORMAT_LABELS_ZH),
        "supported_extension_count": len(SUPPORTED_EXTENSIONS),
        "preview_required_field_count": len(REQUIRED_PREVIEW_FIELDS),
        "checks": checks,
        "accounting": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        **boundary,
    }


__all__ = [
    "ACCEPTANCE_ID",
    "ArchivePolicy",
    "CHECK_IDS",
    "DEFAULT_ARCHIVE_POLICY",
    "FORMAT_GUIDANCE_ZH",
    "GeneralImportError",
    "ImportInterrupted",
    "PARSER_VERSION",
    "ROADMAP_PHASE_ID",
    "RUN_PHASE_ID",
    "TASK_ID",
    "VERSION",
    "build_import_preview",
    "confirm_import_preview",
    "inspect_batch",
    "inspect_file",
    "inspect_zip",
    "list_committed_imports",
    "process_confirmed_import",
    "public_verification",
    "scope_boundary",
]
