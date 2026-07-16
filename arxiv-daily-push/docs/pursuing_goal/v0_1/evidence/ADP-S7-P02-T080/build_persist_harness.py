#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P02-T080 -- build a harness from the REAL worker CSS to prove empirically that a theme switch
(the setAttribute('data-theme',...) that applyTheme performs -- the audit confirms applyTheme does ONLY that
+ sync, no reload/navigate/innerHTML) preserves reading position (scroll), answers (revealed content +
typed input), filters (input value) and expand state (details[open]) across all six themes."""
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import visual_baseline as VB

OUT = V01 / "evidence" / "ADP-S7-P02-T080" / "persist_harness.html"
src = VB.WORKER.read_text(encoding="utf-8")
base_css = VB._tmpl(src, "CSS").replace("${HERO_CSS}", VB._tmpl(src, "HERO_CSS") or "")

ROOT_VARS = """:root{--bg:#f3eee1;--pn:#fdfaf2;--ink:#2f2618;--tx:#4a3d28;--mt:#8b7a5c;--ac:#8a5c16;
--warn:#a4462c;--bd:#d8cfba;--ok:#4f6f3a;--radius:3px;--radius-lg:12px;--pill:3px;--glass-bg:var(--pn);
--glass-blur:0px;--hairline:var(--bd);--shadow:0 1px 3px rgba(47,38,24,.08);--font-body:system-ui,sans-serif;
--font-display:serif;--display-style:normal;--display-ls:0}"""

BODY = """
<header class="top"><b>ADP 前沿学习</b><select id="theme"><option value="warm">warm</option>
<option value="minimal">minimal</option><option value="fresh">fresh</option><option value="techno">techno</option>
<option value="cosmos">cosmos</option><option value="forest">forest</option></select></header>
<main>
  <div class="card"><h2>主动回忆</h2>
    <button class="btn-sm" id="revealBtn" onclick="document.getElementById('revealBox').hidden=false;this.hidden=true">显示答案/讲义</button>
    <div class="reveal" id="revealBox" hidden><p>这是被揭示的答案内容（切主题后应保持展开）。</p></div>
    <div class="gradeRow"><button>忘了</button><button>困难</button><button class="picked">良好</button><button>轻松</button></div>
    <p id="r" class="mt" data-state="ok">已记录状态示例</p>
    <p><label>筛选：<input id="filter" type="text" placeholder="输入关键词"></label></p>
    <details id="dt"><summary>展开更多</summary><p>展开的内容（切主题后应保持展开）。</p></details>
  </div>
  <div class="card" style="height:1400px"><p>占位内容让页面可滚动，用于验证阅读位置不丢。</p></div>
</main>
<script>
// the persistence-relevant line applyTheme runs (audit confirms it does only setAttribute + sync, no reload):
document.getElementById('theme').onchange=function(){document.documentElement.setAttribute('data-theme',this.value);};
</script>
"""
html = ("<!doctype html><html lang='zh' data-nav='topbar' data-theme='warm'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<style>{ROOT_VARS}\n{base_css}</style></head><body>{BODY}</body></html>")
OUT.write_text(html, encoding="utf-8")
print("wrote", OUT, f"({len(html)} bytes)")
