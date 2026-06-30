import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.zero_delta_validator import (
    ZeroDeltaInputError,
    validate_zero_delta,
    write_mismatch_report,
)


class ZeroDeltaValidatorTests(unittest.TestCase):
    def test_passes_when_integer_cents_match_field_by_field(self) -> None:
        authoritative_records = [
            {
                "record_id": "SYN-PROJECT-001",
                "source": "A0_Q5_SYNTHETIC_BASELINE",
                "contract_amount_cents": 1200000,
                "total_expense_cents": 800000,
            }
        ]
        system_records = [
            {
                "record_id": "SYN-PROJECT-001",
                "source": "SYSTEM_RECOMPUTE_SYNTHETIC",
                "contract_amount_cents": 1200000,
                "total_expense_cents": 800000,
            }
        ]

        result = validate_zero_delta(
            authoritative_records,
            system_records,
            key_fields=("record_id",),
            amount_fields=("contract_amount_cents", "total_expense_cents"),
        )

        self.assertTrue(result["zero_delta_passed"])
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["mismatch_count"], 0)
        self.assertEqual(result["mismatches"], [])
        self.assertFalse(result["raw_business_data_used"])

    def test_one_cent_difference_fails_with_required_mismatch_fields(self) -> None:
        authoritative_records = [
            {
                "record_id": "SYN-PROJECT-002",
                "source": "A0_Q5_SYNTHETIC_BASELINE",
                "contract_amount_cents": 123456,
            }
        ]
        system_records = [
            {
                "record_id": "SYN-PROJECT-002",
                "source": "SYSTEM_RECOMPUTE_SYNTHETIC",
                "contract_amount_cents": 123455,
            }
        ]

        result = validate_zero_delta(
            authoritative_records,
            system_records,
            key_fields=("record_id",),
            amount_fields=("contract_amount_cents",),
        )

        self.assertFalse(result["zero_delta_passed"])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["minimum_fail_difference_cents"], 1)
        self.assertEqual(result["mismatch_count"], 1)
        mismatch = result["mismatches"][0]
        self.assertEqual(mismatch["source"], "A0_Q5_SYNTHETIC_BASELINE=>SYSTEM_RECOMPUTE_SYNTHETIC")
        self.assertEqual(mismatch["field"], "contract_amount_cents")
        self.assertEqual(mismatch["authoritative_value_cents"], 123456)
        self.assertEqual(mismatch["system_value_cents"], 123455)
        self.assertEqual(mismatch["difference_cents"], 1)

    def test_mismatch_report_csv_contains_required_public_safe_columns(self) -> None:
        authoritative_records = [
            {
                "record_id": "SYN-PROJECT-003",
                "source": "A0_Q5_SYNTHETIC_BASELINE",
                "total_expense_cents": 9900,
            }
        ]
        system_records = [
            {
                "record_id": "SYN-PROJECT-003",
                "source": "SYSTEM_RECOMPUTE_SYNTHETIC",
                "total_expense_cents": 9899,
            }
        ]
        result = validate_zero_delta(
            authoritative_records,
            system_records,
            key_fields=("record_id",),
            amount_fields=("total_expense_cents",),
        )

        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "mismatch_report.csv"
            write_mismatch_report(result["mismatches"], report_path)
            rows = list(csv.DictReader(report_path.read_text(encoding="utf-8").splitlines()))

        self.assertEqual(len(rows), 1)
        for required_column in (
            "source",
            "field",
            "authoritative_value_cents",
            "system_value_cents",
            "difference_cents",
        ):
            self.assertIn(required_column, rows[0])
        self.assertEqual(rows[0]["difference_cents"], "1")

    def test_rejects_float_money_inputs(self) -> None:
        bad_float = json.loads("123.45")
        with self.assertRaises(ZeroDeltaInputError):
            validate_zero_delta(
                [{"record_id": "SYN-PROJECT-004", "source": "A0_Q5_SYNTHETIC_BASELINE", "amount_cents": bad_float}],
                [{"record_id": "SYN-PROJECT-004", "source": "SYSTEM_RECOMPUTE_SYNTHETIC", "amount_cents": 12345}],
                key_fields=("record_id",),
                amount_fields=("amount_cents",),
            )

    def test_missing_amount_field_fails_instead_of_passing(self) -> None:
        result = validate_zero_delta(
            [{"record_id": "SYN-PROJECT-004A", "source": "A0_Q5_SYNTHETIC_BASELINE"}],
            [{"record_id": "SYN-PROJECT-004A", "source": "SYSTEM_RECOMPUTE_SYNTHETIC"}],
            key_fields=("record_id",),
            amount_fields=("contract_amount_cents",),
        )

        self.assertFalse(result["zero_delta_passed"])
        self.assertEqual(result["mismatch_count"], 1)
        self.assertIsNone(result["mismatches"][0]["authoritative_value_cents"])
        self.assertIsNone(result["mismatches"][0]["system_value_cents"])

    def test_cli_writes_result_json_and_mismatch_report_on_failure(self) -> None:
        root = Path(__file__).resolve().parents[2]
        fixture = {
            "authoritative_records": [
                {
                    "record_id": "SYN-PROJECT-005",
                    "source": "A0_Q5_SYNTHETIC_BASELINE",
                    "contract_amount_cents": 10000,
                }
            ],
            "system_records": [
                {
                    "record_id": "SYN-PROJECT-005",
                    "source": "SYSTEM_RECOMPUTE_SYNTHETIC",
                    "contract_amount_cents": 9999,
                }
            ],
            "key_fields": ["record_id"],
            "amount_fields": ["contract_amount_cents"],
        }

        with tempfile.TemporaryDirectory() as tmp:
            fixture_path = Path(tmp) / "fixture.json"
            result_path = Path(tmp) / "zero_delta_result.json"
            report_path = Path(tmp) / "mismatch_report.csv"
            fixture_path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "KMFA/tools/zero_delta_validator.py",
                    "--fixture",
                    str(fixture_path),
                    "--result-json",
                    str(result_path),
                    "--mismatch-report",
                    str(report_path),
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result_path.read_text(encoding="utf-8"))["mismatch_count"], 1)
            rows = list(csv.DictReader(report_path.read_text(encoding="utf-8").splitlines()))

        self.assertEqual(rows[0]["field"], "contract_amount_cents")
        self.assertEqual(rows[0]["difference_cents"], "1")


if __name__ == "__main__":
    unittest.main()
