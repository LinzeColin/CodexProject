from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_browser_visual_acceptance.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("run_browser_visual_acceptance", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load run_browser_visual_acceptance.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_browser_visual_acceptance"] = module
    spec.loader.exec_module(module)
    return module


class BrowserVisualAcceptanceRunnerTests(unittest.TestCase):
    def test_parser_defaults_to_local_report_portal(self) -> None:
        runner = load_runner_module()
        args = runner.build_parser().parse_args([])
        self.assertEqual(args.base_url, "http://127.0.0.1:8772/")
        self.assertEqual(args.output_dir, "outputs/finance_ledger_20220605_20260603")
        self.assertEqual(args.chrome_startup_retries, 3)

    def test_visual_ok_requires_markers_and_mobile_no_overflow(self) -> None:
        runner = load_runner_module()
        row = {
            "marker_ok": True,
            "text_length": 1000,
            "overflow_x": 0,
            "bad_chart_boxes": [],
            "chart_count": 3,
            "form_control_count": 10,
        }
        self.assertTrue(runner.visual_ok("dashboard.html", row, "mobile"))
        row["overflow_x"] = 24
        self.assertFalse(runner.visual_ok("dashboard.html", row, "mobile"))


if __name__ == "__main__":
    unittest.main()
