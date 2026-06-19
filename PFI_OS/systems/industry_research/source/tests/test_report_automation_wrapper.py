from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReportAutomationWrapperTest(unittest.TestCase):
    def test_execution_readiness_check_is_logged_without_blocking_report_health(self) -> None:
        script = (ROOT / "scripts" / "run_report_automation.sh").read_text(encoding="utf-8")

        self.assertIn("automation-health --date \"$TODAY\"", script)
        self.assertIn("--require-execution-ready", script)
        self.assertIn("execution_readiness=blocked", script)
        self.assertIn('if "$PYTHON_BIN" -m src.cli automation-health --date "$TODAY" --no-quality-check --require-execution-ready; then', script)


if __name__ == "__main__":
    unittest.main()
