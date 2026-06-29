import json
import subprocess
import sys
import unittest
from decimal import Decimal
from pathlib import Path

from KMFA.tools.amount_tools import AmountNormalizationError, normalize_amount_to_cents
from KMFA.tools.field_standardization import FieldStandardizationError, MissingFieldError, standardize_date, standardize_period
from KMFA.tools.generate_tool_test_report import build_report


class BasicToolBoundaryTests(unittest.TestCase):
    def test_amount_decimal_negative_wan_and_abnormal_boundaries(self) -> None:
        cases = [
            ("0.01", 1),
            ("1234567890.12", 123456789012),
            (Decimal("0.01"), 1),
            ("-0.01", -1),
            ("(0.01)", -1),
            ("\u22120.01", -1),
            ("0.0001\u4e07\u5143", 100),
            ("-1.2345\u4e07\u5143", -1234500),
        ]
        for value, expected_cents in cases:
            with self.subTest(value=repr(value)):
                self.assertEqual(normalize_amount_to_cents(value), expected_cents)

        for value in ("1.234", "1#2", "\u91d1\u989d\u5f85\u786e\u8ba4", "\uffe5#"):
            with self.subTest(value=repr(value)):
                with self.assertRaises(AmountNormalizationError):
                    normalize_amount_to_cents(value)

    def test_date_and_period_chinese_year_month_and_nullish_boundaries(self) -> None:
        self.assertEqual(standardize_date("2026\u5e746\u670829\u65e5"), "2026-06-29")
        self.assertEqual(standardize_date("20260629"), "2026-06-29")
        self.assertEqual(standardize_date("2026/6/9"), "2026-06-09")
        self.assertEqual(standardize_period("2026\u5e746\u6708"), "2026-06")
        self.assertEqual(standardize_period("202606"), "2026-06")
        self.assertEqual(standardize_period("2026\u5e746\u670829\u65e5"), "2026-06")

        for value in (None, "", " ", "-", "#", "N/A"):
            with self.subTest(value=repr(value)):
                with self.assertRaises(MissingFieldError):
                    standardize_date(value)

        with self.assertRaises(FieldStandardizationError):
            standardize_period("2026-00")

    def test_tool_function_report_is_generated_from_synthetic_cases(self) -> None:
        report = build_report()
        self.assertEqual(report["stage"], "S04")
        self.assertEqual(report["phase"], "S04-P3")
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["raw_business_data_used"])
        self.assertEqual(report["case_summary"]["failed"], 0)
        self.assertGreaterEqual(report["case_summary"]["total"], 20)
        categories = {case["category"] for case in report["amount_boundary_cases"] + report["date_period_boundary_cases"]}
        self.assertIn("amount_decimal", categories)
        self.assertIn("amount_negative", categories)
        self.assertIn("amount_wan_yuan", categories)
        self.assertIn("amount_abnormal_characters", categories)
        self.assertIn("date_chinese", categories)
        self.assertIn("period_chinese_year_month", categories)
        self.assertIn("date_nullish", categories)

    def test_report_cli_outputs_json_and_markdown(self) -> None:
        root = Path(__file__).resolve().parents[2]
        json_result = subprocess.run(
            [sys.executable, "KMFA/tools/generate_tool_test_report.py", "--format", "json"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(json_result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["raw_business_data_used"])

        markdown_result = subprocess.run(
            [sys.executable, "KMFA/tools/generate_tool_test_report.py", "--format", "markdown"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("S04-P3 Tool Function Test Report", markdown_result.stdout)
        self.assertIn("amount ten-thousand-yuan unit", markdown_result.stdout)


if __name__ == "__main__":
    unittest.main()
