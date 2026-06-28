from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path

from pfi_os.application.homepage_summary import build_homepage_summary
from pfi_v02.stage_v021_runtime_api import (
    build_v021_operational_read_model,
    build_v021_operational_trends,
    import_v021_alipay_payloads,
)


class V021OwnerReworkRealDataUiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        self.css = (self.root / "web" / "styles" / "tokens.css").read_text(encoding="utf-8")
        self.app_source = (self.root / "src" / "pfi_os" / "app" / "streamlit_app.py").read_text(encoding="utf-8")

    def test_home_summary_exposes_real_alipay_history_from_metadatabase(self) -> None:
        summary = build_homepage_summary()
        alipay = summary.get("alipay_import_summary")

        self.assertIsInstance(alipay, dict)
        self.assertEqual(alipay.get("schema"), "PFIAlipayRealImportSummaryV1")
        self.assertEqual(alipay.get("file_count"), 4)
        self.assertEqual(alipay.get("transaction_count"), 8815)
        self.assertEqual(alipay.get("review_count"), 406)
        self.assertEqual(alipay.get("date_start"), "2022-06-06")
        self.assertEqual(alipay.get("date_end"), "2026-06-03")

    def test_streamlit_v2_shell_does_not_append_bottom_upload_patch(self) -> None:
        start = self.app_source.index("def render_pfi_ui_v2_shell()")
        end = self.app_source.index("def main()", start)
        body = self.app_source[start:end]

        self.assertIn("_render_html_frame(_pfi_web_shell_html(home_summary)", body)
        self.assertNotIn("render_pfi_local_data_upload_panel()", body)
        self.assertNotIn("本机真实上传与支付宝账本", body)

    def test_feedback_hub_is_nested_under_settings_not_business_workspace(self) -> None:
        settings_index = self.html.index('data-settings-feedback-console')
        feedback_index = self.html.index('data-feedback-hub')

        self.assertGreater(feedback_index, settings_index)
        self.assertNotIn("data-feedback-hub", self.html[:settings_index])

    def test_web_shell_import_center_and_search_use_real_alipay_numbers(self) -> None:
        self.assertNotIn("IMPORT_BATCH_FIXTURES", self.js)
        self.assertIn("applyAlipayImportSummary", self.js)
        self.assertIn("buildRealAlipayImportBatch", self.js)
        self.assertIn("addRealDataSearchItems", self.js)
        self.assertIn("addRealConsumptionSearchItems", self.js)
        self.assertIn("MetaDatabase 真实支付宝流水", self.js)
        self.assertIn("consumption.has_real_transactions", self.js)
        for token in ("transactionCount", "reviewCount", "dateStart", "dateEnd"):
            self.assertIn(token, self.js)
        self.assertIn("data-nav-index", self.html)

    def test_formal_upload_entry_copy_points_to_real_data_source(self) -> None:
        for required in (
            "data-upload-import-panel",
            "data-upload-input",
            "data-upload-dropzone",
            ".csv,.zip,.xls,.xlsx",
            "/api/imports/alipay",
            "uploadAlipayFilesToBackend",
            "readFileAsBase64",
            "上传中心",
            "导入中心",
            "真实支付宝流水",
            "已接入真实数据",
        ):
            self.assertIn(required, "\n".join((self.html, self.js)))
        for forbidden in (
            "P5-本轮上传-预检",
            "Math.ceil(Number(file.size",
            "recordCount: uploadCenterState.files.reduce",
        ):
            self.assertNotIn(forbidden, self.js)

    def test_function_blocks_hide_stage_labels_and_developer_meta(self) -> None:
        for forbidden in (
            'meta.className = "workflow-meta"',
            "head.appendChild(status)",
            "第 3 阶段：",
            "第 4 阶段：",
            "第 5 阶段：",
            "第 6 阶段：",
            'feature("建议模型", "可用", "第 5 阶段"',
        ):
            self.assertNotIn(forbidden, self.js)
        for required in (
            "ownerVisibleText",
            "renderFeatureCards(workspace.features)",
            "runtimeTarget.textContent = ownerVisibleText(workspace.runtime)",
        ):
            self.assertIn(required, self.js)

    def test_operational_read_model_uses_real_alipay_transactions_for_consumption(self) -> None:
        model = build_v021_operational_read_model()
        consumption = model["consumption"]

        self.assertTrue(consumption["has_real_transactions"])
        self.assertEqual(consumption["source"], "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv")
        self.assertEqual(consumption["transaction_count"], 8815)
        self.assertEqual(consumption["review_count"], 406)
        self.assertEqual(consumption["latest_month"], "2026-06")
        self.assertAlmostEqual(consumption["month_spend_cny"], 7153.98)
        self.assertAlmostEqual(consumption["fixed_spend_cny"], 0.0)
        self.assertAlmostEqual(consumption["flex_spend_cny"], 7153.98)
        self.assertAlmostEqual(consumption["cashflow_forecast_cny"], 13045.93)

        trends = build_v021_operational_trends()
        consumption_trend = trends["consumption"]
        self.assertEqual(consumption_trend["source"], "MetaDatabase 真实支付宝流水")
        self.assertEqual(consumption_trend["periods"], ["最近30天", "本月"])
        month_spend_series = next(item for item in consumption_trend["series"] if item["id"] == "month_spend_cny")
        self.assertEqual(month_spend_series["values"], [13045.93, 7153.98])

    def test_runtime_import_api_writes_owner_real_upload_into_metadatabase(self) -> None:
        raw_file = sorted((self.root.parent / "MetaDatabase" / "PFI" / "alipay_daily" / "raw").glob("*.csv"))[0]
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            result = import_v021_alipay_payloads(
                {
                    "files": [
                        {
                            "name": raw_file.name,
                            "contentBase64": base64.b64encode(raw_file.read_bytes()).decode("ascii"),
                        }
                    ]
                },
                data_home=temp_root / "data_home",
                metadatabase_root=temp_root / "MetaDatabase" / "PFI" / "alipay_daily",
            )

        self.assertEqual(result["schema"], "PFIAlipayLocalImportPreviewV1")
        self.assertEqual(result["file_count"], 1)
        self.assertGreater(result["transaction_count"], 0)
        self.assertGreater(result["review_count"], 0)
        self.assertIn("metadatabase_transactions_path", result)

    def test_mobile_primary_entries_remain_visible_and_scrollable(self) -> None:
        self.assertIn('data-primary-workspaces="10"', self.html)
        self.assertNotIn(".side-nav {\n    display: none;", self.css)
        for required in (
            "grid-template-areas:\n      \"top\"\n      \"nav\"\n      \"main\"",
            "height: 52px;",
            "max-height: 52px;",
            "scroll-snap-type: x proximity",
            "-webkit-overflow-scrolling: touch",
            "height: 42px;",
            ".nav-item {\n    width: auto;",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.css)


if __name__ == "__main__":
    unittest.main()
