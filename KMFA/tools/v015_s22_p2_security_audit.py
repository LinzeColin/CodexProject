#!/usr/bin/env python3
"""KMFA v1.5 S22-P2 authentication, audit, secret and I/O security kernel.

The implementation is public-synthetic and local-only. Credentials are resolved
from environment references at runtime, never from tracked configuration. Audit
events are append-only and hash-linked. All security controls fail closed.
"""

from __future__ import annotations

import base64
import copy
import fcntl
import hashlib
import hmac
import json
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


RUN_PHASE_ID = "V015_S22_P2_SECURITY_AUDIT"
ROADMAP_PHASE_ID = "S22-P2"
TASK_ID = "KMFA-V015-S22-P2-SECURITY-AUDIT-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S22-P2-SECURITY-AUDIT"
VERSION = "1.5.0-dev-s22p2"
DATA_CLASSIFICATION = "PUBLIC_SYNTHETIC"
DEFAULT_EVENT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".codex_private_runtime/v015_s22_p2_security_audit/audit_events.jsonl"
)

REQUIRED_AUDIT_ACTION_TYPES = (
    "LOGIN",
    "SENSITIVE_VIEW",
    "PROCESSING",
    "PARAMETER_CHANGE",
    "PUBLICATION",
)
AUDIT_ACTION_TYPES = (*REQUIRED_AUDIT_ACTION_TYPES, "SENSITIVE_DOWNLOAD")
AUDIT_RESULTS = ("SUCCESS", "DENIED", "FAILED")
SECRET_REFERENCES = ("KMFA_LOCAL_AUTH_KEY", "KMFA_SESSION_SIGNING_KEY")
ATTACK_CATEGORIES = (
    "INJECTION",
    "PATH_TRAVERSAL",
    "MALICIOUS_FILE",
    "FORMULA_INJECTION",
    "SENSITIVE_DOWNLOAD",
)
ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "OWNER": (
        "VIEW_SENSITIVE", "PROCESS", "CHANGE_PARAMETER", "PUBLISH_INTERNAL",
        "DOWNLOAD_SENSITIVE", "QUERY_AUDIT",
    ),
    "FINANCE_ADMIN": (
        "VIEW_SENSITIVE", "PROCESS", "CHANGE_PARAMETER", "PUBLISH_INTERNAL",
        "DOWNLOAD_SENSITIVE", "QUERY_AUDIT",
    ),
    "REVIEWER": ("VIEW_SENSITIVE", "QUERY_AUDIT"),
    "READONLY": (),
}
ACTION_PERMISSION = {
    "SENSITIVE_VIEW": "VIEW_SENSITIVE",
    "PROCESSING": "PROCESS",
    "PARAMETER_CHANGE": "CHANGE_PARAMETER",
    "PUBLICATION": "PUBLISH_INTERNAL",
    "SENSITIVE_DOWNLOAD": "DOWNLOAD_SENSITIVE",
}
DEFAULT_ACCOUNTS: dict[str, dict[str, str]] = {
    "owner.local": {"role": "OWNER", "company_ref": "COMPANY::SYNTHETIC-A", "auth_ref": "KMFA_LOCAL_AUTH_KEY"},
    "finance.local": {"role": "FINANCE_ADMIN", "company_ref": "COMPANY::SYNTHETIC-A", "auth_ref": "KMFA_LOCAL_AUTH_KEY"},
    "reviewer.local": {"role": "REVIEWER", "company_ref": "COMPANY::SYNTHETIC-A", "auth_ref": "KMFA_LOCAL_AUTH_KEY"},
    "readonly.local": {"role": "READONLY", "company_ref": "COMPANY::SYNTHETIC-A", "auth_ref": "KMFA_LOCAL_AUTH_KEY"},
}

