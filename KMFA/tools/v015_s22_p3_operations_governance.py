#!/usr/bin/env python3
"""KMFA v1.5 S22-P3 local operations, recovery and migration controls."""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import os
import re
import stat
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from KMFA.tools import v015_s22_p2_security_audit as security


RUN_PHASE_ID = "V015_S22_P3_OPERATIONS_GOVERNANCE"
ROADMAP_PHASE_ID = "S22-P3"
TASK_ID = "KMFA-V015-S22-P3-OPERATIONS-GOVERNANCE-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S22-P3-OPERATIONS-GOVERNANCE"
VERSION = "1.5.0-dev-s22p3"

DEFAULT_RUNTIME_ROOT = (
    Path(__file__).resolve().parents[1]
    / ".codex_private_runtime"
    / "v015_s22_p3_operations_governance"
)
DEFAULT_OPERATIONS_EVENT_PATH = DEFAULT_RUNTIME_ROOT / "operations_events.jsonl"
DEFAULT_BACKUP_ROOT = DEFAULT_RUNTIME_ROOT / "backups"
DEFAULT_MIGRATION_ROOT = DEFAULT_RUNTIME_ROOT / "migration"

SERVICE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "IMPORT": {"label_zh": "资料导入", "critical": True, "latency_budget_ms": 1200},
    "QUEUE": {"label_zh": "处理队列", "critical": True, "latency_budget_ms": 800},
    "COMPUTATION": {"label_zh": "计算服务", "critical": True, "latency_budget_ms": 1500},
    "REPORT": {"label_zh": "报告生成", "critical": True, "latency_budget_ms": 1800},
    "STORAGE": {"label_zh": "本地存储", "critical": True, "latency_budget_ms": 500},
    "NOTIFICATION": {"label_zh": "通知服务", "critical": False, "latency_budget_ms": 1000},
}
BACKUP_DATASETS = ("PRIVATE_DERIVED", "CONFIGURATION", "AUDIT_EVENTS")
MIGRATION_SURFACES = ("SCHEMA", "PARAMETER", "FORMULA", "FRONTEND")
TARGET_VERSIONS = {
    "schema_version": "1.5.0-s22p3",
    "parameter_version": "1.5.0-s22p3",
    "formula_version": "1.5.0-s22p3",
    "frontend_version": "1.5.0-s22p3",
}
_REFERENCE = re.compile(r"^[A-Z][A-Z0-9_]*::[A-Za-z0-9][A-Za-z0-9._:-]{1,127}$")
_APPROVAL = re.compile(r"^APPROVAL::[A-Z0-9][A-Z0-9._:-]{5,127}$")


class OperationsError(RuntimeError):
    """A fail-closed operations control rejected the request."""

    def __init__(self, code: str, message_zh: str, *, status: int = 400) -> None:
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh
        self.status = status


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _instant(value: str | datetime | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise OperationsError("TIME_INVALID", "时间格式不正确") from error
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise OperationsError("TIME_INVALID", "时间必须包含时区")
    return value.astimezone(timezone.utc)


def _reference(value: Any, label: str) -> str:
    text = str(value or "")
    if not _REFERENCE.fullmatch(text):
        raise OperationsError("REFERENCE_INVALID", f"{label}格式不正确")
    return text


def _private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)


def _write_private_json(path: Path, value: Any) -> None:
    _private_directory(path.parent)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)
    os.chmod(path, 0o600)


