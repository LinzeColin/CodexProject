from __future__ import annotations

import unittest
from pathlib import Path

from pfi_v02.stage_v021_frontend_contract import (
    STAGE8_TASK_IDS,
    build_v021_stage8_contract,
)


class V021Stage8FinalAcceptanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.audit = (self.root / "docs" / "pfi_v02" / "STAGE_V021_FINAL_ACCEPTANCE_AUDIT.md").read_text(
            encoding="utf-8"
        )
        self.roadmap = (self.root / "docs" / "pfi_v02" / "STAGE_V021_FRONTEND_OPTIMIZATION.md").read_text(
            encoding="utf-8"
        )
        self.handoff = (self.root / "HANDOFF.md").read_text(encoding="utf-8")
        self.dev_record = (self.root / "开发记录.md").read_text(encoding="utf-8")
        self.feature_list = (self.root / "功能清单.md").read_text(encoding="utf-8")
        self.parameter_file = (self.root / "模型参数文件.md").read_text(encoding="utf-8")
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        self.app_source = (self.root / "src" / "pfi_os" / "app" / "streamlit_app.py").read_text(encoding="utf-8")

    def test_stage8_contract_locks_final_acceptance_tasks(self) -> None:
        contract = build_v021_stage8_contract()

        self.assertEqual(contract["schema"], "PFIV021FrontendOptimizationStage8ContractV1")
        self.assertEqual(tuple(contract["task_ids"]), STAGE8_TASK_IDS)
        self.assertEqual(
            STAGE8_TASK_IDS,
            ("V021-P8-S8-T01", "V021-P8-S8-T02", "V021-P8-S8-T03"),
        )
        self.assertEqual(contract["acceptance_gate"], "PFI-V021-S8-FINAL-ACCEPTANCE-GATE")
        self.assertEqual(len(contract["prior_stage_contracts"]), 8)
        self.assertIn("build_v021_stage7_contract", contract["prior_stage_contracts"])
        self.assertEqual(contract["browser_validation"]["console_errors_allowed"], 0)
        self.assertIn("/tmp/pfi-v021-stage8-final-desktop-verified.png", contract["browser_validation"]["required_screenshots"])
        self.assertIn("main", contract["local_sync_contract"]["github_branch"])

    def test_command_validation_matrix_is_explicit(self) -> None:
        commands = build_v021_stage8_contract()["command_validation"]

        for key in (
            "frontend_contract_suite",
            "full_unittest",
            "web_shell_syntax",
            "governance",
            "diff_check",
            "macos_app_acceptance",
        ):
            self.assertIn(key, commands)
        self.assertIn("test_v021_stage8_final_acceptance", commands["frontend_contract_suite"])
        self.assertIn("unittest discover", commands["full_unittest"])
        self.assertIn("node --check", commands["web_shell_syntax"])
        self.assertIn("validate_project_governance.py --project PFI", commands["governance"])
        self.assertIn("git diff --check -- PFI", commands["diff_check"])

    def test_final_acceptance_audit_and_handoff_cover_stage0_to_stage8(self) -> None:
        for text in (self.audit, self.roadmap, self.handoff):
            self.assertIn("Stage 8", text)
            self.assertIn("V021-P8-S8-T01", text)
            self.assertIn("V021-P8-S8-T02", text)
            self.assertIn("V021-P8-S8-T03", text)
            self.assertIn("PFI-V021-S8-FINAL-ACCEPTANCE-GATE", text)
        for stage in range(0, 9):
            self.assertIn(f"Stage {stage}", self.audit)
        for required in (
            "Stage 0-8 前端合同",
            "完整 PFI 单测",
            "Chrome headless desktop",
            "Chrome headless mobile",
            "macOS app acceptance lite",
            "GitHub main",
            "canonical PFI",
            "本机非必要缓存清理",
        ):
            self.assertIn(required, self.audit)

    def test_three_human_entry_files_are_updated_for_stage8(self) -> None:
        for text in (self.dev_record, self.feature_list, self.parameter_file):
            self.assertIn("S8 - v0.2.1 最终验收", text)
            self.assertIn("V021-P8-S8-T01..T03", text)
            self.assertIn("V021_STAGE8_FINAL_ACCEPTANCE_VERIFIED", text)
            self.assertNotIn("P8 最终验收尚未执行", text)
        self.assertIn("Stage 0-8 合同", self.feature_list)
        self.assertIn("Stage 8 Final Acceptance Parameters", self.parameter_file)
        self.assertIn("PFI-V021-S8-FINAL-ACCEPTANCE-GATE", self.dev_record)

    def test_web_shell_still_contains_required_user_paths_and_no_forbidden_execution(self) -> None:
        self.assertEqual(self.html.count('data-primary-entry="true"'), 15)
        for required in (
            "CNY/AUD=4.69",
            "AUD/CNY=",
            "data-global-search-input",
            "data-upload-import-panel",
            "data-import-review-link",
            "data-holdings-persistence-panel",
            "data-command-workspace",
            "data-action-feedback",
        ):
            self.assertIn(required, self.html)
        for required in (
            "buildClickSafeInventory",
            "bindClickSafeFeedback",
            "applyRouteFromLocation",
            "renderUploadImportPanel",
            "renderHoldingsPersistencePanel",
        ):
            self.assertIn(required, self.js)
        visible_surface = "\n".join((self.html, self.audit))
        for forbidden in (
            'data-action="trade"',
            'data-action="pay"',
            'data-action="broker-submit"',
            "live_trade_submission_authorized=true",
            "trading_password",
            "自动实盘下单=true",
        ):
            self.assertNotIn(forbidden, visible_surface)
        self.assertIn("不执行实盘自动下单", visible_surface)

    def test_macos_app_entry_renders_web_shell_before_legacy_streamlit_upload_panel(self) -> None:
        start = self.app_source.index("def render_pfi_ui_v2_shell()")
        end = self.app_source.index("def main()", start)
        body = self.app_source[start:end]

        web_shell_index = body.index("_render_html_frame(_pfi_web_shell_html(home_summary)")
        upload_panel_index = body.index("render_pfi_local_data_upload_panel()")

        self.assertLess(web_shell_index, upload_panel_index)
        self.assertIn('st.expander("本机真实上传与支付宝账本", expanded=False)', body)


if __name__ == "__main__":
    unittest.main()
