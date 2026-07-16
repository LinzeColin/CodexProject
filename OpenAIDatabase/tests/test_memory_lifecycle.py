from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPT = DATABASE_DIR / "scripts/memory.py"
VALID_RECORDS = DATABASE_DIR / "tests/fixtures/memory_record_v2/valid_records.json"
SCHEMA = DATABASE_DIR / "config/memory.schema.json"
LIFECYCLE_POLICY = DATABASE_DIR / "config/memory-lifecycle-policy.json"


def load_memory():
    scripts_dir = str(DATABASE_DIR / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("memory_lifecycle_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, sys.modules["memory_lifecycle"], sys.modules["memory_mutation"]


class MemoryLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.memory, cls.lifecycle, cls.mutation = load_memory()
        cls.records = json.loads(VALID_RECORDS.read_text(encoding="utf-8"))
        cls.mutation_policy = cls.memory.load_mutation_policy(
            DATABASE_DIR,
            Path("config/memory-mutation-policy.json"),
        )

    def update_envelope(
        self,
        target: dict[str, object],
        *,
        statement: str,
        label: str,
        valid_from: str,
        observed_at: str,
        authorized_at: str,
    ) -> dict[str, object]:
        value: dict[str, object] = {
            "schema_version": "openai_database.memory_mutation.v1",
            "operation": "update",
            "idempotency_key": "",
            "base_commit_sha": "1" * 40,
            "actor": {"type": "user_via_agent", "id": "lifecycle-test-agent"},
            "source": {
                "type": "explicit_user",
                "ref": f"user-message:{label}",
                "observed_at": observed_at,
                "evidence_hash": None,
            },
            "authorization": {
                "mode": "explicit_user_zero_human",
                "ref": f"owner-authorization:{label}",
                "authorized_at": authorized_at,
            },
            "target": {
                "record_id": target["id"],
                "memory_key": target["memory_key"],
                "scope": copy.deepcopy(target["scope"]),
            },
            "payload": {
                "kind": target["kind"],
                "statement": statement,
                "confidence": "high",
                "importance": "high",
                "aliases": [],
                "tags": ["lifecycle-fixture"],
                "negative_triggers": [],
            },
            "valid_time": {"from": valid_from, "to": None},
            "sensitivity": {
                "classification": "public",
                "handling": "public_text",
                "credential_present": False,
                "public_repository_allowed": True,
            },
            "reason": "Deterministic lifecycle regression update.",
        }
        value["idempotency_key"] = self.mutation.expected_idempotency_key(value)
        return value

    def query_ids(self, records: list[dict[str, object]], **kwargs: object) -> list[str]:
        results, _ = self.memory.query_records(
            records,
            limit=200,
            execution_time=datetime(2026, 7, 16, 6, 0, tzinfo=timezone.utc),
            **kwargs,
        )
        return [str(record["id"]) for record in results]

    def test_policy_schema_and_canonical_quality_baseline_are_clean(self) -> None:
        policy = self.lifecycle.load_policy(LIFECYCLE_POLICY)
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        canonical, _, _ = self.memory.load_input_records(DATABASE_DIR, None)
        assessment = self.lifecycle.assess_lifecycle(canonical)

        self.assertEqual(policy["classification_order"], list(self.lifecycle.CLASSIFICATIONS))
        self.assertFalse(policy["normalization"]["embedding_as_unique_decision"])
        self.assertIn("transitions", schema["properties"]["recorded_time"]["properties"])
        self.assertEqual(schema["x-lifecycle-contract"]["acceptance_id"], "ACC.OpenAIDatabase.PAM1.0010")
        self.assertEqual(assessment["record_count"], 198)
        self.assertEqual(sum(assessment["classification_counts"].values()), 0)
        self.assertEqual(assessment["active_duplicate_conflict_count"], 0)
        self.assertEqual(assessment["unresolved_conflict_ids"], [])
        self.assertTrue(assessment["settlement_allowed"])
        self.assertEqual(assessment["embedding_decision_count"], 0)

    def test_four_classes_and_half_open_boundary_are_deterministic(self) -> None:
        base = copy.deepcopy(self.records[0])
        exact = copy.deepcopy(base)
        exact["id"] = "mem_lifecycle_exact_0001"
        normalized = copy.deepcopy(exact)
        normalized["id"] = "mem_lifecycle_normalized_0002"
        normalized["statement"] = "  " + str(base["statement"]).upper() + "  "
        conflict = copy.deepcopy(exact)
        conflict["id"] = "mem_lifecycle_conflict_0003"
        conflict["statement"] = "A different current fact."

        old = copy.deepcopy(self.records[1])
        successor = copy.deepcopy(self.records[2])
        overlapping = copy.deepcopy(old)
        overlapping["valid_time"]["to"] = "2026-07-16T00:03:00Z"

        self.assertEqual(self.lifecycle.classify_pair(base, exact), "exact_duplicate")
        self.assertEqual(self.lifecycle.classify_pair(base, normalized), "normalized_duplicate")
        self.assertEqual(self.lifecycle.classify_pair(base, conflict), "same_key_conflict")
        self.assertEqual(
            self.lifecycle.classify_pair(overlapping, successor),
            "overlapping_validity_conflict",
        )
        self.assertIsNone(self.lifecycle.classify_pair(old, successor))
        self.assertEqual(
            self.lifecycle.statement_fingerprint(base["statement"]),
            self.lifecycle.statement_fingerprint(normalized["statement"]),
        )

    def test_update_reversal_current_valid_and_recorded_time_are_correct(self) -> None:
        original = copy.deepcopy(self.records[2])
        first_envelope = self.update_envelope(
            original,
            statement="Critical runtime fact version two.",
            label="first-update",
            valid_from="2026-07-16T01:00:00Z",
            observed_at="2026-07-16T02:50:00Z",
            authorized_at="2026-07-16T03:00:00Z",
        )
        first = self.memory.build_mutation_outcome(
            self.records,
            first_envelope,
            self.mutation_policy,
            current_base_sha="1" * 40,
        )
        first_id = str(first["details"]["record_id"])
        first_record = next(record for record in first["records"] if record["id"] == first_id)
        reversal_envelope = self.update_envelope(
            first_record,
            statement=str(original["statement"]),
            label="reversal",
            valid_from="2026-07-16T04:00:00Z",
            observed_at="2026-07-16T04:50:00Z",
            authorized_at="2026-07-16T05:00:00Z",
        )
        reversal = self.memory.build_mutation_outcome(
            first["records"],
            reversal_envelope,
            self.mutation_policy,
            current_base_sha="1" * 40,
        )
        reversal_id = str(reversal["details"]["record_id"])
        key = str(original["memory_key"])
        scope = "project:ExampleProject"

        self.assertEqual(self.query_ids(reversal["records"], key=key, scope=scope), [reversal_id])
        self.assertEqual(
            self.query_ids(reversal["records"], key=key, scope=scope, as_of="2026-07-16T00:30:00Z"),
            [str(original["id"])],
        )
        self.assertEqual(
            self.query_ids(reversal["records"], key=key, scope=scope, as_of="2026-07-16T02:00:00Z"),
            [first_id],
        )
        self.assertEqual(
            self.query_ids(reversal["records"], key=key, scope=scope, as_of="2026-07-16T04:30:00Z"),
            [reversal_id],
        )
        self.assertEqual(
            self.query_ids(
                reversal["records"],
                key=key,
                scope=scope,
                as_of="2026-07-16T02:00:00Z",
                recorded_as_of="2026-07-16T02:30:00Z",
            ),
            [str(original["id"])],
        )
        self.assertEqual(
            self.query_ids(
                reversal["records"],
                key=key,
                scope=scope,
                as_of="2026-07-16T02:00:00Z",
                recorded_as_of="2026-07-16T03:30:00Z",
            ),
            [first_id],
        )
        self.assertEqual(self.query_ids(reversal["records"], record_id=str(original["id"])), [])
        self.assertEqual(self.query_ids(reversal["records"], key=key, scope="global:global"), [])
        self.assertEqual(reversal["details"]["lifecycle"]["active_duplicate_conflict_count"], 0)
        self.assertTrue(reversal["details"]["lifecycle"]["settlement_allowed"])

        concurrent = self.update_envelope(
            original,
            statement="Concurrent stale update.",
            label="concurrent",
            valid_from="2026-07-16T02:00:00Z",
            observed_at="2026-07-16T03:10:00Z",
            authorized_at="2026-07-16T03:20:00Z",
        )
        with self.assertRaisesRegex(self.memory.MutationAdmissionError, "mutation_update_target_not_active"):
            self.memory.build_mutation_outcome(
                first["records"],
                concurrent,
                self.mutation_policy,
                current_base_sha="1" * 40,
            )

        no_fact = self.update_envelope(
            original,
            statement="  " + str(original["statement"]).upper() + "  ",
            label="normalized-no-fact",
            valid_from="2026-07-16T01:00:00Z",
            observed_at="2026-07-16T01:10:00Z",
            authorized_at="2026-07-16T01:20:00Z",
        )
        with self.assertRaisesRegex(self.memory.MutationAdmissionError, "mutation_update_has_no_new_fact"):
            self.memory.build_mutation_outcome(
                self.records,
                no_fact,
                self.mutation_policy,
                current_base_sha="1" * 40,
            )

    def test_recorded_time_uncertainty_and_missing_valid_axis_fail_closed(self) -> None:
        with self.assertRaisesRegex(self.memory.MemoryCLIError, "recorded_as_of_requires_as_of"):
            self.memory.query_records(
                self.records,
                recorded_as_of="2026-07-16T02:00:00Z",
            )

        incomplete = copy.deepcopy(self.records[2])
        incomplete["id"] = "mem_lifecycle_incomplete_0001"
        incomplete["status"] = "retired"
        incomplete["valid_time"]["to"] = "2026-07-16T03:00:00Z"
        incomplete["supersession"] = {
            "supersedes": [],
            "superseded_by": None,
            "reason": "Legacy transition time unavailable.",
        }
        with self.assertRaisesRegex(self.memory.MemoryCLIError, "recorded_time_history_incomplete"):
            self.memory.query_records(
                [incomplete],
                as_of="2026-07-16T02:00:00Z",
                recorded_as_of="2026-07-16T02:30:00Z",
            )


if __name__ == "__main__":
    unittest.main()
