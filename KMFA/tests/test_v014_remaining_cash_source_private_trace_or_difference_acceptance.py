from __future__ import annotations

import importlib
import unittest
from pathlib import Path
from types import ModuleType


GENERATOR_MODULE = "KMFA.tools.v014_remaining_cash_source_private_trace_or_difference_acceptance"
VALIDATOR_MODULE = (
    "KMFA.tools.check_v014_remaining_cash_source_private_trace_or_difference_acceptance"
)


class RemainingCashSourcePrivateTraceOrDifferenceAcceptanceTest(unittest.TestCase):
    artifact_snapshot: dict[Path, bytes | None] = {}

    def _load_modules(self) -> tuple[ModuleType, ModuleType]:
        try:
            generator = importlib.import_module(GENERATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing remaining cash trace generator: {exc.name}")
        try:
            validator = importlib.import_module(VALIDATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing remaining cash trace validator: {exc.name}")
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
                RemainingCashSourcePrivateTraceOrDifferenceAcceptanceTest._contains_float(child)
                for child in value.values()
            )
        if isinstance(value, list):
            return any(
                RemainingCashSourcePrivateTraceOrDifferenceAcceptanceTest._contains_float(child)
                for child in value
            )
        return False

    def tearDown(self) -> None:
        self._restore(self.artifact_snapshot)

    def test_payable_trace_distinguishes_cash_note_unpaid_and_partial_settlement(self) -> None:
        generator, _ = self._load_modules()
        cost = {
            "date": "2025-10-31",
            "voucher": "T-001",
            "account": "5001004-test",
            "summary": "project freight",
            "debit_cents": 150,
            "credit_cents": 0,
        }
        origin = [
            {
                "date": "2025-10-31",
                "voucher": "T-001",
                "account": "2202-test",
                "supplier": "SUP-01",
                "debit_cents": 0,
                "credit_cents": 2_168,
                "balance_cents": 2_168,
            }
        ]
        supplier = [
            *origin,
            {
                "date": "2025-10-31",
                "voucher": "T-002",
                "account": "2202-test",
                "supplier": "SUP-01",
                "debit_cents": 0,
                "credit_cents": 2_600,
                "balance_cents": 4_768,
            },
            {
                "date": "2025-11-03",
                "voucher": "T-003",
                "account": "2202-test",
                "supplier": "SUP-01",
                "debit_cents": 4_768,
                "credit_cents": 0,
                "balance_cents": 0,
            },
        ]
        bank = [
            {
                "date": "2025-11-03",
                "voucher": "T-003",
                "account": "1002-test",
                "debit_cents": 0,
                "credit_cents": 4_768,
            }
        ]
        cash_trace = generator.classify_payable_cost_trace(
            cost_row=cost,
            origin_voucher_rows=origin,
            supplier_payable_rows=supplier,
            bank_rows=bank,
            all_voucher_rows=[*origin, *supplier[1:]],
            cutoff_date="2026-05-31",
        )
        self.assertEqual(cash_trace["trace_classification"], "cash_paid_later")
        self.assertEqual(cash_trace["cash_paid_project_cost_cents"], 150)
        self.assertEqual(cash_trace["settlement_status"], "fully_settled_by_bank")

        note_origin = [
            {
                "date": "2026-02-28",
                "voucher": "T-010",
                "account": "2202-test",
                "supplier": "SUP-02",
                "debit_cents": 0,
                "credit_cents": 2_000,
                "balance_cents": 2_000,
            },
            {
                "date": "2026-02-28",
                "voucher": "T-010",
                "account": "2202-test",
                "supplier": "SUP-02",
                "debit_cents": 2_000,
                "credit_cents": 0,
                "balance_cents": 0,
            },
            {
                "date": "2026-02-28",
                "voucher": "T-010",
                "account": "1121-test",
                "supplier": "",
                "debit_cents": 0,
                "credit_cents": 2_000,
                "balance_cents": 0,
            },
        ]
        note_trace = generator.classify_payable_cost_trace(
            cost_row={**cost, "date": "2026-02-28", "voucher": "T-010", "debit_cents": 1_980},
            origin_voucher_rows=note_origin,
            supplier_payable_rows=note_origin[:2],
            bank_rows=[],
            all_voucher_rows=note_origin,
            cutoff_date="2026-05-31",
        )
        self.assertEqual(note_trace["trace_classification"], "noncash_note_settlement")
        self.assertEqual(note_trace["cash_paid_project_cost_cents"], 0)

        unpaid_origin = [
            {
                "date": "2026-05-31",
                "voucher": "T-020",
                "account": "2202-test",
                "supplier": "SUP-03",
                "debit_cents": 0,
                "credit_cents": 3_550,
                "balance_cents": 3_550,
            }
        ]
        unpaid_trace = generator.classify_payable_cost_trace(
            cost_row={**cost, "date": "2026-05-31", "voucher": "T-020", "debit_cents": 3_515},
            origin_voucher_rows=unpaid_origin,
            supplier_payable_rows=unpaid_origin,
            bank_rows=[],
            all_voucher_rows=unpaid_origin,
            cutoff_date="2026-05-31",
        )
        self.assertEqual(unpaid_trace["trace_classification"], "unpaid_at_cutoff")
        self.assertEqual(unpaid_trace["cash_paid_project_cost_cents"], 0)

        partial_rows = [
            {
                "date": "2026-01-01",
                "voucher": "T-030",
                "account": "2202-test",
                "supplier": "SUP-04",
                "debit_cents": 0,
                "credit_cents": 1_000,
                "balance_cents": 1_000,
            },
            {
                "date": "2026-02-01",
                "voucher": "T-031",
                "account": "2202-test",
                "supplier": "SUP-04",
                "debit_cents": 500,
                "credit_cents": 0,
                "balance_cents": 500,
            },
        ]
        partial_trace = generator.classify_payable_cost_trace(
            cost_row={**cost, "date": "2026-01-01", "voucher": "T-030", "debit_cents": 900},
            origin_voucher_rows=partial_rows[:1],
            supplier_payable_rows=partial_rows,
            bank_rows=[
                {
                    "date": "2026-02-01",
                    "voucher": "T-031",
                    "account": "1002-test",
                    "debit_cents": 0,
                    "credit_cents": 500,
                }
            ],
            all_voucher_rows=partial_rows,
            cutoff_date="2026-05-31",
        )
        self.assertEqual(partial_trace["trace_classification"], "unresolved_partial_settlement")
        self.assertIsNone(partial_trace["cash_paid_project_cost_cents"])
        self.assertFalse(self._contains_float([cash_trace, note_trace, unpaid_trace, partial_trace]))

    def test_real_private_trace_materializes_second_cash_project_and_preserves_differences(self) -> None:
        generator, validator = self._load_modules()
        source_paths = generator.source_private_paths()
        source_before = self._snapshot(source_paths)
        self.artifact_snapshot = self._snapshot(generator.phase_output_paths())

        result = generator.generate(
            generated_at="2026-07-10T16:00:00+10:00",
            write_governance_event=False,
        )

        self.assertEqual(source_before, self._snapshot(source_paths))
        summary = result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["payable_trace_record_count"], 3)
        self.assertEqual(summary["cash_paid_later_trace_count"], 1)
        self.assertEqual(summary["noncash_note_settlement_trace_count"], 1)
        self.assertEqual(summary["unpaid_at_cutoff_trace_count"], 1)
        self.assertEqual(summary["cash_project_resolved_count"], 2)
        self.assertEqual(summary["cash_project_unresolved_count"], 2)
        self.assertEqual(summary["private_cash_metric_record_count"], 6)
        self.assertEqual(summary["materialized_business_value_target_slot_count"], 34)
        self.assertEqual(summary["newly_materialized_cash_target_slot_count"], 3)
        self.assertEqual(summary["unresolved_cash_value_target_slot_count"], 6)
        self.assertEqual(summary["completed_reconciliation_comparison_count"], 10)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 8)
        self.assertEqual(summary["incomplete_cash_reconciliation_count"], 2)
        self.assertEqual(summary["wps_source_count"], 2)
        self.assertEqual(summary["office_compatibility_unlock_count"], 2)
        self.assertEqual(summary["empty_compatibility_workbook_count"], 2)
        self.assertEqual(summary["secure_wps_content_readable_count"], 0)
        self.assertEqual(summary["forced_zero_materialization_count"], 0)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])

        traces = generator.read_jsonl(generator.PRIVATE_PAYABLE_TRACES_PATH)
        decisions = generator.read_jsonl(generator.PRIVATE_CASH_DECISIONS_PATH)
        metrics = generator.read_jsonl(generator.PRIVATE_CASH_METRICS_PATH)
        materialized = generator.read_jsonl(generator.PRIVATE_TARGET_MATERIALIZATIONS_PATH)
        unresolved = generator.read_jsonl(generator.PRIVATE_UNRESOLVED_TARGETS_PATH)
        comparisons = generator.read_jsonl(generator.PRIVATE_RECONCILIATION_COMPARISONS_PATH)
        self.assertEqual(len(traces), 3)
        self.assertEqual(
            {row["trace_classification"] for row in traces},
            {"cash_paid_later", "noncash_note_settlement", "unpaid_at_cutoff"},
        )
        self.assertEqual(len([row for row in decisions if row["resolution_status"].startswith("resolved_")]), 2)
        self.assertEqual(len(metrics), 6)
        self.assertEqual(len(materialized), 34)
        self.assertEqual(len(unresolved), 6)
        self.assertEqual(len(comparisons), 12)
        self.assertFalse(
            self._contains_float([traces, decisions, metrics, materialized, unresolved, comparisons])
        )
        self.assertTrue(all(row["public_commit_allowed"] is False for row in traces))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in metrics))

        manifest = validator.validate(require_private_trace=True)
        self.assertEqual(manifest["summary"]["cash_project_resolved_count"], 2)
        self.assertEqual(
            manifest["summary"]["materialized_business_value_target_slot_count"], 34
        )


if __name__ == "__main__":
    unittest.main()
