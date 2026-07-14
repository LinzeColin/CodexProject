from __future__ import annotations

import importlib
import unittest
from pathlib import Path
from types import ModuleType


GENERATOR_MODULE = (
    "KMFA.tools."
    "v014_remaining_two_project_cash_collection_evidence_or_final_difference_acceptance"
)
VALIDATOR_MODULE = (
    "KMFA.tools."
    "check_v014_remaining_two_project_cash_collection_evidence_or_final_difference_acceptance"
)


class RemainingTwoProjectCashCollectionEvidenceOrFinalDifferenceAcceptanceTest(
    unittest.TestCase
):
    artifact_snapshot: dict[Path, bytes | None] = {}

    def _load_modules(self) -> tuple[ModuleType, ModuleType]:
        try:
            generator = importlib.import_module(GENERATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing final cash evidence generator: {exc.name}")
        try:
            validator = importlib.import_module(VALIDATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing final cash evidence validator: {exc.name}")
        return generator, validator

    @staticmethod
    def _snapshot(paths: list[Path]) -> dict[Path, bytes | None]:
        return {path: path.read_bytes() if path.exists() else None for path in paths}

    @staticmethod
    def _restore(snapshot: dict[Path, bytes | None]) -> None:
        for path, data in snapshot.items():
            if data is None:
                if path.exists():
                    path.unlink()
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    @staticmethod
    def _contains_float(value: object) -> bool:
        if isinstance(value, float):
            return True
        if isinstance(value, dict):
            return any(
                RemainingTwoProjectCashCollectionEvidenceOrFinalDifferenceAcceptanceTest._contains_float(
                    child
                )
                for child in value.values()
            )
        if isinstance(value, list):
            return any(
                RemainingTwoProjectCashCollectionEvidenceOrFinalDifferenceAcceptanceTest._contains_float(
                    child
                )
                for child in value
            )
        return False

    def tearDown(self) -> None:
        self._restore(self.artifact_snapshot)

    def test_collection_link_requires_unique_balanced_receivable_chain(self) -> None:
        generator, _ = self._load_modules()
        source_records = [
            {
                "amount_cents": 15_025,
                "project_dimension_present": True,
                "customer_dimension_present": True,
                "customer_bank_match": True,
                "header_type": "generic_amount",
                "is_formula": False,
                "source_anchor": "private-fixture-1",
            },
            {
                "amount_cents": 15_025,
                "project_dimension_present": True,
                "customer_dimension_present": True,
                "customer_bank_match": True,
                "header_type": "cumulative_or_to_date",
                "is_formula": False,
                "source_anchor": "private-fixture-2",
            },
        ]
        bank_row = {
            "date": "2026-01-10",
            "voucher": "B-001",
            "account": "1002-test",
            "debit_cents": 15_025,
            "credit_cents": 0,
            "balance_cents": 20_000,
        }
        voucher_rows = [
            bank_row,
            {
                "date": "2026-01-10",
                "voucher": "B-001",
                "account": "1122-test",
                "debit_cents": 0,
                "credit_cents": 15_025,
                "balance_cents": 0,
            },
        ]
        accepted = generator.classify_collection_link(
            source_records=source_records,
            bank_row=bank_row,
            voucher_rows=voucher_rows,
        )
        self.assertTrue(accepted["accepted"])
        self.assertEqual(
            accepted["classification"],
            "unique_project_customer_bank_receivable_collection",
        )
        self.assertEqual(accepted["amount_cents"], 15_025)
        self.assertTrue(accepted["voucher_balanced"])
        self.assertTrue(accepted["bank_equals_receivable_credit"])

        cumulative_only = generator.classify_collection_link(
            source_records=[{**source_records[1], "source_anchor": "private-fixture-3"}],
            bank_row=bank_row,
            voucher_rows=voucher_rows,
        )
        self.assertFalse(cumulative_only["accepted"])
        self.assertIn("noncumulative_source_missing", cumulative_only["reason_codes"])

        unbalanced = generator.classify_collection_link(
            source_records=source_records,
            bank_row=bank_row,
            voucher_rows=voucher_rows[:1],
        )
        self.assertFalse(unbalanced["accepted"])
        self.assertIn("voucher_not_balanced", unbalanced["reason_codes"])

        with self.assertRaises(ValueError):
            generator.classify_collection_link(
                source_records=[{**source_records[0], "amount_cents": 150.25}],
                bank_row=bank_row,
                voucher_rows=voucher_rows,
            )

    def test_real_sources_materialize_third_project_and_accept_final_difference(self) -> None:
        generator, validator = self._load_modules()
        source_paths = generator.source_private_paths()
        source_before = self._snapshot(source_paths)
        self.artifact_snapshot = self._snapshot(generator.phase_output_paths())

        result = generator.generate(
            generated_at="2026-07-10T18:00:00+10:00",
            write_governance_event=False,
        )

        self.assertEqual(source_before, self._snapshot(source_paths))
        summary = result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["cash_project_candidate_count"], 4)
        self.assertEqual(summary["cash_project_resolved_count"], 3)
        self.assertEqual(summary["cash_project_unresolved_count"], 1)
        self.assertEqual(summary["collection_evidence_project_resolved_count"], 1)
        self.assertEqual(summary["final_difference_accepted_project_count"], 1)
        self.assertEqual(summary["accessible_nonledger_ooxml_workbook_count"], 19)
        self.assertEqual(summary["raw_collection_candidate_record_count"], 48)
        self.assertEqual(summary["unique_balanced_collection_link_count"], 2)
        self.assertEqual(summary["balanced_receivable_voucher_count"], 2)
        self.assertEqual(summary["private_cash_metric_record_count"], 9)
        self.assertEqual(summary["newly_materialized_cash_target_slot_count"], 3)
        self.assertEqual(summary["materialized_business_value_target_slot_count"], 37)
        self.assertEqual(summary["unresolved_cash_value_target_slot_count"], 3)
        self.assertEqual(summary["reconciliation_record_count"], 12)
        self.assertEqual(summary["completed_reconciliation_comparison_count"], 11)
        self.assertEqual(summary["incomplete_cash_reconciliation_count"], 1)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(summary["secure_wps_content_readable_count"], 0)
        self.assertEqual(summary["forced_zero_materialization_count"], 0)
        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(self._contains_float(result))

        validator.validate(require_private_evidence=True)
        report = generator.PRIVATE_FINAL_DIFFERENCE_REPORT_PATH.read_text(
            encoding="utf-8"
        )
        for required in (
            "最终差异接受",
            "正向收款证据",
            "唯一银行入账链",
            "未写成零",
            "原始数据保持不变",
        ):
            self.assertIn(required, report)


if __name__ == "__main__":
    unittest.main()
