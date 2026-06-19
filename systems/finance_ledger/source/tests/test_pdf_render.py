from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.reports import write_report_pdf


class PdfRenderTests(unittest.TestCase):
    def test_visual_bar_table_renders_to_pdf(self):
        markdown = "\n".join(
            [
                "# 测试报告",
                "",
                "## 可视化图表",
                "",
                "### 现金流视图",
                "",
                "| 项目 | 金额 | 图表 |",
                "|---|---:|---|",
                "| 总支出 | ¥100.00 | ██████████░░░░░░░░ |",
                "| 总收入 | ¥40.00 | ████░░░░░░░░░░░░░░ |",
                "| 待复核支出 | ¥20.00 | ██░░░░░░░░░░░░░░░░ |",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.pdf"
            write_report_pdf(markdown, path)
            data = path.read_bytes()
            self.assertGreater(len(data), 20_000)
            self.assertEqual(data[:5], b"%PDF-")


if __name__ == "__main__":
    unittest.main()
