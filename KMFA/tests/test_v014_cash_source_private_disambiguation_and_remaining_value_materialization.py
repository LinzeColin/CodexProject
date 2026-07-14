from __future__ import annotations

import importlib
import unittest
from pathlib import Path
from types import ModuleType


GENERATOR_MODULE = (
    "KMFA.tools.v014_cash_source_private_disambiguation_and_remaining_value_materialization"
)
VALIDATOR_MODULE = (
    "KMFA.tools.check_v014_cash_source_private_disambiguation_and_remaining_value_materialization"
)


class CashSourcePrivateDisambiguationAndRemainingValueMaterializationTest(unittest.TestCase):
    artifact_snapshot: dict[Path, bytes | None] = {}

    def _load_modules(self) -> tuple[ModuleType, ModuleType]:
        try:
            generator = importlib.import_module(GENERATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing cash-source disambiguation generator: {exc.name}")
        try:
            validator = importlib.import_module(VALIDATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing cash-source disambiguation validator: {exc.name}")
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
                CashSourcePrivateDisambiguationAndRemainingValueMaterializationTest._contains_float(child)
                for child in value.values()
            )
        if isinstance(value, list):
            return any(
                CashSourcePrivateDisambiguationAndRemainingValueMaterializationTest._contains_float(child)
                for child in value
            )
        return False

    def tearDown(self) -> None:
        self._restore(self.artifact_snapshot)

    def test_unique_ledger_evidence_resolves_cash_values_without_force_filling_absence(self) -> None:
        generator, _ = self._load_modules()
        project_code = "101"
        rows = [
            {
                "account": "1122-test",
                "date": "2026-01-02",
                "voucher": "T-001",
                "summary": "received test payment",
                "sales_contract": "CONTRACT-101",
                "research_project": "",
                "debit_cents": 0,
                "credit_cents": 8_000,
            },
            {
                "account": "1122-test",
                "date": "2026-01-02",
                "voucher": "T-001",
                "summary": "adjustment test payment",
                "sales_contract": "CONTRACT-101",
                "research_project": "",
                "debit_cents": 0,
                "credit_cents": 2_000,
            },
            {
                "account": "5001004-test",
                "date": "2026-01-03",
                "voucher": "T-002",
                "summary": "travel reimbursement",
                "sales_contract": "CONTRACT-101",
                "research_project": "",
                "debit_cents": 3_000,
                "credit_cents": 0,
            },
            {
                "account": "5001006-test",
                "date": "2026-01-31",
                "voucher": "T-003",
                "summary": "project allocation",
                "sales_contract": "CONTRACT-101",
                "research_project": "",
                "debit_cents": 900,
                "credit_cents": 0,
            },
        ]
        bank_rows = [
            {
                "account": "1002-test",
                "date": "2026-01-02",
                "voucher": "T-001",
                "summary": "received test payment",
                "debit_cents": 8_000,
                "credit_cents": 0,
            },
            {
                "account": "1002-test",
                "date": "2026-01-03",
                "voucher": "T-002",
                "summary": "travel reimbursement",
                "debit_cents": 0,
                "credit_cents": 3_180,
            },
            {
                "account": "1002-test",
                "date": "2026-01-04",
                "voucher": "T-004",
                "summary": "same customer other project",
                "debit_cents": 0,
                "credit_cents": 7_000,
            },
        ]
        voucher_rows = [
            *rows,
            {
                "account": "2221-test",
                "date": "2026-01-03",
                "voucher": "T-002",
                "summary": "recoverable input tax",
                "sales_contract": "",
                "research_project": "",
                "debit_cents": 180,
                "credit_cents": 0,
            },
            {
                "account": "1221-test",
                "date": "2026-01-04",
                "voucher": "T-004",
                "summary": "guarantee deposit",
                "sales_contract": "CONTRACT-999",
                "research_project": "",
                "debit_cents": 7_000,
                "credit_cents": 0,
            },
        ]

        resolved = generator.resolve_project_cash_sources(
            project_code=project_code,
            project_rows=rows,
            bank_rows=bank_rows,
            voucher_rows=voucher_rows,
            external_crosscheck_status="ole_wps_unavailable_not_claimed",
        )

        self.assertEqual(resolved["resolution_status"], "resolved_accessible_ledger_only")
        self.assertEqual(resolved["collection_amount_cents"], 8_000)
        self.assertEqual(resolved["cash_paid_cost_cents"], 3_000)
        self.assertEqual(resolved["cash_gross_profit_cents"], 5_000)
        self.assertEqual(resolved["noncash_collection_count"], 1)
        self.assertEqual(resolved["noncash_cost_count"], 1)
        self.assertEqual(resolved["unresolved_row_count"], 0)
        self.assertFalse(resolved["external_crosscheck_completed"])
        self.assertFalse(resolved["business_consistency_verified"])
        self.assertFalse(self._contains_float(resolved))

        no_receipt = generator.resolve_project_cash_sources(
            project_code="202",
            project_rows=[rows[-1]],
            bank_rows=[],
            voucher_rows=[rows[-1]],
            external_crosscheck_status="ole_wps_unavailable_not_claimed",
        )
        self.assertEqual(no_receipt["resolution_status"], "unresolved")
        self.assertIsNone(no_receipt["collection_amount_cents"])
        self.assertIsNone(no_receipt["cash_gross_profit_cents"])
        self.assertFalse(no_receipt["zero_inferred_from_absence"])

        ambiguous_cost = generator.resolve_project_cash_sources(
            project_code="303",
            project_rows=[
                rows[0],
                {
                    **rows[2],
                    "date": "2026-01-05",
                    "voucher": "T-005",
                    "summary": "supplier invoice pending payment trace",
                },
            ],
            bank_rows=[bank_rows[0]],
            voucher_rows=[rows[0]],
            external_crosscheck_status="ole_wps_unavailable_not_claimed",
        )
        self.assertEqual(ambiguous_cost["resolution_status"], "unresolved")
        self.assertGreater(ambiguous_cost["unresolved_row_count"], 0)
        self.assertIsNone(ambiguous_cost["cash_paid_cost_cents"])

    def test_real_private_phase_materializes_one_cash_project_and_preserves_raw_sources(self) -> None:
        generator, validator = self._load_modules()
        source_paths = generator.source_private_paths()
        source_before = self._snapshot(source_paths)
        self.artifact_snapshot = self._snapshot(generator.phase_output_paths())

        result = generator.generate(
            generated_at="2026-07-10T15:00:00+10:00",
            write_governance_event=False,
        )

        self.assertEqual(source_before, self._snapshot(source_paths))
        summary = result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["cash_project_candidate_count"], 4)
        self.assertEqual(summary["cash_project_resolved_count"], 1)
        self.assertEqual(summary["cash_project_unresolved_count"], 3)
        self.assertEqual(summary["materialized_business_value_target_slot_count"], 31)
        self.assertEqual(summary["newly_materialized_cash_target_slot_count"], 3)
        self.assertEqual(summary["unresolved_cash_value_target_slot_count"], 9)
        self.assertEqual(summary["completed_reconciliation_comparison_count"], 9)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 7)
        self.assertEqual(summary["incomplete_cash_reconciliation_count"], 3)
        self.assertEqual(summary["external_wps_source_count"], 2)
        self.assertEqual(summary["external_wps_readable_count"], 0)
        self.assertEqual(summary["global_unresolved_difference_count"], 72)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertFalse(summary["full_processed_value_materialization_complete"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])

        decisions = generator.read_jsonl(generator.PRIVATE_CASH_DECISIONS_PATH)
        cash_metrics = generator.read_jsonl(generator.PRIVATE_CASH_METRICS_PATH)
        materialized = generator.read_jsonl(generator.PRIVATE_TARGET_MATERIALIZATIONS_PATH)
        unresolved = generator.read_jsonl(generator.PRIVATE_UNRESOLVED_TARGETS_PATH)
        comparisons = generator.read_jsonl(generator.PRIVATE_RECONCILIATION_COMPARISONS_PATH)
        self.assertEqual(len(decisions), 4)
        self.assertEqual(len(cash_metrics), 3)
        self.assertEqual(len(materialized), 31)
        self.assertEqual(len(unresolved), 9)
        self.assertEqual(len(comparisons), 12)
        self.assertFalse(
            self._contains_float([decisions, cash_metrics, materialized, unresolved, comparisons])
        )
        self.assertTrue(all(row["public_commit_allowed"] is False for row in decisions))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in cash_metrics))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in materialized))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in unresolved))
        self.assertTrue(
            all(row["resolution_status"] != "resolved_by_forced_zero" for row in decisions)
        )

        manifest = validator.validate(require_private_materialization=True)
        self.assertEqual(manifest["summary"]["cash_project_resolved_count"], 1)
        self.assertEqual(
            manifest["summary"]["materialized_business_value_target_slot_count"], 31
        )


if __name__ == "__main__":
    unittest.main()
