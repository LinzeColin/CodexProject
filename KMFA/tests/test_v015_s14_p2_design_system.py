import copy
import unittest

from KMFA.tools import v015_s14_p2_design_system as design


class TestV015S14P2DesignSystem(unittest.TestCase):
    def test_business_blue_tokens_cover_light_and_dark_boundaries(self) -> None:
        contract = design.design_token_contract()
        self.assertEqual(contract["theme_count"], 2)
        self.assertEqual(contract["themes"]["light"]["nav"], "#102F50")
        self.assertEqual(contract["themes"]["light"]["primary"], "#17679B")
        self.assertEqual(contract["themes"]["dark"]["primary"], "#6BC2F2")
        self.assertTrue(contract["light_theme_default"])
        self.assertTrue(contract["dark_theme_optional"])
        self.assertFalse(contract["gradients_allowed"])

    def test_contrast_pairs_all_pass_at_normal_text_threshold(self) -> None:
        evidence = design.contrast_evidence()
        self.assertEqual(evidence["pair_count"], 14)
        self.assertEqual(evidence["pass_count"], 14)
        self.assertEqual(evidence["fail_count"], 0)
        self.assertTrue(all(row["ratio"] >= 4.5 for row in evidence["pairs"]))

    def test_invalid_color_is_rejected(self) -> None:
        with self.assertRaises(design.DesignSystemError):
            design.relative_luminance("blue")

    def test_component_contract_has_all_seven_states_and_feedback(self) -> None:
        contract = design.component_contract()
        self.assertEqual(contract["component_count"], 11)
        self.assertEqual(contract["required_states"], list(design.REQUIRED_COMPONENT_STATES))
        self.assertEqual(contract["full_state_coverage_count"], 11)
        self.assertEqual(contract["no_feedback_component_count"], 0)
        self.assertEqual(contract["color_only_state_count"], 0)
        for component in contract["components"]:
            self.assertEqual(set(component["states"]), set(design.REQUIRED_COMPONENT_STATES))
            self.assertTrue(component["feedback_required"])
            self.assertTrue(component["keyboard_operable"])

    def test_status_semantics_use_symbol_and_chinese_text(self) -> None:
        for row in design.STATUS_SEMANTICS:
            self.assertTrue(row["symbol"])
            self.assertTrue(row["label_zh"])
        contract = design.component_contract()
        self.assertEqual(
            contract["status_has_symbol_and_text_count"],
            contract["status_semantic_count"],
        )

    def test_motion_is_short_purposeful_and_reduced_motion_safe(self) -> None:
        contract = design.motion_contract()
        self.assertLessEqual(contract["maximum_motion_duration_ms"], 220)
        self.assertFalse(contract["layout_animation_allowed"])
        self.assertFalse(contract["autoplay_loop_allowed"])
        self.assertEqual(contract["blocking_animation_count"], 0)
        self.assertEqual(contract["decorative_animation_count"], 0)
        self.assertTrue(contract["reduced_motion_supported"])
        self.assertEqual(contract["reduced_motion_content_loss_count"], 0)

    def test_chart_and_status_rules_do_not_rely_on_color_alone(self) -> None:
        contract = design.design_token_contract()
        self.assertFalse(contract["chart"]["color_only_series_allowed"])
        self.assertTrue(contract["chart"]["accessible_data_table_required"])
        self.assertGreaterEqual(len(contract["chart"]["series_distinction"]), 3)
        self.assertLessEqual(contract["warning_area_limit_bps"], 800)

    def test_rendered_html_contains_real_business_ui_and_no_external_resources(self) -> None:
        html = design.render_html()
        for token in (
            'aria-label="主要导航"',
            'id="theme-toggle"',
            'class="data-table"',
            '<dialog id="follow-dialog"',
            'id="detail-drawer"',
            'id="toast"',
            'class="empty"',
            'prefers-reduced-motion:reduce',
        ):
            self.assertIn(token, html)
        self.assertNotIn("gradient(", html)
        self.assertNotRegex(html, r'(?:src|href)=["\']https?://')

    def test_payload_preserves_s14_p1_navigation_and_closes_side_effects(self) -> None:
        payload = design.interface_payload()
        self.assertEqual(
            [row["label_zh"] for row in payload["navigation"]],
            ["经营首页", "项目", "回款", "资金", "税务与政策", "数据更新", "报告"],
        )
        self.assertEqual(payload["raw_root_access_count"], 0)
        self.assertFalse(payload["raw_business_content_read"])
        self.assertEqual(payload["live_source_read_count"], 0)
        self.assertEqual(payload["real_business_action_count"], 0)
        self.assertFalse(payload["github_upload_performed"])
        self.assertFalse(payload["app_reinstall_performed"])

    def test_public_verification_passes(self) -> None:
        result = design.public_verification()
        self.assertEqual(result["accounting"], {"total": 60, "passed": 60, "failed": 0})
        self.assertEqual(result["failed_checks"], [])


if __name__ == "__main__":
    unittest.main()
