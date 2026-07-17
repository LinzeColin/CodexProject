#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S16-P2 指标下钻与解释公开演示。"""

from __future__ import annotations

import argparse
import json
import threading
from http import HTTPStatus
from typing import Any
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s16_p1_homepage as p1_runtime
from KMFA.tools import v015_s16_p2_drilldown_explanation as kernel


def _json_for_html(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_html() -> str:
    html = p1_runtime.render_html()
    detail = '''
    <section id="drilldown-view" class="drilldown-view" aria-labelledby="drilldown-title" hidden>
      <a id="drilldown-back" class="back-link" href="/overview" data-route="/overview">← 返回经营首页</a>
      <header class="drilldown-head">
        <div>
          <span id="drilldown-domain" class="drilldown-kicker">经营明细</span>
          <h1 id="drilldown-title">正在打开明细…</h1>
          <p id="drilldown-context">正在保留你在首页选择的公司、期间和筛选条件。</p>
        </div>
        <div class="drilldown-cutoff"><span>数据截止</span><strong id="drilldown-cutoff">—</strong></div>
      </header>
      <div id="drilldown-feedback" class="drilldown-feedback" role="status" aria-live="polite">正在核对首页数字与明细…</div>
      <section class="drilldown-section drilldown-summary" aria-labelledby="drilldown-summary-title">
        <div>
          <h2 id="drilldown-summary-title">当前数字</h2>
          <strong id="drilldown-value" class="drilldown-value">—</strong>
          <span id="drilldown-secondary" class="drilldown-secondary"></span>
        </div>
        <div class="plain-explanation">
          <h2>这个数字怎么来的</h2>
          <p id="drilldown-short-explanation">正在读取简明说明…</p>
        </div>
      </section>
      <section class="drilldown-section" aria-labelledby="drilldown-table-title">
        <div class="drilldown-section-head"><div><h2 id="drilldown-table-title">组成明细</h2><p id="drilldown-consistency">正在核对合计…</p></div><span id="drilldown-row-count" class="quiet-count">—</span></div>
        <div class="table-scroll"><table class="drilldown-table"><caption class="visually-hidden">当前指标的公开演示组成明细</caption><thead><tr><th>明细</th><th>当前数值</th><th>补充信息</th><th>状态</th><th>来源</th></tr></thead><tbody id="drilldown-body"></tbody></table></div>
        <p id="drilldown-empty" class="drilldown-empty" hidden></p>
      </section>
      <section class="drilldown-section comparison-section" aria-labelledby="comparison-title">
        <div class="drilldown-section-head">
          <div><h2 id="comparison-title">期间比较</h2><p>只有计算口径和数据范围一致时才显示差异。</p></div>
          <label class="comparison-picker">比较方式<select id="comparison-kind"><option value="MOM">环比</option><option value="YOY">同比</option><option value="BASELINE">预算或基准</option></select></label>
        </div>
        <div id="comparison-feedback" class="comparison-feedback" role="status"></div>
        <dl id="comparison-values" class="comparison-values">
          <div><dt id="current-period-label">当前期间</dt><dd id="comparison-current">—</dd></div>
          <div><dt id="comparison-period-label">比较期间</dt><dd id="comparison-previous">—</dd></div>
          <div><dt>差异</dt><dd id="comparison-delta">—</dd></div>
        </dl>
      </section>
      <details id="professional-evidence" class="professional-evidence">
        <summary>查看专业依据</summary>
        <div class="professional-content"><h2>来源与计算链</h2><p id="drilldown-formula"></p><ol id="lineage-list" class="lineage-list"></ol></div>
      </details>
      <p class="demo-disclaimer">当前均为公开演示内容，只用于验证页面、计算和工作顺序，不代表任何真实公司的经营结论。</p>
    </section>'''
    extra_css = '''
    body[data-drilldown-active="true"] #page-view,body[data-drilldown-active="true"] #access-workspace,body[data-drilldown-active="true"] #experience-workspace,body[data-drilldown-active="true"] #homepage-view,body[data-drilldown-active="true"] #not-found-view,body[data-drilldown-active="true"] #error-view { display:none!important; }
    .drilldown-view { min-width:0; margin-bottom:24px; }
    .back-link { display:inline-flex; min-height:44px; align-items:center; margin-bottom:7px; color:var(--blue-dark); font-size:13px; font-weight:700; text-decoration:none; }
    .back-link:hover { text-decoration:underline; }
    .drilldown-head { display:flex; justify-content:space-between; align-items:flex-start; gap:28px; margin-bottom:16px; }
    .drilldown-kicker { display:block; margin-bottom:5px; color:var(--blue-dark); font-size:12px; font-weight:750; letter-spacing:.04em; }
    .drilldown-head h1 { margin:0; color:var(--navy); font-size:25px; line-height:1.25; }
    .drilldown-head p { max-width:68ch; margin:7px 0 0; color:var(--muted); font-size:14px; line-height:1.6; }
    .drilldown-cutoff { min-width:120px; display:grid; justify-items:end; gap:2px; color:var(--muted); font-size:12px; }
    .drilldown-cutoff strong { color:var(--text); font-size:15px; }
    .drilldown-feedback,.comparison-feedback { padding:9px 12px; border:1px solid #b7cfbf; border-radius:6px; background:#f6faf7; color:#235b3c; font-size:13px; line-height:1.5; }
    .drilldown-feedback { margin-bottom:14px; }
    .drilldown-feedback[data-state="blocked"],.comparison-feedback[data-state="blocked"] { border-color:#d7bc80; background:#fffaf0; color:#6b4c11; }
    .drilldown-feedback[data-state="error"] { border-color:#d7a6a6; background:#fff8f7; color:#7f2929; }
    .drilldown-section { min-width:0; margin-bottom:16px; padding:17px 18px; border:1px solid var(--line); border-radius:8px; background:#fff; }
    .drilldown-summary { display:grid; grid-template-columns:minmax(220px,.36fr) minmax(0,.64fr); gap:22px; align-items:start; }
    .drilldown-section h2,.professional-content h2 { margin:0; color:var(--navy); font-size:17px; line-height:1.35; }
    .drilldown-value { display:block; margin-top:8px; color:var(--navy); font-size:30px; font-variant-numeric:tabular-nums; line-height:1.2; }
    .drilldown-secondary { display:block; min-height:20px; margin-top:5px; color:#40596b; font-size:13px; font-weight:650; }
    .plain-explanation { padding-left:22px; border-left:1px solid var(--line); }
    .plain-explanation p,.drilldown-section-head p,.professional-content p { margin:6px 0 0; color:var(--muted); font-size:13px; line-height:1.65; }
    .drilldown-section-head { display:flex; justify-content:space-between; align-items:flex-start; gap:18px; margin-bottom:12px; }
    .drilldown-table { width:100%; min-width:720px; border-collapse:collapse; font-size:12px; }
    .drilldown-table th,.drilldown-table td { padding:9px; border-bottom:1px solid #e4eaee; text-align:left; vertical-align:top; }
    .drilldown-table th { background:#f3f6f8; color:#4b6171; font-weight:700; white-space:nowrap; }
    .drilldown-table td:first-child { color:var(--text); font-weight:700; }
    .drilldown-table tr:last-child td { border-bottom:0; }
    .drilldown-source { color:var(--muted); font-size:11px; line-height:1.45; }
    .drilldown-empty { margin:0; padding:12px; border:1px solid #d7bc80; border-radius:6px; background:#fffaf0; color:#6b4c11; line-height:1.6; }
    .comparison-picker { display:grid; gap:4px; color:#4b6171; font-size:12px; font-weight:700; }
    .comparison-picker select { min-width:150px; min-height:38px; padding:6px 28px 6px 9px; border:1px solid #afc0cb; border-radius:6px; background:#fff; color:var(--text); }
    .comparison-values { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin:12px 0 0; border:1px solid var(--line); border-radius:7px; overflow:hidden; }
    .comparison-values > div { padding:12px 14px; border-right:1px solid var(--line); background:#fbfcfd; }
    .comparison-values > div:last-child { border-right:0; }
    .comparison-values dt { color:var(--muted); font-size:12px; }
    .comparison-values dd { margin:5px 0 0; color:var(--navy); font-size:18px; font-weight:750; font-variant-numeric:tabular-nums; }
    .professional-evidence { margin-bottom:16px; border:1px solid var(--line); border-radius:8px; background:#fff; }
    .professional-evidence summary { display:flex; min-height:44px; padding:11px 17px; align-items:center; cursor:pointer; color:var(--blue-dark); font-size:13px; font-weight:750; }
    .professional-content { padding:0 17px 17px; border-top:1px solid var(--line); }
    .professional-content h2 { margin-top:15px; }
    .lineage-list { display:grid; gap:8px; margin:13px 0 0; padding:0; list-style:none; }
    .lineage-row { display:grid; grid-template-columns:28px minmax(0,1fr); gap:10px; align-items:start; }
    .lineage-step { display:flex; width:26px; height:26px; align-items:center; justify-content:center; border:1px solid #afc0cb; border-radius:50%; color:var(--blue-dark); font-size:12px; font-weight:750; }
    .lineage-copy strong { display:block; color:var(--text); font-size:13px; }
    .lineage-copy span { display:block; margin-top:2px; color:var(--muted); font-size:12px; line-height:1.5; }
    @media (max-width:760px) { .drilldown-head { display:block; } .drilldown-cutoff { margin-top:12px; justify-items:start; } .drilldown-summary { grid-template-columns:1fr; gap:16px; } .plain-explanation { padding:15px 0 0; border-top:1px solid var(--line); border-left:0; } .drilldown-section-head { display:block; } .comparison-picker { margin-top:12px; } .comparison-picker select { width:100%; min-height:44px; } .comparison-values { grid-template-columns:1fr; } .comparison-values > div { border-right:0; border-bottom:1px solid var(--line); } .comparison-values > div:last-child { border-bottom:0; } .drilldown-section { padding:15px; } .drilldown-head p,.plain-explanation p,.drilldown-section-head p,.drilldown-table,.drilldown-empty,.comparison-feedback,.professional-content p,.lineage-copy strong,.lineage-copy span,.back-link { font-size:14px; } }
    @media (pointer:coarse) { .back-link,.professional-evidence summary,.comparison-picker select { min-height:44px; } }
    @media (prefers-reduced-motion:reduce) { .drilldown-view * { scroll-behavior:auto!important; transition:none!important; animation:none!important; } }
    '''
    script = '''
  <script>
  (() => {
    'use strict';
    const paths=__PATHS__; const metricsBySlug=__SLUGS__; const allowedKinds=__KINDS__; const allowedDataStates=__DATA_STATES__; const allowedLineageStates=__LINEAGE_STATES__; const allowedComparisonStates=__COMPARISON_STATES__;
    const view=document.querySelector('#drilldown-view'); const feedback=document.querySelector('#drilldown-feedback'); const body=document.querySelector('#drilldown-body'); const empty=document.querySelector('#drilldown-empty'); const comparisonKind=document.querySelector('#comparison-kind'); const comparisonFeedback=document.querySelector('#comparison-feedback'); const professional=document.querySelector('#professional-evidence'); const lineageList=document.querySelector('#lineage-list');
    let dataState='complete'; let lineageState='complete'; let comparisonState='exact'; let lastSnapshot=null; let requestSequence=0;
    const metricFromPath=()=>{ const prefix='/overview/detail/'; return location.pathname.startsWith(prefix)?metricsBySlug[location.pathname.slice(prefix.length)]||null:null; };
    const isDetail=()=>Boolean(metricFromPath());
    const text=(tag,value,className='')=>{ const node=document.createElement(tag); node.textContent=value==null?'':String(value); if(className)node.className=className; return node; };
    const identity=()=>window.KMFA_ROLE_TEST.identity(); const context=()=>window.KMFA_TEST.context();
    const contextQuery=()=>{ const scope=context(); return new URLSearchParams({company:scope.company,period:scope.period,project_status:scope.project_status,report_version:scope.report_version}).toString(); };
    const show=()=>{ view.hidden=false; document.body.dataset.drilldownActive='true'; };
    const hide=()=>{ view.hidden=true; delete document.body.dataset.drilldownActive; };
    const setFeedback=(message,state='')=>{ feedback.textContent=message; if(state)feedback.dataset.state=state; else delete feedback.dataset.state; };
    const renderRows=payload=>{ body.replaceChildren(); empty.hidden=true; if(!payload.detail_available){ empty.textContent=payload.explanation.block_reason_zh||payload.metric.missing_reason_zh||'当前资料不完整，暂时不能查看明细。'; empty.hidden=false; return; } payload.detail_rows.forEach(row=>{ const tr=document.createElement('tr'); [row.label_zh,row.primary_display_zh,row.secondary_display_zh||'—',row.status_zh,row.source_zh].forEach((value,index)=>{ const td=text('td',value,index===4?'drilldown-source':''); tr.append(td); }); body.append(tr); }); };
    const renderLineage=payload=>{ lineageList.replaceChildren(); document.querySelector('#drilldown-formula').textContent=payload.explanation.formula_zh; payload.explanation.professional_lineage_nodes.forEach(row=>{ const li=document.createElement('li'); li.className='lineage-row'; const step=text('span',row.step,'lineage-step'); const copy=text('div','', 'lineage-copy'); copy.append(text('strong',row.label_zh),text('span',row.detail_zh)); li.append(step,copy); lineageList.append(li); }); };
    const renderComparison=payload=>{ const value=payload.comparison; document.querySelector('#current-period-label').textContent=value.current_period_zh; document.querySelector('#comparison-period-label').textContent=value.comparison_period_zh; document.querySelector('#comparison-current').textContent=value.current_display_zh; document.querySelector('#comparison-previous').textContent=value.comparison_display_zh; document.querySelector('#comparison-delta').textContent=value.comparison_allowed?((value.delta_direction==='UP'?'+':value.delta_direction==='DOWN'?'−':'')+value.delta_display_zh+'（'+value.delta_rate_display_zh+'）'):'不可比较'; if(value.comparison_allowed){ comparisonFeedback.textContent='计算口径和数据范围一致，可以进行'+value.comparison_label_zh+'。'; delete comparisonFeedback.dataset.state; } else { comparisonFeedback.textContent=value.block_reason_zh; comparisonFeedback.dataset.state='blocked'; } };
    const render=payload=>{ lastSnapshot=payload; show(); document.querySelector('#drilldown-domain').textContent=payload.domain_zh+'明细'; document.querySelector('#drilldown-title').textContent=payload.detail_title_zh; document.querySelector('#drilldown-context').textContent=payload.context_labels.company+' · '+payload.context_labels.period+' · '+payload.context_labels.project_status+' · '+payload.context_labels.report_version; document.querySelector('#drilldown-cutoff').textContent=payload.as_of_date; document.querySelector('#drilldown-value').textContent=payload.metric.display_zh; document.querySelector('#drilldown-secondary').textContent=payload.metric.secondary_display_zh||''; document.querySelector('#drilldown-short-explanation').textContent=payload.explanation.short_explanation_zh; document.querySelector('#drilldown-row-count').textContent=payload.detail_row_count+' 项'; document.querySelector('#drilldown-consistency').textContent=payload.detail_available?'明细合计与首页数字一致。':'明细暂未形成，未显示未经支持的数字。'; setFeedback(payload.detail_available?'已核对：明细合计与首页数字一致。':(payload.explanation.block_reason_zh||payload.metric.missing_reason_zh),'blocked'); if(payload.detail_available)delete feedback.dataset.state; renderRows(payload); renderComparison(payload); renderLineage(payload); professional.open=false; };
    const renderDenied=payload=>{ lastSnapshot=payload; show(); document.querySelector('#drilldown-title').textContent='当前不能查看这项明细'; document.querySelector('#drilldown-context').textContent='已保留当前筛选，没有显示无权查看的内容。'; setFeedback(payload.reason_zh||'当前身份不能查看这项明细。','error'); body.replaceChildren(); empty.textContent='请返回经营首页，选择当前账号可以查看的公司。'; empty.hidden=false; comparisonFeedback.textContent='没有可比较的内容。'; comparisonFeedback.dataset.state='blocked'; lineageList.replaceChildren(); };
    const load=async()=>{ const metricId=metricFromPath(); if(!metricId){ hide(); return null; } show(); setFeedback('正在核对首页数字与明细…'); const sequence=++requestSequence; const who=identity(),scope=context(); const params=new URLSearchParams({metric_id:metricId,user_id:who.user_id,role_id:who.role_id,company:scope.company,period:scope.period,project_status:scope.project_status,report_version:scope.report_version,data_state:dataState,lineage_state:lineageState,comparison_kind:comparisonKind.value,comparison_state:comparisonState}); try { const response=await fetch('/api/drilldown?'+params); const payload=await response.json(); if(sequence!==requestSequence)return {stale_response_ignored:true}; if(!response.ok||!payload.allowed){ renderDenied(payload); return payload; } render(payload); return payload; } catch (_) { if(sequence===requestSequence)setFeedback('明细暂时无法读取，请返回首页后重试。','error'); return null; } };
    const go=(path)=>{ history.pushState({},'',path+'?'+contextQuery()); window.dispatchEvent(new PopStateEvent('popstate')); };
    document.addEventListener('click',event=>{ const summaryLink=event.target.closest('#homepage-metrics .summary-link'); if(summaryLink){ const metricId=summaryLink.closest('[data-metric-id]')?.dataset.metricId; if(metricId&&paths[metricId]){ event.preventDefault(); event.stopImmediatePropagation(); go(paths[metricId]); } return; } const back=event.target.closest('#drilldown-back'); if(back&&isDetail()){ event.preventDefault(); event.stopImmediatePropagation(); go('/overview'); } },true);
    comparisonKind.addEventListener('change',load); document.querySelector('#context-company').addEventListener('change',()=>setTimeout(load,0)); document.querySelector('#context-period').addEventListener('change',()=>setTimeout(load,0)); document.querySelector('#context-project_status').addEventListener('change',()=>setTimeout(load,0)); document.querySelector('#context-report_version').addEventListener('change',()=>setTimeout(load,0)); document.querySelector('#identity-user').addEventListener('change',()=>setTimeout(load,0)); window.addEventListener('popstate',()=>setTimeout(load,0));
    window.KMFA_DRILLDOWN_TEST={load,setDataState:value=>{ dataState=allowedDataStates.includes(value)?value:'complete'; return load(); },setLineageState:value=>{ lineageState=allowedLineageStates.includes(value)?value:'complete'; return load(); },setComparisonState:value=>{ comparisonState=allowedComparisonStates.includes(value)?value:'exact'; return load(); },setComparisonKind:value=>{ comparisonKind.value=allowedKinds.includes(value)?value:'MOM'; return load(); },snapshot:()=>lastSnapshot,isActive:isDetail};
    load();
  })();
  </script>
'''
    script = (
        script.replace("__PATHS__", _json_for_html({key: kernel.detail_path(key) for key in kernel.METRIC_SPECS}))
        .replace("__SLUGS__", _json_for_html(kernel.SLUG_METRICS))
        .replace("__KINDS__", _json_for_html(list(kernel.COMPARISON_KINDS)))
        .replace("__DATA_STATES__", _json_for_html(list(kernel.DATA_STATES)))
        .replace("__LINEAGE_STATES__", _json_for_html(list(kernel.LINEAGE_STATES)))
        .replace("__COMPARISON_STATES__", _json_for_html(list(kernel.COMPARISON_STATES)))
    )
    html = html.replace("<title>KMFA 经营首页 · 经营工作台</title>", "<title>KMFA 经营明细 · 经营工作台</title>")
    html = html.replace("  </style>", extra_css + "  </style>", 1)
    marker = '<section id="homepage-view" class="homepage-view" aria-labelledby="homepage-title" hidden>'
    if marker not in html:
        raise RuntimeError("S16-P1 runtime insertion point drifted")
    html = html.replace(marker, detail + "\n    " + marker, 1)
    html = html.replace("</body>", script + "</body>", 1)
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class DrilldownHandler(p1_runtime.HomepageHandler):
    server_version = "KMFADrilldown/1.5"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/api/drilldown":
            query = parse_qs(parsed.query)
            try:
                value = kernel.drilldown_snapshot(
                    metric_id=query.get("metric_id", ["AVAILABLE_CASH"])[0],
                    user_id=query.get("user_id", ["demo-owner"])[0],
                    role_id=query.get("role_id", ["management"])[0],
                    company=query.get("company", ["demo-north"])[0],
                    period=query.get("period", ["2026-07"])[0],
                    project_status=query.get("project_status", ["all"])[0],
                    report_version=query.get("report_version", ["latest"])[0],
                    data_state=query.get("data_state", ["complete"])[0],
                    lineage_state=query.get("lineage_state", ["complete"])[0],
                    comparison_kind=query.get("comparison_kind", ["MOM"])[0],
                    comparison_state=query.get("comparison_state", ["exact"])[0],
                )
            except kernel.DrilldownError as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error), "detail_rows": []})
                return
            self._send_json(HTTPStatus.OK if value["allowed"] else HTTPStatus.FORBIDDEN, value)
            return
        if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico":
            super().do_GET()
            return
        self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")


class DrilldownServer(p1_runtime.HomepageServer):
    pass


def start_server(host: str = "127.0.0.1", port: int = 0) -> tuple[DrilldownServer, threading.Thread, str]:
    server = DrilldownServer((host, port), DrilldownHandler)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s16p2-drilldown", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S16-P2 指标下钻与解释公开演示")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = DrilldownServer((args.host, args.port), DrilldownHandler)
    print(f"KMFA S16-P2 指标下钻：http://{args.host}:{server.server_address[1]}/overview", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
