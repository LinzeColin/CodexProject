from __future__ import annotations

import unittest
from pathlib import Path

from pfi_os.application.homepage_summary import empty_homepage_summary
from pfi_v02.stage_v021_frontend_contract import (
    STAGE2_TASK_IDS,
    build_v021_stage2_contract,
)


class V021Stage2CopyCleanupContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        self.web_source = self.html + "\n" + self.js

    def test_stage2_contract_covers_all_copy_cleanup_tasks(self) -> None:
        contract = build_v021_stage2_contract()

        self.assertEqual(contract["schema"], "PFIV021FrontendOptimizationStage2ContractV1")
        self.assertEqual(tuple(contract["task_ids"]), STAGE2_TASK_IDS)
        self.assertIn("全局用户可见文案中文化", contract["acceptance"][0])
        self.assertIn("不出现运行边界", contract["acceptance"][1])
        self.assertIn("真实响应式布局", contract["acceptance"][2])

    def test_web_shell_removes_known_visible_english_delivery_noise(self) -> None:
        contract = build_v021_stage2_contract()

        for forbidden in contract["forbidden_visible_english_terms"]:
            self.assertNotIn(forbidden, self.web_source, forbidden)
        for required in contract["required_visible_chinese_terms"]:
            self.assertIn(required, self.web_source, required)
        for forbidden in ("使用限制", "隐私边界", "不做实盘自动下单", "只做研究", "不连接券商", "不提交订单"):
            self.assertNotIn(forbidden, self.web_source, forbidden)

    def test_web_shell_has_no_running_boundary_or_preview_modules(self) -> None:
        contract = build_v021_stage2_contract()

        for forbidden in contract["forbidden_boundary_ui_terms"]:
            self.assertNotIn(forbidden, self.web_source, forbidden)
        for forbidden in contract["forbidden_preview_terms"]:
            self.assertNotIn(forbidden, self.web_source, forbidden)
        self.assertNotIn("<iframe", self.html.lower())
        self.assertNotIn("pfi_os_delivery_stage1_clicksafe", self.web_source)

    def test_dynamic_homepage_evidence_drawer_is_chinese_readable(self) -> None:
        summary = empty_homepage_summary()
        drawer = summary["evidence_drawer"]
        text = "\n".join(str(value) for value in drawer.values())

        self.assertIn("第 6 阶段", drawer["title"])
        self.assertIn("第 5 阶段", drawer["title"])
        self.assertIn("第 4 阶段", drawer["title"])
        self.assertIn("任务包验收门禁", drawer["Evidence"])
        self.assertIn("复核状态=已记录", drawer["Parameters"])
        for forbidden in (
            "Stage 6",
            "Stage 5",
            "Stage 4",
            "synthetic",
            "read-only",
            "TaskPack",
            "acceptance gates",
            "live_trade_submission_authorized=false",
            "实盘",
            "只读",
            "交易密码",
        ):
            self.assertNotIn(forbidden, text, forbidden)


if __name__ == "__main__":
    unittest.main()
