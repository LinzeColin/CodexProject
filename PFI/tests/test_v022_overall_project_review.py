from __future__ import annotations

import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class TestV022OverallProjectReview(unittest.TestCase):
    def test_overall_payload_closes_stage_0_to_13_without_redefining_scope(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v022_overall_review")
        payload = module.build_v022_overall_project_review_payload(ROOT)

        self.assertEqual(payload["schema"], "PFIV022OverallProjectReviewPayloadV1")
        self.assertEqual(payload["stage_count"], 14)
        self.assertEqual(payload["stage_sequence"], tuple(f"Stage {index}" for index in range(14)))
        self.assertTrue(all(item["status_zh"] == "已复审解决" for item in payload["stage_status"]))
        self.assertGreaterEqual(payload["data_boundary"]["alipay_raw_file_count"], 4)
        self.assertEqual(payload["data_boundary"]["alipay_normalized_row_count"], 8815)
        self.assertTrue(payload["sync_plan"]["github_sync_required_after_review"])
        self.assertTrue(payload["sync_plan"]["app_entry_reinstall_required_after_sync"])
        self.assertTrue(payload["overall_ready_for_goal_closeout_after_sync"])
        self.assertIn("MetaDatabase/PFI", payload["sync_plan"]["path_limited_scope"])
        self.assertIn("PFI", payload["sync_plan"]["path_limited_scope"])
        self.assertIn("EEI", payload["sync_plan"]["exclude_unrelated_projects"])

    def test_overall_required_artifacts_exist_and_are_chinese_traceable(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v022_overall_review")
        payload = module.build_v022_overall_project_review_payload(ROOT)
        for path in payload["required_artifacts"]:
            with self.subTest(path=path):
                relative = path.removeprefix("PFI/")
                self.assertTrue((ROOT / relative).exists(), f"{path} missing")

        docs = (
            "docs/pfi_v022/reviews/OVERALL_PROJECT_REVIEW_20260629.md",
            "docs/pfi_v022/reviews/TEST_DATA_AUDIT_FINAL_20260629.md",
            "reports/pfi_v022_overall_closeout_summary.md",
            "reports/pfi_v022_goal_closeout_audit.md",
            "README.md",
            "HANDOFF.md",
            "开发记录.md",
            "功能清单.md",
            "模型参数文件.md",
        )
        required = (
            "整体项目复审解决",
            "Stage 0-13",
            "真实 MetaDatabase",
            "8815",
            "正式页面、报告、图表、首页摘要和建议",
            "不得使用 demo/sample/synthetic/fixture/mock/fake/测试样例数据作为验收依据",
            "GitHub main 同步",
            "app 入口重装",
            "阻塞项数量：`0`",
        )
        for path in docs:
            text = read_text(path)
            for term in required:
                with self.subTest(path=path, term=term):
                    self.assertIn(term, text)

    def test_overall_formal_runtime_boundary_is_not_static_string_only(self) -> None:
        summary_path = Path("/tmp/pfi_v022_overall_review_recheck/summary.json")
        review = read_text("docs/pfi_v022/reviews/OVERALL_PROJECT_REVIEW_20260629.md")
        self.assertIn(str(summary_path), review)
        self.assertIn("真实 8501 浏览器复验", review)
        self.assertIn("全局搜索 `406/8815`", review)
        self.assertIn("二级入口点击", review)
        self.assertIn("console/page errors `0`", review)

    def test_overall_test_data_audit_closes_legacy_risk_for_formal_paths(self) -> None:
        audit = read_text("docs/pfi_v022/reviews/TEST_DATA_AUDIT_FINAL_20260629.md")
        self.assertIn("正式运行路径影响：`0`", audit)
        self.assertIn("正式可见页面污染：`0`", audit)
        self.assertIn("legacy 命中仍存在", audit)
        self.assertIn("不作为产品数据源", audit)
        self.assertIn("不作为 Stage 0-13 验收证据", audit)
        self.assertIn("后续拆除队列", audit)


if __name__ == "__main__":
    unittest.main()
