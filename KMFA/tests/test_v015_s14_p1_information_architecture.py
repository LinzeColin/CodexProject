import copy
import unittest

from KMFA.tools import v015_s14_p1_information_architecture as ia


class TestV015S14P1InformationArchitecture(unittest.TestCase):
    def test_primary_navigation_is_exactly_the_seven_plain_chinese_tasks(self) -> None:
        contract = ia.navigation_contract()
        self.assertEqual(
            [row["label_zh"] for row in contract["items"]],
            ["经营首页", "项目", "回款", "资金", "税务与政策", "数据更新", "报告"],
        )
        self.assertEqual(contract["primary_navigation_count"], 7)
        self.assertFalse(contract["stacked_sidebar_used"])
        self.assertFalse(contract["settings_is_primary_navigation"])

    def test_page_hierarchy_covers_six_types_without_dead_ends_or_cycles(self) -> None:
        result = ia.validate_page_hierarchy()
        self.assertEqual(result["page_node_count"], 18)
        self.assertEqual(result["page_type_count"], 6)
        self.assertEqual(result["dead_end_count"], 0)
        self.assertEqual(result["parent_cycle_count"], 0)
        self.assertEqual(result["previous_task_coverage_bps"], 10_000)

    def test_breadcrumbs_start_at_home_and_end_at_current_page(self) -> None:
        chain = ia.breadcrumbs_for("/projects/demo-project/update")
        self.assertEqual(
            [row["title_zh"] for row in chain],
            ["经营首页", "项目", "示例项目详情", "更新项目资料"],
        )

    def test_missing_parent_is_rejected(self) -> None:
        pages = ia.page_map()
        pages[1]["parent_route"] = "/missing"
        with self.assertRaises(ia.InformationArchitectureError):
            ia.validate_page_hierarchy(pages)

    def test_parent_cycle_is_rejected(self) -> None:
        pages = ia.page_map()
        pages[0]["parent_route"] = "/projects"
        with self.assertRaises(ia.InformationArchitectureError):
            ia.validate_page_hierarchy(pages)

    def test_dead_end_and_self_jump_are_rejected(self) -> None:
        pages = ia.page_map()
        pages[2]["next_routes"] = ()
        with self.assertRaises(ia.InformationArchitectureError):
            ia.validate_page_hierarchy(pages)
        pages = ia.page_map()
        pages[2]["next_routes"] = (pages[2]["route"],)
        with self.assertRaises(ia.InformationArchitectureError):
            ia.validate_page_hierarchy(pages)

    def test_progressive_disclosure_hides_technical_terms_by_default(self) -> None:
        contract = ia.progressive_disclosure_contract()
        self.assertEqual(contract["levels"], list(ia.DISCLOSURE_LEVELS))
        self.assertTrue(contract["management_summary_visible_by_default"])
        self.assertTrue(contract["professional_basis_collapsed_by_default"])
        self.assertTrue(contract["audit_detail_collapsed_by_default"])
        self.assertEqual(contract["default_visible_term_match_count"], 0)
        self.assertEqual(contract["default_visible_term_matches"], [])

    def test_navigation_research_is_explicitly_synthetic_and_all_cases_pass(self) -> None:
        evidence = ia.navigation_research_evidence()
        self.assertIn("不冒充真实用户研究", evidence["method_note_zh"])
        self.assertEqual(evidence["card_sort_case_count"], 21)
        self.assertEqual(evidence["card_sort_pass_count"], 21)
        self.assertEqual(evidence["tree_test_case_count"], 10)
        self.assertEqual(evidence["tree_test_pass_count"], 10)
        self.assertEqual(evidence["failed_count"], 0)

    def test_payload_previous_task_is_bound_to_parent(self) -> None:
        payload = ia.interface_payload()
        for page in payload["pages"]:
            expected = page["parent_route"] or "/overview"
            self.assertEqual(page["previous_task_route"], expected)
            self.assertTrue(page["breadcrumbs"])

    def test_rendered_html_uses_horizontal_navigation_and_no_external_resources(self) -> None:
        html = ia.render_html()
        self.assertIn('aria-label="主要导航"', html)
        self.assertIn("overflow-x:auto", html)
        self.assertNotIn("sidebar", html.casefold())
        self.assertNotRegex(html, r'(?:src|href)=["\']https?://')
        self.assertIn('data-disclosure="professional"', html)
        self.assertIn('data-disclosure="audit"', html)

    def test_public_verification_passes_without_private_or_release_side_effects(self) -> None:
        result = ia.public_verification()
        self.assertEqual(result["failed_checks"], [])
        self.assertEqual(result["accounting"]["failed"], 0)
        self.assertEqual(result["raw_root_access_count"], 0)
        self.assertFalse(result["raw_business_content_read"])
        self.assertEqual(result["live_source_read_count"], 0)
        self.assertEqual(result["real_business_action_count"], 0)
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
