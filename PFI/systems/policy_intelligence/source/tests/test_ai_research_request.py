from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from source_registry.ai_research_request import write_ai_research_priority_file
from source_registry.industry import classify_document_industry, load_industry_config


class AiResearchRequestPriorityTest(unittest.TestCase):
    def test_request_themes_are_promoted_ahead_of_base_industries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "policy_request.json"
            output = root / "request_industries.json"
            request.write_text(
                json.dumps(
                    {
                        "as_of": "2026-06-04",
                        "themes": ["银行", "AI / 人工智能"],
                        "symbols": [
                            {"symbol": "SH.600000", "name": "浦发银行", "theme": "银行"},
                            {"symbol": "SZ.159819", "name": "人工智能ETF", "theme": "AI / 人工智能"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = write_ai_research_priority_file(request, "config/industry_priorities.json", output)
            config = load_industry_config(output)

        self.assertEqual(result["focused_count"], 2)
        self.assertEqual(config.rules[0].name, "金融 / 银行 / 证券 / 保险")
        self.assertEqual(config.rules[1].name, "AI / 人工智能")
        self.assertEqual(classify_document_industry({"title": "银行信贷资本市场政策"}, config)[0], 1)
        self.assertEqual(classify_document_industry({"title": "生成式人工智能产业政策"}, config)[0], 2)


if __name__ == "__main__":
    unittest.main()
