import unittest

from arxiv_daily_push.doctor import doctor_report


class DoctorTests(unittest.TestCase):
    def test_report_contains_resource_gates(self):
        report = doctor_report()
        self.assertIn(report["status"], {"pass", "warn", "blocked"})
        self.assertEqual(report["phase"], "1")
        self.assertIn("disk", report)
        self.assertIn("missing_future_runtime_commands", report)


if __name__ == "__main__":
    unittest.main()

