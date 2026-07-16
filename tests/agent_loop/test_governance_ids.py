from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from governance_ids import (  # noqa: E402
    GovernanceIdError,
    parse_identifier,
    resolve_task_id,
    validate_task_acceptance_pair,
    validate_unique_task_ids,
)


class GovernanceIdsTest(unittest.TestCase):
    def test_v2_pair_has_exact_suffix(self) -> None:
        task, acceptance = validate_task_acceptance_pair(
            "TSK.CodexProject.REPO1.0002",
            "ACC.CodexProject.REPO1.0002",
        )
        self.assertEqual(task.generation, "v2")
        self.assertEqual(task.suffix, acceptance.suffix)

    def test_legacy_pairs_remain_readable(self) -> None:
        for task, acceptance in (
            ("S1PAT01", "ACC-S1PAT01"),
            ("AGENT-LOOP-C2C3D1-T01", "AGENT-LOOP-C2C3D1-A01"),
        ):
            with self.subTest(task=task):
                parsed, _ = validate_task_acceptance_pair(task, acceptance)
                self.assertEqual(parsed.generation, "v1")

    def test_mixed_generation_requires_alias(self) -> None:
        with self.assertRaises(GovernanceIdError):
            validate_task_acceptance_pair(
                "S1PAT01",
                "ACC.CodexProject.REPO1.0001",
            )

    def test_v2_suffix_mismatch_is_rejected(self) -> None:
        with self.assertRaises(GovernanceIdError):
            validate_task_acceptance_pair(
                "TSK.CodexProject.REPO1.0002",
                "ACC.CodexProject.REPO1.0003",
            )

    def test_alias_resolution_is_project_scoped(self) -> None:
        aliases = {
            "CodexProject": {"S1PAT01": "TSK.CodexProject.REPO1.0001"},
            "Other": {"S1PAT01": "TSK.Other.REPO1.0001"},
        }
        self.assertEqual(
            resolve_task_id("S1PAT01", project="CodexProject", aliases=aliases),
            "TSK.CodexProject.REPO1.0001",
        )
        with self.assertRaises(GovernanceIdError):
            resolve_task_id("S1PAT01", project="Missing", aliases=aliases)

    def test_exact_duplicates_are_rejected(self) -> None:
        with self.assertRaises(GovernanceIdError):
            validate_unique_task_ids(["S1PAT01", "S1PAT01"])

    def test_wrong_kind_is_rejected(self) -> None:
        with self.assertRaises(GovernanceIdError):
            parse_identifier("ACC.CodexProject.REPO1.0002", "TSK")

    def test_malformed_v2_does_not_fall_back_to_legacy(self) -> None:
        for value, kind in (
            ("TSK.CodexProject.REPO1.2", "TSK"),
            ("ACC.CodexProject.REPO1.2", "ACC"),
            ("PG.CodexProject.REPO1.2", "PG"),
        ):
            with self.subTest(value=value):
                with self.assertRaises(GovernanceIdError):
                    parse_identifier(value, kind)

    def test_all_bootstrap_schemas_expose_v2_patterns(self) -> None:
        schemas = [
            "delivery_tasks.schema.json",
            "events.schema.json",
            "roadmap.schema.json",
            "run_manifest.schema.json",
            "run_receipt.schema.json",
        ]
        for name in schemas:
            with self.subTest(name=name):
                payload = json.loads((ROOT / "governance" / "schemas" / name).read_text(encoding="utf-8"))
                serialized = json.dumps(payload, sort_keys=True)
                self.assertIn("TSK\\\\.", serialized)
                patterns = [
                    value
                    for key, value in _walk(payload)
                    if key == "pattern" and isinstance(value, str) and value.startswith("^TSK")
                ]
                self.assertTrue(any(re.fullmatch(pattern, "TSK.CodexProject.REPO1.0002") for pattern in patterns))


def _walk(value):
    if isinstance(value, dict):
        for item in value.items():
            yield item
            yield from _walk(item[1])
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


if __name__ == "__main__":
    unittest.main()
