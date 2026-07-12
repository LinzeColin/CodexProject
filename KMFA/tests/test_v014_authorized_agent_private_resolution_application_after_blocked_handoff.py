from __future__ import annotations

import importlib
import json
import unittest
from pathlib import Path
from types import ModuleType


GENERATOR_MODULE = (
    "KMFA.tools.v014_authorized_agent_private_resolution_application_after_blocked_handoff"
)
VALIDATOR_MODULE = (
    "KMFA.tools.check_v014_authorized_agent_private_resolution_application_after_blocked_handoff"
)


class AuthorizedAgentPrivateResolutionApplicationAfterBlockedHandoffTest(unittest.TestCase):
    artifact_snapshot: dict[Path, bytes | None] = {}

    def _load_modules(self) -> tuple[ModuleType, ModuleType]:
        try:
            generator = importlib.import_module(GENERATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing authorized-agent private-resolution generator: {exc.name}")
        try:
            validator = importlib.import_module(VALIDATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing authorized-agent private-resolution validator: {exc.name}")
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

    def tearDown(self) -> None:
        self._restore(self.artifact_snapshot)

    def test_applies_only_deterministic_private_resolutions_and_keeps_value_gates_closed(self) -> None:
        generator, validator = self._load_modules()
        source_before = generator.SOURCE_PRIVATE_OWNER_RESOLUTION_QUEUE_PATH.read_bytes()
        output_paths = generator.phase_output_paths()
        self.artifact_snapshot = self._snapshot(output_paths)

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
            raw_index_override={"source_records": [], "numeric_records": [], "parse_errors": []},
            raw_before_snapshot_override=raw_snapshot,
            raw_after_snapshot_override={**raw_snapshot, "snapshot_kind": "after"},
            write_governance_event=False,
        )

        self.assertEqual(source_before, generator.SOURCE_PRIVATE_OWNER_RESOLUTION_QUEUE_PATH.read_bytes())
        summary = result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_resolution_item_count"], 48)
        self.assertEqual(summary["resolved_structural_item_count"], 8)
        self.assertEqual(summary["resolved_formula_mapping_count"], 4)
        self.assertEqual(summary["resolved_non_numeric_mapping_count"], 4)
        self.assertEqual(summary["unresolved_business_value_item_count"], 40)
        self.assertEqual(summary["unresolved_difference_count"], 72)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertFalse(summary["raw_inbox_mutated_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["processed_consistency_verified"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

        records = [
            json.loads(line)
            for line in generator.PRIVATE_RESOLUTION_RECORDS_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(records), 48)
        resolved = [row for row in records if row["resolution_applied"]]
        unresolved = [row for row in records if not row["resolution_applied"]]
        self.assertEqual(len(resolved), 8)
        self.assertEqual(len(unresolved), 40)
        self.assertTrue(all(row["business_value_materialized"] is False for row in resolved))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in records))
        self.assertTrue(
            all(row["resolution_kind"] in {"formula_contract", "canonical_cost_category_taxonomy"} for row in resolved)
        )
        self.assertTrue(
            all("synthetic_project_identity_not_raw_bound" in row["reason_codes"] for row in unresolved)
        )

        manifest = validator.validate(require_private_resolution=True)
        self.assertEqual(manifest["summary"]["resolved_structural_item_count"], 8)
        self.assertEqual(manifest["summary"]["unresolved_business_value_item_count"], 40)


if __name__ == "__main__":
    unittest.main()
