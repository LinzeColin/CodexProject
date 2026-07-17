import unittest

from KMFA.tools import v015_s14_p3_language_content as language


class TestV015S14P3LanguageContent(unittest.TestCase):
    def test_dictionary_translates_internal_terms(self) -> None:
        contract = language.interface_dictionary_contract()
        self.assertEqual(contract["entry_count"], 14)
        self.assertFalse(contract["professional_terms_default_visible"])
        self.assertFalse(contract["machine_copy_allowed"])
        mapping = {row["internal"]: row["plain_zh"] for row in contract["entries"]}
        self.assertEqual(mapping["hash"], "文件核对标记")
        self.assertEqual(mapping["PENDING"], "待确认")

    def test_default_page_has_no_forbidden_or_machine_copy(self) -> None:
        evidence = language.language_scan_evidence()
        self.assertEqual(evidence["forbidden_term_hit_count"], 0)
        self.assertEqual(evidence["forbidden_ai_copy_hit_count"], 0)
        self.assertEqual(evidence["machine_pattern_hit_count"], 0)
        self.assertFalse(evidence["obvious_ai_or_machine_copy_detected"])

    def test_professional_terms_are_collapsed(self) -> None:
        html = language.render_html()
        self.assertIn("查看专业依据", html)
        self.assertIn("文件指纹（hash）", html)
        self.assertNotIn("<details open", html)
        self.assertNotIn("hash", language.default_visible_text(html))

    def test_money_format_uses_integer_cents(self) -> None:
        self.assertEqual(language.format_money(12_000_000), "¥ 120,000.00")
        self.assertEqual(language.format_money(-1_234_567), "−¥ 12,345.67")
        self.assertEqual(language.format_money(0), "¥ 0.00")
        with self.assertRaises(language.LanguageContentError):
            language.format_money(12.5)  # type: ignore[arg-type]
        with self.assertRaises(language.LanguageContentError):
            language.format_money(True)

    def test_large_money_keeps_exact_value(self) -> None:
        self.assertEqual(
            language.format_money(12_800_000_000, show_large_unit=True),
            "¥ 128,000,000.00（1.28亿元）",
        )

    def test_ratio_date_integer_and_null_formats(self) -> None:
        self.assertEqual(language.format_ratio(9230), "92.30%")
        self.assertEqual(language.format_ratio(-325), "−3.25%")
        self.assertEqual(language.format_integer(128_450), "128,450")
        self.assertEqual(language.format_date("2026-07-16"), "2026年7月16日")
        self.assertEqual(language.format_null("MISSING"), "暂无数据")
        self.assertEqual(language.format_null("NOT_APPLICABLE"), "不适用")

    def test_invalid_date_and_null_fail_closed(self) -> None:
        with self.assertRaises(language.LanguageContentError):
            language.format_date("16/07/2026")
        with self.assertRaises(language.LanguageContentError):
            language.format_null("UNKNOWN_STATE")

    def test_page_report_export_are_consistent(self) -> None:
        contract = language.format_contract()
        self.assertTrue(contract["page_report_export_consistent"])
        self.assertEqual(contract["surface_mismatch_count"], 0)
        self.assertEqual(contract["display_underlying_mismatch_count"], 0)
        for row in contract["cases"]:
            self.assertEqual(row["page_display"], row["report_display"])
            self.assertEqual(row["page_display"], row["export_display"])

    def test_every_screen_has_one_question_and_next_step(self) -> None:
        contract = language.content_density_contract()
        self.assertEqual(contract["screen_count"], 6)
        for screen in contract["screens"]:
            self.assertEqual(screen["main_question_count"], 1)
            self.assertEqual(screen["primary_next_step_count"], 1)
            self.assertGreaterEqual(screen["focus_item_count"], 3)
            self.assertLessEqual(screen["focus_item_count"], 5)
            self.assertLessEqual(screen["initial_content_region_count"], 5)
            self.assertEqual(screen["repeated_conclusion_count"], 0)

    def test_walkthrough_is_explicitly_not_user_research(self) -> None:
        evidence = language.cognitive_walkthrough_evidence()
        self.assertEqual(evidence["method"], "STRUCTURAL_HEURISTIC_NOT_USER_RESEARCH")
        self.assertEqual(evidence["case_count"], 6)
        self.assertEqual(evidence["pass_count"], 6)
        self.assertTrue(
            all(row["estimated_find_time_seconds"] <= 10 for row in evidence["cases"])
        )

    def test_html_has_one_visible_priority_structure(self) -> None:
        html = language.render_html()
        self.assertEqual(len(__import__("re").findall(r"<h1[^>]*data-main-question", html)), 1)
        self.assertEqual(html.count("data-key-number"), 3)
        self.assertEqual(html.count("data-primary-next-step"), 1)
        self.assertNotIn("eyebrow", html)
        self.assertNotIn("gradient(", html)

    def test_public_contract_passes_all_checks(self) -> None:
        result = language.validate_public_contract()
        self.assertEqual(result["total"], 72)
        self.assertEqual(result["passed"], 72)
        self.assertEqual(result["failed"], 0)

    def test_private_and_release_boundaries_remain_closed(self) -> None:
        payload = language.interface_payload()
        self.assertEqual(payload["raw_root_access_count"], 0)
        self.assertFalse(payload["raw_business_content_read"])
        self.assertEqual(payload["live_source_read_count"], 0)
        self.assertEqual(payload["network_request_count"], 0)
        self.assertEqual(payload["real_business_action_count"], 0)
        self.assertFalse(payload["s14_stage_review_started"])
        self.assertFalse(payload["github_upload_performed"])
        self.assertFalse(payload["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
