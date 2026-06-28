from __future__ import annotations

import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class TestV022ReviewStage13(unittest.TestCase):
    def test_stage13_payload_is_triggered_review_not_goal_closeout(self) -> None:
        post_review = importlib.import_module("pfi_v02.stage_v022_post_review")
        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        payload = post_review.build_stage13_post_review_payload(governance.load_v022_parameter_catalog())

        self.assertEqual(payload["schema"], "PFIV022Stage13PostReviewPayloadV2")
        self.assertEqual(payload["trigger_condition"], post_review.STAGE13_OWNER_TRIGGER)
        self.assertTrue(payload["stage13_ready_for_overall_review"])
        self.assertFalse(payload["stage13_ready_for_goal_closeout"])
        self.assertTrue(payload["overall_project_review_deferred"])
        self.assertTrue(payload["github_sync_deferred"])
        self.assertTrue(payload["app_entry_reinstall_deferred"])
        self.assertEqual(payload["stage13_review_summary"]["path"], "PFI/reports/pfi_v022_stage13_review_summary.md")
        self.assertNotIn("PFI/reports/pfi_v022_summary.md", payload["ticket"]["scope_files"])

    def test_stage13_has_own_summary_and_does_not_repollute_stage12_summary(self) -> None:
        stage12_summary = read_text("reports/pfi_v022_summary.md")
        stage13_summary = read_text("reports/pfi_v022_stage13_review_summary.md")

        for forbidden in (
            "S13-P1-T1",
            "S13-P1-T2",
            "S13-P1-T3",
            "Stage 13 目标测试",
            "Stage 0-13",
            "pfi-v022-stage13-app-verified",
        ):
            with self.subTest(stage12_forbidden=forbidden):
                self.assertNotIn(forbidden, stage12_summary)

        for required in (
            "v0.2.2 Stage 13 复审摘要",
            "本轮只复审解决 Stage 13",
            "S13-P1-T1",
            "S13-P1-T2",
            "S13-P1-T3",
            "整体项目复审解决不在本轮实现",
            "GitHub 同步不在本轮执行",
            "app 入口重装不在本轮执行",
            "tests/test_v022_review_stage13.py",
            "Stage 0-13 v0.2.2 相关回归",
        ):
            with self.subTest(stage13_required=required):
                self.assertIn(required, stage13_summary)

    def test_stage13_docs_record_current_review_boundaries(self) -> None:
        docs = (
            "docs/pfi_v022/STAGE13_POST_REVIEW.md",
            "docs/pfi_v022/DOWNLOADS_CLEANUP_STAGE13.md",
            "review_queue/codex_review_stage13_owner_specified_20260628.md",
            "docs/pfi_v022/reviews/STAGE13_REVIEW_20260629.md",
            "开发记录.md",
            "HANDOFF.md",
            "README.md",
        )
        required = (
            "本轮只复审解决 Stage 13",
            "整体项目复审解决不在本轮实现",
            "GitHub 同步不在本轮执行",
            "app 入口重装不在本轮执行",
            "禁止全仓无差别扫描",
            "不联网",
            "不调用外部 LLM",
            "阻塞项数量：`0`",
        )
        for path in docs:
            text = read_text(path)
            for term in required:
                with self.subTest(path=path, term=term):
                    self.assertIn(term, text)

    def test_stage13_downloads_cleanup_is_scoped_and_sources_are_preserved(self) -> None:
        post_review = importlib.import_module("pfi_v02.stage_v022_post_review")
        manifest = read_text("docs/pfi_v022/DOWNLOADS_CLEANUP_STAGE13.md")
        archive = ROOT / "docs" / "pfi_v022" / "downloads_cleanup" / "PFI_V022_PRE_CANONICAL_SYNC_ARCHIVE_20260628.tar.gz"

        self.assertTrue(archive.exists())
        self.assertGreater(archive.stat().st_size, 0)
        for candidate in post_review.STAGE13_DOWNLOADS_CLEANUP_CANDIDATES:
            with self.subTest(candidate=candidate):
                self.assertFalse((DOWNLOADS / candidate).exists())
                self.assertIn(candidate, manifest)

        self.assertTrue((DOWNLOADS / "PFI.app").exists())
        for source_name in (
            "PFI_v0.2.2_Codex_Task_Pack_zh.md",
            "PFI_v0.2.2_Stage_Phase_Task_Roadmap_zh.md",
            "PFI_v0.2.2_E2E_logic_optimization_package.zip",
        ):
            with self.subTest(source_name=source_name):
                self.assertIn(source_name, manifest)

    def test_stage13_review_report_exists_with_current_validation_scope(self) -> None:
        report = ROOT / "docs" / "pfi_v022" / "reviews" / "STAGE13_REVIEW_20260629.md"
        self.assertTrue(report.exists(), "Stage 13 复审报告缺失")
        text = report.read_text(encoding="utf-8")

        for required in (
            "v0.2.2 Stage 13 复审并解决",
            "本轮只复审解决 Stage 13",
            "Stage 13 目标 + 复审测试",
            "Stage 0-13 v0.2.2 相关回归",
            "pfi_stage13_review_recheck",
            "不标记整体 goal 完成",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
