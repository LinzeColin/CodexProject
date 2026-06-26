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
    cycle_id: str | None = None,
    product_id: str = "notification",
    content_revision_id: str | None = None,
    allow_send: bool = False,
    env: Mapping[str, str] | None = None,
    smtp_factory: SmtpFactory | None = None,
    timeout_seconds: int = SMTP_TIMEOUT_SECONDS,
    require_tls: bool = True,
) -> dict[str, Any]:
    """Return a delivery evidence report and only send when explicitly allowed."""

    environment = env if env is not None else os.environ
    identity = _delivery_identity(
        notification,
        generated_at=generated_at,
        cycle_id=cycle_id,
        product_id=product_id,
        content_revision_id=content_revision_id,
    )
    env_gate = _env_gate(environment)
    try:
        requested_timeout = int(timeout_seconds)
    except (TypeError, ValueError):
        requested_timeout = 0
    timeout_valid = 1 <= requested_timeout <= SMTP_MAX_TIMEOUT_SECONDS
    timeout = requested_timeout if timeout_valid else SMTP_TIMEOUT_SECONDS
    base = {
        "delivery_id": identity["delivery_id"],
        "mail_key": identity["mail_key"],
        "content_revision_id": identity["content_revision_id"],
        "message_id": identity["message_id"],
        "validator_id": SMTP_DELIVERY_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "project_name": PROJECT_NAME,
        "generated_at": generated_at,
        "cycle_id": identity["cycle_id"],
        "product_id": identity["product_id"],
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
            "mail_key": identity["mail_key"],
            "mail_key_components": identity["mail_key_components"],
            "content_revision_id": identity["content_revision_id"],
            "body_sha256": identity["body_sha256"],
            "html_body_sha256": identity["html_body_sha256"],
            "html_alternative_present": bool(notification.html_body),
            "body_logged": False,
            "message_id": identity["message_id"],
            "resend_policy": "same_mail_key_and_content_revision_retry_keeps_message_id; content_revision_change_requires_explicit_supersede_or_resend",
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
    message = _email_message(notification, sender=username, identity=identity)
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
    sent["delivery_ref"] = f"smtp://message/{identity['delivery_id']}"
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
    elif (
        not message.get("mail_key")
        or not message.get("content_revision_id")
        or not str(message.get("message_id") or "").startswith("<")
        or "@" not in str(message.get("message_id") or "")
        or "supersede_or_resend" not in str(message.get("resend_policy") or "")
    ):
        errors.append("smtp delivery message identity must include mail_key, content_revision_id, standard Message-ID, and resend policy")
    if report.get("status") == "sent" and not report.get("delivery_ref"):
        errors.append("sent smtp delivery requires delivery_ref")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked smtp delivery requires blocking_reasons")
    if report.get("status") == "dry_run" and report.get("blocking_reasons"):
        errors.append("dry_run smtp delivery cannot include blocking_reasons")
    return errors


def _email_message(notification: EmailNotification, *, sender: str, identity: Mapping[str, Any]) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = notification.recipient
    message["Subject"] = notification.subject
    message["X-ADP-Delivery-ID"] = identity["delivery_id"]
    message["X-ADP-Mail-Key"] = identity["mail_key"]
    message["X-ADP-Content-Revision-ID"] = identity["content_revision_id"]
    message["Message-ID"] = identity["message_id"]
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


def _delivery_identity(
    notification: EmailNotification,
    *,
    generated_at: str,
    cycle_id: str | None,
    product_id: str,
    content_revision_id: str | None,
) -> dict[str, Any]:
    body_hash = hashlib.sha256(notification.body.encode("utf-8")).hexdigest()
    html_hash = hashlib.sha256(notification.html_body.encode("utf-8")).hexdigest() if notification.html_body else ""
    normalized_cycle_id = str(cycle_id or generated_at)
    normalized_product_id = str(product_id or "notification")
    mail_key = _mail_key(normalized_cycle_id, normalized_product_id, notification.recipient)
    revision_id = content_revision_id or _content_revision_id(notification, body_hash=body_hash, html_hash=html_hash)
    delivery_seed = "|".join([mail_key, revision_id])
    delivery_id = f"smtp-delivery:{hashlib.sha256(delivery_seed.encode('utf-8')).hexdigest()[:16]}"
    message_local = _message_id_local_part(
        "adp-"
        + hashlib.sha256("|".join(["message", mail_key, revision_id]).encode("utf-8")).hexdigest()[:24]
    )
    return {
        "cycle_id": normalized_cycle_id,
        "product_id": normalized_product_id,
        "mail_key": mail_key,
        "mail_key_components": {
            "cycle_id": normalized_cycle_id,
            "product_id": normalized_product_id,
            "recipient": notification.recipient,
        },
        "content_revision_id": revision_id,
        "delivery_id": delivery_id,
        "message_id": f"<{message_local}@{SMTP_MESSAGE_ID_DOMAIN}>",
        "body_sha256": body_hash,
        "html_body_sha256": html_hash,
    }


def _mail_key(cycle_id: str, product_id: str, recipient: str) -> str:
    payload = "|".join([cycle_id, product_id, recipient])
    return f"mail-key:{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def _content_revision_id(notification: EmailNotification, *, body_hash: str, html_hash: str) -> str:
    payload = "|".join([notification.subject, body_hash, html_hash])
    return f"content-revision:{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def _message_id_local_part(delivery_id: str) -> str:
    return "".join(character if character.isalnum() or character in {"-", "."} else "-" for character in delivery_id)
