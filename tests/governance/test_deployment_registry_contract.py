"""部署即登记 / 业务基线纵向切片 —— 契约守卫。

`docs/governance/STANDARD.md` 规定:凡是部署到 OVH 或 Cloudflare 的软件都必须在
`LinzeHomeHub/status/` 登记归属并接入实时监控与自愈;每条业务线必须能被九段纵向切片
逐段看穿,且每段带实测证据。

规则只写在文档里会随时间被冲淡,这里把**不可省的要素**钉住:
1. 契约整段在位(防止被删掉或被稀释成一句口号);
2. 九段切片一段不少 —— 少一段,端到端就断了,「白箱受控」就是空话;
3. 「不得制造假红」与「能力边界如实标注」这两条必须保留 ——
   前者防止告警贬值(人一旦习惯红色,真出事那次也不会有人看),
   后者防止用推测冒充枚举。

本文件只校验契约文本。登记表字段完整性与各条误报的回归断言在实现仓:
`LinzeHomeHub/status/collector/tests/test_software_registry.py`。
两边分工:契约在治理仓,可执行判定在实现仓——避免跨仓读取。
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# AGENTS.md 有 4KB 预算,细则按其指引落在 STANDARD.md
CONTRACT = ROOT / "docs" / "governance" / "STANDARD.md"
SECTION = "## 部署即登记 / 业务基线纵向切片"

REQUIRED_MARKERS = (
    "部署即登记(强制)",
    "登记不靠自觉,靠反向核对",
    "完全不看登记表",
    "业务基线纵向切片端到端",
    "不得制造假红",
    "能力边界要如实标注",
    "爆炸半径",
)

# 九段缺一不可:任何一段没有实测证据,这条业务线就不算白箱受控
STAGES = ("代码源", "CI", "部署", "运行", "入口", "数据", "备份", "监控", "自愈")


class DeploymentRegistryContractTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CONTRACT.exists(), "STANDARD.md 不存在")
        self.text = CONTRACT.read_text(encoding="utf-8")

    def test_section_present(self):
        self.assertIn(
            SECTION, self.text,
            "STANDARD.md 缺少「部署即登记 / 业务基线纵向切片」整节。"
            "这条规则被删掉,后来的 agent 就会把服务部署上去而不登记,"
            "机器上会重新长出没人管的软件。")

    def test_required_markers_present(self):
        for marker in REQUIRED_MARKERS:
            self.assertIn(
                marker, self.text,
                f"契约缺少要素:{marker}。少了它规则就会退化成一句无法执行的口号。")

    def test_all_nine_stages_declared(self):
        body = self.text.split(SECTION, 1)[1].split("\n## ", 1)[0]
        for stage in STAGES:
            self.assertIn(
                stage, body,
                f"纵向切片少了「{stage}」段。九段缺一,端到端就断了。")

    def test_false_alarm_clause_keeps_the_regression_requirement(self):
        """光说"不要误报"没用,必须同时要求留下"真故障仍判失败"的回归断言。"""
        body = self.text.split(SECTION, 1)[1].split("\n## ", 1)[0]
        self.assertIn(
            "真故障仍判失败", body,
            "「不得制造假红」必须配一条回归要求,否则为了消灭误报会把真告警一起消灭。")


if __name__ == "__main__":
    unittest.main(verbosity=2)
