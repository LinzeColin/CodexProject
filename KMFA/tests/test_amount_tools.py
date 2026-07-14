import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from KMFA.tools.amount_tools import AmountNormalizationError, normalize_amount_to_cents
from KMFA.tools.check_no_float_money import scan_paths


class AmountToolsTests(unittest.TestCase):
    def test_normalizes_yuan_thousands_and_negative_forms(self) -> None:
        self.assertEqual(normalize_amount_to_cents("1,234.56"), 123456)
        self.assertEqual(normalize_amount_to_cents("人民币1,234.56元"), 123456)
        self.assertEqual(normalize_amount_to_cents("-1,234.56"), -123456)
        self.assertEqual(normalize_amount_to_cents("(1,234.56)"), -123456)
        self.assertEqual(normalize_amount_to_cents(Decimal("12.30")), 1230)
        self.assertEqual(normalize_amount_to_cents(0), 0)

    def test_normalizes_ten_thousand_yuan_without_float_math(self) -> None:
        self.assertEqual(normalize_amount_to_cents("1.2345万元"), 1234500)
        self.assertEqual(normalize_amount_to_cents("1,234.56", unit="wan_yuan"), 1234560000)
        self.assertEqual(normalize_amount_to_cents("0.001千元"), 100)

    def test_rejects_float_and_non_cent_amounts(self) -> None:
        bad_float = json.loads("1.23")
        with self.assertRaises(AmountNormalizationError):
            normalize_amount_to_cents(bad_float)  # type: ignore[arg-type]
        with self.assertRaises(AmountNormalizationError):
            normalize_amount_to_cents("1.234元")
        with self.assertRaises(AmountNormalizationError):
            normalize_amount_to_cents(Decimal("1.001"))

    def test_blank_dash_hash_and_abnormal_text_never_default_to_zero(self) -> None:
        for value in ("", " ", "-", "--", "#", "N/A", "abc", "1#2", "含税金额待确认"):
            with self.subTest(value=value):
                with self.assertRaises(AmountNormalizationError):
                    normalize_amount_to_cents(value)

    def test_check_no_float_money_reports_forbidden_float_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad_money.py"
            bad.write_text("amount_cents = 12.34\nnormalized_amount = float('12.34')\n", encoding="utf-8")
            findings = scan_paths([bad])
        self.assertGreaterEqual(len(findings), 2)

    def test_check_no_float_money_allows_operational_float_contexts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            safe = Path(tmp) / "operational_metrics.py"
            safe.write_text(
                "latest_mtime: float | None = None\n"
                "confidence = max(0.0, 0.85)\n"
                "timeout_seconds = float('1.5')\n",
                encoding="utf-8",
            )
            findings = scan_paths([safe])
        self.assertEqual(findings, [])

    def test_check_no_float_money_uses_enclosing_money_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "money_context.py"
            bad.write_text(
                "def normalize_money(value: float):\n"
                "    return float(value) + 1.25\n",
                encoding="utf-8",
            )
            findings = scan_paths([bad])
        self.assertEqual(len(findings), 3)

    def test_no_float_scan_ignores_non_money_progress_and_directory_only_test_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "safe_progress.py").write_text(
                "status = {'derived_percent': 100.0}\n",
                encoding="utf-8",
            )
            private_dir = root / ".codex_private_runtime"
            private_dir.mkdir()
            (private_dir / "dependency.py").write_text("amount_cents = 12.34\n", encoding="utf-8")
            tests_dir = root / "tests"
            tests_dir.mkdir()
            (tests_dir / "negative_fixture.py").write_text("amount_cents = 12.34\n", encoding="utf-8")

            findings = scan_paths([root])

        self.assertEqual(findings, [])

    def test_cli_entrypoints(self) -> None:
        root = Path(__file__).resolve().parents[2]
        amount_result = subprocess.run(
            [sys.executable, "KMFA/tools/amount_tools.py", "1,234.56万元"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(json.loads(amount_result.stdout)["amount_cents"], 1234560000)

        no_float_result = subprocess.run(
            [sys.executable, "KMFA/tools/check_no_float_money.py"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("PASS: no KMFA Python float money usage found", no_float_result.stdout)


if __name__ == "__main__":
    unittest.main()
