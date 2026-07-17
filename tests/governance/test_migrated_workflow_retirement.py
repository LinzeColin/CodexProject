"""迁出项目的专属工作流必须登记为跨仓退休，且不得残留在 workflows 清单里。

第6波把 KMFA / OpenAIDatabase 迁出本仓后，其专属工作流随项目一并迁走。
本测试钉住这个契约：策略里不能再声称拥有它们，退休记录必须写明跨仓替代物。
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = json.loads((ROOT / "governance" / "workflow_policy.json").read_text(encoding="utf-8"))
MIGRATED = {
    ".github/workflows/kmfa-dual-plane.yml": "LinzeColin/KMOS",
    ".github/workflows/openai-database-ci.yml": "LinzeColin/AgentDatabase",
}
EXTERNAL = re.compile(r"^[\w.-]+/[\w.-]+:.+$")


class MigratedWorkflowRetirementTests(unittest.TestCase):
    def test_migrated_workflows_are_not_owned_anymore(self) -> None:
        owned = {w["path"] for w in POLICY["workflows"]}
        for path in MIGRATED:
            self.assertNotIn(path, owned, f"{path} 已随项目迁走，不应还在 workflows 清单")

    def test_migrated_workflow_files_are_gone(self) -> None:
        for path in MIGRATED:
            self.assertFalse((ROOT / path).exists(), f"{path} 应已随项目删除")

    def test_retirement_records_point_to_the_new_repo(self) -> None:
        retired = {r["path"]: r for r in POLICY["retired_or_merged"]}
        for path, repo in MIGRATED.items():
            self.assertIn(path, retired, f"{path} 必须登记为退休")
            entry = retired[path]
            self.assertEqual(entry["disposition"], "MIGRATED_WITH_PROJECT")
            self.assertTrue(EXTERNAL.match(entry["replacement"]),
                            f"{path} 的替代物须用跨仓记法 owner/repo:path")
            self.assertTrue(entry["replacement"].startswith(repo),
                            f"{path} 应指向 {repo}")


if __name__ == "__main__":
    unittest.main()
