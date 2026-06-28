from __future__ import annotations

import re
import unittest
from pathlib import Path

from pfi_v02.stage_v021_frontend_contract import (
    STAGE7_TASK_IDS,
    build_v021_stage7_contract,
)


class V021Stage7ClicksafeFeedbackTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        self.css = (self.root / "web" / "styles" / "tokens.css").read_text(encoding="utf-8")
        self.web_source = "\n".join((self.html, self.js, self.css))

    def test_stage7_contract_covers_clicksafe_and_feedback_tasks(self) -> None:
        contract = build_v021_stage7_contract()

        self.assertEqual(contract["schema"], "PFIV021FrontendOptimizationStage7ContractV1")
        self.assertEqual(tuple(contract["task_ids"]), STAGE7_TASK_IDS)
        self.assertIn("V021-P7-S7-T01", contract["task_ids"])
        self.assertIn("V021-P7-S7-T02", contract["task_ids"])
        self.assertEqual(contract["feedback_contract"]["states"], ("progress", "success", "failure"))
        self.assertEqual(contract["feedback_contract"]["visible_labels"], ("进行中", "成功", "失败"))
        self.assertEqual(len(contract["click_safe_contract"]["required_routes"]), 15)
        self.assertIn("/investment?tab=holdings", contract["click_safe_contract"]["required_routes"])

    def test_all_static_buttons_have_button_type_and_click_targets(self) -> None:
        button_tags = re.findall(r"<button\b[^>]*>", self.html)

        self.assertGreaterEqual(len(button_tags), 30)
        for tag in button_tags:
            self.assertIn('type="button"', tag, tag)
        for required in (
            'data-primary-entry="true"',
            "data-command-open",
            "data-task-toggle",
            "data-evidence-toggle",
            "data-settings-open",
            "data-function-action",
            "data-import-review-link",
            "data-holdings-save",
            "data-table-sort",
            "data-table-export",
            "data-command-workspace",
        ):
            self.assertIn(required, self.html)

    def test_unified_feedback_surface_supports_progress_success_and_failure(self) -> None:
        feedback = build_v021_stage7_contract()["feedback_contract"]

        for marker in (feedback["surface_marker"], feedback["toast_marker"], feedback["region_marker"]):
            self.assertIn(marker, self.html)
        self.assertIn('role="status"', self.html)
        self.assertIn('aria-live="polite"', self.html)
        self.assertIn(".action-feedback", self.css)
        self.assertIn('[data-feedback-state="progress"]', self.css)
        self.assertIn('[data-feedback-state="success"]', self.css)
        self.assertIn('[data-feedback-state="failure"]', self.css)
        for required in (
            "const FEEDBACK_STATES",
            'progress: "进行中"',
            'success: "成功"',
            'failure: "失败"',
            "function setActionFeedback",
            "function showToast",
            'setActionFeedback("progress", "正在刷新缓存切片")',
            'showToast("刷新失败 · 已切换到缓存兜底", "failure")',
        ):
            self.assertIn(required, self.js)

    def test_owner_facing_multimodal_delivery_style_is_present(self) -> None:
        for required in (
            'data-uiux-delivery-target="v021_multimodal_feedback"',
            "data-settings-feedback-console",
            "feedback-wave",
            'data-feedback-toggle="haptic"',
            'data-feedback-toggle="sound"',
            'data-feedback-toggle="motion"',
            "data-feedback-test",
            "mobile-bottom-nav",
            "data-mobile-workspace",
            "data-nav-icon",
            "data-nav-hint",
        ):
            self.assertIn(required, self.html)
        for required in (
            "function emitMultimodalFeedback",
            "function vibrateFeedback",
            "function playFeedbackTone",
            "function createRipple",
            "function bindFeedbackToggles",
            "function syncMobileTabs",
            "navigator.vibrate",
            "AudioContext",
        ):
            self.assertIn(required, self.js)
        for required in (
            ".feedback-wave",
            ".toggle-row",
            ".toggle-item",
            ".mobile-bottom-nav",
            ".mobile-tab",
            ".ripple",
            "backdrop-filter",
            "data-nav-hint",
            "grid-template-areas",
            "translateX(calc(100% + 24px))",
            ".top-actions .icon-button",
        ):
            self.assertIn(required, self.css)

    def test_clicksafe_inventory_and_global_button_feedback_are_wired(self) -> None:
        click_safe = build_v021_stage7_contract()["click_safe_contract"]

        for function_name in click_safe["required_functions"]:
            self.assertIn(f"function {function_name}", self.js)
        for required in (
            "function isClickSafeVisible",
            "function clickSafeId",
            "function refreshClickSafeInventory",
            "window.PFI_STAGE7_CLICK_SAFE",
            'window.addEventListener("hashchange"',
            "bindClickSafeFeedback();",
            'button.dataset.clickSafe = "true"',
            'setActionFeedback("progress", `${label} · 正在处理`',
            'setActionFeedback("success", `${label} · 已响应`',
            "function restoreOwnerHomeWorkflow",
            "restoreOwnerHomeWorkflow();",
        ):
            self.assertIn(required, self.js)
        for required_css in (
            "scroll-snap-type: x proximity",
            "min-width: max-content",
            "white-space: nowrap",
            "scroll-snap-align: start",
        ):
            self.assertIn(required_css, self.css)

    def test_stage7_keeps_execution_boundary_and_no_forbidden_actions(self) -> None:
        for forbidden in (
            'data-action="trade"',
            'data-action="pay"',
            'data-action="broker-submit"',
            "broker-submit",
            "live_trade_submission_authorized=true",
            "自动实盘下单=true",
        ):
            self.assertNotIn(forbidden, self.web_source)
        self.assertIn("不做实盘自动下单", self.web_source)


if __name__ == "__main__":
    unittest.main()