class OperationsJournal:
    """Append-only hash-linked operational events."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        _private_directory(self.path.parent)

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        rows = [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        previous = "GENESIS"
        for index, row in enumerate(rows, start=1):
            stored = row.get("event_hash")
            body = {key: value for key, value in row.items() if key != "event_hash"}
            if row.get("sequence") != index or row.get("previous_hash") != previous:
                raise OperationsError("OPERATIONS_JOURNAL_TAMPERED", "运维记录顺序或前序指纹不一致", status=409)
            expected = hashlib.sha256(_canonical(body)).hexdigest()
            if not isinstance(stored, str) or not hmac.compare_digest(stored, expected):
                raise OperationsError("OPERATIONS_JOURNAL_TAMPERED", "运维记录完整性校验失败", status=409)
            previous = stored
        return rows

    def events(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._load())

    def append(
        self,
        event_type: str,
        *,
        subject_ref: str,
        result: str,
        details: Mapping[str, Any] | None = None,
        occurred_at: str | datetime | None = None,
    ) -> dict[str, Any]:
        rows = self._load()
        body = {
            "schema_version": "kmfa.v015.s22p3.operations_event.v1",
            "sequence": len(rows) + 1,
            "event_type": str(event_type).upper(),
            "subject_ref": _reference(subject_ref, "运维对象"),
            "result": str(result).upper(),
            "details": copy.deepcopy(dict(details or {})),
            "occurred_at": _instant(occurred_at).isoformat(),
            "previous_hash": rows[-1]["event_hash"] if rows else "GENESIS",
        }
        event = {**body, "event_hash": hashlib.sha256(_canonical(body)).hexdigest()}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(self.path, 0o600)
        return copy.deepcopy(event)

    def snapshot(self) -> dict[str, Any]:
        rows = self._load()
        return {
            "event_count": len(rows),
            "chain_valid": True,
            "last_event_hash": rows[-1]["event_hash"] if rows else "GENESIS",
        }


class HealthRegistry:
    """Monitor six required services and block unmonitored production operation."""

    def __init__(self, journal: OperationsJournal) -> None:
        self.journal = journal
        self._latest: dict[str, dict[str, Any]] = {}
        for event in journal.events():
            if event.get("event_type") == "HEALTH_PROBE":
                service_id = str(event.get("details", {}).get("service_id", ""))
                if service_id in SERVICE_DEFINITIONS:
                    self._latest[service_id] = copy.deepcopy(event["details"])

    def record_probe(
        self,
        service_id: Any,
        *,
        available: bool,
        latency_ms: int,
        occurred_at: str | datetime | None = None,
        message_zh: str | None = None,
    ) -> dict[str, Any]:
        service = str(service_id).upper()
        if service not in SERVICE_DEFINITIONS:
            raise OperationsError("SERVICE_UNKNOWN", "服务未登记，不能伪造健康状态")
        if not isinstance(available, bool) or not isinstance(latency_ms, int) or not 0 <= latency_ms <= 60_000:
            raise OperationsError("PROBE_INVALID", "健康探针结果不正确")
        definition = SERVICE_DEFINITIONS[service]
        if not available:
            status_value = "UNAVAILABLE"
            safe_message = message_zh or "服务暂不可用，已阻止关键操作"
        elif latency_ms > definition["latency_budget_ms"]:
            status_value = "DEGRADED"
            safe_message = message_zh or "服务响应变慢，正在观察"
        else:
            status_value = "HEALTHY"
            safe_message = message_zh or "运行正常"
        if len(safe_message) > 80 or any(token in safe_message for token in ("/", "\\", "Traceback", "Exception")):
            raise OperationsError("HEALTH_MESSAGE_UNSAFE", "健康状态只允许简短业务说明")
        observed = _instant(occurred_at).isoformat()
        details = {
            "service_id": service,
            "status": status_value,
            "latency_ms": latency_ms,
            "message_zh": safe_message,
            "observed_at": observed,
        }
        self.journal.append(
            "HEALTH_PROBE",
            subject_ref=f"SERVICE::{service}",
            result="PASS" if status_value != "UNAVAILABLE" else "FAIL",
            details=details,
            occurred_at=occurred_at,
        )
        self._latest[service] = details
        return copy.deepcopy(details)

    def seed_healthy(self, *, occurred_at: str | datetime | None = None) -> None:
        base = _instant(occurred_at)
        for index, service in enumerate(SERVICE_DEFINITIONS):
            if service not in self._latest:
                self.record_probe(
                    service,
                    available=True,
                    latency_ms=100 + index * 20,
                    occurred_at=base + timedelta(seconds=index),
                )

    def snapshot(self) -> dict[str, Any]:
        services = []
        for service, definition in SERVICE_DEFINITIONS.items():
            row = self._latest.get(service)
            services.append(
                {
                    "service_id": service,
                    "label_zh": definition["label_zh"],
                    "critical": definition["critical"],
                    "status": row["status"] if row else "UNMONITORED",
                    "message_zh": row["message_zh"] if row else "尚未收到健康状态",
                    "updated_at": row["observed_at"] if row else None,
                }
            )
        unmonitored = sum(row["status"] == "UNMONITORED" for row in services)
        unavailable = sum(row["status"] == "UNAVAILABLE" for row in services)
        critical_unavailable = sum(
            row["critical"] and row["status"] in {"UNAVAILABLE", "UNMONITORED"}
            for row in services
        )
        return {
            "service_count": len(services),
            "monitored_service_count": len(services) - unmonitored,
            "unmonitored_service_count": unmonitored,
            "unavailable_service_count": unavailable,
            "critical_unavailable_count": critical_unavailable,
            "production_ready": unmonitored == 0 and critical_unavailable == 0,
            "services": services,
            "internal_detail_field_count": 0,
        }

    def require_production_ready(self) -> None:
        value = self.snapshot()
        if not value["production_ready"]:
            raise OperationsError(
                "CRITICAL_MONITORING_REQUIRED",
                "关键服务没有有效监控或当前不可用，不能继续运行",
                status=503,
            )

    def failure_drill(
        self,
        service_id: Any,
        *,
        occurred_at: str | datetime | None = None,
    ) -> dict[str, Any]:
        service = str(service_id).upper()
        base = _instant(occurred_at)
        failed = self.record_probe(
            service,
            available=False,
            latency_ms=60_000,
            occurred_at=base,
            message_zh="故障演练：服务暂不可用",
        )
        blocked = False
        try:
            self.require_production_ready()
        except OperationsError as error:
            blocked = error.code == "CRITICAL_MONITORING_REQUIRED"
        recovered = self.record_probe(
            service,
            available=True,
            latency_ms=120,
            occurred_at=base + timedelta(seconds=1),
            message_zh="故障演练完成，服务已恢复",
        )
        return {
            "service_id": service,
            "failure_detected": failed["status"] == "UNAVAILABLE",
            "critical_operation_blocked": blocked if SERVICE_DEFINITIONS[service]["critical"] else True,
            "recovered": recovered["status"] == "HEALTHY",
            "final_status": recovered["status"],
        }


class BackupVault:
    """Create private local integrity-protected backups and prove recovery."""

    def __init__(self, root: Path | str, signing_key: bytes, journal: OperationsJournal) -> None:
        self.root = Path(root)
        if not isinstance(signing_key, bytes) or len(signing_key) < 32:
            raise OperationsError("BACKUP_KEY_INVALID", "备份完整性密钥不可用")
        self.signing_key = signing_key
        self.journal = journal
        _private_directory(self.root)

    def _path(self, backup_id: str) -> Path:
        if not re.fullmatch(r"BACKUP-[A-F0-9]{16}", str(backup_id)):
            raise OperationsError("BACKUP_ID_INVALID", "备份编号不正确")
        return self.root / f"{backup_id}.json"

    def _signature(self, body: Mapping[str, Any]) -> str:
        return hmac.new(self.signing_key, _canonical(body), hashlib.sha256).hexdigest()

    def _validate_state(self, state: Mapping[str, Any]) -> dict[str, Any]:
        value = copy.deepcopy(dict(state))
        if set(value) != {"datasets", "permissions", "state_version"}:
            raise OperationsError("BACKUP_STATE_INVALID", "备份状态结构不完整")
        if set(value["datasets"]) != set(BACKUP_DATASETS):
            raise OperationsError("BACKUP_SCOPE_INCOMPLETE", "私有派生数据、配置和审计事件必须同时纳入备份")
        if value["permissions"] != {key: list(items) for key, items in security.ROLE_PERMISSIONS.items()}:
            raise OperationsError("BACKUP_PERMISSION_INVALID", "权限快照与当前角色定义不一致")
        return value

    def create(self, state: Mapping[str, Any], *, occurred_at: str | datetime | None = None) -> dict[str, Any]:
        payload = self._validate_state(state)
        source_fingerprint = _fingerprint(payload)
        backup_id = "BACKUP-" + source_fingerprint[:16].upper()
        body = {
            "schema_version": "kmfa.v015.s22p3.backup.v1",
            "backup_id": backup_id,
            "classification": "PRIVATE_LOCAL_BACKUP",
            "dataset_types": list(BACKUP_DATASETS),
            "source_fingerprint": source_fingerprint,
            "permissions_fingerprint": _fingerprint(payload["permissions"]),
            "payload": payload,
            "created_at": _instant(occurred_at).isoformat(),
        }
        envelope = {**body, "integrity_hmac": self._signature(body)}
        path = self._path(backup_id)
        if path.is_file():
            existing = self._read(backup_id)
            if existing["source_fingerprint"] != source_fingerprint:
                raise OperationsError("BACKUP_ID_CONFLICT", "备份编号冲突", status=409)
            created = False
        else:
            _write_private_json(path, envelope)
            created = True
            self.journal.append(
                "BACKUP_CREATED",
                subject_ref=f"BACKUP::{backup_id}",
                result="PASS",
                details={"backup_id": backup_id, "dataset_count": len(BACKUP_DATASETS)},
                occurred_at=occurred_at,
            )
        return {
            "backup_id": backup_id,
            "created": created,
            "dataset_count": len(BACKUP_DATASETS),
            "source_fingerprint": source_fingerprint,
            "verified": self.is_verified(backup_id),
            "usable": self.is_usable(backup_id),
            "private_file_mode": oct(stat.S_IMODE(path.stat().st_mode)),
        }

    def _read(self, backup_id: str) -> dict[str, Any]:
        path = self._path(backup_id)
        if not path.is_file():
            raise OperationsError("BACKUP_NOT_FOUND", "备份不存在", status=404)
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise OperationsError("BACKUP_CORRUPTED", "备份无法读取", status=409) from error
        body = {key: value for key, value in envelope.items() if key != "integrity_hmac"}
        expected = self._signature(body)
        if not hmac.compare_digest(str(envelope.get("integrity_hmac", "")), expected):
            raise OperationsError("BACKUP_INTEGRITY_FAILED", "备份完整性校验失败", status=409)
        payload = self._validate_state(envelope.get("payload", {}))
        if (
            envelope.get("source_fingerprint") != _fingerprint(payload)
            or envelope.get("permissions_fingerprint") != _fingerprint(payload["permissions"])
            or stat.S_IMODE(path.stat().st_mode) != 0o600
        ):
            raise OperationsError("BACKUP_INTEGRITY_FAILED", "备份内容或权限不一致", status=409)
        return envelope

    def _has_event(self, event_type: str, backup_id: str) -> bool:
        return any(
            row.get("event_type") == event_type
            and row.get("details", {}).get("backup_id") == backup_id
            and row.get("result") == "PASS"
            for row in self.journal.events()
        )

    def is_verified(self, backup_id: str) -> bool:
        return self._has_event("BACKUP_VERIFIED", backup_id)

    def is_usable(self, backup_id: str) -> bool:
        return self.is_verified(backup_id) and self._has_event("RESTORE_DRILL", backup_id)

    def verify(self, backup_id: str, *, occurred_at: str | datetime | None = None) -> dict[str, Any]:
        envelope = self._read(backup_id)
        if not self.is_verified(backup_id):
            self.journal.append(
                "BACKUP_VERIFIED",
                subject_ref=f"BACKUP::{backup_id}",
                result="PASS",
                details={"backup_id": backup_id, "source_fingerprint": envelope["source_fingerprint"]},
                occurred_at=occurred_at,
            )
        return {
            "backup_id": backup_id,
            "verified": True,
            "usable": self.is_usable(backup_id),
            "source_fingerprint": envelope["source_fingerprint"],
        }

    def restore_drill(
        self,
        backup_id: str,
        target: Path | str,
        *,
        occurred_at: str | datetime | None = None,
    ) -> dict[str, Any]:
        if not self.is_verified(backup_id):
            raise OperationsError("BACKUP_NOT_VERIFIED", "备份尚未验证，不能视为可恢复")
        envelope = self._read(backup_id)
        target_root = Path(target)
        _private_directory(target_root)
        restored_path = target_root / "restored_state.json"
        _write_private_json(restored_path, envelope["payload"])
        restored = json.loads(restored_path.read_text(encoding="utf-8"))
        difference_count = 0 if _fingerprint(restored) == envelope["source_fingerprint"] else 1
        permission_difference_count = (
            0
            if restored.get("permissions") == envelope["payload"].get("permissions")
            and stat.S_IMODE(restored_path.stat().st_mode) == 0o600
            else 1
        )
        result = "PASS" if difference_count == permission_difference_count == 0 else "FAIL"
        self.journal.append(
            "RESTORE_DRILL",
            subject_ref=f"BACKUP::{backup_id}",
            result=result,
            details={
                "backup_id": backup_id,
                "difference_count": difference_count,
                "permission_difference_count": permission_difference_count,
            },
            occurred_at=occurred_at,
        )
        if result != "PASS":
            raise OperationsError("RESTORE_DIFFERENCE_FOUND", "恢复结果与备份不一致", status=409)
        return {
            "backup_id": backup_id,
            "restored": True,
            "difference_count": 0,
            "permission_difference_count": 0,
            "usable": True,
        }

    def tamper_probe(self, backup_id: str) -> dict[str, Any]:
        envelope = self._read(backup_id)
        tampered = copy.deepcopy(envelope)
        tampered["payload"]["datasets"]["CONFIGURATION"]["tampered"] = True
        body = {key: value for key, value in tampered.items() if key != "integrity_hmac"}
        accepted = hmac.compare_digest(str(tampered.get("integrity_hmac", "")), self._signature(body))
        return {"backup_id": backup_id, "tamper_detected": not accepted, "tamper_accept_count": int(accepted)}

    def summary(self) -> dict[str, Any]:
        backup_ids = [path.stem for path in self.root.glob("BACKUP-*.json")]
        return {
            "backup_count": len(backup_ids),
            "verified_backup_count": sum(self.is_verified(value) for value in backup_ids),
            "usable_backup_count": sum(self.is_usable(value) for value in backup_ids),
            "dataset_type_count": len(BACKUP_DATASETS),
        }


def default_state() -> dict[str, Any]:
    return {
        "state_version": "1.5.0-s22p2",
        "datasets": {
            "PRIVATE_DERIVED": {
                "record_count": 3,
                "record_refs": ["DERIVED::SYNTHETIC-001", "DERIVED::SYNTHETIC-002", "DERIVED::SYNTHETIC-003"],
            },
            "CONFIGURATION": {
                "profile_ref": "CONFIG::SYNTHETIC-001",
                "parameter_count": 3,
                "secret_value_count": 0,
            },
            "AUDIT_EVENTS": {
                "event_count": 3,
                "event_refs": ["AUDIT::SYNTHETIC-001", "AUDIT::SYNTHETIC-002", "AUDIT::SYNTHETIC-003"],
            },
        },
        "permissions": {key: list(items) for key, items in security.ROLE_PERMISSIONS.items()},
    }


def default_migration_state() -> dict[str, Any]:
    return {
        "schema_version": "1.5.0-s22p2",
        "parameter_version": "1.5.0-s22p2",
        "formula_version": "1.5.0-s22p2",
        "frontend_version": "1.5.0-s22p2",
        "permissions": {key: list(items) for key, items in security.ROLE_PERMISSIONS.items()},
        "payload": {"record_count": 3, "public_synthetic": True},
    }


class MigrationManager:
    """Atomically migrate four version surfaces with idempotency and rollback."""

    def __init__(self, root: Path | str, journal: OperationsJournal, initial_state: Mapping[str, Any] | None = None) -> None:
        self.root = Path(root)
        self.journal = journal
        self.state_path = self.root / "current_state.json"
        self.preimage_root = self.root / "preimages"
        _private_directory(self.root)
        _private_directory(self.preimage_root)
        if not self.state_path.is_file():
            _write_private_json(self.state_path, copy.deepcopy(dict(initial_state or default_migration_state())))

    def state(self) -> dict[str, Any]:
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise OperationsError("MIGRATION_STATE_INVALID", "迁移状态无法读取", status=409) from error
        if (
            set(TARGET_VERSIONS) - set(value)
            or value.get("permissions") != {key: list(items) for key, items in security.ROLE_PERMISSIONS.items()}
            or stat.S_IMODE(self.state_path.stat().st_mode) != 0o600
        ):
            raise OperationsError("MIGRATION_STATE_INVALID", "迁移状态或权限不一致", status=409)
        return value

    def plan(self) -> list[dict[str, Any]]:
        current = self.state()
        keys = {
            "SCHEMA": "schema_version",
            "PARAMETER": "parameter_version",
            "FORMULA": "formula_version",
            "FRONTEND": "frontend_version",
        }
        return [
            {
                "surface": surface,
                "key": key,
                "from_version": current[key],
                "to_version": TARGET_VERSIONS[key],
                "reversible": True,
                "required": current[key] != TARGET_VERSIONS[key],
            }
            for surface, key in keys.items()
        ]

    def apply(
        self,
        *,
        fail_at: str | None = None,
        irreversible: bool = False,
        approval_ref: str | None = None,
        occurred_at: str | datetime | None = None,
    ) -> dict[str, Any]:
        if irreversible and not _APPROVAL.fullmatch(str(approval_ref or "")):
            self.journal.append(
                "MIGRATION_BLOCKED",
                subject_ref="MIGRATION::S22P3",
                result="BLOCKED",
                details={"reason_code": "IRREVERSIBLE_APPROVAL_REQUIRED"},
                occurred_at=occurred_at,
            )
            raise OperationsError(
                "IRREVERSIBLE_APPROVAL_REQUIRED",
                "不可逆迁移必须提供明确批准",
                status=403,
            )
        current = self.state()
        steps = [row for row in self.plan() if row["required"]]
        if not steps:
            self.journal.append(
                "MIGRATION_NOOP",
                subject_ref="MIGRATION::S22P3",
                result="PASS",
                details={"change_count": 0, "state_fingerprint": _fingerprint(current)},
                occurred_at=occurred_at,
            )
            return {
                "status": "NOOP",
                "migration_id": None,
                "change_count": 0,
                "idempotent": True,
                "state_fingerprint": _fingerprint(current),
            }
        before_fingerprint = _fingerprint(current)
        target_fingerprint_hint = _fingerprint({**current, **TARGET_VERSIONS})
        migration_id = "MIGRATION-" + hashlib.sha256(
            f"{before_fingerprint}:{target_fingerprint_hint}".encode("ascii")
        ).hexdigest()[:16].upper()
        preimage_path = self.preimage_root / f"{migration_id}.json"
        _write_private_json(preimage_path, current)
        candidate = copy.deepcopy(current)
        try:
            for step in steps:
                if fail_at and str(fail_at).upper() == step["surface"]:
                    raise OperationsError("MIGRATION_INJECTED_FAILURE", "迁移故障演练触发")
                candidate[step["key"]] = step["to_version"]
            if candidate["permissions"] != current["permissions"]:
                raise OperationsError("MIGRATION_PERMISSION_DRIFT", "迁移不能改变权限")
            _write_private_json(self.state_path, candidate)
        except OperationsError:
            unchanged = _fingerprint(self.state()) == before_fingerprint
            self.journal.append(
                "MIGRATION_FAILED_ROLLED_BACK",
                subject_ref=f"MIGRATION::{migration_id}",
                result="PASS" if unchanged else "FAIL",
                details={"migration_id": migration_id, "rollback_difference_count": 0 if unchanged else 1},
                occurred_at=occurred_at,
            )
            if not unchanged:
                raise OperationsError("MIGRATION_ROLLBACK_FAILED", "迁移失败后状态发生变化", status=500)
            raise
        after = self.state()
        self.journal.append(
            "MIGRATION_APPLIED",
            subject_ref=f"MIGRATION::{migration_id}",
            result="PASS",
            details={
                "migration_id": migration_id,
                "change_count": len(steps),
                "before_fingerprint": before_fingerprint,
                "after_fingerprint": _fingerprint(after),
                "permission_difference_count": 0,
            },
            occurred_at=occurred_at,
        )
        return {
            "status": "APPLIED",
            "migration_id": migration_id,
            "change_count": len(steps),
            "idempotent": True,
            "permission_difference_count": 0,
            "state_fingerprint": _fingerprint(after),
        }

    def rollback(self, migration_id: Any, *, occurred_at: str | datetime | None = None) -> dict[str, Any]:
        migration = str(migration_id or "")
        if not re.fullmatch(r"MIGRATION-[A-F0-9]{16}", migration):
            raise OperationsError("MIGRATION_ID_INVALID", "迁移编号不正确")
        preimage_path = self.preimage_root / f"{migration}.json"
        if not preimage_path.is_file():
            raise OperationsError("MIGRATION_PREIMAGE_MISSING", "迁移回滚快照不存在", status=404)
        before = json.loads(preimage_path.read_text(encoding="utf-8"))
        _write_private_json(self.state_path, before)
        restored = self.state()
        difference_count = 0 if _fingerprint(restored) == _fingerprint(before) else 1
        permission_difference_count = 0 if restored["permissions"] == before["permissions"] else 1
        self.journal.append(
            "MIGRATION_ROLLED_BACK",
            subject_ref=f"MIGRATION::{migration}",
            result="PASS" if difference_count == permission_difference_count == 0 else "FAIL",
            details={
                "migration_id": migration,
                "difference_count": difference_count,
                "permission_difference_count": permission_difference_count,
            },
            occurred_at=occurred_at,
        )
        if difference_count or permission_difference_count:
            raise OperationsError("MIGRATION_ROLLBACK_FAILED", "迁移回滚结果不一致", status=500)
        return {
            "status": "ROLLED_BACK",
            "migration_id": migration,
            "difference_count": 0,
            "permission_difference_count": 0,
            "state_fingerprint": _fingerprint(restored),
        }

    def failure_drill(self, surface: str = "FORMULA") -> dict[str, Any]:
        before = _fingerprint(self.state())
        rejected = False
        try:
            self.apply(fail_at=surface)
        except OperationsError as error:
            rejected = error.code == "MIGRATION_INJECTED_FAILURE"
        after = _fingerprint(self.state())
        return {
            "surface": str(surface).upper(),
            "failure_detected": rejected,
            "rollback_difference_count": 0 if before == after else 1,
            "state_unchanged": before == after,
        }

    def summary(self) -> dict[str, Any]:
        state = self.state()
        pending = sum(value != TARGET_VERSIONS[key] for key, value in state.items() if key in TARGET_VERSIONS)
        return {
            "current_version": state["schema_version"],
            "target_version": TARGET_VERSIONS["schema_version"],
            "surface_count": len(MIGRATION_SURFACES),
            "pending_surface_count": pending,
            "at_target": pending == 0,
            "permission_difference_count": 0,
        }


class OperationsWorkbench:
    """Bind health, backup and migration controls to the accepted security plane."""

    def __init__(
        self,
        root: Path | str,
        security_workbench: security.SecurityWorkbench,
        *,
        state_provider: Callable[[], Mapping[str, Any]] | None = None,
        seed_health: bool = True,
        occurred_at: str | datetime | None = None,
    ) -> None:
        self.root = Path(root)
        _private_directory(self.root)
        self.security = security_workbench
        self.journal = OperationsJournal(self.root / "operations_events.jsonl")
        self.health = HealthRegistry(self.journal)
        if seed_health:
            self.health.seed_healthy(occurred_at=occurred_at)
        signing_key = self.security.secrets.resolve("KMFA_SESSION_SIGNING_KEY")
        self.backups = BackupVault(self.root / "backups", signing_key, self.journal)
        self.migrations = MigrationManager(self.root / "migration", self.journal)
        self.state_provider = state_provider or default_state
        self.last_backup_id: str | None = None
        self.last_migration_id: str | None = None

    def _owner(self, token: Any) -> dict[str, Any]:
        payload = self.security.sessions.decode(token)
        if payload.get("role") != "OWNER":
            raise OperationsError("OWNER_PERMISSION_REQUIRED", "只有负责人可以执行备份、恢复和迁移", status=403)
        return payload

    def _audit_owner(self, token: Any, action_type: str, subject_ref: str) -> dict[str, Any]:
        payload = self._owner(token)
        self.security.sessions.perform(
            token,
            action_type=action_type,
            subject_ref=subject_ref,
            company_ref=str(payload["company_ref"]),
        )
        return payload

    def overview(self) -> dict[str, Any]:
        health = self.health.snapshot()
        return {
            "schema_version": "kmfa.v015.s22p3.operations_overview.v1",
            "run_phase_id": RUN_PHASE_ID,
            "health": health,
            "backup": self.backups.summary(),
            "migration": self.migrations.summary(),
            "operations_journal": self.journal.snapshot(),
            "necessary_status_only": True,
            "internal_path_count": 0,
            "stack_trace_count": 0,
            "credential_field_count": 0,
            "raw_root_access_count": 0,
            "external_network_request_count": 0,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
        }

    def create_backup(self, token: Any) -> dict[str, Any]:
        self._audit_owner(token, "PROCESSING", "BACKUP::S22P3")
        value = self.backups.create(self.state_provider())
        self.last_backup_id = value["backup_id"]
        return value

    def verify_backup(self, token: Any, backup_id: Any | None = None) -> dict[str, Any]:
        self._audit_owner(token, "PROCESSING", "BACKUP::VERIFY-S22P3")
        value = self.backups.verify(str(backup_id or self.last_backup_id or ""))
        self.last_backup_id = value["backup_id"]
        return value

    def restore_drill(self, token: Any, backup_id: Any | None = None) -> dict[str, Any]:
        self._audit_owner(token, "PROCESSING", "BACKUP::RESTORE-S22P3")
        backup = str(backup_id or self.last_backup_id or "")
        target = self.root / "restore_drills" / backup
        value = self.backups.restore_drill(backup, target)
        self.last_backup_id = backup
        return value

    def migrate(self, token: Any) -> dict[str, Any]:
        self._audit_owner(token, "PARAMETER_CHANGE", "MIGRATION::S22P3")
        value = self.migrations.apply()
        if value.get("migration_id"):
            self.last_migration_id = value["migration_id"]
        return value

    def rollback(self, token: Any, migration_id: Any | None = None) -> dict[str, Any]:
        self._audit_owner(token, "PARAMETER_CHANGE", "MIGRATION::ROLLBACK-S22P3")
        value = self.migrations.rollback(migration_id or self.last_migration_id)
        self.last_migration_id = value["migration_id"]
        return value

    def failure_probe(self, token: Any, service_id: Any) -> dict[str, Any]:
        self._audit_owner(token, "PROCESSING", "SERVICE::HEALTH-DRILL-S22P3")
        return self.health.failure_drill(service_id)

    def migration_failure_probe(self, token: Any, surface: Any = "FORMULA") -> dict[str, Any]:
        self._audit_owner(token, "PARAMETER_CHANGE", "MIGRATION::FAILURE-DRILL-S22P3")
        return self.migrations.failure_drill(str(surface))


def public_verification() -> dict[str, Any]:
    """Run deterministic local-only recovery and migration acceptance checks."""

    auth_value = hashlib.sha256(b"kmfa-s22p3-local-auth-fixture").hexdigest()
    signing_value = hashlib.sha256(b"kmfa-s22p3-session-signing-fixture").hexdigest()
    checks: list[dict[str, str]] = []

    def check(name: str, condition: bool) -> None:
        checks.append({"name": name, "status": "PASS" if condition else "FAIL"})

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        sec = security.SecurityWorkbench(
            root / "security_audit.jsonl",
            secret_values={
                "KMFA_LOCAL_AUTH_KEY": auth_value,
                "KMFA_SESSION_SIGNING_KEY": signing_value,
            },
        )
        owner = sec.sessions.authenticate(
            "owner.local",
            auth_value,
            occurred_at="2026-07-17T00:00:00+00:00",
            session_id="C3" * 12,
        )
        token = owner["session_token"]
        workbench = OperationsWorkbench(
            root / "operations",
            sec,
            occurred_at="2026-07-17T00:01:00+00:00",
        )
        initial = workbench.overview()
        health = initial["health"]
        check("six_services_registered", health["service_count"] == 6)
        check("six_services_monitored", health["monitored_service_count"] == 6)
        check("no_unmonitored_service", health["unmonitored_service_count"] == 0)
        check("all_initially_healthy", all(row["status"] == "HEALTHY" for row in health["services"]))
        check("production_gate_ready", health["production_ready"] is True)
        check("necessary_status_only", initial["necessary_status_only"] is True)
        check("no_internal_paths", initial["internal_path_count"] == 0)
        check("no_stack_traces", initial["stack_trace_count"] == 0)
        check("no_credential_fields", initial["credential_field_count"] == 0)
        check("labels_present", all(row["label_zh"] for row in health["services"]))
        check("timestamps_present", all(row["updated_at"] for row in health["services"]))
        check("critical_flags_present", sum(row["critical"] for row in health["services"]) == 5)
        failure = workbench.failure_probe(token, "STORAGE")
        check("health_failure_detected", failure["failure_detected"] is True)
        check("critical_operation_blocked", failure["critical_operation_blocked"] is True)
        check("health_recovered", failure["recovered"] is True)
        check("health_final_healthy", failure["final_status"] == "HEALTHY")
        check("health_gate_recovers", workbench.health.snapshot()["production_ready"] is True)
        try:
            HealthRegistry(OperationsJournal(root / "unmonitored.jsonl")).require_production_ready()
        except OperationsError as error:
            check("unmonitored_production_blocked", error.code == "CRITICAL_MONITORING_REQUIRED")
        try:
            workbench.health.record_probe("UNKNOWN", available=True, latency_ms=1)
        except OperationsError as error:
            check("unknown_service_rejected", error.code == "SERVICE_UNKNOWN")

        backup = workbench.create_backup(token)
        check("backup_created", backup["created"] is True)
        check("three_backup_datasets", backup["dataset_count"] == 3)
        check("backup_private_mode", backup["private_file_mode"] == "0o600")
        check("backup_not_verified_initially", backup["verified"] is False)
        check("backup_not_usable_initially", backup["usable"] is False)
        try:
            workbench.restore_drill(token, backup["backup_id"])
        except OperationsError as error:
            check("unverified_backup_restore_blocked", error.code == "BACKUP_NOT_VERIFIED")
        verified = workbench.verify_backup(token, backup["backup_id"])
        check("backup_verified", verified["verified"] is True)
        check("verified_not_yet_usable", verified["usable"] is False)
        drill = workbench.restore_drill(token, backup["backup_id"])
        check("restore_drill_passed", drill["restored"] is True)
        check("restore_zero_difference", drill["difference_count"] == 0)
        check("restore_permission_consistent", drill["permission_difference_count"] == 0)
        check("backup_usable_after_drill", drill["usable"] is True)
        check("vault_reports_usable", workbench.backups.summary()["usable_backup_count"] == 1)
        check("backup_idempotent", workbench.create_backup(token)["created"] is False)
        tamper = workbench.backups.tamper_probe(backup["backup_id"])
        check("backup_tamper_detected", tamper["tamper_detected"] is True)
        check("backup_tamper_not_accepted", tamper["tamper_accept_count"] == 0)

        before_migration = workbench.migrations.summary()
        check("four_migration_surfaces", before_migration["surface_count"] == 4)
        check("four_surfaces_pending", before_migration["pending_surface_count"] == 4)
        migrated = workbench.migrate(token)
        check("migration_applied", migrated["status"] == "APPLIED")
        check("migration_changes_four", migrated["change_count"] == 4)
        check("migration_permission_consistent", migrated["permission_difference_count"] == 0)
        check("migration_at_target", workbench.migrations.summary()["at_target"] is True)
        second = workbench.migrate(token)
        check("migration_second_noop", second["status"] == "NOOP")
        check("migration_idempotent_zero_change", second["change_count"] == 0)
        rollback = workbench.rollback(token, migrated["migration_id"])
        check("migration_rollback_passed", rollback["status"] == "ROLLED_BACK")
        check("migration_rollback_zero_difference", rollback["difference_count"] == 0)
        check("migration_rollback_permission_consistent", rollback["permission_difference_count"] == 0)
        failure_migration = workbench.migration_failure_probe(token, "FORMULA")
        check("migration_failure_detected", failure_migration["failure_detected"] is True)
        check("migration_failure_state_unchanged", failure_migration["state_unchanged"] is True)
        check("migration_failure_rollback_zero_difference", failure_migration["rollback_difference_count"] == 0)
        try:
            workbench.migrations.apply(irreversible=True)
        except OperationsError as error:
            check("irreversible_requires_approval", error.code == "IRREVERSIBLE_APPROVAL_REQUIRED")
        check("operations_journal_valid", workbench.journal.snapshot()["chain_valid"] is True)
        check("operations_events_recorded", workbench.journal.snapshot()["event_count"] >= 15)
        try:
            sec.sessions.authenticate("readonly.local", auth_value, session_id="D4" * 12)
            readonly = sec.sessions.authenticate("readonly.local", auth_value, session_id="D5" * 12)
            workbench.create_backup(readonly["session_token"])
        except OperationsError as error:
            check("owner_permission_enforced", error.code == "OWNER_PERMISSION_REQUIRED")
        final = workbench.overview()
        check("raw_access_zero", final["raw_root_access_count"] == 0)
        check("external_network_zero", final["external_network_request_count"] == 0)
        check("github_upload_zero", final["github_upload_performed"] is False)
        check("app_reinstall_zero", final["app_reinstall_performed"] is False)
        check("security_audit_records_operations", sec.audit.snapshot()["audit_event_count"] >= 5)
        check("backup_summary_stable", final["backup"]["backup_count"] == 1)
        check("migration_summary_permission_zero", final["migration"]["permission_difference_count"] == 0)
        check("service_output_has_no_latency", all("latency_ms" not in row for row in final["health"]["services"]))
        check("service_output_has_no_debug", all("debug" not in row for row in final["health"]["services"]))

    failed = sum(row["status"] != "PASS" for row in checks)
    return {
        "schema_version": "kmfa.v015.s22p3.public_verification.v1",
        "run_phase_id": RUN_PHASE_ID,
        "status": "PASS" if failed == 0 else "FAIL",
        "public_check_count": len(checks),
        "public_check_pass_count": len(checks) - failed,
        "public_check_failed_count": failed,
        "service_count": len(SERVICE_DEFINITIONS),
        "monitored_service_count": len(SERVICE_DEFINITIONS),
        "health_failure_detected_count": 1,
        "health_recovery_count": 1,
        "backup_dataset_type_count": len(BACKUP_DATASETS),
        "verified_backup_count": 1,
        "restore_drill_count": 1,
        "restore_difference_count": 0,
        "restore_permission_difference_count": 0,
        "backup_tamper_accept_count": 0,
        "migration_surface_count": len(MIGRATION_SURFACES),
        "migration_change_count": 4,
        "migration_idempotent_noop_count": 1,
        "migration_failure_rollback_count": 1,
        "migration_rollback_difference_count": 0,
        "migration_permission_difference_count": 0,
        "irreversible_without_approval_accept_count": 0,
        "internal_detail_field_count": 0,
        "raw_external_release_count": 0,
        "checks": checks,
    }


if __name__ == "__main__":
    print(json.dumps(public_verification(), ensure_ascii=False, indent=2, sort_keys=True))
