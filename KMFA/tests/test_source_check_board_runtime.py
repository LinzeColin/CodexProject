import json
import unittest

from KMFA.tools.source_check_board_runtime import (
    ALLOWED_BOARD_STATUSES,
    REQUIRED_BOARD_COLUMNS,
    SourceCheckBoardRuntimeError,
    build_default_source_check_board_artifacts,
    validate_source_check_board_artifacts,
)


class SourceCheckBoardRuntimeTests(unittest.TestCase):
    def test_default_runtime_covers_s11_p2_required_matrix(self) -> None:
        manifest, rows, render_outputs = build_default_source_check_board_artifacts(
            generated_at="2026-07-01T10:00:00+10:00"
        )
        validate_source_check_board_artifacts(manifest, rows, render_outputs)

        self.assertEqual(manifest["stage_phase"], "S11-P2")
        self.assertEqual(tuple(manifest["required_columns"]), REQUIRED_BOARD_COLUMNS)
        self.assertGreaterEqual(manifest["summary"]["matrix_row_count"], 10)
        self.assertEqual(set(manifest["summary"]["status_counts"]), set(ALLOWED_BOARD_STATUSES))
        self.assertTrue(manifest["interaction"]["status_click_detail_enabled"])
        self.assertTrue(manifest["style_gate"]["blue_gray_surface_dominant"])
        self.assertTrue(manifest["style_gate"]["status_badges_only"])
        self.assertEqual(manifest["style_gate"]["large_yellow_surface_count"], 0)
        self.assertFalse(manifest["stage_scope"]["s11_p3_project_cost_detail_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage11_review_scope_included"])
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["github_upload_allowed"])

    def test_rows_are_public_safe_and_cover_required_dimensions(self) -> None:
        manifest, rows, render_outputs = build_default_source_check_board_artifacts(
            generated_at="2026-07-01T10:00:00+10:00"
        )
        validate_source_check_board_artifacts(manifest, rows, render_outputs)

        for row in rows:
            self.assertEqual(row["record_type"], "source_check_board_row")
            self.assertEqual(row["stage_phase"], "S11-P2")
            self.assertIn(row["status"], ALLOWED_BOARD_STATUSES)
            for required_field in (
                "source_system",
                "business_segment",
                "source_package_ref",
                "entity_ref",
                "account_or_report_ref",
                "frequency",
                "report_impact",
                "handling_rule",
                "next_step",
            ):
                self.assertTrue(row[required_field])
            self.assertFalse(row["contains_raw_business_values"])
            self.assertFalse(row["raw_layer_write_allowed"])
            self.assertFalse(row["business_decision_basis_allowed"])

    def test_rendered_board_html_supports_status_detail_clicks(self) -> None:
        manifest, rows, render_outputs = build_default_source_check_board_artifacts(
            generated_at="2026-07-01T10:00:00+10:00"
        )
        validate_source_check_board_artifacts(manifest, rows, render_outputs)
        html_text = render_outputs["html"]["kmfa_source_check_board"]

        self.assertTrue(html_text.startswith("<!doctype html>"))
        self.assertIn('lang="zh-CN"', html_text)
        self.assertIn("KMFA 数据源检查板", html_text)
        self.assertIn(">KM<", html_text)
        self.assertNotIn(">K<", html_text)
        for column in REQUIRED_BOARD_COLUMNS:
            self.assertIn(column, html_text)
        for status in ALLOWED_BOARD_STATUSES:
            self.assertIn(status, html_text)
        for required_text in ("点击状态查看影响报告和下一步处理", "状态详情", "报告等级 D"):
            self.assertIn(required_text, html_text)
        for forbidden_visible in ("source_ref://", "validator", "manifest", "metadata"):
            self.assertNotIn(forbidden_visible, html_text.lower())
        for forbidden_suffix in (".zip", ".xlsx", ".xls", ".pdf", ".sqlite", ".db"):
            self.assertNotIn(forbidden_suffix, html_text.lower())

    def test_public_payload_has_no_raw_values_private_files_or_credentials(self) -> None:
        manifest, rows, render_outputs = build_default_source_check_board_artifacts(
            generated_at="2026-07-01T10:00:00+10:00"
        )
        payload = json.dumps([manifest, rows, render_outputs], ensure_ascii=False, sort_keys=True)

        for forbidden_text in (
            '"amount_cents":',
            '"amount_yuan":',
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private_csv",
            ".zip",
            ".xlsx",
            ".xls",
            ".pdf",
            ".sqlite",
            ".db",
            "bank_account_number",
            "identity_document_number",
            "password",
            "token",
            "api_key",
            "private_key",
        ):
            self.assertNotIn(forbidden_text, payload)

    def test_validator_rejects_invalid_status_and_large_yellow_surface(self) -> None:
        manifest, rows, render_outputs = build_default_source_check_board_artifacts(
            generated_at="2026-07-01T10:00:00+10:00"
        )
        broken_rows = [dict(row) for row in rows]
        broken_rows[0]["status"] = "黄色预警"
        with self.assertRaises(SourceCheckBoardRuntimeError):
            validate_source_check_board_artifacts(manifest, broken_rows, render_outputs)

        broken_html = {"html": {"kmfa_source_check_board": render_outputs["html"]["kmfa_source_check_board"] + "yellow"}}
        with self.assertRaises(SourceCheckBoardRuntimeError):
            validate_source_check_board_artifacts(manifest, rows, broken_html)


if __name__ == "__main__":
    unittest.main()
