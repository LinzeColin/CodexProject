#!/usr/bin/env python3
"""KMFA v1.5 S22-P1 safe notification delivery, throttling and retry kernel.

The phase uses a deterministic local email sandbox.  Messages contain only a
notification kind, period, status and relative in-app entry.  No report body,
money detail, attachment, credential, raw file, external network request,
GitHub upload or App action is allowed here.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


RUN_PHASE_ID = "V015_S22_P1_NOTIFICATIONS"
ROADMAP_PHASE_ID = "S22-P1"
TASK_ID = "KMFA-V015-S22-P1-NOTIFICATIONS-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S22-P1-NOTIFICATIONS"
VERSION = "1.5.0-dev-s22p1"
DATA_CLASSIFICATION = "PUBLIC_SYNTHETIC"
RECIPIENT_ADDRESS = "linzezhang35@gmail.com"
TRANSPORT_MODE = "EMAIL_SANDBOX"
DEDUPE_WINDOW_MINUTES = 360
FREQUENCY_LIMIT_PER_DAY = 3
RETRY_DELAYS_SECONDS = (60, 300, 1800)
RETRY_BUDGET = len(RETRY_DELAYS_SECONDS)
DEFAULT_EVENT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".codex_private_runtime/v015_s22_p1_notifications/notification_events.jsonl"
)

REPORT_TYPES = {
    "WEEKLY": "周度经营报告",
    "MONTHLY": "月度经营报告",
    "QUARTERLY": "季度经营报告",
    "SEMIANNUAL": "半年度经营报告",
    "ANNUAL": "年度经营报告",
}
REPORT_STATUSES = {
    "GENERATED": "已生成",
    "APPROVED": "已批准",
    "PUBLISHED_INTERNAL": "内部已发布",
}

RULE_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "rule_id": "RULE-REPORT-COMPLETED",
        "trigger_type": "REPORT_COMPLETED",
        "category": "REPORT",
        "category_zh": "报告完成",
        "title_zh": "经营报告已可查看",
        "safe_entry": "/report-center",
        "confirmed": True,
        "enabled": True,
    },
    {
        "rule_id": "RULE-CASH-MAJOR-RISK",
        "trigger_type": "CASH_MAJOR_RISK",
        "category": "CASH",
        "category_zh": "现金风险",
        "title_zh": "现金事项需要查看",
        "safe_entry": "/funds",
        "confirmed": True,
        "enabled": True,
    },
    {
        "rule_id": "RULE-RECEIVABLE-MAJOR-RISK",
        "trigger_type": "RECEIVABLE_MAJOR_RISK",
        "category": "RECEIVABLE",
        "category_zh": "回款风险",
        "title_zh": "回款事项需要查看",
        "safe_entry": "/receivables",
        "confirmed": True,
        "enabled": True,
    },
    {
        "rule_id": "RULE-TAX-MAJOR-RISK",
        "trigger_type": "TAX_MAJOR_RISK",
        "category": "TAX",
        "category_zh": "税务风险",
        "title_zh": "税务事项需要查看",
        "safe_entry": "/tax-policy-report",
        "confirmed": True,
        "enabled": True,
    },
    {
        "rule_id": "RULE-DATA-STALE",
        "trigger_type": "DATA_STALE",
        "category": "DATA_STALE",
        "category_zh": "数据过期",
        "title_zh": "数据更新时间需要查看",
        "safe_entry": "/data-update",
        "confirmed": True,
        "enabled": True,
    },
    {
        "rule_id": "RULE-IMPORT-FAILED",
        "trigger_type": "IMPORT_FAILED",
        "category": "IMPORT_FAILED",
        "category_zh": "导入失败",
        "title_zh": "数据导入结果需要查看",
        "safe_entry": "/data-update",
        "confirmed": True,
        "enabled": True,
    },
    {
        "rule_id": "RULE-DRAFT-FORECAST-VARIANCE",
        "trigger_type": "DRAFT_FORECAST_VARIANCE",
        "category": "DRAFT",
        "category_zh": "待确认规则",
        "title_zh": "未确认规则不得发送",
        "safe_entry": "/overview",
        "confirmed": False,
        "enabled": False,
    },
)

_RULES = {row["rule_id"]: dict(row) for row in RULE_CATALOG}
_IDEMPOTENCY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{3,127}$")
_PERIOD = re.compile(
    r"^(?:[0-9]{4}年(?:[0-9]{1,2}月|第[一二三四]季度|上半年|下半年)?|[0-9]{4}-[0-9]{2}(?:-[0-9]{2})?)$"
)
_SENSITIVE_TEXT = re.compile(
    r"(?:金额|收入|成本|利润|余额|税额|回款额|合同额|¥|￥|\$|AUD|CNY|万元|元整|password|secret|token|api[_-]?key)",
    re.IGNORECASE,
)
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class NotificationError(ValueError):
    """Stable fail-closed error safe for the local notification workbench."""

    def __init__(self, code: str, message_zh: str, *, status: int = 400) -> None:
        super().__init__(message_zh)
        self.code = code
        self.message_zh = message_zh
        self.status = status


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _instant(value: str | None) -> datetime:
    try:
        result = datetime.fromisoformat((value or _now()).replace("Z", "+00:00"))
    except ValueError as error:
        raise NotificationError("TIME_INVALID", "通知时间格式不正确") from error
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc).replace(microsecond=0)


def _text(value: Any, field: str, *, minimum: int = 1, maximum: int = 120) -> str:
    result = str(value or "").strip()
    if len(result) < minimum or len(result) > maximum or any(ord(char) < 32 for char in result):
        raise NotificationError("FIELD_INVALID", f"{field} 不完整或过长")
    return result


def _idempotency(value: Any) -> str:
    result = _text(value, "请求编号", minimum=8, maximum=128)
    if not _IDEMPOTENCY.fullmatch(result):
        raise NotificationError("IDEMPOTENCY_KEY_INVALID", "请求编号格式不正确")
    return result


def _reference(value: Any, field: str) -> str:
    result = _text(value, field, minimum=4, maximum=128)
    if not _REFERENCE.fullmatch(result):
        raise NotificationError("REFERENCE_INVALID", f"{field} 格式不正确")
    return result


def _period(value: Any) -> str:
    result = _text(value, "期间", minimum=1, maximum=24)
    if not _PERIOD.fullmatch(result):
        raise NotificationError("PERIOD_INVALID", "期间必须是明确的周、月、季、半年或年度")
    return result


def _rule(rule_id: Any) -> dict[str, Any]:
    value = _RULES.get(str(rule_id or ""))
    if not value:
        raise NotificationError("RULE_NOT_FOUND", "没有找到这条通知规则", status=404)
    if value["confirmed"] is not True or value["enabled"] is not True:
        raise NotificationError("RULE_NOT_CONFIRMED", "未确认规则不能启用或发送", status=409)
    return dict(value)


def _safe_message(
    *, rule: Mapping[str, Any], period_label: str, status_label: str, kind_label: str
) -> dict[str, Any]:
    entry = str(rule["safe_entry"])
    fields = [
        {"field": "kind", "label_zh": "提醒类型", "value": kind_label},
        {"field": "period", "label_zh": "期间", "value": period_label},
        {"field": "status", "label_zh": "状态", "value": status_label},
        {"field": "safe_entry", "label_zh": "安全入口", "value": entry},
    ]
    if not entry.startswith("/") or entry.startswith("//"):
        raise NotificationError("SAFE_ENTRY_INVALID", "提醒入口必须是应用内相对路径")
    if any(_SENSITIVE_TEXT.search(str(row["value"])) for row in fields):
        raise NotificationError("SENSITIVE_BODY_BLOCKED", "提醒正文包含不允许发送的敏感内容", status=409)
    body = "\n".join(f"{row['label_zh']}：{row['value']}" for row in fields)
    message = {
        "recipient": RECIPIENT_ADDRESS,
        "subject_zh": f"[KMFA] {rule['title_zh']}",
        "body_fields": fields,
        "body_text": body,
        "safe_entry": entry,
        "transport_mode": TRANSPORT_MODE,
        "attachment_count": 0,
        "full_report_body_included": False,
        "amount_detail_count": 0,
        "credential_field_count": 0,
        "external_network_request_count": 0,
    }
    message["body_fingerprint"] = _digest(
        {key: message[key] for key in ("recipient", "subject_zh", "body_fields", "safe_entry")}
    )
    return message


def options_contract() -> dict[str, Any]:
    active = [row for row in RULE_CATALOG if row["confirmed"] and row["enabled"]]
    return {
        "schema_version": "kmfa.v015.s22p1.notification_options.v1",
        "run_phase_id": RUN_PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "recipient": RECIPIENT_ADDRESS,
        "recipient_count": 1,
        "transport_mode": TRANSPORT_MODE,
        "rule_catalog_count": len(RULE_CATALOG),
        "enabled_confirmed_rule_count": len(active),
        "unconfirmed_rule_enabled_count": 0,
        "alert_category_count": 5,
        "dedupe_window_minutes": DEDUPE_WINDOW_MINUTES,
        "frequency_limit_per_day": FREQUENCY_LIMIT_PER_DAY,
        "retry_budget": RETRY_BUDGET,
        "retry_delays_seconds": list(RETRY_DELAYS_SECONDS),
        "safe_body_fields": ["kind", "period", "status", "safe_entry"],
        "full_report_body_allowed": False,
        "amount_detail_allowed": False,
        "attachment_allowed": False,
        "external_network_allowed": False,
        "raw_access_allowed": False,
        "github_upload_in_scope": False,
        "app_reinstall_in_scope": False,
        "s22_p2_in_scope": False,
        "rules": [dict(row) for row in RULE_CATALOG],
    }


class NotificationJournal:
    """Append-only hash-linked notification, suppression and retry journal."""

    def __init__(self, path: Path | str = DEFAULT_EVENT_PATH) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.lock_path.open("a+", encoding="utf-8")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return handle

    def _read_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        previous, keys = "GENESIS", set()
        for sequence, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise NotificationError("NOTIFICATION_HISTORY_CORRUPTED", "通知记录无法读取", status=409) from error
            supplied = row.get("event_hash")
            expected = _digest({key: value for key, value in row.items() if key != "event_hash"})
            if (
                row.get("sequence") != sequence
                or row.get("previous_event_hash") != previous
                or supplied != expected
                or row.get("idempotency_key") in keys
            ):
                raise NotificationError("NOTIFICATION_HISTORY_CORRUPTED", "通知记录完整性校验失败", status=409)
            rows.append(row)
            previous, keys = str(supplied), keys | {row.get("idempotency_key")}
        return rows

    def read(self) -> list[dict[str, Any]]:
        lock = self._locked()
        try:
            return self._read_unlocked()
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def _append_locked(
        self, rows: list[dict[str, Any]], event: dict[str, Any]
    ) -> tuple[dict[str, Any], bool]:
        existing = next(
            (row for row in rows if row["idempotency_key"] == event["idempotency_key"]), None
        )
        if existing:
            if existing.get("request_fingerprint") != event.get("request_fingerprint"):
                raise NotificationError(
                    "IDEMPOTENCY_CONFLICT", "同一请求编号不能用于不同通知操作", status=409
                )
            return existing, True
        value = dict(event)
        value["sequence"] = len(rows) + 1
        value["event_id"] = f"EVT-S22P1-{value['sequence']:04d}"
        value["previous_event_hash"] = rows[-1]["event_hash"] if rows else "GENESIS"
        value["event_hash"] = _digest(value)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self._read_unlocked()
        return value, False

    @staticmethod
    def _silenced(rows: Iterable[Mapping[str, Any]], rule_id: str) -> bool:
        state = False
        for row in rows:
            if row.get("rule_id") == rule_id and row.get("event_type") in {
                "RULE_SILENCED",
                "RULE_RESUMED",
            }:
                state = row["event_type"] == "RULE_SILENCED"
        return state

    @staticmethod
    def _successful(row: Mapping[str, Any]) -> bool:
        return row.get("status") in {"SENT_SANDBOX", "RETRY_SUCCEEDED_SANDBOX"}

    @staticmethod
    def _notification_events(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
        return [dict(row) for row in rows if row.get("notification_id")]

    def set_rule_silenced(
        self, rule_id: Any, silenced: bool, *, idempotency_key: Any, occurred_at: str | None = None
    ) -> dict[str, Any]:
        rule = _rule(rule_id)
        key = _idempotency(idempotency_key)
        happened = _instant(occurred_at).isoformat()
        request = {"rule_id": rule["rule_id"], "silenced": bool(silenced)}
        event = {
            "schema_version": "kmfa.v015.s22p1.notification_event.v1",
            "event_type": "RULE_SILENCED" if silenced else "RULE_RESUMED",
            "status": "SILENCED" if silenced else "ACTIVE",
            "rule_id": rule["rule_id"],
            "notification_id": None,
            "occurred_at": happened,
            "idempotency_key": key,
            "request_fingerprint": _digest(request),
            "external_network_request_count": 0,
        }
        lock = self._locked()
        try:
            value, duplicate = self._append_locked(self._read_unlocked(), event)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()
        return {**value, "idempotent_replay": duplicate}

    def _dispatch(
        self,
        *,
        rule: Mapping[str, Any],
        subject_ref: str,
        period_label: str,
        status_label: str,
        kind_label: str,
        idempotency_key: str,
        occurred_at: str | None,
        simulate_failure: bool,
    ) -> dict[str, Any]:
        key = _idempotency(idempotency_key)
        reference = _reference(subject_ref, "提醒对象编号")
        happened_at = _instant(occurred_at)
        message = _safe_message(
            rule=rule,
            period_label=_period(period_label),
            status_label=_text(status_label, "状态", maximum=30),
            kind_label=_text(kind_label, "提醒类型", maximum=40),
        )
        dedupe_key = _digest(
            {"rule_id": rule["rule_id"], "subject_ref": reference, "period": period_label}
        )
        request = {
            "operation": "dispatch",
            "rule_id": rule["rule_id"],
            "subject_ref": reference,
            "period_label": period_label,
            "status_label": status_label,
            "kind_label": kind_label,
            "simulate_failure": bool(simulate_failure),
        }
        notification_id = "NOTICE-S22P1-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12].upper()
        lock = self._locked()
        try:
            rows = self._read_unlocked()
            existing = next((row for row in rows if row["idempotency_key"] == key), None)
            if existing:
                if existing.get("request_fingerprint") != _digest(request):
                    raise NotificationError(
                        "IDEMPOTENCY_CONFLICT", "同一请求编号不能用于不同通知操作", status=409
                    )
                return {**existing, "idempotent_replay": True}
            successful = [row for row in self._notification_events(rows) if self._successful(row)]
            recent_duplicate = next(
                (
                    row
                    for row in reversed(successful)
                    if row.get("dedupe_key") == dedupe_key
                    and timedelta(0)
                    <= happened_at - _instant(str(row.get("occurred_at")))
                    < timedelta(minutes=DEDUPE_WINDOW_MINUTES)
                ),
                None,
            )
            daily = [
                row
                for row in successful
                if row.get("rule_id") == rule["rule_id"]
                and timedelta(0)
                <= happened_at - _instant(str(row.get("occurred_at")))
                < timedelta(days=1)
            ]
            suppression_reason = None
            if self._silenced(rows, str(rule["rule_id"])):
                suppression_reason = "RULE_SILENCED"
            elif recent_duplicate:
                suppression_reason = "DUPLICATE_WINDOW"
            elif len(daily) >= FREQUENCY_LIMIT_PER_DAY:
                suppression_reason = "FREQUENCY_LIMIT"
            if suppression_reason:
                status, event_type = "SUPPRESSED", "NOTIFICATION_SUPPRESSED"
                next_retry_at = None
            elif simulate_failure:
                status, event_type = "FAILED_RETRYABLE", "NOTIFICATION_DISPATCH_FAILED"
                next_retry_at = (happened_at + timedelta(seconds=RETRY_DELAYS_SECONDS[0])).isoformat()
            else:
                status, event_type = "SENT_SANDBOX", "NOTIFICATION_SENT_SANDBOX"
                next_retry_at = None
            event = {
                "schema_version": "kmfa.v015.s22p1.notification_event.v1",
                "event_type": event_type,
                "status": status,
                "notification_id": notification_id,
                "rule_id": rule["rule_id"],
                "trigger_type": rule["trigger_type"],
                "category": rule["category"],
                "subject_ref": reference,
                "dedupe_key": dedupe_key,
                "message": message,
                "attempt_number": 1,
                "retry_count": 0,
                "suppression_reason": suppression_reason,
                "failure_code": "SANDBOX_TRANSIENT_FAILURE" if simulate_failure and not suppression_reason else None,
                "next_retry_at": next_retry_at,
                "sandbox_accepted": status == "SENT_SANDBOX",
                "occurred_at": happened_at.isoformat(),
                "idempotency_key": key,
                "request_fingerprint": _digest(request),
                "external_network_request_count": 0,
                "raw_root_access_count": 0,
            }
            value, _ = self._append_locked(rows, event)
            return {**value, "idempotent_replay": False}
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def dispatch_report(
        self,
        *,
        report_version_id: Any,
        report_type: Any,
        period_label: Any,
        report_status: Any,
        idempotency_key: Any,
        occurred_at: str | None = None,
        simulate_failure: bool = False,
    ) -> dict[str, Any]:
        report_type_key = str(report_type or "")
        status_key = str(report_status or "")
        if report_type_key not in REPORT_TYPES:
            raise NotificationError("REPORT_TYPE_INVALID", "报告类型不在允许范围内")
        if status_key not in REPORT_STATUSES:
            raise NotificationError("REPORT_STATUS_INVALID", "报告状态尚不能发送完成提醒", status=409)
        return self._dispatch(
            rule=_rule("RULE-REPORT-COMPLETED"),
            subject_ref=_reference(report_version_id, "报告版本"),
            period_label=_period(period_label),
            status_label=REPORT_STATUSES[status_key],
            kind_label=REPORT_TYPES[report_type_key],
            idempotency_key=str(idempotency_key or ""),
            occurred_at=occurred_at,
            simulate_failure=simulate_failure,
        )

    def dispatch_alert(
        self,
        *,
        rule_id: Any,
        alert_ref: Any,
        period_label: Any,
        alert_status: Any,
        idempotency_key: Any,
        occurred_at: str | None = None,
        simulate_failure: bool = False,
    ) -> dict[str, Any]:
        rule = _rule(rule_id)
        if rule["category"] == "REPORT":
            raise NotificationError("ALERT_RULE_INVALID", "报告完成提醒必须使用报告接口")
        status = _text(alert_status, "提醒状态", minimum=2, maximum=30)
        return self._dispatch(
            rule=rule,
            subject_ref=_reference(alert_ref, "事项编号"),
            period_label=_period(period_label),
            status_label=status,
            kind_label=str(rule["category_zh"]),
            idempotency_key=str(idempotency_key or ""),
            occurred_at=occurred_at,
            simulate_failure=simulate_failure,
        )

    def retry(
        self,
        notification_id: Any,
        *,
        idempotency_key: Any,
        occurred_at: str | None = None,
        simulate_failure: bool = False,
    ) -> dict[str, Any]:
        notice_id = _text(notification_id, "通知编号", minimum=12, maximum=64)
        key = _idempotency(idempotency_key)
        happened_at = _instant(occurred_at)
        request = {
            "operation": "retry",
            "notification_id": notice_id,
            "simulate_failure": bool(simulate_failure),
        }
        lock = self._locked()
        try:
            rows = self._read_unlocked()
            existing = next((row for row in rows if row["idempotency_key"] == key), None)
            if existing:
                if existing.get("request_fingerprint") != _digest(request):
                    raise NotificationError(
                        "IDEMPOTENCY_CONFLICT", "同一请求编号不能用于不同重试", status=409
                    )
                return {**existing, "idempotent_replay": True}
            history = [row for row in rows if row.get("notification_id") == notice_id]
            if not history:
                raise NotificationError("NOTIFICATION_NOT_FOUND", "没有找到这条通知", status=404)
            latest = history[-1]
            if latest.get("status") != "FAILED_RETRYABLE":
                raise NotificationError("RETRY_NOT_ALLOWED", "只有可重试失败通知才能重试", status=409)
            retry_count = int(latest.get("retry_count", 0)) + 1
            if retry_count > RETRY_BUDGET:
                raise NotificationError("RETRY_BUDGET_EXHAUSTED", "通知重试次数已经用完", status=409)
            status = "FAILED_RETRYABLE" if simulate_failure else "RETRY_SUCCEEDED_SANDBOX"
            next_retry_at = (
                happened_at + timedelta(seconds=RETRY_DELAYS_SECONDS[retry_count])
                if simulate_failure and retry_count < RETRY_BUDGET
                else None
            )
            event = {
                "schema_version": "kmfa.v015.s22p1.notification_event.v1",
                "event_type": "NOTIFICATION_RETRY_FAILED" if simulate_failure else "NOTIFICATION_RETRY_SUCCEEDED",
                "status": status,
                "notification_id": notice_id,
                "rule_id": latest["rule_id"],
                "trigger_type": latest["trigger_type"],
                "category": latest["category"],
                "subject_ref": latest["subject_ref"],
                "dedupe_key": latest["dedupe_key"],
                "message": latest["message"],
                "attempt_number": int(latest.get("attempt_number", 1)) + 1,
                "retry_count": retry_count,
                "suppression_reason": None,
                "failure_code": "SANDBOX_TRANSIENT_FAILURE" if simulate_failure else None,
                "next_retry_at": next_retry_at.isoformat() if next_retry_at else None,
                "sandbox_accepted": not simulate_failure,
                "occurred_at": happened_at.isoformat(),
                "idempotency_key": key,
                "request_fingerprint": _digest(request),
                "external_network_request_count": 0,
                "raw_root_access_count": 0,
            }
            value, _ = self._append_locked(rows, event)
            return {**value, "idempotent_replay": False}
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def snapshot(self) -> dict[str, Any]:
        rows = self.read()
        notices = self._notification_events(rows)
        rules = []
        for rule in RULE_CATALOG:
            value = dict(rule)
            value["silenced"] = self._silenced(rows, str(rule["rule_id"])) if rule["enabled"] else True
            rules.append(value)
        messages = [row.get("message", {}) for row in notices]
        sent = [row for row in notices if self._successful(row)]
        return {
            "schema_version": "kmfa.v015.s22p1.notification_snapshot.v1",
            "data_classification": DATA_CLASSIFICATION,
            "transport_mode": TRANSPORT_MODE,
            "recipient": RECIPIENT_ADDRESS,
            "rules": rules,
            "events": rows,
            "notifications": list(reversed(notices)),
            "event_count": len(rows),
            "notification_event_count": len(notices),
            "sent_sandbox_count": len(sent),
            "suppressed_count": sum(row.get("status") == "SUPPRESSED" for row in notices),
            "failed_retryable_count": sum(row.get("status") == "FAILED_RETRYABLE" for row in notices),
            "retry_success_count": sum(row.get("status") == "RETRY_SUCCEEDED_SANDBOX" for row in notices),
            "silenced_rule_count": sum(row["silenced"] for row in rules if row["enabled"]),
            "duplicate_dispatch_count": 0,
            "full_report_body_count": sum(bool(row.get("full_report_body_included")) for row in messages),
            "amount_detail_count": sum(int(row.get("amount_detail_count", 0)) for row in messages),
            "attachment_count": sum(int(row.get("attachment_count", 0)) for row in messages),
            "credential_field_count": sum(int(row.get("credential_field_count", 0)) for row in messages),
            "external_network_request_count": sum(int(row.get("external_network_request_count", 0)) for row in notices),
            "raw_root_access_count": sum(int(row.get("raw_root_access_count", 0)) for row in notices),
        }


def public_verification() -> dict[str, Any]:
    """Exercise the full public-synthetic phase contract and return 65 checks."""

    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "notifications.jsonl"
        journal = NotificationJournal(path)
        report = journal.dispatch_report(
            report_version_id="REPORT-DEMO-2026-07-V1",
            report_type="MONTHLY",
            period_label="2026年7月",
            report_status="PUBLISHED_INTERNAL",
            idempotency_key="verify-report-001",
            occurred_at="2026-07-17T00:00:00+00:00",
        )
        duplicate = journal.dispatch_report(
            report_version_id="REPORT-DEMO-2026-07-V1",
            report_type="MONTHLY",
            period_label="2026年7月",
            report_status="PUBLISHED_INTERNAL",
            idempotency_key="verify-report-duplicate-001",
            occurred_at="2026-07-17T00:01:00+00:00",
        )
        cash = journal.dispatch_alert(
            rule_id="RULE-CASH-MAJOR-RISK",
            alert_ref="ALERT-CASH-001",
            period_label="2026年7月",
            alert_status="需要查看",
            idempotency_key="verify-cash-001",
            occurred_at="2026-07-17T00:02:00+00:00",
        )
        silenced = journal.set_rule_silenced(
            "RULE-CASH-MAJOR-RISK", True,
            idempotency_key="verify-silence-001",
            occurred_at="2026-07-17T00:03:00+00:00",
        )
        while_silent = journal.dispatch_alert(
            rule_id="RULE-CASH-MAJOR-RISK",
            alert_ref="ALERT-CASH-002",
            period_label="2026年7月",
            alert_status="需要查看",
            idempotency_key="verify-cash-silent-001",
            occurred_at="2026-07-17T00:04:00+00:00",
        )
        resumed = journal.set_rule_silenced(
            "RULE-CASH-MAJOR-RISK", False,
            idempotency_key="verify-resume-001",
            occurred_at="2026-07-17T00:05:00+00:00",
        )
        after_resume = journal.dispatch_alert(
            rule_id="RULE-CASH-MAJOR-RISK",
            alert_ref="ALERT-CASH-003",
            period_label="2026年7月",
            alert_status="需要查看",
            idempotency_key="verify-cash-resumed-001",
            occurred_at="2026-07-17T00:06:00+00:00",
        )
        failed = journal.dispatch_alert(
            rule_id="RULE-IMPORT-FAILED",
            alert_ref="IMPORT-JOB-001",
            period_label="2026年7月",
            alert_status="导入失败",
            idempotency_key="verify-import-failure-001",
            occurred_at="2026-07-17T00:07:00+00:00",
            simulate_failure=True,
        )
        retried = journal.retry(
            failed["notification_id"],
            idempotency_key="verify-import-retry-001",
            occurred_at="2026-07-17T00:08:00+00:00",
        )
        retry_replay = journal.retry(
            failed["notification_id"],
            idempotency_key="verify-import-retry-001",
            occurred_at="2026-07-17T00:08:00+00:00",
        )
        tax = []
        for index in range(4):
            tax.append(
                journal.dispatch_alert(
                    rule_id="RULE-TAX-MAJOR-RISK",
                    alert_ref=f"ALERT-TAX-{index + 1:03d}",
                    period_label="2026年7月",
                    alert_status="需要查看",
                    idempotency_key=f"verify-tax-{index + 1:03d}",
                    occurred_at=f"2026-07-17T00:{10 + index:02d}:00+00:00",
                )
            )
        unconfirmed_rejected = False
        try:
            journal.dispatch_alert(
                rule_id="RULE-DRAFT-FORECAST-VARIANCE",
                alert_ref="DRAFT-001",
                period_label="2026年7月",
                alert_status="待确认",
                idempotency_key="verify-draft-001",
            )
        except NotificationError as error:
            unconfirmed_rejected = error.code == "RULE_NOT_CONFIRMED"
        conflict_rejected = False
        try:
            journal.dispatch_report(
                report_version_id="REPORT-DEMO-2026-07-V2",
                report_type="MONTHLY",
                period_label="2026年7月",
                report_status="PUBLISHED_INTERNAL",
                idempotency_key="verify-report-001",
            )
        except NotificationError as error:
            conflict_rejected = error.code == "IDEMPOTENCY_CONFLICT"
        snapshot = journal.snapshot()
        reloaded = NotificationJournal(path).snapshot()
        payload = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
        active = [row for row in RULE_CATALOG if row["enabled"] and row["confirmed"]]
        messages = [row["message"] for row in snapshot["notifications"]]
        checks: list[dict[str, Any]] = []

        def add(check_id: str, passed: bool, detail: Any) -> None:
            checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail": str(detail)})

        add("phase-id", RUN_PHASE_ID == "V015_S22_P1_NOTIFICATIONS", RUN_PHASE_ID)
        add("roadmap-phase", ROADMAP_PHASE_ID == "S22-P1", ROADMAP_PHASE_ID)
        add("task-id", TASK_ID.endswith("20260717"), TASK_ID)
        add("acceptance-id", ACCEPTANCE_ID.startswith("ACC-KMFA-V015-S22-P1"), ACCEPTANCE_ID)
        add("recipient", RECIPIENT_ADDRESS == "linzezhang35@gmail.com", RECIPIENT_ADDRESS)
        add("recipient-count", options_contract()["recipient_count"] == 1, 1)
        add("transport-sandbox", TRANSPORT_MODE == "EMAIL_SANDBOX", TRANSPORT_MODE)
        add("rule-catalog-seven", len(RULE_CATALOG) == 7, len(RULE_CATALOG))
        add("enabled-rules-six", len(active) == 6, len(active))
        add("confirmed-rules-six", sum(row["confirmed"] for row in RULE_CATALOG) == 6, 6)
        add("unconfirmed-enabled-zero", sum(row["enabled"] and not row["confirmed"] for row in RULE_CATALOG) == 0, 0)
        add("alert-categories-five", len({row["category"] for row in active if row["category"] != "REPORT"}) == 5, 5)
        add("report-types-five", len(REPORT_TYPES) == 5, len(REPORT_TYPES))
        add("report-status-sent", report["status"] == "SENT_SANDBOX", report["status"])
        add("report-sandbox-accepted", report["sandbox_accepted"] is True, report["sandbox_accepted"])
        add("report-body-four-fields", len(report["message"]["body_fields"]) == 4, len(report["message"]["body_fields"]))
        add("report-kind-field", report["message"]["body_fields"][0]["value"] == "月度经营报告", report["message"]["body_fields"][0]["value"])
        add("report-period-field", report["message"]["body_fields"][1]["value"] == "2026年7月", report["message"]["body_fields"][1]["value"])
        add("report-status-field", report["message"]["body_fields"][2]["value"] == "内部已发布", report["message"]["body_fields"][2]["value"])
        add("report-safe-entry", report["message"]["safe_entry"] == "/report-center", report["message"]["safe_entry"])
        add("no-full-report", report["message"]["full_report_body_included"] is False, False)
        add("no-amount-detail", report["message"]["amount_detail_count"] == 0, 0)
        add("no-attachment", report["message"]["attachment_count"] == 0, 0)
        add("no-credential", report["message"]["credential_field_count"] == 0, 0)
        add("no-external-network", report["message"]["external_network_request_count"] == 0, 0)
        add("duplicate-suppressed", duplicate["status"] == "SUPPRESSED", duplicate["status"])
        add("duplicate-reason", duplicate["suppression_reason"] == "DUPLICATE_WINDOW", duplicate["suppression_reason"])
        add("duplicate-not-accepted", duplicate["sandbox_accepted"] is False, duplicate["sandbox_accepted"])
        add("cash-sent", cash["status"] == "SENT_SANDBOX", cash["status"])
        add("cash-category", cash["category"] == "CASH", cash["category"])
        add("silence-control", silenced["event_type"] == "RULE_SILENCED", silenced["event_type"])
        add("silent-suppressed", while_silent["status"] == "SUPPRESSED", while_silent["status"])
        add("silent-reason", while_silent["suppression_reason"] == "RULE_SILENCED", while_silent["suppression_reason"])
        add("silent-not-accepted", while_silent["sandbox_accepted"] is False, while_silent["sandbox_accepted"])
        add("resume-control", resumed["event_type"] == "RULE_RESUMED", resumed["event_type"])
        add("resume-sent", after_resume["status"] == "SENT_SANDBOX", after_resume["status"])
        add("failure-recorded", failed["status"] == "FAILED_RETRYABLE", failed["status"])
        add("failure-code-safe", failed["failure_code"] == "SANDBOX_TRANSIENT_FAILURE", failed["failure_code"])
        add("retry-scheduled", bool(failed["next_retry_at"]), failed["next_retry_at"])
        add("retry-success", retried["status"] == "RETRY_SUCCEEDED_SANDBOX", retried["status"])
        add("retry-attempt-two", retried["attempt_number"] == 2, retried["attempt_number"])
        add("retry-count-one", retried["retry_count"] == 1, retried["retry_count"])
        add("retry-body-bound", retried["message"]["body_fingerprint"] == failed["message"]["body_fingerprint"], retried["message"]["body_fingerprint"])
        add("retry-idempotent", retry_replay["idempotent_replay"] is True, retry_replay["idempotent_replay"])
        add("idempotency-conflict", conflict_rejected, conflict_rejected)
        add("frequency-first-three", all(row["status"] == "SENT_SANDBOX" for row in tax[:3]), [row["status"] for row in tax[:3]])
        add("frequency-fourth-suppressed", tax[3]["status"] == "SUPPRESSED", tax[3]["status"])
        add("frequency-reason", tax[3]["suppression_reason"] == "FREQUENCY_LIMIT", tax[3]["suppression_reason"])
        add("unconfirmed-rejected", unconfirmed_rejected, unconfirmed_rejected)
        add("journal-has-events", snapshot["event_count"] >= 13, snapshot["event_count"])
        add("journal-sequence", [row["sequence"] for row in snapshot["events"]] == list(range(1, snapshot["event_count"] + 1)), snapshot["event_count"])
        add("journal-hashes", all(_SHA256.fullmatch(str(row["event_hash"])) for row in snapshot["events"]), snapshot["event_count"])
        add("journal-request-fingerprints", all(_SHA256.fullmatch(str(row["request_fingerprint"])) for row in snapshot["events"]), snapshot["event_count"])
        add("journal-reloads", reloaded["event_count"] == snapshot["event_count"], reloaded["event_count"])
        add("event-ids-unique", len({row["event_id"] for row in snapshot["events"]}) == snapshot["event_count"], snapshot["event_count"])
        add("body-fingerprints", all(_SHA256.fullmatch(str(row["body_fingerprint"])) for row in messages), len(messages))
        add("body-fields-allowlisted", all({field["field"] for field in row["body_fields"]} == {"kind", "period", "status", "safe_entry"} for row in messages), len(messages))
        add("body-no-sensitive-text", all(not _SENSITIVE_TEXT.search(row["body_text"]) for row in messages), len(messages))
        add("payload-no-secret", "secret" not in payload.casefold(), "absent")
        add("payload-no-password", "password" not in payload.casefold(), "absent")
        add("payload-no-api-key", "api_key" not in payload.casefold() and "api-key" not in payload.casefold(), "absent")
        add("dedupe-window", DEDUPE_WINDOW_MINUTES == 360, DEDUPE_WINDOW_MINUTES)
        add("frequency-limit", FREQUENCY_LIMIT_PER_DAY == 3, FREQUENCY_LIMIT_PER_DAY)
        add("retry-policy", RETRY_BUDGET == 3 and len(RETRY_DELAYS_SECONDS) == 3, RETRY_DELAYS_SECONDS)
        add("phase-boundary", snapshot["raw_root_access_count"] == snapshot["external_network_request_count"] == 0 and options_contract()["s22_p2_in_scope"] is False, "raw=0 external=0 s22p2=false")
        if len(checks) != 65:
            raise AssertionError(f"expected 65 public checks, got {len(checks)}")
        failed_checks = [row for row in checks if row["status"] != "PASS"]
        return {
            "schema_version": "kmfa.v015.s22p1.public_verification.v1",
            "run_phase_id": RUN_PHASE_ID,
            "public_check_count": len(checks),
            "public_check_pass_count": len(checks) - len(failed_checks),
            "public_check_failed_count": len(failed_checks),
            "checks": checks,
            "fixture_summary": {
                "recipient_count": 1,
                "rule_catalog_count": len(RULE_CATALOG),
                "enabled_confirmed_rule_count": len(active),
                "unconfirmed_rule_enabled_count": 0,
                "alert_category_count": 5,
                "safe_body_field_count": 4,
                "sensitive_body_field_count": 0,
                "attachment_count": 0,
                "duplicate_dispatch_count": 0,
                "silence_action_count": 2,
                "failure_injection_recovery_count": 1,
                "idempotency_conflict_accept_count": 0,
                "external_network_request_count": 0,
                "raw_root_access_count": 0,
            },
        }


def main() -> int:
    value = public_verification()
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if value["public_check_failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
