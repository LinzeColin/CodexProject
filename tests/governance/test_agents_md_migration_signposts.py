"""AGENTS.md 迁移路牌承重测试。

背景：`AGENTS.md` 的「已迁出」清单曾与 `governance/projects.yaml` 的 `migrated_projects`
脱节——KMFA/KM_IDSystem/PFI/OpenAIDatabase 四次迁移完成后清单未更新。清单过时会让 agent
以为目录是"丢失"而去恢复（死循环）。本测试把清单与注册表锁死，任何新迁移不更新 AGENTS.md 即失败。

同时锁：根 AGENTS.md 的 4KB 低 token 预算、数据落地处路牌。
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"

AGENTS_MD_BYTE_BUDGET = 4096  # AGENTS.md Low-Token Contract：根 AGENTS.md <=4KB


def load_module(name: str, path: Path):
    scripts_dir = str(SCRIPTS)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AgentsMdMigrationSignpostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_module(
            "validate_project_governance_signpost_test",
            SCRIPTS / "validate_project_governance.py",
        )
        cls.config = cls.validator.load_yaml(ROOT / "governance" / "projects.yaml")
        cls.agents_md = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    def test_every_migrated_project_is_listed_in_agents_md(self) -> None:
        """承重：projects.yaml 里每个 migrated 项目都必须出现在 AGENTS.md 的已迁出清单。

        去掉任一 project_id -> 本测试失败（防清单再次过时导致 agent 误恢复）。
        """
        migrated = [item["project_id"] for item in self.config["migrated_projects"]]
        self.assertGreaterEqual(len(migrated), 11, "migrated_projects 数量异常")
        missing = [pid for pid in migrated if pid not in self.agents_md]
        self.assertEqual(
            missing,
            [],
            f"AGENTS.md 已迁出清单缺少这些已迁移项目：{missing}；"
            f"迁移完成后必须同步更新 AGENTS.md，否则 agent 会把迁出误判为数据丢失并尝试恢复。",
        )

    def test_agents_md_stays_within_low_token_budget(self) -> None:
        """承重：根 AGENTS.md <=4KB（Low-Token Contract）。"""
        size = len((ROOT / "AGENTS.md").read_bytes())
        self.assertLessEqual(
            size,
            AGENTS_MD_BYTE_BUDGET,
            f"AGENTS.md {size} bytes 超出 {AGENTS_MD_BYTE_BUDGET} 预算；请压缩而非扩张。",
        )

    def test_data_home_signpost_present(self) -> None:
        """承重：数据落地处路牌必须在 AGENTS.md，且带禁 clone 约束。

        全仓数据统一存 LinzeColin/Private-Database（三区）；该仓预计 500GB+，
        整仓 clone 会损伤本地机器，故路牌必须同时载明禁 clone。
        """
        self.assertIn("Private-Database", self.agents_md, "AGENTS.md 缺数据落地处路牌")
        self.assertIn("禁 clone", self.agents_md, "数据路牌必须载明禁 clone 约束")

    def test_migrated_projects_are_absent_from_worktree(self) -> None:
        """承重：已登记 migrated 的项目目录确实不在本仓（迁移真的完成了）。"""
        still_present = [
            item["project_id"]
            for item in self.config["migrated_projects"]
            if (ROOT / str(item["path"])).exists()
        ]
        self.assertEqual(
            still_present,
            [],
            f"这些项目登记为 migrated 但目录仍在本仓：{still_present}",
        )


if __name__ == "__main__":
    unittest.main()
