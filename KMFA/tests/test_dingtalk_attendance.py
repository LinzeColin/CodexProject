import json
import unittest
from pathlib import Path

from KMFA.tools.dingtalk_attendance.healthcheck import build_config_status
from KMFA.tools.dingtalk_attendance.report_renderer import (
    MANAGEMENT_REPORT_SECTIONS,
    HR_REPORT_SECTIONS,
)
from KMFA.tools.dingtalk_attendance.run_attendance import build_run_plan
from KMFA.tools.dingtalk_attendance.check_s19_dingtalk_attendance import validate_s19_files
from KMFA.tools.dingtalk_attendance.validate_no_sensitive_git import scan_payload_for_sensitive_text


ROOT = Path(__file__).resolve().parents[1]


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


if __name__ == "__main__":
    unittest.main()
