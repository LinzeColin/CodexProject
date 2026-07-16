from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = DATABASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import evaluate_memory_snapshot_recovery as evaluator  # noqa: E402
import memory_snapshot  # noqa: E402


CONFIG = DATABASE_DIR / "config/evaluation/memory_snapshot_recovery_v1.json"
POLICY = DATABASE_DIR / "config/memory-snapshot-policy.json"
REPORT = DATABASE_DIR / "data/derived/evaluation/memory_gold/reports/snapshot_recovery_v1.json"


class MemorySnapshotRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        cls.tracked = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.observed, cls.elapsed = evaluator.evaluate(DATABASE_DIR, cls.config)

    def test_tracked_clean_room_drill_is_deterministic_and_passes_hard_gates(self) -> None:
        self.assertEqual(self.observed, self.tracked)
        self.assertEqual(self.observed["status"], "PASS")
        self.assertLess(self.elapsed, self.config["local_drill_bound_seconds"])
        self.assertEqual(self.observed["roundtrip"]["hash_identical_percent"], 100)
        self.assertEqual(self.observed["roundtrip"]["partial_restore_count"], 0)
        self.assertEqual(self.observed["offline_query_smoke"]["total_pass_count"], 10)
        self.assertEqual(self.observed["offline_query_smoke"]["network_request_count"], 0)

    def test_tamper_missing_member_wrong_commit_and_unsafe_paths_fail_closed(self) -> None:
        self.assertEqual(
            set(self.observed["negative_cases"]), set(self.config["required_negative_cases"])
        )
        self.assertTrue(
            all(row["fail_closed"] for row in self.observed["negative_cases"].values())
        )
        for unsafe in (
            "../memory.json",
            "/tmp/memory.json",
            "a\\b",
            "a/./b",
            "a//b",
            "C:memory",
        ):
            with self.subTest(path=unsafe), self.assertRaises(memory_snapshot.SnapshotError):
                memory_snapshot.safe_relative_path(unsafe)

    def test_public_release_boundary_excludes_repository_bundle_and_authenticity_claim(self) -> None:
        memory_snapshot.validate_policy(self.policy)
        release = self.observed["release"]
        self.assertEqual(release["repository"], "LinzeColin/AgentDatabase")
        self.assertEqual(release["visibility"], "public")
        self.assertEqual(release["publish_task_id"], "TSK.OpenAIDatabase.PAM1.0019")
        self.assertFalse(release["asset_published"])
        self.assertFalse(release["repository_archive_or_bundle_created"])
        self.assertFalse(release["archive_branch_created"])
        self.assertEqual(release["public_release_safe_record_count"], 198)
        self.assertFalse(self.observed["snapshot"]["release_candidate"])
        self.assertFalse(self.observed["snapshot"]["all_members_from_source_commit"])
        self.assertFalse(self.observed["snapshot"]["authenticity_claim"])
        self.assertEqual(self.observed["snapshot"]["raw_file_count"], 0)

    def test_public_release_rejects_any_non_redacted_or_credential_record(self) -> None:
        safe = {
            "sensitivity": {
                "public_repository_allowed": True,
                "credential_present": False,
                "handling": "redacted_summary",
            }
        }
        self.assertEqual(
            memory_snapshot.public_release_summary([safe])["public_release_safe_record_count"],
            1,
        )
        for key, value in (
            ("public_repository_allowed", False),
            ("credential_present", True),
            ("handling", "private"),
        ):
            unsafe = json.loads(json.dumps(safe))
            unsafe["sensitivity"][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(
                memory_snapshot.SnapshotError,
                "canonical_record_not_public_release_safe",
            ):
                memory_snapshot.public_release_summary([unsafe])


if __name__ == "__main__":
    unittest.main()
