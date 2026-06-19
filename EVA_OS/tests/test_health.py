import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from quantlab.system import collect_health_checks


class HealthTests(unittest.TestCase):
    def test_collect_health_checks_reports_missing_required_files(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("禁止接入实盘交易，禁止真实下单", encoding="utf-8")
            checks = collect_health_checks(project_root=root, report_root=root / "reports")
        statuses = {check.item_en: check.status for check in checks}
        self.assertEqual(statuses["Project Directory"], "Pass")
        self.assertEqual(statuses["Internal Start Launcher"], "Review")
        self.assertEqual(statuses["Double-Click Stopper"], "Review")
        self.assertEqual(statuses["Status Script"], "Review")
        self.assertEqual(statuses["Verification Script"], "Review")
        self.assertEqual(statuses["Docs Index"], "Review")
        self.assertEqual(statuses["Acceptance Checklist"], "Review")
        self.assertEqual(statuses["Release Notes"], "Review")
        self.assertEqual(statuses["Maturity Roadmap"], "Review")
        self.assertEqual(statuses["Safety Boundary"], "Pass")


if __name__ == "__main__":
    unittest.main()
