from __future__ import annotations

import importlib
import json
import unittest
from pathlib import Path
from types import ModuleType


GENERATOR_MODULE = (
    "KMFA.tools.v014_real_project_identity_private_rebinding_and_processed_value_materialization"
)
VALIDATOR_MODULE = (
    "KMFA.tools.check_v014_real_project_identity_private_rebinding_and_processed_value_materialization"
)


class RealProjectIdentityPrivateRebindingAndProcessedValueMaterializationTest(unittest.TestCase):
    artifact_snapshot: dict[Path, bytes | None] = {}

    def _load_modules(self) -> tuple[ModuleType, ModuleType]:
        try:
            generator = importlib.import_module(GENERATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing real-identity rebinding generator: {exc.name}")
        try:
            validator = importlib.import_module(VALIDATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing real-identity rebinding validator: {exc.name}")
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
                RealProjectIdentityPrivateRebindingAndProcessedValueMaterializationTest._contains_float(child)
                for child in value.values()
            )
        if isinstance(value, list):
            return any(
                RealProjectIdentityPrivateRebindingAndProcessedValueMaterializationTest._contains_float(child)
                for child in value
            )
        return False

    def tearDown(self) -> None:
        self._restore(self.artifact_snapshot)

    def test_rebinds_four_real_projects_and_materializes_only_proven_s09_values(self) -> None:
        generator, validator = self._load_modules()
        source_paths = generator.source_private_paths()
        source_before = self._snapshot(source_paths)
        self.artifact_snapshot = self._snapshot(generator.phase_output_paths())

        projects = [
            (1, 10_000, 6_000, 4_000, 4_000),
            (2, 20_000, 10_000, 8_000, 4_000),
            (3, 30_000, 25_000, 6_000, 2_000),
            (4, 40_000, 28_000, 10_000, 2_500),
        ]
        precheck_records = []
        for order, contract, cost, gross_profit, gross_margin in projects:
            precheck_records.append(
                {
                    "candidate_id": f"PRIVATE-CAND-{order:03d}",
                    "candidate_order": order,
                    "candidate_label": f"PRIVATE-PROJECT-{order:03d}",
                    "source_ref_hash": f"source-{order:03d}",
                    "shared_pdf_source_count": 1,
                    "gross_profit_formula_exact": contract - cost == gross_profit,
                    "authority_margin_formula_exact": True,
                    "workbook_identity_match_count": 2 if order < 4 else 0,
                    "workbook_identity_sheet_count": 2 if order < 4 else 0,
                    "values": {
                        "contract_amount_cents": contract,
                        "cost_total_cents": cost,
                        "authority_gross_profit_cents": gross_profit,
                        "authority_gross_margin_basis_points": gross_margin,
                    },
                    "private_source": {"source_ref_hash": f"source-{order:03d}"},
                }
            )
        raw_snapshot = {
            "schema_version": "test.raw.snapshot.v1",
            "classification": "private_test_fixture",
            "snapshot_kind": "before",
            "records": [],
            "records_sha256": "0" * 64,
            "file_count": 0,
            "total_bytes": 0,
            "extension_counts": {},
        }
        result = generator.generate(
            generated_at="2026-07-10T12:00:00+10:00",
            precheck_override={"records": precheck_records},
            raw_before_snapshot_override=raw_snapshot,
            raw_after_snapshot_override={**raw_snapshot, "snapshot_kind": "after"},
            write_governance_event=False,
        )

        self.assertEqual(source_before, self._snapshot(source_paths))
        summary = result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["real_project_identity_binding_count"], 4)
        self.assertEqual(summary["private_processed_metric_record_count"], 32)
        self.assertEqual(summary["materialized_business_value_target_slot_count"], 28)
        self.assertEqual(summary["unresolved_cash_value_target_slot_count"], 12)
        self.assertEqual(summary["completed_reconciliation_comparison_count"], 8)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 6)
        self.assertEqual(summary["incomplete_cash_reconciliation_count"], 4)
        self.assertEqual(summary["global_unresolved_difference_count"], 72)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertFalse(summary["full_processed_value_materialization_complete"])
        self.assertFalse(summary["processed_consistency_verified"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])

        bindings = generator.read_jsonl(generator.PRIVATE_IDENTITY_BINDINGS_PATH)
        metrics = generator.read_jsonl(generator.PRIVATE_PROCESSED_METRICS_PATH)
        materialized = generator.read_jsonl(generator.PRIVATE_TARGET_MATERIALIZATIONS_PATH)
        unresolved = generator.read_jsonl(generator.PRIVATE_UNRESOLVED_TARGETS_PATH)
        comparisons = generator.read_jsonl(generator.PRIVATE_RECONCILIATION_COMPARISONS_PATH)
        self.assertEqual(len(bindings), 4)
        self.assertEqual(len(metrics), 32)
        self.assertEqual(len(materialized), 28)
        self.assertEqual(len(unresolved), 12)
        self.assertEqual(len(comparisons), 12)
        self.assertFalse(self._contains_float(bindings))
        self.assertFalse(self._contains_float(metrics))
        self.assertFalse(self._contains_float(materialized))
        self.assertFalse(self._contains_float(comparisons))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in bindings))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in metrics))
        self.assertTrue(all(row["materialization_status"] == "materialized_private_only" for row in materialized))
        self.assertTrue(all(row["resolution_status"] == "cash_source_disambiguation_required" for row in unresolved))

        manifest = validator.validate(require_private_materialization=True)
        self.assertEqual(manifest["summary"]["real_project_identity_binding_count"], 4)
        self.assertEqual(manifest["summary"]["materialized_business_value_target_slot_count"], 28)


if __name__ == "__main__":
    unittest.main()
