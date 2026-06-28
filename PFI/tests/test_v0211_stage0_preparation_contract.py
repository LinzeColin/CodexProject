from __future__ import annotations

import unittest
from pathlib import Path

from pfi_v02.stage_v0211_ui_recovery import (
    TOTAL_EXECUTION_STAGES,
    VERSION_NAME,
    build_v0211_stage0_contract,
    v0211_default_navigation_labels,
    v0211_stage_ids,
)


class V0211Stage0PreparationContractTest(unittest.TestCase):
    def test_stage0_locks_six_stage_execution_model(self) -> None:
        contract = build_v0211_stage0_contract()

        self.assertEqual(VERSION_NAME, "v0.2.1.1 Product UI Recovery")
        self.assertEqual(contract["stage"], "S0 准备轮")
        self.assertEqual(contract["total_execution_stages"], TOTAL_EXECUTION_STAGES)
        self.assertEqual(TOTAL_EXECUTION_STAGES, 6)
        self.assertEqual(v0211_stage_ids(), ("S0", "S1", "S2", "S3", "S4", "S5"))
        self.assertEqual(contract["one_run_max_stage_count"], 1)
        self.assertTrue(contract["current_stage_only"])
        self.assertIn("Stage is the pursuing-goal run gate", contract["stage_parent_child_rule"])

    def test_stage0_source_files_and_corrections_are_recorded(self) -> None:
        contract = build_v0211_stage0_contract()
        source_paths = {item["path"] for item in contract["source_files"]}

        self.assertIn("/Users/linzezhang/Downloads/v0.2.1.1.rtf", source_paths)
        self.assertIn(
            "/Users/linzezhang/Downloads/pfi_v0.2.1_controlled_ui_rebuild_task_pack_roadmap.md",
            source_paths,
        )
        decisions = "\n".join(item["default_resolution"] for item in contract["decisions"])
        self.assertIn("10 个正式入口", decisions)
        self.assertIn("市场与研究 > 策略实验室", decisions)
        self.assertIn("S3 操作流，S4 持久化，S5 图表与最终验收", decisions)

    def test_navigation_default_uses_latest_rtf_with_legacy_aliases(self) -> None:
        contract = build_v0211_stage0_contract()

        self.assertEqual(len(v0211_default_navigation_labels()), 10)
        self.assertIn("市场与研究", v0211_default_navigation_labels())
        self.assertNotIn("PFI 1.0 兼容入口", v0211_default_navigation_labels())
        self.assertNotIn("V0.2 当前入口", v0211_default_navigation_labels())
        self.assertEqual(contract["legacy_route_aliases"]["市场"], "市场与研究")
        self.assertEqual(contract["legacy_route_aliases"]["研究"], "市场与研究")
        self.assertEqual(contract["legacy_route_aliases"]["策略实验室"], "市场与研究 > 策略实验室")

    def test_stage0_prevents_ui_shell_edits_and_fake_completion(self) -> None:
        contract = build_v0211_stage0_contract()

        self.assertIn("PFI/web/index.html", contract["stage0_forbidden_file_changes"])
        self.assertIn("PFI/web/app/shell.js", contract["stage0_forbidden_file_changes"])
        self.assertIn("PFI/src/pfi_os/app/streamlit_app.py", contract["stage0_forbidden_file_changes"])
        stop_conditions = "\n".join(contract["stage0_stop_conditions"])
        self.assertIn("声明 v0.2.1.1 已完成", stop_conditions)
        self.assertIn("字符串检查", stop_conditions)

    def test_stage0_documents_and_tribase_records_exist(self) -> None:
        root = Path(__file__).resolve().parents[1]
        required_paths = (
            root / "PRODUCT.md",
            root / "docs" / "pfi_v0211" / "SOURCE_TASK_PACK_MANIFEST.md",
            root / "docs" / "pfi_v0211" / "ROADMAP_LOCK.md",
            root / "docs" / "pfi_v0211" / "STAGE0_PREPARATION.md",
            root / "开发记录.md",
            root / "功能清单.md",
            root / "模型参数文件.md",
        )

        for path in required_paths:
            self.assertTrue(path.exists(), path)

        roadmap = (root / "docs" / "pfi_v0211" / "ROADMAP_LOCK.md").read_text(encoding="utf-8")
        stage0 = (root / "docs" / "pfi_v0211" / "STAGE0_PREPARATION.md").read_text(encoding="utf-8")
        self.assertIn("v0.2.1.1 Product UI Recovery", roadmap)
        self.assertIn("每次 run work 最多完成 1 个 Stage", roadmap)
        self.assertIn("当前 v0.2.1 前端优化判定为失败版本", stage0)
        self.assertIn("不修改 `PFI/web/index.html`", stage0)
        self.assertIn("V0211-S0-T01", stage0)

        for name in ("开发记录.md", "功能清单.md", "模型参数文件.md"):
            text = (root / name).read_text(encoding="utf-8")
            self.assertIn("v0.2.1.1 Product UI Recovery", text, name)


if __name__ == "__main__":
    unittest.main()
