from __future__ import annotations

import importlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
STAGE8_DIR = ROOT / "reports" / "pfi_v024" / "stage_8"
REVIEW_DIR = STAGE8_DIR / "whole_stage_review"
EXPECTED_PHASE_IDS = ["8.1", "8.2", "8.3"]
EXPECTED_PRIMARY_ENTRIES = [
    "首页总览",
    "账户与资产",
    "账本流水",
    "投资管理",
    "消费管理",
    "数据源与上传",
    "建议与复盘",
    "报告与洞察",
    "市场与研究",
    "设置",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_stage8_module():
    return importlib.import_module("pfi_v02.stage_v024_stage8_e2e_acceptance")


class TestV024Stage8WholeReviewContract(unittest.TestCase):
    def test_whole_stage_review_contract_is_bounded_and_non_upload(self) -> None:
        stage8 = load_stage8_module()
        self.assertTrue(hasattr(stage8, "build_v024_stage8_whole_review_contract"))

        contract = stage8.build_v024_stage8_whole_review_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 8")
        self.assertEqual(contract["stage_name"], "端到端浏览器与 app 验收")
        self.assertEqual(contract["review_id"], "stage_8_whole_review")
        self.assertEqual(contract["current_run_unit"], "Stage 8 whole-stage review")
        self.assertTrue(contract["current_run_only"])
        self.assertEqual(contract["reviewed_phase_ids"], EXPECTED_PHASE_IDS)
        self.assertTrue(contract["phase_8_1_required"])
        self.assertTrue(contract["phase_8_2_required"])
        self.assertTrue(contract["phase_8_3_required"])
        self.assertTrue(contract["phase_8_3_user_confirmation_required"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertFalse(contract["stage_9_started"])
        self.assertFalse(contract["app_bundle_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertFalse(contract["formal_fake_financial_data_allowed"])
        self.assertIn("GitHub main upload", contract["explicitly_not_done"])
        self.assertIn("Stage 9 regression freeze", contract["explicitly_not_done"])

    def test_whole_stage_review_artifacts_exist_and_show_pass_after_user_confirmation(self) -> None:
        expected_files = [
            ROOT / "docs" / "pfi_v024" / "STAGE8_WHOLE_STAGE_REVIEW.md",
            REVIEW_DIR / "evidence.json",
            REVIEW_DIR / "terminal.log",
            REVIEW_DIR / "changed_files.txt",
            REVIEW_DIR / "risk_and_rollback.md",
        ]
        for path in expected_files:
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 0, str(path))

        evidence = read_json(REVIEW_DIR / "evidence.json")
        self.assertEqual(evidence["schema"], "PFIV024Stage8WholeReviewEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["source_package_version"], "v0.2.3-repair")
        self.assertEqual(evidence["stage"], "Stage 8")
        self.assertEqual(evidence["review_id"], "stage_8_whole_review")
        self.assertEqual(evidence["current_run_unit"], "Stage 8 whole-stage review")
        self.assertTrue(evidence["current_run_only"])
        self.assertEqual(evidence["status"], "pass")
        self.assertTrue(evidence["stage_8_candidate_complete"])
        self.assertTrue(evidence["stage_8_whole_review_complete"])
        self.assertTrue(evidence["phase_8_3_user_confirmed"])
        self.assertEqual(evidence["user_confirmation_source"], "chat_reply_1")
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["stage_9_started"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])

    def test_review_binds_phase_evidence_browser_screenshots_and_manual_acceptance(self) -> None:
        phase81 = read_json(STAGE8_DIR / "phase_8_1" / "evidence.json")
        phase82 = read_json(STAGE8_DIR / "phase_8_2" / "evidence.json")
        phase83 = read_json(STAGE8_DIR / "phase_8_3" / "evidence.json")
        auto_browser = read_json(STAGE8_DIR / "phase_8_1" / "browser_validation.json")
        screenshot_browser = read_json(STAGE8_DIR / "phase_8_2" / "browser_validation.json")
        screenshot_index = read_json(STAGE8_DIR / "phase_8_2" / "screenshot_index.json")
        app_entry = read_json(STAGE8_DIR / "phase_8_2" / "app_entry_validation.json")
        evidence = read_json(REVIEW_DIR / "evidence.json")

        self.assertEqual(evidence["reviewed_phase_ids"], EXPECTED_PHASE_IDS)
        self.assertEqual(evidence["phase_statuses"], {
            "phase_8_1": "candidate_pass",
            "phase_8_2": "candidate_pass",
            "phase_8_3": "user_confirmed",
        })
        self.assertEqual(phase81["status"], "candidate_pass")
        self.assertEqual(phase82["status"], "candidate_pass")
        self.assertEqual(phase83["status"], "ready_for_user_acceptance")
        self.assertEqual(auto_browser["status"], "pass")
        self.assertEqual(screenshot_browser["status"], "pass")
        self.assertEqual(screenshot_index["status"], "pass")
        self.assertEqual(app_entry["status"], "pass")
        self.assertTrue(auto_browser["route_click_test_passed"])
        self.assertTrue(auto_browser["entry_version_test_passed"])
        self.assertTrue(auto_browser["data_state_test_passed"])
        self.assertTrue(auto_browser["report_center_test_passed"])
        self.assertEqual(auto_browser["console_errors"], [])
        self.assertEqual(auto_browser["page_errors"], [])
        self.assertEqual(auto_browser["http_errors"], [])
        self.assertEqual(screenshot_index["screenshot_count"], 14)
        self.assertEqual(screenshot_index["groups"]["primary_entries"]["count"], 10)
        self.assertEqual(
            [item["label"] for item in screenshot_index["screenshots"] if item["group"] == "primary_entries"],
            EXPECTED_PRIMARY_ENTRIES,
        )
        self.assertTrue(screenshot_browser["desktop_light_ui"])
        self.assertEqual(screenshot_browser["mobile_horizontal_overflow_px"], 0)
        self.assertTrue(app_entry["app_localhost_same_bundle_hash"])
        self.assertTrue(app_entry["downloads_app_points_to_current_checkout"])

    def test_stop_conditions_and_review_findings_are_fixed_before_upload(self) -> None:
        evidence = read_json(REVIEW_DIR / "evidence.json")
        stop_conditions = evidence["stop_condition_audit"]
        findings = evidence["review_findings"]

        self.assertEqual(stop_conditions["route_or_history_failure"], "absent")
        self.assertEqual(stop_conditions["entry_version_mismatch"], "absent")
        self.assertEqual(stop_conditions["false_financial_zero_visible"], "absent")
        self.assertEqual(stop_conditions["report_center_missing_required_fields"], "absent")
        self.assertEqual(stop_conditions["screenshot_evidence_missing"], "absent")
        self.assertEqual(stop_conditions["mobile_horizontal_overflow"], "absent")
        self.assertEqual(stop_conditions["manual_acceptance_missing"], "absent")
        self.assertEqual(stop_conditions["forbidden_financial_data_added"], "absent")
        self.assertEqual(stop_conditions["stage_9_started_before_upload"], "absent")

        self.assertGreaterEqual(len(findings), 3)
        for finding in findings:
            self.assertIn(finding["severity"], {"P1", "P2", "P3"})
            self.assertEqual(finding["status"], "fixed")
            self.assertTrue(finding["fix"])
            self.assertTrue(finding["verification"])

        command_status = {item["cmd"]: item["status"] for item in evidence["commands"]}
        self.assertEqual(command_status["pytest stage8 whole review red run"], "expected_fail")
        self.assertEqual(command_status["pytest stage8 whole review contract"], "pass")
        self.assertEqual(command_status["pytest stage8 phase regression"], "pass")
        self.assertEqual(command_status["python py_compile stage8 contract"], "pass")
        self.assertEqual(command_status["json evidence checks"], "pass")
        self.assertEqual(command_status["changed files reconciliation"], "pass")
        self.assertEqual(command_status["git diff --check -- PFI"], "pass")

        self.assertIn("GitHub main upload", evidence["remaining_gates"])
        self.assertNotIn("Stage 9 regression freeze", evidence["remaining_gates"])
        self.assertIn("Stage 9 regression freeze", evidence["explicitly_not_done"])

    def test_docs_and_status_files_reflect_whole_review_without_upload_or_stage9(self) -> None:
        stage_doc = (ROOT / "docs" / "pfi_v024" / "STAGE8_E2E_ACCEPTANCE.md").read_text(encoding="utf-8")
        review_doc = (ROOT / "docs" / "pfi_v024" / "STAGE8_WHOLE_STAGE_REVIEW.md").read_text(encoding="utf-8")
        run_contract = (ROOT / "docs" / "pfi_v024" / "RUN_CONTRACT.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        handoff = (ROOT / "HANDOFF.md").read_text(encoding="utf-8")

        self.assertIn("Stage 8 Whole-stage Review", stage_doc)
        self.assertIn("Stage 8 whole-stage review pass", stage_doc)
        self.assertIn("Stage 8 whole-stage review - 复审并解决暴露问题", run_contract)
        self.assertIn("Stage 8 whole-stage review pass", readme)
        self.assertIn("Stage 8 whole-stage review pass", handoff)
        self.assertIn("GitHub main upload 仍未执行", review_doc)
        self.assertIn("Stage 9 未开始", review_doc)
        self.assertNotIn("GitHub main uploaded", stage_doc)
        self.assertNotIn("Stage 9 started", stage_doc)


if __name__ == "__main__":
    unittest.main()
