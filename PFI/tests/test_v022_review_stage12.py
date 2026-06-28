from __future__ import annotations

import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class TestV022ReviewStage12(unittest.TestCase):
    def test_stage12_payload_is_stage12_only_and_carries_real_evidence(self) -> None:
        delivery = importlib.import_module("pfi_v02.stage_v022_delivery")
        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        payload = delivery.build_stage12_delivery_payload(governance.load_v022_parameter_catalog())

        self.assertTrue(payload["stage12_ready_for_stage13"])
        self.assertTrue(payload["stage12_only"])
        self.assertFalse(payload["stage13_executed_in_stage12"])
        self.assertFalse(payload["downloads_cleanup_executed_in_stage12"])
        self.assertEqual(payload["official_ui_mutation"], "none")
        self.assertEqual(payload["real_evidence"]["real_data_source"], "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv")
        self.assertEqual(payload["real_evidence"]["stage0_12_regression"], "104 passed, 363 subtests passed")

    def test_stage12_summary_does_not_claim_stage13_or_downloads_cleanup(self) -> None:
        summary = read_text("reports/pfi_v022_summary.md")

        required = (
            "本轮只复审解决 Stage 12",
            "Stage 13 后置触发型复核不在本轮实现",
            "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv",
            "104 passed, 363 subtests passed",
            "用户人工复核",
        )
        for term in required:
            with self.subTest(required=term):
                self.assertIn(term, summary)

        forbidden = (
            "S13-P1-T1",
            "S13-P1-T2",
            "S13-P1-T3",
            "Stage 13 目标测试",
            "Stage 0-13",
            "255 passed",
            "Downloads 污染文件夹已清理",
            "归档 SHA-256",
            "pfi-v022-stage13-app-verified",
            "c636b7afbd40923946af77c4987bb5dc1342e924b89e2b3da5bd2128795b6274",
        )
        for term in forbidden:
            with self.subTest(forbidden=term):
                self.assertNotIn(term, summary)

    def test_stage12_report_records_review_rework_and_not_old_broad_claims(self) -> None:
        report = read_text("docs/pfi_v022/STAGE12_DELIVERY_REPORT.md")

        for required in (
            "Stage 12 复审修正",
            "本轮只复审解决 Stage 12",
            "Stage 12 目标 + 复审测试",
            "Stage 0-12 v0.2.2 相关回归",
            "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv",
            "本地审查 HTML 不进入正式运行页面",
            "不清理或迁移 Downloads 污染文件夹",
        ):
            with self.subTest(required=required):
                self.assertIn(required, report)

        for forbidden in (
            "完整 PFI pytest：`250 passed`",
            "macOS app 入口轻量验收：`29 pass",
            "/tmp/pfi-v022-stage12-app-verified.png",
            "/tmp/pfi-v022-stage12-html-verified.png",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, report)

    def test_stage12_review_report_exists_with_validation_scope(self) -> None:
        report = ROOT / "docs" / "pfi_v022" / "reviews" / "STAGE12_REVIEW_20260629.md"
        self.assertTrue(report.exists(), "Stage 12 复审报告缺失")
        text = report.read_text(encoding="utf-8")

        for required in (
            "v0.2.2 Stage 12 复审并解决",
            "本轮只复审解决 Stage 12",
            "Stage 13 后置触发型复核不在本轮实现",
            "本地审查 HTML 不进入正式运行页面",
            "tests/test_v022_review_stage12.py",
            "Stage 0-12 v0.2.2 相关回归",
            "pfi_stage12_review_recheck",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_stage12_review_html_is_not_linked_from_official_runtime_ui(self) -> None:
        index_html = read_text("web/index.html")
        streamlit_app = read_text("src/pfi_os/app/streamlit_app.py")

        for text in (index_html, streamlit_app):
            with self.subTest(surface="official_runtime_ui"):
                self.assertNotIn("pfi_v022_logic_review", text)
                self.assertNotIn("STAGE12_DELIVERY_REPORT", text)
                self.assertNotIn("Stage 12 - 文档同步与交付", text)


if __name__ == "__main__":
    unittest.main()
