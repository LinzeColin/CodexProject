import gzip
import hashlib
import importlib
import json
import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

from KMFA.tools.dingtalk_attendance.healthcheck import build_config_status
from KMFA.tools.dingtalk_attendance.dws_auth_guard import dws_command_safety_status
from KMFA.tools.dingtalk_attendance.notification_probe import probe_notification_channels
from KMFA.tools.dingtalk_attendance.notification_template import (
    collection_is_complete,
    notification_context_from_output_status,
    official_report_parity_failure_reason,
)
from KMFA.tools.dingtalk_attendance.notification_targets import (
    dispatch_reports_to_targets,
    migrate_legacy_resolved_channel,
    probe_notification_targets,
)
from KMFA.tools.dingtalk_attendance.notifier_dws_personal_chat import (
    dispatch_reports_with_resolved_channel,
    get_dws_help,
    run_dws_command,
    send_dws_chat_message,
)
from KMFA.tools.dingtalk_attendance.notifier_dingtalk import (
    build_signed_robot_url,
    send_group_robot_markdown,
)
from KMFA.tools.dingtalk_attendance.report_renderer import (
    MANAGEMENT_REPORT_SECTIONS,
    HR_REPORT_SECTIONS,
)
from KMFA.tools.dingtalk_attendance.dws_attendance import (
    DwsAttendanceError,
    OfficialAttendanceParityError,
    RealtimeReminderIntegrityError,
    _query_official_report,
    collect_official_org_attendance,
    collect_org_attendance,
    collect_realtime_reminder_attendance,
    run_dws_json,
    write_private_outputs,
)
from KMFA.tools.dingtalk_attendance.collection_integrity import (
    realtime_reminder_integrity_failure_reason,
)
from KMFA.tools.dingtalk_attendance.run_attendance import (
    build_monthly_notification_rollups,
    build_monthly_rest_required_people,
    build_notification_message,
    build_personal_notification_message,
    build_run_plan,
    build_stats_with_rest_required_people,
    dispatch_reports_to_robot,
    run_attendance,
)
from KMFA.tools.dingtalk_attendance.send_latest_report import send_latest_report
from KMFA.tools.dingtalk_attendance.sync_attendance_ledger import (
    DEFAULT_LEDGER_PATH,
    initialize_ledger,
    sync_archives_to_ledger,
    validate_ledger,
)
from KMFA.tools.dingtalk_attendance.query_attendance_ledger import (
    LedgerSchemaUpgradeRequired,
    get_employee_month_effective_days,
    get_month_anomalies,
    get_month_rest_required_people,
    get_month_summary,
    get_run_sync_status,
)
from KMFA.tools.dingtalk_attendance.check_dingtalk_attendance import validate_dingtalk_attendance_files
from KMFA.tools.dingtalk_attendance.validate_no_sensitive_git import scan_payload_for_sensitive_text


ROOT = Path(__file__).resolve().parents[1]
ATTENDANCE_RUNNER = importlib.import_module("KMFA.tools.dingtalk_attendance.run_attendance")


def _official_pass_stats(
    *,
    member_count: int = 2,
    anomaly_names: list[str] | None = None,
) -> dict[str, object]:
    names = list(anomaly_names or [])
    return {
        "attendance_group_member_count": member_count,
        "member_count": member_count,
        "official_report_parity_status": "PASS",
        "official_report_expected_count": member_count,
        "official_report_coverage_count": member_count,
        "official_report_failure_count": 0,
        "official_report_anomaly_count": len(names),
        "official_report_anomaly_names": names,
        "official_effective_day_count": max(member_count - len(names), 0),
        "attendance_required_count": member_count,
        "attendance_anomaly_count": len(names),
        "attendance_anomaly_names": names,
    }


def _realtime_pass_stats(
    *,
    run_type: str = "evening",
    member_count: int = 2,
    anomaly_names: list[str] | None = None,
) -> dict[str, object]:
    names = list(anomaly_names or [])
    return {
        "attendance_group_member_count": member_count,
        "member_count": member_count,
        "realtime_reminder_integrity_status": "PASS",
        "realtime_reminder_run_type": run_type,
        "realtime_reminder_expected_count": member_count,
        "realtime_reminder_coverage_count": member_count,
        "realtime_reminder_query_failure_count": 0,
        "realtime_reminder_parse_failure_count": 0,
        "realtime_reminder_anomaly_count": len(names),
        "realtime_reminder_anomaly_names": names,
        "attendance_anomaly_count": len(names),
        "attendance_anomaly_names": names,
    }


