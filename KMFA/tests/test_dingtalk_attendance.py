import json
import unittest
from pathlib import Path

from KMFA.tools.dingtalk_attendance.healthcheck import build_config_status
from KMFA.tools.dingtalk_attendance.report_renderer import (
    MANAGEMENT_REPORT_SECTIONS,
    HR_REPORT_SECTIONS,
)
from KMFA.tools.dingtalk_attendance.dws_attendance import collect_org_attendance
from KMFA.tools.dingtalk_attendance.run_attendance import build_run_plan
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

    def test_config_only_healthcheck_fails_closed_without_live_credentials(self) -> None:
        status = build_config_status(env={})

        self.assertEqual(status["status"], "CONFIG_MISSING")
        self.assertFalse(status["live_collection_allowed"])
        self.assertFalse(status["uses_sample_data"])
        self.assertIn("DINGTALK_APP_KEY", status["missing"])
        self.assertIn("DINGTALK_APP_CREDENTIAL", status["missing"])
        self.assertIn("DINGTALK_CORP_ID", status["missing"])
        self.assertIn("DINGTALK_AGENT_ID", status["missing"])

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


if __name__ == "__main__":
    unittest.main()
