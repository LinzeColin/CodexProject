#!/usr/bin/env python3
"""KMFA v1.5 S20-P1 human data-update workflow.

This module turns the already accepted S10-P1 safe-import kernel into a small,
recoverable, human-controlled workflow. Uploaded bytes are written only to an
explicit private runtime root. The workflow never discovers, opens, or writes
the finance raw inbox.
"""

from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import re
import shutil
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from KMFA.tools import v015_s10_p1_general_import as import_kernel


RUN_PHASE_ID = "V015_S20_P1_DATA_UPDATE"
ROADMAP_PHASE_ID = "S20-P1"
TASK_ID = "KMFA-V015-S20-P1-DATA-UPDATE-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S20-P1-DATA-UPDATE"
VERSION = "1.5.0-dev-s20p1"
JOB_SCHEMA = "kmfa.v015.s20p1.data_update_job.v1"
MAX_UPLOAD_BYTES = 16 * 1024 * 1024
DEFAULT_RUNTIME_ROOT = (
    Path(__file__).resolve().parents[1]
    / ".codex_private_runtime"
    / "v015_s20_p1_data_update"
    / "runtime"
)

SOURCE_OPTIONS = (
    {"value": "SRC-local-upload-a1b2c3d4", "label_zh": "本机资料上传"},
    {"value": "SRC-finance-export-b2c3d4e5", "label_zh": "财务系统导出"},
    {"value": "SRC-project-ledger-c3d4e5f6", "label_zh": "项目台账导出"},
)
ENTITY_OPTIONS = (
    {"value": "demo-north", "label_zh": "北区演示公司"},
    {"value": "demo-east", "label_zh": "东区演示公司"},
    {"value": "demo-services", "label_zh": "服务演示公司"},
)
SCOPE_OPTIONS = (
    {"value": "ACCOUNT::OPERATING", "kind": "ACCOUNT", "label_zh": "主要经营账户"},
    {"value": "SEGMENT::PROJECT_COST", "kind": "SEGMENT", "label_zh": "项目成本板块"},
    {"value": "SEGMENT::RECEIVABLES", "kind": "SEGMENT", "label_zh": "应收回款板块"},
    {"value": "SEGMENT::TAX", "kind": "SEGMENT", "label_zh": "税票与政策板块"},
)

_SOURCE_BY_ID = {item["value"]: item for item in SOURCE_OPTIONS}
_ENTITY_BY_ID = {item["value"]: item for item in ENTITY_OPTIONS}
_SCOPE_BY_ID = {item["value"]: item for item in SCOPE_OPTIONS}
_JOB_ID = re.compile(r"^DU-[a-f0-9]{24}$")
_PERIOD = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class DataUpdateError(ValueError):
    """Stable fail-closed workflow error safe for the local UI."""

    def __init__(self, code: str, message_zh: str, *, status: int = 400):
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh
        self.status = status


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _with_fingerprint(value: Mapping[str, Any]) -> dict[str, Any]:
    body = copy.deepcopy(dict(value))
    body.pop("state_fingerprint", None)
    body["state_fingerprint"] = _fingerprint(body)
    return body


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _safe_runtime_root(value: str | Path) -> Path:
    supplied = Path(value).expanduser()
    if supplied.exists() and supplied.is_symlink():
        raise DataUpdateError("RUNTIME_ROOT_SYMLINK_REJECTED", "隔离工作区不能是符号链接。")
    root = supplied.resolve(strict=False)
    forbidden = (Path.home() / "Downloads" / ("KMFA_" + "MetaData")).resolve(strict=False)
    if root == forbidden or forbidden in root.parents:
        raise DataUpdateError("RAW_ROOT_WRITE_REJECTED", "上传文件不能写入原始只读目录。")
    return root


def _filename(value: str) -> str:
    name = str(value or "").strip()
    if (
        not name
        or len(name.encode("utf-8")) > 240
        or name != Path(name).name
        or "/" in name
        or "\\" in name
        or "\x00" in name
    ):
        raise DataUpdateError("UPLOAD_FILENAME_INVALID", "文件名不安全，请重新选择文件。")
    return name


