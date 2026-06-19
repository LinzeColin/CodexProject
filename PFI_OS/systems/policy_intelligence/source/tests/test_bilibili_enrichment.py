from __future__ import annotations

import unittest

import source_registry.interpretation as interpretation
from source_registry.interpretation import (
    _bilibili_author_profile,
    _bilibili_video_enrichment,
    _comment_excerpt,
    _danmaku_excerpt,
    _subtitle_excerpt,
    interpretation_health_stats,
)


class BilibiliEnrichmentTest(unittest.TestCase):
    def test_subtitle_excerpt_compacts_public_subtitle_body(self) -> None:
        payload = {
            "body": [
                {"from": 0, "to": 1, "content": "第一句 政策解读"},
                {"from": 1, "to": 2, "content": "第二句 产业影响"},
                {"from": 2, "to": 3, "content": ""},
            ]
        }
        excerpt = _subtitle_excerpt(payload)
        self.assertEqual(excerpt, "第一句 政策解读 第二句 产业影响")

    def test_comment_and_danmaku_excerpt_are_compacted(self) -> None:
        comments = _comment_excerpt(
            [
                {"content": {"message": "第一条 政策解读"}},
                {"content": {"message": "第二条 产业影响"}},
                {"content": {"message": ""}},
            ]
        )
        danmaku = _danmaku_excerpt("<i><d p=\"1\">十五五规划</d><d p=\"2\">农业现代化</d></i>")
        self.assertEqual(comments, "第一条 政策解读；第二条 产业影响")
        self.assertEqual(danmaku, "十五五规划；农业现代化")

    def test_video_enrichment_collects_public_comments_and_danmaku(self) -> None:
        old_fetch_json = interpretation._fetch_json
        old_fetch_text = interpretation._fetch_text

        def fake_fetch_json(url, *args, **kwargs):
            if "web-interface/view" in url:
                return {
                    "code": 0,
                    "data": {
                        "aid": 123,
                        "cid": 456,
                        "desc": "政策解读视频简介",
                        "owner": {"mid": 789, "name": "政策UP"},
                        "stat": {"view": 100, "reply": 2, "favorite": 3, "coin": 4, "share": 5, "like": 6},
                    },
                }
            if "web-interface/card" in url:
                return {
                    "code": 0,
                    "data": {
                        "card": {
                            "mid": 789,
                            "name": "政策UP",
                            "sign": "长期关注政策解读和产业影响",
                            "fans": 2000,
                            "friend": 9,
                            "level_info": {"current_level": 5},
                            "official_verify": {"type": 0, "desc": "政策研究账号"},
                        }
                    },
                }
            if "player/v2" in url:
                return {"code": 0, "data": {"subtitle": {"subtitles": []}}}
            if "x/v2/reply" in url:
                return {
                    "code": 0,
                    "data": {
                        "replies": [
                            {"content": {"message": "评论 政策解读"}},
                            {"content": {"message": "评论 产业影响"}},
                        ]
                    },
                }
            return None

        def fake_fetch_text(url, *args, **kwargs):
            if "comment.bilibili.com" in url:
                return "<i><d p=\"1\">弹幕 政策</d><d p=\"2\">弹幕 规划</d></i>"
            return None

        try:
            interpretation._fetch_json = fake_fetch_json
            interpretation._fetch_text = fake_fetch_text
            enrichment = _bilibili_video_enrichment(
                {"bvid": "BV1x", "aid": 123},
                allow_insecure_tls=False,
                cookie_file=None,
                timeout=1,
                retries=0,
            )
        finally:
            interpretation._fetch_json = old_fetch_json
            interpretation._fetch_text = old_fetch_text

        self.assertTrue(enrichment["detail_enriched"])
        self.assertTrue(enrichment["author_profile_enriched"])
        self.assertEqual(enrichment["author_mid"], 789)
        self.assertEqual(enrichment["author_follower_count"], 2000)
        self.assertEqual(enrichment["author_verified_desc"], "政策研究账号")
        self.assertIn("评论 政策解读", enrichment["comment_excerpt"])
        self.assertIn("弹幕 政策", enrichment["danmaku_excerpt"])
        health = interpretation_health_stats(
            [
                {
                    "platform": "bilibili",
                    "item_type": "video",
                    "title": "政策解读视频",
                    "url": "https://www.bilibili.com/video/BV1x/",
                    "evidence_status": "公开视频搜索结果；互动摘录已采集",
                    "content_excerpt": "评论摘录：评论 政策解读；弹幕摘录：弹幕 政策",
                    "raw_metadata": enrichment,
                }
            ]
        )
        self.assertEqual(health["video_author_profiles_enriched"], 1)
        self.assertEqual(health["video_comments_extracted"], 1)
        self.assertEqual(health["video_danmaku_extracted"], 1)

    def test_author_profile_unavailable_is_non_blocking(self) -> None:
        old_fetch_json = interpretation._fetch_json

        def fake_fetch_json(url, *args, **kwargs):
            return {"code": -404}

        try:
            interpretation._fetch_json = fake_fetch_json
            profile = _bilibili_author_profile(
                "789",
                allow_insecure_tls=False,
                cookie_file=None,
                timeout=1,
                retries=0,
            )
        finally:
            interpretation._fetch_json = old_fetch_json

        self.assertEqual(profile["author_mid"], "789")
        self.assertEqual(profile["author_profile_status"], "author_profile_unavailable:-404")


if __name__ == "__main__":
    unittest.main()
