from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.reports import load_tag_config


class TagConfigTests(unittest.TestCase):
    def test_json_import_keeps_custom_filter_presets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tag_library_custom.json"
            path.write_text(
                json.dumps(
                    {
                        "tags": [
                            {
                                "tag_id": "custom_tag",
                                "tag_name": "自定义标签",
                                "tag_group": "自定义",
                                "color": "#2563eb",
                                "description": "测试标签",
                                "is_active": "1",
                                "source": "custom",
                                "sort_order": 100,
                            }
                        ],
                        "filter_presets": [
                            {
                                "preset_id": "custom_combo",
                                "preset_name": "自定义组合",
                                "tags": "自定义标签|基础支出",
                                "match_mode": "all",
                                "description": "测试组合",
                                "is_active": "1",
                                "source": "custom",
                                "sort_order": 100,
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            tag_rows, preset_rows = load_tag_config(path)

        self.assertTrue(any(row["tag_name"] == "自定义标签" for row in tag_rows))
        custom_preset = next(row for row in preset_rows if row["preset_id"] == "custom_combo")
        self.assertEqual(custom_preset["preset_name"], "自定义组合")
        self.assertEqual(custom_preset["tags"], "自定义标签|基础支出")
        self.assertEqual(custom_preset["match_mode"], "all")


if __name__ == "__main__":
    unittest.main()
