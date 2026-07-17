#!/usr/bin/env python3
"""Probe and persist the first usable KMFA DingTalk attendance notification channel."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from KMFA.tools.dingtalk_attendance import AUTOMATION_NAME, OWNER_DINGTALK_USER_ID, TIMEZONE
from KMFA.tools.dingtalk_attendance.dws_auth_guard import dws_command_safety_status
from KMFA.tools.dingtalk_attendance.notifier_dingtalk import send_group_robot_markdown
from KMFA.tools.dingtalk_attendance.notifier_dws_personal_chat import (
    PRIVATE_RUNTIME_DIR,
    RESOLVED_CHANNEL_PATH,
    get_dws_help,
    run_dws_command,
    send_dws_chat_message,
    send_dws_ding_message,
)
from KMFA.tools.dingtalk_attendance.notification_targets import probe_notification_targets
from KMFA.tools.dingtalk_attendance.secrets_loader import merged_runtime_env


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_MANIFEST_PATH = ROOT / "metadata" / "dingtalk_attendance" / "notification_channel_manifest.json"
RECIPIENT_NAME = "ROLE::OWNER"
PUBLIC_PROBE_STATUSES = frozenset(
    {"SENT", "FAILED", "NOTIFIER_CONFIG_MISSING", "DWS_AUTH_REQUIRED"}
)
PUBLIC_PROBE_CHANNELS = frozenset(
    {
        "dws_userid_chat",
        "dws_open_dingtalk_id_chat",
        "dws_ding_personal",
        "dingtalk_group_robot",
        "dingtalk_work_notification",
    }
)
PUBLIC_PROBE_ERROR_CODES = frozenset(
    {"NONE", "CONFIG_MISSING", "AUTH_REQUIRED", "EXTERNAL_FAILURE", "UNKNOWN_FAILURE"}
)


def probe_notification_channels(
    *,
    recipient: str = OWNER_DINGTALK_USER_ID,
    recipient_name: str = RECIPIENT_NAME,
    runtime_dir: Path = PRIVATE_RUNTIME_DIR,
    public_manifest_path: Path = PUBLIC_MANIFEST_PATH,
    now: datetime | None = None,
    env: Mapping[str, str] | None = None,
    dws_runner: Callable[..., dict[str, Any]] = run_dws_command,
    help_provider: Callable[[list[str]], str] = get_dws_help,
    robot_sender: Callable[..., dict[str, Any]] = send_group_robot_markdown,
) -> dict[str, Any]:
    values = merged_runtime_env() if env is None else dict(env)
    current = now or datetime.now(ZoneInfo(TIMEZONE))
    if not recipient or recipient == "CONFIG_REQUIRED":
        return {
            "status": "NOTIFIER_CONFIG_MISSING",
            "successful_channel": None,
            "recipient_user_id": None,
            "attempts": [],
            "failure_reason": "KMFA_DINGTALK_OWNER_USER_ID is required",
        }
    if dws_runner is run_dws_command and help_provider is get_dws_help:
        dws_safety = dws_command_safety_status(env=values)
        if dws_safety["status"] != "READY":
            return {
                "status": "DWS_AUTH_REQUIRED",
                "successful_channel": None,
                "recipient_user_id": recipient,
                "attempts": [],
                "dws_command_safety": dws_safety,
                "failure_reason": dws_safety["failure_reason"],
            }
    title = "开明考勤个人通知验证"
    text = "\n".join(
        [
            "开明考勤个人通知验证",
            f"收件人：{recipient_name}",
            f"userId：{recipient}",
            f"北京时间：{current.strftime('%Y-%m-%d %H:%M:%S')}",
            "KMFA 钉钉考勤 skill 通知通道：<待探测>",
            "说明：这是 KMFA 钉钉考勤 skill 个人通知通道自动验证消息。",
        ]
    )
    attempts: list[dict[str, Any]] = []
    chat_help = help_provider(["dws", "chat", "message", "send"])

    user_result = send_dws_chat_message(
        recipient_flag="--user",
        recipient_value=recipient,
        title=title,
        text=text.replace("<待探测>", "DWS userId 单聊"),
        help_text=chat_help,
        runner=dws_runner,
    )
    attempts.append(_attempt("dws_userid_chat", user_result))
    if user_result["status"] == "SENT":
        return _persist_success(
            recipient=recipient,
            recipient_name=recipient_name,
            channel={"channel": "dws_userid_chat", "channel_type": "personal", "recipient_user_id": recipient},
            attempts=attempts,
            runtime_dir=runtime_dir,
            public_manifest_path=public_manifest_path,
            now=current,
        )

    open_dingtalk_id = _discover_open_dingtalk_id(recipient=recipient, recipient_name=recipient_name, runner=dws_runner)
    if open_dingtalk_id:
        open_result = send_dws_chat_message(
            recipient_flag="--open-dingtalk-id",
            recipient_value=open_dingtalk_id,
            title=title,
            text=text.replace("<待探测>", "DWS openDingTalkId 单聊"),
            help_text=chat_help,
            runner=dws_runner,
        )
        attempts.append(_attempt("dws_open_dingtalk_id_chat", open_result, identifier_present=True))
        if open_result["status"] == "SENT":
            return _persist_success(
                recipient=recipient,
                recipient_name=recipient_name,
                channel={
                    "channel": "dws_open_dingtalk_id_chat",
                    "channel_type": "personal",
                    "recipient_user_id": recipient,
                    "open_dingtalk_id": open_dingtalk_id,
                },
                attempts=attempts,
                runtime_dir=runtime_dir,
                public_manifest_path=public_manifest_path,
                now=current,
            )
    else:
        attempts.append({"channel": "dws_open_dingtalk_id_chat", "status": "SKIPPED", "failure_reason": "openDingTalkId unavailable"})

    ding_result = send_dws_ding_message(
        recipient_user_id=recipient,
        title=title,
        text=text.replace("<待探测>", "DWS DING 个人通知"),
        env=values,
        runner=dws_runner,
    )
    attempts.append(_attempt("dws_ding_personal", ding_result))
    if ding_result["status"] == "SENT":
        return _persist_success(
            recipient=recipient,
            recipient_name=recipient_name,
            channel={"channel": "dws_ding_personal", "channel_type": "personal", "recipient_user_id": recipient},
            attempts=attempts,
            runtime_dir=runtime_dir,
            public_manifest_path=public_manifest_path,
            now=current,
        )

    work_result = _attempt_work_notification_discovery(env=values, runner=dws_runner)
    attempts.append(work_result)

    robot_result = _attempt_group_robot_fallback(
        title=title,
        text=text.replace("<待探测>", "群机器人 fallback"),
        env=values,
        robot_sender=robot_sender,
    )
    attempts.append(_attempt("dingtalk_group_robot", robot_result))
    if robot_result["status"] == "SENT":
        return _persist_success(
            recipient=recipient,
            recipient_name=recipient_name,
            channel={"channel": "dingtalk_group_robot", "channel_type": "group_fallback", "recipient_user_id": recipient},
            attempts=attempts,
            runtime_dir=runtime_dir,
            public_manifest_path=public_manifest_path,
            now=current,
        )

    result = {
        "status": "FAILED",
        "successful_channel": None,
        "recipient_user_id": recipient,
        "attempts": attempts,
        "next_fallback": _next_fallback(attempts),
    }
    _write_probe_files(
        runtime_dir=runtime_dir,
        public_manifest_path=public_manifest_path,
        resolved_channel=None,
        result=result,
        now=current,
    )
    return result


def _discover_open_dingtalk_id(
    *,
    recipient: str,
    recipient_name: str,
    runner: Callable[..., dict[str, Any]],
) -> str | None:
    for command in (
        ["dws", "contact", "user", "get", "--ids", recipient, "--format", "json"],
        ["dws", "contact", "user", "search", "--query", recipient_name, "--format", "json"],
    ):
        result = runner(command, timeout=45)
        value = _find_key(result.get("payload", {}), ("openDingTalkId", "open_dingtalk_id", "openConversationId", "open_conversation_id"))
        if value:
            return value
    return None


def _attempt_work_notification_discovery(
    *,
    env: Mapping[str, str],
    runner: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    required = ("DINGTALK_APP_KEY", "DINGTALK_APP_CREDENTIAL", "DINGTALK_CORP_ID")
    if any(not env.get(name) for name in required):
        return {
            "channel": "dingtalk_work_notification",
            "status": "NOTIFIER_CONFIG_MISSING",
            "failure_reason": "work notification app config missing",
        }
    if not env.get("DINGTALK_AGENT_ID"):
        discovery = runner(["dws", "api", "GET", "/v1.0/microApp/allApps", "--page-all", "--format", "json"], timeout=60)
        status = "WORK_NOTIFICATION_DISCOVERY_FAILED" if discovery.get("returncode") != 0 else "NOTIFIER_CONFIG_MISSING"
        return {
            "channel": "dingtalk_work_notification",
            "status": status,
            "failure_reason": "DINGTALK_AGENT_ID missing",
        }
    return {
        "channel": "dingtalk_work_notification",
        "status": "NOTIFIER_CONFIG_MISSING",
        "failure_reason": "work notification send not selected; personal DWS channels have priority",
    }


def _attempt_group_robot_fallback(
    *,
    title: str,
    text: str,
    env: Mapping[str, str],
    robot_sender: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    if not env.get("DINGTALK_ROBOT_URL") or not env.get("DINGTALK_ROBOT_SIGNING_KEY"):
        return {
            "status": "NOTIFIER_CONFIG_MISSING",
            "channel": "dingtalk_group_robot",
            "failure_reason": "group robot config missing",
        }
    return robot_sender(title=title, markdown_text=text, env=env)


def _persist_success(
    *,
    recipient: str,
    recipient_name: str,
    channel: dict[str, Any],
    attempts: list[dict[str, Any]],
    runtime_dir: Path,
    public_manifest_path: Path,
    now: datetime,
) -> dict[str, Any]:
    resolved_channel = {
        "schema_version": 1,
        "status": "SENT",
        "resolved_at": now.isoformat(),
        "recipient_name": recipient_name,
        **channel,
    }
    result = {
        "status": "SENT",
        "successful_channel": channel["channel"],
        "channel_type": channel["channel_type"],
        "recipient_user_id": recipient,
        "attempts": attempts,
    }
    _write_probe_files(
        runtime_dir=runtime_dir,
        public_manifest_path=public_manifest_path,
        resolved_channel=resolved_channel,
        result=result,
        now=now,
    )
    return result


def _write_probe_files(
    *,
    runtime_dir: Path,
    public_manifest_path: Path,
    resolved_channel: Mapping[str, Any] | None,
    result: Mapping[str, Any],
    now: datetime,
) -> None:
    runtime_dir.mkdir(parents=True, exist_ok=True)
    if resolved_channel is not None:
        (runtime_dir / "notification_channel_resolved.json").write_text(
            json.dumps(resolved_channel, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    diagnostic = {
        "updated_at": now.isoformat(),
        "result": result,
        "resolved_channel": _redact_private_channel(resolved_channel),
    }
    (runtime_dir / "notification_probe_diagnostic.json").write_text(
        json.dumps(diagnostic, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    public_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    public_manifest = _public_manifest(result=result, now=now)
    _validate_public_probe_manifest(public_manifest)
    public_manifest_path.write_text(
        json.dumps(public_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _public_manifest(*, result: Mapping[str, Any], now: datetime) -> dict[str, Any]:
    status = str(result.get("status") or "")
    if status not in PUBLIC_PROBE_STATUSES:
        raise ValueError("public probe status is not allowlisted")
    success_channel = result.get("successful_channel")
    if success_channel is not None and str(success_channel) not in PUBLIC_PROBE_CHANNELS:
        raise ValueError("public probe success channel is not allowlisted")
    attempts: list[dict[str, Any]] = []
    for attempt in result.get("attempts", []):
        if not isinstance(attempt, Mapping):
            continue
        channel = str(attempt.get("channel") or "")
        attempt_status = str(attempt.get("status") or "FAILED")
        if channel not in PUBLIC_PROBE_CHANNELS or attempt_status not in PUBLIC_PROBE_STATUSES:
            raise ValueError("public probe attempt enum is not allowlisted")
        attempts.append(
            {
                "channel": channel,
                "status": attempt_status,
                "error_code": _public_attempt_error_code(attempt_status, attempt),
                "trace_id_present": bool(attempt.get("trace_id")),
                "identifier_present": bool(attempt.get("identifier_present")),
            }
        )
    manifest = {
        "schema_version": 2,
        "automation_name": AUTOMATION_NAME,
        "updated_at": now.isoformat(),
        "last_probe_status": status,
        "last_success_channel": success_channel,
        "resolved_channel_private_registry_ref": "PRIVATE-REGISTRY::DINGTALK_NOTIFICATION_CHANNEL_RESOLVED",
        "resolved_channel_committed": False,
        "sensitive_values_committed": False,
        "attempt_count": len(attempts),
        "attempts": attempts,
    }
    _validate_public_probe_manifest(manifest)
    return manifest


def _public_attempt_error_code(status: str, attempt: Mapping[str, Any]) -> str:
    if status == "SENT":
        return "NONE"
    if status == "NOTIFIER_CONFIG_MISSING":
        return "CONFIG_MISSING"
    if status == "DWS_AUTH_REQUIRED":
        return "AUTH_REQUIRED"
    if attempt.get("failure_reason") or attempt.get("server_key") or attempt.get("errmsg"):
        return "EXTERNAL_FAILURE"
    return "UNKNOWN_FAILURE"


def _validate_public_probe_manifest(manifest: Mapping[str, Any]) -> None:
    expected_top = {
        "schema_version",
        "automation_name",
        "updated_at",
        "last_probe_status",
        "last_success_channel",
        "resolved_channel_private_registry_ref",
        "resolved_channel_committed",
        "sensitive_values_committed",
        "attempt_count",
        "attempts",
    }
    if set(manifest) != expected_top or manifest.get("schema_version") != 2:
        raise ValueError("public probe manifest schema mismatch")
    if manifest.get("automation_name") != AUTOMATION_NAME:
        raise ValueError("public probe automation mismatch")
    if manifest.get("last_probe_status") not in PUBLIC_PROBE_STATUSES:
        raise ValueError("public probe status mismatch")
    channel = manifest.get("last_success_channel")
    if channel is not None and channel not in PUBLIC_PROBE_CHANNELS:
        raise ValueError("public probe channel mismatch")
    if manifest.get("resolved_channel_private_registry_ref") != "PRIVATE-REGISTRY::DINGTALK_NOTIFICATION_CHANNEL_RESOLVED":
        raise ValueError("public probe private registry ref mismatch")
    if manifest.get("resolved_channel_committed") is not False or manifest.get("sensitive_values_committed") is not False:
        raise ValueError("public probe sensitive-value flags mismatch")
    attempts = manifest.get("attempts")
    if not isinstance(attempts, list) or manifest.get("attempt_count") != len(attempts):
        raise ValueError("public probe attempt count mismatch")
    expected_attempt = {
        "channel",
        "status",
        "error_code",
        "trace_id_present",
        "identifier_present",
    }
    for attempt in attempts:
        if not isinstance(attempt, Mapping) or set(attempt) != expected_attempt:
            raise ValueError("public probe attempt schema mismatch")
        if attempt.get("channel") not in PUBLIC_PROBE_CHANNELS:
            raise ValueError("public probe attempt channel mismatch")
        if attempt.get("status") not in PUBLIC_PROBE_STATUSES:
            raise ValueError("public probe attempt status mismatch")
        if attempt.get("error_code") not in PUBLIC_PROBE_ERROR_CODES:
            raise ValueError("public probe attempt error code mismatch")


def _attempt(channel: str, result: Mapping[str, Any], *, identifier_present: bool = False) -> dict[str, Any]:
    return {
        "channel": channel,
        "status": result.get("status", "FAILED"),
        "failure_reason": result.get("failure_reason"),
        "server_key": result.get("server_key"),
        "trace_id": result.get("trace_id"),
        "errcode": result.get("errcode"),
        "errmsg": result.get("errmsg"),
        "identifier_present": identifier_present,
    }


def _next_fallback(attempts: list[Mapping[str, Any]]) -> str:
    failed = [str(attempt.get("channel")) for attempt in attempts if attempt.get("status") != "SENT"]
    return "manual_open_platform_app_config_review" if failed else "none"


def _find_key(value: Any, keys: tuple[str, ...]) -> str | None:
    if isinstance(value, Mapping):
        for key in keys:
            found = value.get(key)
            if isinstance(found, str) and found:
                return found
        for child in value.values():
            found = _find_key(child, keys)
            if found:
                return found
    if isinstance(value, list):
        for child in value:
            found = _find_key(child, keys)
            if found:
                return found
    return None


def _redact_private_channel(channel: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if channel is None:
        return None
    redacted = dict(channel)
    if "open_dingtalk_id" in redacted:
        redacted["open_dingtalk_id"] = "<present>"
    return redacted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe KMFA DingTalk attendance notification channels.")
    parser.add_argument("--recipient", default=OWNER_DINGTALK_USER_ID)
    parser.add_argument("--recipient-name", default=RECIPIENT_NAME)
    parser.add_argument("--all-targets", action="store_true", help="Probe every enabled target in notification_targets.local.json.")
    args = parser.parse_args(argv)

    if args.all_targets:
        result = probe_notification_targets()
        print(json.dumps(_sanitize_cli_result(result), ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["status"] in {"SENT", "PARTIAL"} else 2

    result = probe_notification_channels(recipient=args.recipient, recipient_name=args.recipient_name)
    print(json.dumps(_sanitize_cli_result(result), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "SENT" else 2


def _sanitize_cli_result(result: Mapping[str, Any]) -> dict[str, Any]:
    sanitized = dict(result)
    sanitized["attempts"] = [
        {key: value for key, value in attempt.items() if key not in {"open_dingtalk_id"}}
        for attempt in result.get("attempts", [])
        if isinstance(attempt, Mapping)
    ]
    return sanitized


if __name__ == "__main__":
    sys.exit(main())
