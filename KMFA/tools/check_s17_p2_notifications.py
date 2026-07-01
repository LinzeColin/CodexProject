#!/usr/bin/env python3
"""Validate KMFA S17-P2 notification public-safe artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.notification_reminders import (
    DEFAULT_OUTPUT_DISPATCH_LOG,
    DEFAULT_OUTPUT_EVENTS,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_RULES,
    read_json,
    read_jsonl,
    validate_notification_reminder_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S17-P2 notification artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--rules", type=Path, default=DEFAULT_OUTPUT_RULES)
    parser.add_argument("--events", type=Path, default=DEFAULT_OUTPUT_EVENTS)
    parser.add_argument("--dispatch-log", type=Path, default=DEFAULT_OUTPUT_DISPATCH_LOG)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    rules = read_jsonl(args.rules)
    events = read_jsonl(args.events)
    dispatch_logs = read_jsonl(args.dispatch_log)

    validate_notification_reminder_artifacts(manifest, rules, events, dispatch_logs)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S17-P2 notification check passed "
        f"(rules={summary['notification_rule_count']}, "
        f"events={summary['notification_event_count']}, "
        f"dispatch_logs={summary['notification_dispatch_log_count']}, "
        "email_reminder_only=true, full_report_body=false, attachments=false, "
        "metadata_logs=true, stage17_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
