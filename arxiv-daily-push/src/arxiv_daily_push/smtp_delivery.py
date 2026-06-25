"""Fail-closed SMTP delivery boundary for production notifications."""

from __future__ import annotations

import hashlib
import os
import smtplib
from collections.abc import Callable, Mapping
from email.message import EmailMessage
from typing import Any

from .config import DEFAULT_RECIPIENT, PROJECT_NAME
from .notifications import EmailNotification


SMTP_DELIVERY_MODEL_ID = "adp-smtp-delivery-v1"
SMTP_SECRET_ENV_KEYS = ("ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD")
SMTP_TIMEOUT_SECONDS = 30
SMTP_MAX_TIMEOUT_SECONDS = 300
SMTP_MESSAGE_ID_DOMAIN = "arxiv-daily-push.local"

SmtpFactory = Callable[..., Any]


def deliver_notification(
    notification: EmailNotification,
    *,
    generated_at: str,
    allow_send: bool = False,
    env: Mapping[str, str] | None = None,
    smtp_factory: SmtpFactory | None = None,
    timeout_seconds: int = SMTP_TIMEOUT_SECONDS,
    require_tls: bool = True,
) -> dict[str, Any]:
    """Return a delivery evidence report and only send when explicitly allowed."""

    environment = env if env is not None else os.environ
    delivery_id = _delivery_id(notification, generated_at)
    env_gate = _env_gate(environment)
    try:
        requested_timeout = int(timeout_seconds)
    except (TypeError, ValueError):
        requested_timeout = 0
    timeout_valid = 1 <= requested_timeout <= SMTP_MAX_TIMEOUT_SECONDS
    timeout = requested_timeout if timeout_valid else SMTP_TIMEOUT_SECONDS
    base = {
        "delivery_id": delivery_id,
        "validator_id": SMTP_DELIVERY_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "project_name": PROJECT_NAME,
        "generated_at": generated_at,
        "recipient": notification.recipient,
        "expected_recipient": DEFAULT_RECIPIENT,
        "subject": notification.subject,
        "status": "dry_run",
        "dry_run": not allow_send,
        "real_smtp_send_enabled": bool(allow_send),
        "required_env_keys": list(SMTP_SECRET_ENV_KEYS),
        "smtp_config": {
            "host_configured": env_gate["host_configured"],
            "port_configured": env_gate["port_configured"],
            "username_configured": env_gate["username_configured"],
            "password_configured": env_gate["password_configured"],
            "port_valid": env_gate["port_valid"],
            "require_tls": bool(require_tls),
            "timeout_seconds": timeout,
            "secret_values_logged": False,
        },
        "message": {
            "body_sha256": hashlib.sha256(notification.body.encode("utf-8")).hexdigest(),
            "html_body_sha256": hashlib.sha256(notification.html_body.encode("utf-8")).hexdigest()
            if notification.html_body
            else "",
            "html_alternative_present": bool(notification.html_body),
            "body_logged": False,
            "message_id": delivery_id,
        },
        "blocking_reasons": [],
    }

    if not allow_send:
        return base
    if not timeout_valid:
        return _blocked(base, [f"SMTP timeout_seconds must be between 1 and {SMTP_MAX_TIMEOUT_SECONDS}"])
    if notification.recipient != DEFAULT_RECIPIENT:
        return _blocked(base, [f"recipient must be {DEFAULT_RECIPIENT}"])
    if env_gate["blocking_reasons"]:
        return _blocked(base, env_gate["blocking_reasons"])

    host = str(environment["ADP_SMTP_HOST"])
    port = int(str(environment["ADP_SMTP_PORT"]))
    username = str(environment["ADP_SMTP_USERNAME"])
    password = str(environment["ADP_SMTP_PASSWORD"])
    message = _email_message(notification, sender=username, delivery_id=delivery_id)
    factory = smtp_factory or smtplib.SMTP
    try:
        with factory(host, port, timeout=timeout) as smtp:
            if require_tls:
                smtp.starttls()
            smtp.login(username, password)
            refused = smtp.send_message(message)
    except Exception as error:  # noqa: BLE001 - report class only; never echo SMTP secret-bearing text.
        return _blocked(base, [f"SMTP delivery failed: {error.__class__.__name__}"])

    refused_recipients = sorted(str(recipient) for recipient in (refused or {}).keys())
    if refused_recipients:
        return _blocked(base, [f"SMTP refused recipients: {', '.join(refused_recipients)}"])
    sent = dict(base)
    sent["status"] = "sent"
    sent["dry_run"] = False
    sent["delivery_ref"] = f"smtp://message/{delivery_id}"
    return sent


