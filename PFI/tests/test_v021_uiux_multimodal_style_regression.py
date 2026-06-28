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

    def test_owner_first_screen_exposes_multimodal_feedback_style(self) -> None:
        for required in (
            "data-owner-feedback-strip",
            'data-feedback-signal="visual"',
            'data-feedback-signal="haptic"',
            'data-feedback-signal="sound"',
            "视觉回弹",
            "触感回馈",
            "声音提示",
        ):
            self.assertIn(required, self.html)
        self.assertIn("data-settings-feedback-console hidden", self.html)

    def test_css_is_delivery_style_not_plain_admin_shell(self) -> None:
        for required in (
            "color-scheme: dark;",
            "--pfi-bg: #06111f",
            "--pfi-accent-rose",
            ".owner-feedback-strip",
            ".feedback-signal",
            ".feedback-signal::before",
            "linear-gradient(135deg",
            "backdrop-filter",
        ):
            self.assertIn(required, self.css)

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

    def test_feedback_signal_buttons_are_clicksafe_bound(self) -> None:
        for required in (
            "bindOwnerFeedbackSignals",
            "data-feedback-signal",
            "dataset.feedbackKind",
            "emitMultimodalFeedback",
            "setActionFeedback",
        ):
            self.assertIn(required, self.js)


if __name__ == "__main__":
    unittest.main()
