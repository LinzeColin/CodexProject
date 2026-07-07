from __future__ import annotations

import argparse
import json
from datetime import datetime, date
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .archive_reader import DwsArchiveReader
from .config_loader import load_yaml
from .ledger import connect, write_run_log
from .models import RoutineCheckResult, RoutineRule
from .rule_engine import evaluate_rule
from .schedule_rules import TRIGGER_WINDOWS, infer_trigger_window, rules_for_trigger_window

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RULES = REPO_ROOT / "KMFA" / "metadata" / "daily_routine_check" / "routine_rules.public.yaml"
DEFAULT_CASH = REPO_ROOT / "KMFA" / "metadata" / "daily_routine_check" / "cash_monitor.public.yaml"
DEFAULT_DB = REPO_ROOT / "KMFA" / "metadata" / "daily_routine_check" / "private_runtime" / "daily_routine_check.sqlite"
DEFAULT_STORAGE = REPO_ROOT / "KMFA" / "metadata" / "daily_routine_check" / "onedrive_storage_manifest.yaml"
DEFAULT_NOTIFICATION_TARGETS = REPO_ROOT / "KMFA" / "metadata" / "daily_routine_check" / "private_runtime" / "notification_targets.local.json"


def parse_date(value: str, tz: ZoneInfo) -> date:
    if value == "today":
        return datetime.now(tz).date()
    return date.fromisoformat(value)


def load_rules(path: str | Path) -> tuple[dict, list[RoutineRule]]:
    path = Path(path)
    raw = load_yaml(path)
    rules = []
    for item in raw.get("rules", []):
        required = tuple((item.get("required_senders") or {}).get("any_of", []))
        kw = item.get("keywords") or {}
        rules.append(RoutineRule(
            rule_id=item["rule_id"],
            group_name=item["group_name"],
            frequency=item["frequency"],
            due_time=item["due_time"],
            required_senders=required,
            artifact_name=item["artifact_name"],
            document_family=item.get("document_family", ""),
            keywords_positive=tuple(kw.get("positive", []) or []),
            keywords_negative=tuple(kw.get("negative", []) or []),
            weekdays=tuple(item.get("weekdays", []) or []),
            independent_required_artifact=bool(item.get("independent_required_artifact", True)),
            trigger_window=item.get("trigger_window", ""),
        ))
    return raw, rules


def build_run_summary(
    *,
    run_at_beijing: str,
    check_date: date,
    trigger_window: str,
    rules_evaluated: list[str],
    rules_skipped: list[str],
    data_quality_issues: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "timezone": "Asia/Shanghai",
        "run_at_beijing": run_at_beijing,
        "check_date": check_date.isoformat(),
        "trigger_window": trigger_window,
        "rules_evaluated": rules_evaluated,
        "rules_skipped": rules_skipped,
        "data_quality_issues": data_quality_issues,
    }


def flag_merged_results(results: list[RoutineCheckResult]) -> list[RoutineCheckResult]:
    by_message_id: dict[str, list[RoutineCheckResult]] = {}
    for result in results:
        if result.matched_message_id and result.status in {"OK", "LATE", "NEEDS_OCR_REVIEW", "NEEDS_REVIEW"}:
            by_message_id.setdefault(result.matched_message_id, []).append(result)

    for matched_results in by_message_id.values():
        if len({result.rule_id for result in matched_results}) < 2:
            continue
        for result in matched_results:
            result.status = "MERGED_REVIEW"
            result.abnormal_type = "merged"
            result.reminder_level = "P1"
            result.reason = "same message matched multiple independent routine rules"
            result.evidence["merged_rule_ids"] = sorted({item.rule_id for item in matched_results})
    return results


