import csv
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "owner" / "CONTENT_LEDGER.csv"
USER_CENTER = ROOT / "用户中心"
CANDIDATE_POOL_PAGE = USER_CENTER / "截至今日候选池.md"
REPORT_PREVIEW_INDEX_PAGE = USER_CENTER / "已生成报告与邮件预览.md"
SUMMARY_PAGES = (
    USER_CENTER / "README.md",
    USER_CENTER / "邮件发送与队列状态.md",
    USER_CENTER / "一看三查.md",
    USER_CENTER / "关键结论与用户决策.md",
)


def _section(text: str, start_heading: str, end_heading: str) -> str:
    start = text.index(start_heading)
    end = text.index(end_heading, start)
    return text[start:end]


class UserCenterCandidatePoolTests(unittest.TestCase):
    def test_total_candidate_pool_page_matches_content_ledger_row_count(self):
        ledger_rows = list(csv.DictReader(LEDGER.read_text(encoding="utf-8").splitlines()))
        page = CANDIDATE_POOL_PAGE.read_text(encoding="utf-8")
        total_pool_section = _section(page, "## 总候选池记录", "## 禁止误读")
        table_rows = re.findall(r"^\| \d+ \|", total_pool_section, flags=re.MULTILINE)

        self.assertEqual(len(ledger_rows), 299)
        self.assertEqual(len(table_rows), len(ledger_rows))
        self.assertTrue(page.startswith("# 截至今日总候选池\n"))
        self.assertIn("截至今日总候选池 | 299 条", page)
        self.assertIn("[CONTENT_LEDGER.csv](../docs/owner/CONTENT_LEDGER.csv)", page)
        self.assertIn("[报告/邮件预览索引](./已生成报告与邮件预览.md#", page)
        self.assertNotIn("../docs/owner/reports.md#", page)
        self.assertRegex(page, r"更新时间：2026-06-26 \d{2}:\d{2}:\d{2} Australia/Sydney")

    def test_candidate_pool_page_exposes_top_20_scored_selection_and_inventory_rules(self):
        page = CANDIDATE_POOL_PAGE.read_text(encoding="utf-8")
        top20_section = _section(page, "## 候选队列前20精选", "## 每日库存流转规则")
        top20_rows = re.findall(r"^\| \d+ \|", top20_section, flags=re.MULTILINE)

        self.assertEqual(len(top20_rows), 20)
        self.assertIn("| 1 | cs.AI | [arXiv:2606.22716]", top20_section)
        self.assertIn("| 65.51 |", top20_section)
        self.assertIn("同一篇文章按 `item_id` 去重", top20_section)
        self.assertIn("截至今日总候选池 = 已处理候选 + 待处理候选", page)
        self.assertIn("每日期末总候选池 = 昨日期末总候选池 + 今日新增候选 - 今日剔除候选", page)
        self.assertIn("今日待处理候选 = 昨日待处理候选 + 今日新增候选 - 今日完成处理 - 今日剔除候选", page)
        self.assertIn("当前仓库尚未接入日级库存流转账本", page)
        self.assertIn("板块期末候选数", page)
        self.assertIn("ending_pool = yesterday_pool + today_added - today_completed - today_removed", page)

    def test_report_preview_index_exists_for_generated_records(self):
        ledger_rows = list(csv.DictReader(LEDGER.read_text(encoding="utf-8").splitlines()))
        generated_rows = [
            row
            for row in ledger_rows
            if row["report_file_state"] == "generated" or row["email_state"] == "preview_generated"
        ]
        page = REPORT_PREVIEW_INDEX_PAGE.read_text(encoding="utf-8")
        table_rows = re.findall(r"^\| \d+ \|", page, flags=re.MULTILINE)

        self.assertEqual(len(generated_rows), 30)
        self.assertEqual(len(table_rows), len(generated_rows))
        self.assertIn("本页是 GitHub 浅层用户中心里的报告/邮件预览索引", page)
        self.assertIn("不是完整报告正文", page)
        self.assertIn("| 序号 | 锚点 | Code/category | 标题 / 条目 | 状态 | 候选日期 | 证据 |", page)
        self.assertNotIn("| 原始定位 |", page)
        self.assertEqual(page.count("[CONTENT_LEDGER.csv](../docs/owner/CONTENT_LEDGER.csv)"), len(generated_rows) + 1)

    def test_summary_pages_do_not_treat_11_item_queue_as_total_pool(self):
        forbidden = (
            "当前展示候选",
            "当前展示 11 条",
            "11 条高价值候选",
            "页面展示 11 条",
            "下表只列当前展示的 11 条",
            "全量内容记录",
            "内容记录全量",
            "当前运行队列",
        )
        for path in SUMMARY_PAGES:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                for phrase in forbidden:
                    self.assertNotIn(phrase, text)
                self.assertIn("[截至今日候选池](./截至今日候选池.md)", text)
                self.assertIn("候选队列前20精选", text)


if __name__ == "__main__":
    unittest.main()
