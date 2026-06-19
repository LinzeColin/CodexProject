from __future__ import annotations

import unittest

from source_registry.platform_page_parser import extract_platform_page_metadata


class PlatformPageParserTest(unittest.TestCase):
    def test_extracts_json_ld_author_date_and_metrics(self) -> None:
        metadata = extract_platform_page_metadata(
            """
            <html>
              <head>
                <title>AI 政策视频解读</title>
                <meta property="og:type" content="video.other">
                <script type="application/ld+json">
                {
                  "@type": "VideoObject",
                  "name": "人工智能政策视频解读",
                  "author": {"name": "政策研究账号", "url": "https://example.com/u/1"},
                  "uploadDate": "2026-06-05T09:00:00+10:00",
                  "interactionStatistic": [
                    {"interactionType": "LikeAction", "userInteractionCount": 120},
                    {"interactionType": "CommentAction", "userInteractionCount": 8}
                  ],
                  "viewCount": 2300
                }
                </script>
              </head>
              <body>2300播放 120点赞 8评论</body>
            </html>
            """,
            url="https://www.douyin.com/video/1",
            platform="douyin",
        )
        self.assertEqual(metadata.status, "parsed")
        self.assertEqual(metadata.content_type, "video")
        self.assertEqual(metadata.title, "人工智能政策视频解读")
        self.assertEqual(metadata.author_name, "政策研究账号")
        self.assertEqual(metadata.author_url, "https://example.com/u/1")
        self.assertEqual(metadata.published_at, "2026-06-05T09:00:00+10:00")
        self.assertEqual(metadata.view_count, 2300)
        self.assertGreaterEqual(metadata.engagement_count or 0, 128)

    def test_extracts_meta_fallbacks_and_chinese_counts(self) -> None:
        metadata = extract_platform_page_metadata(
            """
            <html>
              <head>
                <meta name="author" content="产业观察员">
                <meta property="article:published_time" content="2026-06-05">
                <meta property="og:title" content="机器人政策解读">
              </head>
              <body>1.2万阅读 88赞 12评论</body>
            </html>
            """,
            url="https://example.com/a/1",
            platform="zhihu",
        )
        self.assertEqual(metadata.title, "机器人政策解读")
        self.assertEqual(metadata.author_name, "产业观察员")
        self.assertEqual(metadata.published_at, "2026-06-05")
        self.assertEqual(metadata.view_count, 12000)
        self.assertEqual(metadata.engagement_count, 100)


if __name__ == "__main__":
    unittest.main()
