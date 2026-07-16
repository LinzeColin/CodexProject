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
ROUTER = DATABASE_DIR / "scripts/route_agent_resources.py"
VALID_RECORDS = DATABASE_DIR / "tests/fixtures/memory_record_v2/valid_records.json"
SHARDING_CONTRACT = DATABASE_DIR / "config/memory.sharding.json"
MEMORY_SCHEMA = DATABASE_DIR / "config/memory.schema.json"
HANDSHAKE_SCHEMA = DATABASE_DIR / "config/agent-memory.schema.json"
TRANSPORT_PROFILES = DATABASE_DIR / "config/agent_transport_profiles.json"
TRANSPORT_INSTRUCTIONS = DATABASE_DIR / "docs/AGENT_TRANSPORT_COMPATIBILITY.md"
TRANSPORT_HARNESS = DATABASE_DIR / "scripts/validate_agent_transport_compatibility.py"
MUTATION_SCHEMA = DATABASE_DIR / "config/memory-mutation.schema.json"
MUTATION_POLICY = DATABASE_DIR / "config/memory-mutation-policy.json"
MUTATION_INSTRUCTIONS = DATABASE_DIR / "docs/MEMORY_MUTATION_TRANSACTIONS.md"
LIFECYCLE_POLICY = DATABASE_DIR / "config/memory-lifecycle-policy.json"
FORGETTING_POLICY = DATABASE_DIR / "config/memory-forgetting-policy.json"
FORGETTING_INSTRUCTIONS = DATABASE_DIR / "docs/MEMORY_FORGETTING_AND_REFUSAL.md"
SECURITY_POLICY = DATABASE_DIR / "config/memory-security-policy.json"
RETRIEVAL_CONFIG = DATABASE_DIR / "config/evaluation/memory_retrieval_performance_v1.json"
RETRIEVAL_IMPLEMENTATION = DATABASE_DIR / "scripts/memory_retrieval.py"
COMPACT = Path("data/memory/AGENT_MEMORY.md")
MACHINE = Path("data/memory/agent-memory.json")


