from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from source_registry.industry import (
    DEFAULT_INDUSTRY_NAME,
    classify_document_industry,
    document_is_since,
    document_sort_time,
    load_industry_config,
)


class IndustryPriorityTest(unittest.TestCase):
    def test_loads_user_priority_order_and_classifies_specific_industries(self) -> None:
        config = load_industry_config(Path("config/industry_priorities.json"))

        self.assertEqual(
            classify_document_industry({"title": "十五五区域战略规划纲要"}, config),
            (1, "宏观经济 / 五年规划 / 区域战略"),
        )
        self.assertEqual(
            classify_document_industry({"title": "生成式人工智能产业政策"}, config),
            (2, "AI / 人工智能"),
        )
        self.assertEqual(
            classify_document_industry({"title": "集成电路和芯片产业支持措施"}, config),
            (3, "半导体 / 芯片"),
        )

    def test_ai_keyword_does_not_match_unrelated_letters(self) -> None:
        config = load_industry_config(Path("config/industry_priorities.json"))

        self.assertEqual(
            classify_document_industry({"title": "SAIC 汽车产业政策"}, config)[1],
            "新能源汽车 / 智能汽车",
        )
        self.assertNotEqual(
            classify_document_industry({"title": "SAIC 汽车产业政策"}, config)[1],
            "AI / 人工智能",
        )

    def test_document_since_cutoff(self) -> None:
        self.assertTrue(document_is_since({"published_date": "2025-01-01"}, "2025-01-01"))
        self.assertFalse(document_is_since({"published_date": "2024-12-31"}, "2025-01-01"))
        self.assertEqual(
            document_sort_time({"title": "中华人民共和国国民经济和社会发展第十一个五年规划纲要"}),
            "2006-01-01",
        )
        self.assertFalse(
            document_is_since(
                {"title": "中华人民共和国国民经济和社会发展第十四个五年规划和2035年远景目标纲要"},
                "2025-01-01",
            )
        )
        self.assertTrue(document_is_since({"title": "广州市十五五规划纲要发布"}, "2025-01-01"))
        self.assertEqual(
            classify_document_industry({"title": "无法分类的标题"}, load_industry_config(None))[1],
            DEFAULT_INDUSTRY_NAME,
        )


if __name__ == "__main__":
    unittest.main()
