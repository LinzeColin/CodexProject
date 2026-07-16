from __future__ import annotations

import hashlib
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
LEGACY_RAW_SCRIPT = DATABASE_DIR / "scripts/import_public_raw_evidence.py"
VALID_RECORDS = DATABASE_DIR / "tests/fixtures/memory_record_v2/valid_records.json"
SHARDING_CONTRACT = DATABASE_DIR / "config/memory.sharding.json"
LIFECYCLE_POLICY = DATABASE_DIR / "config/memory-lifecycle-policy.json"
FORGETTING_POLICY = DATABASE_DIR / "config/memory-forgetting-policy.json"
RAW_IMPORT_CONTRACT = DATABASE_DIR / "config/storage/raw_import.json"
SECURITY_POLICY = DATABASE_DIR / "config/memory-security-policy.json"


def load_module():
    spec = importlib.util.spec_from_file_location("memory_cli_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MemoryCLITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.records = json.loads(VALID_RECORDS.read_text(encoding="utf-8"))

    def run_cli(
        self,
        database: Path,
        *args: str,
        script: Path = SCRIPT,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), "--database-dir", str(database), *args],
            cwd=database,
            text=True,
            capture_output=True,
            check=False,
        )

    def json_lines(self, result: subprocess.CompletedProcess[str]) -> list[dict[str, object]]:
        return [json.loads(line) for line in result.stdout.splitlines() if line]

    def copy_contracts(self, database: Path, *, raw: bool = False) -> None:
        (database / "config/storage").mkdir(parents=True, exist_ok=True)
        shutil.copy2(SHARDING_CONTRACT, database / "config/memory.sharding.json")
        shutil.copy2(LIFECYCLE_POLICY, database / "config/memory-lifecycle-policy.json")
        shutil.copy2(FORGETTING_POLICY, database / "config/memory-forgetting-policy.json")
        if raw:
            shutil.copy2(RAW_IMPORT_CONTRACT, database / "config/storage/raw_import.json")
            shutil.copy2(SECURITY_POLICY, database / "config/memory-security-policy.json")

    def write_canonical_fixture(self, database: Path) -> bytes:
        self.copy_contracts(database)
        contract = self.module.load_contract(database)
        plan = self.module.build_plan_for_records(self.records, contract)
        target = database / "data/memory/records"
        target.mkdir(parents=True)
        for shard in plan.shards:
            (target / Path(shard.path).name).write_bytes(shard.payload)
        (target / "manifest.json").write_bytes(plan.manifest_bytes)
        return b"".join(shard.payload for shard in plan.shards)

    def write_input_fixture(self, database: Path) -> Path:
        self.copy_contracts(database)
        plan = self.module.build_plan_for_records(self.records, self.module.load_contract(database))
        path = database / "candidate.jsonl"
        path.write_bytes(b"".join(shard.payload for shard in plan.shards))
        return path

    def init_git(self, database: Path) -> str:
        commands = (
            ["git", "init", "-q"],
            ["git", "config", "user.name", "Memory CLI Test"],
            ["git", "config", "user.email", "memory-cli@example.invalid"],
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

    def raw_authorization(self, payload: bytes) -> dict[str, object]:
        return {
            "schema_version": "openai_database.raw_import_authorization.v1",
            "authorization_id": "AUTH-PAM1-0006-TEST",
            "owner_id": "test-owner",
            "decision": "approved_publication",
            "authorized_at": "2026-07-16T00:00:00Z",
            "content_rights_confirmed": True,
            "public_repository_allowed": True,
            "source_id": "fixture",
            "source_ref": "authorized/fixture.md",
            "observed_at": "2026-07-15T23:00:00Z",
            "source_sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
        }

    def test_help_exposes_exact_unified_subcommands(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            cwd=DATABASE_DIR,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in (
            "validate",
            "build",
            "query",
            "import",
            "export",
            "doctor",
            "benchmark",
            "mutate",
            "apply",
        ):
            self.assertIn(command, result.stdout)

    def test_validate_build_and_export_are_offline_and_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "database"
            database.mkdir()
            expected_jsonl = self.write_canonical_fixture(database)

            validated = self.run_cli(database, "validate")
            first = self.run_cli(database, "build")
            second = self.run_cli(database, "build")
            exported = self.run_cli(database, "export", "--format", "jsonl")

            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(exported.returncode, 0, exported.stderr)
            self.assertEqual(exported.stdout.encode("utf-8"), expected_jsonl)
            payload = self.json_lines(first)[0]
            self.assertTrue(payload["details"]["repeat_build_identical"])
            self.assertEqual(
                payload["details"]["dataset_sha256"],
                "sha256:" + hashlib.sha256(expected_jsonl).hexdigest(),
            )

    def test_query_filters_active_current_and_historical_as_of(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "database"
            database.mkdir()
            self.write_canonical_fixture(database)

            current = self.run_cli(database, "query", "--key", "project.example.runtime", "--full")
            historical = self.run_cli(
                database,
                "query",
                "--key",
                "project.example.runtime",
                "--as-of",
                "2026-07-15T12:00:00Z",
                "--full",
            )
            combined = self.run_cli(
                database,
                "query",
                "--id",
                "mem_fixture_user_0001",
                "--key",
                "preference.output-language",
                "--kind",
                "preference",
                "--scope",
                "global:global",
                "--tag",
                "language",
                "--keyword",
                "中文",
            )
            candidate = self.run_cli(
                database,
                "query",
                "--id",
                "mem_fixture_inference_0004",
                "--include-inactive",
            )
            before_recording = self.run_cli(
                database,
                "query",
                "--key",
                "project.example.runtime",
                "--as-of",
                "2026-07-16T00:02:30Z",
                "--recorded-as-of",
                "2026-07-16T00:02:30Z",
            )
            after_recording = self.run_cli(
                database,
                "query",
                "--key",
                "project.example.runtime",
                "--as-of",
                "2026-07-16T00:02:30Z",
                "--recorded-as-of",
                "2026-07-16T00:03:30Z",
            )
            missing_valid_axis = self.run_cli(
                database,
                "query",
                "--recorded-as-of",
                "2026-07-16T00:03:30Z",
            )

            current_payload = self.json_lines(current)[0]
            historical_payload = self.json_lines(historical)[0]
            candidate_payload = self.json_lines(candidate)[0]
            self.assertEqual(current_payload["records"][0]["id"], "mem_fixture_project_0003")
            self.assertEqual(current_payload["task_id"], "TSK.OpenAIDatabase.PAM1.0011")
            self.assertEqual(current_payload["acceptance_id"], "ACC.OpenAIDatabase.PAM1.0011")
            self.assertEqual(current_payload["retrieval_decision"]["state"], "answer")
            self.assertEqual(
                historical_payload["records"][0]["id"],
                "mem_fixture_project_0002",
            )
            self.assertEqual(historical_payload["retrieval_decision"]["state"], "historical")
            self.assertEqual(self.json_lines(combined)[0]["returned_count"], 1)
            self.assertEqual(candidate_payload["returned_count"], 1)
            self.assertEqual(candidate_payload["retrieval_decision"]["state"], "abstain")
            self.assertFalse(candidate_payload["retrieval_decision"]["inactive_answer_eligible"])
            self.assertEqual(
                self.json_lines(before_recording)[0]["records"][0]["id"],
                "mem_fixture_project_0002",
            )
            self.assertEqual(
                self.json_lines(after_recording)[0]["records"][0]["id"],
                "mem_fixture_project_0003",
            )
            self.assertEqual(self.json_lines(after_recording)[0]["query_mode"], "bitemporal_as_of")
            self.assertEqual(missing_valid_axis.returncode, 2)
            self.assertEqual(
                self.json_lines(missing_valid_axis)[0]["reason"],
                "recorded_as_of_requires_as_of",
            )

    def test_errors_are_json_and_path_encoding_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "database"
            database.mkdir()
            self.write_canonical_fixture(database)
            (database / "invalid.jsonl").write_bytes(b"\xff\n")

            cases = (
                self.run_cli(database, "build", "--input", "../escape.jsonl"),
                self.run_cli(database, "build", "--input", "invalid.jsonl"),
                self.run_cli(database, "query", "--limit", "999"),
                self.run_cli(database, "query", "--unknown"),
            )
            for result in cases:
                with self.subTest(stdout=result.stdout):
                    self.assertEqual(result.returncode, 2)
                    payload = self.json_lines(result)[-1]
                    self.assertEqual(payload["status"], "FAIL_CLOSED")
                    self.assertFalse(payload["writes_files"])

    def test_apply_requires_plan_base_idempotency_and_single_flight(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "database"
            database.mkdir()
            self.write_input_fixture(database)
            base = self.init_git(database)
            target = database / "data/memory/records"

            planned = self.run_cli(database, "apply", "--input", "candidate.jsonl")
            plan = self.json_lines(planned)[0]
            key = str(plan["required_idempotency_key"])
            self.assertEqual(planned.returncode, 0)
            self.assertFalse(target.exists())

            stale = self.run_cli(
                database,
                "apply",
                "--input",
                "candidate.jsonl",
                "--apply",
                "--base-sha",
                "0" * 40,
                "--idempotency-key",
                key,
            )
            self.assertEqual(stale.returncode, 2)
            self.assertEqual(self.json_lines(stale)[-1]["reason"], "base_sha_mismatch")
            self.assertFalse(target.exists())

            lock = database / ".git/openai-memory-cli.lock"
            lock.write_text("occupied\n", encoding="utf-8")
            occupied = self.run_cli(
                database,
                "apply",
                "--input",
                "candidate.jsonl",
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                key,
            )
            self.assertEqual(self.json_lines(occupied)[-1]["reason"], "active_memory_transaction")
            self.assertFalse(target.exists())
            lock.unlink()

            applied = self.run_cli(
                database,
                "apply",
                "--input",
                "candidate.jsonl",
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                key,
            )
            repeated = self.run_cli(
                database,
                "apply",
                "--input",
                "candidate.jsonl",
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                key,
            )
            applied_lines = self.json_lines(applied)
            repeated_lines = self.json_lines(repeated)
            self.assertEqual([row["event"] for row in applied_lines], ["PLAN", "RESULT"])
            self.assertTrue(applied_lines[1]["writes_files"])
            self.assertFalse(repeated_lines[1]["writes_files"])
            self.assertTrue(repeated_lines[1]["idempotent"])
            self.assertEqual(self.run_cli(database, "validate").returncode, 0)

            before_manifest = (target / "manifest.json").read_bytes()
            reduced_plan = self.module.build_plan_for_records(
                [self.records[0]], self.module.load_contract(database)
            )
            (database / "reduced.jsonl").write_bytes(
                b"".join(shard.payload for shard in reduced_plan.shards)
            )
            reduced_dry_run = self.run_cli(database, "apply", "--input", "reduced.jsonl")
            reduced_key = str(self.json_lines(reduced_dry_run)[0]["required_idempotency_key"])
            rejected = self.run_cli(
                database,
                "apply",
                "--input",
                "reduced.jsonl",
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                reduced_key,
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual(
                self.json_lines(rejected)[-1]["reason"],
                "canonical_mutation_admission_required",
            )
            self.assertEqual((target / "manifest.json").read_bytes(), before_manifest)

    def test_raw_import_and_legacy_command_share_one_plan_owner(self) -> None:
        payload = "已授权的最小公开证据。\n".encode("utf-8")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database = root / "database"
            database.mkdir()
            self.copy_contracts(database, raw=True)
            source_root = root / "source"
            source_root.mkdir()
            (source_root / "evidence.md").write_bytes(payload)
            authorization = root / "authorization.json"
            authorization.write_text(
                json.dumps(self.raw_authorization(payload), sort_keys=True),
                encoding="utf-8",
            )
            args = (
                "--source-root",
                str(source_root),
                "--source",
                "evidence.md",
                "--authorization",
                str(authorization),
            )
            direct = self.run_cli(database, "import", *args)
            wrapper = self.run_cli(database, "plan", *args, script=LEGACY_RAW_SCRIPT)
            direct_plan = self.json_lines(direct)[0]
            wrapper_plan = self.json_lines(wrapper)[0]

            self.assertEqual(direct.returncode, 0, direct.stderr)
            self.assertEqual(wrapper.returncode, 0, wrapper.stderr)
            self.assertEqual(direct_plan["plan_sha256"], wrapper_plan["plan_sha256"])
            self.assertTrue(direct_plan["details"]["artifact_plan_sha256"].startswith("sha256:"))
            self.assertFalse((database / "data/public_raw").exists())

            base = self.init_git(database)
            key = str(direct_plan["required_idempotency_key"])
            applied = self.run_cli(
                database,
                "import",
                *args,
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                key,
            )
            repeated = self.run_cli(
                database,
                "import",
                *args,
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                key,
            )
            applied_lines = self.json_lines(applied)
            repeated_lines = self.json_lines(repeated)
            self.assertEqual([row["event"] for row in applied_lines], ["PLAN", "RESULT"])
            self.assertTrue(applied_lines[1]["writes_files"])
            self.assertTrue(repeated_lines[1]["idempotent"])
            self.assertEqual(applied_lines[1]["automatic_active_promotion_count"], 0)

    def test_actual_doctor_and_benchmark_pass_without_extra_samples(self) -> None:
        doctor = self.run_cli(DATABASE_DIR, "doctor")
        benchmark = self.run_cli(DATABASE_DIR, "benchmark", "--iterations", "1")
        doctor_payload = self.json_lines(doctor)[0]
        benchmark_payload = self.json_lines(benchmark)[0]

        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        self.assertEqual(doctor_payload["legacy_independent_writer_count"], 0)
        self.assertEqual(benchmark.returncode, 0, benchmark.stderr)
        self.assertEqual(benchmark_payload["iterations"], 1)


if __name__ == "__main__":
    unittest.main()
