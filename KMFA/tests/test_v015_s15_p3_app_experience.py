from __future__ import annotations

import unittest

from KMFA.tools import v015_s15_p1_app_shell as app_shell
from KMFA.tools import v015_s15_p3_app_experience as kernel


class AppExperienceKernelTests(unittest.TestCase):
    def test_source_contract_matches_s15_p3_taskpack(self) -> None:
        source = kernel.source_contract()
        self.assertEqual(source["roadmap_phase_id"], "S15-P3")
        self.assertEqual(source["task_ids"], ["S15P3T01", "S15P3T02", "S15P3T03"])
        self.assertEqual(source["task_names_zh"], ["实现搜索与最近访问", "实现通知中心和待办", "实现偏好设置"])
        self.assertIn("敏感结果不得泄露。", source["stop_conditions_zh"])

    def test_search_covers_project_customer_report_and_todo(self) -> None:
        self.assertEqual(set(kernel.SEARCH_KINDS), {"PROJECT", "CUSTOMER", "REPORT", "TODO"})
        self.assertEqual({item["kind"] for item in kernel.SEARCH_CATALOG}, set(kernel.SEARCH_KINDS))
        self.assertTrue(all(item["route"] in app_shell.KNOWN_ROUTES for item in kernel.SEARCH_CATALOG))

    def test_search_results_include_source_and_action(self) -> None:
        result = kernel.search_results(
            user_id="demo-owner", role_id="management", company_id="demo-north", query="报告"
        )
        self.assertTrue(result["allowed"])
        self.assertGreater(result["result_count"], 0)
        self.assertEqual(result["source_bound_result_count"], result["result_count"])
        self.assertTrue(all(item["source_zh"] and item["route"] and item["action_zh"] for item in result["results"]))

    def test_sensitive_search_result_is_filtered_by_role(self) -> None:
        management = kernel.search_results(
            user_id="demo-owner", role_id="management", company_id="demo-north", query="敏感来源"
        )
        finance = kernel.search_results(
            user_id="demo-owner", role_id="finance", company_id="demo-north", query="敏感来源"
        )
        self.assertEqual(management["results"], [])
        self.assertEqual([item["item_id"] for item in finance["results"]], ["SEARCH-TODO-SENSITIVE"])

    def test_search_rejects_cross_company_identity_without_leaking_results(self) -> None:
        result = kernel.search_results(
            user_id="demo-finance", role_id="finance", company_id="demo-south", query="项目"
        )
        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason_code"], "COMPANY_NOT_GRANTED")
        self.assertEqual(result["results"], [])

    def test_recent_items_are_rechecked_against_current_permission(self) -> None:
        result = kernel.recent_snapshot(
            user_id="demo-owner",
            role_id="management",
            company_id="demo-north",
            item_ids=["SEARCH-TODO-SENSITIVE", "SEARCH-REPORT-MONTHLY"],
        )
        self.assertTrue(result["permission_rechecked"])
        self.assertEqual([item["item_id"] for item in result["items"]], ["SEARCH-REPORT-MONTHLY"])

    def test_recent_record_rejects_invisible_item(self) -> None:
        denied = kernel.record_recent_decision(
            user_id="demo-owner", role_id="management", company_id="demo-north", item_id="SEARCH-TODO-SENSITIVE"
        )
        self.assertFalse(denied["allowed"])
        self.assertIsNone(denied["item_id"])
        self.assertEqual(denied["other_user_write_count"], 0)

    def test_notifications_cover_all_categories_and_every_item_has_action(self) -> None:
        finance = kernel.notification_snapshot(user_id="demo-owner", role_id="finance", company_id="demo-north")
        self.assertEqual({item["category"] for item in finance["items"]}, {"DATA_UPDATE", "DIFFERENCE", "REPORT", "RISK"})
        self.assertTrue(finance["all_items_have_action"])
        self.assertTrue(all(item["route"] in app_shell.KNOWN_ROUTES and item["action_zh"] for item in finance["items"]))

    def test_notifications_are_permission_filtered(self) -> None:
        management = kernel.notification_snapshot(user_id="demo-owner", role_id="management", company_id="demo-north")
        finance = kernel.notification_snapshot(user_id="demo-owner", role_id="finance", company_id="demo-north")
        self.assertEqual(management["notification_count"], 3)
        self.assertEqual(finance["notification_count"], 4)
        self.assertNotIn("DIFFERENCE", {item["category"] for item in management["items"]})

    def test_preference_validation_accepts_only_declared_user_scoped_values(self) -> None:
        allowed = kernel.preference_save_decision(
            actor_user_id="demo-owner",
            target_user_id="demo-owner",
            role_id="management",
            current_company_id="demo-north",
            preferences={"company": "demo-south", "period": "2026-Q2", "table_columns": ["source", "status"], "density": "comfortable"},
        )
        self.assertTrue(allowed["allowed"])
        self.assertEqual(allowed["preference_scope"], "CURRENT_USER_ONLY")
        self.assertEqual(allowed["fact_layer_write_count"], 0)
        self.assertEqual(allowed["raw_write_count"], 0)

    def test_preference_rejects_other_user_and_ungranted_company(self) -> None:
        other = kernel.preference_save_decision(
            actor_user_id="demo-owner",
            target_user_id="demo-finance",
            role_id="management",
            current_company_id="demo-north",
            preferences=kernel.default_preferences("demo-finance"),
        )
        ungranted = kernel.preference_save_decision(
            actor_user_id="demo-finance",
            target_user_id="demo-finance",
            role_id="finance",
            current_company_id="demo-north",
            preferences={**kernel.default_preferences("demo-finance"), "company": "demo-south"},
        )
        self.assertEqual((other["allowed"], other["reason_code"]), (False, "OTHER_USER_PREFERENCE_DENIED"))
        self.assertEqual((ungranted["allowed"], ungranted["reason_code"]), (False, "PREFERRED_COMPANY_NOT_GRANTED"))

    def test_preference_changes_cannot_change_fact_payload(self) -> None:
        before = app_shell.public_context_result(app_shell.DEFAULT_CONTEXT).as_dict()
        decision = kernel.preference_save_decision(
            actor_user_id="demo-owner",
            target_user_id="demo-owner",
            role_id="management",
            current_company_id="demo-north",
            preferences={"company": "demo-west", "period": "2026-H1", "table_columns": [], "density": "comfortable"},
        )
        after = app_shell.public_context_result(app_shell.DEFAULT_CONTEXT).as_dict()
        self.assertTrue(decision["allowed"])
        self.assertEqual(before, after)

    def test_public_contract_has_no_failed_check_or_real_side_effect(self) -> None:
        contract = kernel.build_contract()
        self.assertEqual(contract["public_check_total"], 16)
        self.assertEqual(contract["public_check_pass_count"], 16)
        self.assertEqual(contract["public_check_failed_count"], 0)
        for key in (
            "sensitive_result_leak_count",
            "notification_without_action_count",
            "fact_layer_write_count",
            "other_user_preference_write_count",
            "raw_root_access_count",
            "live_source_read_count",
            "external_network_request_count",
            "real_business_action_count",
        ):
            self.assertEqual(contract[key], 0, key)


if __name__ == "__main__":
    unittest.main()
