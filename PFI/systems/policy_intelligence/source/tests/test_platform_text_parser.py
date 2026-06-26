from __future__ import annotations

import unittest

from source_registry.platform_text_parser import (
    comment_excerpt_from_replies,
    danmaku_excerpt_from_xml,
    subtitle_excerpt_from_payload,
    subtitle_excerpt_from_text,
)


class PlatformTextParserTest(unittest.TestCase):
    def test_bilibili_json_subtitle_excerpt(self) -> None:
        parsed = subtitle_excerpt_from_payload(
            {
                "body": [
                    {"from": 0, "to": 1, "content": "AI 政策解读"},
                    {"from": 1, "to": 2, "content": "<b>算力</b> 和芯片"},
                ]
            }
        )
        self.assertEqual(parsed.status, "parsed")
        self.assertEqual(parsed.item_count, 2)
        self.assertEqual(parsed.text, "AI 政策解读 算力 和芯片")

    def test_srt_and_webvtt_are_normalized(self) -> None:
        srt = """1
00:00:01,000 --> 00:00:03,000
人工智能政策出台

2
00:00:04,000 --> 00:00:06,000
半导体企业受益
"""
        vtt = """WEBVTT

00:00:01.000 --> 00:00:03.000
机器人产业链扩张

00:00:04.000 --> 00:00:06.000
应用场景落地
"""
        self.assertEqual(subtitle_excerpt_from_text(srt).text, "人工智能政策出台 半导体企业受益")
        self.assertEqual(subtitle_excerpt_from_text(vtt).text, "机器人产业链扩张 应用场景落地")

    def test_comment_and_danmaku_escape_markup(self) -> None:
        comments = comment_excerpt_from_replies(
            [
                {"content": {"message": "第一条 &amp; 政策"}},
                {"message": "<b>第二条</b> 产业"},
            ]
        )
        danmaku = danmaku_excerpt_from_xml("<i><d p=\"1\">十五五&amp;规划</d><d p=\"2\"><![CDATA[芯片<机会>]]></d></i>")
        self.assertEqual(comments.text, "第一条 & 政策；第二条 产业")
        self.assertIn("十五五&规划", danmaku.text)
        self.assertIn("芯片", danmaku.text)

    def test_invalid_json_subtitle_is_auditable(self) -> None:
        parsed = subtitle_excerpt_from_text("{bad-json", fmt="json")
        self.assertEqual(parsed.status, "parse_failed:json")
        self.assertEqual(parsed.text, "")


if __name__ == "__main__":
    unittest.main()