def _write_certificate_bound_final_manifest(
    month_dir: Path,
    *,
    run_id: str,
    work_date: str,
    people: int,
) -> None:
    certificate = {
        "schema": "kmfa.dingtalk_attendance.official_reconciliation.v1",
        "evidence_kind": "INDEPENDENT_OFFICIAL_EXPORT_VS_DWS",
        "official_sha256": "d" * 64,
        "work_date": work_date,
        "status": "PASS",
        "official_people": people,
        "dws_people": people,
        "matched_people": people,
        "compared_columns": 48,
        "compared_cells": people * 48,
        "missing_people": 0,
        "extra_people": 0,
        "missing_required_columns": 0,
        "missing_required_cells": 0,
        "differing_required_cells": 0,
        "optional_unverified_fields": ["部门"],
    }
    (month_dir / f"{run_id}.manifest.json").write_text(
        json.dumps(
            {
                "skill_id": "kmfa-dingtalk-attendance-skill",
                "run_id": run_id,
                "work_date": work_date,
                "result_kind": "OFFICIAL_FINAL_RECONCILIATION",
                "monthly_rollup_eligible": True,
                "official_reconciliation_certificate": certificate,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _write_ledger_fixture_run(
    root: Path,
    *,
    run_id: str,
    work_date: str,
    employees: list[dict[str, object]],
    stats_override: dict[str, object] | None = None,
    dispatch_payload: dict[str, object] | None = None,
) -> dict[str, Path]:
    month_dir = root / work_date[:7].replace("-", "")
    month_dir.mkdir(parents=True, exist_ok=True)
    raw_path = month_dir / f"{run_id}.raw.jsonl.gz"
    stats = {
        "member_count": len(employees),
        "record_success_count": sum(1 for item in employees if item.get("record_success", True)),
        "summary_success_count": sum(1 for item in employees if item.get("summary_success", True)),
        "record_failure_count": sum(1 for item in employees if not item.get("record_success", True)),
        "summary_failure_count": sum(1 for item in employees if not item.get("summary_success", True)),
        "command_failure_count": sum(1 for item in employees if not item.get("record_success", True))
        + sum(1 for item in employees if not item.get("summary_success", True)),
        "attendance_anomaly_count": 0,
        "attendance_anomaly_names": [],
    }
    if stats_override:
        stats.update(stats_override)
    with gzip.open(raw_path, "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "type": "metadata",
                    "run_plan": {"run_id": run_id, "run_type": "evening"},
                    "stats": stats,
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        for item in employees:
            punches = item.get("punches", [])
            assert isinstance(punches, list)
            record_success = bool(item.get("record_success", True))
            summary_success = bool(item.get("summary_success", True))
            member = {"name": item["name"], "userId": item["user_id"]}
            handle.write(
                json.dumps(
                    {
                        "type": "employee_attendance",
                        "member": member,
                        "work_date": work_date,
                        "record": {
                            "final": {
                                "returncode": 0 if record_success else 1,
                                "payload": {
                                    "success": record_success,
                                    "result": {
                                        "recordList": punches,
                                        "isHasSchedule": True,
                                        "isRest": False,
                                    },
                                    "error": {} if record_success else {"server_error_code": "TOKEN_VERIFIED_FAILED"},
                                },
                            }
                        },
                        "summary": {
                            "final": {
                                "returncode": 0 if summary_success else 1,
                                "payload": {
                                    "success": summary_success,
                                    "result": {
                                        "abnormalCount": 0,
                                        "items": item.get("summary_items", []),
                                    },
                                    "error": {} if summary_success else {"server_error_code": "SUMMARY_FAILED"},
                                },
                            }
                        },
                        "derived": {
                            "record_success": record_success,
                            "summary_success": summary_success,
                            "record_count": len(punches),
                            "record_has_full_day": _fixture_has_full_day(punches),
                            "record_anomaly": bool(item.get("record_anomaly", False)),
                            "summary_today_anomaly": bool(item.get("summary_today_anomaly", False)),
                            "summary_today_issues": item.get("summary_today_issues", []),
                            "known_no_record": bool(item.get("known_no_record", False)),
                            **(
                                {"official_effective_day": bool(item.get("official_effective_day"))}
                                if "official_effective_day" in item
                                else {}
                            ),
                            **(
                                {
                                    "official_report_anomaly": bool(item.get("official_report_anomaly")),
                                    "official_report_issues": item.get("official_report_issues", []),
                                }
                                if "official_report_anomaly" in item
                                else {}
                            ),
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    manifest_path = month_dir / f"{run_id}.manifest.json"
    raw_hash = __import__("hashlib").sha256(raw_path.read_bytes()).hexdigest()
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "skill_id": "kmfa-dingtalk-attendance-skill",
                "backend": "dws",
                "raw_jsonl_gz": str(raw_path),
                "raw_jsonl_gz_sha256": raw_hash,
                "management_report": str(month_dir / f"{run_id}.management.md"),
                "hr_report": str(month_dir / f"{run_id}.hr.md"),
                "dispatch_receipt": str(month_dir / f"{run_id}.dispatch.json"),
                "cleanup_audit": str(month_dir / f"{run_id}.cleanup.json"),
                "stats": stats,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    dispatch_path = month_dir / f"{run_id}.dispatch.json"
    dispatch_path.write_text(
        json.dumps(
            dispatch_payload
            or {
                "notification_status": "SENT",
                "target_results": [
                    {
                        "label": "张霖泽",
                        "type": "personal",
                        "channel": "dws_open_dingtalk_id_chat",
                        "management_status": "SENT",
                        "hr_status": "SENT",
                        "trace_id_present": False,
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    cleanup_path = month_dir / f"{run_id}.cleanup.json"
    cleanup_path.write_text(json.dumps({"status": "OK"}, ensure_ascii=False), encoding="utf-8")
    return {"raw": raw_path, "manifest": manifest_path, "dispatch": dispatch_path, "cleanup": cleanup_path}


def _fixture_punches(*, morning: bool = True, evening: bool = True) -> list[dict[str, str]]:
    punches: list[dict[str, str]] = []
    if morning:
        punches.append({"checkTypeDesc": "上班", "userCheckTime": "2026-06-01 08:31:00"})
    if evening:
        punches.append({"checkTypeDesc": "下班", "userCheckTime": "2026-06-01 18:19:00"})
    return punches


def _fixture_has_full_day(punches: list[object]) -> bool:
    text = json.dumps(punches, ensure_ascii=False)
    return "上班" in text and "下班" in text


class FakeDwsRunner:
    def __init__(self, *, fail_first_record_for: str | None = None) -> None:
        self.calls: list[tuple[tuple[str, ...], bool]] = []
        self.timeouts: list[tuple[tuple[str, ...], int]] = []
        self.fail_first_record_for = fail_first_record_for
        self.failed_once = False

    def __call__(self, args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
        self.calls.append((tuple(args), verbose))
        self.timeouts.append((tuple(args), timeout))
        if args == ["contact", "dept", "list-children", "--dept", "1"]:
            return {"returncode": 0, "payload": {"success": True, "result": [{"deptId": 100, "deptName": "生产部"}]}}
        if args == ["contact", "dept", "list-children", "--dept", "100"]:
            return {"returncode": 0, "payload": {"success": True, "result": []}}
        if args == ["contact", "dept", "list-members", "--depts", "1,100"]:
            return {
                "returncode": 0,
                "payload": {
                    "success": True,
                    "deptUserList": [
                        {"userInfo": {"name": "张霖泽", "userId": "zhang-dws-id"}},
                        {"userInfo": {"name": "林全意", "userId": "lin-dws-id"}},
                        {"userInfo": {"name": "李同林", "userId": "li-dws-id"}},
                    ],
                },
            }
        if args[:4] == ["attendance", "record", "get", "--user"]:
            user_id = args[4]
            if self.fail_first_record_for == user_id and not self.failed_once:
                self.failed_once = True
                return {"returncode": 1, "payload": {"error": {"server_error_code": "PAT_AUTH_CALL_FAILED"}}}
            record_list = [] if user_id in {"zhang-dws-id", "lin-dws-id"} else [{"checkTypeDesc": "上班"}, {"checkTypeDesc": "下班"}]
            return {
                "returncode": 0,
                "payload": {"success": True, "code": "0", "result": {"recordList": record_list, "isHasSchedule": True, "isRest": False}},
            }
        if args[:3] == ["attendance", "summary", "--user"]:
            return {
                "returncode": 0,
                "payload": {
                    "success": True,
                    "code": "0",
                    "result": {
                        "abnormalCount": 0,
                        "items": [{"id": "RealAttend_Y", "name": "出勤天数", "remark": "1天"}],
                    },
                },
            }
        raise AssertionError(f"unexpected dws args: {args}")


class OfficialParityFixtureRunner:
    REQUIRED_COLUMNS = (
        "考勤结果",
        "应出勤天数",
        "出勤天数",
        "休息天数",
        "迟到次数",
        "早退次数",
        "上班缺卡次数",
        "下班缺卡次数",
        "旷工天数",
    )

    def __init__(
        self,
        *,
        omit_user: str | None = None,
        omit_column: str | None = None,
        status_overrides: dict[str, str] | None = None,
        date_overrides: dict[str, str] | None = None,
    ) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.omit_user = omit_user
        self.omit_column = omit_column
        self.status_overrides = status_overrides or {}
        self.date_overrides = date_overrides or {}
        self.column_ids = {name: f"c-{index}" for index, name in enumerate(self.REQUIRED_COLUMNS, start=1)}

    def __call__(self, args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
        self.calls.append(tuple(args))
        if args == ["contact", "dept", "list-children", "--dept", "1"]:
            return {"returncode": 0, "payload": {"success": True, "result": []}}
        if args == ["contact", "dept", "list-members", "--depts", "1"]:
            return {
                "returncode": 0,
                "payload": {
                    "success": True,
                    "deptUserList": [
                        {"userInfo": {"name": "正常员工", "userId": "u-normal"}},
                        {"userInfo": {"name": "异常员工", "userId": "u-anomaly"}},
                        {"userInfo": {"name": "非考勤组员工", "userId": "u-outside"}},
                    ],
                },
            }
        if args[:4] == ["attendance", "record", "get", "--user"]:
            user_id = args[4]
            record_list = (
                [{"checkTypeDesc": "上班", "isNormal": True}, {"checkTypeDesc": "下班", "isNormal": True}]
                if user_id == "u-normal"
                else [{"checkTypeDesc": "上班", "isNormal": True}]
            )
            return {
                "returncode": 0,
                "payload": {
                    "success": True,
                    "result": {"recordList": record_list, "isHasSchedule": True, "isRest": False},
                },
            }
        if args[:3] == ["attendance", "summary", "--user"]:
            return {
                "returncode": 0,
                "payload": {"success": True, "result": {"abnormalCount": 0, "items": []}},
            }
        if args[:3] == ["attendance", "group", "search"]:
            return {
                "returncode": 0,
                "payload": {
                    "success": True,
                    "result": {"items": [{"id": 101, "name": "测试考勤组"}], "totalCount": 1},
                },
            }
        if args[:3] == ["attendance", "group", "filtered-get"]:
            return {
                "returncode": 0,
                "payload": {
                    "success": True,
                    "result": {"id": 101, "memberUsers": ["u-normal", "u-anomaly"]},
                },
            }
        if args == ["attendance", "report", "columns"]:
            return {
                "returncode": 0,
                "payload": {
                    "success": True,
                    "result": [
                        {"id": column_id, "name": name}
                        for name, column_id in self.column_ids.items()
                        if name != self.omit_column
                    ],
                },
            }
        if args[:3] == ["attendance", "report", "query-data"]:
            requested = args[args.index("--users") + 1].split(",")
            rows = []
            for user_id in requested:
                if user_id == self.omit_user:
                    continue
                status = self.status_overrides.get(
                    user_id,
                    "旷工" if user_id == "u-anomaly" else "正常",
                )
                values = {
                    "考勤结果": status,
                    "应出勤天数": "1",
                    "出勤天数": "0" if user_id == "u-anomaly" else "1",
                    "休息天数": "0",
                    "迟到次数": "0",
                    "早退次数": "0",
                    "上班缺卡次数": "0",
                    "下班缺卡次数": "0",
                    "旷工天数": "1" if user_id == "u-anomaly" else "0",
                }
                rows.append(
                    {
                        "userId": user_id,
                        "workDate": self.date_overrides.get(user_id, "2026-07-11"),
                        "values": [
                            {"termId": self.column_ids[name], "value": value}
                            for name, value in values.items()
                        ],
                    }
                )
            return {"returncode": 0, "payload": {"success": True, "result": {"records": rows}}}
        raise AssertionError(f"unexpected dws args: {args}")


class RealtimeMorningReplayRunner(OfficialParityFixtureRunner):
    """Public-safe replay shape for the saved 2026-07-13 morning failure."""

    def __init__(self, *, omit_user: str | None = None, query_failure: bool = False) -> None:
        super().__init__(
            omit_user=omit_user,
            date_overrides={"u-normal": "2026-07-13", "u-anomaly": "2026-07-13"},
        )
        self.query_failure = query_failure

    def __call__(self, args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
        if args[:4] == ["attendance", "record", "get", "--user"]:
            user_id = args[4]
            if self.query_failure and user_id == "u-normal":
                return {
                    "returncode": 1,
                    "payload": {
                        "success": False,
                        "code": "request_timeout",
                        "reason": "saved replay query failure",
                        "error": {"retryable": False},
                    },
                }
            if user_id == self.omit_user:
                return {"returncode": 0, "payload": {"success": True}}
        result = super().__call__(args, timeout=timeout, verbose=verbose)
        if args[:3] != ["attendance", "report", "query-data"]:
            return result
        if self.query_failure:
            return {
                "returncode": 1,
                "payload": {
                    "success": False,
                    "code": "request_timeout",
                    "reason": "saved replay query failure",
                    "error": {"retryable": False},
                },
            }
        records = result["payload"]["result"]["records"]
        for record in records:
            for entry in record["values"]:
                if entry["termId"] != self.column_ids["考勤结果"]:
                    entry["value"] = ""
        return result


class DingTalkAttendanceContractTests(unittest.TestCase):
    def test_r32_monthly_rollup_reads_only_current_final_reconciliation_archives(self) -> None:
        from KMFA.tools.dingtalk_attendance.official_report_reconstruction import (
            RECONCILIATION_CERTIFICATE_SCHEMA,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            month_dir = Path(tmpdir)
            for run_id, marker in (
                ("s19_evening_20260710_200000", "legacy"),
                ("dingtalk_attendance_morning_20260710_104500", "morning"),
                ("dingtalk_attendance_evening_20260710_200000", "evening"),
                ("dingtalk_attendance_final_20260711_090000", "final"),
                ("dingtalk_attendance_final_20260712_090000", "unbound-final"),
            ):
                with gzip.open(month_dir / f"{run_id}.raw.jsonl.gz", "wt", encoding="utf-8") as handle:
                    handle.write(json.dumps({"type": "metadata", "run_plan": {"run_id": run_id}}) + "\n")
                    handle.write(
                        json.dumps(
                            {
                                "type": "employee_attendance",
                                "member": {"name": marker, "userId": marker},
                                "work_date": "2026-07-10",
                                "derived": {
                                    "official_report_covered": marker != "legacy",
                                    "official_report_anomaly": False,
                                },
                            }
                        )
                        + "\n"
                    )
            valid_run_id = "dingtalk_attendance_final_20260711_090000"
            certificate = {
                "schema": RECONCILIATION_CERTIFICATE_SCHEMA,
                "evidence_kind": "INDEPENDENT_OFFICIAL_EXPORT_VS_DWS",
                "official_sha256": "c" * 64,
                "work_date": "2026-07-10",
                "status": "PASS",
                "official_people": 44,
                "dws_people": 44,
                "matched_people": 44,
                "compared_columns": 48,
                "compared_cells": 2112,
                "missing_people": 0,
                "extra_people": 0,
                "missing_required_columns": 0,
                "missing_required_cells": 0,
                "differing_required_cells": 0,
                "optional_unverified_fields": ["部门"],
            }
            (month_dir / f"{valid_run_id}.manifest.json").write_text(
                json.dumps(
                    {
                        "skill_id": "kmfa-dingtalk-attendance-skill",
                        "run_id": valid_run_id,
                        "work_date": "2026-07-10",
                        "result_kind": "OFFICIAL_FINAL_RECONCILIATION",
                        "monthly_rollup_eligible": True,
                        "official_reconciliation_certificate": certificate,
                    }
                ),
                encoding="utf-8",
            )

            records = ATTENDANCE_RUNNER._monthly_attendance_records(month_dir)

        self.assertEqual([record["member"]["name"] for record in records], ["final"])
        self.assertEqual(records[0]["work_date"], "2026-07-10")

    def test_r32_morning_and_evening_are_labeled_temporary_reminders(self) -> None:
        morning = build_notification_message(
            work_date="2026-07-10",
            run_type="morning",
            current_time="10:45",
            unexpected_empty_record_names=[],
            known_no_record_names=[],
            member_count=2,
        )
        evening = build_notification_message(
            work_date="2026-07-10",
            run_type="evening",
            current_time="20:00",
            unexpected_empty_record_names=[],
            known_no_record_names=[],
            member_count=2,
        )

        self.assertIn("晨间暂时提醒", morning)
        self.assertIn("晚间暂时提醒", evening)

    def test_r32_delivery_is_disabled_at_production_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = send_latest_report(onedrive_root=Path(tmpdir))

        self.assertEqual(result["status"], "NOT_SENT_OWNER_DISABLED")
        self.assertEqual(result["notification_status"], "NOT_SENT_OWNER_DISABLED")

    def test_r32_final_reconciliation_page_is_aggregate_and_send_disabled(self) -> None:
        from KMFA.tools.dingtalk_attendance.final_reconciliation import build_one_page_result

        page = build_one_page_result(
            work_date="2026-07-10",
            morning={"evidence_status": "FOUND", "official_parity": "UNKNOWN"},
            evening={"evidence_status": "FOUND", "official_parity": "UNKNOWN"},
            final_stats=_official_pass_stats(member_count=2, anomaly_names=[]),
            final_run_id="dingtalk_attendance_final_20260711_090000",
        )

        self.assertIn("晨间提醒—晚间提醒—官方最终核对", page)
        self.assertIn("发送状态：关闭", page)
        self.assertIn("官方最终核对：EVIDENCE_MISSING", page)
        self.assertIn("INDEPENDENT_OFFICIAL_EXPORT_REQUIRED", page)
        self.assertNotIn("REAL_DINGTALK_OFFICIAL_REPORT", page)
        self.assertNotIn("employee", page.lower())

    def test_r4_final_reconciliation_fails_closed_without_independent_export(self) -> None:
        from KMFA.tools.dingtalk_attendance.final_reconciliation import run_final_reconciliation

        def collector(**_: object) -> dict:
            raise AssertionError("DWS collector must not run without independent official export evidence")

        result = run_final_reconciliation(
            work_date="2026-07-10",
            timezone="Asia/Shanghai",
            collector=collector,
            cleanup=lambda: {"status": "PASS"},
            now=datetime(2026, 7, 12, 9, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        )

        self.assertEqual(result["status"], "OFFICIAL_EVIDENCE_MISSING")
        self.assertEqual(result["independent_evidence_status"], "EVIDENCE_MISSING")
        self.assertEqual(result["notification_status"], "NOT_SENT_OWNER_DISABLED")

    def test_official_reconstruction_preserves_49_column_semantics(self) -> None:
        from KMFA.tools.dingtalk_attendance.official_report_reconstruction import (
            COLUMN_SOURCES,
            OFFICIAL_COLUMNS,
            VALUE_DIFFERENT,
            build_reconstructed_rows,
            classify_cell,
        )

        report_values = {name: "" for name in OFFICIAL_COLUMNS[8:37] + OFFICIAL_COLUMNS[45:49]}
        report_values.update({"班次": "测试班次 08:00-17:30", "迟到次数": "0"})
        column_ids = {name: str(index + 1000) for index, name in enumerate(report_values)}
        snapshot = {
            "report_column_names": list(report_values),
            "report_column_ids": [column_ids[name] for name in report_values],
            "report_query_data": {
                "2026-07-09": [{
                    "result": [{
                        "userId": "00123",
                        "workDate": "2026-07-09",
                        "values": [
                            {"termId": column_ids[name], "value": value, "type": "DYNAMIC"}
                            for name, value in report_values.items()
                        ],
                    }]
                }]
            },
            "report_query_leave": {
                "2026-07-09": [{
                    "result": [{
                        "userId": "00123",
                        "leaveVals": [
                            {"leaveName": name, "date": "1783526400000", "value": "0.0"}
                            for name in ("事假", "病假", "年假", "调休", "婚假", "产假", "陪产假", "路途假")
                        ],
                    }]
                }]
            },
            "user_profiles": [{
                "result": [{
                    "orgEmployeeModel": {
                        "orgUserId": "00123",
                        "orgUserName": "测试员工",
                        "depts": [{"deptId": "10", "deptName": "测试部门"}],
                        "jobNumber": "0007",
                        "orgTitle": "测试职位",
                    }
                }]
            }],
            "attendance_groups": [
                {"result": {"items": [{"id": 1, "name": "测试组"}]}},
                {"result": {"id": 1, "name": "测试组", "memberUsers": ["00123"]}},
            ],
            "department_directory": {"10": {"name": "测试部门", "path": ["技术部", "测试部门"]}},
        }

        rows = build_reconstructed_rows(snapshot, work_date="2026-07-09")
        values = rows["00123"]

        self.assertEqual(len(OFFICIAL_COLUMNS), 49)
        self.assertEqual(len(COLUMN_SOURCES), 49)
        self.assertEqual(len(values), 49)
        self.assertEqual(values[5], "00123")
        self.assertEqual(values[6], "26-07-09 星期四")
        self.assertEqual(values[7], "1783526400000")
        self.assertEqual(values[2], "技术部-测试部门")
        self.assertIsNone(values[25])
        self.assertIsNone(values[37])
        self.assertIsNone(values[30])
        self.assertEqual(classify_cell(None, "0", column_name="迟到次数"), VALUE_DIFFERENT)

    def test_official_reconciliation_treats_department_as_optional_display_only(self) -> None:
        from KMFA.tools.dingtalk_attendance.official_report_reconstruction import (
            NO_SOURCE,
            PASS,
            REQUIRED_COLUMNS,
            build_reconciliation_certificate,
            compare_standard_entry,
            validate_reconciliation_certificate,
            write_reconciliation_certificate,
        )

        official_row = [None] * 49
        official_row[0] = "测试员工"
        official_row[2] = "生产部-测试组"
        official_row[5] = "00123"
        rebuilt_row = list(official_row)
        rebuilt_row[2] = NO_SOURCE
        standard = {
            "values": [
                ["2026-07-09 每日统计"],
                [],
                [],
                [],
                official_row,
            ]
        }

        result = compare_standard_entry(
            standard,
            {"00123": rebuilt_row},
            work_date="2026-07-09",
        )
        certificate = build_reconciliation_certificate(
            result,
            official_sha256="a" * 64,
        )

        self.assertEqual(len(REQUIRED_COLUMNS), 48)
        self.assertEqual(result["status"], PASS)
        self.assertEqual(result["compared_cells"], 48)
        self.assertEqual(result["missing_required_columns"], [])
        self.assertEqual(result["required_missing_cells"], 0)
        self.assertEqual(result["true_differences"], 0)
        self.assertEqual(result["optional_unverified_fields"], ["部门"])
        self.assertEqual(certificate["official_people"], 1)
        self.assertEqual(certificate["dws_people"], 1)
        self.assertEqual(certificate["matched_people"], 1)
        self.assertEqual(certificate["compared_columns"], 48)
        self.assertEqual(certificate["compared_cells"], 48)
        self.assertEqual(certificate["missing_people"], 0)
        self.assertEqual(certificate["extra_people"], 0)
        self.assertEqual(certificate["missing_required_columns"], 0)
        self.assertEqual(certificate["missing_required_cells"], 0)
        self.assertEqual(certificate["differing_required_cells"], 0)
        self.assertEqual(certificate["optional_unverified_fields"], ["部门"])
        self.assertEqual(validate_reconciliation_certificate(certificate), [])
        with tempfile.TemporaryDirectory() as tmpdir:
            certificate_path = write_reconciliation_certificate(certificate, Path(tmpdir))
            self.assertEqual(
                certificate_path.name,
                "official_reconciliation_2026-07-09.certificate.json",
            )
            self.assertEqual(
                json.loads(certificate_path.read_text(encoding="utf-8")),
                certificate,
            )

    def test_final_reconciliation_reads_the_canonical_certificate_without_conversion(self) -> None:
        from KMFA.tools.dingtalk_attendance.final_reconciliation import (
            _load_independent_reconciliation_evidence,
        )
        from KMFA.tools.dingtalk_attendance.official_report_reconstruction import (
            RECONCILIATION_CERTIFICATE_SCHEMA,
        )

        certificate = {
            "schema": RECONCILIATION_CERTIFICATE_SCHEMA,
            "evidence_kind": "INDEPENDENT_OFFICIAL_EXPORT_VS_DWS",
            "official_sha256": "b" * 64,
            "work_date": "2026-07-10",
            "status": "PASS",
            "official_people": 44,
            "dws_people": 44,
            "matched_people": 44,
            "compared_columns": 48,
            "compared_cells": 2112,
            "missing_people": 0,
            "extra_people": 0,
            "missing_required_columns": 0,
            "missing_required_cells": 0,
            "differing_required_cells": 0,
            "optional_unverified_fields": ["部门"],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "official_reconciliation_2026-07-10.certificate.json"
            path.write_text(json.dumps(certificate, ensure_ascii=False), encoding="utf-8")
            loaded = _load_independent_reconciliation_evidence(path, work_date="2026-07-10")

        self.assertEqual(loaded["status"], "PASS")
        self.assertEqual(loaded["evidence_status"], "PASS")
        self.assertEqual(loaded["certificate"], certificate)

    def test_required_official_field_still_blocks_reconciliation(self) -> None:
        from KMFA.tools.dingtalk_attendance.official_report_reconstruction import (
            BLOCKED,
            NO_SOURCE,
            compare_standard_entry,
        )

        official_row = [None] * 49
        official_row[0] = "测试员工"
        official_row[5] = "00123"
        rebuilt_row = list(official_row)
        rebuilt_row[22] = NO_SOURCE
        standard = {"values": [["2026-07-09 每日统计"], [], [], [], official_row]}

        result = compare_standard_entry(
            standard,
            {"00123": rebuilt_row},
            work_date="2026-07-09",
        )

        self.assertEqual(result["status"], BLOCKED)
        self.assertEqual(result["missing_required_columns"], ["出勤天数"])
        self.assertEqual(result["required_missing_cells"], 1)

    def test_r6_date_slot_idempotency_and_interruption_recovery(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import R6Coordinator

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            coordinator = R6Coordinator(root)
            calls: list[str] = []

            def successful_runner() -> dict[str, object]:
                calls.append("evening")
                return {
                    "status": "COMPLETED",
                    "notification_status": "SENT",
                    "member_count": 42,
                }

            first = coordinator.ensure_slot(
                work_date="2026-07-13",
                run_slot="evening",
                trigger_source="automation",
                runner=successful_runner,
                completed_probe=lambda: None,
            )
            duplicate = coordinator.ensure_slot(
                work_date="2026-07-13",
                run_slot="evening",
                trigger_source="automation",
                runner=successful_runner,
                completed_probe=lambda: None,
            )

            marker = root / "morning-complete"

            def interrupted_runner() -> dict[str, object]:
                calls.append("morning")
                marker.write_text("complete", encoding="utf-8")
                raise InterruptedError("simulated process interruption")

            interrupted = coordinator.ensure_slot(
                work_date="2026-07-14",
                run_slot="morning",
                trigger_source="automation",
                runner=interrupted_runner,
                completed_probe=lambda: ({"member_count": 42} if marker.exists() else None),
            )
            recovered = coordinator.ensure_slot(
                work_date="2026-07-14",
                run_slot="morning",
                trigger_source="automation",
                runner=lambda: (_ for _ in ()).throw(AssertionError("must not rerun after artifact recovery")),
                completed_probe=lambda: ({"member_count": 42} if marker.exists() else None),
            )

            self.assertEqual(first["status"], "COMPLETED")
            self.assertEqual(duplicate["status"], "IDEMPOTENT_SKIP")
            self.assertEqual(interrupted["status"], "INTERRUPTED")
            self.assertEqual(recovered["status"], "RECOVERED_COMPLETE")
            self.assertEqual(calls, ["evening", "morning"])
            self.assertTrue((root / "运行状态.md").is_file())

    def test_r6_final_waits_then_commits_certificate_bound_result_once(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import R6Coordinator

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            coordinator = R6Coordinator(root)
            export_path = root / "official.xlsx"
            certificate_path = root / "official.certificate.json"
            final_marker = root / "final.complete"
            calls = {"certificate": 0, "final": 0}

            waiting = coordinator.advance_final(
                work_date="2026-07-13",
                export_finder=lambda: None,
                certificate_builder=lambda _: certificate_path,
                final_runner=lambda _: {"status": "OFFICIAL_FINAL_RECONCILIATION_PASS"},
                completed_probe=lambda: None,
            )
            export_path.write_text("frozen", encoding="utf-8")

            def build_certificate(_: Path) -> Path:
                calls["certificate"] += 1
                certificate_path.write_text("{}", encoding="utf-8")
                return certificate_path

            def run_final(_: Path) -> dict[str, object]:
                calls["final"] += 1
                final_marker.write_text("complete", encoding="utf-8")
                return {
                    "status": "OFFICIAL_FINAL_RECONCILIATION_PASS",
                    "monthly_written": True,
                }

            completed = coordinator.advance_final(
                work_date="2026-07-13",
                export_finder=lambda: export_path,
                certificate_builder=build_certificate,
                final_runner=run_final,
                completed_probe=lambda: ({"monthly_written": True} if final_marker.exists() else None),
            )
            duplicate = coordinator.advance_final(
                work_date="2026-07-13",
                export_finder=lambda: export_path,
                certificate_builder=build_certificate,
                final_runner=run_final,
                completed_probe=lambda: ({"monthly_written": True} if final_marker.exists() else None),
            )

            self.assertEqual(waiting["status"], "WAITING_OFFICIAL_REPORT")
            self.assertEqual(completed["status"], "OFFICIAL_FINAL_RECONCILIATION_PASS")
            self.assertEqual(duplicate["status"], "IDEMPOTENT_SKIP")
            self.assertEqual(calls, {"certificate": 1, "final": 1})

    def test_r6_natural_acceptance_excludes_manual_runs(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import R6Coordinator

        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_identity = {
                "git_commit": "a" * 40,
                "attendance_runtime_fingerprint": "f" * 64,
                "attendance_runtime_tree_state": "CLEAN",
                "tracked_tree_state": "DIRTY",
                "prompt_mirrors_match": True,
                "morning_prompt_sha256": "b" * 64,
                "evening_prompt_sha256": "c" * 64,
            }
            coordinator = R6Coordinator(Path(tmpdir), runtime_identity=runtime_identity)
            for work_date, verified, actual_workday in (
                ("2026-07-13", True, True),
                ("2026-07-14", False, True),
                ("2026-07-18", True, False),
            ):
                for slot in ("morning", "evening"):
                    coordinator.ensure_slot(
                        work_date=work_date,
                        run_slot=slot,
                        trigger_source="automation",
                        task_evidence={
                            "verified": verified,
                            "task_id": f"task-{work_date}-{slot}",
                            "thread_source": "automation" if verified else "manual",
                            "automation_id": "kmfa" if slot == "morning" else "kmfa-3",
                            "triggered_at": f"{work_date}T00:00:00Z",
                            "prompt_sha256": runtime_identity[f"{slot}_prompt_sha256"],
                        },
                        runner=lambda: {
                            "status": "COMPLETED",
                            "notification_status": "SENT",
                            "member_count": 42,
                        },
                        completed_probe=lambda: None,
                    )
                coordinator.record_final_success(
                    work_date=work_date,
                    trigger_source="automation",
                    task_evidence={
                        "verified": verified,
                        "task_id": f"task-{work_date}-final",
                        "thread_source": "automation" if verified else "manual",
                        "automation_id": "kmfa",
                        "triggered_at": f"{work_date}T01:00:00Z",
                        "prompt_sha256": runtime_identity["morning_prompt_sha256"],
                    },
                    result={
                        "status": "OFFICIAL_FINAL_RECONCILIATION_PASS",
                        "differing_required_cells": 0,
                        "monthly_written": True,
                        "actual_workday": actual_workday,
                    },
                )

            summary = coordinator.acceptance_summary()

        self.assertEqual(summary["morning"]["natural_success_count"], 2)
        self.assertEqual(summary["morning"]["natural_success_dates"], ["2026-07-13", "2026-07-18"])
        self.assertEqual(summary["evening"]["natural_success_count"], 2)
        self.assertEqual(summary["evening"]["natural_success_dates"], ["2026-07-13", "2026-07-18"])
        self.assertEqual(summary["final_reconciliation"]["pass_count"], 1)
        self.assertEqual(summary["final_reconciliation"]["pass_dates"], ["2026-07-13"])
        self.assertEqual(summary["delivery"]["owner_disabled_count"], 0)
        self.assertEqual(summary["delivery"]["sent_count"], 4)
        self.assertNotIn("target_work_days", summary)
        self.assertNotIn("natural_completed_work_days", summary)

    def test_r6_morning_reminder_completes_before_and_survives_final_failure(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import (
            OfficialExportAmbiguousError,
            run_automatic_cycle,
        )

        runtime_identity = {
            "git_commit": "a" * 40,
            "attendance_runtime_fingerprint": "f" * 64,
            "attendance_runtime_tree_state": "CLEAN",
            "prompt_mirrors_match": True,
            "morning_prompt_sha256": "b" * 64,
            "evening_prompt_sha256": "c" * 64,
        }
        task_evidence = {
            "verified": True,
            "task_id": "natural-morning-task",
            "thread_source": "automation",
            "automation_id": "kmfa",
            "triggered_at": "2026-07-15T02:45:00Z",
            "prompt_sha256": runtime_identity["morning_prompt_sha256"],
        }
        order: list[str] = []
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "KMFA.tools.dingtalk_attendance.automatic_closure.find_latest_pending_work_date",
                return_value="2026-07-14",
            ),
            patch(
                "KMFA.tools.dingtalk_attendance.automatic_closure._slot_runner",
                side_effect=lambda **_: order.append("reminder") or {
                    "status": "COMPLETED",
                    "notification_status": "SENT",
                    "member_count": 45,
                },
            ),
            patch(
                "KMFA.tools.dingtalk_attendance.automatic_closure._completed_reminder_probe",
                return_value=None,
            ),
            patch(
                "KMFA.tools.dingtalk_attendance.automatic_closure._completed_final_probe",
                return_value=None,
            ),
            patch(
                "KMFA.tools.dingtalk_attendance.automatic_closure.find_official_export",
                side_effect=lambda **_: order.append("final")
                or (_ for _ in ()).throw(OfficialExportAmbiguousError("conflict")),
            ),
        ):
            result = run_automatic_cycle(
                run_slot="morning",
                trigger_source="automation",
                task_evidence=task_evidence,
                runtime_identity=runtime_identity,
                private_root=Path(tmpdir) / "private",
                archive_root=Path(tmpdir) / "archive",
                now=datetime(2026, 7, 15, 10, 45, tzinfo=ZoneInfo("Asia/Shanghai")),
            )

        self.assertEqual(order, ["reminder", "final"])
        self.assertEqual(result["reminder"]["status"], "COMPLETED")
        self.assertEqual(result["final"]["status"], "FAILED")
        self.assertEqual(result["status"], "REMINDER_COMPLETED_FINAL_FAILED")

    def test_r6_saved_morning_failure_replay_completes_while_prior_final_keeps_waiting(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import run_automatic_cycle

        runtime_identity = {
            "git_commit": "a" * 40,
            "attendance_runtime_fingerprint": "f" * 64,
            "attendance_runtime_tree_state": "CLEAN",
            "prompt_mirrors_match": True,
            "morning_prompt_sha256": "b" * 64,
            "evening_prompt_sha256": "c" * 64,
        }
        task_evidence = {
            "verified": True,
            "task_id": "saved-2026-07-13-natural-morning-task",
            "thread_source": "automation",
            "automation_id": "kmfa",
            "triggered_at": "2026-07-13T00:46:38.292Z",
            "prompt_sha256": runtime_identity["morning_prompt_sha256"],
        }
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "KMFA.tools.dingtalk_attendance.automatic_closure.find_latest_pending_work_date",
                return_value="2026-07-12",
            ),
            patch(
                "KMFA.tools.dingtalk_attendance.automatic_closure._slot_runner",
                return_value={
                    "status": "COMPLETED",
                    "notification_status": "SENT",
                    "member_count": 2,
                    "run_id": "dingtalk_attendance_morning_20260713_085450",
                },
            ),
            patch(
                "KMFA.tools.dingtalk_attendance.automatic_closure._completed_reminder_probe",
                return_value=None,
            ),
            patch(
                "KMFA.tools.dingtalk_attendance.automatic_closure._completed_final_probe",
                return_value=None,
            ),
            patch(
                "KMFA.tools.dingtalk_attendance.automatic_closure.find_official_export",
                return_value=None,
            ),
        ):
            result = run_automatic_cycle(
                run_slot="morning",
                trigger_source="automation",
                task_evidence=task_evidence,
                runtime_identity=runtime_identity,
                private_root=Path(tmpdir) / "private",
                archive_root=Path(tmpdir) / "archive",
                now=datetime(2026, 7, 13, 10, 45, tzinfo=ZoneInfo("Asia/Shanghai")),
            )

        self.assertEqual(result["reminder"]["status"], "COMPLETED")
        self.assertEqual(result["reminder"]["notification_status"], "SENT")
        self.assertEqual(result["final"]["work_date"], "2026-07-12")
        self.assertEqual(result["final"]["status"], "WAITING_OFFICIAL_REPORT")
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["result_message"], "提醒成功，事后核验等待")
        self.assertEqual(
            result["follow_up"],
            {
                "kind": "OFFICIAL_FINAL_RECONCILIATION",
                "status": "WAITING_OFFICIAL_REPORT",
                "work_date": "2026-07-12",
                "blocks_reminder": False,
            },
        )
        self.assertEqual(result["acceptance"]["morning"]["natural_success_count"], 1)
        self.assertEqual(result["acceptance"]["final_reconciliation"]["waiting_dates"], ["2026-07-12"])

    def test_r6_manual_artifact_recovery_keeps_original_source_and_is_not_natural(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import R6Coordinator

        runtime_identity = {
            "git_commit": "a" * 40,
            "morning_prompt_sha256": "b" * 64,
            "evening_prompt_sha256": "c" * 64,
        }
        manual_evidence = {
            "verified": False,
            "task_id": "manual-task",
            "thread_source": "manual",
            "automation_id": "kmfa",
            "triggered_at": "2026-07-15T02:45:00Z",
            "prompt_sha256": runtime_identity["morning_prompt_sha256"],
        }
        natural_evidence = {
            **manual_evidence,
            "verified": True,
            "task_id": "natural-task",
            "thread_source": "automation",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = R6Coordinator(Path(tmpdir), runtime_identity=runtime_identity)
            coordinator.ensure_slot(
                work_date="2026-07-15",
                run_slot="morning",
                trigger_source="manual",
                task_evidence=manual_evidence,
                runner=lambda: (_ for _ in ()).throw(InterruptedError("manual interrupted")),
                completed_probe=lambda: None,
            )
            recovered = coordinator.ensure_slot(
                work_date="2026-07-15",
                run_slot="morning",
                trigger_source="automation",
                task_evidence=natural_evidence,
                runner=lambda: (_ for _ in ()).throw(AssertionError("must recover")),
                completed_probe=lambda: {"member_count": 45, "trigger_source": "manual"},
            )
            saved = coordinator.state["work_dates"]["2026-07-15"]["slots"]["morning"]

        self.assertEqual(recovered["status"], "RECOVERED_COMPLETE")
        self.assertEqual(saved["task_evidence"]["thread_source"], "manual")
        self.assertFalse(saved["task_evidence"]["verified"])

    def test_attendance_runtime_fingerprint_ignores_unrelated_files_and_detects_runtime_or_prompt_changes(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import attendance_runtime_fingerprint

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            relative_paths = ("runtime.py", "rules.yaml", "morning.md", "evening.md")
            for rel, content in zip(relative_paths, ("runtime-v1", "rules-v1", "morning-v1", "evening-v1")):
                (root / rel).write_text(content, encoding="utf-8")
            live_prompts = {"morning": "morning-v1", "evening": "evening-v1"}

            baseline = attendance_runtime_fingerprint(
                repo_root=root,
                live_prompts=live_prompts,
                relative_paths=relative_paths,
            )
            (root / "unrelated.txt").write_text("other project commit", encoding="utf-8")
            after_unrelated = attendance_runtime_fingerprint(
                repo_root=root,
                live_prompts=live_prompts,
                relative_paths=relative_paths,
            )
            (root / "runtime.py").write_text("runtime-v2", encoding="utf-8")
            after_runtime = attendance_runtime_fingerprint(
                repo_root=root,
                live_prompts=live_prompts,
                relative_paths=relative_paths,
            )
            (root / "runtime.py").write_text("runtime-v1", encoding="utf-8")
            after_prompt = attendance_runtime_fingerprint(
                repo_root=root,
                live_prompts={**live_prompts, "evening": "evening-v2"},
                relative_paths=relative_paths,
            )

        self.assertEqual(after_unrelated, baseline)
        self.assertNotEqual(after_runtime, baseline)
        self.assertNotEqual(after_prompt, baseline)

    def test_r6_runtime_change_preserves_facts_and_revalidates_affected_components(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import R6Coordinator

        first_identity = {
            "git_commit": "a" * 40,
            "attendance_runtime_fingerprint": "f" * 64,
            "attendance_runtime_tree_state": "CLEAN",
            "tracked_tree_state": "CLEAN",
            "prompt_mirrors_match": True,
            "morning_prompt_sha256": "b" * 64,
            "evening_prompt_sha256": "c" * 64,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first = R6Coordinator(root, runtime_identity=first_identity)
            for slot in ("morning", "evening"):
                first.ensure_slot(
                    work_date="2026-07-15",
                    run_slot=slot,
                    trigger_source="automation",
                    task_evidence={
                        "verified": True,
                        "task_id": f"task-2026-07-15-{slot}",
                        "thread_source": "automation",
                        "automation_id": "kmfa" if slot == "morning" else "kmfa-3",
                        "triggered_at": "2026-07-15T00:00:00Z",
                        "prompt_sha256": first_identity[f"{slot}_prompt_sha256"],
                    },
                    runner=lambda: {
                        "status": "COMPLETED",
                        "notification_status": "SENT",
                        "member_count": 42,
                    },
                    completed_probe=lambda: None,
                )
            first.record_final_success(
                work_date="2026-07-15",
                trigger_source="automation",
                task_evidence={
                    "verified": True,
                    "task_id": "task-2026-07-15-final",
                    "thread_source": "automation",
                    "automation_id": "kmfa",
                    "triggered_at": "2026-07-15T01:00:00Z",
                    "prompt_sha256": first_identity["morning_prompt_sha256"],
                },
                result={
                    "status": "OFFICIAL_FINAL_RECONCILIATION_PASS",
                    "differing_required_cells": 0,
                    "monthly_written": True,
                    "actual_workday": True,
                },
            )
            self.assertEqual(first.acceptance_summary()["morning"]["natural_success_count"], 1)
            self.assertEqual(first.acceptance_summary()["evening"]["natural_success_count"], 1)

            unrelated_commit_identity = {**first_identity, "git_commit": "d" * 40}
            preserved = R6Coordinator(root, runtime_identity=unrelated_commit_identity)
            self.assertIn("2026-07-15", preserved.state["work_dates"])
            self.assertEqual(preserved.state["runtime_identity"], unrelated_commit_identity)
            self.assertEqual(preserved.acceptance_summary()["morning"]["natural_success_count"], 1)
            self.assertEqual(preserved.acceptance_summary()["evening"]["natural_success_count"], 1)

            changed_fingerprint_identity = {
                **unrelated_commit_identity,
                "attendance_runtime_fingerprint": "e" * 64,
                "evening_prompt_sha256": "9" * 64,
            }
            reset = R6Coordinator(root, runtime_identity=changed_fingerprint_identity)
            self.assertEqual(reset.acceptance_summary()["morning"]["natural_success_count"], 1)
            self.assertEqual(reset.acceptance_summary()["evening"]["natural_success_count"], 1)
            self.assertEqual(reset.state["runtime_identity"], changed_fingerprint_identity)
            self.assertIn("2026-07-15", reset.state["work_dates"])
            self.assertEqual(
                reset.state["runtime_transitions"][-1]["revalidation_scope"],
                "CHANGED_COMPONENTS_ONLY",
            )

    def test_r6_saved_20260714_morning_replay_is_permanent_and_waiting_final_is_nonblocking(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import R6Coordinator

        old_identity = {
            "git_commit": "9" * 40,
            "attendance_runtime_fingerprint": "8" * 64,
            "attendance_runtime_tree_state": "CLEAN",
            "prompt_mirrors_match": True,
            "morning_prompt_sha256": "3" * 64,
            "evening_prompt_sha256": "4" * 64,
        }
        new_identity = {
            **old_identity,
            "git_commit": "a" * 40,
            "attendance_runtime_fingerprint": "7" * 64,
        }
        task_evidence = {
            "verified": True,
            "task_id": "saved-20260714-morning-task",
            "thread_source": "automation",
            "automation_id": "kmfa",
            "triggered_at": "2026-07-14T00:46:39.769Z",
            "prompt_sha256": old_identity["morning_prompt_sha256"],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            root.mkdir(parents=True, exist_ok=True)
            (root / "state.json").write_text(
                json.dumps(
                    {
                        "schema_version": 3,
                        "runtime_identity": old_identity,
                        "work_dates": {
                            "2026-07-12": {
                                "slots": {},
                                "official_export": {"status": "WAITING_OFFICIAL_REPORT"},
                                "final": {
                                    "status": "WAITING_OFFICIAL_REPORT",
                                    "trigger_source": "automation",
                                    "task_evidence": task_evidence,
                                    "runtime_identity": old_identity,
                                },
                            },
                            "2026-07-14": {
                                "slots": {
                                    "morning": {
                                        "status": "COMPLETED",
                                        "trigger_source": "automation",
                                        "task_evidence": task_evidence,
                                        "runtime_identity": old_identity,
                                        "notification_status": "NOT_SENT_OWNER_DISABLED",
                                        "member_count": 42,
                                        "run_id": "dingtalk_attendance_morning_20260714_084749",
                                    }
                                }
                            },
                        },
                        "events": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            coordinator = R6Coordinator(root, runtime_identity=new_identity)
            replay = coordinator.ensure_slot(
                work_date="2026-07-14",
                run_slot="morning",
                trigger_source="manual",
                runner=lambda: (_ for _ in ()).throw(AssertionError("saved reminder must not rerun")),
                completed_probe=lambda: {
                    "member_count": 42,
                    "run_id": "dingtalk_attendance_morning_20260714_084749",
                    "realtime_integrity_status": "PASS",
                    "realtime_expected_count": 42,
                    "realtime_coverage_count": 42,
                    "query_failure_count": 0,
                    "parse_failure_count": 0,
                    "command_failure_count": 0,
                    "archive_generated": True,
                },
            )
            summary = coordinator.acceptance_summary()
            state = json.loads((root / "state.json").read_text(encoding="utf-8"))
            status_text = (root / "运行状态.md").read_text(encoding="utf-8")

        saved = state["work_dates"]["2026-07-14"]["slots"]["morning"]
        self.assertEqual(replay["status"], "IDEMPOTENT_SKIP")
        self.assertEqual(saved["realtime_integrity_status"], "PASS")
        self.assertEqual(saved["realtime_expected_count"], 42)
        self.assertEqual(saved["realtime_coverage_count"], 42)
        self.assertTrue(saved["archive_generated"])
        self.assertEqual(summary["morning"]["natural_success_dates"], ["2026-07-14"])
        self.assertEqual(summary["final_reconciliation"]["waiting_dates"], ["2026-07-12"])
        self.assertIn("晨间自然成功：1", status_text)
        self.assertIn("事后核验等待：2026-07-12", status_text)
        self.assertNotIn("0 / 5", status_text)

    def test_r6_task_evidence_requires_real_automation_session_metadata(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import read_automation_task_evidence

        prompt = "Use $kmfa-dingtalk-attendance-skill.\nAutomation ID bound prompt."
        prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            automation_path = root / "automation.jsonl"
            manual_path = root / "manual.jsonl"
            wrapped = "Automation: test\nAutomation ID: kmfa\nLast run: none\n\n" + prompt
            for path, source in ((automation_path, "automation"), (manual_path, "manual")):
                path.write_text(
                    "\n".join(
                        json.dumps(row, ensure_ascii=False)
                        for row in (
                            {
                                "type": "session_meta",
                                "payload": {
                                    "id": f"task-{source}",
                                    "timestamp": "2026-07-15T02:45:00Z",
                                    "cwd": "/Users/linzezhang/CodexProject",
                                    "thread_source": source,
                                },
                            },
                            {
                                "type": "response_item",
                                "payload": {
                                    "type": "message",
                                    "role": "user",
                                    "content": [{"type": "input_text", "text": wrapped}],
                                },
                            },
                        )
                    )
                    + "\n",
                    encoding="utf-8",
                )
            verified = read_automation_task_evidence(
                automation_path,
                expected_automation_id="kmfa",
                expected_prompt_sha256=prompt_sha,
                expected_cwd=Path("/Users/linzezhang/CodexProject"),
            )
            rejected = read_automation_task_evidence(
                manual_path,
                expected_automation_id="kmfa",
                expected_prompt_sha256=prompt_sha,
                expected_cwd=Path("/Users/linzezhang/CodexProject"),
            )

        self.assertTrue(verified["verified"])
        self.assertEqual(verified["thread_source"], "automation")
        self.assertFalse(rejected["verified"])

    def test_r6_task_discovery_requires_current_codex_thread_id(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import discover_automation_task_evidence

        prompt = "Use $kmfa-dingtalk-attendance-skill.\nCurrent task only."
        prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
        with tempfile.TemporaryDirectory() as tmpdir:
            codex_home = Path(tmpdir)
            session_dir = codex_home / "sessions"
            session_dir.mkdir()
            session = session_dir / "automation.jsonl"
            wrapped = "Automation: test\nAutomation ID: kmfa\nLast run: none\n\n" + prompt
            session.write_text(
                "\n".join(
                    json.dumps(row)
                    for row in (
                        {
                            "type": "session_meta",
                            "payload": {
                                "id": "natural-task-id",
                                "timestamp": "2026-07-15T02:45:00Z",
                                "cwd": "/Users/linzezhang/CodexProject",
                                "thread_source": "automation",
                            },
                        },
                        {
                            "type": "response_item",
                            "payload": {
                                "type": "message",
                                "role": "user",
                                "content": [{"type": "input_text", "text": wrapped}],
                            },
                        },
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.dict(
                "os.environ",
                {"CODEX_HOME": str(codex_home), "CODEX_THREAD_ID": "manual-other-task"},
                clear=False,
            ):
                rejected = discover_automation_task_evidence(
                    automation_id="kmfa",
                    prompt_sha256=prompt_sha,
                    now=datetime(2026, 7, 15, 2, 50, tzinfo=ZoneInfo("UTC")),
                )

        self.assertFalse(rejected["verified"])

    def test_r6_official_csv_parser_supports_45_dynamic_people(self) -> None:
        import csv

        from KMFA.tools.dingtalk_attendance.automatic_closure import parse_official_csv
        from KMFA.tools.dingtalk_attendance.official_report_reconstruction import (
            OFFICIAL_COLUMNS,
            compare_standard_entry,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "official.csv"
            primary = list(OFFICIAL_COLUMNS)
            secondary = [""] * 49
            primary[37:45] = ["请假", "", "", "", "", "", "", ""]
            secondary[37:45] = list(OFFICIAL_COLUMNS[37:45])
            primary[46:49] = ["加班时长（转调休）", "", ""]
            secondary[46:49] = list(OFFICIAL_COLUMNS[46:49])
            rows = [["每日统计 统计日期：2026-07-15 至 2026-07-15"], ["报表生成时间"], primary, secondary]
            for index in range(45):
                row = [""] * 49
                row[0] = f"测试员工{index + 1}"
                row[5] = f"00{index + 1:04d}"
                rows.append(row)
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                csv.writer(handle).writerows(rows)
            standard = parse_official_csv(path, work_date="2026-07-15")
            comparison = compare_standard_entry(
                standard,
                {str(row[5]): list(row) for row in standard["values"][4:]},
                work_date="2026-07-15",
            )

        self.assertEqual(len(standard["values"]), 49)
        self.assertEqual(comparison["official_people"], 45)
        self.assertEqual(comparison["matched_people"], 45)
        self.assertEqual(comparison["compared_columns"], 48)
        self.assertEqual(comparison["compared_cells"], 45 * 48)
        self.assertEqual(comparison["status"], "PASS")

    def test_r6_official_csv_parser_preserves_49_columns_and_user_id_text(self) -> None:
        import csv

        from KMFA.tools.dingtalk_attendance.automatic_closure import parse_official_csv
        from KMFA.tools.dingtalk_attendance.official_report_reconstruction import OFFICIAL_COLUMNS

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "official.csv"
            rows = [
                ["每日统计 统计日期：2026-07-15 至 2026-07-15"],
                ["报表生成时间：2026-07-16 10:00"],
                list(OFFICIAL_COLUMNS),
                [""] * 49,
            ]
            for index in range(44):
                row = [""] * 49
                row[0] = f"测试员工{index + 1}"
                row[5] = f"00{index + 1:04d}"
                row[6] = "26-07-15 星期三"
                row[7] = "1784044800000"
                rows.append(row)
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                csv.writer(handle).writerows(rows)

            standard = parse_official_csv(path, work_date="2026-07-15")

        self.assertEqual(len(standard["values"]), 48)
        self.assertTrue(all(len(row) == 49 for row in standard["values"]))
        self.assertEqual(standard["values"][4][5], "000001")
        self.assertEqual(standard["values"][-1][5], "000044")
        self.assertIsNone(standard["values"][4][2])

    def test_r6_two_row_merged_header_resolves_exact_official_columns(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import merge_official_header_rows
        from KMFA.tools.dingtalk_attendance.official_report_reconstruction import OFFICIAL_COLUMNS

        primary = list(OFFICIAL_COLUMNS)
        secondary = [""] * 49
        primary[37:45] = ["请假", "", "", "", "", "", "", ""]
        secondary[37:45] = [
            "事假(天)",
            "病假(天)",
            "年假(天)",
            "调休(天)",
            "婚假(天)",
            "产假(天)",
            "陪产假(天)",
            "路途假(天)",
        ]
        primary[46:49] = ["加班时长（转调休）", "", ""]
        secondary[46:49] = ["工作日（转调休）", "休息日（转调休）", "节假日（转调休）"]

        resolved = merge_official_header_rows(primary, secondary)

        self.assertEqual(tuple(resolved), OFFICIAL_COLUMNS)
        self.assertEqual(resolved[37:45], list(OFFICIAL_COLUMNS[37:45]))
        self.assertEqual(resolved[46:49], list(OFFICIAL_COLUMNS[46:49]))
        self.assertNotIn("请假", resolved)
        self.assertNotIn("加班时长（转调休）", resolved)

    def test_r6_official_export_selection_rejects_ambiguous_fingerprints(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import (
            OfficialExportAmbiguousError,
            find_official_export,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first = root / "企业_每日统计_20260715-20260715.xlsx"
            duplicate = root / "企业_每日统计_20260715-20260715 (1).xlsx"
            first.write_bytes(b"same official workbook")
            duplicate.write_bytes(first.read_bytes())

            selected = find_official_export(
                work_date="2026-07-15",
                search_roots=[root],
                validator=lambda _: True,
            )
            duplicate.write_bytes(b"different official workbook")
            with self.assertRaises(OfficialExportAmbiguousError):
                find_official_export(
                    work_date="2026-07-15",
                    search_roots=[root],
                    validator=lambda _: True,
                )

        self.assertEqual(selected, duplicate)

    def test_identity_migration_new_writer_and_legacy_reader_contract(self) -> None:
        identity = importlib.import_module("KMFA.tools.dingtalk_attendance.identity")
        plan = build_run_plan(
            run_type="morning",
            timezone="Asia/Shanghai",
            run_datetime=datetime(2026, 7, 12, 10, 45, tzinfo=ZoneInfo("Asia/Shanghai")),
        )

        self.assertEqual(plan["skill_id"], "kmfa-dingtalk-attendance-skill")
        self.assertNotIn("stage_id", plan)
        self.assertEqual(plan["run_id"], "dingtalk_attendance_morning_20260712_104500")
        self.assertEqual(
            identity.validate_manifest_identity({"skill_id": "kmfa-dingtalk-attendance-skill"}),
            {"skill_id": "kmfa-dingtalk-attendance-skill", "identity_source": "skill_id"},
        )
        self.assertEqual(
            identity.validate_manifest_identity({"stage_id": "S19"}),  # legacy_read_only
            {"skill_id": "kmfa-dingtalk-attendance-skill", "identity_source": "legacy_read_only"},
        )
        with self.assertRaises(identity.IdentityConflictError):
            identity.validate_manifest_identity(
                {"skill_id": "another-skill", "stage_id": "S19"}  # legacy_read_only conflict
            )

    def test_identity_migration_archive_discovery_dual_reads_new_and_legacy(self) -> None:
        identity = importlib.import_module("KMFA.tools.dingtalk_attendance.identity")
        with tempfile.TemporaryDirectory() as tmpdir:
            month_dir = Path(tmpdir)
            new_manifest = month_dir / "dingtalk_attendance_evening_20260712_200000.manifest.json"
            legacy_manifest = month_dir / "s19_evening_20260711_200000.manifest.json"  # legacy_read_only
            ignored_manifest = month_dir / "unrelated.manifest.json"
            for path in (new_manifest, legacy_manifest, ignored_manifest):
                path.write_text("{}", encoding="utf-8")

            self.assertEqual(
                set(identity.archive_manifest_paths(month_dir)),
                {new_manifest, legacy_manifest},
            )

    def test_identity_migration_environment_keys_prefer_new_and_fail_on_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "pat_policy.json"
            policy_path.write_text(
                json.dumps({"default": {"openBrowser": False}}, ensure_ascii=False),
                encoding="utf-8",
            )
            new_env = {
                "KMFA_DINGTALK_ATTENDANCE_ALLOW_DWS_COMMANDS": "1",
                "KMFA_DINGTALK_ATTENDANCE_DWS_BROWSER_POLICY_PATH": str(policy_path),
            }
            allowed = dws_command_safety_status(env=new_env)
            conflict = dws_command_safety_status(
                env={
                    **new_env,
                    "KMFA_S19_ALLOW_DWS_COMMANDS": "0",  # legacy_read_only conflict
                }
            )

        self.assertEqual(allowed["status"], "READY")
        self.assertEqual(
            allowed["required_env"],
            "KMFA_DINGTALK_ATTENDANCE_ALLOW_DWS_COMMANDS",
        )
        self.assertEqual(conflict["status"], "DWS_ENV_CONFLICT")
        self.assertFalse(conflict["dws_commands_allowed"])

    def test_identity_migration_timeout_key_new_legacy_and_conflict(self) -> None:
        dws_module = importlib.import_module("KMFA.tools.dingtalk_attendance.dws_attendance")

        self.assertEqual(
            dws_module.resolve_dws_timeout(
                {"KMFA_DINGTALK_ATTENDANCE_DWS_TIMEOUT_SECONDS": "120"},
                45,
            ),
            120,
        )
        self.assertEqual(
            dws_module.resolve_dws_timeout(
                {"KMFA_S19_DWS_TIMEOUT_SECONDS": "90"},  # legacy_read_only fallback
                45,
            ),
            90,
        )
        with self.assertRaises(DwsAttendanceError):
            dws_module.resolve_dws_timeout(
                {
                    "KMFA_DINGTALK_ATTENDANCE_DWS_TIMEOUT_SECONDS": "120",
                    "KMFA_S19_DWS_TIMEOUT_SECONDS": "90",  # legacy_read_only conflict
                },
                45,
            )

    def test_identity_migration_checker_new_entry_and_deprecated_wrapper(self) -> None:
        current = importlib.import_module(
            "KMFA.tools.dingtalk_attendance.check_dingtalk_attendance"
        )
        deprecated = importlib.import_module(
            "KMFA.tools.dingtalk_attendance.check_s19_dingtalk_attendance"  # deprecated_compatibility
        )

        self.assertIs(
            deprecated.validate_s19_files,  # deprecated_compatibility
            current.validate_dingtalk_attendance_files,
        )
        self.assertTrue(deprecated.DEPRECATED_COMPATIBILITY)

    def test_run_plan_locks_attendance_schedule_storage_and_owner(self) -> None:
        plan = build_run_plan(run_type="morning", timezone="Asia/Shanghai", run_id="contract-only")

        self.assertEqual(plan["skill_id"], "kmfa-dingtalk-attendance-skill")
        self.assertNotIn("stage_id", plan)
        self.assertEqual(plan["automation_name"], "每日早晚钉钉考勤检查")
        self.assertEqual(plan["run_type"], "morning")
        self.assertEqual(plan["timezone"], "Asia/Shanghai")
        self.assertEqual(plan["business_date_timezone"], "Asia/Shanghai")
        self.assertFalse(plan["scheduler_timezone_configured"])
        self.assertEqual(plan["schedule"]["morning"], "10:35")
        self.assertEqual(plan["schedule"]["evening"], "20:05")
        self.assertEqual(plan["schedule_clock"]["evening"], "local_wall_clock")
        self.assertEqual(
            plan["summary_datetime_source"],
            "actual_run_datetime_in_business_date_timezone",
        )
        self.assertEqual(plan["onedrive_root"], "/Users/linzezhang/OneDrive/dingtalk_attendance")
        self.assertEqual(plan["onedrive_month_folder_pattern"], "YYYYMM")
        self.assertEqual(plan["known_recipients"]["zhang_linze"]["dingtalk_user_id"], "1iv-1t2oesv2yd")
        self.assertFalse(plan["public_repo_safety"]["employee_plaintext_committed"])
        self.assertFalse(plan["public_repo_safety"]["sqlite_committed"])
        self.assertFalse(plan["public_repo_safety"]["credential_committed"])
        self.assertTrue(plan["live_only"])

    def test_cli_exit_code_fails_closed_for_runtime_and_notification_failures(self) -> None:
        self.assertEqual(
            ATTENDANCE_RUNNER.result_exit_code(
                {"status": "DWS_AUTH_REQUIRED", "notification_status": "NOT_SENT_DWS_AUTH_REQUIRED"}
            ),
            2,
        )
        self.assertEqual(ATTENDANCE_RUNNER.result_exit_code({"status": "DWS_UNAVAILABLE"}), 3)
        self.assertEqual(
            ATTENDANCE_RUNNER.result_exit_code({"status": "PARTIAL", "notification_status": "SENT"}),
            4,
        )
        self.assertEqual(
            ATTENDANCE_RUNNER.result_exit_code({"status": "COMPLETED", "notification_status": "FAILED"}),
            5,
        )
        self.assertEqual(
            ATTENDANCE_RUNNER.result_exit_code({"status": "COMPLETED", "notification_status": "SENT"}),
            0,
        )
        self.assertEqual(
            ATTENDANCE_RUNNER.result_exit_code({"status": "SENT", "notification_status": "FAILED"}),
            5,
        )
        self.assertEqual(
            ATTENDANCE_RUNNER.result_exit_code({"status": "SENT", "notification_status": "SENT"}),
            0,
        )

    def test_live_evening_summary_uses_actual_beijing_time_not_scheduler_wall_clock(self) -> None:
        captured: dict[str, str] = {}

        def capture_then_stop(*, work_date: str, summary_datetime: str, run_type: str) -> dict:
            captured["work_date"] = work_date
            captured["summary_datetime"] = summary_datetime
            captured["run_type"] = run_type
            raise DwsAttendanceError("stop after summary datetime capture")

        actual_beijing_time = datetime(2026, 7, 10, 18, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        with (
            patch.object(ATTENDANCE_RUNNER, "_scheduled_run_datetime", return_value=actual_beijing_time),
            patch.object(ATTENDANCE_RUNNER, "dws_command_safety_status", return_value={"status": "READY"}),
            patch.dict("os.environ", {}, clear=False),
        ):
            result = run_attendance(
                run_type="evening",
                timezone="Asia/Shanghai",
                collector=capture_then_stop,
                cleanup=lambda: {"status": "OK"},
            )

        self.assertEqual(result["status"], "DWS_UNAVAILABLE")
        self.assertEqual(captured["work_date"], "2026-07-10")
        self.assertEqual(captured["summary_datetime"], "2026-07-10 18:00:00")
        self.assertEqual(captured["run_type"], "evening")

    def test_run_plan_supports_controlled_work_date_rerun_datetime(self) -> None:
        plan = build_run_plan(
            run_type="morning",
            timezone="Asia/Shanghai",
            run_datetime=datetime(2026, 7, 6, 10, 35, tzinfo=ZoneInfo("Asia/Shanghai")),
        )

        self.assertEqual(plan["run_id"], "dingtalk_attendance_morning_20260706_103500")
        self.assertIn("/202607/", plan["archive_paths"]["archive_manifest"])

    def test_attendance_ledger_initializes_required_private_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "attendance_ledger.sqlite"

            result = initialize_ledger(db_path)

            self.assertEqual(result["status"], "READY")
            import sqlite3

            with closing(sqlite3.connect(db_path)) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "select name from sqlite_master where type='table' and name not like 'sqlite_%'"
                    )
                }
            self.assertTrue(
                {
                    "runs",
                    "employees",
                    "daily_attendance",
                    "punch_records",
                    "summary_items",
                    "anomalies",
                    "rest_required_snapshots",
                    "dispatch_receipts",
                    "sync_audit",
                }.issubset(tables)
            )

    def test_attendance_ledger_sync_is_idempotent_and_preserves_run_stats(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "onedrive"
            db_path = Path(tmpdir) / "attendance_ledger.sqlite"
            _write_ledger_fixture_run(
                root,
                run_id="dingtalk_attendance_evening_20260601_181500",
                work_date="2026-06-01",
                employees=[
                    {"name": "测试甲", "user_id": "u1", "punches": _fixture_punches()},
                    {"name": "测试乙", "user_id": "u2", "punches": _fixture_punches(morning=True, evening=False)},
                ],
                stats_override={"member_count": 2, "record_success_count": 2, "summary_success_count": 2},
            )

            first = sync_archives_to_ledger(onedrive_root=root, db_path=db_path, all_months=True)
            second = sync_archives_to_ledger(onedrive_root=root, db_path=db_path, all_months=True)

            self.assertEqual(first["synced_runs"], 1)
            self.assertEqual(second["synced_runs"], 1)
            summary = get_month_summary(db_path=db_path, month="202606")
            self.assertEqual(summary["run_count"], 1)
            self.assertEqual(summary["employee_count"], 2)
            self.assertEqual(summary["member_count_total"], 2)
            self.assertEqual(summary["record_success_count_total"], 2)
            self.assertEqual(summary["summary_success_count_total"], 2)
            import sqlite3

            with closing(sqlite3.connect(db_path)) as conn:
                sync_run_audits = conn.execute(
                    "select count(*) from sync_audit where event_type='SYNC_RUN' and run_id='dingtalk_attendance_evening_20260601_181500'"
                ).fetchone()[0]
            self.assertEqual(sync_run_audits, 1)

    def test_attendance_ledger_rest_required_starts_from_23rd_effective_day_and_excludes_rest_exempt_people(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "onedrive"
            db_path = Path(tmpdir) / "attendance_ledger.sqlite"
            for day in range(1, 24):
                work_date = f"2026-06-{day:02d}"
                _write_ledger_fixture_run(
                    root,
                    run_id=f"dingtalk_attendance_evening_202606{day:02d}_181500",
                    work_date=work_date,
                    employees=[
                        {"name": "测试甲", "user_id": "u1", "punches": _fixture_punches()},
                        {"name": "丁春法", "user_id": "u2", "punches": _fixture_punches()},
                        {"name": "李永占", "user_id": "u3", "punches": _fixture_punches()},
                    ],
                )

            sync_archives_to_ledger(onedrive_root=root, db_path=db_path, all_months=True)

            self.assertEqual(get_employee_month_effective_days(db_path=db_path, month="202606", employee="测试甲"), 23)
            self.assertEqual(get_employee_month_effective_days(db_path=db_path, month="202606", employee="丁春法"), 23)
            self.assertEqual(get_employee_month_effective_days(db_path=db_path, month="202606", employee="李永占"), 23)
            rest_people = get_month_rest_required_people(db_path=db_path, month="202606")
            self.assertEqual(rest_people, [{"name": "测试甲", "user_id": "u1", "first_work_date": "2026-06-23", "effective_attendance_days": 23}])

    def test_attendance_ledger_requires_both_morning_and_evening_punches_for_effective_day(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "onedrive"
            db_path = Path(tmpdir) / "attendance_ledger.sqlite"
            _write_ledger_fixture_run(
                root,
                run_id="dingtalk_attendance_evening_20260601_181500",
                work_date="2026-06-01",
                employees=[{"name": "测试甲", "user_id": "u1", "punches": _fixture_punches(morning=True, evening=False)}],
            )
            _write_ledger_fixture_run(
                root,
                run_id="dingtalk_attendance_evening_20260602_181500",
                work_date="2026-06-02",
                employees=[{"name": "测试甲", "user_id": "u1", "punches": _fixture_punches(morning=False, evening=True)}],
            )
            _write_ledger_fixture_run(
                root,
                run_id="dingtalk_attendance_evening_20260603_181500",
                work_date="2026-06-03",
                employees=[{"name": "测试甲", "user_id": "u1", "punches": _fixture_punches()}],
            )

            sync_archives_to_ledger(onedrive_root=root, db_path=db_path, all_months=True)

            self.assertEqual(get_employee_month_effective_days(db_path=db_path, month="202606", employee="测试甲"), 1)

    def test_attendance_ledger_prefers_official_effective_day_and_anomaly_over_two_punch_heuristic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "onedrive"
            db_path = Path(tmpdir) / "attendance_ledger.sqlite"
            _write_ledger_fixture_run(
                root,
                run_id="dingtalk_attendance_morning_20260711_103500",
                work_date="2026-07-11",
                employees=[
                    {
                        "name": "测试甲",
                        "user_id": "u1",
                        "punches": _fixture_punches(morning=True, evening=False),
                        "record_anomaly": True,
                        "official_effective_day": True,
                        "official_report_anomaly": False,
                    },
                    {
                        "name": "测试乙",
                        "user_id": "u2",
                        "punches": _fixture_punches(),
                        "official_effective_day": False,
                        "official_report_anomaly": True,
                        "official_report_issues": ["旷工天数=1"],
                    },
                ],
            )

            sync_archives_to_ledger(onedrive_root=root, db_path=db_path, all_months=True)

            self.assertEqual(get_employee_month_effective_days(db_path=db_path, month="202607", employee="测试甲"), 1)
            self.assertEqual(get_employee_month_effective_days(db_path=db_path, month="202607", employee="测试乙"), 0)
            anomalies = get_month_anomalies(db_path=db_path, month="202607")
            self.assertEqual([(row["name"], row["anomaly_type"]) for row in anomalies], [("测试乙", "OFFICIAL_REPORT_ANOMALY")])

    def test_attendance_ledger_canonical_user_day_prefers_official_over_later_legacy_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "onedrive"
            db_path = Path(tmpdir) / "attendance_ledger.sqlite"
            _write_ledger_fixture_run(
                root,
                run_id="dingtalk_attendance_morning_20260710_103500",
                work_date="2026-07-10",
                employees=[
                    {
                        "name": "测试甲",
                        "user_id": "u1",
                        "punches": [],
                        "official_effective_day": False,
                        "official_report_anomaly": False,
                    }
                ],
            )
            _write_ledger_fixture_run(
                root,
                run_id="dingtalk_attendance_evening_20260710_230000",
                work_date="2026-07-10",
                employees=[
                    {
                        "name": "测试甲",
                        "user_id": "u1",
                        "punches": _fixture_punches(),
                        "record_anomaly": True,
                    }
                ],
            )
            _write_ledger_fixture_run(
                root,
                run_id="dingtalk_attendance_morning_20260711_103500",
                work_date="2026-07-11",
                employees=[
                    {
                        "name": "测试甲",
                        "user_id": "u1",
                        "punches": [],
                        "official_effective_day": False,
                        "official_report_anomaly": True,
                        "official_report_issues": ["未打卡"],
                    }
                ],
            )

            sync_archives_to_ledger(onedrive_root=root, db_path=db_path, all_months=True)

            self.assertEqual(get_employee_month_effective_days(db_path=db_path, month="202607", employee="测试甲"), 0)
            anomalies = get_month_anomalies(db_path=db_path, month="202607")
            self.assertEqual(
                [(row["work_date"], row["anomaly_type"]) for row in anomalies],
                [("2026-07-11", "OFFICIAL_REPORT_ANOMALY")],
            )
            summary = get_month_summary(db_path=db_path, month="202607")
            self.assertEqual(summary["attendance_anomaly_count_total"], 1)

    def test_attendance_ledger_uses_shared_timestamp_key_for_suffixed_official_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "onedrive"
            db_path = Path(tmpdir) / "attendance_ledger.sqlite"
            _write_ledger_fixture_run(
                root,
                run_id="dingtalk_attendance_morning_20260710_103500",
                work_date="2026-07-10",
                employees=[
                    {
                        "name": "测试甲",
                        "user_id": "u1",
                        "punches": [],
                        "official_effective_day": False,
                        "official_report_anomaly": True,
                        "official_report_issues": ["未打卡"],
                    }
                ],
            )
            _write_ledger_fixture_run(
                root,
                run_id="dingtalk_attendance_evening_20260710_200000_retry",
                work_date="2026-07-10",
                employees=[
                    {
                        "name": "测试甲",
                        "user_id": "u1",
                        "punches": _fixture_punches(),
                        "official_effective_day": True,
                        "official_report_anomaly": False,
                    }
                ],
            )

            sync_archives_to_ledger(onedrive_root=root, db_path=db_path, all_months=True)

            self.assertEqual(get_employee_month_effective_days(db_path=db_path, month="202607", employee="测试甲"), 1)
            self.assertEqual(get_month_anomalies(db_path=db_path, month="202607"), [])

    def test_attendance_ledger_v1_state_fails_closed_until_raw_manifest_resync(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "onedrive"
            db_path = Path(tmpdir) / "attendance_ledger.sqlite"
            _write_ledger_fixture_run(
                root,
                run_id="dingtalk_attendance_morning_20260710_103500",
                work_date="2026-07-10",
                employees=[
                    {
                        "name": "测试甲",
                        "user_id": "u1",
                        "punches": _fixture_punches(),
                        "official_effective_day": False,
                        "official_report_anomaly": False,
                    }
                ],
            )
            sync_archives_to_ledger(onedrive_root=root, db_path=db_path, all_months=True)
            import sqlite3

            with closing(sqlite3.connect(db_path)) as conn:
                conn.execute("update daily_attendance set official_report_present = 0")
                conn.execute("update runs set canonical_schema_version = 1")
                conn.execute("drop view canonical_daily_attendance")
                conn.commit()

            validation = validate_ledger(db_path=db_path)
            self.assertEqual(validation["status"], "MIGRATION_REQUIRED")
            self.assertEqual(validation["schema_version"], 1)
            self.assertTrue(validation["migration_required"])
            with self.assertRaisesRegex(LedgerSchemaUpgradeRequired, "LEDGER_SCHEMA_MIGRATION_REQUIRED"):
                get_month_summary(db_path=db_path, month="202607")

            sync_archives_to_ledger(onedrive_root=root, db_path=db_path, all_months=True)

            validation = validate_ledger(db_path=db_path)
            self.assertEqual(validation["status"], "PASS")
            self.assertEqual(validation["schema_version"], 2)
            self.assertEqual(get_employee_month_effective_days(db_path=db_path, month="202607", employee="测试甲"), 0)

    def test_attendance_ledger_preserves_record_failure_as_system_anomaly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "onedrive"
            db_path = Path(tmpdir) / "attendance_ledger.sqlite"
            _write_ledger_fixture_run(
                root,
                run_id="dingtalk_attendance_evening_20260601_181500",
                work_date="2026-06-01",
                employees=[{"name": "测试甲", "user_id": "u1", "punches": [], "record_success": False}],
            )

            sync_archives_to_ledger(onedrive_root=root, db_path=db_path, all_months=True)

            anomalies = get_month_anomalies(db_path=db_path, month="202606")
            self.assertEqual(anomalies[0]["name"], "测试甲")
            self.assertEqual(anomalies[0]["anomaly_type"], "SYSTEM_RECORD_FAILURE")
            self.assertEqual(get_employee_month_effective_days(db_path=db_path, month="202606", employee="测试甲"), 0)

    def test_attendance_ledger_default_database_path_is_git_ignored_private_runtime(self) -> None:
        self.assertEqual(DEFAULT_LEDGER_PATH.name, "attendance_ledger.sqlite")
        self.assertIn("metadata/dingtalk_attendance/private_runtime", DEFAULT_LEDGER_PATH.as_posix())
        result = __import__("subprocess").run(
            ["git", "check-ignore", "-q", str(DEFAULT_LEDGER_PATH.relative_to(ROOT))],
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(result.returncode, 0)

    def test_attendance_ledger_validate_reports_ready_after_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "onedrive"
            db_path = Path(tmpdir) / "attendance_ledger.sqlite"
            paths = _write_ledger_fixture_run(
                root,
                run_id="dingtalk_attendance_evening_20260601_181500",
                work_date="2026-06-01",
                employees=[{"name": "测试甲", "user_id": "u1", "punches": _fixture_punches()}],
            )

            sync_archives_to_ledger(onedrive_root=root, db_path=db_path, all_months=True)

            validation = validate_ledger(db_path=db_path)
            self.assertEqual(validation["status"], "PASS")
            self.assertEqual(get_run_sync_status(db_path=db_path, run_id="dingtalk_attendance_evening_20260601_181500")["raw_path"], str(paths["raw"]))

    def test_run_attendance_fails_closed_before_dws_without_explicit_auth_allow(self) -> None:
        def blocked_collector(**kwargs: object) -> dict:
            raise AssertionError("collector must not be called when DWS auth is not explicitly allowed")

        result = run_attendance(
            run_type="morning",
            timezone="Asia/Shanghai",
            env={},
            collector=blocked_collector,
            cleanup=lambda: {"status": "OK"},
        )

        self.assertEqual(result["status"], "DWS_AUTH_REQUIRED")
        self.assertEqual(result["collection_status"], "SKIPPED_DWS_AUTH_REQUIRED")
        self.assertEqual(result["notification_status"], "NOT_SENT_DWS_AUTH_REQUIRED")
        self.assertFalse(result["dws_command_safety"]["dws_commands_allowed"])
        self.assertEqual(result["dws_command_safety"]["required_env"], "KMFA_DINGTALK_ATTENDANCE_ALLOW_DWS_COMMANDS")

    def test_dws_command_safety_requires_explicit_local_allow(self) -> None:
        blocked = dws_command_safety_status(env={})
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "pat_policy.json"
            policy_path.write_text(json.dumps({"default": {"openBrowser": False}}, ensure_ascii=False), encoding="utf-8")
            allowed = dws_command_safety_status(
                env={
                    "KMFA_DINGTALK_ATTENDANCE_ALLOW_DWS_COMMANDS": "1",
                    "KMFA_DINGTALK_ATTENDANCE_DWS_BROWSER_POLICY_PATH": str(policy_path),
                }
            )

        self.assertEqual(blocked["status"], "DWS_AUTH_REQUIRED")
        self.assertFalse(blocked["dws_commands_allowed"])
        self.assertEqual(allowed["status"], "READY")
        self.assertTrue(allowed["dws_commands_allowed"])

    def test_dws_command_safety_rejects_allow_without_no_browser_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "pat_policy.json"
            policy_path.write_text(json.dumps({"default": {"openBrowser": True}}, ensure_ascii=False), encoding="utf-8")
            result = dws_command_safety_status(
                env={
                    "KMFA_DINGTALK_ATTENDANCE_ALLOW_DWS_COMMANDS": "1",
                    "KMFA_DINGTALK_ATTENDANCE_DWS_BROWSER_POLICY_PATH": str(policy_path),
                }
            )

        self.assertEqual(result["status"], "DWS_BROWSER_POLICY_REQUIRED")
        self.assertFalse(result["dws_commands_allowed"])
        self.assertFalse(result["browser_popup_prevention"])

    def test_default_dws_helpers_fail_closed_without_starting_subprocess(self) -> None:
        with (
            patch("KMFA.tools.dingtalk_attendance.dws_auth_guard.merged_runtime_env", return_value={}),
            patch("subprocess.run") as subprocess_run,
        ):
            help_text = get_dws_help(["dws", "chat", "message", "send"])
            result = run_dws_command(["dws", "contact", "user", "get", "--ids", "u1"], timeout=1)

        self.assertEqual(help_text, "")
        self.assertEqual(result["returncode"], 1)
        self.assertEqual(result["payload"]["error"]["reason"], "DWS_AUTH_REQUIRED")
        subprocess_run.assert_not_called()

    def test_notification_target_probe_fails_closed_without_overwriting_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            targets_config = root / "notification_targets.local.json"
            targets_resolved = root / "notification_targets_resolved.json"
            public_manifest = root / "notification_targets_manifest.json"
            targets_config.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "targets": [
                            {
                                "label": "张霖泽",
                                "type": "personal",
                                "enabled": True,
                                "reports": ["management", "hr"],
                                "user_id": "1iv-1t2oesv2yd",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            existing_resolved = {
                "schema_version": 1,
                "targets": [
                    {
                        "label": "张霖泽",
                        "type": "personal",
                        "enabled": True,
                        "reports": ["management", "hr"],
                        "resolved_channel": "dws_open_dingtalk_id_chat",
                        "user_id": "1iv-1t2oesv2yd",
                        "open_dingtalk_id": "open-secret-id",
                        "last_probe_status": "SENT",
                    }
                ],
            }
            targets_resolved.write_text(json.dumps(existing_resolved, ensure_ascii=False), encoding="utf-8")

            with patch("subprocess.run") as subprocess_run:
                result = probe_notification_targets(
                    targets_config_path=targets_config,
                    targets_resolved_path=targets_resolved,
                    public_manifest_path=public_manifest,
                    env={},
                )

            self.assertEqual(result["status"], "DWS_AUTH_REQUIRED")
            self.assertEqual(json.loads(targets_resolved.read_text(encoding="utf-8")), existing_resolved)
            self.assertFalse(public_manifest.exists())
            subprocess_run.assert_not_called()

    def test_config_only_healthcheck_fails_closed_without_notification_channel(self) -> None:
        status = build_config_status(env={})

        self.assertEqual(status["status"], "NOTIFIER_CONFIG_MISSING")
        self.assertFalse(status["notification_ready"])
        self.assertFalse(status["uses_sample_data"])
        self.assertIn("DINGTALK_ROBOT_URL", status["group_robot_missing"])
        self.assertIn("DINGTALK_APP_KEY", status["work_notification_missing"])

    def test_config_only_healthcheck_marks_group_robot_ready_without_work_notification(self) -> None:
        status = build_config_status(
            env={
                "DINGTALK_NOTIFY_MODE": "dingtalk_group_robot",
                "DINGTALK_ROBOT_URL": "https://example.invalid/robot/send?token=masked",
                "DINGTALK_ROBOT_SIGNING_KEY": "local-signing-key",
            }
        )

        self.assertEqual(status["status"], "READY")
        self.assertTrue(status["notification_ready"])
        self.assertTrue(status["notifier_configured"])
        self.assertEqual(status["active_notify_mode"], "dingtalk_group_robot")
        self.assertEqual(status["notification_ready_channels"], ["dingtalk_group_robot"])
        self.assertEqual(status["group_robot_missing"], [])
        self.assertIn("DINGTALK_BOSS_USER_ID", status["work_notification_missing"])

    def test_config_only_healthcheck_marks_work_notification_ready_without_group_robot(self) -> None:
        status = build_config_status(
            env={
                "DINGTALK_BOSS_USER_ID": "boss-user",
                "DINGTALK_APP_KEY": "app-key",
                "DINGTALK_APP_CREDENTIAL": "credential",
                "DINGTALK_CORP_ID": "corp-id",
                "DINGTALK_AGENT_ID": "agent-id",
            }
        )

        self.assertEqual(status["status"], "READY")
        self.assertTrue(status["notification_ready"])
        self.assertEqual(status["notification_ready_channels"], ["dingtalk_work_notification"])

    def test_report_templates_keep_management_and_hr_boundaries(self) -> None:
        self.assertEqual(
            MANAGEMENT_REPORT_SECTIONS,
            ("一、总体情况", "二、今日异常人员", "三、建议动作", "四、系统运行状态"),
        )
        self.assertEqual(
            HR_REPORT_SECTIONS,
            ("一、异常明细", "二、连续异常人员", "三、数据质量与系统运行状态"),
        )
        self.assertNotIn("关键人员风险", json.dumps(MANAGEMENT_REPORT_SECTIONS, ensure_ascii=False))

    def test_sensitive_payload_scanner_rejects_credentials_and_robot_endpoint(self) -> None:
        bad_payloads = [
            "access" + "_token=abc",
            "app" + "_sec" + "ret=abc",
            "sec" + "ret=abc",
            "https://oapi.dingtalk.com/robot/" + "send?access" + "_token=abc",
        ]

        for payload in bad_payloads:
            with self.subTest(payload=payload):
                findings = scan_payload_for_sensitive_text(payload)
                self.assertGreaterEqual(len(findings), 1)
        allowed_schema_payload = "web" + "hook_env_key=DINGTALK_GROUP_ENDPOINT_ENV"
        self.assertEqual(scan_payload_for_sensitive_text(allowed_schema_payload), [])
        self.assertEqual(scan_payload_for_sensitive_text("credential_" + "sec" + "ret=false"), [])

    def test_attendance_file_contract_is_complete_and_private_runtime_is_placeholder_only(self) -> None:
        result = validate_dingtalk_attendance_files(ROOT)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["automation_name"], "每日早晚钉钉考勤检查")
        self.assertEqual(result["skill_id"], "kmfa-dingtalk-attendance-skill")
        self.assertEqual(result["onedrive_root"], "/Users/linzezhang/OneDrive/dingtalk_attendance")
        self.assertEqual(result["prompt_count"], 3)
        self.assertTrue(result["prompt_mirrors_match"])
        self.assertEqual(result["private_runtime_tracked_files"], [".gitkeep", "README.md"])
        self.assertTrue(result["automation_prompt_contracts"]["all_prompts_call_skill"])
        self.assertTrue(result["automation_prompt_contracts"]["all_prompts_use_beijing_time"])
        self.assertTrue(result["automation_prompt_contracts"]["all_prompts_preserve_github_sync"])
        self.assertTrue(result["automation_prompt_contracts"]["all_prompts_fail_closed_for_dws"])
        self.assertTrue(result["automation_prompt_contracts"]["temporary_prompts_use_realtime_integrity"])
        self.assertTrue(result["automation_prompt_contracts"]["temporary_prompts_reject_final_parity_gate"])
        self.assertTrue(result["automation_prompt_contracts"]["final_prompts_keep_official_report_parity"])
        self.assertTrue(result["automation_prompt_contracts"]["all_prompts_protect_private_runtime"])

    def test_official_collector_uses_attendance_group_scope_and_official_report_as_business_truth(self) -> None:
        runner = OfficialParityFixtureRunner()

        collection = collect_official_org_attendance(
            work_date="2026-07-11",
            summary_datetime="2026-07-11 10:35:00",
            runner=runner,
        )

        self.assertEqual(collection["stats"]["member_count"], 2)
        self.assertEqual(collection["stats"]["attendance_group_member_count"], 2)
        self.assertEqual(collection["stats"]["official_report_expected_count"], 2)
        self.assertEqual(collection["stats"]["official_report_coverage_count"], 2)
        self.assertEqual(collection["stats"]["official_report_parity_status"], "PASS")
        self.assertEqual(collection["stats"]["official_report_anomaly_names"], ["异常员工"])
        self.assertEqual(collection["stats"]["attendance_anomaly_names"], ["异常员工"])
        self.assertEqual(collection["stats"]["attendance_anomaly_count"], 1)
        self.assertEqual(collection["stats"]["record_incomplete_success_count"], 0)
        self.assertEqual(collection["stats"]["legacy_diagnostic_skipped_count"], 2)
        self.assertNotIn("正常员工", collection["stats"]["attendance_anomaly_names"])
        self.assertNotIn("非考勤组员工", [row["member"]["name"] for row in collection["results"]])
        self.assertEqual(
            [row["derived"]["official_status_text"] for row in collection["results"]],
            ["旷工", "正常"],
        )
        report_queries = [call for call in runner.calls if call[:3] == ("attendance", "report", "query-data")]
        self.assertEqual(len(report_queries), 1)
        self.assertEqual(report_queries[0][report_queries[0].index("--start") + 1], "2026-07-11 00:00:00")
        self.assertEqual(report_queries[0][report_queries[0].index("--end") + 1], "2026-07-11 23:59:59")

    def test_official_collector_keeps_record_and_summary_permission_errors_diagnostic_only(self) -> None:
        delegate = OfficialParityFixtureRunner()

        def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            if args[:2] in (["attendance", "record"], ["attendance", "summary"]):
                raise DwsAttendanceError("diagnostic scope unavailable")
            return delegate(args, timeout=timeout, verbose=verbose)

        collection = collect_official_org_attendance(
            work_date="2026-07-11",
            summary_datetime="2026-07-11 10:35:00",
            runner=runner,
        )

        self.assertEqual(collection["stats"]["official_report_parity_status"], "PASS")
        self.assertEqual(collection["stats"]["official_report_coverage_count"], 2)
        self.assertEqual(collection["stats"]["official_report_anomaly_count"], 1)
        self.assertEqual(collection["stats"]["command_failure_count"], 0)
        self.assertEqual(collection["stats"]["legacy_diagnostic_skipped_count"], 2)
        self.assertIsNone(official_report_parity_failure_reason(collection["stats"]))

    def test_official_collector_does_not_block_on_legacy_per_member_diagnostics(self) -> None:
        delegate = OfficialParityFixtureRunner()

        def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            if args[:2] in (["attendance", "record"], ["attendance", "summary"]):
                raise AssertionError("official production collector must not call legacy per-member diagnostics")
            return delegate(args, timeout=timeout, verbose=verbose)

        collection = collect_official_org_attendance(
            work_date="2026-07-11",
            summary_datetime="2026-07-11 10:35:00",
            runner=runner,
        )

        self.assertEqual(collection["stats"]["official_report_parity_status"], "PASS")
        self.assertEqual(collection["stats"]["official_report_coverage_count"], 2)
        self.assertEqual(collection["stats"]["legacy_diagnostic_mode"], "SKIPPED_OFFICIAL_REPORT_AUTHORITATIVE")
        self.assertEqual(collection["stats"]["legacy_diagnostic_skipped_count"], 2)
        self.assertEqual(collection["stats"]["command_failure_count"], 0)

    def test_realtime_morning_replay_accepts_unsettled_final_metrics_with_exact_live_coverage(self) -> None:
        runner = RealtimeMorningReplayRunner()

        collection = collect_realtime_reminder_attendance(
            work_date="2026-07-13",
            summary_datetime="2026-07-13 08:54:50",
            run_type="morning",
            runner=runner,
        )

        stats = collection["stats"]
        self.assertEqual(stats["realtime_reminder_integrity_status"], "PASS")
        self.assertEqual(stats["realtime_reminder_run_type"], "morning")
        self.assertEqual(stats["realtime_reminder_expected_count"], 2)
        self.assertEqual(stats["realtime_reminder_coverage_count"], 2)
        self.assertEqual(stats["realtime_reminder_query_failure_count"], 0)
        self.assertEqual(stats["realtime_reminder_parse_failure_count"], 0)
        self.assertEqual(stats["attendance_anomaly_names"], ["异常员工"])
        self.assertNotIn("official_report_parity_status", stats)
        self.assertIsNone(realtime_reminder_integrity_failure_reason(stats, run_type="morning"))
        self.assertTrue(any(call[:2] == ("attendance", "record") for call in runner.calls))
        self.assertTrue(any(call[:2] == ("attendance", "summary") for call in runner.calls))
        self.assertFalse(any(call[:3] == ("attendance", "report", "query-data") for call in runner.calls))

    def test_realtime_evening_accepts_successful_empty_punch_result_as_covered(self) -> None:
        runner = RealtimeMorningReplayRunner()

        original_call = runner.__call__

        def empty_punch_runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            if args[:5] == ["attendance", "record", "get", "--user", "u-normal"]:
                runner.calls.append(tuple(args))
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "result": {"recordList": [], "isHasSchedule": True, "isRest": False},
                    },
                }
            return original_call(args, timeout=timeout, verbose=verbose)

        collection = collect_realtime_reminder_attendance(
            work_date="2026-07-13",
            summary_datetime="2026-07-13 18:02:22",
            run_type="evening",
            runner=empty_punch_runner,
        )

        self.assertEqual(collection["stats"]["realtime_reminder_coverage_count"], 2)
        self.assertEqual(collection["stats"]["realtime_reminder_query_failure_count"], 0)
        self.assertNotIn("official_report_parity_status", collection["stats"])

    def test_realtime_morning_replay_fails_closed_when_current_member_is_missing(self) -> None:
        runner = RealtimeMorningReplayRunner(omit_user="u-normal")

        with self.assertRaisesRegex(RealtimeReminderIntegrityError, "REALTIME_REMINDER_PARSE_FAILED"):
            collect_realtime_reminder_attendance(
                work_date="2026-07-13",
                summary_datetime="2026-07-13 08:54:50",
                run_type="morning",
                runner=runner,
            )

    def test_realtime_morning_replay_fails_closed_when_live_query_fails(self) -> None:
        runner = RealtimeMorningReplayRunner(query_failure=True)

        with self.assertRaisesRegex(RealtimeReminderIntegrityError, "REALTIME_REMINDER_QUERY_FAILED"):
            collect_realtime_reminder_attendance(
                work_date="2026-07-13",
                summary_datetime="2026-07-13 08:54:50",
                run_type="morning",
                runner=runner,
            )

    def test_realtime_reminder_fails_closed_when_punch_date_is_wrong(self) -> None:
        runner = RealtimeMorningReplayRunner()
        original_call = runner.__call__

        def wrong_date_runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            result = original_call(args, timeout=timeout, verbose=verbose)
            if args[:5] == ["attendance", "record", "get", "--user", "u-normal"]:
                result["payload"]["result"]["recordList"][0]["userCheckTime"] = "2026-07-12 08:30:00"
            return result

        with self.assertRaisesRegex(RealtimeReminderIntegrityError, "REALTIME_REMINDER_PARSE_FAILED"):
            collect_realtime_reminder_attendance(
                work_date="2026-07-13",
                summary_datetime="2026-07-13 18:02:22",
                run_type="evening",
                runner=wrong_date_runner,
            )

    def test_r6_failed_slot_persists_redacted_integrity_details_in_private_status(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import R6Coordinator

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            coordinator = R6Coordinator(root)
            result = coordinator.ensure_slot(
                work_date="2026-07-13",
                run_slot="evening",
                trigger_source="automation",
                runner=lambda: {
                    "status": "REALTIME_REMINDER_INTEGRITY_FAILED",
                    "notification_status": "NOT_SENT_REALTIME_REMINDER_INTEGRITY_FAILED",
                    "integrity_error": "batch coverage mismatch",
                    "error_code": "REALTIME_REMINDER_COVERAGE_MISMATCH",
                    "coverage_stats": {
                        "expected_people": 42,
                        "queried_people": 15,
                        "successful_people": 10,
                        "missing_people": 32,
                        "failed_batch_index": 3,
                        "failed_batch_expected": 5,
                        "failed_batch_actual": None,
                        "query_failure_count": 0,
                        "parse_failure_count": 0,
                    },
                },
                completed_probe=lambda: None,
            )
            state = json.loads((root / "state.json").read_text(encoding="utf-8"))
            private_slot = state["work_dates"]["2026-07-13"]["slots"]["evening"]
            chinese_status = (root / "运行状态.md").read_text(encoding="utf-8")

        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(private_slot["error_code"], "REALTIME_REMINDER_COVERAGE_MISMATCH")
        self.assertEqual(private_slot["coverage_stats"]["expected_people"], 42)
        self.assertEqual(private_slot["coverage_stats"]["failed_batch_index"], 3)
        self.assertIn("REALTIME_REMINDER_COVERAGE_MISMATCH", chinese_status)
        self.assertIn("期望人数 42", chinese_status)

    def test_r6_prior_final_waiting_does_not_block_current_evening_reminder(self) -> None:
        from KMFA.tools.dingtalk_attendance.automatic_closure import R6Coordinator

        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = R6Coordinator(Path(tmpdir))
            final = coordinator.advance_final(
                work_date="2026-07-12",
                export_finder=lambda: None,
                certificate_builder=lambda _: (_ for _ in ()).throw(AssertionError("no export")),
                final_runner=lambda _: (_ for _ in ()).throw(AssertionError("no certificate")),
                completed_probe=lambda: None,
            )
            evening = coordinator.ensure_slot(
                work_date="2026-07-13",
                run_slot="evening",
                trigger_source="automation",
                runner=lambda: {
                    "status": "COMPLETED",
                    "notification_status": "SENT",
                    "member_count": 42,
                    "run_id": "dingtalk_attendance_evening_20260713_180222",
                },
                completed_probe=lambda: None,
            )
            state = json.loads((Path(tmpdir) / "state.json").read_text(encoding="utf-8"))

        self.assertEqual(final["status"], "WAITING_OFFICIAL_REPORT")
        self.assertEqual(evening["status"], "COMPLETED")
        self.assertEqual(state["work_dates"]["2026-07-12"]["final"]["status"], "WAITING_OFFICIAL_REPORT")
        self.assertEqual(state["work_dates"]["2026-07-13"]["slots"]["evening"]["status"], "COMPLETED")

    def test_official_collector_fails_closed_when_report_coverage_is_incomplete(self) -> None:
        runner = OfficialParityFixtureRunner(omit_user="u-normal")

        with self.assertRaisesRegex(OfficialAttendanceParityError, "OFFICIAL_REPORT_COVERAGE_MISMATCH"):
            collect_official_org_attendance(
                work_date="2026-07-11",
                summary_datetime="2026-07-11 10:35:00",
                runner=runner,
            )

    def test_official_collector_fails_closed_for_missing_exact_column_unknown_status_and_wrong_date(self) -> None:
        scenarios = (
            (
                OfficialParityFixtureRunner(omit_column="旷工天数"),
                "OFFICIAL_REPORT_REQUIRED_COLUMN_MISSING",
            ),
            (
                OfficialParityFixtureRunner(status_overrides={"u-normal": "未来新增状态"}),
                "OFFICIAL_REPORT_STATUS_UNKNOWN",
            ),
            (
                OfficialParityFixtureRunner(status_overrides={"u-normal": "未出勤"}),
                "OFFICIAL_REPORT_STATUS_UNKNOWN",
            ),
            (
                OfficialParityFixtureRunner(status_overrides={"u-normal": "非正常"}),
                "OFFICIAL_REPORT_STATUS_UNKNOWN",
            ),
            (
                OfficialParityFixtureRunner(date_overrides={"u-normal": "2026-07-10"}),
                "OFFICIAL_REPORT_DATE_MISMATCH",
            ),
        )
        for runner, expected_code in scenarios:
            with self.subTest(expected_code=expected_code):
                with self.assertRaisesRegex(OfficialAttendanceParityError, expected_code):
                    collect_official_org_attendance(
                        work_date="2026-07-11",
                        summary_datetime="2026-07-11 10:35:00",
                        runner=runner,
                    )

    def test_official_collector_accepts_only_explicit_known_status_combinations(self) -> None:
        runner = OfficialParityFixtureRunner(
            status_overrides={"u-normal": "上班外勤+下班外勤"},
        )

        collection = collect_official_org_attendance(
            work_date="2026-07-11",
            summary_datetime="2026-07-11 10:35:00",
            runner=runner,
        )

        normal = next(row for row in collection["results"] if row["member"]["userId"] == "u-normal")
        self.assertEqual(normal["derived"]["official_status_category"], "non_anomaly")

    def test_official_report_rejects_cross_batch_user_swaps(self) -> None:
        column_ids = {
            name: f"c-{index}"
            for index, name in enumerate(OfficialParityFixtureRunner.REQUIRED_COLUMNS, start=1)
        }
        members = [{"userId": f"u-{index}", "name": f"员工{index}"} for index in range(1, 7)]

        def report_row(user_id: str) -> dict[str, object]:
            values = {
                "考勤结果": "正常",
                "应出勤天数": "1",
                "出勤天数": "1",
                "休息天数": "0",
                "迟到次数": "0",
                "早退次数": "0",
                "上班缺卡次数": "0",
                "下班缺卡次数": "0",
                "旷工天数": "0",
            }
            return {
                "userId": user_id,
                "workDate": "2026-07-11",
                "values": [
                    {"termId": column_ids[name], "value": value}
                    for name, value in values.items()
                ],
            }

        def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            requested = args[args.index("--users") + 1].split(",")
            returned = [*requested[:-1], "u-6"] if len(requested) == 5 else ["u-5"]
            return {
                "returncode": 0,
                "payload": {"success": True, "result": {"records": [report_row(user_id) for user_id in returned]}},
            }

        with self.assertRaisesRegex(OfficialAttendanceParityError, "OFFICIAL_REPORT_BATCH_SCOPE_MISMATCH"):
            _query_official_report(
                runner=runner,
                members=members,
                work_date="2026-07-11",
                column_ids=column_ids,
            )

    def test_official_group_permission_failure_is_reported_as_parity_failure(self) -> None:
        delegate = OfficialParityFixtureRunner()

        def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            if args[:3] == ["attendance", "group", "search"]:
                return {
                    "returncode": 4,
                    "payload": {
                        "success": False,
                        "code": "PAT_MEDIUM_RISK_NO_PERMISSION",
                        "data": {"openBrowser": True, "requiredScopes": [{"scope": "attendance.group:read"}]},
                    },
                }
            return delegate(args, timeout=timeout, verbose=verbose)

        with self.assertRaisesRegex(OfficialAttendanceParityError, "OFFICIAL_REPORT_PERMISSION_REQUIRED"):
            collect_official_org_attendance(
                work_date="2026-07-11",
                summary_datetime="2026-07-11 10:35:00",
                runner=runner,
            )

    def test_run_dws_json_maps_subprocess_timeout_to_retryable_result(self) -> None:
        timeout_error = __import__("subprocess").TimeoutExpired(cmd="dws", timeout=65)
        with (
            patch(
                "KMFA.tools.dingtalk_attendance.dws_attendance.dws_command_safety_status",
                return_value={"status": "READY"},
            ),
            patch("KMFA.tools.dingtalk_attendance.dws_attendance.subprocess.run", side_effect=timeout_error),
        ):
            result = run_dws_json(["attendance", "report", "columns"], timeout=60)

        self.assertEqual(result["returncode"], 124)
        self.assertEqual(result["payload"]["code"], "request_timeout")
        self.assertTrue(result["payload"]["error"]["retryable"])

    def test_notification_uses_only_official_report_anomaly_names_when_parity_is_present(self) -> None:
        context = notification_context_from_output_status(
            {
                "run_id": "dingtalk_attendance_morning_20260711_103500",
                "run_type": "morning",
                "work_date": "2026-07-11",
                "current_time": "10:35",
                "stats": {
                    "member_count": 2,
                    "record_success_count": 2,
                    "summary_success_count": 2,
                    "record_failure_count": 0,
                    "summary_failure_count": 0,
                    "command_failure_count": 0,
                    "official_report_parity_status": "PASS",
                    "official_report_failure_count": 0,
                    "official_report_anomaly_names": ["官方异常员工"],
                    "unexpected_empty_record_names": ["原始记录误报员工"],
                    "incomplete_record_names": ["两卡规则误报员工"],
                    "summary_today_anomaly_names": ["摘要误报员工"],
                },
            }
        )
        body = build_notification_message(**context, markdown=False)

        self.assertIn("官方异常员工", body)
        self.assertNotIn("原始记录误报员工", body)
        self.assertNotIn("两卡规则误报员工", body)
        self.assertNotIn("摘要误报员工", body)

    def test_official_delivery_gate_requires_complete_exact_stats(self) -> None:
        valid = _official_pass_stats(member_count=2, anomaly_names=["异常员工"])
        self.assertIsNone(official_report_parity_failure_reason(valid))
        self.assertTrue(collection_is_complete(valid))

        scenarios: list[dict[str, object]] = []
        for missing_key in (
            "attendance_group_member_count",
            "member_count",
            "official_report_expected_count",
            "official_report_coverage_count",
            "official_report_failure_count",
            "official_report_anomaly_count",
            "official_report_anomaly_names",
            "attendance_required_count",
            "official_effective_day_count",
        ):
            candidate = dict(valid)
            candidate.pop(missing_key)
            scenarios.append(candidate)
        scenarios.extend(
            [
                {**valid, "official_report_parity_status": "FAILED"},
                {**valid, "member_count": 0, "attendance_group_member_count": 0, "official_report_expected_count": 0, "official_report_coverage_count": 0},
                {**valid, "official_report_coverage_count": 1},
                {**valid, "official_report_failure_count": 1},
                {**valid, "official_report_anomaly_count": 0},
            ]
        )
        for stats in scenarios:
            with self.subTest(stats=stats):
                self.assertIsNotNone(official_report_parity_failure_reason(stats))
                self.assertFalse(collection_is_complete(stats))

    def test_official_delivery_gate_ignores_legacy_diagnostic_failures(self) -> None:
        stats = {
            **_official_pass_stats(member_count=2),
            "record_failure_count": 2,
            "summary_failure_count": 2,
            "command_failure_count": 4,
        }

        self.assertIsNone(official_report_parity_failure_reason(stats))
        self.assertTrue(collection_is_complete(stats))

    def test_official_delivery_gate_allows_distinct_people_with_the_same_display_name(self) -> None:
        stats = _official_pass_stats(member_count=2, anomaly_names=["同名员工", "同名员工"])

        self.assertIsNone(official_report_parity_failure_reason(stats))
        self.assertTrue(collection_is_complete(stats))

    def test_run_attendance_fails_closed_without_notification_when_official_parity_fails(self) -> None:
        def parity_failure_collector(**kwargs: object) -> dict:
            raise OfficialAttendanceParityError(
                "OFFICIAL_REPORT_COVERAGE_MISMATCH",
                "expected 2 users, received 1",
            )

        with patch.object(ATTENDANCE_RUNNER, "dws_command_safety_status", return_value={"status": "READY"}):
            result = run_attendance(
                run_type="morning",
                timezone="Asia/Shanghai",
                collector=parity_failure_collector,
                cleanup=lambda: {"status": "OK"},
            )

        self.assertEqual(result["status"], "OFFICIAL_ATTENDANCE_PARITY_FAILED")
        self.assertEqual(result["collection_status"], "SKIPPED_OFFICIAL_ATTENDANCE_PARITY_FAILED")
        self.assertEqual(result["notification_status"], "NOT_SENT_OFFICIAL_ATTENDANCE_PARITY_FAILED")
        self.assertEqual(ATTENDANCE_RUNNER.result_exit_code(result), 6)

    def test_run_attendance_rejects_collector_payload_without_exact_parity_before_archive(self) -> None:
        def incomplete_collector(**kwargs: object) -> dict[str, object]:
            return {"stats": {}, "results": []}

        with (
            patch.object(ATTENDANCE_RUNNER, "dws_command_safety_status", return_value={"status": "READY"}),
            patch.object(
                ATTENDANCE_RUNNER,
                "write_private_outputs",
                side_effect=AssertionError("must not archive a parity-failed collection"),
            ),
        ):
            result = run_attendance(
                run_type="morning",
                timezone="Asia/Shanghai",
                collector=incomplete_collector,
                cleanup=lambda: {"status": "OK"},
            )

        self.assertEqual(result["status"], "REALTIME_REMINDER_INTEGRITY_FAILED")
        self.assertEqual(result["notification_status"], "NOT_SENT_REALTIME_REMINDER_INTEGRITY_FAILED")
        self.assertEqual(result["error_code"], "REALTIME_REMINDER_INTEGRITY_ASSERTION_FAILED")
        self.assertEqual(result["coverage_stats"]["expected_people"], 0)
        self.assertEqual(result["coverage_stats"]["successful_people"], 0)

    def test_automatic_slot_runner_preserves_integrity_details_for_coordinator(self) -> None:
        automatic_closure = importlib.import_module("KMFA.tools.dingtalk_attendance.automatic_closure")
        with patch.object(
            automatic_closure,
            "run_attendance",
            return_value={
                "status": "REALTIME_REMINDER_INTEGRITY_FAILED",
                "notification_status": "NOT_SENT_REALTIME_REMINDER_INTEGRITY_FAILED",
                "integrity_error": "REALTIME_REMINDER_QUERY_FAILED: scoped query failed",
                "error_code": "REALTIME_REMINDER_QUERY_FAILED",
                "coverage_stats": {
                    "expected_people": 42,
                    "queried_people": 42,
                    "successful_people": 41,
                    "missing_people": 1,
                    "query_failure_count": 1,
                    "parse_failure_count": 0,
                },
                "collection_stats": {},
                "run_plan": {"run_id": "dingtalk_attendance_evening_20260713_180222"},
            },
        ) as run_mock:
            result = automatic_closure._slot_runner(run_slot="evening")

        self.assertEqual(result["error_code"], "REALTIME_REMINDER_QUERY_FAILED")
        self.assertEqual(result["coverage_stats"]["missing_people"], 1)
        self.assertEqual(run_mock.call_args.kwargs["notification_target_filter"], "group")

    def test_run_attendance_passes_run_type_and_uses_realtime_reminder_gate(self) -> None:
        captured: dict[str, object] = {}
        dispatch_calls: list[dict[str, object]] = []
        runner = RealtimeMorningReplayRunner()

        def realtime_collector(**kwargs: object) -> dict[str, object]:
            captured.update(kwargs)
            return collect_realtime_reminder_attendance(
                work_date=str(kwargs["work_date"]),
                summary_datetime=str(kwargs["summary_datetime"]),
                run_type=str(kwargs["run_type"]),
                runner=runner,
            )

        def fake_dispatch(**kwargs: object) -> dict[str, object]:
            dispatch_calls.append(dict(kwargs))
            output_status = kwargs["output_status"]
            assert isinstance(output_status, dict)
            receipt = {
                "notification_status": "SENT",
                "messages": [{"report": "attendance_notification", "status": "SENT"}],
                "target_results": [{"type": "group", "status": "SENT"}],
            }
            Path(str(output_status["dispatch_receipt"])).write_text(
                json.dumps(receipt, ensure_ascii=False), encoding="utf-8"
            )
            return receipt

        with tempfile.TemporaryDirectory() as tmpdir:
            archive_root = Path(tmpdir)
            plan = ATTENDANCE_RUNNER.build_run_plan(
                "morning",
                run_datetime=datetime(2026, 7, 13, 8, 54, 50, tzinfo=ZoneInfo("Asia/Shanghai")),
            )
            plan["archive_paths"] = {
                "month_dir": str(archive_root),
                "raw_jsonl_gz": str(archive_root / "raw.jsonl.gz"),
                "management_report": str(archive_root / "management.md"),
                "hr_report": str(archive_root / "hr.md"),
                "dispatch_receipt": str(archive_root / "receipt.json"),
                "archive_manifest": str(archive_root / "manifest.json"),
                "cleanup_audit": str(archive_root / "cleanup.json"),
            }
            with (
                patch.object(ATTENDANCE_RUNNER, "build_run_plan", return_value=plan),
                patch.object(ATTENDANCE_RUNNER, "dws_command_safety_status", return_value={"status": "READY"}),
                patch.object(ATTENDANCE_RUNNER, "build_stats_with_rest_required_people", side_effect=lambda stats, **_: stats),
                patch.object(ATTENDANCE_RUNNER, "dispatch_reports_to_targets", side_effect=fake_dispatch),
            ):
                result = run_attendance(
                    run_type="morning",
                    timezone="Asia/Shanghai",
                    work_date="2026-07-13",
                    collector=realtime_collector,
                    cleanup=lambda: {"status": "OK"},
                )
            receipt = json.loads((archive_root / "receipt.json").read_text(encoding="utf-8"))

        self.assertEqual(captured["run_type"], "morning")
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["notification_status"], "SENT")
        self.assertEqual(receipt["notification_status"], "SENT")
        self.assertEqual(dispatch_calls[0]["target_filter"], "group")

    def test_run_attendance_realtime_incomplete_payload_fails_before_archive(self) -> None:
        def incomplete_collector(**kwargs: object) -> dict[str, object]:
            return {
                "stats": {
                    "realtime_reminder_integrity_status": "PASS",
                    "realtime_reminder_run_type": kwargs["run_type"],
                    "attendance_group_member_count": 2,
                    "member_count": 2,
                    "realtime_reminder_expected_count": 2,
                    "realtime_reminder_coverage_count": 1,
                    "realtime_reminder_query_failure_count": 0,
                    "realtime_reminder_parse_failure_count": 0,
                    "realtime_reminder_anomaly_count": 0,
                    "realtime_reminder_anomaly_names": [],
                },
                "results": [],
            }

        with (
            patch.object(ATTENDANCE_RUNNER, "dws_command_safety_status", return_value={"status": "READY"}),
            patch.object(
                ATTENDANCE_RUNNER,
                "write_private_outputs",
                side_effect=AssertionError("must not archive an incomplete realtime reminder"),
            ),
        ):
            result = run_attendance(
                run_type="morning",
                timezone="Asia/Shanghai",
                work_date="2026-07-13",
                collector=incomplete_collector,
                cleanup=lambda: {"status": "OK"},
            )

        self.assertEqual(result["status"], "REALTIME_REMINDER_INTEGRITY_FAILED")
        self.assertEqual(result["notification_status"], "NOT_SENT_REALTIME_REMINDER_INTEGRITY_FAILED")

    def test_dws_attendance_collects_org_records_and_summaries_without_mock_data(self) -> None:
        runner = FakeDwsRunner()

        result = collect_org_attendance(
            work_date="2026-07-07",
            summary_datetime="2026-07-07 18:15:00",
            runner=runner,
        )

        self.assertTrue(result["dws_live"])
        self.assertFalse(result["uses_mock_data"])
        self.assertEqual(result["stats"]["member_count"], 3)
        self.assertEqual(result["stats"]["record_success_count"], 3)
        self.assertEqual(result["stats"]["summary_success_count"], 3)
        self.assertEqual(result["stats"]["record_nonempty_count"], 1)
        self.assertEqual(result["stats"]["known_no_record_count"], 2)
        self.assertEqual(result["stats"]["unexpected_empty_record_count"], 0)
        self.assertNotIn("--mock", json.dumps(runner.calls, ensure_ascii=False))

    def test_dws_department_and_member_listing_use_extended_timeout(self) -> None:
        runner = FakeDwsRunner()

        collect_org_attendance(
            work_date="2026-07-07",
            summary_datetime="2026-07-07 18:15:00",
            runner=runner,
        )

        timeout_by_call = dict(runner.timeouts)
        self.assertEqual(timeout_by_call[("contact", "dept", "list-children", "--dept", "1")], 120)
        self.assertEqual(timeout_by_call[("contact", "dept", "list-children", "--dept", "100")], 120)
        self.assertEqual(timeout_by_call[("contact", "dept", "list-members", "--depts", "1,100")], 120)
        self.assertEqual(
            timeout_by_call[("attendance", "record", "get", "--user", "li-dws-id", "--date", "2026-07-07")],
            60,
        )

    def test_dws_department_empty_failure_is_retried_before_failing_run(self) -> None:
        dept_one_calls = 0

        def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            nonlocal dept_one_calls
            if args == ["contact", "dept", "list-children", "--dept", "1"]:
                dept_one_calls += 1
                if dept_one_calls == 1:
                    return {"returncode": 4, "payload": {"success": False}}
                return {"returncode": 0, "payload": {"success": True, "result": [{"deptId": 100}]}}
            if args == ["contact", "dept", "list-children", "--dept", "100"]:
                return {"returncode": 0, "payload": {"success": True, "result": []}}
            if args == ["contact", "dept", "list-members", "--depts", "1,100"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "deptUserList": [{"userInfo": {"name": "李同林", "userId": "li-dws-id"}}],
                    },
                }
            if args[:4] == ["attendance", "record", "get", "--user"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "code": "0",
                        "result": {"recordList": [{"checkTypeDesc": "上班"}, {"checkTypeDesc": "下班"}]},
                    },
                }
            if args[:3] == ["attendance", "summary", "--user"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "code": "0",
                        "result": {"abnormalCount": 0, "items": []},
                    },
                }
            raise AssertionError(f"unexpected dws args: {args}")

        result = collect_org_attendance(
            work_date="2026-07-09",
            summary_datetime="2026-07-09 20:00:00",
            runner=runner,
        )

        self.assertEqual(dept_one_calls, 2)
        self.assertEqual(result["stats"]["command_failure_count"], 0)

    def test_run_dws_json_passes_effective_timeout_to_dws_cli(self) -> None:
        captured: dict[str, object] = {}

        class Proc:
            returncode = 0
            stdout = '{"success": true}'
            stderr = ""

        def fake_run(command: list[str], **kwargs: object) -> Proc:
            captured["command"] = command
            captured["timeout"] = kwargs["timeout"]
            captured["env"] = kwargs["env"]
            return Proc()

        with (
            patch("KMFA.tools.dingtalk_attendance.dws_attendance.dws_command_safety_status", return_value={"status": "READY"}),
            patch("KMFA.tools.dingtalk_attendance.dws_attendance.subprocess.run", side_effect=fake_run),
            patch.dict("os.environ", {"DWS_BIN": "/tmp/fake-dws", "KMFA_DINGTALK_ATTENDANCE_DWS_TIMEOUT_SECONDS": "120"}),
        ):
            result = run_dws_json(["contact", "dept", "list-members"], timeout=45)

        self.assertEqual(result["payload"], {"success": True})
        self.assertEqual(
            captured["command"],
            ["/tmp/fake-dws", "contact", "dept", "list-members", "--timeout", "120", "--format", "json"],
        )
        self.assertEqual(captured["timeout"], 125)
        self.assertEqual(captured["env"]["TZ"], "Asia/Shanghai")

    def test_run_dws_json_env_timeout_cannot_shrink_call_timeout(self) -> None:
        captured: dict[str, object] = {}

        class Proc:
            returncode = 0
            stdout = '{"success": true}'
            stderr = ""

        def fake_run(command: list[str], **kwargs: object) -> Proc:
            captured["command"] = command
            captured["timeout"] = kwargs["timeout"]
            return Proc()

        with (
            patch("KMFA.tools.dingtalk_attendance.dws_attendance.dws_command_safety_status", return_value={"status": "READY"}),
            patch("KMFA.tools.dingtalk_attendance.dws_attendance.subprocess.run", side_effect=fake_run),
            patch.dict("os.environ", {"DWS_BIN": "/tmp/fake-dws", "KMFA_DINGTALK_ATTENDANCE_DWS_TIMEOUT_SECONDS": "20"}),
        ):
            run_dws_json(["attendance", "record", "get"], timeout=60)

        self.assertIn("--timeout", captured["command"])
        self.assertEqual(captured["command"][captured["command"].index("--timeout") + 1], "60")
        self.assertEqual(captured["timeout"], 65)

    def test_department_discovery_retries_timeout_error_once(self) -> None:
        calls: list[tuple[tuple[str, ...], int, bool]] = []
        failed_once = False

        def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            nonlocal failed_once
            calls.append((tuple(args), timeout, verbose))
            if args == ["contact", "dept", "list-children", "--dept", "1"]:
                if not failed_once:
                    failed_once = True
                    return {
                        "returncode": 1,
                        "payload": {"error": {"code": "6"}, "reason": "timed out while listing departments"},
                    }
                return {"returncode": 0, "payload": {"success": True, "result": []}}
            if args == ["contact", "dept", "list-members", "--depts", "1"]:
                return {"returncode": 0, "payload": {"success": True, "deptUserList": []}}
            raise AssertionError(f"unexpected dws args: {args}")

        result = collect_org_attendance(
            work_date="2026-07-07",
            summary_datetime="2026-07-07 18:15:00",
            runner=runner,
        )

        department_calls = [call for call in calls if call[0] == ("contact", "dept", "list-children", "--dept", "1")]
        self.assertEqual(len(department_calls), 2)
        self.assertEqual(department_calls[0][1], 120)
        self.assertFalse(department_calls[0][2])
        self.assertTrue(department_calls[1][2])
        self.assertEqual(result["stats"]["member_count"], 0)

    def test_complete_collection_with_exempt_people_and_two_empty_records_notifies_two_real_anomalies(self) -> None:
        members = [
            {"name": "张霖泽", "userId": "u-zhang"},
            {"name": "林全意", "userId": "u-lin"},
            *[
                {"name": f"员工{index:02d}", "userId": f"u-{index:02d}"}
                for index in range(1, 43)
            ],
        ]

        def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            if args == ["contact", "dept", "list-children", "--dept", "1"]:
                return {"returncode": 0, "payload": {"success": True, "result": []}}
            if args == ["contact", "dept", "list-members", "--depts", "1"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "deptUserList": [{"userInfo": member} for member in members],
                    },
                }
            if args[:4] == ["attendance", "record", "get", "--user"]:
                user_id = args[4]
                is_has_schedule = True
                if user_id in {"u-zhang", "u-lin", "u-01", "u-02"}:
                    record_list = []
                elif user_id == "u-03":
                    is_has_schedule = False
                    record_list = []
                else:
                    record_list = [{"checkTypeDesc": "上班"}, {"checkTypeDesc": "下班"}]
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "code": "0",
                        "result": {"recordList": record_list, "isHasSchedule": is_has_schedule},
                    },
                }
            if args[:3] == ["attendance", "summary", "--user"]:
                user_id = args[3]
                if user_id in {"u-01", "u-02"}:
                    items = [
                        {
                            "id": "RealAttend_Y|Lack_Y",
                            "name": "缺卡",
                            "children": [{"name": "2026-07-07（星期二）08:00"}],
                        }
                    ]
                elif user_id in {"u-zhang", "u-lin", "u-03"}:
                    items = []
                else:
                    items = [
                        {
                            "id": "RealAttend_Y",
                            "name": "出勤天数",
                            "children": [{"name": "2026-07-07（星期二）", "values": ["1.0"]}],
                        }
                    ]
                return {
                    "returncode": 0,
                    "payload": {"success": True, "code": "0", "result": {"abnormalCount": 0, "items": items}},
                }
            raise AssertionError(f"unexpected dws args: {args}")

        collection = collect_org_attendance(
            work_date="2026-07-07",
            summary_datetime="2026-07-07 08:35:00",
            runner=runner,
        )
        context = notification_context_from_output_status(
            {
                "run_id": "dingtalk_attendance_morning_20260707_083500",
                "run_type": "morning",
                "work_date": "2026-07-07",
                "current_time": "08:35",
                "stats": collection["stats"],
            }
        )
        body = build_notification_message(**context, markdown=False)

        self.assertEqual(collection["stats"]["member_count"], 44)
        self.assertEqual(collection["stats"]["record_success_count"], 44)
        self.assertEqual(collection["stats"]["summary_success_count"], 44)
        self.assertEqual(collection["stats"]["command_failure_count"], 0)
        self.assertEqual(collection["stats"]["known_no_record_names"], ["张霖泽", "林全意"])
        self.assertEqual(collection["stats"]["attendance_required_count"], 41)
        self.assertEqual(collection["stats"]["summary_today_present_count"], 41)
        self.assertEqual(collection["stats"]["unexpected_empty_record_names"], ["员工01", "员工02"])
        self.assertEqual(collection["stats"]["incomplete_record_names"], [])
        self.assertEqual(collection["stats"]["summary_today_anomaly_names"], ["员工01", "员工02"])
        self.assertEqual(collection["stats"]["attendance_anomaly_names"], ["员工01", "员工02"])
        self.assertIn("今日异常 / 无考勤\n员工01（本月累计1次）\n员工02（本月累计1次）", body)
        self.assertNotIn("今日异常人员 / 无考勤人员：张霖泽", body)
        self.assertNotIn("林全意。", body)
        self.assertNotIn("今天一切良好", body)

    def test_summary_backed_agent_code_missing_is_detail_unavailable_not_command_failure(self) -> None:
        def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            if args == ["contact", "dept", "list-children", "--dept", "1"]:
                return {"returncode": 0, "payload": {"success": True, "result": []}}
            if args == ["contact", "dept", "list-members", "--depts", "1"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "deptUserList": [{"userInfo": {"name": "吴云霞", "userId": "u-wu"}}],
                    },
                }
            if args[:4] == ["attendance", "record", "get", "--user"]:
                return {"returncode": 4, "payload": {"success": False, "code": "AGENT_CODE_NOT_EXISTS", "data": None}}
            if args[:3] == ["attendance", "summary", "--user"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "code": "0",
                        "result": {
                            "abnormalCount": 0,
                            "items": [
                                {
                                    "id": "RealAttend_Y",
                                    "name": "出勤天数",
                                    "children": [{"name": "2026-07-09（星期四）", "values": ["1.0"]}],
                                }
                            ],
                        },
                    },
                }
            raise AssertionError(f"unexpected dws args: {args}")

        collection = collect_org_attendance(
            work_date="2026-07-09",
            summary_datetime="2026-07-09 10:35:00",
            runner=runner,
        )

        self.assertEqual(collection["stats"]["record_success_count"], 1)
        self.assertEqual(collection["stats"]["record_failure_count"], 0)
        self.assertEqual(collection["stats"]["command_failure_count"], 0)
        self.assertEqual(collection["stats"]["record_detail_unavailable_count"], 1)
        self.assertEqual(collection["stats"]["record_detail_unavailable_names"], ["吴云霞"])
        self.assertEqual(collection["stats"]["attendance_required_count"], 1)
        self.assertEqual(collection["stats"]["attendance_anomaly_count"], 0)

    def test_known_no_record_summary_agent_code_missing_is_not_command_failure(self) -> None:
        def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            if args == ["contact", "dept", "list-children", "--dept", "1"]:
                return {"returncode": 0, "payload": {"success": True, "result": []}}
            if args == ["contact", "dept", "list-members", "--depts", "1"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "deptUserList": [{"userInfo": {"name": "张霖泽", "userId": "u-test"}}],
                    },
                }
            if args[:4] == ["attendance", "record", "get", "--user"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "code": "0",
                        "result": {"recordList": [], "isHasSchedule": True},
                    },
                }
            if args[:3] == ["attendance", "summary", "--user"]:
                return {"returncode": 4, "payload": {"success": False, "code": "AGENT_CODE_NOT_EXISTS", "data": None}}
            raise AssertionError(f"unexpected dws args: {args}")

        collection = collect_org_attendance(
            work_date="2026-07-09",
            summary_datetime="2026-07-09 20:00:00",
            runner=runner,
        )

        self.assertEqual(collection["stats"]["record_success_count"], 1)
        self.assertEqual(collection["stats"]["summary_success_count"], 1)
        self.assertEqual(collection["stats"]["summary_failure_count"], 0)
        self.assertEqual(collection["stats"]["command_failure_count"], 0)
        self.assertEqual(collection["stats"]["known_no_record_names"], ["张霖泽"])
        self.assertEqual(collection["stats"]["summary_not_applicable_count"], 1)
        self.assertEqual(collection["stats"]["summary_not_applicable_names"], ["张霖泽"])
        self.assertEqual(collection["stats"]["attendance_required_count"], 0)
        self.assertEqual(collection["stats"]["attendance_anomaly_count"], 0)

    def test_full_record_summary_agent_code_missing_is_detail_unavailable_not_command_failure(self) -> None:
        def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            if args == ["contact", "dept", "list-children", "--dept", "1"]:
                return {"returncode": 0, "payload": {"success": True, "result": []}}
            if args == ["contact", "dept", "list-members", "--depts", "1"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "deptUserList": [{"userInfo": {"name": "周稳", "userId": "u-zhou"}}],
                    },
                }
            if args[:4] == ["attendance", "record", "get", "--user"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "code": "0",
                        "result": {
                            "recordList": [{"checkTypeDesc": "上班"}, {"checkTypeDesc": "下班"}],
                            "isHasSchedule": True,
                        },
                    },
                }
            if args[:3] == ["attendance", "summary", "--user"]:
                return {"returncode": 4, "payload": {"success": False, "code": "AGENT_CODE_NOT_EXISTS", "data": None}}
            raise AssertionError(f"unexpected dws args: {args}")

        collection = collect_org_attendance(
            work_date="2026-07-09",
            summary_datetime="2026-07-09 20:00:00",
            runner=runner,
        )

        self.assertEqual(collection["stats"]["record_success_count"], 1)
        self.assertEqual(collection["stats"]["summary_success_count"], 1)
        self.assertEqual(collection["stats"]["summary_failure_count"], 0)
        self.assertEqual(collection["stats"]["command_failure_count"], 0)
        self.assertEqual(collection["stats"]["summary_detail_unavailable_count"], 1)
        self.assertEqual(collection["stats"]["summary_detail_unavailable_names"], ["周稳"])
        self.assertEqual(collection["stats"]["attendance_required_count"], 1)
        self.assertEqual(collection["stats"]["attendance_anomaly_count"], 0)

    def test_scheduled_partial_record_counts_as_attendance_anomaly(self) -> None:
        def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            if args == ["contact", "dept", "list-children", "--dept", "1"]:
                return {"returncode": 0, "payload": {"success": True, "result": []}}
            if args == ["contact", "dept", "list-members", "--depts", "1"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "deptUserList": [{"userInfo": {"name": "员工A", "userId": "u-a"}}],
                    },
                }
            if args[:4] == ["attendance", "record", "get", "--user"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "code": "0",
                        "result": {
                            "recordList": [{"checkTypeDesc": "上班"}],
                            "isHasSchedule": True,
                        },
                    },
                }
            if args[:3] == ["attendance", "summary", "--user"]:
                return {
                    "returncode": 0,
                    "payload": {"success": True, "code": "0", "result": {"abnormalCount": 0, "items": []}},
                }
            raise AssertionError(f"unexpected dws args: {args}")

        collection = collect_org_attendance(
            work_date="2026-07-07",
            summary_datetime="2026-07-07 08:35:00",
            runner=runner,
        )
        context = notification_context_from_output_status(
            {
                "run_id": "dingtalk_attendance_morning_20260707_083500",
                "run_type": "morning",
                "work_date": "2026-07-07",
                "current_time": "08:35",
                "stats": {**collection["stats"], **_official_pass_stats(member_count=1)},
            }
        )
        body = build_notification_message(**context, markdown=False)

        self.assertEqual(collection["stats"]["attendance_required_count"], 1)
        self.assertEqual(collection["stats"]["incomplete_record_names"], ["员工A"])
        self.assertEqual(collection["stats"]["attendance_anomaly_names"], ["员工A"])
        self.assertIn("本次1人全部考勤正常", body)
        self.assertNotIn("今日异常 / 无考勤", body)
        self.assertNotIn("员工A", body)

    def test_today_summary_lack_counts_as_anomaly_even_when_record_has_full_day(self) -> None:
        def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            if args == ["contact", "dept", "list-children", "--dept", "1"]:
                return {"returncode": 0, "payload": {"success": True, "result": []}}
            if args == ["contact", "dept", "list-members", "--depts", "1"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "deptUserList": [{"userInfo": {"name": "员工B", "userId": "u-b"}}],
                    },
                }
            if args[:4] == ["attendance", "record", "get", "--user"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "code": "0",
                        "result": {
                            "recordList": [{"checkTypeDesc": "上班"}, {"checkTypeDesc": "下班"}],
                            "isHasSchedule": False,
                        },
                    },
                }
            if args[:3] == ["attendance", "summary", "--user"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "code": "0",
                        "result": {
                            "abnormalCount": 1,
                            "items": [
                                {
                                    "id": "RealAttend_Y|Lack_Y",
                                    "name": "缺卡",
                                    "children": [{"name": "2026-07-07（星期二）08:00"}],
                                }
                            ],
                        },
                    },
                }
            raise AssertionError(f"unexpected dws args: {args}")

        collection = collect_org_attendance(
            work_date="2026-07-07",
            summary_datetime="2026-07-07 08:35:00",
            runner=runner,
        )
        context = notification_context_from_output_status(
            {
                "run_id": "dingtalk_attendance_morning_20260707_083500",
                "run_type": "morning",
                "work_date": "2026-07-07",
                "current_time": "08:35",
                "stats": collection["stats"],
            }
        )
        body = build_notification_message(**context, markdown=False)

        self.assertEqual(collection["stats"]["attendance_required_count"], 1)
        self.assertEqual(collection["stats"]["summary_today_anomaly_names"], ["员工B"])
        self.assertEqual(collection["stats"]["attendance_anomaly_names"], ["员工B"])
        self.assertIn("今日异常 / 无考勤\n员工B（本月累计1次）", body)
        self.assertNotIn("今天一切良好", body)

    def test_today_summary_absence_status_tokens_all_count_as_today_anomaly(self) -> None:
        for status_name in ("缺卡", "未打卡", "旷工", "迟到", "早退"):
            with self.subTest(status_name=status_name):
                def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
                    if args == ["contact", "dept", "list-children", "--dept", "1"]:
                        return {"returncode": 0, "payload": {"success": True, "result": []}}
                    if args == ["contact", "dept", "list-members", "--depts", "1"]:
                        return {
                            "returncode": 0,
                            "payload": {
                                "success": True,
                                "deptUserList": [{"userInfo": {"name": "员工C", "userId": "u-c"}}],
                            },
                        }
                    if args[:4] == ["attendance", "record", "get", "--user"]:
                        return {
                            "returncode": 0,
                            "payload": {
                                "success": True,
                                "code": "0",
                                "result": {
                                    "recordList": [{"checkTypeDesc": "上班"}, {"checkTypeDesc": "下班"}],
                                    "isHasSchedule": True,
                                },
                            },
                        }
                    if args[:3] == ["attendance", "summary", "--user"]:
                        return {
                            "returncode": 0,
                            "payload": {
                                "success": True,
                                "code": "0",
                                "result": {
                                    "abnormalCount": 1,
                                    "items": [
                                        {
                                            "id": status_name,
                                            "name": status_name,
                                            "children": [{"name": "2026-07-07（星期二）"}],
                                        }
                                    ],
                                },
                            },
                        }
                    raise AssertionError(f"unexpected dws args: {args}")

                collection = collect_org_attendance(
                    work_date="2026-07-07",
                    summary_datetime="2026-07-07 10:35:00",
                    runner=runner,
                )
                context = notification_context_from_output_status(
                    {
                        "run_id": "dingtalk_attendance_morning_20260707_103500",
                        "run_type": "morning",
                        "work_date": "2026-07-07",
                        "current_time": "10:35",
                        "stats": collection["stats"],
                    }
                )
                body = build_notification_message(**context, markdown=False)

                self.assertEqual(collection["stats"]["summary_today_anomaly_names"], ["员工C"])
                self.assertIn("今日异常 / 无考勤\n员工C（本月累计1次）", body)

    def test_dws_attendance_fails_fast_on_pat_scope_auth_required(self) -> None:
        calls: list[tuple[str, ...]] = []

        def runner(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
            calls.append(tuple(args))
            if args == ["contact", "dept", "list-children", "--dept", "1"]:
                return {"returncode": 0, "payload": {"success": True, "result": []}}
            if args == ["contact", "dept", "list-members", "--depts", "1"]:
                return {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "deptUserList": [{"userInfo": {"name": "李同林", "userId": "li-dws-id"}}],
                    },
                }
            if args[:4] == ["attendance", "record", "get", "--user"]:
                return {
                    "returncode": 4,
                    "payload": {
                        "raw": (
                            '{"success":false,"code":"PAT_MEDIUM_RISK_NO_PERMISSION",'
                            '"data":{"openBrowser":true,'
                            '"requiredScopes":[{"scope":"attendance.record:get"}]}}'
                        )
                    },
                }
            raise AssertionError(f"unexpected dws args: {args}")

        with self.assertRaisesRegex(DwsAttendanceError, "DWS_PAT_SCOPE_AUTH_REQUIRED"):
            collect_org_attendance(
                work_date="2026-07-07",
                summary_datetime="2026-07-07 08:35:00",
                runner=runner,
            )

        self.assertFalse(any(call[:2] == ("attendance", "summary") for call in calls))

    def test_private_reports_never_display_hidden_no_record_people(self) -> None:
        collection = collect_org_attendance(
            work_date="2026-07-07",
            summary_datetime="2026-07-07 08:35:00",
            runner=FakeDwsRunner(),
        )

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            plan = {
                "run_id": "dingtalk_attendance_morning_20260707_083500",
                "skill_id": "kmfa-dingtalk-attendance-skill",
                "run_type": "morning",
                "archive_paths": {
                    "month_dir": str(base),
                    "raw_jsonl_gz": str(base / "raw.jsonl.gz"),
                    "management_report": str(base / "management.md"),
                    "hr_report": str(base / "hr.md"),
                    "dispatch_receipt": str(base / "dispatch.json"),
                    "archive_manifest": str(base / "manifest.json"),
                    "cleanup_audit": str(base / "cleanup.json"),
                },
                "public_repo_safety": {"no_sensitive_git": True},
            }

            output = write_private_outputs(plan=plan, collection=collection, cleanup_status={"status": "SKIPPED"})
            management = Path(output["management_report"]).read_text(encoding="utf-8")
            hr = Path(output["hr_report"]).read_text(encoding="utf-8")
            manifest = json.loads(Path(output["archive_manifest"]).read_text(encoding="utf-8"))

        for report in (management, hr):
            self.assertNotIn("张霖泽", report)
            self.assertNotIn("林全意", report)
            self.assertNotIn("morning", report)
            self.assertNotIn("evening", report)
        self.assertIn("# 开明考勤管理报告｜2026-07-07｜晨间暂时提醒", management)
        self.assertIn("# 开明考勤 HR 报告｜2026-07-07｜晨间暂时提醒", hr)
        self.assertIn("今日异常人员 / 无考勤人员：无。", management)
        self.assertIn("无考勤记录人员：无。", management)
        self.assertIn("打卡记录不完整人员：无。", management)
        self.assertIn("今日异常人员 / 无考勤人员：无。", hr)
        self.assertNotIn("待审批/待补卡/待核查", hr)
        self.assertEqual(manifest["stats"]["known_no_record_names"], ["张霖泽", "林全意"])

    def test_private_reports_keep_backend_collection_diagnostics_out_of_user_text(self) -> None:
        collection = collect_org_attendance(
            work_date="2026-07-07",
            summary_datetime="2026-07-07 08:35:00",
            runner=FakeDwsRunner(fail_first_record_for="li-dws-id"),
        )
        collection["stats"]["record_failure_count"] = 1
        collection["stats"]["command_failure_count"] = 1
        collection["stats"]["record_success_count"] = collection["stats"]["member_count"] - 1

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            plan = {
                "run_id": "dingtalk_attendance_morning_20260707_083500",
                "skill_id": "kmfa-dingtalk-attendance-skill",
                "run_type": "morning",
                "archive_paths": {
                    "month_dir": str(base),
                    "raw_jsonl_gz": str(base / "raw.jsonl.gz"),
                    "management_report": str(base / "management.md"),
                    "hr_report": str(base / "hr.md"),
                    "dispatch_receipt": str(base / "dispatch.json"),
                    "archive_manifest": str(base / "manifest.json"),
                    "cleanup_audit": str(base / "cleanup.json"),
                },
                "public_repo_safety": {"no_sensitive_git": True},
            }

            output = write_private_outputs(plan=plan, collection=collection, cleanup_status={"status": "SKIPPED"})
            report_text = (
                Path(output["management_report"]).read_text(encoding="utf-8")
                + "\n"
                + Path(output["hr_report"]).read_text(encoding="utf-8")
            )
            manifest = json.loads(Path(output["archive_manifest"]).read_text(encoding="utf-8"))

        for backend_text in (
            "DWS",
            "record",
            "summary",
            "command_failure",
            "接口局部失败",
            "权限",
            "命令失败",
            "mock",
            "attendance.record:get",
        ):
            self.assertNotIn(backend_text, report_text)
        self.assertEqual(manifest["stats"]["record_failure_count"], 1)
        self.assertEqual(manifest["stats"]["command_failure_count"], 1)

    def test_official_reports_expose_only_official_totals_and_preserve_raw_evidence_privately(self) -> None:
        collection = collect_official_org_attendance(
            work_date="2026-07-11",
            summary_datetime="2026-07-11 10:35:00",
            runner=OfficialParityFixtureRunner(),
        )

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            plan = {
                "run_id": "dingtalk_attendance_morning_20260711_103500",
                "skill_id": "kmfa-dingtalk-attendance-skill",
                "run_type": "morning",
                "archive_paths": {
                    "month_dir": str(base),
                    "raw_jsonl_gz": str(base / "raw.jsonl.gz"),
                    "management_report": str(base / "management.md"),
                    "hr_report": str(base / "hr.md"),
                    "dispatch_receipt": str(base / "dispatch.json"),
                    "archive_manifest": str(base / "manifest.json"),
                    "cleanup_audit": str(base / "cleanup.json"),
                },
                "public_repo_safety": {"no_sensitive_git": True},
            }

            output = write_private_outputs(plan=plan, collection=collection, cleanup_status={"status": "SKIPPED"})
            report_text = (
                Path(output["management_report"]).read_text(encoding="utf-8")
                + "\n"
                + Path(output["hr_report"]).read_text(encoding="utf-8")
            )
            with gzip.open(output["raw_jsonl_gz"], "rt", encoding="utf-8") as handle:
                raw_rows = [json.loads(line) for line in handle if line.strip()]

        self.assertIn("官方报表覆盖 2 人", report_text)
        self.assertIn("应考勤 2 人", report_text)
        self.assertIn("有效出勤 1 人", report_text)
        self.assertNotIn("当天有打卡记录", report_text)
        self.assertNotIn("无考勤记录人员", report_text)
        self.assertNotIn("打卡记录不完整人员", report_text)
        self.assertTrue(any(row.get("type") == "official_report_evidence" for row in raw_rows))

    def test_dws_attendance_retries_transient_attendance_error_once(self) -> None:
        runner = FakeDwsRunner(fail_first_record_for="li-dws-id")

        result = collect_org_attendance(
            work_date="2026-07-07",
            summary_datetime="2026-07-07 18:15:00",
            runner=runner,
        )

        li_record_calls = [
            call
            for call in runner.calls
            if call[0] == ("attendance", "record", "get", "--user", "li-dws-id", "--date", "2026-07-07")
        ]
        self.assertEqual(len(li_record_calls), 2)
        self.assertTrue(li_record_calls[1][1])
        self.assertEqual(result["stats"]["record_success_count"], 3)

    def test_group_robot_sender_signs_markdown_and_injects_required_keyword(self) -> None:
        captured: dict[str, object] = {}

        class FakeResponse:
            status = 200

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def read(self) -> bytes:
                return b'{"errcode":0,"errmsg":"ok"}'

        def fake_urlopen(request: object, timeout: int = 0) -> FakeResponse:
            captured["url"] = request.full_url
            captured["body"] = request.data.decode("utf-8")
            captured["timeout"] = timeout
            return FakeResponse()

        env = {
            "DINGTALK_ROBOT_URL": "https://example.invalid/robot/send?token=masked",
            "DINGTALK_ROBOT_SIGNING_KEY": "local-signing-key",
        }
        expected_url = build_signed_robot_url(
            robot_url=env["DINGTALK_ROBOT_URL"],
            signing_key=env["DINGTALK_ROBOT_SIGNING_KEY"],
            timestamp_ms=1234567890,
        )

        result = send_group_robot_markdown(
            title="管理报告",
            markdown_text="## 一、总体情况\n已生成。",
            env=env,
            timestamp_ms=1234567890,
            urlopen=fake_urlopen,
        )

        parsed_query = parse_qs(urlparse(str(captured["url"])).query)
        expected_query = parse_qs(urlparse(expected_url).query)
        self.assertEqual(result["status"], "SENT")
        self.assertEqual(parsed_query["timestamp"], ["1234567890"])
        self.assertEqual(parsed_query["sign"], expected_query["sign"])
        self.assertIn("开明考勤", str(captured["body"]))
        self.assertNotIn(env["DINGTALK_ROBOT_SIGNING_KEY"], json.dumps(result, ensure_ascii=False))

    def test_dispatch_reports_to_robot_reads_private_reports_and_writes_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            management = root / "run.management.md"
            hr = root / "run.hr.md"
            receipt = root / "run.dispatch.json"
            management.write_text("# 开明考勤管理报告\n\n## 一、总体情况\n完成。\n", encoding="utf-8")
            hr.write_text("# 开明考勤 HR 报告\n\n## 一、异常明细\n无。\n", encoding="utf-8")

            sent_titles: list[str] = []
            sent_bodies: list[str] = []

            def fake_sender(*, title: str, markdown_text: str, env: dict[str, str]) -> dict[str, object]:
                sent_titles.append(title)
                sent_bodies.append(markdown_text)
                self.assertIn("开明考勤", markdown_text)
                return {"status": "SENT", "channel": "dingtalk_group_robot", "http_status": 200}

            result = dispatch_reports_to_robot(
                output_status={
                    "run_id": "dingtalk_attendance_evening_20260707_181500",
                    "run_type": "evening",
                    "work_date": "2026-07-07",
                    "current_time": "18:15",
                    "stats": {
                        **_official_pass_stats(anomaly_names=["张三"]),
                        "unexpected_empty_record_names": ["张三"],
                        "known_no_record_names": ["张霖泽"],
                    },
                    "management_report": str(management),
                    "hr_report": str(hr),
                    "dispatch_receipt": str(receipt),
                },
                env={
                    "DINGTALK_NOTIFY_MODE": "dingtalk_group_robot",
                    "DINGTALK_ROBOT_URL": "https://example.invalid/robot/send?token=masked",
                    "DINGTALK_ROBOT_SIGNING_KEY": "local-signing-key",
                },
                sender=fake_sender,
            )

            receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(result["notification_status"], "SENT")
            self.assertEqual(receipt_payload["notification_status"], "SENT")
            self.assertEqual(sent_titles, ["开明考勤提醒"])
            self.assertEqual(len(receipt_payload["messages"]), 1)
            self.assertEqual(receipt_payload["notification_template_text"], sent_bodies[0])
            self.assertEqual(receipt_payload["notification_delivery_table"], "| 发送对象 | 是否成功 |\n|---|---|\n| 钉钉群机器人 | 是 |")
            self.assertIn("开明考勤提醒｜2026-07-07｜晚间暂时提醒", sent_bodies[0])
            self.assertNotIn("evening", sent_bodies[0])
            self.assertNotIn("morning", sent_bodies[0])
            self.assertIn("截止 18:15", sent_bodies[0])
            self.assertIn("## 今日异常 / 无考勤\n张三（本月累计1次）", sent_bodies[0])
            self.assertNotIn("张霖泽", sent_bodies[0])
            self.assertNotIn("林全意", sent_bodies[0])
            self.assertNotIn("## 一、总体情况", sent_bodies[0])
            self.assertNotIn("## 一、异常明细", sent_bodies[0])
            self.assertEqual(receipt_payload["messages"][0]["report"], "combined_attendance_notification")

    def test_notification_template_hides_empty_sections_and_shows_all_clear(self) -> None:
        message = build_notification_message(
            work_date="2026-07-07",
            run_type="morning",
            current_time="08:35",
            unexpected_empty_record_names=[],
            known_no_record_names=[],
            consecutive_anomaly_summary=[],
            pending_hr_actions=[],
            member_count=41,
        )

        self.assertEqual(
            message,
            "# 开明考勤提醒｜2026-07-07｜晨间暂时提醒\n\n截止 08:35\n\n本次41人全部考勤正常\n",
        )
        self.assertNotIn("morning", message)
        self.assertNotIn("evening", message)
        self.assertNotIn("今日异常人员", message)
        self.assertNotIn("连续异常人员", message)
        self.assertNotIn("待审批/待补卡/待核查", message)

    def test_notification_context_all_clear_uses_member_count_phrase(self) -> None:
        context = notification_context_from_output_status(
            {
                "run_id": "dingtalk_attendance_morning_20260707_083500",
                "run_type": "morning",
                "work_date": "2026-07-07",
                "current_time": "08:35",
                "stats": {
                    **_official_pass_stats(member_count=41),
                    "record_success_count": 41,
                    "summary_success_count": 41,
                    "record_failure_count": 0,
                    "summary_failure_count": 0,
                    "command_failure_count": 0,
                    "attendance_anomaly_names": [],
                    "rest_required_people": [],
                },
            }
        )
        body = build_notification_message(**context, markdown=False)

        self.assertIn("本次41人全部考勤正常", body)
        self.assertNotIn("今天一切良好", body)

    def test_notification_template_renders_monthly_cumulative_sections_and_top10(self) -> None:
        names = [f"员工{i:02d}" for i in range(1, 12)]
        monthly_items = [
            {"name": name, "monthly_count": index, "latest_date": f"2026-07-{index:02d}"}
            for index, name in enumerate(names, start=1)
        ]
        context = notification_context_from_output_status(
            {
                "run_id": "dingtalk_attendance_evening_20260711_181500",
                "run_type": "evening",
                "work_date": "2026-07-11",
                "current_time": "18:15",
                "stats": {
                    "member_count": 41,
                    "attendance_anomaly_names": names,
                    "monthly_attendance_anomalies": monthly_items,
                    "monthly_consecutive_anomalies": [
                        {
                            "name": "员工11",
                            "monthly_count": 11,
                            "consecutive_days": 3,
                            "latest_date": "2026-07-11",
                        }
                    ],
                    "monthly_pending_actions": [
                        {"name": "员工10", "monthly_count": 4, "latest_date": "2026-07-11"}
                    ],
                    "rest_required_people": [
                        {"name": "员工09", "effective_attendance_days": 25, "latest_date": "2026-07-11"}
                    ],
                },
            }
        )

        markdown = build_notification_message(**context, markdown=True)
        plain = build_notification_message(**context, markdown=False)

        self.assertIn("## 今日异常 / 无考勤\n共 11 人，本月累计 Top10:", markdown)
        self.assertIn("1. 员工11（本月累计11次）", markdown)
        self.assertIn("10. 员工02（本月累计2次）", markdown)
        self.assertNotIn("员工01（本月累计1次）", markdown)
        self.assertIn("## 连续异常\n员工11（连续3天，本月累计11次）", markdown)
        self.assertNotIn("待审批 / 待补卡 / 待核查", markdown)
        self.assertNotIn("员工10（本月累计4项）", markdown)
        self.assertIn("## 需要休息\n员工09（本月有效考勤25天）", markdown)
        self.assertNotIn("今日异常人员 / 无考勤人员：", markdown)
        self.assertNotIn("今天一切良好", markdown)
        self.assertNotIn("#", plain)
        self.assertIn("今日异常 / 无考勤\n共 11 人，本月累计 Top10:", plain)

    def test_notification_template_does_not_render_historical_monthly_anomalies_as_today(self) -> None:
        message = build_notification_message(
            work_date="2026-07-08",
            run_type="morning",
            current_time="08:50",
            unexpected_empty_record_names=[],
            known_no_record_names=[],
            monthly_attendance_anomalies=[
                {"name": "历史异常甲", "monthly_count": 3, "latest_date": "2026-07-03"},
                {"name": "历史异常乙", "monthly_count": 1, "latest_date": "2026-07-01"},
            ],
            member_count=44,
            markdown=True,
        )

        self.assertIn("本次44人全部考勤正常", message)
        self.assertNotIn("历史异常甲", message)
        self.assertNotIn("## 今日异常 / 无考勤", message)

    def test_notification_template_ignores_pending_section_and_omits_empty_sections_when_other_sections_have_content(self) -> None:
        message = build_notification_message(
            work_date="2026-07-08",
            run_type="morning",
            current_time="08:50",
            unexpected_empty_record_names=[],
            known_no_record_names=[],
            consecutive_anomaly_summary=[],
            pending_hr_actions=["王五待补卡"],
            monthly_pending_actions=[{"name": "王五", "monthly_count": 3, "latest_date": "2026-07-08"}],
            rest_required_people=[{"name": "赵六", "effective_attendance_days": 24, "latest_date": "2026-07-08"}],
            markdown=True,
        )

        self.assertIn("## 需要休息\n赵六（本月有效考勤24天）", message)
        self.assertNotIn("待审批 / 待补卡 / 待核查", message)
        self.assertNotIn("王五", message)
        self.assertNotIn("## 今日异常 / 无考勤", message)
        self.assertNotIn("## 连续异常", message)

    def test_monthly_rollups_count_current_month_and_rest_from_23rd_effective_day(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            month_dir = Path(tmpdir)
            for day in range(1, 24):
                run_id = f"dingtalk_attendance_final_202607{day:02d}_181500"
                work_date = f"2026-07-{day:02d}"
                raw_path = month_dir / f"{run_id}.raw.jsonl.gz"
                with gzip.open(raw_path, "wt", encoding="utf-8") as handle:
                    handle.write(
                        json.dumps(
                            {"type": "metadata", "run_plan": {"run_id": run_id}},
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    employees = [("张三", "u1"), ("丁春法", "u3"), ("李永占", "u4")]
                    if day in (1, 23):
                        employees.append(("李四", "u2"))
                    for name, user_id in employees:
                        is_anomaly = name == "李四" or (day == 23 and name in {"丁春法", "李永占"})
                        handle.write(
                            json.dumps(
                                {
                                    "type": "employee_attendance",
                                    "member": {"name": name, "userId": user_id},
                                    "work_date": work_date,
                                    "record_list": (
                                        []
                                        if name == "李四"
                                        else [{"checkTypeDesc": "上班"}, {"checkTypeDesc": "下班"}]
                                    ),
                                    "derived": {
                                        "record_success": True,
                                        "summary_success": True,
                                        "record_anomaly": is_anomaly,
                                    },
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
                _write_certificate_bound_final_manifest(
                    month_dir,
                    run_id=run_id,
                    work_date=work_date,
                    people=len(employees),
                )

            stats = build_stats_with_rest_required_people(
                {"member_count": 4, "attendance_anomaly_names": ["李四", "丁春法", "李永占"]},
                month_dir=month_dir,
                work_date="2026-07-23",
            )

            self.assertEqual(stats["rest_required_people"], [{"name": "张三", "effective_attendance_days": 23, "latest_date": "2026-07-23"}])
            self.assertEqual(
                stats["monthly_attendance_anomalies"],
                [
                    {"name": "李四", "monthly_count": 2, "latest_date": "2026-07-23"},
                    {"name": "丁春法", "monthly_count": 1, "latest_date": "2026-07-23"},
                    {"name": "李永占", "monthly_count": 1, "latest_date": "2026-07-23"},
                ],
            )

    def test_rest_exempt_people_are_only_removed_from_rest_required_section(self) -> None:
        markdown = build_notification_message(
            work_date="2026-07-23",
            run_type="evening",
            current_time="18:15",
            unexpected_empty_record_names=["丁春法", "李永占"],
            known_no_record_names=[],
            monthly_attendance_anomalies=[
                {"name": "丁春法", "monthly_count": 1, "latest_date": "2026-07-23"},
                {"name": "李永占", "monthly_count": 1, "latest_date": "2026-07-23"},
            ],
            monthly_pending_actions=[
                {"name": "丁春法", "monthly_count": 2, "latest_date": "2026-07-23"},
            ],
            rest_required_people=[
                {"name": "张三", "effective_attendance_days": 23, "latest_date": "2026-07-23"},
                {"name": "丁春法", "effective_attendance_days": 23, "latest_date": "2026-07-23"},
                {"name": "李永占", "effective_attendance_days": 23, "latest_date": "2026-07-23"},
            ],
            markdown=True,
        )

        self.assertIn("## 今日异常 / 无考勤\n丁春法（本月累计1次）\n李永占（本月累计1次）", markdown)
        self.assertNotIn("待审批 / 待补卡 / 待核查", markdown)
        self.assertNotIn("丁春法（本月累计2项）", markdown)
        self.assertIn("## 需要休息\n张三（本月有效考勤23天）", markdown)
        self.assertNotIn("丁春法（本月有效考勤23天）", markdown)
        self.assertNotIn("李永占（本月有效考勤23天）", markdown)

    def test_notification_template_uses_chinese_fallback_for_unknown_run_type(self) -> None:
        message = build_notification_message(
            work_date="2026-07-07",
            run_type="unknown",
            current_time="08:35",
            unexpected_empty_record_names=[],
            known_no_record_names=[],
            markdown=False,
        )

        self.assertIn("开明考勤提醒｜2026-07-07｜未知报次", message)
        self.assertNotIn("unknown", message)

    def test_notification_template_keeps_group_and_personal_content_consistent(self) -> None:
        markdown = build_notification_message(
            work_date="2026-07-07",
            run_type="evening",
            current_time="18:15",
            unexpected_empty_record_names=["张三"],
            known_no_record_names=[],
            consecutive_anomaly_summary=["李四连续 2 天异常"],
            pending_hr_actions=["王五待补卡"],
            markdown=True,
        )
        plain = build_personal_notification_message(
            work_date="2026-07-07",
            run_type="evening",
            current_time="18:15",
            unexpected_empty_record_names=["张三"],
            known_no_record_names=[],
            consecutive_anomaly_summary=["李四连续 2 天异常"],
            pending_hr_actions=["王五待补卡"],
            markdown=False,
        )

        self.assertEqual(markdown.replace("# ", "", 1).replace("## ", ""), plain)
        self.assertIn("今日异常 / 无考勤\n张三（本月累计1次）", plain)
        self.assertIn("连续异常\n李四连续 2 天异常", plain)
        self.assertNotIn("待审批 / 待补卡 / 待核查", plain)
        self.assertNotIn("王五待补卡", plain)

    def test_attendance_notification_template_shows_rest_required_people(self) -> None:
        markdown = build_notification_message(
            work_date="2026-07-27",
            run_type="evening",
            current_time="18:15",
            unexpected_empty_record_names=[],
            known_no_record_names=[],
            consecutive_anomaly_summary=[],
            pending_hr_actions=[],
            rest_required_people=[
                {"name": "张三", "effective_attendance_days": 25},
                {"name": "李四", "effective_attendance_days": 28},
            ],
            markdown=True,
        )
        plain = build_personal_notification_message(
            work_date="2026-07-27",
            run_type="evening",
            current_time="18:15",
            unexpected_empty_record_names=[],
            known_no_record_names=[],
            consecutive_anomaly_summary=[],
            pending_hr_actions=[],
            rest_required_people=[
                {"name": "张三", "effective_attendance_days": 25},
                {"name": "李四", "effective_attendance_days": 28},
            ],
            markdown=False,
        )

        self.assertEqual(markdown.replace("# ", "", 1).replace("## ", ""), plain)
        self.assertIn("## 需要休息\n李四（本月有效考勤28天）\n张三（本月有效考勤25天）", markdown)
        self.assertNotIn("今天一切良好", markdown)

    def test_notification_context_uses_real_anomaly_names_without_exempt_people(self) -> None:
        context = notification_context_from_output_status(
            {
                "run_id": "dingtalk_attendance_morning_20260707_083500",
                "run_type": "morning",
                "work_date": "2026-07-07",
                "current_time": "08:35",
                "stats": {
                    "attendance_anomaly_names": ["张三", "李四"],
                    "summary_today_anomaly_names": ["张三", "李四"],
                    "unexpected_empty_record_names": ["张霖泽", "林全意"],
                    "known_no_record_names": ["张霖泽", "林全意"],
                },
            }
        )
        body = build_notification_message(**context, markdown=False)

        self.assertIn("今日异常 / 无考勤\n张三（本月累计1次）\n李四（本月累计1次）", body)
        self.assertNotIn("张霖泽", body)
        self.assertNotIn("林全意", body)

    def test_notification_context_excludes_morning_incomplete_records_from_today_sections(self) -> None:
        context = notification_context_from_output_status(
            {
                "run_id": "dingtalk_attendance_morning_20260708_083500",
                "run_type": "morning",
                "work_date": "2026-07-08",
                "current_time": "08:35",
                "stats": {
                    **_official_pass_stats(member_count=44),
                    "record_success_count": 44,
                    "summary_success_count": 44,
                    "command_failure_count": 0,
                    "attendance_anomaly_names": ["员工A"],
                    "unexpected_empty_record_names": [],
                    "summary_today_anomaly_names": [],
                    "incomplete_record_names": ["员工A"],
                    "monthly_attendance_anomalies": [
                        {"name": "员工A", "monthly_count": 2, "latest_date": "2026-07-08"}
                    ],
                    "monthly_consecutive_anomalies": [
                        {
                            "name": "员工A",
                            "monthly_count": 2,
                            "consecutive_days": 2,
                            "latest_date": "2026-07-08",
                        }
                    ],
                },
            }
        )
        body = build_notification_message(**context, markdown=False)

        self.assertIn("本次44人全部考勤正常", body)
        self.assertNotIn("今日异常 / 无考勤", body)
        self.assertNotIn("连续异常", body)
        self.assertNotIn("员工A", body)

    def test_notification_context_keeps_evening_incomplete_records_as_today_anomalies(self) -> None:
        context = notification_context_from_output_status(
            {
                "run_id": "dingtalk_attendance_evening_20260708_181500",
                "run_type": "evening",
                "work_date": "2026-07-08",
                "current_time": "18:15",
                "stats": {
                    "member_count": 44,
                    "attendance_anomaly_names": ["员工A"],
                    "unexpected_empty_record_names": [],
                    "summary_today_anomaly_names": [],
                    "incomplete_record_names": ["员工A"],
                    "monthly_attendance_anomalies": [
                        {"name": "员工A", "monthly_count": 2, "latest_date": "2026-07-08"}
                    ],
                    "monthly_consecutive_anomalies": [
                        {
                            "name": "员工A",
                            "monthly_count": 2,
                            "consecutive_days": 2,
                            "latest_date": "2026-07-08",
                        }
                    ],
                },
            }
        )
        body = build_notification_message(**context, markdown=False)

        self.assertIn("今日异常 / 无考勤\n员工A（本月累计2次）", body)
        self.assertIn("连续异常\n员工A（连续2天，本月累计2次）", body)
        self.assertNotIn("今天一切良好", body)

    def test_notification_context_reports_system_collection_failures(self) -> None:
        context = notification_context_from_output_status(
            {
                "run_id": "dingtalk_attendance_morning_20260707_083500",
                "run_type": "morning",
                "work_date": "2026-07-07",
                "current_time": "08:35",
                "stats": {
                    "command_failure_count": 44,
                    "record_failure_count": 44,
                    "summary_failure_count": 0,
                    "unexpected_empty_record_names": [],
                },
            }
        )
        body = build_notification_message(**context, markdown=False)

        self.assertIn("本次暂无需要处理的考勤事项", body)
        self.assertNotIn("待审批 / 待补卡 / 待核查", body)
        self.assertNotIn("DWS", body)
        self.assertNotIn("record", body)
        self.assertNotIn("attendance.record:get", body)
        self.assertNotIn("权限", body)

    def test_notification_context_blocks_all_clear_when_success_counts_do_not_cover_members(self) -> None:
        context = notification_context_from_output_status(
            {
                "run_id": "dingtalk_attendance_morning_20260707_083500",
                "run_type": "morning",
                "work_date": "2026-07-07",
                "current_time": "08:35",
                "stats": {
                    "member_count": 44,
                    "record_success_count": 43,
                    "summary_success_count": 44,
                    "record_failure_count": 0,
                    "summary_failure_count": 0,
                    "command_failure_count": 0,
                    "attendance_anomaly_names": [],
                },
            }
        )
        body = build_notification_message(**context, markdown=False)

        self.assertIn("本次暂无需要处理的考勤事项", body)
        self.assertNotIn("DWS", body)
        self.assertNotIn("record", body)
        self.assertNotIn("未覆盖", body)

    def test_notification_context_keeps_backend_diagnostics_out_of_user_message(self) -> None:
        context = notification_context_from_output_status(
            {
                "run_id": "dingtalk_attendance_morning_20260708_083500",
                "run_type": "morning",
                "work_date": "2026-07-08",
                "current_time": "08:35",
                "stats": {
                    "member_count": 44,
                    "record_success_count": 43,
                    "summary_success_count": 44,
                    "record_failure_count": 1,
                    "summary_failure_count": 0,
                    "command_failure_count": 1,
                    "unexpected_empty_record_names": [],
                    "summary_today_anomaly_names": [],
                    "incomplete_record_names": [],
                    "attendance_anomaly_names": [],
                },
            }
        )
        body = build_notification_message(**context, markdown=False)

        self.assertIn("本次暂无需要处理的考勤事项", body)
        for backend_text in ("DWS", "record", "summary", "attendance.record:get", "权限", "取数失败", "未覆盖"):
            self.assertNotIn(backend_text, body)

    def test_rest_required_people_count_only_full_morning_and_evening_attendance_days(self) -> None:
        records = [
            {
                "member": {"name": "张三", "userId": "u1"},
                "work_date": "2026-07-01",
                "record_list": [{"checkTypeDesc": "上班"}, {"checkTypeDesc": "下班"}],
            },
            {
                "member": {"name": "张三", "userId": "u1"},
                "work_date": "2026-07-02",
                "record_list": [{"checkTypeDesc": "上班"}],
            },
            {
                "member": {"name": "张三", "userId": "u1"},
                "work_date": "2026-07-03",
                "record_list": [{"checkType": "OnDuty"}, {"checkType": "OffDuty"}],
            },
            {
                "member": {"name": "张三", "userId": "u1"},
                "work_date": "2026-07-03",
                "record_list": [{"checkTypeDesc": "上班"}, {"checkTypeDesc": "下班"}],
            },
            {
                "member": {"name": "李四", "userId": "u2"},
                "work_date": "2026-07-01",
                "record_list": [{"checkTypeDesc": "上班"}, {"checkTypeDesc": "下班"}],
            },
        ]

        self.assertEqual(
            build_monthly_rest_required_people(records, threshold_days=2),
            [{"name": "张三", "effective_attendance_days": 2, "latest_date": "2026-07-03"}],
        )

    def test_monthly_rollup_uses_latest_official_user_day_over_legacy_and_earlier_official_runs(self) -> None:
        records = [
            {
                "_archive_run_id": "dingtalk_attendance_evening_20260710_230000",
                "member": {"name": "测试甲", "userId": "u1"},
                "work_date": "2026-07-10",
                "record_list": [{"checkTypeDesc": "上班"}, {"checkTypeDesc": "下班"}],
                "derived": {"record_success": True, "record_anomaly": True},
            },
            {
                "_archive_run_id": "dingtalk_attendance_morning_20260710_103500",
                "member": {"name": "测试甲", "userId": "u1"},
                "work_date": "2026-07-10",
                "derived": {
                    "official_report_anomaly": True,
                    "official_effective_day": False,
                },
            },
            {
                "_archive_run_id": "dingtalk_attendance_evening_20260710_200000",
                "member": {"name": "测试甲", "userId": "u1"},
                "work_date": "2026-07-10",
                "derived": {
                    "official_report_anomaly": False,
                    "official_effective_day": True,
                },
            },
            {
                "_archive_run_id": "dingtalk_attendance_morning_20260711_103500",
                "member": {"name": "测试甲", "userId": "u1"},
                "work_date": "2026-07-11",
                "derived": {
                    "official_report_anomaly": True,
                    "official_effective_day": False,
                },
            },
        ]

        result = build_monthly_notification_rollups(
            records,
            current_stats={"attendance_anomaly_names": ["测试甲"]},
            work_date="2026-07-11",
            threshold_days=1,
        )

        self.assertEqual(
            result["monthly_attendance_anomalies"],
            [{"name": "测试甲", "monthly_count": 1, "latest_date": "2026-07-11"}],
        )
        self.assertEqual(result["monthly_consecutive_anomalies"], [])
        self.assertEqual(
            result["rest_required_people"],
            [{"name": "测试甲", "effective_attendance_days": 1, "latest_date": "2026-07-10"}],
        )

    def test_rest_required_people_can_be_built_from_monthly_private_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            month_dir = Path(tmpdir)
            for day in ("20260701", "20260702", "20260703"):
                run_id = f"dingtalk_attendance_final_{day}_181500"
                work_date = f"{day[:4]}-{day[4:6]}-{day[6:]}"
                raw_path = month_dir / f"{run_id}.raw.jsonl.gz"
                record_list = [{"checkTypeDesc": "上班"}, {"checkTypeDesc": "下班"}]
                if day == "20260702":
                    record_list = [{"checkTypeDesc": "上班"}]
                with gzip.open(raw_path, "wt", encoding="utf-8") as handle:
                    handle.write(
                        json.dumps(
                            {"type": "metadata", "run_plan": {"run_id": run_id}},
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    handle.write(
                        json.dumps(
                            {
                                "type": "employee_attendance",
                                "member": {"name": "张三", "userId": "u1"},
                                "record": {
                                    "final": {
                                        "payload": {
                                            "result": {"recordList": record_list},
                                        }
                                    }
                                },
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                _write_certificate_bound_final_manifest(
                    month_dir,
                    run_id=run_id,
                    work_date=work_date,
                    people=1,
                )

            stats = build_stats_with_rest_required_people({}, month_dir=month_dir, threshold_days=2)

            self.assertEqual(stats["rest_required_people"], [{"name": "张三", "effective_attendance_days": 2, "latest_date": "2026-07-03"}])

    def test_dws_user_chat_sender_uses_text_flag_and_records_business_error(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(args: list[str], timeout: int = 30) -> dict:
            calls.append(args)
            return {
                "returncode": 1,
                "payload": {
                    "error": {
                        "server_key": "chat",
                        "reason": "business_error",
                        "message": "系统错误",
                        "trace_id": "trace-1",
                    }
                },
            }

        result = send_dws_chat_message(
            recipient_flag="--user",
            recipient_value="1iv-1t2oesv2yd",
            title="开明考勤个人通知验证",
            text="开明考勤个人通知验证",
            help_text="Flags:\n      --user string\n      --text string\n",
            runner=fake_runner,
        )

        self.assertEqual(calls[0][:7], ["dws", "chat", "message", "send", "--user", "1iv-1t2oesv2yd", "--title"])
        self.assertIn("--text", calls[0])
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["channel"], "dws_userid_chat")
        self.assertEqual(result["failure_reason"], "business_error")
        self.assertEqual(result["server_key"], "chat")
        self.assertEqual(result["trace_id"], "trace-1")

    def test_notification_probe_falls_back_to_open_dingtalk_id_and_writes_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = Path(tmpdir) / "private_runtime"
            manifest_path = Path(tmpdir) / "notification_channel_manifest.json"
            calls: list[list[str]] = []

            def fake_runner(args: list[str], timeout: int = 30) -> dict:
                calls.append(args)
                if args[:5] == ["dws", "chat", "message", "send", "--user"]:
                    return {"returncode": 1, "payload": {"error": {"server_key": "chat", "reason": "business_error", "message": "系统错误"}}}
                if args[:5] == ["dws", "contact", "user", "get", "--ids"]:
                    return {"returncode": 0, "payload": {"success": True, "result": [{"name": "张霖泽", "userId": "1iv-1t2oesv2yd"}]}}
                if args[:5] == ["dws", "contact", "user", "search", "--query"]:
                    return {
                        "returncode": 0,
                        "payload": {
                            "success": True,
                            "result": [{"name": "张霖泽", "userId": "1iv-1t2oesv2yd", "openDingTalkId": "open-ding-id"}],
                        },
                    }
                if args[:5] == ["dws", "chat", "message", "send", "--open-dingtalk-id"]:
                    return {"returncode": 0, "payload": {"success": True, "openTaskId": "task-1"}}
                raise AssertionError(f"unexpected args: {args}")

            result = probe_notification_channels(
                recipient="1iv-1t2oesv2yd",
                recipient_name="张霖泽",
                runtime_dir=runtime_dir,
                public_manifest_path=manifest_path,
                now=datetime(2026, 7, 7, 18, 15),
                env={},
                dws_runner=fake_runner,
                help_provider=lambda command: "Flags:\n      --user string\n      --open-dingtalk-id string\n      --text string\n",
                robot_sender=lambda **kwargs: {"status": "NOTIFIER_CONFIG_MISSING", "channel": "dingtalk_group_robot"},
            )

            resolved = json.loads((runtime_dir / "notification_channel_resolved.json").read_text(encoding="utf-8"))
            public_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "SENT")
            self.assertEqual(result["successful_channel"], "dws_open_dingtalk_id_chat")
            self.assertEqual(resolved["channel"], "dws_open_dingtalk_id_chat")
            self.assertEqual(resolved["channel_type"], "personal")
            self.assertNotIn("open-ding-id", json.dumps(public_manifest, ensure_ascii=False))
            self.assertEqual(public_manifest["last_success_channel"], "dws_open_dingtalk_id_chat")

    def test_dispatch_reports_with_resolved_channel_sends_unified_attendance_notification(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            management = root / "run.management.md"
            hr = root / "run.hr.md"
            receipt = root / "run.dispatch.json"
            resolved = root / "notification_channel_resolved.json"
            management.write_text("# 开明考勤管理报告\n\n## 一、总体情况\n完成。", encoding="utf-8")
            hr.write_text("# 开明考勤 HR 报告\n\n" + "长" * 5000, encoding="utf-8")
            resolved.write_text(
                json.dumps(
                    {
                        "status": "SENT",
                        "channel": "dws_userid_chat",
                        "channel_type": "personal",
                        "recipient_user_id": "1iv-1t2oesv2yd",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            sent: list[tuple[str, str]] = []

            def fake_sender(*, channel: dict, title: str, text: str, env: dict[str, str]) -> dict:
                sent.append((title, text))
                return {"status": "SENT", "channel": channel["channel"]}

            result = dispatch_reports_with_resolved_channel(
                output_status={
                    "run_id": "dingtalk_attendance_evening_20260707_181500",
                    "run_type": "evening",
                    "work_date": "2026-07-07",
                    "current_time": "18:15",
                    "stats": {
                        **_official_pass_stats(anomaly_names=["张三"]),
                        "unexpected_empty_record_names": ["张三"],
                        "known_no_record_names": ["张霖泽"],
                        "rest_required_people": [{"name": "李四", "effective_attendance_days": 25}],
                    },
                    "management_report": str(management),
                    "hr_report": str(hr),
                    "dispatch_receipt": str(receipt),
                },
                resolved_path=resolved,
                env={},
                sender=fake_sender,
            )

            self.assertEqual(result["notification_status"], "SENT")
            self.assertEqual([title for title, _ in sent], ["开明考勤提醒"])
            self.assertIn("开明考勤提醒｜2026-07-07｜晚间暂时提醒", sent[0][1])
            self.assertNotIn("evening", sent[0][1])
            self.assertNotIn("morning", sent[0][1])
            self.assertIn("今日异常 / 无考勤\n张三（本月累计1次）", sent[0][1])
            self.assertNotIn("张霖泽", sent[0][1])
            self.assertNotIn("林全意", sent[0][1])
            self.assertIn("需要休息\n李四（本月有效考勤25天）", sent[0][1])
            self.assertNotIn("run_id：dingtalk_attendance_evening_20260707_181500", sent[0][1])
            self.assertNotIn("北京时间：18:15", sent[0][1])
            self.assertNotIn("OneDrive 报告路径：", sent[0][1])
            self.assertNotIn(f"管理报告：{management}", sent[0][1])
            self.assertNotIn(f"HR 报告：{hr}", sent[0][1])
            self.assertNotIn(str(management), sent[0][1])
            self.assertNotIn("# 开明考勤管理报告", sent[0][1])
            self.assertNotIn("# 开明考勤 HR 报告", sent[0][1])
            self.assertNotIn("## 一、总体情况", sent[0][1])
            self.assertNotIn("长" * 100, sent[0][1])
            receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual([message["report"] for message in receipt_payload["messages"]], ["attendance_notification"])
            self.assertEqual(receipt_payload["run_id"], "dingtalk_attendance_evening_20260707_181500")
            self.assertEqual(receipt_payload["management_report"], str(management))
            self.assertEqual(receipt_payload["hr_report"], str(hr))

    def test_send_latest_report_does_not_resend_legacy_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            month_dir = root / "202607"
            runtime_dir = root / "private_runtime"
            month_dir.mkdir()
            runtime_dir.mkdir()
            management = month_dir / "dingtalk_attendance_evening_20260707_181500.management.md"
            hr = month_dir / "dingtalk_attendance_evening_20260707_181500.hr.md"
            receipt = month_dir / "dingtalk_attendance_evening_20260707_181500.dispatch.json"
            manifest = month_dir / "dingtalk_attendance_evening_20260707_181500.manifest.json"
            management.write_text("# 开明考勤管理报告\n完成。", encoding="utf-8")
            hr.write_text("# 开明考勤 HR 报告\n无。", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "run_id": "dingtalk_attendance_evening_20260707_181500",
                        "skill_id": "kmfa-dingtalk-attendance-skill",
                        "management_report": str(management),
                        "hr_report": str(hr),
                        "dispatch_receipt": str(receipt),
                        "cleanup_audit": str(month_dir / "dingtalk_attendance_evening_20260707_181500.cleanup.json"),
                        "stats": _official_pass_stats(),
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (runtime_dir / "notification_channel_resolved.json").write_text(
                json.dumps(
                    {
                        "status": "SENT",
                        "channel": "dws_userid_chat",
                        "channel_type": "personal",
                        "recipient_user_id": "1iv-1t2oesv2yd",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            sent: list[dict[str, object]] = []

            def fake_sender(**kwargs: object) -> dict[str, object]:
                sent.append(dict(kwargs))
                channel_payload = kwargs["channel"]
                assert isinstance(channel_payload, dict)
                return {"status": "SENT", "channel": channel_payload["channel"]}

            result = send_latest_report(
                channel="auto",
                onedrive_root=root,
                resolved_path=runtime_dir / "notification_channel_resolved.json",
                targets_resolved_path=runtime_dir / "notification_targets_resolved.json",
                public_targets_manifest_path=runtime_dir / "notification_targets_manifest.json",
                env={},
                sender=fake_sender,
                delivery_enabled=True,
            )

            self.assertEqual(result["status"], "NOT_SENT_REALTIME_REMINDER_INTEGRITY_FAILED")
            self.assertEqual(result["manifest"], str(manifest))
            self.assertEqual(sent, [])
            self.assertTrue(receipt.exists())

    def test_send_latest_report_rejects_legacy_manifest_without_exact_official_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            month_dir = root / "202607"
            runtime_dir = root / "private_runtime"
            month_dir.mkdir()
            runtime_dir.mkdir()
            management = month_dir / "dingtalk_attendance_evening_20260707_200000.management.md"
            hr = month_dir / "dingtalk_attendance_evening_20260707_200000.hr.md"
            receipt = month_dir / "dingtalk_attendance_evening_20260707_200000.dispatch.json"
            manifest = month_dir / "dingtalk_attendance_evening_20260707_200000.manifest.json"
            management.write_text("# legacy management", encoding="utf-8")
            hr.write_text("# legacy hr", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "run_id": "dingtalk_attendance_evening_20260707_200000",
                        "skill_id": "kmfa-dingtalk-attendance-skill",
                        "management_report": str(management),
                        "hr_report": str(hr),
                        "dispatch_receipt": str(receipt),
                        "stats": {},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            targets_resolved = runtime_dir / "notification_targets_resolved.json"
            targets_resolved.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "targets": [
                            {
                                "label": "张霖泽",
                                "type": "personal",
                                "enabled": True,
                                "reports": ["management", "hr"],
                                "resolved_channel": "dws_userid_chat",
                                "user_id": "local-test-user",
                                "last_probe_status": "SENT",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            sent: list[dict[str, object]] = []

            result = send_latest_report(
                channel="auto",
                onedrive_root=root,
                targets_resolved_path=targets_resolved,
                public_targets_manifest_path=runtime_dir / "notification_targets_manifest.json",
                env={},
                sender=lambda **kwargs: sent.append(dict(kwargs)) or {"status": "SENT"},
                delivery_enabled=True,
            )

            self.assertEqual(result["status"], "OFFICIAL_ATTENDANCE_PARITY_FAILED")
            self.assertEqual(result["notification_status"], "NOT_SENT_OFFICIAL_ATTENDANCE_PARITY_FAILED")
            self.assertEqual(sent, [])
            self.assertFalse(receipt.exists())

    def test_run_attendance_send_latest_only_rejects_manifest_without_official_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = root / "dingtalk_attendance_morning_20260711_103500.manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "run_id": "dingtalk_attendance_morning_20260711_103500",
                        "skill_id": "kmfa-dingtalk-attendance-skill",
                        "management_report": str(root / "management.md"),
                        "hr_report": str(root / "hr.md"),
                        "dispatch_receipt": str(root / "dispatch.json"),
                        "cleanup_audit": str(root / "cleanup.json"),
                        "stats": {},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.object(ATTENDANCE_RUNNER, "find_latest_report_manifest", return_value=manifest),
                patch.object(
                    ATTENDANCE_RUNNER,
                    "dispatch_reports_to_targets",
                    side_effect=AssertionError("must not dispatch an unverified archive"),
                ),
                patch.object(ATTENDANCE_RUNNER, "cleanup_runtime", return_value={"status": "OK"}),
            ):
                result = ATTENDANCE_RUNNER.send_latest_report_only("morning", "Asia/Shanghai")

            self.assertEqual(result["status"], "NOT_SENT_OWNER_DISABLED")
            self.assertEqual(result["notification_status"], "NOT_SENT_OWNER_DISABLED")

    def test_legacy_resolved_channel_migrates_to_multitarget_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = Path(tmpdir) / "private_runtime"
            runtime_dir.mkdir()
            legacy_resolved = runtime_dir / "notification_channel_resolved.json"
            targets_config = runtime_dir / "notification_targets.local.json"
            targets_resolved = runtime_dir / "notification_targets_resolved.json"
            public_manifest = Path(tmpdir) / "notification_targets_manifest.json"
            legacy_resolved.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "SENT",
                        "resolved_at": "2026-07-07T18:15:00+08:00",
                        "recipient_name": "张霖泽",
                        "channel": "dws_open_dingtalk_id_chat",
                        "channel_type": "personal",
                        "recipient_user_id": "1iv-1t2oesv2yd",
                        "open_dingtalk_id": "open-secret-id",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = migrate_legacy_resolved_channel(
                legacy_path=legacy_resolved,
                targets_config_path=targets_config,
                targets_resolved_path=targets_resolved,
                public_manifest_path=public_manifest,
            )

            resolved = json.loads(targets_resolved.read_text(encoding="utf-8"))
            manifest = json.loads(public_manifest.read_text(encoding="utf-8"))
            self.assertTrue(result["migrated"])
            self.assertEqual(resolved["targets"][0]["label"], "张霖泽")
            self.assertEqual(resolved["targets"][0]["resolved_channel"], "dws_open_dingtalk_id_chat")
            self.assertEqual(resolved["targets"][0]["open_dingtalk_id"], "open-secret-id")
            self.assertEqual(manifest["targets"][0]["resolved_channel"], "dws_open_dingtalk_id_chat")
            self.assertFalse(manifest["sensitive_values_committed"])
            self.assertNotIn("open-secret-id", json.dumps(manifest, ensure_ascii=False))

    def test_dispatch_reports_to_targets_sends_one_unique_template_per_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            management = root / "run.management.md"
            hr = root / "run.hr.md"
            receipt = root / "run.dispatch.json"
            targets_resolved = root / "notification_targets_resolved.json"
            management.write_text("# 开明考勤管理报告\n\n## 一、总体情况\n完成。", encoding="utf-8")
            hr.write_text("# 开明考勤 HR 报告\n\n## 一、异常明细\n无。", encoding="utf-8")
            targets_resolved.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "targets": [
                            {
                                "label": "张霖泽",
                                "type": "personal",
                                "enabled": True,
                                "reports": ["management"],
                                "resolved_channel": "dws_userid_chat",
                                "user_id": "1iv-1t2oesv2yd",
                                "last_probe_status": "SENT",
                            },
                            {
                                "label": "考勤小群",
                                "type": "group",
                                "enabled": True,
                                "reports": ["hr"],
                                "resolved_channel": "dws_group_chat",
                                "group_conversation_id": "cid-secret",
                                "last_probe_status": "SENT",
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            sent: list[tuple[str, str, str]] = []

            def fake_sender(*, channel: dict, title: str, text: str, env: dict[str, str]) -> dict:
                sent.append((channel["channel"], title, text))
                return {"status": "SENT", "channel": channel["channel"]}

            result = dispatch_reports_to_targets(
                output_status={
                    "run_id": "dingtalk_attendance_evening_20260707_181500",
                    "run_type": "evening",
                    "work_date": "2026-07-07",
                    "current_time": "18:15",
                    "stats": _realtime_pass_stats(),
                    "management_report": str(management),
                    "hr_report": str(hr),
                    "dispatch_receipt": str(receipt),
                },
                targets_resolved_path=targets_resolved,
                env={},
                sender=fake_sender,
            )

            self.assertEqual(result["notification_status"], "SENT")
            self.assertEqual([item[1] for item in sent], ["开明考勤提醒", "开明考勤提醒"])
            self.assertEqual([item[0] for item in sent], ["dws_userid_chat", "dws_group_chat"])
            for _, _, body in sent:
                self.assertIn("开明考勤提醒｜2026-07-07｜晚间暂时提醒", body)
                self.assertNotIn("evening", body)
                self.assertNotIn("morning", body)
                self.assertNotIn("run_id：", body)
                self.assertNotIn("北京时间：", body)
                self.assertNotIn("OneDrive 报告路径：", body)
                self.assertNotIn(str(management), body)
                self.assertNotIn(str(hr), body)
                self.assertNotIn("# 开明考勤管理报告", body)
                self.assertNotIn("# 开明考勤 HR 报告", body)
                self.assertNotIn("## 一、总体情况", body)
                self.assertNotIn("## 一、异常明细", body)
            self.assertEqual(result["notification_template_text"], sent[0][2])
            self.assertEqual(
                result["notification_delivery_table"],
                "| 发送对象 | 是否成功 |\n|---|---|\n| 张霖泽 | 是 |\n| 考勤小群 | 是 |",
            )
            receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(receipt_payload["run_id"], "dingtalk_attendance_evening_20260707_181500")
            self.assertEqual(receipt_payload["target_results"][0]["management_status"], "SENT")
            self.assertEqual(receipt_payload["target_results"][0]["hr_status"], "SKIPPED")
            self.assertEqual(receipt_payload["target_results"][1]["management_status"], "SKIPPED")
            self.assertEqual(receipt_payload["target_results"][1]["hr_status"], "SENT")
            self.assertFalse(receipt_payload["target_results"][1]["trace_id_present"])

    def test_dispatch_boundary_rejects_missing_official_parity_before_sender_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            targets_resolved = root / "notification_targets_resolved.json"
            receipt = root / "dispatch.json"
            targets_resolved.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "targets": [
                            {
                                "label": "张霖泽",
                                "type": "personal",
                                "enabled": True,
                                "reports": ["management", "hr"],
                                "resolved_channel": "dws_userid_chat",
                                "user_id": "local-test-user",
                                "last_probe_status": "SENT",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            sent: list[dict[str, object]] = []

            result = dispatch_reports_to_targets(
                output_status={
                    "run_id": "dingtalk_attendance_evening_20260707_200000",
                    "run_type": "evening",
                    "work_date": "2026-07-07",
                    "stats": {},
                    "management_report": str(root / "management.md"),
                    "hr_report": str(root / "hr.md"),
                    "dispatch_receipt": str(receipt),
                },
                targets_resolved_path=targets_resolved,
                env={},
                sender=lambda **kwargs: sent.append(dict(kwargs)) or {"status": "SENT"},
            )

            self.assertEqual(result["notification_status"], "NOT_SENT_REALTIME_REMINDER_INTEGRITY_FAILED")
            self.assertEqual(sent, [])
            self.assertTrue(receipt.exists())

    def test_dispatch_duplicate_guard_blocks_same_work_date_and_slot_without_sender_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            prior_receipt = root / "prior.dispatch.json"
            current_receipt = root / "current.dispatch.json"
            targets_resolved = root / "notification_targets_resolved.json"
            prior_receipt.write_text(
                json.dumps(
                    {
                        "notification_status": "SENT",
                        "run_id": "dingtalk_attendance_evening_20260716_200500",
                        "run_type": "evening",
                        "work_date": "2026-07-16",
                    }
                ),
                encoding="utf-8",
            )
            targets_resolved.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "targets": [
                            {
                                "label": "生产管理群",
                                "type": "group",
                                "enabled": True,
                                "reports": ["management", "hr"],
                                "resolved_channel": "dingtalk_group_robot_env",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            sent: list[dict[str, object]] = []

            result = dispatch_reports_to_targets(
                output_status={
                    "run_id": "dingtalk_attendance_evening_20260716_200501",
                    "run_type": "evening",
                    "work_date": "2026-07-16",
                    "stats": _realtime_pass_stats(),
                    "management_report": str(root / "management.md"),
                    "hr_report": str(root / "hr.md"),
                    "dispatch_receipt": str(current_receipt),
                },
                targets_resolved_path=targets_resolved,
                target_filter="group",
                env={},
                sender=lambda **kwargs: sent.append(dict(kwargs)) or {"status": "SENT"},
            )

            self.assertEqual(result["notification_status"], "NOT_SENT_DUPLICATE_GUARD")
            self.assertEqual(sent, [])
            self.assertTrue(current_receipt.exists())

    def test_dispatch_persists_send_started_before_external_group_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            management = root / "management.md"
            hr = root / "hr.md"
            receipt = root / "current.dispatch.json"
            targets_resolved = root / "notification_targets_resolved.json"
            management.write_text("management", encoding="utf-8")
            hr.write_text("hr", encoding="utf-8")
            targets_resolved.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "targets": [
                            {
                                "label": "生产管理群",
                                "type": "group",
                                "enabled": True,
                                "reports": ["management", "hr"],
                                "resolved_channel": "dingtalk_group_robot_env",
                                "webhook_env_key": "ROBOT_URL",
                                "secret_env_key": "ROBOT_SECRET",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            def fake_sender(**_: object) -> dict[str, object]:
                intent = json.loads(receipt.read_text(encoding="utf-8"))
                self.assertEqual(intent["notification_status"], "SEND_STARTED")
                return {"status": "SENT", "channel": "dingtalk_group_robot"}

            result = dispatch_reports_to_targets(
                output_status={
                    "run_id": "dingtalk_attendance_evening_20260716_200500",
                    "run_type": "evening",
                    "work_date": "2026-07-16",
                    "current_time": "20:05",
                    "stats": _realtime_pass_stats(),
                    "management_report": str(management),
                    "hr_report": str(hr),
                    "dispatch_receipt": str(receipt),
                },
                targets_resolved_path=targets_resolved,
                target_filter="group",
                env={"ROBOT_URL": "https://example.invalid", "ROBOT_SECRET": "placeholder-secret"},
                sender=fake_sender,
            )

            self.assertEqual(result["notification_status"], "SENT")

    def test_probe_notification_targets_resolves_personal_target_and_redacts_public_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            runtime_dir = root / "private_runtime"
            runtime_dir.mkdir()
            targets_config = runtime_dir / "notification_targets.local.json"
            targets_resolved = runtime_dir / "notification_targets_resolved.json"
            public_manifest = root / "notification_targets_manifest.json"
            targets_config.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "targets": [
                            {
                                "label": "张霖泽",
                                "type": "personal",
                                "enabled": True,
                                "reports": ["management", "hr"],
                                "user_id": "1iv-1t2oesv2yd",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            calls: list[list[str]] = []

            def fake_runner(args: list[str], timeout: int = 30) -> dict:
                calls.append(args)
                if args[:5] == ["dws", "contact", "user", "get", "--ids"]:
                    return {
                        "returncode": 0,
                        "payload": {
                            "success": True,
                            "result": [{"name": "张霖泽", "userId": "1iv-1t2oesv2yd", "openDingTalkId": "open-secret-id"}],
                        },
                    }
                if args[:5] == ["dws", "chat", "message", "send", "--open-dingtalk-id"]:
                    return {"returncode": 0, "payload": {"success": True, "openTaskId": "task-1"}}
                raise AssertionError(f"unexpected args: {args}")

            result = probe_notification_targets(
                targets_config_path=targets_config,
                targets_resolved_path=targets_resolved,
                public_manifest_path=public_manifest,
                now=datetime(2026, 7, 7, 18, 15),
                env={},
                dws_runner=fake_runner,
                help_provider=lambda command: "Flags:\n      --user string\n      --open-dingtalk-id string\n      --text string\n",
            )

            resolved = json.loads(targets_resolved.read_text(encoding="utf-8"))
            manifest = json.loads(public_manifest.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "SENT")
            self.assertEqual(resolved["targets"][0]["resolved_channel"], "dws_open_dingtalk_id_chat")
            self.assertEqual(resolved["targets"][0]["open_dingtalk_id"], "open-secret-id")
            self.assertEqual(manifest["targets"][0]["resolved_channel"], "dws_open_dingtalk_id_chat")
            self.assertFalse(manifest["sensitive_values_committed"])
            self.assertNotIn("open-secret-id", json.dumps(manifest, ensure_ascii=False))
            self.assertTrue(any(call[:5] == ["dws", "chat", "message", "send", "--open-dingtalk-id"] for call in calls))

    def test_probe_notification_targets_searches_open_id_when_user_get_lacks_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            runtime_dir = root / "private_runtime"
            runtime_dir.mkdir()
            targets_config = runtime_dir / "notification_targets.local.json"
            targets_config.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "targets": [
                            {
                                "label": "张霖泽",
                                "type": "personal",
                                "enabled": True,
                                "reports": ["management", "hr"],
                                "user_id": "1iv-1t2oesv2yd",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            calls: list[list[str]] = []

            def fake_runner(args: list[str], timeout: int = 30) -> dict:
                calls.append(args)
                if args[:5] == ["dws", "contact", "user", "get", "--ids"]:
                    return {"returncode": 0, "payload": {"success": True, "result": [{"name": "张霖泽", "userId": "1iv-1t2oesv2yd"}]}}
                if args[:5] == ["dws", "contact", "user", "search", "--query"]:
                    return {
                        "returncode": 0,
                        "payload": {
                            "success": True,
                            "result": [{"name": "张霖泽", "userId": "1iv-1t2oesv2yd", "openDingTalkId": "open-secret-id"}],
                        },
                    }
                if args[:5] == ["dws", "chat", "message", "send", "--open-dingtalk-id"]:
                    return {"returncode": 0, "payload": {"success": True, "openTaskId": "task-1"}}
                raise AssertionError(f"unexpected args: {args}")

            result = probe_notification_targets(
                targets_config_path=targets_config,
                targets_resolved_path=runtime_dir / "notification_targets_resolved.json",
                public_manifest_path=root / "notification_targets_manifest.json",
                now=datetime(2026, 7, 7, 18, 15),
                env={},
                dws_runner=fake_runner,
                help_provider=lambda command: "Flags:\n      --user string\n      --open-dingtalk-id string\n      --text string\n",
            )

            self.assertEqual(result["status"], "SENT")
            self.assertTrue(any(call[:5] == ["dws", "contact", "user", "search", "--query"] for call in calls))
            self.assertTrue(any(call[:5] == ["dws", "chat", "message", "send", "--open-dingtalk-id"] for call in calls))

    def test_probe_notification_targets_merges_single_target_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            runtime_dir = root / "private_runtime"
            runtime_dir.mkdir()
            targets_config = runtime_dir / "notification_targets.local.json"
            targets_resolved = runtime_dir / "notification_targets_resolved.json"
            public_manifest = root / "notification_targets_manifest.json"
            targets_config.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "targets": [
                            {
                                "label": "张霖泽",
                                "type": "personal",
                                "enabled": True,
                                "reports": ["management", "hr"],
                                "user_id": "1iv-1t2oesv2yd",
                            },
                            {
                                "label": "考勤小群",
                                "type": "group",
                                "enabled": True,
                                "reports": ["management", "hr"],
                                "conversation_id": "cid-secret",
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            targets_resolved.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "targets": [
                            {
                                "label": "张霖泽",
                                "type": "personal",
                                "enabled": True,
                                "reports": ["management", "hr"],
                                "resolved_channel": "dws_open_dingtalk_id_chat",
                                "user_id": "1iv-1t2oesv2yd",
                                "open_dingtalk_id": "open-secret-id",
                                "last_probe_status": "SENT",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            def fake_runner(args: list[str], timeout: int = 30) -> dict:
                if args[:5] == ["dws", "chat", "message", "send", "--group"]:
                    return {"returncode": 0, "payload": {"success": True}}
                raise AssertionError(f"unexpected args: {args}")

            result = probe_notification_targets(
                targets_config_path=targets_config,
                targets_resolved_path=targets_resolved,
                public_manifest_path=public_manifest,
                label_filter="考勤小群",
                now=datetime(2026, 7, 7, 18, 15),
                env={},
                dws_runner=fake_runner,
                help_provider=lambda command: "Flags:\n      --group string\n      --text string\n",
            )

            resolved = json.loads(targets_resolved.read_text(encoding="utf-8"))
            manifest = json.loads(public_manifest.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "SENT")
            self.assertEqual([target["label"] for target in resolved["targets"]], ["张霖泽", "考勤小群"])
            self.assertEqual(resolved["targets"][1]["resolved_channel"], "dws_group_chat")
            self.assertNotIn("open-secret-id", json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