def build_notification_events(results: list[Any], data_quality_issues: list[dict[str, Any]], target_label: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for issue in data_quality_issues:
        issue_type = issue.get("issue_type")
        if issue_type in {"SOURCE_MISSING", "SOURCE_STALE"}:
            events.append({
                "event_type": issue_type,
                "target_label": target_label,
                "group_name": issue.get("group_name", ""),
                "idempotency_key": f"{issue_type}:{issue.get('group_name', '')}:{issue.get('check_date', '')}:{issue.get('issue_code', '')}",
                "payload": issue,
            })
    for result in results:
        if result.status == "MISSING":
            event_type = "MISSING_ROUTINE_ITEM"
        elif result.status == "LATE":
            event_type = "LATE_ROUTINE_ITEM"
        elif result.status == "WRONG":
            event_type = "WRONG_ROUTINE_ITEM"
        elif result.status == "MERGED_REVIEW":
            event_type = "MERGED_ROUTINE_ITEM"
        elif result.status in {"NEEDS_OCR_REVIEW", "NEEDS_REVIEW"}:
            event_type = "LOW_CONFIDENCE_ROUTINE_MATCH"
        else:
            continue
        events.append({
            "event_type": event_type,
            "target_label": target_label,
            "group_name": result.group_name,
            "rule_id": result.rule_id,
            "artifact_name": result.artifact_name,
            "idempotency_key": f"{event_type}:{result.check_date.isoformat()}:{result.rule_id}:{target_label}",
            "payload": {
                "check_date": result.check_date.isoformat(),
                "status": result.status,
                "abnormal_type": result.abnormal_type,
                "reminder_level": result.reminder_level,
                "matched_message_id": result.matched_message_id,
                "matched_sender_name": result.matched_sender_name,
                "confidence": result.confidence,
                "reason": result.reason,
                "evidence": result.evidence,
            },
        })
    return events


def notification_delivery_status(send_requested: bool, events: list[dict[str, Any]], target_config: Path = DEFAULT_NOTIFICATION_TARGETS) -> str:
    if not events:
        return "NO_EVENTS"
    if not send_requested:
        return "LOG_ONLY_DRY_RUN"
    if not target_config.exists():
        return "CONFIG_MISSING"
    return "READY_FOR_PRIVATE_NOTIFIER"


def append_onedrive_run_log(payload: dict[str, Any], check_date: date, storage_manifest_path: Path = DEFAULT_STORAGE) -> Path:
    storage = load_yaml(storage_manifest_path)
    private_output_root = Path(storage["private_output_root"]).expanduser()
    month = check_date.strftime("%Y%m")
    month_dir = private_output_root / month
    month_dir.mkdir(parents=True, exist_ok=True)
    log_path = month_dir / f"run_log_{month}.jsonl"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return log_path


def persist_run_log(run_id: str, payload: dict[str, Any]) -> dict[str, str]:
    check_date = date.fromisoformat(payload["check_date"])
    conn = connect(DEFAULT_DB)
    try:
        write_run_log(conn, run_id, payload)
    finally:
        conn.close()
    onedrive_log_path = append_onedrive_run_log(payload, check_date)
    return {
        "sqlite_path": str(DEFAULT_DB),
        "onedrive_run_log": str(onedrive_log_path),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="today")
    ap.add_argument("--timezone", default="Asia/Shanghai")
    ap.add_argument("--trigger-window", choices=sorted(TRIGGER_WINDOWS), default=None)
    ap.add_argument("--input-root", default=None)
    ap.add_argument("--rules", default=str(DEFAULT_RULES))
    ap.add_argument("--cash-config", default=str(DEFAULT_CASH))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--cleanup", action="store_true")
    args = ap.parse_args()

    if args.timezone != "Asia/Shanghai":
        raise SystemExit("Dingtalk-routine-check only supports --timezone Asia/Shanghai")

    tz = ZoneInfo("Asia/Shanghai")
    now = datetime.now(tz)
    check_date = parse_date(args.date, tz)
    raw_rules, rules = load_rules(Path(args.rules))
    input_root = Path(args.input_root or raw_rules.get("input_root_default")).expanduser()
    trigger_window = args.trigger_window or infer_trigger_window(now)
    rules_to_evaluate, rules_skipped = rules_for_trigger_window(rules, check_date, trigger_window)

    reader = DwsArchiveReader(input_root)
    group_names = sorted({r.group_name for r in rules_to_evaluate})
    data_quality_issues: list[dict[str, Any]] = []
    messages = []
    for group in group_names:
        data_quality_issues.extend(reader.inspect_group_sources(group, check_date))
        messages.extend(reader.read_messages(group))

    results = []
    for rule in rules_to_evaluate:
        result = evaluate_rule(rule, messages, check_date, now)
        if result is not None:
            results.append(result)
    results = flag_merged_results(results)
    notification_events = build_notification_events(results, data_quality_issues, raw_rules.get("notify_target_label", "张霖泽"))

    run_summary = build_run_summary(
        run_at_beijing=now.isoformat(timespec="seconds"),
        check_date=check_date,
        trigger_window=trigger_window,
        rules_evaluated=[rule.rule_id for rule in rules_to_evaluate],
        rules_skipped=[rule.rule_id for rule in rules_skipped],
        data_quality_issues=data_quality_issues,
    )

    output = {
        "run_id": f"drc_{now.strftime('%Y%m%dT%H%M%S')}_{trigger_window}",
        "automation_name": raw_rules.get("automation_name"),
        "chinese_name": raw_rules.get("chinese_name"),
        "input_root": str(input_root),
        "dry_run": args.dry_run,
        "send": args.send,
        **run_summary,
        "results": [r.__dict__ | {"check_date": r.check_date.isoformat()} for r in results],
        "notification_target": raw_rules.get("notify_target_label"),
        "notification_events": notification_events,
        "notification_delivery_status": notification_delivery_status(args.send, notification_events),
    }
    if not args.dry_run:
        output["persistence"] = persist_run_log(output["run_id"], output)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
