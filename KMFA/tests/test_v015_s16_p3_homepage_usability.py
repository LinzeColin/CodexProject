from __future__ import annotations

import unittest

from KMFA.tools import v015_s16_p1_homepage as homepage
from KMFA.tools import v015_s16_p3_homepage_usability as usability


class HomepageUsabilityTests(unittest.TestCase):
    def test_source_contract_matches_taskpack_s16_p3(self) -> None:
        source = usability.source_contract()
        self.assertEqual(source["roadmap_phase_id"], "S16-P3")
        self.assertEqual(source["phase_name_zh"], "首页人类可用验收")
        self.assertEqual(source["task_ids"], ["S16P3T01", "S16P3T02", "S16P3T03"])
        self.assertEqual(source["acceptance_zh"], ["成功率达到验收标准。", "高频任务点击数受控。", "无假数据、无误导。"])

    def test_six_unprimed_recognition_cases_reach_full_internal_threshold(self) -> None:
        cases = usability.ten_second_cases()
        self.assertEqual(len(cases), 6)
        self.assertTrue(all(row["time_limit_seconds"] == 10 for row in cases))
        self.assertTrue(all(row["instruction_read_before_test"] is False for row in cases))
        self.assertEqual(usability.recognition_success_bps(6, 6), 10_000)
        self.assertGreaterEqual(10_000, usability.TEN_SECOND_SUCCESS_THRESHOLD_BPS)

    def test_ready_snapshot_names_status_priorities_and_next_step(self) -> None:
        value = usability.enhance_homepage_snapshot(homepage.homepage_snapshot())
        self.assertEqual(value["scan_status"], "ATTENTION")
        self.assertIn("可用资金", value["scan_summary_zh"])
        self.assertIn("预计净流入", value["scan_summary_zh"])
        self.assertIn("先处理回款", value["scan_summary_zh"])
        self.assertEqual(value["priority_preview_count"], 3)
        self.assertEqual(value["priority_preview"][0]["domain"], "COLLECTION")
        self.assertIsInstance(value["net_flow_cents"], int)

    def test_partial_snapshot_refuses_to_infer_operating_status(self) -> None:
        value = usability.enhance_homepage_snapshot(homepage.homepage_snapshot(data_state="partial"))
        self.assertEqual(value["scan_status"], "INCOMPLETE")
        self.assertIn("当前不判断经营状态", value["scan_summary_zh"])
        self.assertFalse(value["complete_real_business_conclusion_allowed"])

    def test_three_critical_routes_are_one_click_and_known(self) -> None:
        paths = usability.critical_task_paths()
        self.assertEqual({row["target_route"] for row in paths}, {"/projects", "/collections", "/reports"})
        self.assertTrue(all(row["max_clicks"] == 1 for row in paths))
        self.assertTrue(all(row["target_route"] in homepage.app_shell.KNOWN_ROUTES for row in paths))
        self.assertTrue(all(row["dead_end_allowed"] is False for row in paths))

    def test_empty_error_and_stale_states_fail_closed(self) -> None:
        for state in usability.FAULT_STATES:
            value = usability.fault_state_response(state)
            self.assertFalse(value["allowed"])
            self.assertEqual(value["displayed_business_value_count"], 0)
            self.assertEqual(value["fake_business_value_count"], 0)
            self.assertFalse(value["blank_page_allowed"])
            self.assertTrue(value["state_contract"]["reason_zh"])
            self.assertTrue(value["state_contract"]["impact_zh"])
            self.assertTrue(value["state_contract"]["action_zh"])

    def test_empty_does_not_turn_missing_into_zero(self) -> None:
        value = usability.fault_state_response("empty")
        self.assertIn("不会用 0", value["state_contract"]["impact_zh"])
        self.assertEqual(value["summary_metrics"], [])

    def test_error_has_retry_and_stale_is_explicit(self) -> None:
        error = usability.fault_state_response("error")["state_contract"]
        stale = usability.fault_state_response("stale")["state_contract"]
        self.assertEqual(error["action_zh"], "重新加载")
        self.assertIn("已过期", stale["title_zh"])

    def test_invalid_counts_and_states_are_rejected(self) -> None:
        for args in ((-1, 6), (7, 6), (1, 0), (True, 1)):
            with self.assertRaises(usability.HomepageUsabilityError):
                usability.recognition_success_bps(*args)
        with self.assertRaises(usability.HomepageUsabilityError):
            usability.fault_state_response("unknown")

    def test_all_public_checks_pass_without_external_study_claim(self) -> None:
        value = usability.build_contract()
        self.assertEqual(value["public_check_total"], 55)
        self.assertEqual(value["public_check_pass_count"], 55)
        self.assertEqual(value["public_check_failed_count"], 0)
        self.assertEqual(value["external_human_participant_count"], 0)
        self.assertFalse(value["external_human_study_claimed"])
        self.assertEqual(value["raw_root_access_count"], 0)
        self.assertEqual(value["real_business_action_count"], 0)


if __name__ == "__main__":
    unittest.main()
