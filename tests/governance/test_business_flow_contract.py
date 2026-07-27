"""业务流登记 / 软件内部功能实现监控 —— 契约守卫。

`docs/governance/STANDARD.md` 规定:有治理文件的项目必须发布 `flow.yaml`,
阶段由各项目自定义、只统一接口,状态四态齐全,自报与实测必须交叉校验,
且探针不得执行登记文件里的自由字符串。

这些是**踩过的坑换来的条款**,写在文档里会随时间被冲淡,这里钉成机器判定:
少了 `blocked_by_policy` 一态,合规策略会被整片标红;
少了「不得执行自由字符串」,任何能改仓库文件的人就拿到了主机 shell。
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs" / "governance" / "STANDARD.md"   # 根 AGENTS.md 有 4KB 预算,细则落这里
SECTION = "## 业务流登记 / 软件内部功能实现监控"

REQUIRED = (
    "有治理文件就必须登记业务流",
    "合入 main",
    "统一接口,不统一内容",
    "由每个项目按自己的业务\n   语义定义",
    "状态四态,一态都不能少",
    "blocked_by_policy",
    "双向:自报 + 实测,必须交叉校验",
    "缺陷逐条挂在 基线 × 阶段 上",
    "同一天取最差的一次",
    "传导必须标注",
    "绝不执行登记文件里的自由字符串",
    "绝不读业务数据内容",
)


class BusinessFlowContractTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CONTRACT.exists(), "STANDARD.md 不存在")
        self.text = CONTRACT.read_text(encoding="utf-8")

    def test_section_present(self):
        self.assertIn(SECTION, self.text,
                      "缺少「业务流登记」整节。删掉它,后来的 agent 会把「部署好了吗」"
                      "和「业务跑通了吗」做成同一张表,两个问题就都没人回答了。")

    def test_required_clauses(self):
        for m in REQUIRED:
            self.assertIn(m, self.text, "契约缺少要素:%s" % m.replace("\n", " "))

    def test_four_states_declared_in_one_enumeration(self):
        """必须在**同一处枚举**里四态齐全。

        ★ 只用 `assertIn(state, body)` 是装饰性断言 —— 实测负控:把枚举行里的
          `blocked_by_policy` 删掉,守卫依然全绿,因为该词在本节的解释段里还出现着。
          断言必须钉在枚举本身,否则删掉一态不会被发现。
        """
        body = self.text.split(SECTION, 1)[1].split("\n## ", 1)[0]
        line = next((l for l in body.splitlines()
                     if l.count("`") >= 8 and "ok" in l and "warn" in l), "")
        self.assertTrue(line, "找不到四态枚举行")
        for st in ("ok", "warn", "blocked_by_policy", "not_implemented"):
            self.assertIn("`%s`" % st, line,
                          "四态枚举里少了 %s。少一态,合规策略会被整片标成红色。" % st)

    def test_ops_slice_and_business_slice_stay_separate(self):
        """两种纵向切片必须明确区分,否则会被后人合并掉。"""
        body = self.text.split(SECTION, 1)[1].split("\n## ", 1)[0]
        self.assertIn("两者不可互相替代", body)

    def test_untrusted_input_stance_is_explicit(self):
        body = self.text.split(SECTION, 1)[1].split("\n## ", 1)[0]
        self.assertIn("不可信输入", body,
                      "必须写明登记文件是不可信输入 —— 少了这句,"
                      "后来的实现会图省事直接执行 YAML 里的字符串。")


if __name__ == "__main__":
    unittest.main(verbosity=2)
