#!/usr/bin/env python3
"""DingTalk robot notification boundary for KMFA S19."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import ssl
import time
from collections.abc import Mapping
from typing import Any
from urllib import error, parse, request


GROUP_ROBOT_REQUIRED_ENV = ("DINGTALK_ROBOT_URL", "DINGTALK_ROBOT_SIGNING_KEY")
REQUIRED_KEYWORD = "开明考勤"


def robot_notification_status(env: Mapping[str, str]) -> dict[str, Any]:
    missing = [name for name in GROUP_ROBOT_REQUIRED_ENV if not env.get(name)]
    configured = not missing
    return {
        "channel": "dingtalk_group_robot",
        "configured": configured,
        "status": "READY" if configured else "NOTIFIER_CONFIG_MISSING",
        "missing": missing,
    }


def build_signed_robot_url(
    *,
    robot_url: str,
    signing_key: str,
    timestamp_ms: int | None = None,
) -> str:
    timestamp = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    string_to_sign = f"{timestamp}\n{signing_key}"
    digest = hmac.new(
        signing_key.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    signature = parse.quote_plus(base64.b64encode(digest))
    separator = "&" if "?" in robot_url else "?"
    return f"{robot_url}{separator}timestamp={timestamp}&sign={signature}"


def send_group_robot_markdown(
    *,
    title: str,
    markdown_text: str,
    env: Mapping[str, str],
    timestamp_ms: int | None = None,
    timeout: int = 15,
    urlopen: Any = request.urlopen,
) -> dict[str, Any]:
    status = robot_notification_status(env)
    if not status["configured"]:
        return {
            "status": "NOTIFIER_CONFIG_MISSING",
            "channel": "dingtalk_group_robot",
            "missing": status["missing"],
        }

    robot_url = str(env["DINGTALK_ROBOT_URL"])
    signing_key = str(env["DINGTALK_ROBOT_SIGNING_KEY"])
    signed_url = build_signed_robot_url(
        robot_url=robot_url,
        signing_key=signing_key,
        timestamp_ms=timestamp_ms,
    )
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": _with_required_keyword(title),
            "text": _with_required_keyword(markdown_text),
        },
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        signed_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with _call_urlopen(urlopen, req, timeout=timeout) as response:
            http_status = getattr(response, "status", None)
            response_payload = _parse_response_payload(response.read())
    except error.HTTPError as exc:
        return {
            "status": "FAILED",
            "channel": "dingtalk_group_robot",
            "http_status": exc.code,
            "robot_url": _redact_robot_url(robot_url),
            "error_type": "HTTPError",
        }
    except (error.URLError, TimeoutError, OSError) as exc:
        return {
            "status": "FAILED",
            "channel": "dingtalk_group_robot",
            "robot_url": _redact_robot_url(robot_url),
            "error_type": exc.__class__.__name__,
        }

    errcode = response_payload.get("errcode")
    if errcode in (0, "0", None):
        return {
            "status": "SENT",
            "channel": "dingtalk_group_robot",
            "http_status": http_status,
            "robot_url": _redact_robot_url(robot_url),
        }
    return {
        "status": "DINGTALK_ROBOT_ERROR",
        "channel": "dingtalk_group_robot",
        "http_status": http_status,
        "robot_url": _redact_robot_url(robot_url),
        "errcode": errcode,
        "errmsg": str(response_payload.get("errmsg") or "")[:200],
    }


def _with_required_keyword(value: str) -> str:
    return value if REQUIRED_KEYWORD in value else f"{REQUIRED_KEYWORD}\n\n{value}"


def _parse_response_payload(data: bytes) -> dict[str, Any]:
    if not data:
        return {}
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"parse_error": True}
    return payload if isinstance(payload, dict) else {"payload_type": type(payload).__name__}


def _call_urlopen(urlopen: Any, req: request.Request, *, timeout: int) -> Any:
    context = _build_ssl_context()
    try:
        return urlopen(req, timeout=timeout, context=context)
    except TypeError:
        return urlopen(req, timeout=timeout)


def _build_ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore[import-not-found]

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _redact_robot_url(robot_url: str) -> str:
    parts = parse.urlparse(robot_url)
    return parse.urlunparse((parts.scheme, parts.netloc, parts.path, "", "redacted=1", ""))
