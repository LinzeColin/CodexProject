from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKUP_ROOT = (
    ROOT
    / "KM_IDSystem"
    / "governance"
    / "archive"
    / "local_handoff_20260716"
    / "backup"
)
REMOVED_BACKUP_PAYLOADS = (
    "KM_IDS-HEAD-e1679d24-project-snapshot.tar.gz",
    "KM_IDS-local-commits-565babef-to-e1679d24.bundle",
    "KM_IDS-main-integration-candidate.bundle",
    "KM_IDS-working-tree-overlay.tar.gz",
    "opme-system-legacy-assets.tar.gz",
)


class CleanMemoryPublicSplitSafetyTests(unittest.TestCase):
    def test_agent_database_route_remains_public(self) -> None:
        contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("公开 `LinzeColin/AgentDatabase`", contract)
        self.assertIn("不得改仓库可见性", contract)
        self.assertNotIn("AgentDatabase（私有）", contract)

    def test_duplicate_backup_payloads_are_absent_from_current_tree(self) -> None:
        for filename in REMOVED_BACKUP_PAYLOADS:
            self.assertFalse((BACKUP_ROOT / filename).exists(), filename)

    def test_policy_is_fail_closed_after_reviewed_baseline_migration(self) -> None:
        policy = json.loads(
            (ROOT / "governance" / "repository_hygiene_policy.json").read_text(encoding="utf-8")
        )
        self.assertLessEqual(policy["regular_blob_max_bytes"], 1_048_576)
        self.assertFalse(policy["history_rewrite"]["allowed_in_this_task"])
        self.assertEqual(policy["history_rewrite"]["decision"], "DEFERRED")

        rules = {rule["id"]: rule for rule in policy["retained_objects"]}
        expected = {
            "PFI_VISUAL_ACCEPTANCE": ("large", 12_680_824),
            "PFI_ACCEPTANCE_ARCHIVES": ("archive", 12_680_824),
            "PFI_V025_SOURCE_TASKPACK": ("archive", 86_942),
            "ARXIV_PURSUING_GOAL_EVIDENCE": ("large", 1_556_045),
        }
        for rule_id, (kind, maximum) in expected.items():
            rule = rules[rule_id]
            self.assertIn(kind, rule["kinds"])
            self.assertEqual(rule["max_bytes"], maximum)
            self.assertEqual(rule["change_policy"], "baseline_oid_only")


if __name__ == "__main__":
    unittest.main()