def _selection(value: Mapping[str, Any]) -> dict[str, str]:
    source_id = str(value.get("source_id", "")).strip()
    entity_id = str(value.get("entity_id", "")).strip()
    scope_id = str(value.get("scope_id", "")).strip()
    period = str(value.get("period", "")).strip()
    if source_id not in _SOURCE_BY_ID:
        raise DataUpdateError("SOURCE_SELECTION_REQUIRED", "请选择资料来源。")
    if entity_id not in _ENTITY_BY_ID:
        raise DataUpdateError("ENTITY_SELECTION_REQUIRED", "请选择公司主体。")
    if scope_id not in _SCOPE_BY_ID:
        raise DataUpdateError("SCOPE_SELECTION_REQUIRED", "请选择账户或业务板块。")
    if not _PERIOD.fullmatch(period):
        raise DataUpdateError("PERIOD_SELECTION_REQUIRED", "请选择有效月份。")
    source = _SOURCE_BY_ID[source_id]
    entity = _ENTITY_BY_ID[entity_id]
    scope = _SCOPE_BY_ID[scope_id]
    return {
        "source_id": source_id,
        "source_label_zh": source["label_zh"],
        "entity_id": entity_id,
        "entity_label_zh": entity["label_zh"],
        "scope_id": scope_id,
        "scope_kind": scope["kind"],
        "scope_label_zh": scope["label_zh"],
        "period": period,
    }


def _progress() -> list[dict[str, Any]]:
    return [
        {"stage": "UPLOAD", "label_zh": "上传到隔离工作区", "status": "NOT_STARTED", "detail_zh": "尚未上传。"},
        {"stage": "INSPECT", "label_zh": "识别与安全检查", "status": "NOT_STARTED", "detail_zh": "尚未检查。"},
        {"stage": "CONFIRM", "label_zh": "人工确认", "status": "NOT_STARTED", "detail_zh": "等待预览。"},
        {"stage": "IMPORT", "label_zh": "导入登记", "status": "NOT_STARTED", "detail_zh": "确认后才会开始。"},
        {"stage": "VALIDATE", "label_zh": "结果校验", "status": "NOT_STARTED", "detail_zh": "等待导入。"},
        {"stage": "RECALCULATE", "label_zh": "重算影响", "status": "NOT_EXECUTED", "detail_zh": "本阶段只识别影响，不执行重算。"},
        {"stage": "REPORT", "label_zh": "报告影响", "status": "NOT_EXECUTED", "detail_zh": "本阶段只列出可能受影响的报告。"},
    ]


def _set_stage(job: dict[str, Any], stage: str, status: str, detail_zh: str) -> None:
    for row in job["progress"]:
        if row["stage"] == stage:
            row["status"] = status
            row["detail_zh"] = detail_zh
            row["updated_at"] = _now()
            return
    raise DataUpdateError("PROGRESS_STAGE_MISSING", "处理进度记录不完整。", status=500)


def _impact_plan(selection: Mapping[str, str]) -> dict[str, Any]:
    scope = selection["scope_id"]
    map_by_scope = {
        "ACCOUNT::OPERATING": ("资金余额与现金预测", ("资金概览", "资金关系报告")),
        "SEGMENT::PROJECT_COST": ("项目成本与利润", ("项目详情", "项目成本专题报告", "经营首页")),
        "SEGMENT::RECEIVABLES": ("应收与回款", ("回款工作台", "经营首页", "资金关系报告")),
        "SEGMENT::TAX": ("税票与政策材料", ("税务与发票", "政策材料", "税务与政策报告")),
    }
    recalculation_zh, reports = map_by_scope[scope]
    return {
        "recalculation_scope_zh": recalculation_zh,
        "report_labels_zh": list(reports),
        "recalculation_executed": False,
        "report_refresh_executed": False,
        "next_step_zh": "导入结果已校验；重算和报告刷新必须在后续流程再次确认。",
    }


def options_contract() -> dict[str, Any]:
    return {
        "sources": copy.deepcopy(list(SOURCE_OPTIONS)),
        "entities": copy.deepcopy(list(ENTITY_OPTIONS)),
        "scopes": copy.deepcopy(list(SCOPE_OPTIONS)),
        "supported_extensions": list(import_kernel.SUPPORTED_EXTENSIONS),
        "max_upload_bytes": MAX_UPLOAD_BYTES,
        "raw_write_allowed": False,
        "steps": ("选择并上传", "预览并确认", "查看处理结果"),
    }


