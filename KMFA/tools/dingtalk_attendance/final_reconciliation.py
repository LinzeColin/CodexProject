#!/usr/bin/env python3
"""Create a send-disabled final reconciliation from DingTalk's official report."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from KMFA.tools.dingtalk_attendance import ONEDRIVE_ROOT, TIMEZONE
from KMFA.tools.dingtalk_attendance.cleanup_runtime import cleanup_runtime
from KMFA.tools.dingtalk_attendance.delivery_policy import (
    DELIVERY_DISABLED_STATUS,
    write_delivery_disabled_receipt,
)
from KMFA.tools.dingtalk_attendance.dws_attendance import (
    DwsAttendanceError,
    OfficialAttendanceParityError,
    collect_official_org_attendance,
    write_private_outputs,
)
from KMFA.tools.dingtalk_attendance.dws_auth_guard import (
    DWS_COMMAND_ALLOW_ENV,
    dws_command_safety_status,
)
from KMFA.tools.dingtalk_attendance.identity import (
    IdentityConflictError,
    archive_manifest_paths,
    run_type_from_run_id,
    validate_manifest_identity,
)
from KMFA.tools.dingtalk_attendance.notification_template import official_report_parity_failure_reason
from KMFA.tools.dingtalk_attendance.official_report_reconstruction import (
    INDEPENDENT_EVIDENCE_KIND,
    validate_reconciliation_certificate,
)
from KMFA.tools.dingtalk_attendance.onedrive_archive import archive_paths_for_run
from KMFA.tools.dingtalk_attendance.run_attendance import build_run_plan


FINAL_RESULT_KIND = "OFFICIAL_FINAL_RECONCILIATION"


def build_one_page_result(
    *,
    work_date: str,
    morning: Mapping[str, Any],
    evening: Mapping[str, Any],
    final_stats: Mapping[str, Any],
    final_run_id: str,
    independent_evidence_status: str = "EVIDENCE_MISSING",
) -> str:
    """Render an aggregate-only page; names and report bodies stay out of this artifact."""
    lines = [
        "# 晨间提醒—晚间提醒—官方最终核对",
        "",
        f"- 工作日：{work_date}",
        "- 当前可用性：UNAVAILABLE",
        "- 结果依据：INDEPENDENT_OFFICIAL_EXPORT_REQUIRED",
        "- 发送状态：关闭",
        f"- 官方最终核对：{independent_evidence_status}",
        f"- final run：{final_run_id}",
        "",
        "| 阶段 | 证据状态 | 身份类别 | official parity | 与最终核对关系 |",
        "|---|---|---|---|---|",
        _reminder_table_row("晨间暂时提醒", morning, final_stats),
        _reminder_table_row("晚间暂时提醒", evening, final_stats),
        "",
        "## 官方最终核对汇总",
        "",
        f"- 覆盖人数：{_safe_count(final_stats, 'official_report_coverage_count')}",
        f"- 应考勤人数：{_safe_count(final_stats, 'attendance_required_count')}",
        f"- 有效出勤人数：{_safe_count(final_stats, 'official_effective_day_count')}",
        f"- 异常人数：{_safe_count(final_stats, 'official_report_anomaly_count')}",
        "- 月累计来源：仅 canonical final archives；legacy、morning、evening archives 均不参与",
        "- production acceptance：NOT_EVALUATED",
        "- owner usability：NOT_ACCEPTED",
        "",
        "只有独立官方导出原件与对应 DWS raw 完成逐员工、48 个必需列零缺失零差异对账时，本页才可标记 PASS；部门仅为可选展示字段，DWS 内部检查不能替代该证据。",
        "",
    ]
    return "\n".join(lines)


def run_final_reconciliation(
    *,
    work_date: str,
    timezone: str = TIMEZONE,
    allow_dws_commands: bool = False,
    env: Mapping[str, str] | None = None,
    onedrive_root: Path = Path(ONEDRIVE_ROOT),
    collector: Callable[..., dict[str, Any]] = collect_official_org_attendance,
    cleanup: Callable[[], dict[str, Any]] = cleanup_runtime,
    now: datetime | None = None,
    independent_evidence_path: Path | None = None,
) -> dict[str, Any]:
    current = now or datetime.now(ZoneInfo(timezone))
    target = _validated_final_work_date(work_date, timezone=timezone, current=current)
    evidence = _load_independent_reconciliation_evidence(independent_evidence_path, work_date=work_date)
    if evidence["status"] != "PASS":
        return {
            "status": evidence["status"],
            "work_date": work_date,
            "notification_status": DELIVERY_DISABLED_STATUS,
            "independent_evidence_status": evidence["evidence_status"],
            "failure_reason": evidence["failure_reason"],
            "cleanup_status": cleanup(),
        }
    safety = dws_command_safety_status(env=env, allow_override=allow_dws_commands)
    if safety["status"] != "READY":
        return {
            "status": "DWS_AUTH_REQUIRED",
            "work_date": work_date,
            "notification_status": DELIVERY_DISABLED_STATUS,
            "dws_command_safety": safety,
            "cleanup_status": cleanup(),
        }

    os.environ[DWS_COMMAND_ALLOW_ENV] = "1"
    summary_datetime = current.strftime("%Y-%m-%d %H:%M:%S")
    try:
        collection = collector(work_date=work_date, summary_datetime=summary_datetime)
        parity_failure = official_report_parity_failure_reason(collection.get("stats", {}))
        if parity_failure:
            raise OfficialAttendanceParityError("OFFICIAL_REPORT_PARITY_ASSERTION_FAILED", parity_failure)
    except OfficialAttendanceParityError as exc:
        return {
            "status": "OFFICIAL_ATTENDANCE_PARITY_FAILED",
            "work_date": work_date,
            "notification_status": DELIVERY_DISABLED_STATUS,
            "failure_reason": str(exc),
            "cleanup_status": cleanup(),
        }
    except (DwsAttendanceError, FileNotFoundError, TimeoutError) as exc:
        return {
            "status": "DWS_UNAVAILABLE",
            "work_date": work_date,
            "notification_status": DELIVERY_DISABLED_STATUS,
            "failure_reason": str(exc),
            "cleanup_status": cleanup(),
        }

    plan = build_run_plan(run_type="final", timezone=timezone, run_datetime=current)
    plan["archive_paths"] = archive_paths_for_run(
        plan["run_id"],
        target,
        onedrive_root=onedrive_root,
    )
    plan["onedrive_root"] = str(onedrive_root)
    output = write_private_outputs(
        plan=plan,
        collection=collection,
        cleanup_status={"status": "PENDING_FINAL_RECONCILIATION"},
    )
    receipt = write_delivery_disabled_receipt(
        {
            **output,
            "run_id": plan["run_id"],
            "run_type": "final",
            "work_date": work_date,
        }
    )
    morning = find_reminder_evidence(onedrive_root=onedrive_root, work_date=work_date, run_type="morning")
    evening = find_reminder_evidence(onedrive_root=onedrive_root, work_date=work_date, run_type="evening")
    page = build_one_page_result(
        work_date=work_date,
        morning=morning,
        evening=evening,
        final_stats=collection["stats"],
        final_run_id=plan["run_id"],
        independent_evidence_status="PASS",
    )
    page_path = Path(plan["archive_paths"]["one_page_result"])
    page_path.write_text(page, encoding="utf-8")
    manifest_path = Path(output["archive_manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "result_kind": FINAL_RESULT_KIND,
            "one_page_result": str(page_path),
            "notification_status": receipt["notification_status"],
            "monthly_rollup_eligible": True,
        }
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    cleanup_status = cleanup()
    Path(output["cleanup_audit"]).write_text(
        json.dumps(cleanup_status, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "status": "OFFICIAL_FINAL_RECONCILIATION_PASS",
        "work_date": work_date,
        "result_kind": FINAL_RESULT_KIND,
        "notification_status": receipt["notification_status"],
        "one_page_result": str(page_path),
        "archive_manifest": str(manifest_path),
        "official_report_parity_status": collection["stats"]["official_report_parity_status"],
        "independent_evidence_status": "PASS",
        "morning_evidence_status": morning["evidence_status"],
        "evening_evidence_status": evening["evidence_status"],
        "cleanup_status": cleanup_status,
    }


def _load_independent_reconciliation_evidence(path: Path | None, *, work_date: str) -> dict[str, str]:
    if path is None:
        return {
            "status": "OFFICIAL_EVIDENCE_MISSING",
            "evidence_status": "EVIDENCE_MISSING",
            "failure_reason": "an independently exported DingTalk attendance workbook and full-column reconciliation evidence are required",
        }
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "status": "OFFICIAL_EVIDENCE_MISSING",
            "evidence_status": "EVIDENCE_MISSING",
            "failure_reason": "independent reconciliation evidence is missing or unreadable",
        }
    validation_errors = validate_reconciliation_certificate(evidence, expected_work_date=work_date)
    if validation_errors:
        return {
            "status": "OFFICIAL_FINAL_RECONCILIATION_BLOCKED",
            "evidence_status": "BLOCKED",
            "failure_reason": "independent official-export reconciliation certificate is invalid: "
            + ", ".join(validation_errors),
        }
    return {"status": "PASS", "evidence_status": "PASS", "failure_reason": ""}


def find_reminder_evidence(
    *,
    onedrive_root: Path,
    work_date: str,
    run_type: str,
) -> dict[str, Any]:
    month_dir = onedrive_root / work_date[:7].replace("-", "")
    candidates: list[tuple[str, dict[str, Any], str]] = []
    for path in archive_manifest_paths(month_dir):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            run_id = str(manifest.get("run_id") or path.name.removesuffix(".manifest.json"))
            if run_type_from_run_id(run_id) != run_type or str(manifest.get("work_date") or "") != work_date:
                continue
            identity = validate_manifest_identity(manifest)
        except (OSError, json.JSONDecodeError, IdentityConflictError):
            continue
        candidates.append((path.name, manifest, identity["identity_source"]))
    if not candidates:
        return {
            "evidence_status": "MISSING",
            "identity_source": "NONE",
            "official_parity": "UNKNOWN",
            "notification_status": "UNKNOWN",
        }
    _, manifest, identity_source = max(candidates, key=lambda item: item[0])
    stats = manifest.get("stats", {})
    if not isinstance(stats, Mapping):
        stats = {}
    notification_status = "UNKNOWN"
    receipt_path = manifest.get("dispatch_receipt")
    if receipt_path:
        try:
            receipt = json.loads(Path(str(receipt_path)).read_text(encoding="utf-8"))
            notification_status = str(receipt.get("notification_status") or "UNKNOWN")
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "evidence_status": "FOUND",
        "identity_source": identity_source,
        "official_parity": str(stats.get("official_report_parity_status") or "UNKNOWN"),
        "notification_status": notification_status,
        "official_report_coverage_count": stats.get("official_report_coverage_count"),
        "attendance_required_count": stats.get("attendance_required_count"),
        "official_effective_day_count": stats.get("official_effective_day_count"),
        "official_report_anomaly_count": stats.get("official_report_anomaly_count"),
    }


def find_latest_pending_work_date(
    *,
    onedrive_root: Path = Path(ONEDRIVE_ROOT),
    timezone: str = TIMEZONE,
    now: datetime | None = None,
) -> str | None:
    """Find the latest canonical evening reminder that has no canonical final result."""
    current = now or datetime.now(ZoneInfo(timezone))
    today = current.astimezone(ZoneInfo(timezone)).date().isoformat()
    evening_dates: set[str] = set()
    final_dates: set[str] = set()
    for month_dir in onedrive_root.glob("20[0-9][0-9][0-9][0-9]"):
        if not month_dir.is_dir():
            continue
        for path in archive_manifest_paths(month_dir):
            try:
                manifest = json.loads(path.read_text(encoding="utf-8"))
                identity = validate_manifest_identity(manifest)
                if identity["identity_source"] != "skill_id":
                    continue
                run_id = str(manifest.get("run_id") or path.name.removesuffix(".manifest.json"))
                work_date = str(manifest.get("work_date") or "")
            except (OSError, json.JSONDecodeError, IdentityConflictError):
                continue
            if not work_date or work_date >= today:
                continue
            if run_type_from_run_id(run_id) == "evening":
                evening_dates.add(work_date)
            elif run_type_from_run_id(run_id) == "final":
                final_dates.add(work_date)
    pending = sorted(evening_dates - final_dates)
    return pending[-1] if pending else None


def _validated_final_work_date(work_date: str, *, timezone: str, current: datetime) -> datetime:
    try:
        target = datetime.strptime(work_date, "%Y-%m-%d").replace(tzinfo=ZoneInfo(timezone))
    except ValueError as exc:
        raise ValueError("work_date must be YYYY-MM-DD") from exc
    if target.date() >= current.astimezone(ZoneInfo(timezone)).date():
        raise ValueError("official final reconciliation requires a completed prior work date")
    return target


def _reminder_table_row(label: str, reminder: Mapping[str, Any], final_stats: Mapping[str, Any]) -> str:
    comparison = _comparison_with_final(reminder, final_stats)
    return "| {label} | {evidence} | {identity} | {parity} | {comparison} |".format(
        label=label,
        evidence=str(reminder.get("evidence_status") or "UNKNOWN"),
        identity=str(reminder.get("identity_source") or "UNKNOWN"),
        parity=str(reminder.get("official_parity") or "UNKNOWN"),
        comparison=comparison,
    )


def _comparison_with_final(reminder: Mapping[str, Any], final_stats: Mapping[str, Any]) -> str:
    if reminder.get("official_parity") != "PASS":
        return "UNVERIFIED_REMINDER"
    keys = (
        "official_report_coverage_count",
        "attendance_required_count",
        "official_effective_day_count",
        "official_report_anomaly_count",
    )
    if any(reminder.get(key) is None for key in keys):
        return "EVIDENCE_MISSING"
    return "MATCH" if all(reminder.get(key) == final_stats.get(key) for key in keys) else "CHANGED_AFTER_FINAL"


def _safe_count(stats: Mapping[str, Any], key: str) -> str:
    value = stats.get(key)
    return str(value) if isinstance(value, int) and value >= 0 else "UNKNOWN"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create the send-disabled official final attendance reconciliation.")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--work-date")
    selection.add_argument("--latest-pending", action="store_true")
    parser.add_argument("--timezone", default=TIMEZONE)
    parser.add_argument("--allow-dws-commands", action="store_true")
    parser.add_argument("--independent-reconciliation-evidence", type=Path)
    args = parser.parse_args(argv)
    work_date = args.work_date
    if args.latest_pending:
        work_date = find_latest_pending_work_date(timezone=args.timezone)
        if work_date is None:
            print(json.dumps({"status": "NO_PENDING_FINAL_RECONCILIATION"}, ensure_ascii=False))
            return 0
    result = run_final_reconciliation(
        work_date=str(work_date),
        timezone=args.timezone,
        allow_dws_commands=args.allow_dws_commands,
        independent_evidence_path=args.independent_reconciliation_evidence,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") == "OFFICIAL_FINAL_RECONCILIATION_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