def load_script(name: str, path: Path):
    scripts_dir = str(DATABASE_DIR / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AgentMemoryViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.memory = load_script("agent_memory_view_test", SCRIPT)
        cls.router = load_script("agent_memory_route_test", ROUTER)
        cls.records = json.loads(VALID_RECORDS.read_text(encoding="utf-8"))

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

    def write_fixture(self, database: Path) -> str:
        (database / "config").mkdir(parents=True)
        shutil.copy2(SHARDING_CONTRACT, database / "config/memory.sharding.json")
        shutil.copy2(MEMORY_SCHEMA, database / "config/memory.schema.json")
        shutil.copy2(HANDSHAKE_SCHEMA, database / "config/agent-memory.schema.json")
        for source, relative in (
            (TRANSPORT_PROFILES, Path("config/agent_transport_profiles.json")),
            (TRANSPORT_INSTRUCTIONS, Path("docs/AGENT_TRANSPORT_COMPATIBILITY.md")),
            (TRANSPORT_HARNESS, Path("scripts/validate_agent_transport_compatibility.py")),
            (MUTATION_SCHEMA, Path("config/memory-mutation.schema.json")),
            (MUTATION_POLICY, Path("config/memory-mutation-policy.json")),
            (MUTATION_INSTRUCTIONS, Path("docs/MEMORY_MUTATION_TRANSACTIONS.md")),
            (LIFECYCLE_POLICY, Path("config/memory-lifecycle-policy.json")),
            (FORGETTING_POLICY, Path("config/memory-forgetting-policy.json")),
            (FORGETTING_INSTRUCTIONS, Path("docs/MEMORY_FORGETTING_AND_REFUSAL.md")),
            (SECURITY_POLICY, Path("config/memory-security-policy.json")),
            (RETRIEVAL_CONFIG, Path("config/evaluation/memory_retrieval_performance_v1.json")),
            (RETRIEVAL_IMPLEMENTATION, Path("scripts/memory_retrieval.py")),
        ):
            target = database / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        plan = self.memory.build_plan_for_records(self.records, self.memory.load_contract(database))
        target = database / "data/memory/records"
        target.mkdir(parents=True)
        for shard in plan.shards:
            (target / Path(shard.path).name).write_bytes(shard.payload)
        (target / "manifest.json").write_bytes(plan.manifest_bytes)
        commands = (
            ["git", "init", "-q"],
            ["git", "config", "user.name", "Agent Memory Test"],
            ["git", "config", "user.email", "agent-memory@example.invalid"],
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

    def test_repository_views_are_bounded_deterministic_and_source_bound(self) -> None:
        first_plan, first_artifacts, handshake = self.memory.build_agent_memory_views(DATABASE_DIR)
        second_plan, second_artifacts, _ = self.memory.build_agent_memory_views(DATABASE_DIR)
        compact = (DATABASE_DIR / COMPACT).read_bytes()
        machine = (DATABASE_DIR / MACHINE).read_bytes()
        schema = json.loads(HANDSHAKE_SCHEMA.read_text(encoding="utf-8"))
        manifest = json.loads((DATABASE_DIR / "data/memory/records/manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(first_plan, second_plan)
        self.assertEqual(first_artifacts, second_artifacts)
        self.assertEqual(first_artifacts, {COMPACT: compact, MACHINE: machine})
        self.assertLessEqual(len(compact), 24 * 1024)
        self.assertLessEqual(len(machine), 256 * 1024)
        self.assertEqual((compact + machine).decode("utf-8").count("LINZE_AGENT_MEMORY_V3"), 1)
        self.assertEqual(set(handshake), set(schema["required"]))
        for key in ("schema_version", "protocol", "protocol_version", "generated", "editable", "marker"):
            self.assertEqual(handshake[key], schema["properties"][key]["const"])
        self.assertEqual(handshake["capabilities"]["discovery_object_count"], 1)
        self.assertEqual(handshake["adapter_contract"]["profile_count"], 5)
        self.assertEqual(
            handshake["adapter_contract"]["published_live_acceptance_task"],
            "TSK.OpenAIDatabase.PAM1.0019",
        )
        for key, path in (
            ("profiles", TRANSPORT_PROFILES),
            ("instructions", TRANSPORT_INSTRUCTIONS),
            ("harness", TRANSPORT_HARNESS),
        ):
            self.assertEqual(
                handshake["adapter_contract"][key]["sha256"],
                "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        for key, path in (
            ("schema", MUTATION_SCHEMA),
            ("policy", MUTATION_POLICY),
            ("instructions", MUTATION_INSTRUCTIONS),
        ):
            self.assertEqual(
                handshake["mutation_contract"][key]["sha256"],
                "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        self.assertEqual(handshake["mutation_contract"]["operations"], ["add", "update", "retire", "dispute"])
        self.assertEqual(
            handshake["lifecycle_contract"]["policy"]["sha256"],
            "sha256:" + hashlib.sha256(LIFECYCLE_POLICY.read_bytes()).hexdigest(),
        )
        self.assertEqual(handshake["lifecycle_contract"]["acceptance_id"], "ACC.OpenAIDatabase.PAM1.0010")
        for key, path in (
            ("policy", FORGETTING_POLICY),
            ("instructions", FORGETTING_INSTRUCTIONS),
        ):
            self.assertEqual(
                handshake["forgetting_contract"][key]["sha256"],
                "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        self.assertEqual(handshake["forgetting_contract"]["acceptance_id"], "ACC.OpenAIDatabase.PAM1.0011")
        self.assertEqual(handshake["forgetting_contract"]["current_answer_statuses"], ["active"])
        self.assertFalse(handshake["forgetting_contract"]["public_git_history_is_erasure"])
        self.assertEqual(handshake["retrieval_contract"]["task_id"], "TSK.OpenAIDatabase.PAM1.0015")
        self.assertEqual(handshake["retrieval_contract"]["acceptance_id"], "ACC.OpenAIDatabase.PAM1.0015")
        self.assertEqual(handshake["retrieval_contract"]["index"]["record_count"], 6)
        self.assertLessEqual(
            handshake["retrieval_contract"]["request_budget"]["indexed_fact_content_get_count_max"],
            2,
        )
        for key, path in (
            ("config", RETRIEVAL_CONFIG),
            ("implementation", RETRIEVAL_IMPLEMENTATION),
        ):
            self.assertEqual(
                handshake["retrieval_contract"][key]["sha256"],
                "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        self.assertEqual(
            handshake["raw"]["security_policy_sha256"],
            "sha256:" + hashlib.sha256(SECURITY_POLICY.read_bytes()).hexdigest(),
        )
        self.assertEqual(handshake["entrypoints"]["compact"]["sha256"], "sha256:" + hashlib.sha256(compact).hexdigest())
        self.assertEqual(handshake["canonical"]["dataset_sha256"], manifest["dataset_sha256"])
        self.assertEqual(handshake["canonical"]["record_count"], manifest["record_count"])
        self.assertEqual(self.memory.agent_view_drift(DATABASE_DIR, first_artifacts)["drift_count"], 0)
        combined = (compact + machine).decode("utf-8")
        self.assertNotIn("OpenAI-export.zip", combined)
        self.assertNotIn("/Users/", combined)
        self.assertIn("Generated-only", combined)

    def test_plan_apply_idempotency_and_manual_edit_drift_use_one_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "database"
            database.mkdir()
            base = self.write_fixture(database)

            planned = self.run_cli(database, "build", "--agent-views")
            plan = self.json_lines(planned)[0]
            key = str(plan["required_idempotency_key"])
            missing = self.run_cli(database, "build", "--agent-views", "--check")
            self.assertEqual(missing.returncode, 1)
            self.assertEqual(self.json_lines(missing)[-1]["drift_count"], 2)

            applied = self.run_cli(
                database,
                "build",
                "--agent-views",
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                key,
            )
            replay = self.run_cli(
                database,
                "build",
                "--agent-views",
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                key,
            )
            self.assertEqual(applied.returncode, 0, applied.stdout)
            self.assertEqual(self.json_lines(applied)[-1]["write_count"], 2)
            self.assertEqual(replay.returncode, 0, replay.stdout)
            self.assertTrue(self.json_lines(replay)[-1]["idempotent"])

            compact = database / COMPACT
            compact.write_text(compact.read_text(encoding="utf-8") + "manual edit\n", encoding="utf-8")
            drift = self.run_cli(database, "build", "--agent-views", "--check")
            self.assertEqual(drift.returncode, 1)
            self.assertEqual(self.json_lines(drift)[-1]["drift_paths"], [COMPACT.as_posix()])
            repaired = self.run_cli(
                database,
                "build",
                "--agent-views",
                "--apply",
                "--base-sha",
                base,
                "--idempotency-key",
                key,
            )
            checked = self.run_cli(database, "build", "--agent-views", "--check")
            self.assertEqual(repaired.returncode, 0, repaired.stdout)
            self.assertEqual(checked.returncode, 0, checked.stdout)
            self.assertEqual(self.json_lines(checked)[-1]["drift_count"], 0)

    def test_startup_discovers_exactly_one_generated_object(self) -> None:
        result = self.router.route_resources(DATABASE_DIR, "startup")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["read_order"], [MACHINE.as_posix()])
        conditional = {row["path"] for row in result["conditional_resources"]}
        self.assertIn(COMPACT.as_posix(), conditional)
        self.assertEqual(len(result["context_used"]), 1)


if __name__ == "__main__":
    unittest.main()
