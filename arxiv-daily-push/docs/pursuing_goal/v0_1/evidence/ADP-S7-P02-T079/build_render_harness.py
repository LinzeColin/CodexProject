#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P02-T079 -- build a faithful standalone render harness from the REAL worker base CSS, so the
acceptance criterion "no full-page horizontal scroll" can be proven by an actual browser render at
360/390/430 px (addresses the skeptic's methodological point + the nav.nav-top overflow candidate).

The harness embeds the worker's base CSS verbatim (structural box-model rules -- flex/padding/overflow-wrap/
table display:block are what govern overflow, and are colour-independent), provides :root variable fallbacks
so the layout resolves, sets data-nav=topbar + data-theme=minimal (a topbar theme, the nav.nav-top case),
and fills the page with WORST-CASE data-dense content: an unbreakable long URL, a long 文号/DOI, a wide
multi-column table, and a wide image. If documentElement.scrollWidth <= innerWidth at every width, there is
no full-page horizontal scroll."""
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import visual_baseline as VB

OUT = V01 / "evidence" / "ADP-S7-P02-T079" / "render_harness.html"

src = VB.WORKER.read_text(encoding="utf-8")
base_css = VB._tmpl(src, "CSS")           # the real ${CSS} template body
hero_css = VB._tmpl(src, "HERO_CSS") or ""
# ${HERO_CSS} is interpolated into CSS at runtime; inline it so the harness matches the served CSS.
base_css = base_css.replace("${HERO_CSS}", hero_css)

# :root variable fallbacks (topbar/minimal-ish) so the box model resolves; colours are irrelevant to overflow.
ROOT_VARS = """:root{
  --bg:#f7f7fb; --tx:#1a1a22; --ink:#0b0b12; --ac:#3a5bd9; --hairline:#e2e2ea;
  --glass-bg:rgba(255,255,255,.7); --glass-blur:10px; --pill:999px; --radius:16px; --shadow:0 1px 3px rgba(0,0,0,.08);
  --card-bg:#fff; --muted:#6b6b78; --font-body:system-ui,sans-serif; --font-display:system-ui,sans-serif;
  --display-style:normal; --display-ls:0; --good:#1a7f4b; --bad:#c0392b; --warn:#b8860b;
  --nav-w:216px; --line:#e2e2ea; --chip:#eef;
}
:root[data-nav="topbar"]{}"""

# worst-case data-dense content: long unbreakable URL, long 文号/DOI, wide table, wide image
BODY = """
<header class="top"><b><a href="/" style="color:inherit">ADP 前沿学习</a></b>
<nav class="nav-top" aria-label="主导航"><a href="/" class="active">今天</a><a href="/review">复习</a><a href="/radar">前沿雷达</a><a href="/system">系统</a></nav></header>
<main>
  <div class="card">
    <div class="body">
      <h3>数据密集卡片（最坏情况）</h3>
      <p>原文链接：https://www.gov.cn/zhengce/zhengceku/2016-2026/notice/very-long-unbreakable-path/GBT-1234567890-ABCDEFGHIJKLMNOP/index.html?ref=adp&amp;q=super-long-query-string-that-cannot-break</p>
      <p>文号：国办发〔2026〕第114514191981号 · DOI：10.1000/xyz123.4567890123456789.abcdefghijklmnop.qrstuvwxyz</p>
      <p>跨源关系：中央政策（国务院）→ 省级实施细则（广东省人民政府办公厅）→ 市级配套（深圳市发展和改革委员会）→ 学术支撑 arXiv:2601.01234v3</p>
      <table>
        <thead><tr><th>数据源</th><th>板块</th><th>层级</th><th>最近运行</th><th>状态</th><th>覆盖年月</th><th>成本估计</th><th>下一步</th></tr></thead>
        <tbody>
        <tr><td>国务院政策文件库</td><td>政策</td><td>A0</td><td>2026-07-16 20:00</td><td>健康</td><td>2016-01 至 2026-07</td><td>￥0.00</td><td>继续每日抓取</td></tr>
        <tr><td>国家统计局统计数据发布</td><td>统计</td><td>A0</td><td>2026-07-16 20:00</td><td>健康</td><td>2016-01 至 2026-07</td><td>￥0.00</td><td>继续每日抓取</td></tr>
        </tbody>
      </table>
      <img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1600' height='200'><rect width='1600' height='200' fill='%23ccc'/></svg>" alt="wide image 1600px">
    </div>
  </div>
</main>
"""

html = ("<!doctype html><html lang='zh' data-nav='topbar' data-theme='minimal'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<style>{ROOT_VARS}\n{base_css}</style></head><body>{BODY}</body></html>")
OUT.write_text(html, encoding="utf-8")
print("wrote", OUT, f"({len(html)} bytes)")
print("base_css length:", len(base_css), "| hero_css inlined:", len(hero_css))
