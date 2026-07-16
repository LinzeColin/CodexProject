from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
HARNESS = DATABASE_DIR / "scripts/validate_agent_transport_compatibility.py"


def load_harness():
    scripts_dir = str(DATABASE_DIR / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("agent_transport_compatibility_test", HARNESS)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {HARNESS}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AgentTransportCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.harness = load_harness()
        cls.handshake = json.loads(
            (DATABASE_DIR / "data/memory/agent-memory.json").read_text(encoding="utf-8")
        )
        cls.machine = (DATABASE_DIR / "data/memory/agent-memory.json").read_bytes()

    def test_repository_candidate_snapshot_passes_all_five_profiles_with_one_identity(self) -> None:
        result = self.harness.run_compatibility(DATABASE_DIR)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["profile_count"], 5)
        self.assertEqual(result["profile_pass_count"], 5)
        self.assertTrue(result["all_profiles_same_identity"])
        self.assertEqual(result["discovery_object_count"], 1)
        self.assertEqual(result["indexed_content_get_count"], 2)
        self.assertEqual(result["raw_expansion_content_get_count_max"], 3)
        self.assertTrue(result["conditional_etag_cache"])
        self.assertFalse(result["full_repo_scan"])
        self.assertFalse(result["remote_memory_target_tested"])
        self.assertFalse(result["writes_files"])
        identities = {json.dumps(row["identity"], sort_keys=True) for row in result["profiles"]}
        self.assertEqual(len(identities), 1)
        for profile in result["profiles"]:
            self.assertEqual(set(profile["operations"]), set(self.harness.REQUIRED_OPERATIONS))
            self.assertEqual(set(profile["operations"].values()), {"PASS"})
            self.assertTrue(profile["fallback"])
            self.assertFalse(profile["full_repo_scan"])
            self.assertEqual(profile["writes"], 0)
            self.assertEqual(profile["indexed_content_get_count"], 2)

        shard = DATABASE_DIR / self.handshake["active_index"][0]["shard"]
        record = next(
            row
            for row in self.harness.parse_jsonl_bytes(shard.read_bytes())
            if row["id"] == result["record_id"]
        )
        self.assertNotIn(record["statement"], json.dumps(result, ensure_ascii=False))

    def test_stale_commit_etag_and_tampered_transport_payload_fail_closed(self) -> None:
        expected_commit = self.handshake["commit_sha"]
        self.harness.require_fresh_commit(expected_commit, expected_commit)
        with self.assertRaisesRegex(self.harness.CompatibilityError, "stale_or_invalid"):
            self.harness.require_fresh_commit("0" * 40, expected_commit)

        etag = self.harness.replay_etag(self.machine)
        self.assertEqual(self.harness.conditional_status(etag, etag), 304)
        self.assertEqual(self.harness.conditional_status(etag, '"stale"'), 200)

        path = "OpenAIDatabase/data/memory/agent-memory.json"
        rest = self.harness.make_envelope("rest_https", path, self.machine, "CANDIDATE_TREE")
        rest["https"]["text"] += "tamper"
        with self.assertRaisesRegex(self.harness.CompatibilityError, "rest_https_parity_mismatch"):
            self.harness.decode_envelope("rest_https", rest, path, "CANDIDATE_TREE")

        mcp = self.harness.make_envelope("github_mcp", path, self.machine, "CANDIDATE_TREE")
        mcp["read_only"] = False
        with self.assertRaisesRegex(self.harness.CompatibilityError, "mcp_not_pinned_read_only"):
            self.harness.decode_envelope("github_mcp", mcp, path, "CANDIDATE_TREE")

    def test_profile_contract_path_and_publication_boundaries_fail_closed(self) -> None:
        contract = json.loads(
            (DATABASE_DIR / "config/agent_transport_profiles.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(self.harness.validate_profile_contract(contract)), 5)

        writable = copy.deepcopy(contract)
        writable["profiles"][0]["write_policy"] = "direct"
        with self.assertRaisesRegex(self.harness.CompatibilityError, "profile_write_not_disabled"):
            self.harness.validate_profile_contract(writable)

        missing = copy.deepcopy(contract)
        missing["profiles"].pop()
        with self.assertRaisesRegex(self.harness.CompatibilityError, "profile_count_mismatch"):
            self.harness.validate_profile_contract(missing)

        with self.assertRaisesRegex(self.harness.CompatibilityError, "unsafe_repository_path"):
            self.harness.safe_file(DATABASE_DIR, Path("../AGENTS.md"))
        with self.assertRaisesRegex(self.harness.CompatibilityError, "artifact_ref_invalid"):
            self.harness.run_compatibility(DATABASE_DIR, artifact_ref="main")


if __name__ == "__main__":
    unittest.main()
