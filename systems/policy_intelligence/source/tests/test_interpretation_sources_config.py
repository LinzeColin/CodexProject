from __future__ import annotations

import json
import unittest
from pathlib import Path


class InterpretationSourcesConfigTest(unittest.TestCase):
    def test_toutiao_has_public_and_authorized_sources(self) -> None:
        sources = _sources()
        toutiao = [item for item in sources if item.get("platform") == "toutiao"]
        collectors = {item.get("collector_type") for item in toutiao}
        self.assertIn("public_search_html", collectors)
        self.assertIn("authorized_public_search", collectors)
        self.assertTrue(any(item.get("auth_required") is True for item in toutiao))
        self.assertTrue(any(item.get("auth_required") is False for item in toutiao))

    def test_xiaohongshu_uses_authorized_public_search_not_landing_only(self) -> None:
        sources = _sources()
        xhs = [item for item in sources if item.get("platform") == "xiaohongshu"]
        self.assertEqual(len(xhs), 1)
        self.assertEqual(xhs[0].get("collector_type"), "authorized_public_search")
        self.assertTrue(xhs[0].get("auth_required"))


def _sources() -> list[dict]:
    path = Path("config/interpretation_sources.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [item for item in payload["sources"] if item.get("enabled", True)]


if __name__ == "__main__":
    unittest.main()
