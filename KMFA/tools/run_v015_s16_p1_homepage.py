#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S16-P1 经营首页公开演示。"""

from __future__ import annotations

import argparse
import json
import threading
from http import HTTPStatus
from typing import Any
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s15_p3_app_experience as p3_runtime
from KMFA.tools import v015_s16_p1_homepage as kernel


def _json_for_html(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_html() -> str:
    html = p3_runtime.render_html()
    homepage = '''
    <section id="homepage-view" class="homepage-view" aria-labelledby="homepage-title" hidden>
      <header class="homepage-head">
        <div>
          <span class="homepage-kicker">经营首页</span>
          <h1 id="homepage-title">今天先看这 5 件事</h1>
          <p id="homepage-summary">正在核对当前公司和期间的公开演示资料…</p>
        </div>
        <div class="homepage-cutoff"><span>数据截止</span><strong id="homepage-cutoff">—</strong><span id="homepage-scope">—</span></div>
      </header>
      <div id="homepage-feedback" class="homepage-feedback" role="status" aria-live="polite">正在加载经营摘要…</div>
      <section class="homepage-section" aria-labelledby="business-summary-title">
        <div class="section-heading"><div><h2 id="business-summary-title">核心经营摘要</h2><p>每个数字都说明来源、截止日和资料是否完整。</p></div><span id="summary-count" class="quiet-count">5 项</span></div>
        <div id="homepage-metrics" class="summary-rail" aria-label="核心经营数字"></div>
      </section>
      <div class="homepage-columns">
        <section class="homepage-section focus-section" aria-labelledby="focus-title">
          <div class="section-heading"><div><h2 id="focus-title">本期重点事项</h2><p>只保留最需要处理的 5 项，每项一个主动作。</p></div><span class="quiet-count">最多 5 项</span></div>
          <ol id="homepage-focus" class="focus-list"></ol>
        </section>
        <section class="homepage-section trend-section" aria-labelledby="trend-title">
          <div class="section-heading"><div><h2 id="trend-title">近四期趋势</h2><p>看方向，不用装饰图形代替判断。</p></div></div>
          <div id="homepage-trends" class="trend-list"></div>
          <details class="trend-table-details" open><summary>趋势数据表</summary><div class="table-scroll"><table><caption class="visually-hidden">近四期经营趋势表格</caption><thead id="trend-table-head"></thead><tbody id="trend-table-body"></tbody></table></div></details>
        </section>
      </div>
      <section class="homepage-section portfolio-section" aria-labelledby="portfolio-title">
        <div class="section-heading"><div><h2 id="portfolio-title">项目组合</h2><p>用收入、毛利率、回款进度和状态快速比较，不使用装饰性雷达图。</p></div><a class="text-link" href="/projects" data-route="/projects">查看全部项目</a></div>
        <div class="table-scroll"><table class="portfolio-table"><caption class="visually-hidden">公开演示项目组合矩阵</caption><thead><tr><th>项目</th><th>收入</th><th>毛利率</th><th>回款进度</th><th>状态</th><th>下一步</th></tr></thead><tbody id="portfolio-body"></tbody></table></div>
      </section>
      <p class="demo-disclaimer">当前均为公开演示内容，用于验证页面和工作顺序，不代表任何真实公司的经营结论。</p>
    </section>'''
    extra_css = '''
    .homepage-view { margin-bottom:24px; }
    body[data-homepage-active="true"] #page-view,body[data-homepage-active="true"] #experience-workspace { display:none!important; }
    .homepage-head { display:flex; justify-content:space-between; align-items:flex-start; gap:28px; margin:4px 0 16px; }
    .homepage-kicker { display:block; margin-bottom:5px; color:var(--blue-dark); font-size:12px; font-weight:750; letter-spacing:.04em; }
    .homepage-head h1 { margin:0; color:var(--navy); font-size:25px; line-height:1.25; }
    .homepage-head p { max-width:64ch; margin:7px 0 0; color:var(--muted); font-size:14px; line-height:1.6; }
    .homepage-cutoff { min-width:190px; display:grid; justify-items:end; gap:2px; color:var(--muted); font-size:12px; }
    .homepage-cutoff strong { color:var(--text); font-size:15px; }
    .homepage-feedback { margin-bottom:14px; padding:9px 12px; border:1px solid #b7cfbf; border-radius:6px; background:#f6faf7; color:#235b3c; font-size:13px; line-height:1.5; }
    .homepage-feedback[data-state="incomplete"] { border-color:#d7bc80; background:#fffaf0; color:#6b4c11; }
    .homepage-feedback[data-state="error"] { border-color:#d7a6a6; background:#fff8f7; color:#7f2929; }
    .homepage-section { margin-bottom:16px; padding:17px 18px; border:1px solid var(--line); border-radius:8px; background:#fff; }
    .section-heading { display:flex; justify-content:space-between; align-items:flex-start; gap:18px; margin-bottom:13px; }
    .section-heading h2 { margin:0; color:var(--navy); font-size:17px; line-height:1.35; }
    .section-heading p { margin:4px 0 0; color:var(--muted); font-size:13px; line-height:1.5; }
    .quiet-count { flex:none; color:#536b7c; font-size:12px; font-weight:650; }
    .summary-rail { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); border:1px solid var(--line); border-radius:7px; overflow:hidden; }
    .summary-item { min-width:0; padding:13px 14px; border-right:1px solid var(--line); background:#fbfcfd; }
    .summary-item:last-child { border-right:0; }
    .summary-label { display:flex; align-items:center; justify-content:space-between; gap:8px; color:#4b6171; font-size:12px; font-weight:700; }
    .summary-completeness { color:#246044; font-size:11px; font-weight:700; white-space:nowrap; }
    .summary-completeness[data-state="INCOMPLETE"] { color:#7a5413; }
    .summary-value { display:block; margin-top:8px; color:var(--navy); font-size:21px; font-variant-numeric:tabular-nums; line-height:1.25; }
    .summary-secondary { display:block; min-height:18px; margin-top:4px; color:#40596b; font-size:12px; font-weight:650; }
    .summary-source { display:block; min-height:54px; margin-top:9px; color:var(--muted); font-size:11px; line-height:1.45; }
    .summary-link { display:inline-flex; min-height:32px; margin-top:7px; align-items:center; color:var(--blue-dark); font-size:12px; font-weight:700; text-decoration:none; }
    .summary-link:hover,.text-link:hover { text-decoration:underline; }
    .homepage-columns { min-width:0; display:grid; grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr); gap:16px; align-items:start; }
    .homepage-columns > * { min-width:0; }
    .focus-list { margin:0; padding:0; list-style:none; }
    .focus-row { display:grid; grid-template-columns:28px minmax(0,1fr) auto; gap:10px; align-items:center; padding:11px 0; border-top:1px solid #e4eaee; }
    .focus-row:first-child { padding-top:0; border-top:0; }
    .focus-rank { display:flex; width:25px; height:25px; align-items:center; justify-content:center; border:1px solid #b5c6d2; border-radius:50%; color:var(--blue-dark); font-size:12px; font-weight:750; }
    .focus-copy strong { display:block; color:var(--text); font-size:14px; line-height:1.4; }
    .focus-copy span { display:block; margin-top:3px; color:var(--muted); font-size:12px; line-height:1.45; }
    .primary-link { display:inline-flex; min-height:38px; padding:7px 10px; align-items:center; border:1px solid #9eb5c5; border-radius:6px; color:var(--blue-dark); font-size:12px; font-weight:700; text-decoration:none; white-space:nowrap; }
    .primary-link:hover { border-color:var(--blue); background:#edf6fb; }
    .trend-list { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
    .trend-item { padding:11px; border:1px solid #dbe4ea; border-radius:6px; background:#fbfcfd; }
    .trend-item-head { display:flex; justify-content:space-between; align-items:baseline; gap:8px; }
    .trend-item strong { color:var(--text); font-size:13px; }
    .trend-item span { color:var(--muted); font-size:11px; }
    .trend-svg { width:100%; height:70px; margin-top:7px; overflow:visible; }
    .trend-svg line { stroke:#d7e0e6; stroke-width:1; }
    .trend-svg polyline { fill:none; stroke:var(--blue); stroke-width:2.5; stroke-linecap:round; stroke-linejoin:round; }
    .trend-svg circle { fill:#fff; stroke:var(--blue); stroke-width:2; }
    .trend-table-details { margin-top:11px; }
    .trend-table-details summary { cursor:pointer; color:var(--blue-dark); font-size:12px; font-weight:700; }
    .table-scroll { display:block; width:100%; max-width:100%; overflow:auto; }
    .trend-table-details table,.portfolio-table { width:100%; margin-top:8px; border-collapse:collapse; font-size:12px; }
    .trend-table-details th,.trend-table-details td,.portfolio-table th,.portfolio-table td { padding:8px 9px; border-bottom:1px solid #e4eaee; text-align:left; white-space:nowrap; }
    .trend-table-details th,.portfolio-table th { background:#f3f6f8; color:#4b6171; font-weight:700; }
    .portfolio-table td:first-child { color:var(--text); font-weight:700; }
    .portfolio-table tr:last-child td,.trend-table-details tr:last-child td { border-bottom:0; }
    .status-text { display:inline-flex; align-items:center; gap:6px; color:#275d43; font-weight:700; }
    .status-text::before { content:'✓'; }
    .status-text[data-state="ATTENTION"] { color:#855b12; }
    .status-text[data-state="ATTENTION"]::before { content:'!'; }
    .text-link { display:inline-flex; min-height:32px; align-items:center; color:var(--blue-dark); font-size:12px; font-weight:700; text-decoration:none; }
    .demo-disclaimer { margin:2px 2px 0; color:var(--muted); font-size:12px; line-height:1.5; }
    @media (max-width:1100px) { .summary-rail { grid-template-columns:repeat(3,minmax(0,1fr)); } .summary-item:nth-child(3) { border-right:0; } .summary-item:nth-child(n+4) { border-top:1px solid var(--line); } .summary-item:nth-child(4) { grid-column:span 2; } .homepage-columns { grid-template-columns:minmax(0,1fr); } }
    @media (max-width:760px) { .homepage-head { display:block; } .homepage-cutoff { margin-top:12px; justify-items:start; } .summary-rail { grid-template-columns:1fr; } .summary-item,.summary-item:nth-child(3),.summary-item:nth-child(4) { grid-column:auto; border-right:0; border-top:1px solid var(--line); } .summary-item:first-child { border-top:0; } .summary-source { min-height:0; } .trend-list { grid-template-columns:1fr; } .focus-row { grid-template-columns:28px minmax(0,1fr); } .focus-row .primary-link { grid-column:2; justify-self:start; min-height:44px; } .homepage-section { padding:15px; } .section-heading { align-items:flex-start; } .homepage-head p,.section-heading p,.summary-label,.summary-value,.summary-secondary,.summary-source,.summary-link,.focus-copy strong,.focus-copy span,.primary-link,.trend-item strong,.trend-item span,.trend-table-details summary,.trend-table-details table,.portfolio-table,.demo-disclaimer { font-size:14px; } }
    @media (pointer:coarse) { .summary-link,.primary-link,.text-link,.trend-table-details summary { min-height:44px; } }
    @media (prefers-reduced-motion:reduce) { .homepage-view * { scroll-behavior:auto!important; transition:none!important; animation:none!important; } }
    '''
    script = f'''
  <script>
  (() => {{
    'use strict';
    const homepage=document.querySelector('#homepage-view'); const feedback=document.querySelector('#homepage-feedback'); const metricsRoot=document.querySelector('#homepage-metrics'); const focusRoot=document.querySelector('#homepage-focus'); const trendsRoot=document.querySelector('#homepage-trends'); const trendHead=document.querySelector('#trend-table-head'); const trendBody=document.querySelector('#trend-table-body'); const portfolioBody=document.querySelector('#portfolio-body');
    let dataState='complete'; let lastSnapshot=null; let requestSequence=0;
    const isHome=()=>location.pathname==='/'||location.pathname==='/overview';
    const text=(tag,value,className='')=>{{ const node=document.createElement(tag); node.textContent=value==null?'':String(value); if(className)node.className=className; return node; }};
    const routeLink=(label,route,className)=>{{ const link=text('a',label,className); link.href=route; link.dataset.route=route; return link; }};
    const identity=()=>window.KMFA_ROLE_TEST.identity();
    const context=()=>window.KMFA_TEST.context();
    const setFeedback=(message,state='')=>{{ feedback.textContent=message; if(state)feedback.dataset.state=state; else delete feedback.dataset.state; }};
    const renderMetrics=rows=>{{ metricsRoot.replaceChildren(); rows.forEach(row=>{{ const article=document.createElement('article'); article.className='summary-item'; article.dataset.metricId=row.metric_id; const label=text('div','', 'summary-label'); label.append(text('span',row.label_zh),text('span',row.completeness_zh,'summary-completeness')); label.lastChild.dataset.state=row.completeness; const value=text('strong',row.display_zh,'summary-value'); const secondary=text('span',row.secondary_display_zh||' ','summary-secondary'); const source=text('small','来源：'+row.source_zh+'\\n截止：'+row.cutoff_date+' · '+row.completeness_zh,'summary-source'); source.style.whiteSpace='pre-line'; const link=routeLink('查看详情',row.route,'summary-link'); article.append(label,value,secondary,source,link); metricsRoot.append(article); }}); }};
    const renderFocus=rows=>{{ focusRoot.replaceChildren(); rows.forEach(row=>{{ const li=document.createElement('li'); li.className='focus-row'; const rank=text('span',row.focus_rank,'focus-rank'); const copy=text('div','', 'focus-copy'); copy.append(text('strong',row.title_zh),text('span',row.owner_role+' · '+row.reason_zh)); const action=routeLink(row.primary_action.label_zh,row.primary_action.route,'primary-link'); li.append(rank,copy,action); focusRoot.append(li); }}); }};
    const points=values=>{{ const min=Math.min(...values),max=Math.max(...values),span=Math.max(1,max-min); return values.map((value,index)=>{{ const x=8+index*28; const y=60-Math.round((value-min)*44/span); return x+','+y; }}).join(' '); }};
    const renderTrends=rows=>{{ trendsRoot.replaceChildren(); rows.forEach(row=>{{ const article=document.createElement('article'); article.className='trend-item'; const head=text('div','', 'trend-item-head'); head.append(text('strong',row.label_zh),text('span',row.display_values_zh.at(-1))); const svg=document.createElementNS('http://www.w3.org/2000/svg','svg'); svg.classList.add('trend-svg'); svg.setAttribute('viewBox','0 0 100 68'); svg.setAttribute('role','img'); svg.setAttribute('aria-label',row.label_zh+'：'+row.periods.map((period,index)=>period+' '+row.display_values_zh[index]).join('，')); [16,38,60].forEach(y=>{{ const line=document.createElementNS(svg.namespaceURI,'line'); line.setAttribute('x1','8'); line.setAttribute('x2','92'); line.setAttribute('y1',String(y)); line.setAttribute('y2',String(y)); svg.append(line); }}); const poly=document.createElementNS(svg.namespaceURI,'polyline'); poly.setAttribute('points',points(row.values_cents)); svg.append(poly); points(row.values_cents).split(' ').forEach(pair=>{{ const [x,y]=pair.split(','); const circle=document.createElementNS(svg.namespaceURI,'circle'); circle.setAttribute('cx',x); circle.setAttribute('cy',y); circle.setAttribute('r','3'); svg.append(circle); }}); article.append(head,svg); trendsRoot.append(article); }}); trendHead.replaceChildren(); const tr=document.createElement('tr'); tr.append(text('th','指标')); rows[0].periods.forEach(period=>tr.append(text('th',period))); trendHead.append(tr); trendBody.replaceChildren(); rows.forEach(row=>{{ const tableRow=document.createElement('tr'); tableRow.append(text('th',row.label_zh)); row.display_values_zh.forEach(value=>tableRow.append(text('td',value))); trendBody.append(tableRow); }}); }};
    const renderProjects=rows=>{{ portfolioBody.replaceChildren(); rows.forEach(row=>{{ const tr=document.createElement('tr'); const status=text('span',row.status_zh,'status-text'); status.dataset.state=row.status; const action=routeLink(row.next_step_zh,row.route,'text-link'); [text('td',row.project_name_zh),text('td',row.revenue_display_zh),text('td',row.gross_margin_display_zh),text('td',row.collection_display_zh)].forEach(node=>tr.append(node)); const statusCell=document.createElement('td'); statusCell.append(status); const actionCell=document.createElement('td'); actionCell.append(action); tr.append(statusCell,actionCell); portfolioBody.append(tr); }}); }};
    const render=payload=>{{ lastSnapshot=payload; document.querySelector('#homepage-cutoff').textContent=payload.as_of_date; document.querySelector('#homepage-scope').textContent=payload.context_labels.company+' · '+payload.context_labels.period; document.querySelector('#homepage-summary').textContent=payload.honest_summary_zh; document.querySelector('#summary-count').textContent=payload.summary_metric_count+' 项'; renderMetrics(payload.summary_metrics); renderFocus(payload.focus_items); renderTrends(payload.trend_series); renderProjects(payload.project_portfolio); const incomplete=payload.overall_completeness==='INCOMPLETE'; setFeedback((incomplete?'资料不完整：':'资料已核对：')+payload.honest_summary_zh,incomplete?'incomplete':''); }};
    const load=async()=>{{ if(!isHome()){{ homepage.hidden=true; delete document.body.dataset.homepageActive; return null; }} homepage.hidden=false; document.body.dataset.homepageActive='true'; setFeedback('正在核对当前公司和期间的经营摘要…'); const sequence=++requestSequence; const who=identity(),scope=context(); const params=new URLSearchParams({{user_id:who.user_id,role_id:who.role_id,company_id:scope.company,period:scope.period,data_state:dataState}}); try {{ const response=await fetch('/api/homepage?'+params); const payload=await response.json(); if(sequence!==requestSequence)return {{stale_response_ignored:true}}; if(!response.ok||!payload.allowed){{ setFeedback(payload.reason_zh||'当前身份无法查看经营首页。','error'); metricsRoot.replaceChildren(); focusRoot.replaceChildren(); trendsRoot.replaceChildren(); portfolioBody.replaceChildren(); return payload; }} render(payload); return payload; }} catch (_) {{ if(sequence===requestSequence)setFeedback('经营摘要暂时无法读取，请重新尝试。','error'); return null; }} }};
    const refresh=()=>setTimeout(load,0);
    document.querySelector('#context-company').addEventListener('change',refresh); document.querySelector('#context-period').addEventListener('change',refresh); document.querySelector('#identity-user').addEventListener('change',refresh); window.addEventListener('popstate',refresh);
    new MutationObserver(refresh).observe(document.querySelector('#page-title'),{{childList:true,subtree:true}}); new MutationObserver(refresh).observe(document.querySelector('#active-role-chip'),{{childList:true,subtree:true}});
    window.KMFA_HOMEPAGE_TEST={{load,setDataState:value=>{{ dataState={_json_for_html(list(kernel.DATA_STATES))}.includes(value)?value:'complete'; return load(); }},snapshot:()=>lastSnapshot,isActive:isHome}};
    load();
  }})();
  </script>
'''
    html = html.replace("<title>KMFA 快速工作 · 经营工作台</title>", "<title>KMFA 经营首页 · 经营工作台</title>")
    html = html.replace("  </style>", extra_css + "  </style>", 1)
    marker = '<div id="context-status" class="status-line" role="status" aria-live="polite"><span>正在准备演示内容…</span></div>'
    if marker not in html:
        raise RuntimeError("S15-P3 runtime insertion point drifted")
    html = html.replace(marker, marker + homepage, 1)
    html = html.replace("</body>", script + "</body>", 1)
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class HomepageHandler(p3_runtime.AppExperienceHandler):
    server_version = "KMFAHomepage/1.5"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/api/homepage":
            query = parse_qs(parsed.query)
            try:
                value = kernel.homepage_snapshot(
                    user_id=query.get("user_id", ["demo-owner"])[0],
                    role_id=query.get("role_id", ["management"])[0],
                    company_id=query.get("company_id", ["demo-north"])[0],
                    period=query.get("period", ["2026-07"])[0],
                    data_state=query.get("data_state", ["complete"])[0],
                )
            except kernel.HomepageError as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})
                return
            self._send_json(HTTPStatus.OK if value["allowed"] else HTTPStatus.FORBIDDEN, value)
            return
        if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico":
            super().do_GET()
            return
        self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")


class HomepageServer(p3_runtime.AppExperienceServer):
    pass


def start_server(host: str = "127.0.0.1", port: int = 0) -> tuple[HomepageServer, threading.Thread, str]:
    server = HomepageServer((host, port), HomepageHandler)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s16p1-homepage", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S16-P1 经营首页公开演示")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = HomepageServer((args.host, args.port), HomepageHandler)
    print(f"KMFA S16-P1 经营首页：http://{args.host}:{server.server_address[1]}/overview", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