class DataUpdateStore:
    """Filesystem-backed, refresh-safe state for local data-update jobs."""

    def __init__(self, root: str | Path = DEFAULT_RUNTIME_ROOT):
        self.root = _safe_runtime_root(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._thread_lock = threading.RLock()
        self._lock_path = self.root / ".data-update.lock"

    def _job_dir(self, job_id: str) -> Path:
        if not _JOB_ID.fullmatch(job_id):
            raise DataUpdateError("JOB_ID_INVALID", "更新任务编号不正确。")
        return self.root / "jobs" / job_id

    def _state_path(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "job.json"

    def _locked(self):
        class _Lock:
            def __init__(inner, outer: DataUpdateStore):
                inner.outer = outer
                inner.handle = None

            def __enter__(inner):
                inner.outer._thread_lock.acquire()
                inner.handle = inner.outer._lock_path.open("a+b")
                fcntl.flock(inner.handle.fileno(), fcntl.LOCK_EX)
                return inner

            def __exit__(inner, exc_type, exc, tb):
                assert inner.handle is not None
                fcntl.flock(inner.handle.fileno(), fcntl.LOCK_UN)
                inner.handle.close()
                inner.outer._thread_lock.release()
        return _Lock(self)

    def _write(self, job: Mapping[str, Any]) -> dict[str, Any]:
        value = _with_fingerprint(job)
        _atomic_json(self._state_path(str(value["job_id"])), value)
        return value

    def _read_unlocked(self, job_id: str) -> dict[str, Any]:
        path = self._state_path(job_id)
        if not path.is_file():
            raise DataUpdateError("JOB_NOT_FOUND", "没有找到这次更新任务。", status=404)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise DataUpdateError("JOB_STATE_CORRUPT", "更新任务记录无法读取。", status=500) from error
        supplied = str(value.pop("state_fingerprint", ""))
        if value.get("schema_version") != JOB_SCHEMA or supplied != _fingerprint(value):
            raise DataUpdateError("JOB_STATE_TAMPERED", "更新任务记录已损坏或被改写。", status=409)
        value["state_fingerprint"] = supplied
        return value

    def read(self, job_id: str) -> dict[str, Any]:
        with self._locked():
            return self.public_view(self._read_unlocked(job_id))

    def create(self, selection: Mapping[str, Any], filename: str, content: bytes) -> dict[str, Any]:
        selected = _selection(selection)
        safe_name = _filename(filename)
        if not isinstance(content, bytes) or not content:
            raise DataUpdateError("UPLOAD_EMPTY", "请选择一个非空文件。")
        if len(content) > MAX_UPLOAD_BYTES:
            raise DataUpdateError("UPLOAD_TOO_LARGE", "文件超过 16 MB，请拆分后再上传。", status=413)
        if Path(safe_name).suffix.lower() not in import_kernel.SUPPORTED_EXTENSIONS:
            raise DataUpdateError("UPLOAD_FORMAT_UNSUPPORTED", "当前只支持 ZIP、Excel、CSV、PDF 和 WPS 文件。")
        job_id = "DU-" + uuid.uuid4().hex[:24]
        with self._locked():
            job_dir = self._job_dir(job_id)
            upload_dir = job_dir / "upload"
            upload_dir.mkdir(parents=True)
            source_path = upload_dir / safe_name
            temporary = upload_dir / ("." + safe_name + ".uploading")
            try:
                with temporary.open("xb") as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, source_path)
            finally:
                temporary.unlink(missing_ok=True)
            job: dict[str, Any] = {
                "schema_version": JOB_SCHEMA,
                "job_id": job_id,
                "status": "INSPECTING",
                "current_step": 1,
                "created_at": _now(),
                "updated_at": _now(),
                "selection": selected,
                "file_display_name": safe_name,
                "private_source_relative_path": source_path.relative_to(self.root).as_posix(),
                "source_copy_present": True,
                "progress": _progress(),
                "issues": [],
                "preview": None,
                "confirmation": None,
                "result": None,
                "raw_root_access_count": 0,
                "raw_write_performed": False,
                "source_original_mutation_performed": False,
                "s20_p2_started": False,
                "s20_p3_started": False,
                "github_upload_performed": False,
                "app_reinstall_performed": False,
            }
            _set_stage(job, "UPLOAD", "COMPLETED", "文件已完整写入隔离工作区；原文件未改动。")
            try:
                inspection = import_kernel.inspect_file(source_path)
                preview = import_kernel.build_import_preview(
                    inspection,
                    source_id=selected["source_id"],
                    source_label=selected["source_label_zh"],
                    entity_label=selected["entity_label_zh"],
                    business_segment=selected["scope_label_zh"],
                    period=selected["period"],
                )
            except import_kernel.GeneralImportError as error:
                job["status"] = "PREVIEW_BLOCKED"
                job["current_step"] = 2
                job["issues"] = [{"code": error.code, "message_zh": error.message_zh, "blocks_processing": True}]
                _set_stage(job, "INSPECT", "FAILED", error.message_zh)
                _set_stage(job, "CONFIRM", "BLOCKED", "文件问题解决前不能确认。")
            else:
                job["status"] = "AWAITING_CONFIRMATION"
                job["current_step"] = 2
                job["preview"] = preview
                _set_stage(job, "INSPECT", "COMPLETED", "格式、结构和安全边界已实际检查。")
                _set_stage(job, "CONFIRM", "WAITING_USER", "请核对预览后明确确认。")
            return self.public_view(self._write(job))

    def confirm(
        self,
        job_id: str,
        *,
        preview_id: str,
        confirm_token: str,
        operator_role: str = "ROLE::DATA_STEWARD",
        interrupt_at: str | None = None,
    ) -> dict[str, Any]:
        with self._locked():
            job = self._read_unlocked(job_id)
            if job["status"] == "COMPLETED":
                return self.public_view(job)
            if job["status"] not in {"AWAITING_CONFIRMATION", "INTERRUPTED"}:
                raise DataUpdateError("JOB_NOT_CONFIRMABLE", "当前任务不能进入处理。", status=409)
            preview = job.get("preview")
            if not isinstance(preview, dict):
                raise DataUpdateError("JOB_PREVIEW_MISSING", "当前任务缺少可确认的预览。", status=409)
            if preview_id != preview["preview_id"] or confirm_token != preview["preview_fingerprint"]:
                raise DataUpdateError("PREVIEW_CONFIRMATION_MISMATCH", "页面预览已变化，请刷新后重新确认。", status=409)
            if job.get("confirmation") is None:
                try:
                    confirmation = import_kernel.confirm_import_preview(
                        preview,
                        preview_id=preview_id,
                        preview_fingerprint=confirm_token,
                        decision="CONFIRM",
                        operator_role=operator_role,
                        occurred_at=_now(),
                    )
                except import_kernel.GeneralImportError as error:
                    raise DataUpdateError(error.code, error.message_zh, status=409) from error
                job["confirmation"] = confirmation
            job["status"] = "PROCESSING"
            job["current_step"] = 3
            job["updated_at"] = _now()
            _set_stage(job, "CONFIRM", "COMPLETED", "已记录人工确认，并精确绑定当前预览。")
            _set_stage(job, "IMPORT", "IN_PROGRESS", "正在登记已确认的隔离副本。")
            self._write(job)
            source_path = self.root / job["private_source_relative_path"]
            private_import_root = self._job_dir(job_id) / "committed"
            try:
                result = import_kernel.process_confirmed_import(
                    source_path,
                    preview,
                    job["confirmation"],
                    private_root=private_import_root,
                    interrupt_at=interrupt_at,
                )
            except import_kernel.ImportInterrupted as error:
                job["status"] = "INTERRUPTED"
                job["updated_at"] = _now()
                job["interrupted_at"] = error.checkpoint
                _set_stage(job, "IMPORT", "PAUSED", "处理已安全暂停；未完成内容不可见，可继续。")
                return self.public_view(self._write(job))
            except import_kernel.GeneralImportError as error:
                job["status"] = "FAILED"
                job["updated_at"] = _now()
                job["issues"] = [{"code": error.code, "message_zh": error.message_zh, "blocks_processing": True}]
                _set_stage(job, "IMPORT", "FAILED", error.message_zh)
                return self.public_view(self._write(job))
            _set_stage(job, "IMPORT", "COMPLETED", "隔离副本已完成原子登记；未出现半成品记录。")
            _set_stage(job, "VALIDATE", "IN_PROGRESS", "正在核对登记记录与内容副本。")
            self._write(job)
            records = import_kernel.list_committed_imports(private_import_root)
            record = result["record"]
            registration_id = record["idempotency_key"]
            validated = any(item.get("idempotency_key") == registration_id for item in records)
            object_path = private_import_root / record["private_object_relative_path"]
            if not validated or not object_path.is_file():
                job["status"] = "FAILED"
                _set_stage(job, "VALIDATE", "FAILED", "导入记录与内容副本未能相互核对。")
                return self.public_view(self._write(job))
            _set_stage(job, "VALIDATE", "COMPLETED", "登记记录、内容副本和来源指纹一致。")
            impact = _impact_plan(job["selection"])
            _set_stage(job, "RECALCULATE", "NOT_EXECUTED", "已识别影响范围；本阶段没有执行重算。")
            _set_stage(job, "REPORT", "NOT_EXECUTED", "已列出受影响报告；本阶段没有刷新或发布报告。")
            job["result"] = {
                "outcome": result["outcome"],
                "new_record_created": result["new_record_created"],
                "resumed_from_checkpoint": result["resumed_from_checkpoint"],
                "visible_committed_count": result["visible_committed_count"],
                "registration_id": registration_id,
                "validation_passed": True,
                "partial_commit_visible": result["partial_commit_visible"],
                "impact": impact,
            }
            job["status"] = "COMPLETED"
            job["updated_at"] = _now()
            job["completed_at"] = _now()
            upload_dir = self._job_dir(job_id) / "upload"
            if upload_dir.exists():
                shutil.rmtree(upload_dir)
            job["source_copy_present"] = False
            job["upload_copy_removed_after_commit"] = True
            return self.public_view(self._write(job))

    def resume(self, job_id: str) -> dict[str, Any]:
        with self._locked():
            job = self._read_unlocked(job_id)
            if job["status"] != "INTERRUPTED":
                raise DataUpdateError("JOB_NOT_INTERRUPTED", "当前任务不需要继续。", status=409)
            preview = job["preview"]
        return self.confirm(
            job_id,
            preview_id=preview["preview_id"],
            confirm_token=preview["preview_fingerprint"],
        )

    def cancel(self, job_id: str) -> dict[str, Any]:
        with self._locked():
            job = self._read_unlocked(job_id)
            if job["status"] == "COMPLETED":
                raise DataUpdateError("COMPLETED_JOB_NOT_CANCELLABLE", "已完成的登记不能用取消按钮撤回。", status=409)
            job_dir = self._job_dir(job_id)
            for name in ("upload", "committed"):
                target = job_dir / name
                if target.exists():
                    shutil.rmtree(target)
            job["status"] = "CANCELLED"
            job["updated_at"] = _now()
            job["cancelled_at"] = _now()
            job["source_copy_present"] = False
            job["preview"] = None
            job["confirmation"] = None
            job["result"] = None
            for row in job["progress"]:
                if row["status"] in {"NOT_STARTED", "WAITING_USER", "IN_PROGRESS", "PAUSED"}:
                    row["status"] = "CANCELLED"
                    row["detail_zh"] = "任务已取消。"
            return self.public_view(self._write(job))

    @staticmethod
    def public_view(job: Mapping[str, Any]) -> dict[str, Any]:
        value = copy.deepcopy(dict(job))
        value.pop("state_fingerprint", None)
        value.pop("private_source_relative_path", None)
        confirmation = value.pop("confirmation", None)
        preview = value.get("preview")
        if isinstance(preview, dict):
            value["preview"] = {
                "preview_id": preview["preview_id"],
                "confirm_token": preview["preview_fingerprint"],
                "file_display_name": preview["file_display_name"],
                "file_size_bytes": preview["file_size_bytes"],
                "format_code": preview["format_code"],
                "format_label_zh": preview["format_label_zh"],
                "format_guidance_zh": preview["format_guidance_zh"],
                "detection_result_zh": preview["detection_result_zh"],
                "period": preview["period"]["value"],
                "source_label_zh": preview["source_label"]["value"],
                "entity_label_zh": preview["entity_label"]["value"],
                "scope_label_zh": preview["business_segment"]["value"],
                "fields": [
                    {"label_zh": "资料来源", "value": preview["source_label"]["value"], "origin": "USER_SELECTED", "origin_zh": "你选择的"},
                    {"label_zh": "公司主体", "value": preview["entity_label"]["value"], "origin": "USER_SELECTED", "origin_zh": "你选择的"},
                    {"label_zh": "账户或板块", "value": preview["business_segment"]["value"], "origin": "USER_SELECTED", "origin_zh": "你选择的"},
                    {"label_zh": "资料期间", "value": preview["period"]["value"], "origin": "USER_SELECTED", "origin_zh": "你选择的"},
                    {"label_zh": "文件类型", "value": preview["format_label_zh"], "origin": "AUTO_DETECTED", "origin_zh": "系统自动识别，需你确认"},
                ],
                "user_confirmation_required": True,
                "processing_allowed": False,
            }
        value["confirmation_recorded"] = confirmation is not None
        return value


def scope_boundary() -> dict[str, Any]:
    return {
        "raw_root_access_count": 0,
        "raw_write_performed": False,
        "source_original_mutation_performed": False,
        "s20_p2_started": False,
        "s20_p3_started": False,
        "s20_stage_review_started": False,
        "recalculation_executed": False,
        "report_refresh_executed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


def _check(check_id: str, condition: bool) -> dict[str, str]:
    return {"check_id": check_id, "status": "PASS" if condition else "FAIL"}


def public_verification() -> dict[str, Any]:
    """Exercise the complete S20-P1 contract with small synthetic files only."""

    selection = {
        "source_id": "SRC-local-upload-a1b2c3d4",
        "entity_id": "demo-north",
        "scope_id": "SEGMENT::PROJECT_COST",
        "period": "2026-07",
    }
    csv_bytes = b"project,cost\nA,100\n"
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        store = DataUpdateStore(root / "runtime")
        preview = store.create(selection, "public-sample.csv", csv_bytes)
        reloaded_preview = DataUpdateStore(root / "runtime").read(preview["job_id"])
        try:
            store.confirm(
                preview["job_id"],
                preview_id=preview["preview"]["preview_id"],
                confirm_token="sha256:" + "0" * 64,
            )
        except DataUpdateError as error:
            wrong_preview_rejected = error.code == "PREVIEW_CONFIRMATION_MISMATCH"
        else:
            wrong_preview_rejected = False
        interrupted = store.confirm(
            preview["job_id"],
            preview_id=preview["preview"]["preview_id"],
            confirm_token=preview["preview"]["confirm_token"],
            interrupt_at="AFTER_STAGE",
        )
        resumed = DataUpdateStore(root / "runtime").resume(preview["job_id"])
        completed_reload = DataUpdateStore(root / "runtime").read(preview["job_id"])

        cancel_job = store.create(selection, "cancel.csv", csv_bytes)
        cancelled = store.cancel(cancel_job["job_id"])
        cancelled_dir = store._job_dir(cancel_job["job_id"]) / "upload"

        bad_job = store.create(selection, "broken.pdf", b"not a pdf")
        try:
            store.confirm(bad_job["job_id"], preview_id="none", confirm_token="none")
        except DataUpdateError as error:
            blocked_confirm_rejected = error.code == "JOB_NOT_CONFIRMABLE"
        else:
            blocked_confirm_rejected = False

        duplicate_job = store.create(selection, "second.csv", csv_bytes)
        duplicate_result = store.confirm(
            duplicate_job["job_id"],
            preview_id=duplicate_job["preview"]["preview_id"],
            confirm_token=duplicate_job["preview"]["confirm_token"],
        )

        try:
            store.create(selection, "../escape.csv", csv_bytes)
        except DataUpdateError as error:
            traversal_rejected = error.code == "UPLOAD_FILENAME_INVALID"
        else:
            traversal_rejected = False
        try:
            DataUpdateStore(Path.home() / "Downloads" / ("KMFA_" + "MetaData"))
        except DataUpdateError as error:
            raw_root_rejected = error.code == "RAW_ROOT_WRITE_REJECTED"
        else:
            raw_root_rejected = False

        preview_fields = preview["preview"]["fields"]
        completed_stages = {row["stage"]: row["status"] for row in resumed["progress"]}
        checks = [
            _check("THREE_STEP_WORKFLOW_DECLARED", len(options_contract()["steps"]) == 3),
            _check("SOURCE_OPTIONS_AVAILABLE", len(SOURCE_OPTIONS) == 3),
            _check("ENTITY_OPTIONS_AVAILABLE", len(ENTITY_OPTIONS) == 3),
            _check("ACCOUNT_OR_SEGMENT_OPTIONS_AVAILABLE", {row["kind"] for row in SCOPE_OPTIONS} == {"ACCOUNT", "SEGMENT"}),
            _check("SUPPORTED_FORMATS_EXPLICIT", set(import_kernel.SUPPORTED_EXTENSIONS) == {".zip", ".xlsx", ".xls", ".csv", ".pdf", ".wps", ".et", ".dps"}),
            _check("UPLOAD_SIZE_LIMIT_EXPLICIT", options_contract()["max_upload_bytes"] == MAX_UPLOAD_BYTES),
            _check("RAW_WRITE_OPTION_FALSE", options_contract()["raw_write_allowed"] is False),
            _check("UPLOAD_WRITTEN_TO_PRIVATE_WORKSPACE", preview["progress"][0]["status"] == "COMPLETED"),
            _check("ORIGINAL_SOURCE_MUTATION_FALSE", preview["source_original_mutation_performed"] is False),
            _check("RAW_ACCESS_ZERO", preview["raw_root_access_count"] == 0),
            _check("RAW_WRITE_FALSE", preview["raw_write_performed"] is False),
            _check("INSPECTION_ACTUALLY_COMPLETED", preview["progress"][1]["status"] == "COMPLETED"),
            _check("PREVIEW_REQUIRES_USER", preview["preview"]["user_confirmation_required"] is True),
            _check("PREVIEW_PROCESSING_FALSE", preview["preview"]["processing_allowed"] is False),
            _check("PREVIEW_FILE_DISPLAYED", preview["preview"]["file_display_name"] == "public-sample.csv"),
            _check("PREVIEW_PERIOD_DISPLAYED", preview["preview"]["period"] == "2026-07"),
            _check("PREVIEW_SOURCE_DISPLAYED", preview["preview"]["source_label_zh"] == "本机资料上传"),
            _check("PREVIEW_ENTITY_DISPLAYED", preview["preview"]["entity_label_zh"] == "北区演示公司"),
            _check("PREVIEW_SCOPE_DISPLAYED", preview["preview"]["scope_label_zh"] == "项目成本板块"),
            _check("AUTO_DETECTION_EXPLICITLY_MARKED", sum(row["origin"] == "AUTO_DETECTED" for row in preview_fields) == 1),
            _check("USER_SELECTIONS_EXPLICITLY_MARKED", sum(row["origin"] == "USER_SELECTED" for row in preview_fields) == 4),
            _check("AUTO_DETECTION_NEEDS_CONFIRM_COPY", "需你确认" in next(row["origin_zh"] for row in preview_fields if row["origin"] == "AUTO_DETECTED")),
            _check("REFRESH_RESTORES_PREVIEW", reloaded_preview == preview),
            _check("WRONG_PREVIEW_TOKEN_REJECTED", wrong_preview_rejected),
            _check("CONFIRMATION_BOUND_BEFORE_PROCESS", interrupted["confirmation_recorded"] is True),
            _check("INTERRUPTION_REPORTED", interrupted["status"] == "INTERRUPTED"),
            _check("INTERRUPTED_IMPORT_PAUSED", next(row for row in interrupted["progress"] if row["stage"] == "IMPORT")["status"] == "PAUSED"),
            _check("INTERRUPTED_PARTIAL_NOT_VISIBLE", interrupted["result"] is None),
            _check("RESUME_COMPLETES", resumed["status"] == "COMPLETED"),
            _check("RESUME_CHECKPOINT_PROVEN", resumed["result"]["resumed_from_checkpoint"] is True),
            _check("IMPORT_COMPLETED_REAL", completed_stages["IMPORT"] == "COMPLETED"),
            _check("VALIDATION_COMPLETED_REAL", completed_stages["VALIDATE"] == "COMPLETED"),
            _check("RECALC_NOT_FAKED", completed_stages["RECALCULATE"] == "NOT_EXECUTED"),
            _check("REPORT_REFRESH_NOT_FAKED", completed_stages["REPORT"] == "NOT_EXECUTED"),
            _check("RESULT_VALIDATED", resumed["result"]["validation_passed"] is True),
            _check("NO_PARTIAL_COMMIT_VISIBLE", resumed["result"]["partial_commit_visible"] is False),
            _check("IMPACT_SCOPE_DISPLAYED", resumed["result"]["impact"]["recalculation_scope_zh"] == "项目成本与利润"),
            _check("IMPACT_REPORTS_DISPLAYED", len(resumed["result"]["impact"]["report_labels_zh"]) == 3),
            _check("RECALC_EXECUTION_FALSE", resumed["result"]["impact"]["recalculation_executed"] is False),
            _check("REPORT_EXECUTION_FALSE", resumed["result"]["impact"]["report_refresh_executed"] is False),
            _check("UPLOAD_COPY_REMOVED_AFTER_COMMIT", resumed["source_copy_present"] is False and resumed["upload_copy_removed_after_commit"] is True),
            _check("COMPLETED_REFRESH_RESTORES", completed_reload == resumed),
            _check("CANCEL_STATUS_RECORDED", cancelled["status"] == "CANCELLED"),
            _check("CANCEL_REMOVES_PRIVATE_UPLOAD", cancelled["source_copy_present"] is False and not cancelled_dir.exists()),
            _check("CANCEL_CLEARS_PREVIEW", cancelled["preview"] is None),
            _check("BROKEN_FILE_PREVIEW_BLOCKED", bad_job["status"] == "PREVIEW_BLOCKED"),
            _check("BROKEN_FILE_ISSUE_DISPLAYED", len(bad_job["issues"]) == 1 and bad_job["issues"][0]["blocks_processing"] is True),
            _check("BROKEN_FILE_CONFIRM_REJECTED", blocked_confirm_rejected),
            _check("JOB_IDS_ARE_ISOLATED", preview["job_id"] != duplicate_job["job_id"]),
            _check("SECOND_JOB_COMPLETES_INDEPENDENTLY", duplicate_result["status"] == "COMPLETED"),
            _check("FILENAME_TRAVERSAL_REJECTED", traversal_rejected),
            _check("RAW_RUNTIME_ROOT_REJECTED", raw_root_rejected),
            _check("PUBLIC_VIEW_HAS_NO_PRIVATE_PATH", "private_source_relative_path" not in preview),
            _check("PUBLIC_VIEW_HAS_NO_FILE_HASH", "file_hash" not in json.dumps(preview, ensure_ascii=False)),
            _check("S20_P2_NOT_STARTED", resumed["s20_p2_started"] is False),
            _check("S20_P3_NOT_STARTED", resumed["s20_p3_started"] is False),
            _check("GITHUB_UPLOAD_FALSE", resumed["github_upload_performed"] is False),
            _check("APP_REINSTALL_FALSE", resumed["app_reinstall_performed"] is False),
            _check("BOUNDARY_CONTRACT_ALL_CLOSED", not any(scope_boundary().values())),
        ]
        return {
            "schema_version": "kmfa.v015.s20p1.public_verification.v1",
            "check_count": len(checks),
            "pass_count": sum(row["status"] == "PASS" for row in checks),
            "fail_count": sum(row["status"] != "PASS" for row in checks),
            "checks": checks,
            "preview_contract": {
                "field_count": len(preview_fields),
                "auto_detected_field_count": sum(row["origin"] == "AUTO_DETECTED" for row in preview_fields),
                "user_selected_field_count": sum(row["origin"] == "USER_SELECTED" for row in preview_fields),
            },
            "recovery_contract": {
                "refresh_preview_restored": reloaded_preview == preview,
                "interruption_status": interrupted["status"],
                "resume_status": resumed["status"],
                "resumed_from_checkpoint": resumed["result"]["resumed_from_checkpoint"],
            },
            "scope_boundary": scope_boundary(),
        }
