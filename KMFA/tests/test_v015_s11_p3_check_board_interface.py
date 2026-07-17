from __future__ import annotations

import unittest

from KMFA.tools import v015_s11_p3_check_board_interface as ui


class CheckBoardInterfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = ui.interface_payload()
        self.rows = self.payload["rows"]
        self.leaves = [row for row in self.rows if row["is_leaf"]]

    def test_payload_reuses_s11_p2_hierarchy_without_frontend_status_write(self) -> None:
        self.assertEqual(self.payload["row_count"], 34)
        self.assertEqual(self.payload["leaf_count"], 6)
        self.assertEqual(len(self.payload["root_node_ids"]), 4)
        self.assertFalse(self.payload["frontend_status_mutation_allowed"])
        self.assertTrue(all(row["frontend_status_mutation_allowed"] is False for row in self.rows))
        self.assertTrue(all(row["status_source_zh"] == "系统导入与质量检查结果" for row in self.rows))

    def test_plain_chinese_detail_contains_file_issue_impact_owner_and_next_step(self) -> None:
        for row in self.leaves:
            self.assertTrue(row["file_package_zh"])
            self.assertTrue(row["quality_issue_zh"])
            self.assertTrue(row["report_impact_zh"])
            self.assertTrue(row["owner_role_zh"])
            self.assertTrue(row["next_action_zh"])
            self.assertNotIn("technical", str(row).casefold())

    def test_upload_sync_confirm_and_view_flows_are_routed(self) -> None:
        kinds = {row["action"]["kind"] for row in self.leaves}
        self.assertEqual(kinds, set(ui.ACTION_KINDS))
        for row in self.leaves:
            self.assertIn("label_zh", row["action"])
            self.assertTrue(row["action"]["label_zh"])
            self.assertTrue(row["action"]["intro_zh"])
            self.assertTrue(row["action"]["submit_zh"])

    def test_context_preserves_filters_expansion_scroll_and_focus(self) -> None:
        leaf = self.leaves[2]
        context = {
            "search_text": " 回款 ",
            "status_filters": ["不可使用"],
            "owner_filter": leaf["owner_role_zh"],
            "alert_only": True,
            "expanded_node_ids": self.payload["root_node_ids"][:2],
            "scroll_y": 420,
            "table_scroll_left": 160,
            "focus_node_id": leaf["node_id"],
        }
        normalized = ui.validate_context_state(context, {row["node_id"] for row in self.rows})
        self.assertEqual(normalized["search_text"], "回款")
        self.assertEqual(normalized["status_filters"], ["不可使用"])
        self.assertEqual(normalized["scroll_y"], 420)
        self.assertEqual(normalized["table_scroll_left"], 160)
        self.assertEqual(normalized["focus_node_id"], leaf["node_id"])

    def test_context_rejects_frontend_status_mutation(self) -> None:
        with self.assertRaises(ui.CheckBoardInterfaceError) as raised:
            ui.validate_context_state({"status_override": "已通过"}, {row["node_id"] for row in self.rows})
        self.assertEqual(raised.exception.code, "CONTEXT_STATUS_MUTATION_FORBIDDEN")

    def test_action_request_cannot_change_status_or_raw_source(self) -> None:
        leaf = self.leaves[0]
        context = {
            "search_text": "",
            "status_filters": [],
            "owner_filter": "",
            "alert_only": False,
            "expanded_node_ids": self.payload["root_node_ids"],
            "scroll_y": 0,
            "table_scroll_left": 0,
            "focus_node_id": leaf["node_id"],
        }
        request = ui.create_action_request(leaf["node_id"], context)
        self.assertEqual(request["frontend_status_write_count"], 0)
        self.assertFalse(request["status_change_requested"])
        self.assertFalse(request["raw_source_mutation_requested"])
        self.assertEqual(request["backend_state_fingerprint"], self.payload["backend_state_fingerprint"])

    def test_action_return_keeps_context_and_backend_state_exact(self) -> None:
        leaf = self.leaves[0]
        context = {
            "search_text": "票据",
            "status_filters": [leaf["status_zh"]],
            "owner_filter": leaf["owner_role_zh"],
            "alert_only": leaf["has_alert"],
            "expanded_node_ids": self.payload["root_node_ids"],
            "scroll_y": 360,
            "table_scroll_left": 220,
            "focus_node_id": leaf["node_id"],
        }
        evidence = ui.simulate_action_and_return(leaf["node_id"], context)
        self.assertTrue(evidence["context_exact"])
        self.assertTrue(evidence["backend_state_unchanged"])
        self.assertEqual(evidence["frontend_status_write_count"], 0)

    def test_visual_contract_is_business_blue_readable_and_color_independent(self) -> None:
        visual = ui.visual_contract()
        self.assertTrue(visual["business_blue_primary"])
        self.assertEqual(visual["large_yellow_surface_count"], 0)
        self.assertEqual(visual["large_status_color_surface_count"], 0)
        self.assertEqual(visual["status_color_usage"], "BADGE_ICON_TEXT_ONLY")
        self.assertTrue(visual["contrast_all_pass"])
        self.assertTrue(all(row["ratio"] >= row["minimum"] for row in visual["contrast_pairs"]))
        self.assertFalse(visual["color_only_status_allowed"])

    def test_html_is_self_contained_accessible_and_context_aware(self) -> None:
        html = ui.render_html(self.payload)
        for expected in (
            'lang="zh-CN"',
            'class="skip-link"',
            'role="search"',
            '<table class="matrix">',
            'aria-live="polite"',
            'aria-live="assertive"',
            'aria-expanded=',
            ':focus-visible',
            'prefers-reduced-motion:reduce',
            'sessionStorage.setItem',
            'window.scrollTo',
            'focus_node_id',
            'data-start-action',
            'dataset.completeReturn',
        ):
            self.assertIn(expected, html)
        self.assertNotIn("gradient(", html)
        self.assertNotRegex(html, r'(?:src|href)=["\']https?://')

    def test_public_verification_passes_every_check(self) -> None:
        result = ui.public_verification()
        self.assertEqual(result["accounting"]["failed"], 0)
        self.assertEqual(result["accounting"]["passed"], result["accounting"]["total"])
        self.assertGreaterEqual(result["accounting"]["total"], 60)


if __name__ == "__main__":
    unittest.main()
