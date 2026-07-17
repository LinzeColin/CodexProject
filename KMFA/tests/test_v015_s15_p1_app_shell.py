from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s15_p1_app_shell as shell


class AppShellKernelTests(unittest.TestCase):
    def test_source_contract_matches_taskpack_phase(self) -> None:
        contract = shell.source_contract()
        self.assertEqual(contract["stage_id"], "S15")
        self.assertEqual(contract["roadmap_phase_id"], "S15-P1")
        self.assertEqual(contract["task_ids"], ["S15P1T01", "S15P1T02", "S15P1T03"])
        self.assertIn("静态 HTML 不算完成。", contract["stop_conditions_zh"])
        self.assertIn("跨主体数据泄露即失败。", contract["stop_conditions_zh"])
        self.assertIn("白屏或静默失败即失败。", contract["stop_conditions_zh"])

    def test_navigation_and_deep_link_contract_are_inherited_exactly(self) -> None:
        self.assertEqual(len(shell.NAV_ITEMS), 7)
        self.assertEqual(len(shell.KNOWN_ROUTES), 18)
        self.assertEqual(shell.KNOWN_ROUTES[0], "/overview")
        self.assertEqual(len(set(shell.KNOWN_ROUTES)), 18)
        self.assertEqual(
            [item["label_zh"] for item in shell.NAV_ITEMS],
            ["经营首页", "项目", "回款", "资金", "税务与政策", "数据更新", "报告"],
        )

    def test_invalid_persisted_context_is_safely_normalized(self) -> None:
        self.assertEqual(shell.normalize_context({"company": "private-company"}), shell.DEFAULT_CONTEXT)
        context = shell.normalize_context(
            {
                "company": "demo-south",
                "period": "2026-Q2",
                "project_status": "attention",
                "report_version": "approved",
            }
        )
        self.assertEqual(context["company"], "demo-south")
        self.assertIn("company=demo-south", shell.context_query(context))
        self.assertIn("report_version=approved", shell.context_query(context))

    def test_each_company_payload_is_explicitly_company_bound(self) -> None:
        item_ids: set[str] = set()
        for option in shell.CONTEXT_OPTIONS["company"]:
            context = {**shell.DEFAULT_CONTEXT, "company": option["value"]}
            payload = shell.public_context_result(context).as_dict()
            shell.validate_public_payload(payload, context)
            self.assertTrue(payload["items"])
            self.assertTrue(all(item["company_id"] == option["value"] for item in payload["items"]))
            current_ids = {item["item_id"] for item in payload["items"]}
            self.assertFalse(item_ids & current_ids)
            item_ids.update(current_ids)

    def test_cross_company_payload_is_rejected(self) -> None:
        requested = {**shell.DEFAULT_CONTEXT, "company": "demo-south"}
        payload = shell.public_context_result(requested).as_dict()
        tampered = copy.deepcopy(payload)
        tampered["items"][0]["company_id"] = "demo-north"
        with self.assertRaisesRegex(shell.ContextError, "cross-company"):
            shell.validate_public_payload(tampered, requested)

    def test_all_four_errors_have_clear_chinese_action(self) -> None:
        self.assertEqual(set(shell.FAULT_CONTRACT), {"network", "parse", "calculation", "permission"})
        for contract in shell.FAULT_CONTRACT.values():
            self.assertTrue(contract["title_zh"])
            self.assertTrue(contract["message_zh"])
            self.assertIn(contract["action_zh"], {"重新加载", "返回经营首页"})

    def test_public_contract_passes_without_private_or_live_access(self) -> None:
        contract = shell.build_contract()
        self.assertEqual(contract["public_check_failed_count"], 0)
        self.assertEqual(contract["public_check_total"], contract["public_check_pass_count"])
        self.assertEqual(contract["raw_root_access_count"], 0)
        self.assertEqual(contract["live_source_read_count"], 0)
        self.assertEqual(contract["external_network_request_count"], 0)
        self.assertEqual(contract["real_business_action_count"], 0)


if __name__ == "__main__":
    unittest.main()
