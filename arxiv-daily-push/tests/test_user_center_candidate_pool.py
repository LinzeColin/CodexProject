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
)


class UserCenterCandidatePoolTests(unittest.TestCase):
    def test_total_candidate_pool_page_matches_content_ledger_row_count(self):
        ledger_rows = list(csv.DictReader(LEDGER.read_text(encoding="utf-8").splitlines()))
        page = CANDIDATE_POOL_PAGE.read_text(encoding="utf-8")
        table_rows = re.findall(r"^\| \d+ \|", page, flags=re.MULTILINE)

        self.assertEqual(len(ledger_rows), 299)
        self.assertEqual(len(table_rows), len(ledger_rows))
        self.assertTrue(page.startswith("# 截至今日总候选池\n"))
        self.assertIn("截至今日总候选池 | 299 条", page)
        self.assertIn("[CONTENT_LEDGER.csv](../docs/owner/CONTENT_LEDGER.csv)", page)
        self.assertIn("[报告/邮件预览索引](./已生成报告与邮件预览.md#", page)
        self.assertNotIn("../docs/owner/reports.md#", page)
        self.assertRegex(page, r"更新时间：2026-06-26 \d{2}:\d{2}:\d{2} Australia/Sydney")

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
        )
        for path in SUMMARY_PAGES:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                for phrase in forbidden:
                    self.assertNotIn(phrase, text)
                self.assertIn("[截至今日候选池](./截至今日候选池.md)", text)


if __name__ == "__main__":
    unittest.main()
