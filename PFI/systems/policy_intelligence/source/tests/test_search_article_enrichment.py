from __future__ import annotations

import unittest

import source_registry.interpretation as interpretation
import source_registry.web_article as web_article
from source_registry.web_article import ArticleExtraction
from source_registry.web_search import SearchResult


class SearchArticleEnrichmentTest(unittest.TestCase):
    def test_policy_document_query_strips_site_and_duplicate_interpretation_suffix(self) -> None:
        query = interpretation._query_for_document(
            {
                "title": "“十五五”时期农业农村现代化这样推进_政策解读",
                "source_name": "中国政府网",
            }
        )
        self.assertEqual(query, "“十五五”时期农业农村现代化这样推进 政策解读")

        query = interpretation._query_for_document(
            {
                "title": "国务院关于推进人工智能产业发展的通知__中国政府网",
                "source_name": "中国政府网",
            }
        )
        self.assertEqual(query, "推进人工智能产业发展 政策解读")

        query = interpretation._query_for_document(
            {
                "title": "广东省药品监督管理局关于公开征求《广东省药品监督管理局药品零售许可验收实施细则（2026年修订）》（征求意见稿）意见 广东省人民政府门户网站",
                "source_name": "广东省人民政府门户网站",
            }
        )
        self.assertEqual(query, "广东省药品监督管理局药品零售许可验收实施细则（2026年修订） 政策解读")

    def test_search_result_page_excerpt_counts_as_reference(self) -> None:
        old_collect = interpretation.collect_search_results
        old_fetch = interpretation.fetch_public_article
        try:
            interpretation.collect_search_results = lambda **kwargs: (
                [
                    SearchResult(
                        title="人工智能政策解读：产业影响分析",
                        url="https://example.com/ai-policy",
                        snippet="搜索摘要",
                        source="example.com",
                    )
                ],
                "ok",
            )
            interpretation.fetch_public_article = lambda *args, **kwargs: ArticleExtraction(
                status="article_excerpt_extracted",
                title="人工智能政策深度分析",
                text="人工智能政策解读 正文摘录，分析产业影响、监管要求、算力、数据、模型、安全评估和企业机会。",
                content_type="text/html",
                fetched_url="https://example.com/ai-policy",
            )
            items = interpretation._collect_search_api_items(
                source={
                    "interpretation_source_id": "interp_bing_policy",
                    "name": "Bing 全网政策解读搜索",
                    "platform": "bing",
                    "collector_type": "search_api_bing",
                    "url_template": "https://www.bing.com/search?q={query}",
                    "max_results": 1,
                },
                document={"document_id": "doc_1", "title": "人工智能政策"},
                run_id="2026060401",
                query="人工智能 政策解读",
                allow_insecure_tls=False,
                secrets_file=None,
                fetch_result_pages=True,
                timeout=1,
                retries=0,
            )
        finally:
            interpretation.collect_search_results = old_collect
            interpretation.fetch_public_article = old_fetch

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["evidence_status"], "bing公开搜索结果；正文已摘录")
        self.assertIn("正文摘录", items[0]["content_excerpt"])
        self.assertEqual(interpretation.count_reference_items(items), 1)
        health = interpretation.interpretation_health_stats(items)
        self.assertEqual(health["article_pages_fetched"], 1)
        self.assertEqual(health["article_excerpts_extracted"], 1)

    def test_blocked_article_page_does_not_count_as_reference(self) -> None:
        item = {
            "platform": "bing",
            "item_type": "search_result",
            "title": "人工智能政策解读",
            "url": "https://example.com/paywall",
            "query": "人工智能 政策解读",
            "evidence_status": "bing公开搜索结果；正文受限",
            "content_excerpt": "政策解读 搜索摘要",
            "raw_metadata": {"article_fetch_status": "article_fetch_blocked:paywall"},
        }
        self.assertEqual(interpretation.count_reference_items([item]), 0)
        health = interpretation.interpretation_health_stats([item])
        self.assertEqual(health["article_pages_fetched"], 1)
        self.assertEqual(health["article_pages_blocked"], 1)

    def test_raw_metadata_json_failed_article_does_not_count_as_reference(self) -> None:
        item = {
            "platform": "mp.weixin.qq.com",
            "item_type": "article",
            "title": "政策解读 微信搜索候选",
            "url": "https://mp.weixin.qq.com/s/example",
            "query": "政策解读",
            "evidence_status": "sogou公开搜索结果",
            "content_excerpt": "政策解读 微信搜索候选",
            "relevance_score": 70,
            "raw_metadata_json": '{"article_fetch_status":"article_fetch_failed:UnicodeEncodeError"}',
        }
        self.assertEqual(interpretation.count_reference_items([item]), 0)
        health = interpretation.interpretation_health_stats([item])
        self.assertEqual(health["article_pages_failed"], 1)

    def test_low_relevance_article_page_does_not_count_as_reference(self) -> None:
        item = {
            "platform": "cctv.com",
            "item_type": "article",
            "title": "自然_CCTV节目官网-纪录片_央视网",
            "url": "https://tv.cctv.com/2013/01/14/example.shtml",
            "query": "海洋生物医药产业发展 政策解读",
            "evidence_status": "cctv.com公开站内搜索结果；正文已摘录",
            "content_excerpt": "播出中外自然类纪录片精品，展示大自然的神奇瑰丽。",
            "relevance_score": 52,
            "raw_metadata_json": '{"article_fetch_status":"article_excerpt_extracted"}',
        }
        self.assertEqual(interpretation.count_reference_items([item]), 0)

    def test_generic_policy_index_page_does_not_count_as_reference(self) -> None:
        item = {
            "platform": "gov.cn",
            "item_type": "article",
            "title": "最新政策",
            "url": "https://www.gov.cn/zhengce/index.htm",
            "query": "海洋生物医药产业发展 政策解读",
            "evidence_status": "已入库公开相关文件/解读",
            "content_excerpt": "最新政策 国务院关于印发规划的通知 政策解读 答记者问 更多。",
            "relevance_score": 78,
            "raw_metadata_json": '{"local_related_document":true}',
        }
        self.assertEqual(interpretation.count_reference_items([item]), 0)

        item["title"] = "省政府公报"
        item["url"] = "https://www.gd.gov.cn/zwgk/gongbao/index.html"
        item["content_excerpt"] = "省政府公报 最新发布 历史公报 政策文件目录。"
        self.assertEqual(interpretation.count_reference_items([item]), 0)

    def test_broad_health_plan_does_not_count_for_drug_retail_license_subject(self) -> None:
        item = {
            "platform": "gov.cn",
            "item_type": "article",
            "title": "国务院办公厅关于印发“十四五”国民健康规划的通知",
            "url": "https://www.gov.cn/zhengce/content/2022-05/20/content_5691424.htm",
            "query": "广东省药品监督管理局药品零售许可验收实施细则（2026年修订） 政策解读",
            "evidence_status": "已入库公开相关文件/解读",
            "content_excerpt": "国民健康规划提出完善医疗卫生服务、药品供应保障和公共卫生体系。",
            "relevance_score": 80,
            "raw_metadata_json": '{"local_related_document":true}',
        }
        self.assertFalse(
            interpretation.has_subject_relevance(
                item["title"],
                item["content_excerpt"],
                item["query"],
            )
        )
        self.assertEqual(interpretation.count_reference_items([item]), 0)

    def test_policy_article_without_subject_match_does_not_count_as_reference(self) -> None:
        item = {
            "platform": "gd.gov.cn",
            "item_type": "article",
            "title": "农村集体土地留用地管理政策解读",
            "url": "https://www.gd.gov.cn/land-policy.html",
            "query": "广东省药品监督管理局 药品零售许可验收实施细则 政策解读",
            "evidence_status": "已入库公开相关文件/解读",
            "content_excerpt": "该政策解读围绕农村集体土地留用地开发利用、规划管理和收益分配展开。",
            "relevance_score": 94,
            "raw_metadata_json": '{"local_related_document":true}',
        }
        self.assertFalse(
            interpretation.has_subject_relevance(
                item["title"],
                item["content_excerpt"],
                item["query"],
            )
        )
        self.assertEqual(interpretation.count_reference_items([item]), 0)

    def test_policy_article_with_subject_match_counts_as_reference(self) -> None:
        item = {
            "platform": "gd.gov.cn",
            "item_type": "article",
            "title": "广东省药品零售许可验收实施细则政策解读",
            "url": "https://www.gd.gov.cn/drug-retail-policy.html",
            "query": "广东省药品监督管理局 药品零售许可验收实施细则 政策解读",
            "evidence_status": "已入库公开相关文件/解读",
            "content_excerpt": "该政策解读围绕药品零售许可、验收实施细则、药品监管要求和企业开办流程展开。",
            "relevance_score": 82,
            "raw_metadata_json": '{"local_related_document":true}',
        }
        self.assertTrue(
            interpretation.has_subject_relevance(
                item["title"],
                item["content_excerpt"],
                item["query"],
            )
        )
        self.assertEqual(interpretation.count_reference_items([item]), 1)

    def test_exam_or_recruiting_video_does_not_count_as_reference(self) -> None:
        item = {
            "platform": "bilibili",
            "item_type": "video",
            "title": "农业农村厅招聘 事业单位笔试备考",
            "url": "https://www.bilibili.com/video/BV1",
            "query": "农业农村现代化 政策解读",
            "evidence_status": "公开视频搜索结果；互动摘录已采集",
            "content_excerpt": "标签：事业单位招聘, 公考, 备考, 刷题。",
            "relevance_score": 78,
        }
        self.assertEqual(interpretation.count_reference_items([item]), 0)

    def test_low_value_trading_video_does_not_count_as_reference(self) -> None:
        item = {
            "platform": "bilibili",
            "item_type": "video",
            "title": "消费、酒、证券 不动 明天再看一天",
            "url": "https://www.bilibili.com/video/BV1",
            "query": "加强监管防范风险促进私募投资基金高质量发展的指导意见 证券 政策解读",
            "evidence_status": "公开视频搜索结果；互动摘录已采集",
            "content_excerpt": "证券 ETF 复盘，明天再看一天，短线不动。",
            "relevance_score": 78,
        }
        self.assertEqual(interpretation.count_reference_items([item]), 0)

    def test_policy_research_video_counts_as_reference(self) -> None:
        item = {
            "platform": "bilibili",
            "item_type": "video",
            "title": "私募投资基金监管指导意见政策解读",
            "url": "https://www.bilibili.com/video/BV2",
            "query": "加强监管防范风险促进私募投资基金高质量发展的指导意见 证券 政策解读",
            "evidence_status": "公开视频搜索结果；互动摘录已采集",
            "content_excerpt": "围绕国务院办公厅指导意见、证监会监管要求、私募基金风险防范和资本市场高质量发展进行分析。",
            "relevance_score": 82,
        }
        self.assertEqual(interpretation.count_reference_items([item]), 1)

    def test_land_protection_policy_article_counts_as_reference(self) -> None:
        item = {
            "platform": "news.ycwb.com",
            "item_type": "article",
            "title": "守护城市粮袋子，广州耕地保护专项规划等你提建议",
            "url": "https://news.ycwb.com/example.html",
            "query": "广州首部区级耕地保护专项规划 政策解读",
            "evidence_status": "sogou公开搜索结果；正文已摘录",
            "content_excerpt": "广州市规划和自然资源局发布耕地保护专项规划公众征求意见稿，围绕粮食安全、永久基本农田、国土空间格局和耕地后备资源不足等问题展开。",
            "relevance_score": 60,
            "raw_metadata_json": '{"article_fetch_status":"article_excerpt_extracted"}',
        }
        self.assertTrue(
            interpretation.has_subject_relevance(
                item["title"],
                item["content_excerpt"],
                item["query"],
            )
        )
        self.assertEqual(interpretation.count_reference_items([item]), 1)

    def test_land_protection_policy_video_counts_as_reference(self) -> None:
        item = {
            "platform": "bilibili",
            "item_type": "video",
            "title": "如何以补定占坚持耕地保护？专家谈因地制宜",
            "url": "https://www.bilibili.com/video/BV3",
            "query": "广州首部区级耕地保护专项规划 政策解读",
            "evidence_status": "公开视频搜索结果；互动摘录已采集",
            "content_excerpt": "三农智库围绕一号文件、耕地保护、粮食安全、乡村振兴和地方落实约束进行政策分析。",
            "relevance_score": 68,
        }
        self.assertEqual(interpretation.count_reference_items([item]), 1)

    def test_land_protection_game_video_does_not_count_as_reference(self) -> None:
        item = {
            "platform": "bilibili",
            "item_type": "video",
            "title": "我的世界网红模组：耕地保护",
            "url": "https://www.bilibili.com/video/BV4",
            "query": "广州首部区级耕地保护专项规划 政策解读",
            "evidence_status": "公开视频搜索结果；互动摘录已采集",
            "content_excerpt": "标签：MC, MOD, 单机游戏, 模组推荐, 我的世界。",
            "relevance_score": 68,
        }
        self.assertEqual(interpretation.count_reference_items([item]), 0)

    def test_duplicate_current_and_historical_reference_counts_once(self) -> None:
        base = {
            "platform": "serpapi_google",
            "item_type": "search_result",
            "title": "广州市耕地保护专项规划（2021—2035年）",
            "url": "https://ghzyj.gz.gov.cn/sjb/zw/zcfg/content/post_10358375.html?from=serp",
            "query": "广州首部区级耕地保护专项规划 政策解读",
            "evidence_status": "serpapi公开搜索结果；正文已摘录",
            "content_excerpt": "广州市耕地保护专项规划围绕粮食安全、永久基本农田、自然资源管理、国土空间和耕地保护责任进行部署。",
            "relevance_score": 84,
            "raw_metadata_json": '{"article_fetch_status":"article_excerpt_extracted"}',
        }
        reused = {
            **base,
            "url": "https://ghzyj.gz.gov.cn/sjb/zw/zcfg/content/post_10358375.html",
            "evidence_status": "历史成功公开参考复用；原状态：serpapi公开搜索结果；正文已摘录",
            "relevance_score": 68,
        }
        self.assertEqual(interpretation.count_reference_items([base, reused]), 1)

    def test_public_article_follows_client_side_redirect_once(self) -> None:
        old_urlopen = web_article.urlopen
        calls: list[str] = []

        class FakeResponse:
            def __init__(self, url: str, body: str) -> None:
                self._url = url
                self._body = body.encode("utf-8")
                self.headers = {"Content-Type": "text/html; charset=utf-8"}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def geturl(self) -> str:
                return self._url

            def read(self, _max_bytes: int) -> bytes:
                return self._body

        def fake_urlopen(request, *args, **kwargs):
            url = request.full_url
            calls.append(url)
            if url == "https://www.sogou.com/link?url=abc":
                return FakeResponse(
                    url,
                    '<script>window.location.replace("https://news.example.com/policy.html")</script>',
                )
            return FakeResponse(
                url,
                """
                <html><head><title>政策解读：产业影响</title></head><body>
                <article><p>政策解读正文摘录，分析产业影响、监管要求、企业机会、实施路径、风险约束和后续监测指标。文章进一步说明执行主体、时间安排、配套措施、商业影响、合规边界和地方落地差异，足以作为公开网页参考材料。</p></article>
                </body></html>
                """,
            )

        try:
            web_article.urlopen = fake_urlopen
            result = web_article.fetch_public_article("https://www.sogou.com/link?url=abc", retries=0)
        finally:
            web_article.urlopen = old_urlopen

        self.assertEqual(result.status, "article_excerpt_extracted")
        self.assertEqual(result.fetched_url, "https://news.example.com/policy.html")
        self.assertIn("产业影响", result.text)
        self.assertEqual(calls, ["https://www.sogou.com/link?url=abc", "https://news.example.com/policy.html"])


if __name__ == "__main__":
    unittest.main()
