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
FORGETTING_POLICY = DATABASE_DIR / "config/memory-forgetting-policy.json"
DOC = DATABASE_DIR / "docs/MEMORY_FORGETTING_AND_REFUSAL.md"
EXECUTION_TIME = datetime(2026, 7, 16, 6, 0, tzinfo=timezone.utc)


def load_memory():
    scripts_dir = str(DATABASE_DIR / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("memory_forgetting_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, sys.modules["memory_forgetting"], sys.modules["memory_mutation"]


class MemoryForgettingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.memory, cls.forgetting, cls.mutation = load_memory()
        cls.records = json.loads(VALID_RECORDS.read_text(encoding="utf-8"))
        cls.policy = cls.forgetting.load_policy(FORGETTING_POLICY)
        cls.mutation_policy = cls.memory.load_mutation_policy(
            DATABASE_DIR,
            Path("config/memory-mutation-policy.json"),
        )

    def envelope(
        self,
        *,
        operation: str,
        label: str,
        valid_from: str,
        target: dict[str, object] | None = None,
        kind: str = "fact",
        statement: str = "Confirmed current fact.",
        negative_triggers: list[str] | None = None,
    ) -> dict[str, object]:
        add = operation == "add"
        target_record = target or {}
        value: dict[str, object] = {
            "schema_version": "openai_database.memory_mutation.v1",
            "operation": operation,
            "idempotency_key": "",
            "base_commit_sha": "1" * 40,
            "actor": {"type": "user_via_agent", "id": "forgetting-test-agent"},
            "source": {
                "type": "explicit_user",
                "ref": f"user-message:{label}",
                "observed_at": "2026-07-16T02:00:00Z",
                "evidence_hash": None,
            },
            "authorization": {
                "mode": "explicit_user_zero_human",
                "ref": f"owner-authorization:{label}",
                "authorized_at": "2026-07-16T03:00:00Z",
            },
            "target": {
                "record_id": None if add else target_record["id"],
                "memory_key": (
                    f"negative.boundary.{label}"
                    if add
                    else target_record["memory_key"]
                ),
                "scope": (
                    {"type": "project", "key": "ExampleProject"}
                    if add
                    else copy.deepcopy(target_record["scope"])
                ),
            },
            "payload": (
                {
                    "kind": kind,
                    "statement": statement,
                    "confidence": "high",
                    "importance": "high",
                    "aliases": [],
                    "tags": ["forgetting-regression"],
                    "negative_triggers": negative_triggers or [],
                }
                if operation in {"add", "update"}
                else None
            ),
            "valid_time": {"from": valid_from, "to": None},
            "sensitivity": {
                "classification": "public",
                "handling": "public_text",
                "credential_present": False,
                "public_repository_allowed": True,
            },
            "reason": "Deterministic forgetting and refusal regression.",
        }
        value["idempotency_key"] = self.mutation.expected_idempotency_key(value)
        return value

    def query(
        self,
        records: list[dict[str, object]],
        *,
        record_id: str | None = None,
        key: str | None = None,
        as_of: str | None = None,
        include_inactive: bool = False,
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        trace: dict[str, object] = {}
        results, _ = self.memory.query_records(
            records,
            record_id=record_id,
            key=key,
            as_of=as_of,
            include_inactive=include_inactive,
            limit=200,
            execution_time=EXECUTION_TIME,
            trace=trace,
        )
        decision = self.forgetting.retrieval_decision(
            results,
            trace,
            query_mode="valid_as_of" if as_of else "current",
            include_inactive=include_inactive,
        )
        return results, decision

    def test_policy_schema_baseline_and_fama_formula_are_exact(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        canonical, _, _ = self.memory.load_input_records(DATABASE_DIR, None)
        assessment = self.forgetting.assess_forgetting_dataset(
            canonical,
            execution_time=EXECUTION_TIME,
        )
        score = self.forgetting.fama_score(
            presence_total=2,
            presence_satisfied=2,
            forgetting_total=2,
            forgetting_satisfied=1,
        )

        self.assertEqual(self.policy["current_answer"]["eligible_statuses"], ["active"])
        self.assertEqual(self.policy["current_answer"]["critical_stale_use_max"], 0)
        self.assertFalse(self.policy["negative_memory"]["infer_from_absence"])
        self.assertFalse(self.policy["privacy"]["public_git_history_is_erasure"])
        self.assertEqual(schema["x-forgetting-contract"]["acceptance_id"], "ACC.OpenAIDatabase.PAM1.0011")
        self.assertEqual(schema["x-query-contract"]["include_inactive_mode"], "audit_only_never_answer")
        self.assertEqual(assessment["record_count"], 198)
        self.assertEqual(assessment["current_answer_eligible_count"], 6)
        self.assertEqual(assessment["inactive_answer_eligible_count"], 0)
        self.assertEqual(assessment["absence_inference_count"], 0)
        self.assertEqual(score["memory_presence_accuracy"], 1.0)
        self.assertEqual(score["forgetting_absence_accuracy"], 0.5)
        self.assertEqual(score["forgetting_weight"], 0.5)
        self.assertEqual(score["fama"], 0.75)
        self.assertIn("not a privacy erasure guarantee", DOC.read_text(encoding="utf-8"))

    def test_negative_memory_requires_authority_verification_trigger_and_validity(self) -> None:
        base = copy.deepcopy(self.records[0])
        base["kind"] = "negative_trigger"
        base["negative_triggers"] = ["This assertion is no longer applicable."]

        missing_trigger = copy.deepcopy(base)
        missing_trigger["negative_triggers"] = []
        with self.assertRaisesRegex(self.forgetting.ForgettingError, "negative_memory_triggers_required"):
            self.forgetting.validate_negative_memory_record(missing_trigger)

        wrong_authority = copy.deepcopy(base)
        wrong_authority["source"]["type"] = "raw_import"
        with self.assertRaisesRegex(self.forgetting.ForgettingError, "negative_memory_authority_invalid"):
            self.forgetting.validate_negative_memory_record(wrong_authority)

        unverified = copy.deepcopy(base)
        unverified["verification"]["state"] = "unverified"
        with self.assertRaisesRegex(self.forgetting.ForgettingError, "negative_memory_not_verified"):
            self.forgetting.validate_negative_memory_record(unverified)

        invalid_validity = copy.deepcopy(base)
        invalid_validity["valid_time"]["to"] = invalid_validity["valid_time"]["from"]
        with self.assertRaisesRegex(self.forgetting.ForgettingError, "negative_memory_valid_interval_invalid"):
            self.forgetting.validate_negative_memory_record(invalid_validity)

    def test_active_only_history_and_audit_only_inactive_are_explicit(self) -> None:
        active = self.records[0]
        retired = self.records[1]
        candidate = self.records[3]
        disputed = copy.deepcopy(active)
        disputed["id"] = "mem_forgetting_disputed_0001"
        disputed["status"] = "disputed"
        disputed["conflict"] = {
            "state": "unresolved",
            "with": [],
            "resolution": None,
        }
        expired_active = copy.deepcopy(active)
        expired_active["id"] = "mem_forgetting_expired_active_0001"
        expired_active["valid_time"]["to"] = "2026-07-16T01:00:00Z"

        active_rows, active_decision = self.query(self.records, record_id=str(active["id"]))
        retired_rows, retired_decision = self.query(self.records, record_id=str(retired["id"]))
        candidate_rows, candidate_decision = self.query(self.records, record_id=str(candidate["id"]))
        disputed_rows, disputed_decision = self.query([disputed], record_id=str(disputed["id"]))
        audit_rows, audit_decision = self.query(
            [disputed],
            record_id=str(disputed["id"]),
            include_inactive=True,
        )
        expired_audit_rows, expired_audit_decision = self.query(
            [expired_active],
            record_id=str(expired_active["id"]),
            include_inactive=True,
        )
        missing_rows, missing_decision = self.query(self.records, record_id="mem_missing_record_0001")
        history_rows, history_decision = self.query(
            self.records,
            record_id=str(retired["id"]),
            as_of="2026-07-15T12:00:00Z",
        )

        self.assertEqual([row["id"] for row in active_rows], [active["id"]])
        self.assertEqual(active_decision["state"], "answer")
        self.assertTrue(active_decision["positive_assertion_allowed"])
        self.assertEqual(retired_rows, [])
        self.assertEqual(retired_decision["reason_code"], "retired_or_expired")
        self.assertEqual(candidate_rows, [])
        self.assertEqual(candidate_decision["reason_code"], "candidate_or_unverified")
        self.assertEqual(disputed_rows, [])
        self.assertEqual(disputed_decision["reason_code"], "unresolved_conflict")
        self.assertEqual(len(audit_rows), 1)
        self.assertEqual(audit_decision["state"], "abstain")
        self.assertEqual(audit_decision["audit_only_count"], 1)
        self.assertFalse(audit_decision["inactive_answer_eligible"])
        self.assertEqual(len(expired_audit_rows), 1)
        self.assertFalse(expired_audit_rows[0]["query_state"]["retrieval_eligible"])
        self.assertEqual(expired_audit_decision["state"], "abstain")
        self.assertEqual(expired_audit_decision["reason_code"], "retired_or_expired")
        self.assertEqual(
            expired_audit_decision["missing_conditions"],
            ["current_validity", "verified_active_record"],
        )
        self.assertEqual(expired_audit_decision["audit_only_count"], 1)
        self.assertEqual(missing_rows, [])
        self.assertEqual(missing_decision["knowledge_state"], "UNKNOWN")
        self.assertEqual(missing_decision["missing_conditions"], ["verified_active_record"])
        self.assertEqual([row["id"] for row in history_rows], [retired["id"]])
        self.assertEqual(history_decision["state"], "historical")
        self.assertFalse(history_decision["positive_assertion_allowed"])
        self.assertTrue(history_decision["historical_assertion_only"])

    def test_real_mutations_meet_stale_fama_abstention_and_negative_gates(self) -> None:
        current = self.records[2]
        update = self.memory.build_mutation_outcome(
            self.records,
            self.envelope(
                operation="update",
                label="update",
                valid_from="2026-07-16T01:00:00Z",
                target=current,
                kind=str(current["kind"]),
                statement="Confirmed runtime fact after update.",
            ),
            self.mutation_policy,
            current_base_sha="1" * 40,
        )
        updated_id = str(update["details"]["record_id"])
        update_rows, update_decision = self.query(
            update["records"],
            key=str(current["memory_key"]),
        )

        active = self.records[0]
        retire = self.memory.build_mutation_outcome(
            self.records,
            self.envelope(
                operation="retire",
                label="retire",
                valid_from="2026-07-16T01:00:00Z",
                target=active,
            ),
            self.mutation_policy,
            current_base_sha="1" * 40,
        )
        retire_rows, retire_decision = self.query(
            retire["records"],
            record_id=str(active["id"]),
        )

        dispute = self.memory.build_mutation_outcome(
            self.records,
            self.envelope(
                operation="dispute",
                label="dispute",
                valid_from="2026-07-16T01:00:00Z",
                target=active,
            ),
            self.mutation_policy,
            current_base_sha="1" * 40,
        )
        dispute_rows, dispute_decision = self.query(
            dispute["records"],
            record_id=str(active["id"]),
        )

        candidate = self.records[3]
        candidate_rows, candidate_decision = self.query(
            self.records,
            record_id=str(candidate["id"]),
        )
        missing_rows, missing_decision = self.query(
            self.records,
            record_id="mem_no_evidence_0001",
        )

        negative_envelope = self.envelope(
            operation="add",
            label="not-applicable",
            valid_from="2026-07-16T01:00:00Z",
            kind="negative_trigger",
            statement="The superseded workflow is confirmed no longer applicable.",
            negative_triggers=["Do not use the superseded workflow as current guidance."],
        )
        negative = self.memory.build_mutation_outcome(
            self.records,
            negative_envelope,
            self.mutation_policy,
            current_base_sha="1" * 40,
        )
        negative_id = str(negative["details"]["record_id"])
        negative_rows, negative_decision = self.query(
            negative["records"],
            key=str(negative_envelope["target"]["memory_key"]),
        )

        cases = [
            {
                "case_id": "update",
                "critical": True,
                "expected_record_ids": [updated_id],
                "forbidden_record_ids": [str(current["id"])],
                "returned_record_ids": [str(row["id"]) for row in update_rows],
                "should_abstain": False,
                "decision_state": update_decision["state"],
            },
            {
                "case_id": "retire",
                "critical": True,
                "expected_record_ids": [],
                "forbidden_record_ids": [str(active["id"])],
                "returned_record_ids": [str(row["id"]) for row in retire_rows],
                "should_abstain": True,
                "decision_state": retire_decision["state"],
            },
            {
                "case_id": "dispute",
                "critical": True,
                "expected_record_ids": [],
                "forbidden_record_ids": [str(active["id"])],
                "returned_record_ids": [str(row["id"]) for row in dispute_rows],
                "should_abstain": True,
                "decision_state": dispute_decision["state"],
            },
            {
                "case_id": "candidate",
                "critical": True,
                "expected_record_ids": [],
                "forbidden_record_ids": [str(candidate["id"])],
                "returned_record_ids": [str(row["id"]) for row in candidate_rows],
                "should_abstain": True,
                "decision_state": candidate_decision["state"],
            },
            {
                "case_id": "missing",
                "critical": True,
                "expected_record_ids": [],
                "forbidden_record_ids": [],
                "returned_record_ids": [str(row["id"]) for row in missing_rows],
                "should_abstain": True,
                "decision_state": missing_decision["state"],
            },
            {
                "case_id": "negative-boundary",
                "critical": True,
                "expected_record_ids": [negative_id],
                "forbidden_record_ids": [],
                "returned_record_ids": [str(row["id"]) for row in negative_rows],
                "should_abstain": False,
                "decision_state": negative_decision["state"],
            },
        ]
        evaluation = self.forgetting.evaluate_forgetting_cases(cases, self.policy)

        self.assertEqual([row["id"] for row in update_rows], [updated_id])
        self.assertEqual(retire_decision["state"], "abstain")
        self.assertEqual(dispute_decision["state"], "abstain")
        self.assertEqual(candidate_decision["state"], "abstain")
        self.assertEqual(missing_decision["state"], "abstain")
        self.assertEqual([row["id"] for row in negative_rows], [negative_id])
        self.assertEqual(negative_decision["state"], "negative_boundary")
        self.assertFalse(negative_decision["positive_assertion_allowed"])
        self.assertTrue(negative_decision["confirmed_negative_assertion_allowed"])
        self.assertEqual(evaluation["case_count"], 6)
        self.assertEqual(evaluation["critical_stale_use_count"], 0)
        self.assertEqual(evaluation["fama"], 1.0)
        self.assertEqual(evaluation["abstention_precision"], 1.0)
        self.assertEqual(evaluation["abstention_recall"], 1.0)
        self.assertTrue(evaluation["passed"])


if __name__ == "__main__":
    unittest.main()
