from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPT = DATABASE_DIR / "scripts/memory.py"
VALID_RECORDS = DATABASE_DIR / "tests/fixtures/memory_record_v2/valid_records.json"
SHARDING_CONTRACT = DATABASE_DIR / "config/memory.sharding.json"
MUTATION_POLICY = DATABASE_DIR / "config/memory-mutation-policy.json"
MUTATION_SCHEMA = DATABASE_DIR / "config/memory-mutation.schema.json"
LIFECYCLE_POLICY = DATABASE_DIR / "config/memory-lifecycle-policy.json"
FORGETTING_POLICY = DATABASE_DIR / "config/memory-forgetting-policy.json"


def load_memory():
    scripts_dir = str(DATABASE_DIR / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("memory_mutation_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, sys.modules["memory_mutation"]


class MemoryMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.memory, cls.mutation = load_memory()
        cls.records = json.loads(VALID_RECORDS.read_text(encoding="utf-8"))
        cls.policy = cls.memory.load_mutation_policy(
            DATABASE_DIR,
            Path("config/memory-mutation-policy.json"),
        )

    def envelope(
        self,
        *,
        source_type: str = "explicit_user",
        operation: str = "add",
        base: str = "1" * 40,
        label: str | None = None,
    ) -> dict[str, object]:
        repository_source = source_type == "repository_evidence"
        if operation == "add":
            target = {
                "record_id": None,
                "memory_key": f"fixture.mutation.{source_type.replace('_', '-')}",
                "scope": {
                    "type": "project" if repository_source else "global",
                    "key": "ExampleProject" if repository_source else "global",
                },
            }
        else:
            record = self.records[2]
            target = {
                "record_id": record["id"],
                "memory_key": record["memory_key"],
                "scope": record["scope"],
            }
        payload = None
        if operation in {"add", "update"}:
            payload = {
                "kind": "project_context" if repository_source else "preference",
                "statement": f"Governed fixture for {source_type} {operation}.",
                "confidence": "high",
                "importance": "medium",
                "aliases": [],
                "tags": ["mutation-fixture"],
                "negative_triggers": [],
            }
        request_label = label or f"{source_type}:{operation}"
        value = {
            "schema_version": "openai_database.memory_mutation.v1",
            "operation": operation,
            "idempotency_key": "",
            "base_commit_sha": base,
            "actor": {
                "type": "automation_c" if repository_source else "user_via_agent",
                "id": "fixture-agent",
            },
            "source": {
                "type": source_type,
                "ref": "repo:fixture" if repository_source else "user-message:fixture",
                "observed_at": "2026-07-17T00:00:00Z",
                "evidence_hash": "sha256:" + "a" * 64 if repository_source else None,
            },
            "authorization": {
                "mode": "repository_evidence_preapproved" if repository_source else "explicit_user_zero_human",
                "ref": f"owner-authorization:{request_label}",
                "authorized_at": "2026-07-17T00:01:00Z",
            },
            "target": target,
            "payload": payload,
            "valid_time": {"from": "2026-07-17T00:02:00Z", "to": None},
            "sensitivity": {
                "classification": "public",
                "handling": "public_text",
                "credential_present": False,
                "public_repository_allowed": True,
            },
            "reason": "Explicit governed mutation fixture.",
        }
        value["idempotency_key"] = self.mutation.expected_idempotency_key(value)
        return value

    def run_cli(self, database: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--database-dir", str(database), *args],
            cwd=database,
            text=True,
            capture_output=True,
            check=False,
        )

    def json_lines(self, result: subprocess.CompletedProcess[str]) -> list[dict[str, object]]:
        return [json.loads(line) for line in result.stdout.splitlines() if line]

    def write_database(self, database: Path) -> str:
        (database / "config").mkdir(parents=True)
        shutil.copy2(SHARDING_CONTRACT, database / "config/memory.sharding.json")
        shutil.copy2(MUTATION_POLICY, database / "config/memory-mutation-policy.json")
        shutil.copy2(LIFECYCLE_POLICY, database / "config/memory-lifecycle-policy.json")
        shutil.copy2(FORGETTING_POLICY, database / "config/memory-forgetting-policy.json")
        plan = self.memory.build_plan_for_records(self.records, self.memory.load_contract(database))
        target = database / "data/memory/records"
        target.mkdir(parents=True)
        for shard in plan.shards:
            (target / Path(shard.path).name).write_bytes(shard.payload)
        (target / "manifest.json").write_bytes(plan.manifest_bytes)
        commands = (
            ["git", "init", "-q", "-b", "main"],
            ["git", "config", "user.name", "Memory Mutation Test"],
            ["git", "config", "user.email", "memory-mutation@example.invalid"],
            ["git", "add", "."],
            ["git", "commit", "-q", "-m", "fixture"],
        )
        for command in commands:
            subprocess.run(command, cwd=database, check=True, capture_output=True, text=True)
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=database,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def read_records(self, database: Path) -> list[dict[str, object]]:
        records, _, _ = self.memory.load_input_records(database.resolve(), None)
        return records

    def test_schema_policy_and_source_operation_matrix(self) -> None:
        schema = json.loads(MUTATION_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], "openai_database.memory_mutation.v1")
        accepted = 0
        for source in ("explicit_user", "repository_evidence"):
            for operation in ("add", "update", "retire", "dispute"):
                with self.subTest(source=source, operation=operation):
                    outcome = self.memory.build_mutation_outcome(
                        self.records,
                        self.envelope(source_type=source, operation=operation),
                        self.policy,
                        current_base_sha="1" * 40,
                    )
                    self.assertEqual(outcome["details"]["model_inference_persisted"], 0)
                    self.assertFalse(outcome["details"]["manual_approval_required"])
                    accepted += 1
        self.assertEqual(accepted, 8)

        for source in ("raw_import", "model_inference"):
            for operation in ("add", "update", "retire", "dispute"):
                envelope = self.envelope(source_type=source, operation=operation)
                before = copy.deepcopy(self.records)
                with self.subTest(source=source, operation=operation):
                    with self.assertRaisesRegex(
                        self.memory.MutationAdmissionError,
                        "mutation_source_not_persistable",
                    ):
                        self.memory.build_mutation_outcome(
                            self.records,
                            envelope,
                            self.policy,
                            current_base_sha="1" * 40,
                        )
                    self.assertEqual(self.records, before)

    def test_add_plan_is_deterministic_redacted_and_apply_replay_is_zero_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "database"
            database.mkdir()
            base = self.write_database(database)
            envelope = self.envelope(base=base, label="cli-add-replay")
            envelope_path = database / "mutation.json"
            envelope_path.write_text(json.dumps(envelope), encoding="utf-8")

            first = self.run_cli(database, "mutate", "--envelope", "mutation.json")
            second = self.run_cli(database, "mutate", "--envelope", "mutation.json")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(first.stdout, second.stdout)
            plan = self.json_lines(first)[0]
            self.assertNotIn(str(envelope["payload"]["statement"]), first.stdout)
            self.assertTrue(plan["details"]["automation_c"]["transaction_required"])

            main_apply = self.run_cli(
                database,
                "mutate",
                "--envelope",
                "mutation.json",
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                str(envelope["idempotency_key"]),
            )
            self.assertEqual(main_apply.returncode, 2)
            self.assertEqual(self.json_lines(main_apply)[-1]["reason"], "mutation_apply_requires_exact_automation_c_branch")
            self.assertEqual(len(self.read_records(database)), len(self.records))

            branch = str(plan["details"]["automation_c"]["branch"])
            subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=database, check=True)
            applied = self.run_cli(
                database,
                "mutate",
                "--envelope",
                "mutation.json",
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                str(envelope["idempotency_key"]),
            )
            replay = self.run_cli(
                database,
                "mutate",
                "--envelope",
                "mutation.json",
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                str(envelope["idempotency_key"]),
            )
            self.assertEqual(applied.returncode, 0, applied.stdout)
            self.assertTrue(self.json_lines(applied)[-1]["writes_files"])
            self.assertEqual(replay.returncode, 0, replay.stdout)
            self.assertTrue(self.json_lines(replay)[-1]["idempotent"])
            self.assertEqual(len(self.read_records(database)), len(self.records) + 1)
            replay_plan = self.run_cli(database, "mutate", "--envelope", "mutation.json")
            self.assertFalse(self.json_lines(replay_plan)[0]["details"]["automation_c"]["transaction_required"])

    def test_update_replay_creates_one_new_record_and_retires_one_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "database"
            database.mkdir()
            base = self.write_database(database)
            envelope = self.envelope(operation="update", base=base, label="cli-update-replay")
            (database / "mutation.json").write_text(json.dumps(envelope), encoding="utf-8")
            plan = self.json_lines(self.run_cli(database, "mutate", "--envelope", "mutation.json"))[0]
            branch = str(plan["details"]["automation_c"]["branch"])
            subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=database, check=True)
            args = (
                "mutate",
                "--envelope",
                "mutation.json",
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                str(envelope["idempotency_key"]),
            )
            first = self.run_cli(database, *args)
            second = self.run_cli(database, *args)
            self.assertEqual(first.returncode, 0, first.stdout)
            self.assertEqual(second.returncode, 0, second.stdout)
            records = {record["id"]: record for record in self.read_records(database)}
            new_id = str(plan["details"]["record_id"])
            old_id = str(envelope["target"]["record_id"])
            self.assertEqual(len(records), len(self.records) + 1)
            self.assertEqual(records[old_id]["status"], "retired")
            self.assertEqual(records[old_id]["supersession"]["superseded_by"], new_id)
            self.assertEqual(records[new_id]["status"], "active")
            self.assertEqual(records[new_id]["supersession"]["supersedes"], [old_id])

    def test_stale_base_authorization_scope_and_credential_fail_before_write(self) -> None:
        tampered = self.envelope()
        tampered["target"]["memory_key"] = "fixture.mutation.tampered"
        with self.assertRaisesRegex(self.memory.MutationAdmissionError, "mutation_idempotency_key_content_mismatch"):
            self.memory.build_mutation_outcome(
                self.records,
                tampered,
                self.policy,
                current_base_sha="1" * 40,
            )

        stale = self.envelope()
        with self.assertRaisesRegex(self.memory.MutationAdmissionError, "mutation_base_sha_mismatch"):
            self.memory.build_mutation_outcome(
                self.records,
                stale,
                self.policy,
                current_base_sha="2" * 40,
            )

        unauthorized = self.envelope()
        unauthorized["authorization"]["mode"] = "none"
        unauthorized["idempotency_key"] = self.mutation.expected_idempotency_key(unauthorized)
        with self.assertRaisesRegex(self.memory.MutationAdmissionError, "mutation_authorization_missing_or_invalid"):
            self.memory.build_mutation_outcome(
                self.records,
                unauthorized,
                self.policy,
                current_base_sha="1" * 40,
            )

        wrong_scope = self.envelope(source_type="repository_evidence")
        wrong_scope["target"]["scope"] = {"type": "global", "key": "global"}
        wrong_scope["idempotency_key"] = self.mutation.expected_idempotency_key(wrong_scope)
        with self.assertRaisesRegex(self.memory.MutationAdmissionError, "mutation_scope_not_authorized_for_source"):
            self.memory.build_mutation_outcome(
                self.records,
                wrong_scope,
                self.policy,
                current_base_sha="1" * 40,
            )

        credential = self.envelope()
        credential["payload"]["statement"] = "pass" + "word=ExampleCredential123"
        credential["idempotency_key"] = self.mutation.expected_idempotency_key(credential)
        with self.assertRaises(self.memory.PrivacyViolation):
            self.memory.build_mutation_outcome(
                self.records,
                credential,
                self.policy,
                current_base_sha="1" * 40,
            )

    def test_unresolved_conflict_blocks_apply_before_canonical_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "database"
            database.mkdir()
            base = self.write_database(database)
            envelope = self.envelope(operation="dispute", base=base, label="blocked-dispute")
            (database / "mutation.json").write_text(json.dumps(envelope), encoding="utf-8")
            planned = self.run_cli(database, "mutate", "--envelope", "mutation.json")
            plan = self.json_lines(planned)[0]

            self.assertEqual(planned.returncode, 0, planned.stdout)
            self.assertFalse(plan["details"]["lifecycle"]["settlement_allowed"])
            self.assertEqual(len(plan["details"]["lifecycle"]["unresolved_conflict_ids"]), 1)
            branch = str(plan["details"]["automation_c"]["branch"])
            subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=database, check=True)
            applied = self.run_cli(
                database,
                "mutate",
                "--envelope",
                "mutation.json",
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                str(envelope["idempotency_key"]),
            )

            self.assertEqual(applied.returncode, 2, applied.stdout)
            self.assertEqual(
                self.json_lines(applied)[-1]["reason"],
                "lifecycle_unresolved_conflict_blocks_settlement",
            )
            self.assertEqual(
                {record["id"]: record for record in self.read_records(database)},
                {record["id"]: record for record in self.records},
            )


if __name__ == "__main__":
    unittest.main()