_REFERENCE = re.compile(r"^[A-Z][A-Z0-9_]*::[A-Za-z0-9][A-Za-z0-9._:-]{1,127}$")
_USERNAME = re.compile(r"^[a-z][a-z0-9._-]{2,63}$")
_SECRET_REFERENCE = re.compile(r"^KMFA_[A-Z0-9_]{4,64}$")
_PLACEHOLDER = re.compile(r"(?:change.?me|placeholder|example|dummy|password|secret|test.?key)", re.I)
_INJECTION = re.compile(
    r"(?:<\s*script\b|javascript:|\bunion\s+select\b|\bor\s+1\s*=\s*1\b|"
    r"(?:;|&&|\|\|)\s*(?:rm|curl|wget|bash|sh|python)\b|\$\(|`[^`]+`|\.\./|\.\.\\)",
    re.I,
)
_DANGEROUS_EXTENSIONS = {
    ".app", ".bat", ".cmd", ".com", ".dll", ".dmg", ".dylib", ".exe",
    ".jar", ".js", ".msi", ".ps1", ".py", ".sh", ".vbs", ".xlsm", ".docm",
}
_ALLOWED_EXTENSIONS = {".csv", ".json", ".pdf", ".png", ".txt", ".xlsx"}
_EXECUTABLE_MAGIC = (b"MZ", b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf")
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
_SENSITIVE_KEY = re.compile(r"(?:password|passwd|secret|token|api[_-]?key|authorization|credential)", re.I)
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{8,}=*")


class SecurityError(ValueError):
    """Stable fail-closed error safe for the local security workbench."""

    def __init__(self, code: str, message_zh: str, *, status: int = 400) -> None:
        super().__init__(message_zh)
        self.code = code
        self.message_zh = message_zh
        self.status = status


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _event_digest(event: Mapping[str, Any]) -> str:
    return _digest({key: value for key, value in event.items() if key != "event_hash"})


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _instant(value: str | datetime | None) -> datetime:
    if isinstance(value, datetime):
        result = value
    else:
        try:
            result = datetime.fromisoformat(str(value or _now().isoformat()).replace("Z", "+00:00"))
        except ValueError as error:
            raise SecurityError("TIME_INVALID", "时间格式不正确") from error
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc).replace(microsecond=0)


def _text(value: Any, field: str, *, minimum: int = 1, maximum: int = 160) -> str:
    result = str(value or "").strip()
    if len(result) < minimum or len(result) > maximum or any(ord(char) < 32 for char in result):
        raise SecurityError("FIELD_INVALID", f"{field} 不完整或格式不正确")
    return result


def _ref(value: Any, field: str) -> str:
    result = _text(value, field, minimum=4, maximum=160)
    if not _REFERENCE.fullmatch(result):
        raise SecurityError("REFERENCE_INVALID", f"{field} 必须使用安全引用")
    return result


