#!/usr/bin/env python3
"""Manage local KMFA DingTalk attendance notification targets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from KMFA.tools.dingtalk_attendance.notification_targets import (
    disable_target,
    list_targets,
    probe_notification_targets,
    upsert_target,
)


def add_person_target(*, label: str, user_id: str | None = None, name: str | None = None, mobile: str | None = None) -> dict[str, Any]:
    target: dict[str, Any] = {
        "label": label,
        "type": "personal",
        "enabled": True,
        "reports": ["management", "hr"],
    }
    if user_id:
        target["user_id"] = user_id
        target["preferred_channel"] = "dws_open_dingtalk_id_chat"
    if name:
        target["name"] = name
    if mobile:
        target["mobile"] = mobile
    update_result = upsert_target(target=target)
    probe_result = probe_notification_targets(label_filter=label)
    return {"status": probe_result["status"], "update": update_result, "probe": probe_result}


def add_group_target(
    *,
    label: str,
    group_name: str | None = None,
    conversation_id: str | None = None,
    webhook_env_key: str | None = None,
    secret_env_key: str | None = None,
) -> dict[str, Any]:
    target: dict[str, Any] = {
        "label": label,
        "type": "group",
        "enabled": True,
        "reports": ["management", "hr"],
    }
    if group_name:
        target["group_name"] = group_name
    if conversation_id:
        target["conversation_id"] = conversation_id
    if webhook_env_key:
        target["webhook_env_key"] = webhook_env_key
    if secret_env_key:
        target["secret_env_key"] = secret_env_key
    update_result = upsert_target(target=target)
    probe_result = probe_notification_targets(label_filter=label)
    return {"status": probe_result["status"], "update": update_result, "probe": probe_result}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage KMFA DingTalk attendance notification targets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_person = subparsers.add_parser("add-person")
    add_person.add_argument("--label", required=True)
    person_identity = add_person.add_mutually_exclusive_group(required=True)
    person_identity.add_argument("--user-id")
    person_identity.add_argument("--name")
    person_identity.add_argument("--mobile")

    add_group = subparsers.add_parser("add-group")
    add_group.add_argument("--label", required=True)
    group_identity = add_group.add_mutually_exclusive_group(required=True)
    group_identity.add_argument("--group-name")
    group_identity.add_argument("--conversation-id")

    add_webhook = subparsers.add_parser("add-group-webhook")
    add_webhook.add_argument("--label", required=True)
    add_webhook.add_argument("--webhook-env-key", required=True)
    add_webhook.add_argument("--secret-env-key", required=True)

    disable = subparsers.add_parser("disable")
    disable.add_argument("--label", required=True)

    subparsers.add_parser("list")

    args = parser.parse_args(argv)
    if args.command == "add-person":
        result = add_person_target(label=args.label, user_id=args.user_id, name=args.name, mobile=args.mobile)
    elif args.command == "add-group":
        result = add_group_target(label=args.label, group_name=args.group_name, conversation_id=args.conversation_id)
    elif args.command == "add-group-webhook":
        result = add_group_target(label=args.label, webhook_env_key=args.webhook_env_key, secret_env_key=args.secret_env_key)
    elif args.command == "disable":
        result = disable_target(label=args.label)
    else:
        result = list_targets()

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") in {"OK", "SENT", "PARTIAL"} or args.command == "list" else 2


if __name__ == "__main__":
    sys.exit(main())
