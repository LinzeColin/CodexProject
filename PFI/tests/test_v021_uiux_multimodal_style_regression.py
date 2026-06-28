from __future__ import annotations

import unittest
from pathlib import Path


class V021UiuxMultimodalStyleRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.css = (self.root / "web" / "styles" / "tokens.css").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        self.app_source = (self.root / "src" / "pfi_os" / "app" / "streamlit_app.py").read_text(encoding="utf-8")

    def test_multimodal_feedback_hub_is_settings_only(self) -> None:
        for required in (
            "data-feedback-hub",
            'data-feedback-lane="visual"',
            'data-feedback-lane="haptic"',
            'data-feedback-lane="sound"',
            "视觉状态轨道",
            "触感反馈",
            "声音反馈",
            "data-feedback-meter",
            "data-feedback-event-log",
        ):
            self.assertIn(required, self.html)
        settings_index = self.html.index("data-settings-feedback-console")
        feedback_index = self.html.index("data-feedback-hub")
        self.assertGreater(feedback_index, settings_index)
        self.assertNotIn("data-feedback-hub", self.html[:settings_index])
        for forbidden in (
            "data-owner-feedback-strip",
            "feedback-signal",
            "视觉回弹",
            "触感回馈",
            "声音提示",
        ):
            self.assertNotIn(forbidden, self.html)
        self.assertIn("data-settings-feedback-console hidden", self.html)
        self.assertNotIn("多模态交互反馈", self.html)
        self.assertNotIn("运行反馈控制台", self.html)

    def test_css_is_delivery_style_not_plain_admin_shell(self) -> None:
        for required in (
            "color-scheme: dark;",
            "--pfi-bg: #06111f",
            "--pfi-accent-rose",
            ".feedback-hub",
            ".feedback-lane",
            ".feedback-meter",
            ".feedback-event-log",
            "linear-gradient(135deg",
            "backdrop-filter",
        ):
            self.assertIn(required, self.css)
        for forbidden in (
            ".owner-feedback-strip",
            ".feedback-signal",
            ".feedback-signal::before",
        ):
            self.assertNotIn(forbidden, self.css)

    def test_outer_streamlit_upload_surface_is_chinese_and_not_raw_native_english(self) -> None:
        for required in (
            "def _render_pfi_native_shell_style()",
            "ALIPAY_IMPORT_STATUS_LABELS",
            ".stDeployButton",
            "data-testid=\"stFileUploaderDropzone\"",
            "拖拽 CSV / ZIP 到这里",
            "选择文件",
            "单文件上限 200MB",
            "就绪",
        ):
            self.assertIn(required, self.app_source)
        for forbidden in (
            "Drag and drop files here",
            "Browse files",
        ):
            self.assertNotIn(forbidden, self.app_source)

    def test_feedback_hub_updates_visible_state_and_clicksafe_binding(self) -> None:
        for required in (
            "bindFeedbackHub",
            "data-feedback-lane",
            "data-feedback-event-log",
            "data-feedback-meter",
            "dataset.feedbackLane",
            "updateFeedbackHub",
            "emitMultimodalFeedback",
            "setActionFeedback",
        ):
            self.assertIn(required, self.js)


if __name__ == "__main__":
    unittest.main()
