"""项目即登记 —— 契约守卫。

`STANDARD.md` 规定：长得像项目的目录必须有治理文件，否则要显式豁免并写明理由。

这一条补的是最前面那一环。缺了它，「部署即登记」和「业务流登记」都白搭 ——
一个项目在写出治理文件之前对监控中枢是**彻底隐形**的，
而隐形不会让任何指标变红。实测全仓有 10 个这样的目录，
其中 CyberBoss 有 634 个文件、是 owner 明确在跑的活跃项目。
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs" / "governance" / "STANDARD.md"
SECTION = "## 项目即登记（长得像项目就必须有治理文件）"

REQUIRED = (
    "隐形不会让任何指标变红",
    "就必须有\n   `docs/governance/project.yaml`（强制）",
    "不自动下结论，强制表态",
    "沉默不是选项",
    "豁免必须带理由",
    "治理文件先于第一行业务代码",
    "如实优先于好看",
    "宁可一片 `not_built`，不要一格假 `healthy`",
)


class ProjectRegistryContractTest(unittest.TestCase):
    def setUp(self):
        self.text = CONTRACT.read_text(encoding="utf-8")

    def test_section_exists(self):
        self.assertIn(SECTION, self.text, "STANDARD.md 缺「项目即登记」一节")

    def test_every_clause_present(self):
        body = self.text.split(SECTION, 1)[1].split("\n## ", 1)[0]
        missing = [k for k in REQUIRED if k not in body]
        self.assertFalse(missing, "本节缺少这些不可让步的条款：%s" % missing)

    def test_points_at_executable_assertions(self):
        body = self.text.split(SECTION, 1)[1].split("\n## ", 1)[0]
        self.assertIn("test_ungoverned_projects.py", body,
                      "文档条款没有指向真正跑得起来的断言，就只是一段散文")

    def test_sits_before_the_hub_section(self):
        """顺序有意义：先「进得来」，再「以谁为准」。"""
        self.assertLess(self.text.index(SECTION),
                        self.text.index("## status 是权威监控中枢"))


if __name__ == "__main__":
    unittest.main()
