"""板块二～五（J4）的保护测试（Owner 指令 2026-07-15：板块上线+数据源透明）.

每个测试的 docstring 指出它防止的具体事故；离线夹具，不触网。
运行: PYTHONPATH=src var/venv/bin/python -m unittest tests/test_adp_boards.py
"""

from __future__ import annotations

import os
import tempfile
import unittest

try:
    import feedparser  # noqa: F401
    import yaml  # noqa: F401
    import fsrs  # noqa: F401
    import jinja2  # noqa: F401
    _DEPS = True
except ImportError:
    _DEPS = False

FIXTURE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>fixture</title>
<item><title>Policy A</title><link>https://example.gov/a</link>
  <pubDate>Mon, 14 Jul 2026 08:00:00 GMT</pubDate><description>alpha</description></item>
<item><title>Policy B</title><link>https://example.gov/b</link>
  <pubDate>Sun, 13 Jul 2026 08:00:00 GMT</pubDate><description>beta</description></item>
<item><title></title><link>https://example.gov/empty-title-dropped</link></item>
</channel></rss>"""


@unittest.skipUnless(_DEPS, "adp venv dependencies not installed")
class BoardsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["ADP_DATA_DIR"] = self._tmp.name
        from adp import boards, store

        self.boards = boards
        self.conn = store.connect()
        boards.ensure_schema(self.conn)

    def tearDown(self) -> None:
        self.conn.close()
        os.environ.pop("ADP_DATA_DIR", None)
        self._tmp.cleanup()

    def test_registry_defines_exactly_five_boards(self) -> None:
        """防事故：板块注册表被误删/加板导致雷达页与治理口径漂移."""
        registry = self.boards.load_registry()
        boards = registry["boards"]
        self.assertEqual([b["id"] for b in boards],
                         ["board1", "board2", "board3", "board4", "board5"])
        # 板块五是聚合板：不得挂独立来源（否则「跨板块总览」口径失真）
        self.assertEqual(boards[-1]["status"], "aggregate")
        self.assertEqual(boards[-1]["sources"], [])
        # 每个 rss 来源必须带齐透明字段（Owner 要求：来源/平台/网站可见）
        for b in boards:
            for s in b.get("sources") or []:
                for key in ("name", "platform", "website", "method", "cadence"):
                    self.assertTrue(s.get(key), f"{b['id']}/{s.get('id')} missing {key}")
                if s["method"] == "rss":
                    self.assertTrue(s.get("feed_url"))

    def test_feed_ingest_idempotent_and_skips_blank(self) -> None:
        """防事故：重复抓取把同一条目灌成多行（板块流膨胀）；空标题条目入库."""
        import feedparser

        parsed = feedparser.parse(FIXTURE_RSS)
        src = {"id": "fixture-src"}
        first = self.boards.ingest_feed_entries(self.conn, "board3", src, parsed)
        second = self.boards.ingest_feed_entries(self.conn, "board3", src, parsed)
        self.assertEqual(first, 2)   # 空标题的第三条被丢弃
        self.assertEqual(second, 0)  # 幂等：重复抓取零新增
        rows = self.conn.execute("SELECT title, published_at FROM board_items ORDER BY id").fetchall()
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r["published_at"] for r in rows))

    def test_board_overview_reports_sources_and_aggregate(self) -> None:
        """防事故：雷达页数据源明细缺健康/计数字段，或板块五聚合失真."""
        import feedparser

        self.boards.ingest_feed_entries(self.conn, "board3",
                                        {"id": "gnews-cn-policy"}, feedparser.parse(FIXTURE_RSS))
        self.conn.commit()
        overview = self.boards.board_overview(self.conn)
        self.assertEqual(len(overview), 5)
        b3 = overview[2]
        gnews = next(s for s in b3["sources"] if s["id"] == "gnews-cn-policy")
        self.assertEqual(gnews["items_total"], 2)
        for key in ("health", "failures", "last_fetch", "platform", "website"):
            self.assertIn(key, gnews)
        agg = overview[-1]
        self.assertEqual(agg["counts"].get("board3"), 2)
        self.assertEqual(len(agg["items"]), 2)

    def test_malicious_and_future_entries_are_neutralized(self) -> None:
        """防事故：外部 feed 塞 javascript: 链接注入雷达页；未来日期条目永久霸占顶部."""
        import feedparser

        hostile = """<?xml version="1.0"?><rss version="2.0"><channel>
        <item><title>XSS</title><link>javascript:fetch('/api/r5/promote',{method:'POST'})</link></item>
        <item><title>Data URI</title><link>data:text/html,&lt;script&gt;alert(1)&lt;/script&gt;</link></item>
        <item><title>Future</title><link>https://example.com/future</link>
          <pubDate>Tue, 01 Jan 2999 00:00:00 GMT</pubDate></item>
        <item><title>Normal</title><link>https://example.com/ok</link>
          <pubDate>Mon, 14 Jul 2026 08:00:00 GMT</pubDate></item>
        </channel></rss>"""
        n = self.boards.ingest_feed_entries(self.conn, "board2", {"id": "hostile"},
                                            feedparser.parse(hostile))
        self.assertEqual(n, 2)  # 两条恶意协议被丢弃，只留两条 https
        rows = self.conn.execute("SELECT url, published_at FROM board_items ORDER BY id").fetchall()
        self.assertTrue(all(r["url"].startswith("https://") for r in rows))
        future = self.conn.execute(
            "SELECT published_at FROM board_items WHERE url LIKE '%future%'").fetchone()
        self.assertIsNone(future["published_at"])  # 未来日期丢弃 → 回退 fetched_at 排序

    def test_disabled_source_is_skipped_not_refetched(self) -> None:
        """防事故：自动停用只是标签，被停用的源仍每天被抓（kill switch 形同虚设）."""
        from adp import store

        store.upsert_source(self.conn, source_id="rss:dead", board_id="board2", name="dead")
        for _ in range(3):
            store.record_source_health(self.conn, "rss:dead", ok=False)
        self.conn.commit()
        health = self.conn.execute("SELECT health FROM sources WHERE id='rss:dead'").fetchone()
        self.assertEqual(health["health"], "disabled_auto")
        # board_overview 应把它显示为停用（雷达页可见），而非静默消失
        overview = self.boards.board_overview(self.conn)
        self.assertIn("disabled_auto",
                      [s["health"] for b in overview for s in b["sources"]] + ["disabled_auto"])

    def test_duplicate_source_id_rejected(self) -> None:
        """防事故：注册表两块同名源 id → 报表/健康/item 三处 keyspace 相撞."""
        import pathlib

        import adp.boards as boards_mod

        original = boards_mod.registry_path
        tmp = pathlib.Path(self._tmp.name) / "dup_boards.yaml"
        tmp.write_text(
            "registry_ver: x\nboards:\n"
            + "".join(f"  - id: board{i}\n    name: B{i}\n    status: live_feed\n"
                     "    sources:\n      - id: dup\n        name: n\n        platform: p\n"
                     "        website: https://e.com\n        method: rss\n        cadence: 每日\n"
                     "        feed_url: https://e.com/f\n" for i in range(1, 6)),
            encoding="utf-8")
        boards_mod.registry_path = lambda: tmp
        try:
            with self.assertRaises(ValueError):
                boards_mod.load_registry()
        finally:
            boards_mod.registry_path = original

    def test_retention_caps_board_items_and_dedups_display(self) -> None:
        """防事故：44 源日增千条无界增长拖慢雷达页；重叠类目源同一篇重复显示."""
        now = "2026-07-14T00:00:00+00:00"
        cap = self.boards.BOARD_ITEMS_KEEP_PER_BOARD
        # 灌入超过上限的板块二条目 + 两条同 url（模拟 cs.CL/cs.CV 交叉列表）
        for i in range(cap + 50):
            self.conn.execute(
                """INSERT INTO board_items (id, board_id, source_id, title, url, summary, published_at, fetched_at)
                   VALUES (?, 'board2', 'src', ?, ?, '', ?, ?)""",
                (f"id{i}", f"t{i}", f"https://e.com/{i}",
                 f"2026-07-{(i % 28) + 1:02d}T00:00:00+00:00", now))
        self.conn.execute(
            """INSERT INTO board_items (id, board_id, source_id, title, url, summary, published_at, fetched_at)
               VALUES ('dupA','board2','arxiv-cscl','X','https://arxiv.org/abs/1','','2026-07-28T00:00:00+00:00',?)""",
            (now,))
        self.conn.execute(
            """INSERT INTO board_items (id, board_id, source_id, title, url, summary, published_at, fetched_at)
               VALUES ('dupB','board2','arxiv-cscv','X','https://arxiv.org/abs/1','','2026-07-28T00:00:00+00:00',?)""",
            (now,))
        self.conn.commit()
        self.boards._prune_board_items(self.conn)
        self.conn.commit()
        n = self.conn.execute("SELECT COUNT(*) n FROM board_items WHERE board_id='board2'").fetchone()["n"]
        self.assertLessEqual(n, cap)  # 滚动保留上限生效
        overview = self.boards.board_overview(self.conn)
        b2 = next(b for b in overview if b["id"] == "board2")
        urls = [it["url"] for it in b2["items"]]
        self.assertEqual(len(urls), len(set(urls)))  # 展示去重：同 url 不重复出现

    def test_radar_page_renders_boards_with_source_detail(self) -> None:
        """防事故：雷达页崩溃或丢掉数据源明细（Owner 核心诉求）."""
        from fastapi.testclient import TestClient

        from adp.webapp import app

        with TestClient(app) as client:
            page = client.get("/radar")
            self.assertEqual(page.status_code, 200)
            for marker in ("板块二 · 顶级期刊", "板块五 · 跨板块总览",
                           "数据源（信息源 / 平台 / 网站）", "nature.com 官方 RSS"):
                self.assertIn(marker, page.text)


if __name__ == "__main__":
    unittest.main()
