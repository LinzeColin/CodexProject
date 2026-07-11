#!/usr/bin/env python3
"""Multi-target DingTalk notification routing for KMFA S19."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from KMFA.tools.dingtalk_attendance import AUTOMATION_NAME, TIMEZONE, ZHANG_LINZE_USER_ID
from KMFA.tools.dingtalk_attendance.dws_auth_guard import dws_command_safety_status
from KMFA.tools.dingtalk_attendance.notification_template import (
    build_notification_message,
    notification_context_from_output_status,
    official_report_parity_failure_reason,
)
from KMFA.tools.dingtalk_attendance.notifier_dingtalk import send_group_robot_markdown
from KMFA.tools.dingtalk_attendance.notifier_dws_personal_chat import (
    PRIVATE_RUNTIME_DIR,
    RESOLVED_CHANNEL_PATH,
    get_dws_help,
    run_dws_command,
    send_dws_chat_message,
    send_dws_ding_message,
    send_dws_group_message,
    send_text_with_resolved_channel,
)
from KMFA.tools.dingtalk_attendance.secrets_loader import merged_runtime_env


ROOT = Path(__file__).resolve().parents[2]
TARGETS_CONFIG_PATH = PRIVATE_RUNTIME_DIR / "notification_targets.local.json"
TARGETS_RESOLVED_PATH = PRIVATE_RUNTIME_DIR / "notification_targets_resolved.json"
PUBLIC_TARGETS_MANIFEST_PATH = ROOT / "metadata" / "dingtalk_attendance" / "notification_targets_manifest.json"
DEFAULT_TARGET_LABEL = "张霖泽"
DEFAULT_REPORTS = ("management", "hr")


def default_targets_config() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "targets": [
            {
                "label": DEFAULT_TARGET_LABEL,
                "type": "personal",
                "enabled": True,
                "reports": list(DEFAULT_REPORTS),
                "user_id": ZHANG_LINZE_USER_ID,
                "preferred_channel": "dws_open_dingtalk_id_chat",
            }
        ],
    }


def migrate_legacy_resolved_channel(
    *,
    legacy_path: Path = RESOLVED_CHANNEL_PATH,
    targets_config_path: Path = TARGETS_CONFIG_PATH,
    targets_resolved_path: Path = TARGETS_RESOLVED_PATH,
    public_manifest_path: Path = PUBLIC_TARGETS_MANIFEST_PATH,
    now: datetime | None = None,
) -> dict[str, Any]:
    if targets_resolved_path.exists():
        return {"migrated": False, "reason": "targets_resolved_exists"}
    if not legacy_path.exists():
        return {"migrated": False, "reason": "legacy_resolved_missing"}

    current = now or datetime.now(ZoneInfo(TIMEZONE))
    legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
    label = str(legacy.get("recipient_name") or DEFAULT_TARGET_LABEL)
    user_id = str(legacy.get("recipient_user_id") or ZHANG_LINZE_USER_ID)
    channel = str(legacy.get("channel") or "")
    target = {
        "label": label,
        "type": "personal",
        "enabled": True,
        "reports": list(DEFAULT_REPORTS),
        "user_id": user_id,
        "preferred_channel": channel or "dws_open_dingtalk_id_chat",
    }
    resolved_target = {
        "label": label,
        "type": "personal",
        "enabled": True,
        "reports": list(DEFAULT_REPORTS),
        "resolved_channel": channel,
        "user_id": user_id,
        "open_dingtalk_id": legacy.get("open_dingtalk_id"),
        "group_conversation_id": None,
        "webhook_env_key": None,
        "secret_env_key": None,
        "last_probe_status": str(legacy.get("status") or "SENT"),
        "last_probe_at": str(legacy.get("resolved_at") or current.isoformat()),
        "last_error": None,
    }
    targets_config_path.parent.mkdir(parents=True, exist_ok=True)
    if not targets_config_path.exists():
        _write_json(targets_config_path, {"schema_version": 1, "targets": [target]})
    _write_json(targets_resolved_path, {"schema_version": 1, "updated_at": current.isoformat(), "targets": [resolved_target]})
    write_public_targets_manifest(_public_targets_from_resolved([resolved_target], updated_at=current.isoformat()), public_manifest_path)
    return {"migrated": True, "target_count": 1}


def ensure_targets_config(
    *,
    targets_config_path: Path = TARGETS_CONFIG_PATH,
    legacy_path: Path = RESOLVED_CHANNEL_PATH,
) -> dict[str, Any]:
    if targets_config_path.exists():
        return json.loads(targets_config_path.read_text(encoding="utf-8"))
    if legacy_path.exists():
        migrate_legacy_resolved_channel(legacy_path=legacy_path, targets_config_path=targets_config_path)
        if targets_config_path.exists():
            return json.loads(targets_config_path.read_text(encoding="utf-8"))
    config = default_targets_config()
    targets_config_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(targets_config_path, config)
    return config


def probe_notification_targets(
    *,
    targets_config_path: Path = TARGETS_CONFIG_PATH,
    targets_resolved_path: Path = TARGETS_RESOLVED_PATH,
    public_manifest_path: Path = PUBLIC_TARGETS_MANIFEST_PATH,
    target_filter: str = "all",
    label_filter: str | None = None,
    now: datetime | None = None,
    env: Mapping[str, str] | None = None,
    dws_runner: Callable[..., dict[str, Any]] = run_dws_command,
    help_provider: Callable[[list[str]], str] = get_dws_help,
    robot_sender: Callable[..., dict[str, Any]] = send_group_robot_markdown,
) -> dict[str, Any]:
    values = merged_runtime_env() if env is None else dict(env)
    current = now or datetime.now(ZoneInfo(TIMEZONE))
    if dws_runner is run_dws_command and help_provider is get_dws_help:
        dws_safety = dws_command_safety_status(env=values)
        if dws_safety["status"] != "READY":
            return {
                "status": "DWS_AUTH_REQUIRED",
                "target_results": [],
                "targets_resolved": str(targets_resolved_path),
                "dws_command_safety": dws_safety,
                "failure_reason": dws_safety["failure_reason"],
            }
    config = ensure_targets_config(targets_config_path=targets_config_path)
    targets = _selected_targets(config.get("targets", []), target_filter=target_filter, label_filter=label_filter)
    resolved_targets: list[dict[str, Any]] = []
    target_results: list[dict[str, Any]] = []
    chat_help = help_provider(["dws", "chat", "message", "send"])

    for target in targets:
        if not isinstance(target, Mapping):
            continue
        resolved = _probe_one_target(
            target=target,
            now=current,
            env=values,
            dws_runner=dws_runner,
            chat_help=chat_help,
            robot_sender=robot_sender,
        )
        resolved_targets.append(resolved)
        target_results.append(
            {
                "label": resolved.get("label"),
                "type": resolved.get("type"),
                "status": resolved.get("last_probe_status"),
                "resolved_channel": resolved.get("resolved_channel"),
                "failure_reason": resolved.get("last_error"),
            }
        )

    manifest_targets = resolved_targets
    if (label_filter or target_filter != "all") and targets_resolved_path.exists():
        existing_payload = json.loads(targets_resolved_path.read_text(encoding="utf-8"))
        manifest_targets = _merge_resolved_targets(existing_payload.get("targets", []), resolved_targets)

    payload = {"schema_version": 1, "updated_at": current.isoformat(), "targets": manifest_targets}
    targets_resolved_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(targets_resolved_path, payload)
    write_public_targets_manifest(_public_targets_from_resolved(manifest_targets, updated_at=current.isoformat()), public_manifest_path)
    status = _summarize_target_probe_status([str(item.get("status")) for item in target_results])
    return {"status": status, "target_results": target_results, "targets_resolved": str(targets_resolved_path)}


def dispatch_reports_to_targets(
    *,
    output_status: Mapping[str, Any],
    targets_resolved_path: Path = TARGETS_RESOLVED_PATH,
    legacy_resolved_path: Path = RESOLVED_CHANNEL_PATH,
    public_manifest_path: Path = PUBLIC_TARGETS_MANIFEST_PATH,
    target_filter: str = "all",
    env: Mapping[str, str] | None = None,
    sender: Callable[..., dict[str, Any]] = send_text_with_resolved_channel,
) -> dict[str, Any]:
    receipt_path = Path(str(output_status["dispatch_receipt"]))
    stats = output_status.get("stats", {})
    parity_failure = official_report_parity_failure_reason(stats if isinstance(stats, Mapping) else {})
    if parity_failure:
        receipt = _targets_receipt(
            status="NOT_SENT_OFFICIAL_ATTENDANCE_PARITY_FAILED",
            output_status=output_status,
            target_results=[],
            failure_reason=parity_failure,
        )
        _write_json(receipt_path, receipt)
        return receipt
    if not targets_resolved_path.exists():
        migrate_legacy_resolved_channel(
            legacy_path=legacy_resolved_path,
            targets_resolved_path=targets_resolved_path,
            public_manifest_path=public_manifest_path,
        )
    if not targets_resolved_path.exists():
        receipt = _targets_receipt(
            status="NOTIFIER_CONFIG_MISSING",
            output_status=output_status,
            target_results=[],
            failure_reason=f"missing targets resolved file: {targets_resolved_path}",
        )
        _write_json(receipt_path, receipt)
        return receipt

    payload = json.loads(targets_resolved_path.read_text(encoding="utf-8"))
    targets = _selected_targets(payload.get("targets", []), target_filter=target_filter)
    values = merged_runtime_env() if env is None else dict(env)
    target_results: list[dict[str, Any]] = []
    messages: list[dict[str, Any]] = []
    notification_template_text = ""

    for target in targets:
        if not isinstance(target, Mapping) or not target.get("enabled", True):
            continue
        reports = _coerce_reports(target.get("reports"))
        if not reports:
            target_results.append(_target_send_result(target=target, status="SKIPPED", reports=reports, failure_reason="reports empty"))
            continue
        try:
            _assert_selected_report_files_exist(output_status, reports)
            channel = _channel_payload_from_target(target)
            text = _build_target_notification_text(output_status=output_status, reports=reports, markdown=_target_uses_markdown(target, channel))
            if not notification_template_text:
                notification_template_text = text
            send_result = sender(channel=channel, title="开明考勤提醒", text=text, env=values)
        except (KeyError, OSError) as exc:
            send_result = {
                "status": "FAILED",
                "channel": str(target.get("resolved_channel") or "unknown"),
                "failure_reason": exc.__class__.__name__,
            }
        result = _target_send_result(target=target, status=str(send_result.get("status", "FAILED")), reports=reports, send_result=send_result)
        target_results.append(result)
        messages.append(
            {
                "report": "attendance_notification",
                "label": result["label"],
                "type": result["type"],
                "channel": result["channel"],
                "status": str(send_result.get("status", "FAILED")),
            }
        )

    status = _summarize_dispatch_status(target_results)
    receipt = _targets_receipt(
        status=status,
        output_status=output_status,
        target_results=target_results,
        messages=messages,
        notification_template_text=notification_template_text,
    )
    _write_json(receipt_path, receipt)
    return receipt


def write_public_targets_manifest(manifest: Mapping[str, Any], public_manifest_path: Path = PUBLIC_TARGETS_MANIFEST_PATH) -> None:
    public_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(public_manifest_path, manifest)


def upsert_target(
    *,
    target: Mapping[str, Any],
    targets_config_path: Path = TARGETS_CONFIG_PATH,
) -> dict[str, Any]:
    config = ensure_targets_config(targets_config_path=targets_config_path)
    targets = [item for item in config.get("targets", []) if isinstance(item, Mapping)]
    label = str(target.get("label") or "").strip()
    if not label:
        raise ValueError("target label required")
    normalized = _normalize_target(target)
    replaced = False
    new_targets: list[dict[str, Any]] = []
    for item in targets:
        if str(item.get("label") or "") == label:
            new_targets.append(normalized)
            replaced = True
        else:
            new_targets.append(dict(item))
    if not replaced:
        new_targets.append(normalized)
    payload = {"schema_version": 1, "targets": new_targets}
    _write_json(targets_config_path, payload)
    return {"status": "OK", "label": label, "updated": replaced}


def disable_target(*, label: str, targets_config_path: Path = TARGETS_CONFIG_PATH) -> dict[str, Any]:
    config = ensure_targets_config(targets_config_path=targets_config_path)
    updated = False
    targets: list[dict[str, Any]] = []
    for item in config.get("targets", []):
        if not isinstance(item, Mapping):
            continue
        row = dict(item)
        if str(row.get("label") or "") == label:
            row["enabled"] = False
            updated = True
        targets.append(row)
    _write_json(targets_config_path, {"schema_version": 1, "targets": targets})
    return {"status": "OK" if updated else "NOT_FOUND", "label": label}


def list_targets(*, targets_config_path: Path = TARGETS_CONFIG_PATH) -> dict[str, Any]:
    config = ensure_targets_config(targets_config_path=targets_config_path)
    return {
        "schema_version": 1,
        "targets": [
            _redact_target_for_cli(item)
            for item in config.get("targets", [])
            if isinstance(item, Mapping)
        ],
    }


def _probe_one_target(
    *,
    target: Mapping[str, Any],
    now: datetime,
    env: Mapping[str, str],
    dws_runner: Callable[..., dict[str, Any]],
    chat_help: str,
    robot_sender: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    target_type = str(target.get("type") or "personal")
    if target_type == "group":
        return _probe_group_target(
            target=target,
            now=now,
            env=env,
            dws_runner=dws_runner,
            chat_help=chat_help,
            robot_sender=robot_sender,
        )
    return _probe_personal_target(target=target, now=now, env=env, dws_runner=dws_runner, chat_help=chat_help)


def _probe_personal_target(
    *,
    target: Mapping[str, Any],
    now: datetime,
    env: Mapping[str, str],
    dws_runner: Callable[..., dict[str, Any]],
    chat_help: str,
) -> dict[str, Any]:
    label = str(target.get("label") or DEFAULT_TARGET_LABEL)
    reports = _coerce_reports(target.get("reports"))
    user = _resolve_user(target=target, runner=dws_runner)
    if user.get("status") != "OK":
        return _resolved_target(target=target, status="FAILED", now=now, last_error=str(user.get("failure_reason") or "user resolve failed"))
    user_id = str(user.get("user_id") or "")
    open_dingtalk_id = str(user.get("open_dingtalk_id") or "")
    title, text = _probe_message(label=label, now=now, channel_hint="DWS personal target")
    attempts: list[dict[str, Any]] = []
    if open_dingtalk_id:
        result = send_dws_chat_message(
            recipient_flag="--open-dingtalk-id",
            recipient_value=open_dingtalk_id,
            title=title,
            text=text,
            help_text=chat_help,
            runner=dws_runner,
        )
        attempts.append(result)
        if result.get("status") == "SENT":
            return _resolved_target(
                target=target,
                status="SENT",
                now=now,
                resolved_channel="dws_open_dingtalk_id_chat",
                user_id=user_id,
                open_dingtalk_id=open_dingtalk_id,
                reports=reports,
            )
    if user_id:
        result = send_dws_chat_message(
            recipient_flag="--user",
            recipient_value=user_id,
            title=title,
            text=text,
            help_text=chat_help,
            runner=dws_runner,
        )
        attempts.append(result)
        if result.get("status") == "SENT":
            return _resolved_target(
                target=target,
                status="SENT",
                now=now,
                resolved_channel="dws_userid_chat",
                user_id=user_id,
                open_dingtalk_id=open_dingtalk_id or None,
                reports=reports,
            )
    ding = send_dws_ding_message(recipient_user_id=user_id, title=title, text=text, env=env, runner=dws_runner)
    attempts.append(ding)
    if ding.get("status") == "SENT":
        return _resolved_target(target=target, status="SENT", now=now, resolved_channel="dws_ding_personal", user_id=user_id, reports=reports)
    return _resolved_target(
        target=target,
        status="FAILED",
        now=now,
        user_id=user_id,
        open_dingtalk_id=open_dingtalk_id or None,
        reports=reports,
        last_error=_last_failure_reason(attempts),
    )


def _probe_group_target(
    *,
    target: Mapping[str, Any],
    now: datetime,
    env: Mapping[str, str],
    dws_runner: Callable[..., dict[str, Any]],
    chat_help: str,
    robot_sender: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    label = str(target.get("label") or target.get("group_name") or "DingTalk group")
    reports = _coerce_reports(target.get("reports"))
    conversation_id = str(target.get("conversation_id") or target.get("group_conversation_id") or "").strip()
    if not conversation_id and target.get("group_name"):
        conversation_id = _resolve_group_conversation_id(group_name=str(target.get("group_name")), runner=dws_runner)
    title, text = _probe_message(label=label, now=now, channel_hint="DWS group target")
    if conversation_id:
        result = send_dws_group_message(
            group_conversation_id=conversation_id,
            title=title,
            text=text,
            help_text=chat_help,
            runner=dws_runner,
        )
        if result.get("status") == "SENT":
            return _resolved_target(
                target=target,
                status="SENT",
                now=now,
                resolved_channel="dws_group_chat",
                group_conversation_id=conversation_id,
                reports=reports,
            )
        last_error = str(result.get("failure_reason") or result.get("errmsg") or "dws group send failed")
    else:
        last_error = "group conversation id unavailable"

    webhook_env_key = str(target.get("webhook_env_key") or "").strip()
    secret_env_key = str(target.get("secret_env_key") or "").strip()
    if webhook_env_key and env.get(webhook_env_key):
        webhook_result = _probe_group_webhook(
            title=title,
            text=text,
            webhook_env_key=webhook_env_key,
            secret_env_key=secret_env_key,
            env=env,
            robot_sender=robot_sender,
            dws_runner=dws_runner,
        )
        if webhook_result.get("status") == "SENT":
            return _resolved_target(
                target=target,
                status="SENT",
                now=now,
                resolved_channel="dingtalk_group_robot_env",
                webhook_env_key=webhook_env_key,
                secret_env_key=secret_env_key or None,
                reports=reports,
            )
        last_error = str(webhook_result.get("failure_reason") or webhook_result.get("error_type") or "webhook send failed")
    return _resolved_target(target=target, status="FAILED", now=now, reports=reports, last_error=last_error)


def _probe_group_webhook(
    *,
    title: str,
    text: str,
    webhook_env_key: str,
    secret_env_key: str,
    env: Mapping[str, str],
    robot_sender: Callable[..., dict[str, Any]],
    dws_runner: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    webhook_value = str(env.get(webhook_env_key) or "")
    secret_value = str(env.get(secret_env_key) or "") if secret_env_key else ""
    if webhook_value.startswith("http") and secret_value:
        return robot_sender(
            title=title,
            markdown_text=text,
            env={"DINGTALK_ROBOT_URL": webhook_value, "DINGTALK_ROBOT_SIGNING_KEY": secret_value},
        )
    if webhook_value:
        result = dws_runner(
            ["dws", "chat", "message", "send-by-webhook", "--token", webhook_value, "--title", title, "--text", text, "--format", "json"],
            timeout=45,
        )
        if result.get("returncode") == 0:
            return {"status": "SENT", "channel": "dingtalk_group_robot_env"}
        payload = result.get("payload", {}) if isinstance(result, Mapping) else {}
        return {
            "status": "FAILED",
            "channel": "dingtalk_group_robot_env",
            "failure_reason": _first_error_text(payload) or "webhook dws send failed",
        }
    return {"status": "NOTIFIER_CONFIG_MISSING", "failure_reason": "webhook env missing"}


def _resolve_user(*, target: Mapping[str, Any], runner: Callable[..., dict[str, Any]]) -> dict[str, Any]:
    if target.get("user_id"):
        result = runner(["dws", "contact", "user", "get", "--ids", str(target["user_id"]), "--format", "json"], timeout=45)
        records = _extract_user_records(result.get("payload", {}))
        if records:
            user_id = _first_nonempty(records[0], ("userId", "user_id")) or str(target["user_id"])
            open_id = _first_nonempty(records[0], ("openDingTalkId", "open_dingtalk_id", "openConversationId", "open_conversation_id"))
            if not open_id and target.get("label"):
                searched = _resolve_user_by_query(query=str(target["label"]), runner=runner, fallback_user_id=user_id)
                open_id = str(searched.get("open_dingtalk_id") or "") or None
            return {"status": "OK", "user_id": user_id, "open_dingtalk_id": open_id}
        if target.get("label"):
            return _resolve_user_by_query(query=str(target["label"]), runner=runner, fallback_user_id=str(target["user_id"]))
    if target.get("name"):
        return _resolve_user_by_query(query=str(target["name"]), runner=runner)
    if target.get("mobile"):
        result = runner(["dws", "contact", "user", "search-mobile", "--mobile", str(target["mobile"]), "--format", "json"], timeout=45)
        return _unique_user_result(result.get("payload", {}))
    return {"status": "FAILED", "failure_reason": "user_id/name/mobile missing"}


def _resolve_user_by_query(*, query: str, runner: Callable[..., dict[str, Any]], fallback_user_id: str | None = None) -> dict[str, Any]:
    result = runner(["dws", "contact", "user", "search", "--query", query, "--format", "json"], timeout=45)
    user = _unique_user_result(result.get("payload", {}))
    if user.get("status") == "OK" and fallback_user_id and not user.get("user_id"):
        user["user_id"] = fallback_user_id
    return user


def _unique_user_result(payload: Any) -> dict[str, Any]:
    records = _extract_user_records(payload)
    if len(records) != 1:
        return {"status": "FAILED", "failure_reason": f"user search returned {len(records)} matches"}
    record = records[0]
    return {
        "status": "OK",
        "user_id": _first_nonempty(record, ("userId", "user_id")),
        "open_dingtalk_id": _first_nonempty(record, ("openDingTalkId", "open_dingtalk_id", "openConversationId", "open_conversation_id")),
    }


def _resolve_group_conversation_id(*, group_name: str, runner: Callable[..., dict[str, Any]]) -> str:
    result = runner(["dws", "chat", "search", "--query", group_name, "--limit", "20", "--format", "json"], timeout=45)
    records = _extract_list_records(result.get("payload", {}))
    if len(records) != 1:
        return ""
    return _first_nonempty(records[0], ("openConversationId", "open_conversation_id", "conversationId", "conversation_id", "id")) or ""


def _extract_user_records(payload: Any) -> list[Mapping[str, Any]]:
    records = _extract_list_records(payload)
    return [record for record in records if isinstance(record, Mapping)]


def _extract_list_records(payload: Any) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, Mapping)]
    if not isinstance(payload, Mapping):
        return []
    for key in ("result", "results", "users", "list", "items", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, Mapping)]
        if isinstance(value, Mapping):
            nested = _extract_list_records(value)
            if nested:
                return nested
    return []


def _resolved_target(
    *,
    target: Mapping[str, Any],
    status: str,
    now: datetime,
    resolved_channel: str | None = None,
    user_id: str | None = None,
    open_dingtalk_id: str | None = None,
    group_conversation_id: str | None = None,
    webhook_env_key: str | None = None,
    secret_env_key: str | None = None,
    reports: list[str] | None = None,
    last_error: str | None = None,
) -> dict[str, Any]:
    return {
        "label": str(target.get("label") or DEFAULT_TARGET_LABEL),
        "type": str(target.get("type") or "personal"),
        "enabled": bool(target.get("enabled", True)),
        "reports": reports or _coerce_reports(target.get("reports")),
        "resolved_channel": resolved_channel or str(target.get("preferred_channel") or ""),
        "user_id": user_id or target.get("user_id"),
        "open_dingtalk_id": open_dingtalk_id,
        "group_conversation_id": group_conversation_id,
        "webhook_env_key": webhook_env_key,
        "secret_env_key": secret_env_key,
        "last_probe_status": status,
        "last_probe_at": now.isoformat(),
        "last_error": last_error,
    }


def _channel_payload_from_target(target: Mapping[str, Any]) -> dict[str, Any]:
    channel = str(target.get("resolved_channel") or "")
    payload = {"channel": channel}
    if channel == "dws_open_dingtalk_id_chat":
        payload["open_dingtalk_id"] = target.get("open_dingtalk_id")
        payload["recipient_user_id"] = target.get("user_id")
    elif channel in {"dws_userid_chat", "dws_ding_personal"}:
        payload["recipient_user_id"] = target.get("user_id")
    elif channel == "dws_group_chat":
        payload["group_conversation_id"] = target.get("group_conversation_id")
    elif channel == "dingtalk_group_robot_env":
        payload["webhook_env_key"] = target.get("webhook_env_key")
        payload["secret_env_key"] = target.get("secret_env_key")
    return payload


def _build_target_notification_text(*, output_status: Mapping[str, Any], reports: list[str], markdown: bool) -> str:
    context = notification_context_from_output_status(output_status)
    report_paths: dict[str, str] = {}
    if "management" in reports and output_status.get("management_report"):
        report_paths["management_report"] = str(output_status["management_report"])
    if "hr" in reports and output_status.get("hr_report"):
        report_paths["hr_report"] = str(output_status["hr_report"])
    context["report_paths"] = report_paths
    return build_notification_message(**context, markdown=markdown)


def _target_send_result(
    *,
    target: Mapping[str, Any],
    status: str,
    reports: list[str],
    send_result: Mapping[str, Any] | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    result = send_result or {}
    management_status = status if "management" in reports else "SKIPPED"
    hr_status = status if "hr" in reports else "SKIPPED"
    return {
        "label": str(target.get("label") or ""),
        "type": str(target.get("type") or ""),
        "channel": str(result.get("channel") or target.get("resolved_channel") or "unknown"),
        "management_status": management_status,
        "hr_status": hr_status,
        "failure_reason": failure_reason or result.get("failure_reason"),
        "trace_id": result.get("trace_id"),
        "trace_id_present": bool(result.get("trace_id")),
    }


def _targets_receipt(
    *,
    status: str,
    output_status: Mapping[str, Any],
    target_results: list[dict[str, Any]],
    messages: list[dict[str, Any]] | None = None,
    notification_template_text: str = "",
    failure_reason: str | None = None,
) -> dict[str, Any]:
    receipt = {
        "notification_status": status,
        "channel": "multi_target",
        "target_results": target_results,
        "messages": messages or [],
        "run_id": str(output_status.get("run_id", "")),
        "run_type": str(output_status.get("run_type", "")),
        "work_date": str(output_status.get("work_date", "")),
        "management_report": str(output_status.get("management_report", "")),
        "hr_report": str(output_status.get("hr_report", "")),
        "notification_template_text": notification_template_text,
        "notification_delivery_table": _build_notification_delivery_table(target_results),
    }
    if failure_reason:
        receipt["failure_reason"] = failure_reason
    return receipt


def _public_targets_from_resolved(resolved_targets: list[Mapping[str, Any]], *, updated_at: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "automation_name": AUTOMATION_NAME,
        "updated_at": updated_at,
        "sensitive_values_committed": False,
        "targets": [
            {
                "label": target.get("label"),
                "type": target.get("type"),
                "enabled": bool(target.get("enabled", True)),
                "reports": _coerce_reports(target.get("reports")),
                "resolved_channel": target.get("resolved_channel"),
                "last_probe_status": target.get("last_probe_status"),
                "last_probe_at": target.get("last_probe_at"),
                "sensitive_values_committed": False,
            }
            for target in resolved_targets
        ],
    }


def _merge_resolved_targets(existing_targets: Any, new_targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    new_by_label = {str(target.get("label") or ""): target for target in new_targets}
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for target in existing_targets if isinstance(existing_targets, list) else []:
        if not isinstance(target, Mapping):
            continue
        label = str(target.get("label") or "")
        if label in new_by_label:
            merged.append(new_by_label[label])
            seen.add(label)
        else:
            merged.append(dict(target))
    for target in new_targets:
        label = str(target.get("label") or "")
        if label not in seen:
            merged.append(target)
    return merged


def _normalize_target(target: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(target)
    normalized["label"] = str(target.get("label") or "").strip()
    normalized["type"] = str(target.get("type") or "personal")
    normalized["enabled"] = bool(target.get("enabled", True))
    normalized["reports"] = _coerce_reports(target.get("reports"))
    return normalized


def _selected_targets(targets: Any, *, target_filter: str, label_filter: str | None = None) -> list[Mapping[str, Any]]:
    selected: list[Mapping[str, Any]] = []
    for target in targets if isinstance(targets, list) else []:
        if not isinstance(target, Mapping):
            continue
        if label_filter and str(target.get("label") or "") != label_filter:
            continue
        target_type = str(target.get("type") or "")
        if target_filter in {"personal", "group"} and target_type != target_filter:
            continue
        selected.append(target)
    return selected


def _coerce_reports(value: Any) -> list[str]:
    if not isinstance(value, list):
        return list(DEFAULT_REPORTS)
    reports = [str(item).strip() for item in value if str(item).strip() in DEFAULT_REPORTS]
    return reports or list(DEFAULT_REPORTS)


def _assert_selected_report_files_exist(output_status: Mapping[str, Any], reports: list[str]) -> None:
    if "management" in reports:
        path = Path(str(output_status["management_report"]))
        if not path.exists():
            raise FileNotFoundError(str(path))
    if "hr" in reports:
        path = Path(str(output_status["hr_report"]))
        if not path.exists():
            raise FileNotFoundError(str(path))


def _target_uses_markdown(target: Mapping[str, Any], channel: Mapping[str, Any]) -> bool:
    return str(target.get("type") or "") == "group" or str(channel.get("channel") or "") in {
        "dingtalk_group_robot",
        "dingtalk_group_robot_env",
    }


def _probe_message(*, label: str, now: datetime, channel_hint: str) -> tuple[str, str]:
    title = "开明考勤通知目标验证"
    text = "\n".join(
        [
            "开明考勤通知目标验证",
            f"目标：{label}",
            f"北京时间：{now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"KMFA S19 通知通道：{channel_hint}",
            "说明：这是 KMFA S19 多目标通知路由自动验证消息。",
        ]
    )
    return title, text


def _summarize_target_probe_status(statuses: list[str]) -> str:
    active = [status for status in statuses if status]
    if active and all(status == "SENT" for status in active):
        return "SENT"
    if active and any(status == "SENT" for status in active):
        return "PARTIAL"
    return "FAILED"


def _summarize_dispatch_status(target_results: list[Mapping[str, Any]]) -> str:
    statuses: list[str] = []
    for result in target_results:
        for key in ("management_status", "hr_status"):
            status = str(result.get(key) or "")
            if status != "SKIPPED":
                statuses.append(status)
    if statuses and all(status == "SENT" for status in statuses):
        return "SENT"
    if statuses and all(status == "NOTIFIER_CONFIG_MISSING" for status in statuses):
        return "NOTIFIER_CONFIG_MISSING"
    return "FAILED"


def _build_notification_delivery_table(target_results: list[Mapping[str, Any]]) -> str:
    lines = ["| 发送对象 | 是否成功 |", "|---|---|"]
    for result in target_results:
        label = str(result.get("label") or "UNKNOWN")
        lines.append(f"| {label} | {'是' if _target_delivery_succeeded(result) else '否'} |")
    return "\n".join(lines)


def _target_delivery_succeeded(result: Mapping[str, Any]) -> bool:
    statuses = [
        str(result.get(key) or "")
        for key in ("management_status", "hr_status")
        if str(result.get(key) or "") != "SKIPPED"
    ]
    return bool(statuses) and all(status == "SENT" for status in statuses)


def _last_failure_reason(results: list[Mapping[str, Any]]) -> str:
    for result in reversed(results):
        reason = result.get("failure_reason") or result.get("errmsg")
        if reason:
            return str(reason)
    return "all notification channels failed"


def _first_error_text(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key in ("reason", "message", "errmsg", "code", "errcode"):
            if value.get(key):
                return str(value[key])
        for child in value.values():
            found = _first_error_text(child)
            if found:
                return found
    if isinstance(value, list):
        for child in value:
            found = _first_error_text(child)
            if found:
                return found
    return None


def _first_nonempty(payload: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _redact_target_for_cli(target: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in target.items()
        if key not in {"open_dingtalk_id", "group_conversation_id", "webhook_env_key", "secret_env_key"}
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
