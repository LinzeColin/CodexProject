from __future__ import annotations

import unittest
import sqlite3

import source_registry.interpretation as interpretation
from source_registry.content_db import begin_run, init_content_database, upsert_document
from source_registry.content_db import upsert_interpretation_item, upsert_interpretation_source
from source_registry.web_article import ArticleExtraction


class PublicSiteSearchTest(unittest.TestCase):
    def test_historical_public_references_reuse_only_successful_deduped_refs(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        init_content_database(conn)
        begin_run(conn, "2026060401", "test")
        begin_run(conn, "2026060402", "test")
        document_id, _ = upsert_document(
            conn,
            {
                "source_id": "src_gd",
                "source_name": "广东省人民政府门户网站",
                "source_url": "https://www.gd.gov.cn/",
                "authority_tier_snapshot": "A",
                "authority_score_snapshot": 95,
                "title": "留用地高效开发利用意见",
                "url": "https://www.gd.gov.cn/land-use.html",
                "text_excerpt": "农村集体土地留用地高效开发利用政策文件。",
            },
            "2026060401",
        )
        upsert_interpretation_source(
            conn,
            {
                "interpretation_source_id": "sogou",
                "name": "搜狗中文政策解读搜索",
                "platform": "sogou",
                "url_template": "https://www.sogou.com/web?query={query}",
            },
        )
        query = "留用地高效开发利用 政策解读"
        for suffix in ("a", "b"):
            upsert_interpretation_item(
                conn,
                {
                    "run_id": "2026060401",
                    "document_id": document_id,
                    "interpretation_source_id": "sogou",
                    "platform": "mp.weixin.qq.com",
                    "item_type": "article",
                    "title": "留用地高效开发利用政策解读",
                    "url": f"https://mp.weixin.qq.com/s/{suffix}",
                    "query": query,
                    "evidence_status": "sogou公开搜索结果；正文已摘录",
                    "summary": "留用地政策解读。",
                    "content_excerpt": "留用地高效开发利用政策解读，分析农村集体土地、规划管理、收益分配、产业园区和企业投资影响。",
                    "relevance_score": 92,
                    "raw_metadata": {"article_fetch_status": "article_excerpt_extracted"},
                },
            )
        upsert_interpretation_item(
            conn,
            {
                "run_id": "2026060401",
                "document_id": document_id,
                "interpretation_source_id": "sogou",
                "platform": "gd.gov.cn",
                "item_type": "article",
                "title": "一图读懂留用地政策",
                "url": "https://www.gd.gov.cn/one-picture.html",
                "query": query,
                "evidence_status": "已入库公开相关文件/解读",
                "summary": "本地相关文件不应被历史公开参考复用。",
                "content_excerpt": "留用地政策解读。",
                "relevance_score": 90,
                "raw_metadata": {"local_related_document": True},
            },
        )

        items = interpretation._collect_local_historical_reference_items(
            conn=conn,
            source={
                "interpretation_source_id": "interp_local_historical_public_refs",
                "name": "历史成功公开参考复用",
                "platform": "historical_references",
                "collector_type": "local_historical_references",
                "max_results": 2,
            },
            document={"document_id": document_id, "title": "留用地高效开发利用意见"},
            run_id="2026060402",
            query=query,
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["platform"], "mp.weixin.qq.com")
        self.assertIn("历史成功公开参考复用", items[0]["evidence_status"])
        self.assertTrue(items[0]["raw_metadata"]["historical_public_reference"])
        self.assertEqual(interpretation.count_reference_items(items), 1)
        conn.close()

    def test_local_related_documents_count_as_context_reference_not_primary_document(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        init_content_database(conn)
        begin_run(conn, "2026060401", "test")
        primary_id, _ = upsert_document(
            conn,
            {
                "source_id": "src_gov",
                "source_name": "中国政府网",
                "source_url": "https://www.gov.cn/",
                "authority_tier_snapshot": "A",
                "authority_score_snapshot": 96,
                "title": "“十五五”时期农业农村现代化这样推进_政策解读",
                "url": "https://www.gov.cn/zhengce/202606/content_1.htm",
                "text_excerpt": "主研究文件。",
            },
            "2026060401",
        )
        upsert_document(
            conn,
            {
                "source_id": "src_gov",
                "source_name": "中国政府网",
                "source_url": "https://www.gov.cn/",
                "authority_tier_snapshot": "A",
                "authority_score_snapshot": 96,
                "title": "两部门负责人就《加快农业农村现代化“十五五”规划》答记者问",
                "url": "https://www.gov.cn/zhengce/202606/content_2.htm",
                "text_excerpt": "农业农村现代化 十五五 规划 政策解读 答记者问，说明重点任务和实施路径。",
            },
            "2026060401",
        )
        upsert_document(
            conn,
            {
                "source_id": "src_gov",
                "source_name": "中国政府网",
                "source_url": "https://www.gov.cn/",
                "authority_tier_snapshot": "A",
                "authority_score_snapshot": 96,
                "title": "文件库",
                "url": "https://www.gov.cn/zhengce/index.htm",
                "text_excerpt": "农业农村现代化 十五五 规划 政策解读 文件库 栏目页。",
            },
            "2026060401",
        )
        items = interpretation._collect_local_related_document_items(
            conn=conn,
            source={
                "interpretation_source_id": "interp_local_related_public_docs",
                "name": "已入库相关公开文件与官方解读",
                "platform": "local_corpus",
                "collector_type": "local_related_documents",
                "max_results": 3,
            },
            document={"document_id": primary_id, "title": "“十五五”时期农业农村现代化这样推进_政策解读"},
            run_id="2026060401",
            query="“十五五”时期农业农村现代化这样推进 政策解读",
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["platform"], "gov.cn")
        self.assertEqual(items[0]["evidence_status"], "已入库公开相关文件/解读")
        self.assertNotEqual(items[0]["title"], "文件库")
        self.assertNotEqual(items[0]["raw_metadata"]["related_document_id"], primary_id)
        self.assertEqual(interpretation.count_reference_items(items), 1)
        conn.close()

    def test_local_related_documents_require_subject_match(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        init_content_database(conn)
        begin_run(conn, "2026060401", "test")
        primary_id, _ = upsert_document(
            conn,
            {
                "source_id": "src_gd",
                "source_name": "广东省人民政府门户网站",
                "source_url": "https://www.gd.gov.cn/",
                "authority_tier_snapshot": "B",
                "authority_score_snapshot": 82,
                "title": "广东省药品监督管理局药品零售许可验收实施细则（2026年修订）征求意见",
                "url": "https://www.gd.gov.cn/drug-retail.html",
                "text_excerpt": "主研究文件。",
            },
            "2026060401",
        )
        upsert_document(
            conn,
            {
                "source_id": "src_gd",
                "source_name": "广东省人民政府门户网站",
                "source_url": "https://www.gd.gov.cn/",
                "authority_tier_snapshot": "B",
                "authority_score_snapshot": 82,
                "title": "农村集体土地留用地管理政策解读",
                "url": "https://www.gd.gov.cn/land-policy.html",
                "text_excerpt": "政策解读围绕农村集体土地留用地开发利用、规划管理和收益分配展开。",
            },
            "2026060401",
        )
        items = interpretation._collect_local_related_document_items(
            conn=conn,
            source={
                "interpretation_source_id": "interp_local_related_public_docs",
                "name": "已入库相关公开文件与官方解读",
                "platform": "local_corpus",
                "collector_type": "local_related_documents",
                "max_results": 3,
            },
            document={"document_id": primary_id, "title": "广东省药品监督管理局药品零售许可验收实施细则"},
            run_id="2026060401",
            query="广东省药品监督管理局 药品零售许可验收实施细则 政策解读",
        )
        self.assertEqual(items, [])
        conn.close()

    def test_public_search_html_result_counts_by_resolved_article_domain(self) -> None:
        old_fetch_html = interpretation._fetch_html
        old_fetch_article = interpretation.fetch_public_article

        def fake_fetch_html(url, *args, **kwargs):
            return """
            <html><body>
              <a href="https://www.sogou.com/web?query=test">搜索页自身</a>
              <a href="https://finance.example.com/policy/ai.html">人工智能政策解读：产业影响分析</a>
            </body></html>
            """

        def fake_fetch_article(url, *args, **kwargs):
            return ArticleExtraction(
                status="article_excerpt_extracted",
                title="人工智能政策解读：产业影响分析",
                text="人工智能政策解读 正文摘录，分析产业影响、监管要求、算力、数据、模型、安全评估、企业机会和地方配套。",
                content_type="text/html",
                fetched_url="https://finance.example.com/policy/ai.html",
            )

        try:
            interpretation._fetch_html = fake_fetch_html
            interpretation.fetch_public_article = fake_fetch_article
            items = interpretation._collect_public_search_html_items(
                source={
                    "interpretation_source_id": "interp_sogou_web_policy",
                    "name": "搜狗中文政策解读搜索",
                    "platform": "sogou",
                    "url_template": "https://www.sogou.com/web?query={query}",
                    "collector_type": "public_search_html",
                    "max_results": 3,
                },
                document={"document_id": "doc_1", "title": "人工智能政策"},
                run_id="2026060401",
                query="人工智能 政策解读",
                allow_insecure_tls=False,
                timeout=1,
                retries=0,
            )
        finally:
            interpretation._fetch_html = old_fetch_html
            interpretation.fetch_public_article = old_fetch_article

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["platform"], "finance.example.com")
        self.assertEqual(items[0]["evidence_status"], "sogou公开搜索结果；正文已摘录")
        self.assertEqual(interpretation.count_reference_items(items), 1)
        health = interpretation.interpretation_health_stats(items)
        self.assertEqual(health["public_search_html_searches"], 1)
        self.assertEqual(health["public_search_html_results"], 1)
        self.assertEqual(health["article_excerpts_extracted"], 1)

    def test_public_search_html_excludes_search_engine_self_pages(self) -> None:
        links = interpretation._public_search_result_links(
            """
            <html><body>
              <a href="https://pic.sogou.com/pics?query=政策解读">搜狗图片搜索</a>
              <a href="https://weixin.sogou.com/weixin?type=2&query=政策解读">微信搜索页</a>
              <a href="https://www.sogou.com/web?query=政策解读">网页搜索页</a>
              <a href="https://finance.example.com/policy/ai.html">人工智能政策解读</a>
            </body></html>
            """,
            "https://www.sogou.com/web?query=test",
            "人工智能 政策解读",
        )
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["url"], "https://finance.example.com/policy/ai.html")

    def test_public_search_html_repairs_timestamp_href_entity(self) -> None:
        links = interpretation._public_search_result_links(
            """
            <html><body>
              <a href="http://mp.weixin.qq.com/s?src=11&timestamp=1780560005&ver=6761&signature=abc">药品零售许可政策解读</a>
            </body></html>
            """,
            "https://www.sogou.com/web?query=test",
            "药品零售许可 政策解读",
        )
        self.assertEqual(len(links), 1)
        self.assertIn("&timestamp=1780560005", links[0]["url"])
        self.assertNotIn("×tamp", links[0]["url"])

    def test_public_search_html_upgrades_wechat_public_article_to_https(self) -> None:
        links = interpretation._public_search_result_links(
            """
            <html><body>
              <a href="http://mp.weixin.qq.com/s?src=11&timestamp=1780560005&ver=6761&signature=abc">政策解读：留用地高效开发利用</a>
            </body></html>
            """,
            "https://www.sogou.com/web?query=test",
            "留用地高效开发利用 政策解读",
        )
        self.assertEqual(len(links), 1)
        self.assertTrue(links[0]["url"].startswith("https://mp.weixin.qq.com/s?"))

    def test_public_search_html_decodes_chinese_search_redirect_targets(self) -> None:
        links = interpretation._public_search_result_links(
            """
            <html><body>
              <a href="https://www.so.com/s?q=政策解读">360 搜索自身</a>
              <a href="https://www.so.com/link?u=https%3A%2F%2Fresearch.example.cn%2Frobot-policy.html">机器人政策解读：产业影响分析</a>
              <a href="https://www.sogou.com/link?url=https%3A%2F%2Fthinktank.example.cn%2Fchip-policy.html">半导体政策解读：产业链机会</a>
            </body></html>
            """,
            "https://www.so.com/s?q=test",
            "机器人 政策解读",
        )
        urls = [link["url"] for link in links]
        self.assertIn("https://research.example.cn/robot-policy.html", urls)
        self.assertIn("https://thinktank.example.cn/chip-policy.html", urls)
        self.assertNotIn("https://www.so.com/s?q=政策解读", urls)

    def test_public_search_html_prefers_data_url_from_search_result_anchor(self) -> None:
        links = interpretation._public_search_result_links(
            """
            <html><body>
              <a href="/s?wd=人工智能政策解读">百度搜索自身</a>
              <a href="/link?url=opaque" data-url="https://analysis.example.cn/ai-policy.html">人工智能政策解读：企业机会分析</a>
            </body></html>
            """,
            "https://www.baidu.com/s?wd=test",
            "人工智能 政策解读",
        )
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["url"], "https://analysis.example.cn/ai-policy.html")

    def test_public_site_search_filters_search_page_itself(self) -> None:
        links = interpretation._public_site_result_links(
            """
            <html><body>
              <a href="https://search.cctv.com/index.php">央视搜索</a>
              <a href="https://news.cctv.com/2026/06/04/ARTI123.shtml">政策解读：产业影响</a>
            </body></html>
            """,
            "https://search.cctv.com/search.php?qtext=test",
            "cctv.com",
            "政策解读",
        )
        self.assertEqual(len(links), 1)
        self.assertIn("news.cctv.com", links[0]["url"])

    def test_public_site_search_result_page_counts_as_reference(self) -> None:
        old_fetch_html = interpretation._fetch_html
        old_fetch_article = interpretation.fetch_public_article

        def fake_fetch_html(url, *args, **kwargs):
            return """
            <html><body>
              <a href="https://www.gov.cn/zhengce/202606/content_1.htm">政策解读：人工智能产业影响</a>
              <a href="https://example.com/noise.htm">站外噪声</a>
              <a href="/sousuo/search.shtml?q=test">搜索页自身</a>
            </body></html>
            """

        def fake_fetch_article(url, *args, **kwargs):
            return ArticleExtraction(
                status="article_excerpt_extracted",
                title="政策解读：人工智能产业影响",
                text="人工智能政策解读 正文摘录，分析产业影响、监管要求、算力、数据、模型、安全评估、企业机会和地方配套。",
                content_type="text/html",
                fetched_url=url,
            )

        try:
            interpretation._fetch_html = fake_fetch_html
            interpretation.fetch_public_article = fake_fetch_article
            items = interpretation._collect_public_site_search_items(
                source={
                    "interpretation_source_id": "interp_gov_policy_explain",
                    "name": "中国政府网政策解读搜索",
                    "platform": "gov.cn",
                    "url_template": "https://sousuo.www.gov.cn/sousuo/search.shtml?searchWord={query}",
                    "collector_type": "public_site_search",
                    "max_results": 3,
                },
                document={"document_id": "doc_1", "title": "人工智能政策"},
                run_id="2026060401",
                query="人工智能 政策解读",
                allow_insecure_tls=False,
                timeout=1,
                retries=0,
            )
        finally:
            interpretation._fetch_html = old_fetch_html
            interpretation.fetch_public_article = old_fetch_article

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["platform"], "gov.cn")
        self.assertEqual(items[0]["item_type"], "article")
        self.assertEqual(items[0]["evidence_status"], "gov.cn公开站内搜索结果；正文已摘录")
        self.assertIn("正文摘录", items[0]["content_excerpt"])
        self.assertEqual(interpretation.count_reference_items(items), 1)
        health = interpretation.interpretation_health_stats(items)
        self.assertEqual(health["public_site_searches"], 1)
        self.assertEqual(health["public_site_results"], 1)
        self.assertEqual(health["article_pages_fetched"], 1)
        self.assertEqual(health["article_excerpts_extracted"], 1)

    def test_public_site_search_blocked_page_is_not_reference(self) -> None:
        old_fetch_html = interpretation._fetch_html
        old_fetch_article = interpretation.fetch_public_article

        def fake_fetch_html(url, *args, **kwargs):
            return '<html><body><a href="https://www.yicai.com/news/123.html">政策分析</a></body></html>'

        def fake_fetch_article(url, *args, **kwargs):
            return ArticleExtraction(
                status="article_fetch_blocked:paywall",
                title="政策分析",
                text="",
                content_type="text/html",
                fetched_url=url,
            )

        try:
            interpretation._fetch_html = fake_fetch_html
            interpretation.fetch_public_article = fake_fetch_article
            items = interpretation._collect_public_site_search_items(
                source={
                    "interpretation_source_id": "interp_yicai_policy",
                    "name": "第一财经政策解读搜索",
                    "platform": "yicai.com",
                    "url_template": "https://www.yicai.com/search?keys={query}",
                    "collector_type": "public_site_search",
                    "max_results": 1,
                },
                document={"document_id": "doc_1", "title": "人工智能政策"},
                run_id="2026060401",
                query="人工智能 政策解读",
                allow_insecure_tls=False,
                timeout=1,
                retries=0,
            )
        finally:
            interpretation._fetch_html = old_fetch_html
            interpretation.fetch_public_article = old_fetch_article

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["evidence_status"], "yicai.com公开站内搜索结果；正文受限")
        self.assertEqual(interpretation.count_reference_items(items), 0)
        health = interpretation.interpretation_health_stats(items)
        self.assertEqual(health["article_pages_blocked"], 1)

    def test_public_site_search_too_short_page_is_not_reference(self) -> None:
        item = {
            "platform": "gov.cn",
            "item_type": "article",
            "title": "政策解读",
            "url": "https://www.gov.cn/zhengce/202606/content_1.htm",
            "query": "人工智能 政策解读",
            "evidence_status": "gov.cn公开站内搜索结果",
            "content_excerpt": "政策解读",
            "raw_metadata": {
                "public_site_search": True,
                "public_site_result": True,
                "article_fetch_status": "article_excerpt_too_short",
            },
        }
        self.assertEqual(interpretation.count_reference_items([item]), 0)
        health = interpretation.interpretation_health_stats([item])
        self.assertEqual(health["public_site_results"], 1)
        self.assertEqual(health["article_pages_fetched"], 1)


if __name__ == "__main__":
    unittest.main()