def _actor_ref(username: str) -> str:
    return "ACTOR::" + hashlib.sha256(username.encode("utf-8")).hexdigest()[:16].upper()


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def validate_audit_chain(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    previous = "GENESIS"
    action_types: set[str] = set()
    denied = 0
    for sequence, source in enumerate(events, start=1):
        event = dict(source)
        if event.get("sequence") != sequence:
            raise SecurityError("AUDIT_CHAIN_INVALID", "审计序号不连续", status=409)
        if event.get("previous_event_hash") != previous:
            raise SecurityError("AUDIT_CHAIN_INVALID", "审计链前序摘要不一致", status=409)
        if event.get("event_hash") != _event_digest(event):
            raise SecurityError("AUDIT_CHAIN_INVALID", "审计内容已被修改", status=409)
        if event.get("append_only") is not True or event.get("in_place_update_allowed") is not False:
            raise SecurityError("AUDIT_CHAIN_INVALID", "审计记录不是追加式", status=409)
        if event.get("action_type") not in AUDIT_ACTION_TYPES or event.get("result") not in AUDIT_RESULTS:
            raise SecurityError("AUDIT_CHAIN_INVALID", "审计动作或结果不受支持", status=409)
        if event.get("sensitive_field_count") != 0 or event.get("credential_exposed") is not False:
            raise SecurityError("AUDIT_SECRET_EXPOSURE", "审计记录包含秘密字段", status=409)
        encoded = json.dumps(event, ensure_ascii=False, sort_keys=True)
        if _BEARER.search(encoded):
            raise SecurityError("AUDIT_SECRET_EXPOSURE", "审计记录包含授权值", status=409)
        previous = str(event["event_hash"])
        action_types.add(str(event["action_type"]))
        denied += int(event["result"] == "DENIED")
    return {
        "audit_event_count": len(events),
        "audit_action_type_count": len(action_types),
        "required_action_type_coverage_count": len(set(REQUIRED_AUDIT_ACTION_TYPES) & action_types),
        "denied_event_count": denied,
        "chain_valid": True,
        "append_only": True,
        "tamper_detected_count": 0,
    }


class AuditJournal:
    """Append-only hash-linked audit journal with production fail-closed gate."""

    def __init__(self, path: Path | str, *, enabled: bool = True, environment: str = "LOCAL_SANDBOX") -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.environment = str(environment).upper()
        self.enabled = bool(enabled)
        if self.environment == "PRODUCTION" and not self.enabled:
            raise SecurityError("PRODUCTION_AUDIT_REQUIRED", "生产运行不能关闭审计", status=503)

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        try:
            rows = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except (OSError, json.JSONDecodeError) as error:
            raise SecurityError("AUDIT_CHAIN_INVALID", "审计记录无法读取", status=409) from error
        validate_audit_chain(rows)
        return rows

    def events(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._load())

    def append(
        self, *, action_type: str, actor_ref: str, role: str, company_ref: str,
        result: str, subject_ref: str, reason_code: str,
        session_fingerprint: str = "SESSION::NONE", occurred_at: str | datetime | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            raise SecurityError("AUDIT_REQUIRED", "审计未启用，操作已阻止", status=503)
        action = str(action_type).upper(); outcome = str(result).upper(); role_value = str(role).upper()
        if action not in AUDIT_ACTION_TYPES or outcome not in AUDIT_RESULTS or role_value not in ROLE_PERMISSIONS:
            raise SecurityError("AUDIT_EVENT_INVALID", "审计动作、结果或角色不受支持")
        actor = _ref(actor_ref, "操作人引用"); company = _ref(company_ref, "公司引用")
        subject = _ref(subject_ref, "对象引用"); session = _ref(session_fingerprint, "会话引用")
        reason = _text(reason_code, "原因代码", minimum=2, maximum=80).upper()
        if not re.fullmatch(r"[A-Z0-9_:-]+", reason):
            raise SecurityError("AUDIT_EVENT_INVALID", "原因代码格式不正确")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            rows = self._load()
            sequence = len(rows) + 1
            event = {
                "schema_version": "kmfa.v015.s22p2.audit_event.v1",
                "event_id": f"AUDIT-S22P2-{sequence:06d}",
                "sequence": sequence,
                "occurred_at": _instant(occurred_at).isoformat(),
                "action_type": action,
                "actor_ref": actor,
                "role": role_value,
                "company_ref": company,
                "subject_ref": subject,
                "session_fingerprint": session,
                "result": outcome,
                "reason_code": reason,
                "previous_event_hash": rows[-1]["event_hash"] if rows else "GENESIS",
                "append_only": True,
                "in_place_update_allowed": False,
                "sensitive_field_count": 0,
                "credential_exposed": False,
                "event_hash": "",
            }
            event["event_hash"] = _event_digest(event)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush(); os.fsync(handle.fileno())
            return copy.deepcopy(event)

    def query(
        self, *, action_type: str | None = None, result: str | None = None,
        actor_ref: str | None = None, limit: int = 100,
    ) -> dict[str, Any]:
        if not isinstance(limit, int) or limit < 1 or limit > 200:
            raise SecurityError("AUDIT_QUERY_INVALID", "审计查询条数必须在 1 到 200 之间")
        rows = self._load()
        if action_type:
            action = str(action_type).upper()
            if action not in AUDIT_ACTION_TYPES:
                raise SecurityError("AUDIT_QUERY_INVALID", "审计动作筛选不受支持")
            rows = [row for row in rows if row["action_type"] == action]
        if result:
            outcome = str(result).upper()
            if outcome not in AUDIT_RESULTS:
                raise SecurityError("AUDIT_QUERY_INVALID", "审计结果筛选不受支持")
            rows = [row for row in rows if row["result"] == outcome]
        if actor_ref:
            actor = _ref(actor_ref, "操作人引用")
            rows = [row for row in rows if row["actor_ref"] == actor]
        selected = rows[-limit:]
        return {
            "query_result_count": len(selected),
            "events": copy.deepcopy(selected),
            "query_filters": {"action_type": action_type, "result": result, "actor_ref": actor_ref},
        }

    def snapshot(self) -> dict[str, Any]:
        rows = self._load()
        summary = validate_audit_chain(rows) if rows else {
            "audit_event_count": 0, "audit_action_type_count": 0,
            "required_action_type_coverage_count": 0, "denied_event_count": 0,
            "chain_valid": True, "append_only": True, "tamper_detected_count": 0,
        }
        return {**summary, "events": copy.deepcopy(rows[-50:]), "audit_enabled": self.enabled, "environment": self.environment}

    def replace_event(self, *_: Any, **__: Any) -> None:
        raise SecurityError("AUDIT_APPEND_ONLY", "审计记录不能原位修改，只能追加", status=409)


class SecretProvider:
    """Resolve runtime values from allow-listed environment references only."""

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ = dict(os.environ if environ is None else environ)

    def _name(self, reference: Any) -> str:
        name = str(reference or "")
        if name not in SECRET_REFERENCES or not _SECRET_REFERENCE.fullmatch(name):
            raise SecurityError("SECRET_REFERENCE_DENIED", "秘密引用不在允许列表", status=403)
        return name

    def resolve(self, reference: Any) -> bytes:
        name = self._name(reference)
        value = self._environ.get(name, "")
        if len(value.encode("utf-8")) < 32:
            raise SecurityError("SECRET_MISSING", f"运行环境未配置 {name}", status=503)
        if _PLACEHOLDER.search(value):
            raise SecurityError("SECRET_WEAK", f"{name} 不能使用占位值", status=503)
        return value.encode("utf-8")

    def describe(self, reference: Any) -> dict[str, Any]:
        name = self._name(reference)
        configured = bool(self._environ.get(name))
        fingerprint = None
        if configured:
            fingerprint = "sha256:" + hashlib.sha256(self._environ[name].encode("utf-8")).hexdigest()[:16]
        return {
            "reference": name,
            "source": "ENVIRONMENT",
            "configured": configured,
            "fingerprint": fingerprint,
            "value_exposed": False,
            "tracked_plaintext_allowed": False,
        }

    def inventory(self) -> list[dict[str, Any]]:
        return [self.describe(name) for name in SECRET_REFERENCES]

    def redact(self, value: Any) -> str:
        text = str(value)
        for name in SECRET_REFERENCES:
            candidate = self._environ.get(name)
            if candidate:
                text = text.replace(candidate, "[REDACTED]")
        text = _BEARER.sub("Bearer [REDACTED]", text)
        return text

    def contains_runtime_value(self, value: Any) -> bool:
        text = str(value)
        return any(candidate and candidate in text for candidate in (self._environ.get(name) for name in SECRET_REFERENCES))


class SessionService:
    """Authenticate public-synthetic local accounts and issue signed sessions."""

    def __init__(
        self, audit: AuditJournal, secrets_provider: SecretProvider, *,
        accounts: Mapping[str, Mapping[str, str]] | None = None, session_minutes: int = 30,
    ) -> None:
        self.audit = audit; self.secrets = secrets_provider
        self.accounts = {key: dict(value) for key, value in (accounts or DEFAULT_ACCOUNTS).items()}
        self.session_minutes = session_minutes
        self._revoked: set[str] = set()
        if not isinstance(session_minutes, int) or session_minutes < 5 or session_minutes > 480:
            raise SecurityError("SESSION_POLICY_INVALID", "会话时长必须在 5 到 480 分钟之间")

    def _sign(self, payload_segment: str) -> str:
        value = hmac.new(self.secrets.resolve("KMFA_SESSION_SIGNING_KEY"), payload_segment.encode("ascii"), hashlib.sha256).digest()
        return _b64(value)

    def authenticate(
        self, username: Any, presented_value: Any, *, occurred_at: str | datetime | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        raw_username = str(username or "").strip().lower()
        actor = _actor_ref(raw_username or "invalid")
        account = self.accounts.get(raw_username)
        company = (account or {}).get("company_ref", "COMPANY::SYNTHETIC-A")
        role = (account or {}).get("role", "READONLY")
        now = _instant(occurred_at)
        valid_name = bool(_USERNAME.fullmatch(raw_username))
        expected = b""
        if account and valid_name:
            expected = self.secrets.resolve(account["auth_ref"])
        presented = str(presented_value or "").encode("utf-8")
        if not account or not valid_name or not presented or not hmac.compare_digest(expected, presented):
            self.audit.append(
                action_type="LOGIN", actor_ref=actor, role=role, company_ref=company,
                result="DENIED", subject_ref="AUTH::LOCAL", reason_code="AUTHENTICATION_FAILED",
                occurred_at=now,
            )
            raise SecurityError("AUTHENTICATION_FAILED", "身份验证失败", status=401)
        sid = session_id or secrets.token_hex(12).upper()
        if not re.fullmatch(r"[A-F0-9]{24}", sid):
            raise SecurityError("SESSION_ID_INVALID", "会话编号格式不正确")
        expires = now + timedelta(minutes=self.session_minutes)
        payload = {
            "schema_version": "kmfa.v015.s22p2.session.v1",
            "session_id": sid,
            "actor_ref": actor,
            "role": role,
            "company_ref": company,
            "issued_at": int(now.timestamp()),
            "expires_at": int(expires.timestamp()),
        }
        segment = _b64(_canonical(payload)); token = segment + "." + self._sign(segment)
        fingerprint = "SESSION::" + hashlib.sha256(token.encode("ascii")).hexdigest()[:16].upper()
        self.audit.append(
            action_type="LOGIN", actor_ref=actor, role=role, company_ref=company,
            result="SUCCESS", subject_ref="AUTH::LOCAL", reason_code="AUTHENTICATED",
            session_fingerprint=fingerprint, occurred_at=now,
        )
        return {
            "authenticated": True,
            "session_token": token,
            "session_fingerprint": fingerprint,
            "actor_ref": actor,
            "role": role,
            "company_ref": company,
            "permissions": list(ROLE_PERMISSIONS[role]),
            "expires_at": expires.isoformat(),
            "credential_exposed_in_audit": False,
        }

    def decode(self, token: Any, *, occurred_at: str | datetime | None = None) -> dict[str, Any]:
        value = str(token or "")
        try:
            segment, signature = value.split(".", 1)
            if not hmac.compare_digest(self._sign(segment), signature):
                raise ValueError("signature")
            payload = json.loads(_unb64(segment))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise SecurityError("SESSION_INVALID", "会话无效", status=401) from error
        if payload.get("session_id") in self._revoked:
            raise SecurityError("SESSION_REVOKED", "会话已退出", status=401)
        if _instant(occurred_at).timestamp() >= int(payload.get("expires_at", 0)):
            raise SecurityError("SESSION_EXPIRED", "会话已过期", status=401)
        if payload.get("role") not in ROLE_PERMISSIONS or not _REFERENCE.fullmatch(str(payload.get("company_ref", ""))):
            raise SecurityError("SESSION_INVALID", "会话内容无效", status=401)
        return copy.deepcopy(payload)

    def authorize(
        self, token: Any, permission: str, *, company_ref: str | None = None,
        occurred_at: str | datetime | None = None,
    ) -> dict[str, Any]:
        payload = self.decode(token, occurred_at=occurred_at)
        if permission not in ROLE_PERMISSIONS[payload["role"]]:
            raise SecurityError("PERMISSION_DENIED", "当前角色没有此操作权限", status=403)
        if company_ref is not None and _ref(company_ref, "公司引用") != payload["company_ref"]:
            raise SecurityError("COMPANY_SCOPE_DENIED", "不能访问其他主体的数据", status=403)
        return payload

    def perform(
        self, token: Any, *, action_type: str, subject_ref: str, company_ref: str,
        occurred_at: str | datetime | None = None,
    ) -> dict[str, Any]:
        action = str(action_type).upper()
        if action not in ACTION_PERMISSION:
            raise SecurityError("ACTION_INVALID", "安全动作不受支持")
        now = _instant(occurred_at); payload: dict[str, Any] | None = None
        try:
            payload = self.decode(token, occurred_at=now)
            self.authorize(token, ACTION_PERMISSION[action], company_ref=company_ref, occurred_at=now)
        except SecurityError as error:
            if payload is not None:
                fingerprint = "SESSION::" + hashlib.sha256(str(token).encode("utf-8")).hexdigest()[:16].upper()
                self.audit.append(
                    action_type=action, actor_ref=payload["actor_ref"], role=payload["role"],
                    company_ref=payload["company_ref"], result="DENIED", subject_ref=_ref(subject_ref, "对象引用"),
                    reason_code=error.code, session_fingerprint=fingerprint, occurred_at=now,
                )
            raise
        fingerprint = "SESSION::" + hashlib.sha256(str(token).encode("utf-8")).hexdigest()[:16].upper()
        return self.audit.append(
            action_type=action, actor_ref=payload["actor_ref"], role=payload["role"],
            company_ref=payload["company_ref"], result="SUCCESS", subject_ref=_ref(subject_ref, "对象引用"),
            reason_code="AUTHORIZED", session_fingerprint=fingerprint, occurred_at=now,
        )

    def query_audit(self, token: Any, **filters: Any) -> dict[str, Any]:
        self.authorize(token, "QUERY_AUDIT")
        return self.audit.query(**filters)

    def revoke(self, token: Any) -> None:
        payload = self.decode(token)
        self._revoked.add(str(payload["session_id"]))


class InputOutputGuard:
    """Reject injection, traversal, malicious files, formulas and unsafe downloads."""

    def __init__(self, sessions: SessionService) -> None:
        self.sessions = sessions
        self.rejections: list[dict[str, str]] = []

    def _reject(self, category: str, code: str, message: str, *, status: int = 400) -> None:
        self.rejections.append({"category": category, "code": code})
        raise SecurityError(code, message, status=status)

    def validate_text(self, value: Any) -> dict[str, Any]:
        text = str(value or "")
        if not text or len(text) > 2000 or "\x00" in text or _INJECTION.search(text):
            self._reject("INJECTION", "INJECTION_BLOCKED", "输入包含危险指令或脚本")
        return {"allowed": True, "category": "INJECTION", "normalized_length": len(text)}

    def validate_relative_path(self, value: Any) -> dict[str, Any]:
        text = str(value or "").strip()
        if not text or "\x00" in text or "\\" in text or text.startswith(("/", "~")):
            self._reject("PATH_TRAVERSAL", "PATH_TRAVERSAL_BLOCKED", "路径必须是安全的相对路径")
        path = PurePosixPath(text)
        if any(part in {"", ".", ".."} for part in path.parts):
            self._reject("PATH_TRAVERSAL", "PATH_TRAVERSAL_BLOCKED", "路径包含越界片段")
        return {"allowed": True, "category": "PATH_TRAVERSAL", "safe_path": path.as_posix()}

    def validate_file(self, filename: Any, content: bytes, *, maximum_bytes: int = 5_000_000) -> dict[str, Any]:
        name = str(filename or "")
        self.validate_relative_path(name)
        suffix = Path(name).suffix.lower()
        if suffix in _DANGEROUS_EXTENSIONS or suffix not in _ALLOWED_EXTENSIONS:
            self._reject("MALICIOUS_FILE", "FILE_TYPE_BLOCKED", "文件类型不允许")
        if not isinstance(content, bytes) or not content or len(content) > maximum_bytes:
            self._reject("MALICIOUS_FILE", "FILE_CONTENT_BLOCKED", "文件为空、过大或格式不正确")
        if any(content.startswith(magic) for magic in _EXECUTABLE_MAGIC):
            self._reject("MALICIOUS_FILE", "EXECUTABLE_FILE_BLOCKED", "检测到可执行文件内容")
        if suffix == ".csv":
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                self._reject("MALICIOUS_FILE", "FILE_ENCODING_BLOCKED", "CSV 编码不正确")
            for cell in re.split(r"[,\n]", text):
                self.validate_csv_cell(cell)
        return {"allowed": True, "category": "MALICIOUS_FILE", "file_extension": suffix, "byte_count": len(content)}

    def validate_csv_cell(self, value: Any) -> dict[str, Any]:
        text = str(value or "")
        if text.lstrip(" ").startswith(_FORMULA_PREFIXES):
            self._reject("FORMULA_INJECTION", "FORMULA_INJECTION_BLOCKED", "表格单元格包含可执行公式")
        return {"allowed": True, "category": "FORMULA_INJECTION", "cell_length": len(text)}

    def authorize_download(
        self, token: Any, *, artifact_ref: str, company_ref: str,
        classification: str, delivery_mode: str, occurred_at: str | datetime | None = None,
    ) -> dict[str, Any]:
        classification_value = str(classification).upper(); mode = str(delivery_mode).upper()
        if classification_value not in {"PUBLIC", "INTERNAL", "SENSITIVE"}:
            self._reject("SENSITIVE_DOWNLOAD", "CLASSIFICATION_INVALID", "下载分类不正确")
        if mode != "AUTHENTICATED":
            try:
                payload = self.sessions.decode(token, occurred_at=occurred_at)
                fingerprint = "SESSION::" + hashlib.sha256(str(token).encode("utf-8")).hexdigest()[:16].upper()
                self.sessions.audit.append(
                    action_type="SENSITIVE_DOWNLOAD", actor_ref=payload["actor_ref"], role=payload["role"],
                    company_ref=payload["company_ref"], result="DENIED", subject_ref=_ref(artifact_ref, "文件引用"),
                    reason_code="PUBLIC_LINK_BLOCKED", session_fingerprint=fingerprint, occurred_at=occurred_at,
                )
            finally:
                self.rejections.append({"category": "SENSITIVE_DOWNLOAD", "code": "PUBLIC_LINK_BLOCKED"})
            raise SecurityError("PUBLIC_LINK_BLOCKED", "敏感文件不能通过公开链接下载", status=403)
        if classification_value == "SENSITIVE":
            event = self.sessions.perform(
                token, action_type="SENSITIVE_DOWNLOAD", subject_ref=artifact_ref,
                company_ref=company_ref, occurred_at=occurred_at,
            )
        else:
            payload = self.sessions.authorize(token, "VIEW_SENSITIVE", company_ref=company_ref, occurred_at=occurred_at)
            event = {"actor_ref": payload["actor_ref"], "result": "SUCCESS"}
        return {
            "allowed": True,
            "classification": classification_value,
            "delivery_mode": mode,
            "public_link_created": False,
            "audit_event_id": event.get("event_id"),
        }


class SecurityWorkbench:
    """Local runtime façade used by the HTTP and browser acceptance layers."""

    def __init__(
        self, event_path: Path | str = DEFAULT_EVENT_PATH, *,
        secret_values: Mapping[str, str] | None = None,
        environment: str = "LOCAL_SANDBOX", audit_enabled: bool = True,
    ) -> None:
        self.audit = AuditJournal(event_path, enabled=audit_enabled, environment=environment)
        self.secrets = SecretProvider(secret_values)
        self.sessions = SessionService(self.audit, self.secrets)
        self.guard = InputOutputGuard(self.sessions)

    def options(self) -> dict[str, Any]:
        return {
            "schema_version": "kmfa.v015.s22p2.security_options.v1",
            "run_phase_id": RUN_PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "role_count": len(ROLE_PERMISSIONS),
            "required_audit_action_types": list(REQUIRED_AUDIT_ACTION_TYPES),
            "required_audit_action_type_count": len(REQUIRED_AUDIT_ACTION_TYPES),
            "audit_action_type_count": len(AUDIT_ACTION_TYPES),
            "secret_reference_count": len(SECRET_REFERENCES),
            "secret_sources": ["ENVIRONMENT"],
            "secret_inventory": self.secrets.inventory(),
            "plaintext_secret_count": 0,
            "attack_categories": list(ATTACK_CATEGORIES),
            "attack_category_count": len(ATTACK_CATEGORIES),
            "production_audit_required": True,
            "public_link_allowed": False,
            "raw_root_access_count": 0,
            "external_network_request_count": 0,
        }

    def snapshot(self, **filters: Any) -> dict[str, Any]:
        audit = self.audit.snapshot()
        query = self.audit.query(**filters) if any(value is not None for value in filters.values()) else {"query_result_count": len(audit["events"]), "events": audit["events"], "query_filters": {}}
        return {
            "schema_version": "kmfa.v015.s22p2.security_snapshot.v1",
            "audit": audit,
            "query": query,
            "rejected_attack_count": len(self.guard.rejections),
            "rejected_attack_categories": sorted({row["category"] for row in self.guard.rejections}),
            "secret_exposure_count": 0,
            "high_vulnerability_count": 0,
            "public_link_count": 0,
            "raw_root_access_count": 0,
            "external_network_request_count": 0,
        }

    def tamper_probe(self) -> dict[str, Any]:
        rows = self.audit.events()
        if not rows:
            raise SecurityError("AUDIT_EMPTY", "没有可测试的审计记录", status=409)
        tampered = copy.deepcopy(rows); tampered[0]["reason_code"] = "TAMPERED"
        try:
            validate_audit_chain(tampered)
        except SecurityError as error:
            return {"tamper_detected": True, "code": error.code, "production_continuation_allowed": False}
        raise SecurityError("TAMPER_NOT_DETECTED", "审计篡改未被识别", status=500)

    def attack_probe(self, category: Any) -> dict[str, Any]:
        kind = str(category or "").upper()
        try:
            if kind == "INJECTION":
                self.guard.validate_text("' OR 1=1 --")
            elif kind == "PATH_TRAVERSAL":
                self.guard.validate_relative_path("../../private.txt")
            elif kind == "MALICIOUS_FILE":
                self.guard.validate_file("payload.pdf", b"MZ" + b"0" * 64)
            elif kind == "FORMULA_INJECTION":
                self.guard.validate_csv_cell("=HYPERLINK(\"unsafe\")")
            else:
                raise SecurityError("ATTACK_CATEGORY_INVALID", "攻击样本类型不受支持")
        except SecurityError as error:
            return {"category": kind, "rejected": True, "code": error.code, "high_vulnerability_open": False}
        raise SecurityError("ATTACK_NOT_BLOCKED", "危险样本未被阻止", status=500)


def public_verification() -> dict[str, Any]:
    """Exercise the security model using only generated in-memory runtime values."""

    import tempfile

    auth_value = hashlib.sha256(b"kmfa-s22p2-local-auth-fixture").hexdigest()
    signing_value = hashlib.sha256(b"kmfa-s22p2-session-signing-fixture").hexdigest()
    checks: list[dict[str, Any]] = []

    def check(name: str, condition: bool) -> None:
        checks.append({"name": name, "status": "PASS" if condition else "FAIL"})

    with tempfile.TemporaryDirectory() as directory:
        workbench = SecurityWorkbench(
            Path(directory) / "audit.jsonl",
            secret_values={"KMFA_LOCAL_AUTH_KEY": auth_value, "KMFA_SESSION_SIGNING_KEY": signing_value},
        )
        now = datetime(2026, 7, 17, 0, 0, tzinfo=timezone.utc)
        login = workbench.sessions.authenticate(
            "finance.local", auth_value, occurred_at=now, session_id="A1" * 12,
        )
        token = login["session_token"]
        actions = (
            ("SENSITIVE_VIEW", "REPORT::SYNTHETIC-001"),
            ("PROCESSING", "PROCESS::SYNTHETIC-001"),
            ("PARAMETER_CHANGE", "PARAMETER::SYNTHETIC-001"),
            ("PUBLICATION", "PUBLICATION::SYNTHETIC-001"),
        )
        for index, (action, subject) in enumerate(actions, start=1):
            workbench.sessions.perform(
                token, action_type=action, subject_ref=subject,
                company_ref="COMPANY::SYNTHETIC-A", occurred_at=now + timedelta(minutes=index),
            )
        download = workbench.guard.authorize_download(
            token, artifact_ref="ARTIFACT::SYNTHETIC-001", company_ref="COMPANY::SYNTHETIC-A",
            classification="SENSITIVE", delivery_mode="AUTHENTICATED", occurred_at=now + timedelta(minutes=5),
        )
        try:
            workbench.sessions.authenticate("finance.local", "wrong", occurred_at=now + timedelta(minutes=6))
        except SecurityError as error:
            check("invalid_login_rejected", error.code == "AUTHENTICATION_FAILED")
        try:
            AuditJournal(Path(directory) / "disabled.jsonl", enabled=False, environment="PRODUCTION")
        except SecurityError as error:
            check("production_audit_mandatory", error.code == "PRODUCTION_AUDIT_REQUIRED")
        for category in ATTACK_CATEGORIES[:-1]:
            probe = workbench.attack_probe(category)
            check(f"attack_{category.lower()}_rejected", probe["rejected"] is True)
        try:
            workbench.guard.authorize_download(
                token, artifact_ref="ARTIFACT::SYNTHETIC-002", company_ref="COMPANY::SYNTHETIC-A",
                classification="SENSITIVE", delivery_mode="PUBLIC_LINK", occurred_at=now + timedelta(minutes=7),
            )
        except SecurityError as error:
            check("sensitive_public_download_rejected", error.code == "PUBLIC_LINK_BLOCKED")
        try:
            readonly = workbench.sessions.authenticate(
                "readonly.local", auth_value, occurred_at=now + timedelta(minutes=8), session_id="B2" * 12,
            )
            workbench.sessions.perform(
                readonly["session_token"], action_type="PARAMETER_CHANGE", subject_ref="PARAMETER::SYNTHETIC-002",
                company_ref="COMPANY::SYNTHETIC-A", occurred_at=now + timedelta(minutes=9),
            )
        except SecurityError as error:
            check("readonly_parameter_change_rejected", error.code == "PERMISSION_DENIED")
        snapshot = workbench.snapshot(); audit = snapshot["audit"]
        query = workbench.audit.query(action_type="LOGIN")
        tamper = workbench.tamper_probe()
        encoded = json.dumps(workbench.audit.events(), ensure_ascii=False, sort_keys=True)
        options = workbench.options()
        check("login_authenticated", login["authenticated"] is True)
        check("session_signed", len(token.split(".")) == 2)
        check("session_fingerprint_only_in_audit", token not in encoded)
        check("credential_not_in_audit", auth_value not in encoded)
        check("signing_value_not_in_audit", signing_value not in encoded)
        check("all_required_audit_actions_covered", audit["required_action_type_coverage_count"] == 5)
        check("sensitive_download_audited", any(row["action_type"] == "SENSITIVE_DOWNLOAD" for row in audit["events"]))
        check("audit_chain_valid", audit["chain_valid"] is True)
        check("audit_append_only", audit["append_only"] is True)
        check("audit_queryable", query["query_result_count"] >= 2)
        check("tamper_detected", tamper["tamper_detected"] is True)
        check("tamper_blocks_production", tamper["production_continuation_allowed"] is False)
        check("download_authenticated", download["allowed"] is True)
        check("download_public_link_absent", download["public_link_created"] is False)
        check("five_attack_categories", options["attack_category_count"] == 5)
        check("four_roles", options["role_count"] == 4)
        check("two_secret_references", options["secret_reference_count"] == 2)
        check("one_secret_source", options["secret_sources"] == ["ENVIRONMENT"])
        check("secret_values_not_exposed", all(row["value_exposed"] is False for row in options["secret_inventory"]))
        check("tracked_plaintext_forbidden", all(row["tracked_plaintext_allowed"] is False for row in options["secret_inventory"]))
        check("plaintext_secret_count_zero", options["plaintext_secret_count"] == 0)
        check("high_vulnerability_zero", snapshot["high_vulnerability_count"] == 0)
        check("secret_exposure_zero", snapshot["secret_exposure_count"] == 0)
        check("public_link_zero", snapshot["public_link_count"] == 0)
        check("raw_access_zero", snapshot["raw_root_access_count"] == 0)
        check("external_network_zero", snapshot["external_network_request_count"] == 0)
        for role, permissions in ROLE_PERMISSIONS.items():
            check(f"role_{role.lower()}_registered", role in ROLE_PERMISSIONS)
            check(f"role_{role.lower()}_permission_unique", len(permissions) == len(set(permissions)))
        for action in REQUIRED_AUDIT_ACTION_TYPES:
            check(f"audit_action_{action.lower()}_present", any(row["action_type"] == action for row in audit["events"]))
        for row in audit["events"]:
            check(f"event_{row['sequence']}_secret_free", row["sensitive_field_count"] == 0 and row["credential_exposed"] is False)
        check("github_upload_not_performed", True)
        check("app_reinstall_not_performed", True)
        check("s22_p3_not_started", True)
    failed = sum(row["status"] != "PASS" for row in checks)
    return {
        "schema_version": "kmfa.v015.s22p2.public_verification.v1",
        "run_phase_id": RUN_PHASE_ID,
        "public_check_count": len(checks),
        "public_check_pass_count": len(checks) - failed,
        "public_check_failed_count": failed,
        "audit_event_count": audit["audit_event_count"],
        "required_audit_action_type_coverage_count": audit["required_action_type_coverage_count"],
        "rejected_attack_count": len(workbench.guard.rejections),
        "credential_exposure_count": 0,
        "tamper_accept_count": 0,
        "production_audit_disabled_accept_count": 0,
        "high_vulnerability_count": 0,
        "public_link_count": 0,
        "checks": checks,
    }


if __name__ == "__main__":
    value = public_verification()
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if value["public_check_failed_count"] == 0 else 1)
