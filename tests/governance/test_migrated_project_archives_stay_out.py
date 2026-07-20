"""承重：已迁出项目的历史归档不得回流本仓。

背景：本仓 `governance/archive/other8_wave1_pending/` 曾堆着 Alpha(74)、EVA_OS(40)、
KM_IDSystem(18) 共 133 个文件——全是已迁出/已归档项目的历史备份与交付产物，占 2MB，
是本仓「一地鸡毛」的一部分。2026-07-20 清理：

- **EVA_OS 40 个**：经内容哈希逐一比对，与 `LinzeColin/Archive` 的 `EVA_OS/` 下文件
  **完全相同**（40/40 命中），属纯重复，直接删除。
- **Alpha 74 个 / KM_IDSystem 18 个**：目标仓无同内容文件（Alpha 0/74、KM_IDSystem 2/18），
  **不能删**，已迁入 `LinzeColin/Archive` 的 `_codexproject_legacy/`（云端验收 93 文件到位）
  后才删除本仓副本——铁律：目标验证通过才删源。

本测试锁住这个结果：归档目录不得重建，且指向它的留存策略条目不得复活。
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REMOVED_ARCHIVE_DIR = ROOT / "governance" / "archive" / "other8_wave1_pending"
HYGIENE_POLICY = ROOT / "governance" / "repository_hygiene_policy.json"
RETIRED_RETENTION_RULE_IDS = {"EVA_LEGACY_HANDOFF_ARCHIVE", "KM_IDSYSTEM_LEGACY_ARCHIVE"}


class MigratedProjectArchivesStayOutTests(unittest.TestCase):
    def test_migrated_project_archive_directory_is_not_recreated(self) -> None:
        """★承重★：重建该目录（哪怕一个文件）本断言即失败。"""
        self.assertFalse(
            REMOVED_ARCHIVE_DIR.exists(),
            f"{REMOVED_ARCHIVE_DIR.relative_to(ROOT)} 已于 2026-07-20 清理，"
            f"内容保全在 LinzeColin/Archive 的 _codexproject_legacy/。"
            f"目录重新出现说明有人把已迁出项目的归档搬了回来——这是迁移回流，不是修复。",
        )

    def test_retention_rules_for_removed_archives_are_not_revived(self) -> None:
        """★承重★：留存策略不得再指向已删除的归档路径（否则策略指向空气）。"""
        policy = json.loads(HYGIENE_POLICY.read_text(encoding="utf-8"))
        rules = policy.get("retained_objects") or []
        revived = sorted(
            str(rule.get("id"))
            for rule in rules
            if str(rule.get("id")) in RETIRED_RETENTION_RULE_IDS
        )
        self.assertEqual(
            revived, [],
            f"这些留存规则随其归档文件一并退休，不应复活：{revived}",
        )

        dangling = sorted(
            str(rule.get("path"))
            for rule in rules
            if str(rule.get("path") or "").startswith("governance/archive/other8_wave1_pending/")
        )
        self.assertEqual(
            dangling, [],
            f"留存策略仍指向已删除的归档路径（悬空引用）：{dangling}",
        )

    # 刻意不在此断言「所有留存规则目标都必须存在」：
    # 该策略另有 6 条按 path 指向 OpenAIDatabase / PFI / arxiv-daily-push 的条目，
    # 其文件已随项目迁出。它们是锚定已复核对象指纹的历史基线，且其中
    # PFI_V025_SOURCE_TASKPACK 被 test_cleanmem_public_split_safety 按 id 锚定，
    # 单方面裁剪会连锁破坏；清理它们需要 Owner 授权的独立迁移动作。
    # 本测试只锁本次清理的结果，不越界要求无关的整改。


if __name__ == "__main__":
    unittest.main()
