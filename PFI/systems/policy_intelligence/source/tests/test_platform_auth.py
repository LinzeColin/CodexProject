from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from source_registry.interpretation import (
    _collect_authorized_public_search_items,
    _search_landing_item,
    count_reference_items,
    interpretation_health_stats,
)
from source_registry.platform_auth import platform_auth_state


class PlatformAuthTest(unittest.TestCase):
    def test_cookie_file_state_is_available_without_exposing_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cookie_file = root / "douyin_cookie.txt"
            cookie_file.write_text("sessionid=secret-cookie-value", encoding="utf-8")
            auth_file = root / "platform_auth.json"
            auth_file.write_text(
                json.dumps(
                    {
                        "platforms": {
                            "douyin": {
                                "cookie_file": str(cookie_file),
                                "allowed_capabilities": ["search", "video_detail"],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            state = platform_auth_state("douyin", auth_file)
            self.assertTrue(state.available)
            metadata = state.as_metadata()
            self.assertTrue(metadata["cookie_file_configured"])
            self.assertNotIn("secret-cookie-value", json.dumps(metadata, ensure_ascii=False))
            self.assertEqual(metadata["allowed_capabilities"], ["search", "video_detail"])

    def test_chrome_profile_reference_is_available_but_not_collector_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "ChromeProfile"
            profile.mkdir()
            auth_file = root / "platform_auth.json"
            auth_file.write_text(
                json.dumps(
                    {
                        "platforms": {
                            "douyin": {
                                "chrome_profile_dir": str(profile),
                                "allowed_capabilities": ["search", "video_detail"],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            state = platform_auth_state("douyin", auth_file)
            metadata = state.as_metadata()

        self.assertTrue(state.available)
        self.assertTrue(metadata["session_file_configured"])
        self.assertFalse(metadata["cookie_file_configured"])
        self.assertFalse(metadata["collector_ready"])
        self.assertEqual(state.auth_method, "chrome_profile_reference")
        self.assertNotIn(str(profile), json.dumps(metadata, ensure_ascii=False))

    def test_authorized_landing_is_a_parser_gap_not_a_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cookie_file = root / "weibo_cookie.txt"
            cookie_file.write_text("SUB=secret", encoding="utf-8")
            auth_file = root / "platform_auth.json"
            auth_file.write_text(
                json.dumps({"platforms": {"weibo": {"cookie_file": str(cookie_file)}}}),
                encoding="utf-8",
            )
            state = platform_auth_state("weibo", auth_file)
            item = _search_landing_item(
                {
                    "interpretation_source_id": "interp_weibo_policy",
                    "name": "微博政策讨论搜索",
                    "platform": "weibo",
                    "url_template": "https://s.weibo.com/weibo?q={query}",
                    "auth_required": True,
                },
                {
                    "document_id": "doc_1",
                    "title": "政策文件",
                    "source_name": "Example Gov",
                },
                "2026060401",
                "政策文件 政策解读",
                attempted_online=True,
                auth_state=state,
            )

            self.assertEqual(item["evidence_status"], "授权文件可用；待接入平台解析器")
            self.assertEqual(count_reference_items([item]), 0)
            health = interpretation_health_stats([item])
            self.assertEqual(health["interpretation_auth_configured"], 1)
            self.assertEqual(health["interpretation_auth_parser_pending"], 1)
            self.assertNotIn("secret", json.dumps(item["raw_metadata"], ensure_ascii=False))

    def test_authorized_public_search_extracts_reference_without_exposing_cookie(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cookie_file = root / "zhihu_cookie.txt"
            cookie_file.write_text("z_c0=secret-cookie-value", encoding="utf-8")
            auth_file = root / "platform_auth.json"
            auth_file.write_text(
                json.dumps({"platforms": {"zhihu": {"cookie_file": str(cookie_file)}}}),
                encoding="utf-8",
            )
            state = platform_auth_state("zhihu", auth_file)
            old_fetch = __import__("source_registry.interpretation", fromlist=["_fetch_authorized_html"])._fetch_authorized_html
            calls: list[str] = []

            def fake_fetch(url, cookie_file_arg, *, allow_insecure_tls, timeout, retries):
                self.assertEqual(str(cookie_file_arg), str(cookie_file))
                calls.append(url)
                if "zhihu.com/search" in url:
                    return (
                        '<a href="https://research.example.com/ai-policy.html">人工智能政策解读：产业影响分析</a>',
                        "ok",
                        "text/html; charset=utf-8",
                        url,
                    )
                return (
                    """
                    <html><head><title>人工智能政策解读：产业影响分析</title></head>
                    <body>
                    <meta name="author" content="政策研究账号">
                    <meta property="article:published_time" content="2026-06-05">
                    <script type="application/ld+json">
                    {"@type":"Article","headline":"人工智能政策解读：产业影响分析","author":{"name":"政策研究账号","url":"https://research.example.com/u/policy"},"datePublished":"2026-06-05","viewCount":3200,"likeCount":45,"commentCount":6}
                    </script>
                    <article><p>人工智能政策解读 正文摘录，分析产业影响、监管要求、算力、数据、模型、安全评估、企业机会、地方配套、产业链约束、投资风险、实施节奏、监管口径、地方财政承载能力和企业合规成本。</p></article></body></html>
                    """,
                    "ok",
                    "text/html; charset=utf-8",
                    url,
                )

            import source_registry.interpretation as interpretation

            try:
                interpretation._fetch_authorized_html = fake_fetch
                items = _collect_authorized_public_search_items(
                    source={
                        "interpretation_source_id": "interp_zhihu_policy",
                        "name": "知乎政策解读搜索",
                        "platform": "zhihu",
                        "url_template": "https://www.zhihu.com/search?type=content&q={query}",
                        "collector_type": "authorized_public_search",
                        "max_results": 1,
                    },
                    document={"document_id": "doc_1", "title": "人工智能政策"},
                    run_id="2026060505",
                    query="人工智能 政策解读",
                    auth_state=state,
                    allow_insecure_tls=False,
                    timeout=1,
                    retries=0,
                )
            finally:
                interpretation._fetch_authorized_html = old_fetch

        encoded = json.dumps(items, ensure_ascii=False)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["evidence_status"], "zhihu授权公开搜索结果；正文已摘录")
        self.assertEqual(items[0]["author_name"], "政策研究账号")
        self.assertEqual(items[0]["author_url"], "https://research.example.com/u/policy")
        self.assertEqual(items[0]["published_at"], "2026-06-05")
        self.assertEqual(items[0]["view_count"], 3200)
        self.assertEqual(items[0]["engagement_count"], 51)
        self.assertEqual(items[0]["raw_metadata"]["page_metadata_status"], "parsed")
        self.assertEqual(count_reference_items(items), 1)
        self.assertEqual(len(calls), 2)
        self.assertNotIn("secret-cookie-value", encoded)
        self.assertNotIn(str(cookie_file), encoded)
        health = interpretation_health_stats(items)
        self.assertEqual(health["authorized_public_searches"], 1)
        self.assertEqual(health["authorized_public_results"], 1)

    def test_authorized_public_search_blocked_page_is_not_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cookie_file = root / "weibo_cookie.txt"
            cookie_file.write_text("SUB=secret-cookie-value", encoding="utf-8")
            auth_file = root / "platform_auth.json"
            auth_file.write_text(
                json.dumps(
                    {
                        "platforms": {
                            "weibo": {
                                "cookie_file": str(cookie_file),
                                "login_required_markers": ["登录"],
                                "captcha_markers": ["安全验证"],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            state = platform_auth_state("weibo", auth_file)
            import source_registry.interpretation as interpretation

            old_fetch = interpretation._fetch_authorized_html

            def fake_fetch(url, cookie_file_arg, *, allow_insecure_tls, timeout, retries):
                return "安全验证", "ok", "text/html; charset=utf-8", url

            try:
                interpretation._fetch_authorized_html = fake_fetch
                items = _collect_authorized_public_search_items(
                    source={
                        "interpretation_source_id": "interp_weibo_policy",
                        "name": "微博政策讨论搜索",
                        "platform": "weibo",
                        "url_template": "https://s.weibo.com/weibo?q={query}",
                        "collector_type": "authorized_public_search",
                        "max_results": 1,
                    },
                    document={"document_id": "doc_1", "title": "人工智能政策"},
                    run_id="2026060505",
                    query="人工智能 政策解读",
                    auth_state=state,
                    allow_insecure_tls=False,
                    timeout=1,
                    retries=0,
                )
            finally:
                interpretation._fetch_authorized_html = old_fetch

        encoded = json.dumps(items, ensure_ascii=False)
        self.assertEqual(len(items), 1)
        self.assertIn("授权搜索受限：captcha", items[0]["evidence_status"])
        self.assertEqual(count_reference_items(items), 0)
        self.assertNotIn("secret-cookie-value", encoded)
        self.assertNotIn(str(cookie_file), encoded)
        health = interpretation_health_stats(items)
        self.assertEqual(health["authorized_public_blocked"], 1)


if __name__ == "__main__":
    unittest.main()
