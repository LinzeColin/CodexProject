import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from KMFA.tools.dingtalk_attendance.healthcheck import build_config_status
from KMFA.tools.dingtalk_attendance.notifier_dingtalk import (
    build_signed_robot_url,
    send_group_robot_markdown,
)
from KMFA.tools.dingtalk_attendance.report_renderer import (
    MANAGEMENT_REPORT_SECTIONS,
    HR_REPORT_SECTIONS,
)
from KMFA.tools.dingtalk_attendance.dws_attendance import collect_org_attendance
from KMFA.tools.dingtalk_attendance.run_attendance import build_run_plan, dispatch_reports_to_robot
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
            "web" + "hook=https://example.invalid",
            "https://oapi.dingtalk.com/robot/" + "send?access" + "_token=abc",
        ]

        for payload in bad_payloads:
            with self.subTest(payload=payload):
                findings = scan_payload_for_sensitive_text(payload)
                self.assertGreaterEqual(len(findings), 1)

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
            self.assertEqual(sent_titles, ["开明考勤管理报告", "开明考勤 HR 报告"])
            self.assertEqual(len(receipt_payload["messages"]), 2)
            self.assertIn("## 一、总体情况", sent_bodies[0])
            self.assertIn("## 一、异常明细", sent_bodies[1])
            self.assertEqual(receipt_payload["messages"][0]["report"], "management_report")
            self.assertEqual(receipt_payload["messages"][1]["report"], "hr_report")


if __name__ == "__main__":
    unittest.main()
