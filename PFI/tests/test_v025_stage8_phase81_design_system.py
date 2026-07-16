from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOKENS_PATH = ROOT / "web" / "styles" / "tokens.css"
INDEX_PATH = ROOT / "web" / "index.html"
COMPONENT_PATH = ROOT / "web" / "app" / "components" / "designSystem.js"
SHELL_PATH = ROOT / "web" / "app" / "shell.js"
PHASE_DIR = ROOT / "reports" / "pfi_v025" / "stage_8" / "phase_8_1"


def _token(css: str, name: str) -> str:
    matched = re.search(rf"{re.escape(name)}:\s*([^;]+);", css)
    if not matched:
        raise AssertionError(f"missing token: {name}")
    return matched.group(1).strip()


def _relative_luminance(value: str) -> float:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise AssertionError(f"expected six-digit hex color, got {value!r}")
    channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    high, low = sorted((_relative_luminance(first), _relative_luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


class TestV025Stage8Phase81DesignSystem(unittest.TestCase):
    def setUp(self) -> None:
        self.css = TOKENS_PATH.read_text(encoding="utf-8")
        self.index = INDEX_PATH.read_text(encoding="utf-8")
        self.shell = SHELL_PATH.read_text(encoding="utf-8")
        self.component = COMPONENT_PATH.read_text(encoding="utf-8") if COMPONENT_PATH.exists() else ""

    def test_default_is_explicit_light_with_complete_token_families(self) -> None:
        self.assertIn('<meta name="color-scheme" content="light" />', self.index)
        self.assertIn('data-v025-stage8-design-system="phase_8_1"', self.index)
        self.assertIn("color-scheme: light;", self.css)
        self.assertNotIn("@media (prefers-color-scheme: dark)", self.css)

        required = (
            "--pfi-bg",
            "--pfi-surface",
            "--pfi-surface-raised",
            "--pfi-surface-muted",
            "--pfi-ink",
            "--pfi-muted",
            "--pfi-border",
            "--pfi-border-strong",
            "--pfi-blue",
            "--pfi-teal",
            "--pfi-amber",
            "--pfi-red",
            "--pfi-focus",
            "--pfi-chart-grid",
            "--pfi-chart-1",
            "--pfi-chart-2",
            "--pfi-chart-3",
            "--pfi-space-1",
            "--pfi-space-2",
            "--pfi-space-3",
            "--pfi-space-4",
            "--pfi-space-5",
            "--pfi-space-6",
            "--pfi-radius-control",
            "--pfi-radius-panel",
            "--pfi-shadow-panel",
            "--pfi-font",
            "--pfi-font-mono",
            "--pfi-text-xs",
            "--pfi-text-sm",
            "--pfi-text-md",
            "--pfi-text-lg",
            "--pfi-target",
            "--pfi-z-nav",
            "--pfi-z-overlay",
        )
        for name in required:
            _token(self.css, name)

        self.assertGreaterEqual(_contrast(_token(self.css, "--pfi-ink"), _token(self.css, "--pfi-surface")), 7.0)
        self.assertGreaterEqual(_contrast(_token(self.css, "--pfi-muted"), _token(self.css, "--pfi-surface")), 4.5)

    def test_ten_primary_workspaces_use_ten_semantic_archetypes(self) -> None:
        expected = {
            "home": "status_board",
            "accounts": "balance_sheet",
            "ledger": "review_table",
            "investment": "portfolio_analytics",
            "consumption": "spending_flow",
            "sync": "data_pipeline",
            "recommendations": "decision_inbox",
            "insights": "report_library",
            "market_research": "research_workspace",
            "settings": "control_center",
        }
        self.assertIn('<script src="./app/components/designSystem.js"></script>', self.index)
        self.assertIn("PFI_V025_STAGE8_DESIGN_SYSTEM", self.component)
        for workspace, archetype in expected.items():
            self.assertRegex(self.component, rf"\b{re.escape(workspace)}:\s*\"{re.escape(archetype)}\"")
            self.assertIn(f'[data-stage8-archetype="{archetype}"]', self.css)
        self.assertEqual(len(set(expected.values())), 10)
        self.assertIn("MutationObserver", self.component)

    def test_chart_has_accessible_real_empty_error_stale_and_ready_states(self) -> None:
        self.assertIn('canvas.setAttribute("role", "img")', self.component)
        self.assertIn('canvas.setAttribute("aria-describedby"', self.component)
        for state in ("empty", "error", "stale", "ready"):
            self.assertIn(f'"{state}"', self.component)
            self.assertIn(f'[data-stage8-chart-state="{state}"]', self.css)
        self.assertIn("当前不显示伪造曲线", self.shell)
        empty_branch = self.shell.index("if (!series.length)")
        draw_series = self.shell.index("series.forEach((item) => drawTrendSeries", empty_branch)
        self.assertLess(empty_branch, draw_series)
        self.assertNotIn("stage8Synthetic", self.component)

    def test_desktop_tablet_and_mobile_are_real_layouts_without_device_mockup(self) -> None:
        self.assertIn("@media (max-width: 1180px)", self.css)
        self.assertIn("@media (max-width: 780px)", self.css)
        self.assertIn("@media (max-width: 480px)", self.css)
        self.assertIn("grid-template-areas:", self.css)
        self.assertIn("overflow-x: auto", self.css)
        forbidden = "phone-preview mobile-preview-frame device-mockup iphone-frame".split()
        for term in forbidden:
            self.assertNotIn(term, (self.css + self.index + self.component).lower())

    def test_phase_evidence_is_complete_and_does_not_claim_later_phases(self) -> None:
        required = (
            "evidence.json",
            "design_tokens.json",
            "browser_validation.json",
            "terminal.log",
            "changed_files.txt",
            "risk_and_rollback.md",
            "browser_trace.zip",
        )
        for name in required:
            self.assertTrue((PHASE_DIR / name).is_file(), name)
        evidence = json.loads((PHASE_DIR / "evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["schema"], "PFIV025Stage8Phase81EvidenceV1")
        self.assertEqual(evidence["task_ids"], ["S8-P1-T1", "S8-P1-T2", "S8-P1-T3", "S8-P1-T4"])
        self.assertEqual(evidence["acceptance_id"], "ACC-PFI-V025-STAGE8-WHOLE-REVIEW")
        self.assertTrue(evidence["phase_8_1_complete"])
        self.assertFalse(evidence["phase_8_2_started"])
        self.assertFalse(evidence["phase_8_3_started"])
        self.assertFalse(evidence["stage_8_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["finder_used"])


if __name__ == "__main__":
    unittest.main()
