#!/usr/bin/env python3
"""Resolved DingTalk notification channels for KMFA S19."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from KMFA.tools.dingtalk_attendance.notifier_dingtalk import send_group_robot_markdown
from KMFA.tools.dingtalk_attendance.notification_template import (
    build_notification_message,
    notification_context_from_output_status,
)
from KMFA.tools.dingtalk_attendance.secrets_loader import merged_runtime_env


ROOT = Path(__file__).resolve().parents[2]
PRIVATE_RUNTIME_DIR = ROOT / "metadata" / "dingtalk_attendance" / "private_runtime"
RESOLVED_CHANNEL_PATH = PRIVATE_RUNTIME_DIR / "notification_channel_resolved.json"


def run_dws_command(args: list[str], *, timeout: int = 45) -> dict[str, Any]:
    proc = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
    payload_text = proc.stdout.strip() or proc.stderr.strip() or "{}"
    return {
        "returncode": proc.returncode,
        "payload": _parse_json_payload(payload_text),
    }


def get_dws_help(command: list[str]) -> str:
    proc = subprocess.run([*command, "--help"], text=True, capture_output=True, timeout=30, check=False)
    return proc.stdout or proc.stderr or ""


def send_dws_chat_message(
    *,
    recipient_flag: str,
    recipient_value: str,
    title: str,
    text: str,
    help_text: str | None = None,
    runner: Callable[..., dict[str, Any]] = run_dws_command,
    timeout: int = 45,
) -> dict[str, Any]:
    channel = "dws_open_dingtalk_id_chat" if recipient_flag == "--open-dingtalk-id" else "dws_userid_chat"
    command = ["dws", "chat", "message", "send", recipient_flag, recipient_value, "--title", title]
    if help_text is None:
        help_text = get_dws_help(["dws", "chat", "message", "send"])
    if "--text" in help_text:
        command.extend(["--text", text])
    else:
        command.append(text)
    command.extend(["--format", "json"])
    result = runner(command, timeout=timeout)
    return _dws_result_to_status(result, channel=channel)


def send_dws_ding_message(
    *,
    recipient_user_id: str,
    title: str,
    text: str,
    env: Mapping[str, str],
    runner: Callable[..., dict[str, Any]] = run_dws_command,
    timeout: int = 45,
) -> dict[str, Any]:
    robot_code = env.get("DINGTALK_DING_ROBOT_CODE")
    if not robot_code:
        return {
            "status": "NOTIFIER_CONFIG_MISSING",
            "channel": "dws_ding_personal",
            "failure_reason": "DINGTALK_DING_ROBOT_CODE missing",
        }
    result = runner(
        [
            "dws",
            "ding",
            "message",
            "send",
            "--robot-code",
            robot_code,
            "--type",
            "app",
            "--users",
            recipient_user_id,
            "--content",
            f"{title}\n\n{text}",
            "--format",
            "json",
        ],
        timeout=timeout,
    )
    return _dws_result_to_status(result, channel="dws_ding_personal")


def send_text_with_resolved_channel(
    *,
    channel: Mapping[str, Any],
    title: str,
    text: str,
    env: Mapping[str, str] | None = None,
    runner: Callable[..., dict[str, Any]] = run_dws_command,
    help_provider: Callable[[list[str]], str] = get_dws_help,
    robot_sender: Callable[..., dict[str, Any]] = send_group_robot_markdown,
) -> dict[str, Any]:
    values = merged_runtime_env() if env is None else dict(env)
    channel_name = str(channel.get("channel") or "")
    if channel_name == "dws_userid_chat":
        return send_dws_chat_message(
            recipient_flag="--user",
            recipient_value=str(channel.get("recipient_user_id") or ""),
            title=title,
            text=text,
            help_text=help_provider(["dws", "chat", "message", "send"]),
            runner=runner,
        )
    if channel_name == "dws_open_dingtalk_id_chat":
        return send_dws_chat_message(
            recipient_flag="--open-dingtalk-id",
            recipient_value=str(channel.get("open_dingtalk_id") or ""),
            title=title,
            text=text,
            help_text=help_provider(["dws", "chat", "message", "send"]),
            runner=runner,
        )
    if channel_name == "dws_group_chat":
        return send_dws_group_message(
            group_conversation_id=str(channel.get("group_conversation_id") or ""),
            title=title,
            text=text,
            help_text=help_provider(["dws", "chat", "message", "send"]),
            runner=runner,
        )
    if channel_name == "dws_ding_personal":
        return send_dws_ding_message(
            recipient_user_id=str(channel.get("recipient_user_id") or ""),
            title=title,
            text=text,
            env=values,
            runner=runner,
        )
    if channel_name == "dingtalk_group_robot":
        return robot_sender(title=title, markdown_text=text, env=values)
    if channel_name == "dingtalk_group_robot_env":
        webhook_env_key = str(channel.get("webhook_env_key") or "")
        secret_env_key = str(channel.get("secret_env_key") or "")
        webhook_value = values.get(webhook_env_key)
        signing_key = values.get(secret_env_key)
        if not webhook_value:
            return {
                "status": "NOTIFIER_CONFIG_MISSING",
                "channel": channel_name,
                "failure_reason": "group robot env keys missing",
            }
        if not str(webhook_value).startswith("http"):
            webhook_result = runner(
                [
                    "dws",
                    "chat",
                    "message",
                    "send-by-webhook",
                    "--token",
                    str(webhook_value),
                    "--title",
                    title,
                    "--text",
                    text,
                    "--format",
                    "json",
                ],
                timeout=45,
            )
            return _dws_result_to_status(webhook_result, channel=channel_name)
        if not signing_key:
            return {
                "status": "NOTIFIER_CONFIG_MISSING",
                "channel": channel_name,
                "failure_reason": "group robot signing key env missing",
            }
        return robot_sender(
            title=title,
            markdown_text=text,
            env={"DINGTALK_ROBOT_URL": webhook_value, "DINGTALK_ROBOT_SIGNING_KEY": signing_key},
        )
    return {
        "status": "NOTIFIER_CONFIG_MISSING",
        "channel": channel_name or "unknown",
        "failure_reason": "resolved channel unsupported or missing",
    }


def send_dws_group_message(
    *,
    group_conversation_id: str,
    title: str,
    text: str,
    help_text: str | None = None,
    runner: Callable[..., dict[str, Any]] = run_dws_command,
    timeout: int = 45,
) -> dict[str, Any]:
    command = ["dws", "chat", "message", "send", "--group", group_conversation_id, "--title", title]
    if help_text is None:
        help_text = get_dws_help(["dws", "chat", "message", "send"])
    if "--text" in help_text:
        command.extend(["--text", text])
    else:
        command.append(text)
    command.extend(["--format", "json"])
    result = runner(command, timeout=timeout)
    return _dws_result_to_status(result, channel="dws_group_chat")


def dispatch_reports_with_resolved_channel(
    *,
    output_status: Mapping[str, Any],
    resolved_path: Path = RESOLVED_CHANNEL_PATH,
    env: Mapping[str, str] | None = None,
    sender: Callable[..., dict[str, Any]] = send_text_with_resolved_channel,
) -> dict[str, Any]:
    receipt_path = Path(str(output_status["dispatch_receipt"]))
    if not resolved_path.exists():
        receipt = _receipt(
            status="NOTIFIER_CONFIG_MISSING",
            channel="unresolved",
            output_status=output_status,
            messages=[],
            failure_reason=f"missing resolved channel file: {resolved_path}",
        )
        _write_receipt(receipt_path, receipt)
        return receipt

    channel = json.loads(resolved_path.read_text(encoding="utf-8"))
    channel_name = str(channel.get("channel") or "unknown")
    messages: list[dict[str, Any]] = []
    try:
        management_report = Path(str(output_status["management_report"]))
        hr_report = Path(str(output_status["hr_report"]))
        for report_path in (management_report, hr_report):
            if not report_path.exists():
                raise FileNotFoundError(str(report_path))
        notification_context = notification_context_from_output_status(output_status)
        text = build_notification_message(
            **notification_context,
            markdown=channel_name == "dingtalk_group_robot",
        )
        send_result = sender(channel=channel, title="开明考勤提醒", text=text, env=dict(env or {}))
    except (KeyError, OSError) as exc:
        send_result = {
            "status": "FAILED",
            "channel": channel_name,
            "failure_reason": exc.__class__.__name__,
        }

    messages.append(
        {
            "report": "attendance_notification",
            "management_report": str(output_status.get("management_report", "")),
            "hr_report": str(output_status.get("hr_report", "")),
            "status": send_result.get("status", "FAILED"),
            "channel": send_result.get("channel", channel_name),
            "failure_reason": send_result.get("failure_reason"),
            "server_key": send_result.get("server_key"),
            "trace_id": send_result.get("trace_id"),
            "errcode": send_result.get("errcode"),
            "errmsg": send_result.get("errmsg"),
        }
    )

    notification_status = _summarize_status([str(message["status"]) for message in messages])
    receipt = _receipt(
        status=notification_status,
        channel=channel_name,
        output_status=output_status,
        messages=messages,
    )
    _write_receipt(receipt_path, receipt)
    return receipt


def _receipt(
    *,
    status: str,
    channel: str,
    output_status: Mapping[str, Any],
    messages: list[dict[str, Any]],
    failure_reason: str | None = None,
) -> dict[str, Any]:
    receipt = {
        "notification_status": status,
        "channel": channel,
        "messages": messages,
        "management_report": str(output_status.get("management_report", "")),
        "hr_report": str(output_status.get("hr_report", "")),
    }
    if failure_reason:
        receipt["failure_reason"] = failure_reason
    return receipt


def _write_receipt(receipt_path: Path, receipt: Mapping[str, Any]) -> None:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")


def _summarize_status(statuses: list[str]) -> str:
    if statuses and all(status == "SENT" for status in statuses):
        return "SENT"
    if statuses and all(status == "NOTIFIER_CONFIG_MISSING" for status in statuses):
        return "NOTIFIER_CONFIG_MISSING"
    if statuses and any(status == "DINGTALK_ROBOT_ERROR" for status in statuses):
        return "DINGTALK_ROBOT_ERROR"
    return "FAILED"


def _dws_result_to_status(result: Mapping[str, Any], *, channel: str) -> dict[str, Any]:
    payload = result.get("payload", {})
    error_payload = _find_error_payload(payload)
    if result.get("returncode") == 0 and not error_payload:
        return {"status": "SENT", "channel": channel}
    return {
        "status": "FAILED",
        "channel": channel,
        "failure_reason": _first_nonempty(error_payload, ("reason", "message", "code")) or "dws_command_failed",
        "server_key": _first_nonempty(error_payload, ("server_key", "serverKey")),
        "trace_id": _first_nonempty(error_payload, ("trace_id", "traceId", "request_id", "requestId")),
        "errcode": _first_nonempty(error_payload, ("errcode", "errorCode", "code")),
        "errmsg": _first_nonempty(error_payload, ("errmsg", "message")),
    }


def _find_error_payload(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        if isinstance(value.get("error"), Mapping):
            return value["error"]
        if any(key in value for key in ("errcode", "errmsg", "server_key", "reason", "message")) and value.get("success") is not True:
            return value
        for child in value.values():
            found = _find_error_payload(child)
            if found:
                return found
    if isinstance(value, list):
        for child in value:
            found = _find_error_payload(child)
            if found:
                return found
    return {}


def _first_nonempty(payload: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _parse_json_payload(payload_text: str) -> dict[str, Any]:
    start = payload_text.find("{")
    if start == -1:
        return {"raw": payload_text[:1000]}
    try:
        payload = json.loads(payload_text[start:])
    except json.JSONDecodeError as exc:
        return {"parse_error": str(exc), "raw": payload_text[:1000]}
    return payload if isinstance(payload, dict) else {"payload": payload}
