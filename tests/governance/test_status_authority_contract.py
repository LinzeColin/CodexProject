"""status 是权威监控中枢 —— 契约守卫。

`docs/governance/STANDARD.md` 规定：status 是全域唯一的「现在到底怎么样」权威，
任何 agent 开工第一步、收尾最后一步都要读它；探不到的步骤由各项目回流；
回流带时间戳且过期降级；给人看的一级状态只有四个。

这些同样是**踩过的坑换来的条款**，写在文档里会随时间被冲淡，这里钉成机器判定：

- 少了「单一权威」，各仓会各建一块看板，漂移之后没人知道该信哪块。
- 少了「过期一律降级成不确定」，三个月前的绿会被当成今天跑通了。
- 少了「不得拿相邻信号冒充这一步的产出」，覆盖率会瞬间好看而且**永远是绿的** ——
  这是本域反复出现的假绿形态，代价是真出事那次没人看得见。
- 少了「颜色只能是辅助」，状态又会退回纯色块编码：实测七个状态色两两对比度
  全部 <3:1，色盲与灰度下等于没有编码。
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs" / "governance" / "STANDARD.md"
SECTION = "## status 是权威监控中枢（开工第一步、收尾最后一步）"

REQUIRED = (
    "开工第一步、收尾最后一步（强制）",
    "单一权威",
    "不得自建第二块",
    "双向",
    "flow_state.json",
    "status 只读不写",
    "过期一律降级成「不确定」",
    "没有时间戳的自报不算实测",
    "绝不能拿相邻信号冒充这一步的产出",
    "宁可覆盖率难看，不要假覆盖",
    "通 / 断了 / 没做 / 不确定",
    "颜色永远只能是辅助通道",
    "status 自己也在这套规则之内",
)


class StatusAuthorityContractTest(unittest.TestCase):
    def setUp(self):
        self.text = CONTRACT.read_text(encoding="utf-8")

    def test_section_exists(self):
        self.assertIn(SECTION, self.text,
                      "STANDARD.md 缺「status 是权威监控中枢」一节")

    def test_every_clause_present(self):
        body = self.text.split(SECTION, 1)[1].split("\n## ", 1)[0]
        missing = [k for k in REQUIRED if k not in body]
        self.assertFalse(missing, "本节缺少这些不可让步的条款：%s" % missing)

    def test_points_at_executable_assertions(self):
        """文档条款必须指向真正跑得起来的断言，否则就只是一段散文。"""
        body = self.text.split(SECTION, 1)[1].split("\n## ", 1)[0]
        self.assertIn("test_repo_state_probe.py", body)
        self.assertIn("FLOW_STATE_CONTRACT.md", body)

    def test_four_level_one_states_are_exactly_four(self):
        """一级状态必须正好四个 —— 多一个就是又在往人脸上糊机器状态。"""
        body = self.text.split(SECTION, 1)[1].split("\n## ", 1)[0]
        line = [x for x in body.splitlines() if "通 / 断了 / 没做 / 不确定" in x]
        self.assertTrue(line)
        self.assertEqual(len(line[0].split("：")[-1].split(" / ")), 4)


if __name__ == "__main__":
    unittest.main()
