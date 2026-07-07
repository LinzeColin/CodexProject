import gzip
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from KMFA.tools.dingtalk_attendance.healthcheck import build_config_status
from KMFA.tools.dingtalk_attendance.dws_auth_guard import dws_command_safety_status
from KMFA.tools.dingtalk_attendance.notification_probe import probe_notification_channels
from KMFA.tools.dingtalk_attendance.notification_template import notification_context_from_output_status
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
from KMFA.tools.dingtalk_attendance.dws_attendance import DwsAttendanceError, collect_org_attendance, write_private_outputs
from KMFA.tools.dingtalk_attendance.run_attendance import (
    build_monthly_rest_required_people,
    build_notification_message,
    build_personal_notification_message,
    build_run_plan,
    build_stats_with_rest_required_people,
    dispatch_reports_to_robot,
    run_attendance,
)
from KMFA.tools.dingtalk_attendance.send_latest_report import send_latest_report
from KMFA.tools.dingtalk_attendance.check_s19_dingtalk_attendance import validate_s19_files
from KMFA.tools.dingtalk_attendance.validate_no_sensitive_git import scan_payload_for_sensitive_text


ROOT = Path(__file__).resolve().parents[1]


class FakeDwsRunner:
    def __init__(self, *, fail_first_record_for: str | None = None) -> None:
        self.calls: list[tuple[tuple[str, ...], bool]] = []
        self.fail_first_record_for = fail_first_record_for
        self.failed_once = False

    def __call__(self, args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict:
        self.calls.append((tuple(args), verbose))
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


class DingTalkAttendanceContractTests(unittest.TestCase):
    def test_run_plan_locks_s19_schedule_storage_and_owner(self) -> None:
        plan = build_run_plan(run_type="morning", timezone="Asia/Shanghai", run_id="contract-only")

        self.assertEqual(plan["stage_id"], "S19")
        self.assertEqual(plan["automation_name"], "每日早晚钉钉考勤检查")
        self.assertEqual(plan["run_type"], "morning")
        self.assertEqual(plan["timezone"], "Asia/Shanghai")
        self.assertEqual(plan["schedule"]["morning"], "08:35")
        self.assertEqual(plan["schedule"]["evening"], "18:15")
        self.assertEqual(plan["onedrive_root"], "/Users/linzezhang/OneDrive/dingtalk_attendance")
        self.assertEqual(plan["onedrive_month_folder_pattern"], "YYYYMM")
        self.assertEqual(plan["known_recipients"]["zhang_linze"]["dingtalk_user_id"], "1iv-1t2oesv2yd")
        self.assertFalse(plan["public_repo_safety"]["employee_plaintext_committed"])
        self.assertFalse(plan["public_repo_safety"]["sqlite_committed"])
        self.assertFalse(plan["public_repo_safety"]["credential_committed"])
        self.assertTrue(plan["live_only"])

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
        self.assertEqual(result["dws_command_safety"]["required_env"], "KMFA_S19_ALLOW_DWS_COMMANDS")

    def test_dws_command_safety_requires_explicit_local_allow(self) -> None:
        blocked = dws_command_safety_status(env={})
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "pat_policy.json"
            policy_path.write_text(json.dumps({"default": {"openBrowser": False}}, ensure_ascii=False), encoding="utf-8")
            allowed = dws_command_safety_status(
                env={
                    "KMFA_S19_ALLOW_DWS_COMMANDS": "1",
                    "KMFA_S19_DWS_BROWSER_POLICY_PATH": str(policy_path),
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
                    "KMFA_S19_ALLOW_DWS_COMMANDS": "1",
                    "KMFA_S19_DWS_BROWSER_POLICY_PATH": str(policy_path),
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
            ("一、异常明细", "二、连续异常人员", "三、待审批/待补卡/待核查", "四、数据质量与系统运行状态"),
        )
        self.assertNotIn("关键人员风险", json.dumps(MANAGEMENT_REPORT_SECTIONS, ensure_ascii=False))

    def test_sensitive_payload_scanner_rejects_credentials_and_robot_endpoint(self) -> None:
        bad_payloads = [
            "access" + "_token=abc",
            "app" + "_sec" + "ret=abc",
            "https://oapi.dingtalk.com/robot/" + "send?access" + "_token=abc",
        ]

        for payload in bad_payloads:
            with self.subTest(payload=payload):
                findings = scan_payload_for_sensitive_text(payload)
                self.assertGreaterEqual(len(findings), 1)
        allowed_schema_payload = "web" + "hook_env_key=DINGTALK_GROUP_ENDPOINT_ENV"
        self.assertEqual(scan_payload_for_sensitive_text(allowed_schema_payload), [])

    def test_s19_file_contract_is_complete_and_private_runtime_is_placeholder_only(self) -> None:
        result = validate_s19_files(ROOT)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["automation_name"], "每日早晚钉钉考勤检查")
        self.assertEqual(result["onedrive_root"], "/Users/linzezhang/OneDrive/dingtalk_attendance")
        self.assertEqual(result["prompt_count"], 3)
        self.assertEqual(result["private_runtime_tracked_files"], [".gitkeep", "README.md"])

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
                "run_id": "s19_morning_20260707_083500",
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
        self.assertIn("今日异常人员 / 无考勤人员：员工01、员工02。", body)
        self.assertNotIn("今日异常人员 / 无考勤人员：张霖泽", body)
        self.assertNotIn("林全意。", body)
        self.assertNotIn("今天一切良好", body)

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
                "run_id": "s19_morning_20260707_083500",
                "run_type": "morning",
                "work_date": "2026-07-07",
                "current_time": "08:35",
                "stats": collection["stats"],
            }
        )
        body = build_notification_message(**context, markdown=False)

        self.assertEqual(collection["stats"]["attendance_required_count"], 1)
        self.assertEqual(collection["stats"]["incomplete_record_names"], ["员工A"])
        self.assertEqual(collection["stats"]["attendance_anomaly_names"], ["员工A"])
        self.assertIn("今日异常人员 / 无考勤人员：员工A。", body)
        self.assertNotIn("今天一切良好", body)

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
                "run_id": "s19_morning_20260707_083500",
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
        self.assertIn("今日异常人员 / 无考勤人员：员工B。", body)
        self.assertNotIn("今天一切良好", body)

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
                "run_id": "s19_morning_20260707_083500",
                "stage_id": "S19",
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
        self.assertIn("# 开明考勤管理报告｜2026-07-07｜晨报", management)
        self.assertIn("# 开明考勤 HR 报告｜2026-07-07｜晨报", hr)
        self.assertIn("今日异常人员 / 无考勤人员：无。", management)
        self.assertIn("record 为空人员：无。", management)
        self.assertIn("record 缺少上下班打卡人员：无。", management)
        self.assertIn("今日异常人员 / 无考勤人员：无。", hr)
        self.assertIn("record 为空或缺少应有上下班打卡均计入用户可见异常。", hr)
        self.assertEqual(manifest["stats"]["known_no_record_names"], ["张霖泽", "林全意"])

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
                    "run_id": "s19_evening_20260707_181500",
                    "run_type": "evening",
                    "work_date": "2026-07-07",
                    "current_time": "18:15",
                    "stats": {
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
            self.assertIn("开明考勤提醒｜2026-07-07｜晚报", sent_bodies[0])
            self.assertNotIn("evening", sent_bodies[0])
            self.assertNotIn("morning", sent_bodies[0])
            self.assertIn("截止 18:15", sent_bodies[0])
            self.assertIn("今日异常人员 / 无考勤人员：张三。", sent_bodies[0])
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
        )

        self.assertEqual(
            message,
            "# 开明考勤提醒｜2026-07-07｜晨报\n\n截止 08:35\n\n今天一切良好\n",
        )
        self.assertNotIn("morning", message)
        self.assertNotIn("evening", message)
        self.assertNotIn("今日异常人员", message)
        self.assertNotIn("连续异常人员", message)
        self.assertNotIn("待审批/待补卡/待核查", message)

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

        self.assertEqual(markdown.replace("# ", "", 1), plain)
        self.assertIn("今日异常人员 / 无考勤人员：张三。", plain)
        self.assertIn("连续异常人员：\n李四连续 2 天异常", plain)
        self.assertIn("待审批/待补卡/待核查：\n王五待补卡", plain)

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
                {"name": "张三", "effective_attendance_days": 27},
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
                {"name": "张三", "effective_attendance_days": 27},
                {"name": "李四", "effective_attendance_days": 28},
            ],
            markdown=False,
        )

        self.assertEqual(markdown.replace("# ", "", 1), plain)
        self.assertIn("需要休息的人员：\n张三（已考勤27天）\n李四（已考勤28天）", markdown)
        self.assertNotIn("今天一切良好", markdown)

    def test_notification_context_uses_real_anomaly_names_without_exempt_people(self) -> None:
        context = notification_context_from_output_status(
            {
                "run_id": "s19_morning_20260707_083500",
                "run_type": "morning",
                "work_date": "2026-07-07",
                "current_time": "08:35",
                "stats": {
                    "attendance_anomaly_names": ["张三", "李四"],
                    "unexpected_empty_record_names": ["张霖泽", "林全意"],
                    "known_no_record_names": ["张霖泽", "林全意"],
                },
            }
        )
        body = build_notification_message(**context, markdown=False)

        self.assertIn("今日异常人员 / 无考勤人员：张三、李四。", body)
        self.assertNotIn("张霖泽", body)
        self.assertNotIn("林全意", body)

    def test_notification_context_reports_system_collection_failures(self) -> None:
        context = notification_context_from_output_status(
            {
                "run_id": "s19_morning_20260707_083500",
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

        self.assertIn("待审批/待补卡/待核查：", body)
        self.assertIn("DWS record 取数失败 44 人，需核查 attendance.record:get 权限。", body)
        self.assertNotIn("今天一切良好", body)

    def test_notification_context_blocks_all_clear_when_success_counts_do_not_cover_members(self) -> None:
        context = notification_context_from_output_status(
            {
                "run_id": "s19_morning_20260707_083500",
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

        self.assertIn("DWS record 取数未覆盖全部人员：成功 43/44，不得判定为正常。", body)
        self.assertNotIn("今天一切良好", body)

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
            [{"name": "张三", "effective_attendance_days": 2}],
        )

    def test_rest_required_people_can_be_built_from_monthly_private_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            month_dir = Path(tmpdir)
            for day in ("20260701", "20260702", "20260703"):
                raw_path = month_dir / f"s19_evening_{day}_181500.raw.jsonl.gz"
                record_list = [{"checkTypeDesc": "上班"}, {"checkTypeDesc": "下班"}]
                if day == "20260702":
                    record_list = [{"checkTypeDesc": "上班"}]
                with gzip.open(raw_path, "wt", encoding="utf-8") as handle:
                    handle.write(
                        json.dumps(
                            {"type": "metadata", "run_plan": {"run_id": f"s19_evening_{day}_181500"}},
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

            stats = build_stats_with_rest_required_people({}, month_dir=month_dir, threshold_days=2)

            self.assertEqual(stats["rest_required_people"], [{"name": "张三", "effective_attendance_days": 2}])

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
                    "run_id": "s19_evening_20260707_181500",
                    "run_type": "evening",
                    "work_date": "2026-07-07",
                    "current_time": "18:15",
                    "stats": {
                        "unexpected_empty_record_names": ["张三"],
                        "known_no_record_names": ["张霖泽"],
                        "rest_required_people": [{"name": "李四", "effective_attendance_days": 27}],
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
            self.assertIn("开明考勤提醒｜2026-07-07｜晚报", sent[0][1])
            self.assertNotIn("evening", sent[0][1])
            self.assertNotIn("morning", sent[0][1])
            self.assertIn("今日异常人员 / 无考勤人员：张三。", sent[0][1])
            self.assertNotIn("张霖泽", sent[0][1])
            self.assertNotIn("林全意", sent[0][1])
            self.assertIn("需要休息的人员：\n李四（已考勤27天）", sent[0][1])
            self.assertNotIn("run_id：s19_evening_20260707_181500", sent[0][1])
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
            self.assertEqual(receipt_payload["run_id"], "s19_evening_20260707_181500")
            self.assertEqual(receipt_payload["management_report"], str(management))
            self.assertEqual(receipt_payload["hr_report"], str(hr))

    def test_send_latest_report_uses_latest_manifest_without_collection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            month_dir = root / "202607"
            runtime_dir = root / "private_runtime"
            month_dir.mkdir()
            runtime_dir.mkdir()
            management = month_dir / "s19_evening_20260707_181500.management.md"
            hr = month_dir / "s19_evening_20260707_181500.hr.md"
            receipt = month_dir / "s19_evening_20260707_181500.dispatch.json"
            manifest = month_dir / "s19_evening_20260707_181500.manifest.json"
            management.write_text("# 开明考勤管理报告\n完成。", encoding="utf-8")
            hr.write_text("# 开明考勤 HR 报告\n无。", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "run_id": "s19_evening_20260707_181500",
                        "management_report": str(management),
                        "hr_report": str(hr),
                        "dispatch_receipt": str(receipt),
                        "cleanup_audit": str(month_dir / "s19_evening_20260707_181500.cleanup.json"),
                        "stats": {},
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
            )

            self.assertEqual(result["status"], "SENT")
            self.assertEqual(result["manifest"], str(manifest))
            self.assertEqual([item["title"] for item in sent], ["开明考勤提醒"])
            self.assertEqual(result["notification_template_text"], sent[0]["text"])
            self.assertIn("开明考勤提醒｜2026-07-07｜晚报", result["notification_template_text"])
            self.assertNotIn("evening", result["notification_template_text"])
            self.assertNotIn("morning", result["notification_template_text"])
            self.assertNotIn("run_id：", str(sent[0]["text"]))
            self.assertNotIn("北京时间：", str(sent[0]["text"]))
            self.assertNotIn("OneDrive 报告路径：", str(sent[0]["text"]))
            self.assertNotIn(str(management), str(sent[0]["text"]))
            self.assertNotIn(str(hr), str(sent[0]["text"]))
            self.assertEqual(result["notification_delivery_table"], "| 发送对象 | 是否成功 |\n|---|---|\n| 张霖泽 | 是 |")
            self.assertNotIn("# 开明考勤管理报告", str(sent[0]["text"]))
            self.assertNotIn("# 开明考勤 HR 报告", str(sent[0]["text"]))
            self.assertTrue(receipt.exists())

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
                    "run_id": "s19_evening_20260707_181500",
                    "run_type": "evening",
                    "work_date": "2026-07-07",
                    "current_time": "18:15",
                    "stats": {},
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
                self.assertIn("开明考勤提醒｜2026-07-07｜晚报", body)
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
            self.assertEqual(receipt_payload["run_id"], "s19_evening_20260707_181500")
            self.assertEqual(receipt_payload["target_results"][0]["management_status"], "SENT")
            self.assertEqual(receipt_payload["target_results"][0]["hr_status"], "SKIPPED")
            self.assertEqual(receipt_payload["target_results"][1]["management_status"], "SKIPPED")
            self.assertEqual(receipt_payload["target_results"][1]["hr_status"], "SENT")
            self.assertFalse(receipt_payload["target_results"][1]["trace_id_present"])

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