def validate_smtp_delivery_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("validator_id") != SMTP_DELIVERY_MODEL_ID:
        errors.append("smtp delivery validator_id must be adp-smtp-delivery-v1")
    if report.get("recipient") != DEFAULT_RECIPIENT:
        errors.append(f"smtp delivery recipient must be {DEFAULT_RECIPIENT}")
    if report.get("status") not in {"dry_run", "sent", "blocked"}:
        errors.append("smtp delivery status must be dry_run, sent, or blocked")
    smtp_config = report.get("smtp_config")
    if not isinstance(smtp_config, Mapping) or smtp_config.get("secret_values_logged") is not False:
        errors.append("smtp delivery must explicitly avoid logging secret values")
    elif not 1 <= int(smtp_config.get("timeout_seconds") or 0) <= SMTP_MAX_TIMEOUT_SECONDS:
        errors.append(f"smtp delivery timeout_seconds must be between 1 and {SMTP_MAX_TIMEOUT_SECONDS}")
    message = report.get("message")
    if not isinstance(message, Mapping) or not message.get("body_sha256") or message.get("body_logged") is not False:
        errors.append("smtp delivery report must include body_sha256 and must not log body")
    if report.get("status") == "sent" and not report.get("delivery_ref"):
        errors.append("sent smtp delivery requires delivery_ref")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked smtp delivery requires blocking_reasons")
    if report.get("status") == "dry_run" and report.get("blocking_reasons"):
        errors.append("dry_run smtp delivery cannot include blocking_reasons")
    return errors


def _email_message(notification: EmailNotification, *, sender: str, delivery_id: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = notification.recipient
    message["Subject"] = notification.subject
    message["X-ADP-Delivery-ID"] = delivery_id
    message["Message-ID"] = f"<{_message_id_local_part(delivery_id)}@{SMTP_MESSAGE_ID_DOMAIN}>"
    message.set_content(notification.body)
    if notification.html_body:
        message.add_alternative(notification.html_body, subtype="html")
    return message


def _env_gate(env: Mapping[str, str]) -> dict[str, Any]:
    missing = [key for key in SMTP_SECRET_ENV_KEYS if not env.get(key)]
    reasons = [f"missing required SMTP environment keys: {', '.join(missing)}"] if missing else []
    port_valid = False
    if env.get("ADP_SMTP_PORT"):
        try:
            port = int(str(env["ADP_SMTP_PORT"]))
            port_valid = 1 <= port <= 65535
        except ValueError:
            port_valid = False
        if not port_valid:
            reasons.append("ADP_SMTP_PORT must be an integer between 1 and 65535")
    return {
        "host_configured": bool(env.get("ADP_SMTP_HOST")),
        "port_configured": bool(env.get("ADP_SMTP_PORT")),
        "username_configured": bool(env.get("ADP_SMTP_USERNAME")),
        "password_configured": bool(env.get("ADP_SMTP_PASSWORD")),
        "port_valid": port_valid,
        "blocking_reasons": reasons,
    }


def _blocked(base: Mapping[str, Any], reasons: list[str]) -> dict[str, Any]:
    blocked = dict(base)
    blocked["status"] = "blocked"
    blocked["blocking_reasons"] = reasons
    return blocked


def _delivery_id(notification: EmailNotification, generated_at: str) -> str:
    body_hash = hashlib.sha256(notification.body.encode("utf-8")).hexdigest()
    html_hash = hashlib.sha256(notification.html_body.encode("utf-8")).hexdigest() if notification.html_body else ""
    payload = "|".join([generated_at, notification.recipient, notification.subject, body_hash, html_hash])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"smtp-delivery:{digest}"


def _message_id_local_part(delivery_id: str) -> str:
    return "".join(character if character.isalnum() or character in {"-", "."} else "-" for character in delivery_id)
