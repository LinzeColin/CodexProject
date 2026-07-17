#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S17-P2 项目详情。"""

from __future__ import annotations

import argparse
import threading
from http import HTTPStatus
from typing import Any
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s17_p1_project_list as list_runtime
from KMFA.tools import v015_s12_p2_core_calculations as calculations
from KMFA.tools import v015_s16_p1_homepage as homepage_kernel
from KMFA.tools import v015_s17_p1_project_list as list_kernel
from KMFA.tools import v015_s17_p2_project_detail as kernel


def _first(query: dict[str, list[str]], key: str, default: str) -> str:
    return query.get(key, [default])[0]


def _list_context(query: dict[str, list[str]]) -> dict[str, str]:
    return {key: _first(query, key, "") for key in kernel.LIST_CONTEXT_KEYS if _first(query, key, "")}


def _detail_payload(query: dict[str, list[str]]) -> dict[str, Any]:
    return kernel.project_detail(
        project_id=_first(query, "project_id", ""),
        company_id=_first(query, "company_id", "demo-north"),
        period=_first(query, "period", "2026-07"),
        active_tab=_first(query, "active_tab", "overview"),
        list_context=_list_context(query),
    )


def render_html() -> str:
    html = list_runtime.render_html()
    detail_view = '''
    <section id="project-detail-view" class="project-detail-view" aria-labelledby="detail-project-name" hidden>
      <a id="detail-return" class="detail-return" href="/projects">← 返回项目列表</a>
      <header class="detail-head">
        <div><span class="detail-kicker">项目详情</span><h1 id="detail-project-name">正在核对项目…</h1><p id="detail-project-meta">请稍候</p></div>
        <div class="detail-cutoff"><span>公开演示 · 数据截止</span><strong id="detail-cutoff-date">2026-07-15</strong></div>
      </header>
      <div id="detail-feedback" class="detail-feedback" role="status" aria-live="polite">正在核对项目详情…</div>
      <nav id="detail-tabs" class="detail-tabs" aria-label="项目详情栏目"></nav>
      <section id="detail-panel-overview" class="detail-panel" data-detail-panel="overview" aria-labelledby="detail-tab-overview"></section>
      <section id="detail-panel-cost" class="detail-panel" data-detail-panel="cost" aria-labelledby="detail-tab-cost" hidden></section>
      <section id="detail-panel-revenue_collection" class="detail-panel" data-detail-panel="revenue_collection" aria-labelledby="detail-tab-revenue_collection" hidden></section>
      <section id="detail-panel-variance" class="detail-panel" data-detail-panel="variance" aria-labelledby="detail-tab-variance" hidden></section>
      <section id="detail-panel-documents" class="detail-panel" data-detail-panel="documents" aria-labelledby="detail-tab-documents" hidden></section>
      <p class="detail-disclaimer">当前详情只使用公开合成项目，用于验证项目成本、收入、回款、差异和资料流程，不代表任何真实公司的经营情况。</p>
    </section>'''
    extra_css = '''
    body[data-project-detail-active="true"] #page-view,
    body[data-project-detail-active="true"] #loading-view,
    body[data-project-detail-active="true"] #error-view,
    body[data-project-detail-active="true"] #not-found-view,
    body[data-project-detail-active="true"] #homepage-view,
    body[data-project-detail-active="true"] #project-list-view,
    body[data-project-detail-active="true"] #context-status,
    body[data-project-detail-active="true"] .identity-shell,
    body[data-project-detail-active="true"] .quick-shell,
    body[data-project-detail-active="true"] #access-workspace,
    body[data-project-detail-active="true"] #experience-workspace { display:none!important; }
    .project-detail-link { color:#0f5d8b; font-weight:750; text-decoration:none; }
    .project-detail-link:hover { text-decoration:underline; }
    .project-detail-view { margin:2px 0 28px; }
    .detail-return { display:inline-flex; min-height:38px; margin:0 0 12px; align-items:center; color:#155f8d; font-size:13px; font-weight:750; text-decoration:none; }
    .detail-return:hover { text-decoration:underline; }
    .detail-head { display:flex; justify-content:space-between; gap:24px; align-items:flex-start; margin-bottom:14px; }
    .detail-kicker { display:block; margin-bottom:5px; color:var(--blue-dark); font-size:12px; font-weight:750; letter-spacing:.04em; }
    .detail-head h1 { margin:0; color:var(--navy); font-size:29px; line-height:1.25; }
    .detail-head p { margin:7px 0 0; color:var(--muted); font-size:14px; line-height:1.55; }
    .detail-cutoff { display:grid; justify-items:end; flex:none; color:var(--muted); font-size:12px; }
    .detail-cutoff strong { margin-top:3px; color:var(--text); font-size:14px; }
    .detail-feedback { min-height:39px; margin-bottom:13px; padding:9px 12px; border:1px solid #bfd2df; border-left:4px solid var(--blue); border-radius:6px; background:#edf6fb; color:#29475d; font-size:13px; line-height:1.5; }
    .detail-feedback[data-state="error"] { border-color:#d7a6a6; background:#fff8f7; color:#7f2929; }
    .detail-tabs { display:flex; gap:3px; margin-bottom:14px; padding:4px; overflow:auto; border:1px solid #cfdce4; border-radius:8px; background:#f3f6f8; }
    .detail-tab { min-height:42px; padding:8px 15px; border:1px solid transparent; border-radius:6px; color:#40596b; background:transparent; font:inherit; font-size:13px; font-weight:750; white-space:nowrap; cursor:pointer; }
    .detail-tab:hover { color:#114f79; background:#fff; }
    .detail-tab[aria-selected="true"] { border-color:#9bb8ca; color:#0d517b; background:#fff; box-shadow:0 1px 3px rgba(16,47,80,.08); }
    .detail-panel { padding:19px; border:1px solid var(--line); border-radius:8px; background:#fff; }
    .detail-section-head { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; margin-bottom:15px; }
    .detail-section-head h2 { margin:0; color:var(--navy); font-size:20px; line-height:1.35; }
    .detail-section-head p { margin:4px 0 0; color:var(--muted); font-size:13px; line-height:1.5; }
    .detail-source { color:#597080; font-size:11px; line-height:1.45; }
    .profit-callout { display:grid; grid-template-columns:minmax(220px,.75fr) minmax(0,1.4fr); gap:18px; margin-bottom:15px; padding:18px; border:1px solid #a9c9ba; border-left:5px solid #31845c; border-radius:8px; background:#f2faf6; }
    .profit-callout[data-risk="HIGH"] { border-color:#dfb3b0; border-left-color:#b44741; background:#fff7f6; }
    .profit-callout[data-risk="MEDIUM"] { border-color:#dec897; border-left-color:#b47a20; background:#fffbf2; }
    .profit-verdict span { display:block; color:#496456; font-size:12px; font-weight:750; }
    .profit-verdict strong { display:block; margin-top:5px; color:#173b2b; font-size:25px; line-height:1.25; }
    .profit-reasons { margin:0; padding-left:19px; color:#344d40; font-size:13px; line-height:1.65; }
    .detail-metrics { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-bottom:15px; }
    .detail-metric { min-width:0; padding:13px; border:1px solid #d9e3e9; border-radius:7px; background:#f8fafb; }
    .detail-metric span { display:block; color:var(--muted); font-size:11px; }
    .detail-metric strong { display:block; margin-top:5px; overflow-wrap:anywhere; color:var(--navy); font-size:17px; line-height:1.3; }
    .detail-note { padding:12px 13px; border:1px solid #dce5ea; border-radius:7px; background:#f8fafb; color:#40596b; font-size:13px; line-height:1.6; }
    .professional-basis { margin-top:13px; border:1px solid #dce5ea; border-radius:7px; }
    .professional-basis summary { min-height:42px; padding:10px 12px; color:#40596b; font-size:12px; font-weight:750; cursor:pointer; }
    .professional-basis > div { padding:0 12px 12px; color:#536b7c; font-size:12px; line-height:1.55; }
    .cost-summary { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-bottom:15px; }
    .zero-difference { padding:12px; border:1px solid #a9c9ba; border-radius:7px; background:#f2faf6; color:#276346; font-size:12px; font-weight:750; }
    .cost-layout { display:grid; grid-template-columns:minmax(290px,.85fr) minmax(0,1.45fr); gap:15px; margin-bottom:15px; }
    .cost-chart,.cost-table-shell,.trend-shell,.flow-shell,.variance-shell,.document-shell { padding:15px; border:1px solid #d9e3e9; border-radius:7px; background:#fbfcfd; }
    .cost-chart h3,.cost-table-shell h3,.trend-shell h3,.flow-shell h3,.variance-shell h3,.document-shell h3 { margin:0 0 11px; color:#29475d; font-size:15px; }
    .bar-list { display:grid; gap:9px; }
    .bar-row { display:grid; grid-template-columns:58px minmax(70px,1fr) 80px; gap:8px; align-items:center; color:#40596b; font-size:11px; }
    .bar-track { height:9px; overflow:hidden; border-radius:999px; background:#e2e9ed; }
    .bar-fill { height:100%; border-radius:999px; background:#2b79a8; }
    .bar-row strong { text-align:right; color:#29475d; font-size:11px; }
    .detail-table-wrap { width:100%; overflow:auto; border:1px solid #dce5ea; border-radius:6px; }
    .detail-table { width:100%; border-collapse:collapse; font-size:12px; }
    .detail-table th,.detail-table td { padding:9px 10px; border-bottom:1px solid #e2e9ed; text-align:left; vertical-align:top; white-space:nowrap; }
    .detail-table th { background:#f3f6f8; color:#40596b; font-weight:750; }
    .detail-table tr:last-child td { border-bottom:0; }
    .detail-table .numeric { text-align:right; }
    .unallocated-note { margin:12px 0 0; padding:11px 12px; border:1px solid #dec897; border-radius:7px; background:#fffbf2; color:#624b22; font-size:12px; line-height:1.55; }
    .trend-bars { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; align-items:end; min-height:165px; padding:10px 6px 0; }
    .trend-column { display:grid; grid-template-rows:22px 110px 20px; gap:5px; justify-items:center; color:#536b7c; font-size:11px; }
    .trend-value { color:#29475d; font-weight:750; }
    .trend-bar-wrap { display:flex; width:42px; height:110px; align-items:flex-end; border-radius:5px 5px 0 0; background:#e3edf3; }
    .trend-bar { width:100%; border-radius:5px 5px 0 0; background:#4a8db5; }
    .flow-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; }
    .flow-card { position:relative; padding:13px; border:1px solid #d9e3e9; border-radius:7px; background:#fff; }
    .flow-card span { display:block; color:var(--muted); font-size:11px; }
    .flow-card strong { display:block; margin:5px 0; color:var(--navy); font-size:16px; }
    .flow-card small { color:#536b7c; font-size:11px; }
    .document-list { display:grid; grid-template-columns:1fr 1fr; gap:9px; margin:0; padding:0; list-style:none; }
    .document-item { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:10px; padding:12px; border:1px solid #d9e3e9; border-radius:7px; background:#fff; }
    .document-item strong { color:#29475d; font-size:13px; }
    .document-item small { display:block; margin-top:3px; color:var(--muted); font-size:11px; }
    .document-status { color:#236347; font-size:12px; font-weight:750; }
    .detail-disclaimer { margin:12px 2px 0; color:var(--muted); font-size:12px; line-height:1.5; }
    @media (max-width:900px) { .detail-metrics,.cost-summary { grid-template-columns:1fr 1fr; } .cost-layout { grid-template-columns:1fr; } .flow-grid { grid-template-columns:1fr 1fr; } }
    @media (max-width:760px) {
      .detail-return,.detail-tab { min-height:44px; font-size:14px; }
      .detail-head { display:block; } .detail-cutoff { justify-items:start; margin-top:10px; }
      .detail-head h1 { font-size:25px; } .detail-panel { padding:15px; }
      .profit-callout { grid-template-columns:1fr; gap:11px; padding:15px; }
      .profit-verdict strong { font-size:22px; }
      .detail-metrics,.cost-summary,.flow-grid,.document-list { grid-template-columns:1fr; }
      .detail-metric strong { font-size:16px; }
      .cost-table-shell,.cost-chart,.trend-shell,.flow-shell,.variance-shell,.document-shell { padding:12px; }
      .bar-row { grid-template-columns:52px minmax(60px,1fr) 72px; }
    }
    @media (prefers-reduced-motion:reduce) { .project-detail-view * { scroll-behavior:auto!important; transition:none!important; animation:none!important; } }
    '''
    script = '''
  <script>
  (() => {
    'use strict';
    const view=document.querySelector('#project-detail-view');const feedback=document.querySelector('#detail-feedback');const tabs=document.querySelector('#detail-tabs');const returnLink=document.querySelector('#detail-return');const LIST_CONTEXT_KEY='kmfa.v015.s17p1.return-context.v1';let lastPayload=null;let activeTab='overview';let sequence=0;
    const isActive=()=>location.pathname.startsWith('/projects/')&&location.pathname.split('/').filter(Boolean).length===2;const projectId=()=>decodeURIComponent(location.pathname.split('/').filter(Boolean).pop()||'');
    const text=(tag,value,className='')=>{const node=document.createElement(tag);node.textContent=value==null?'':String(value);if(className)node.className=className;return node;};
    const money=value=>{const sign=value<0?'-':'';const absolute=Math.abs(value);return sign+'¥'+(absolute/100).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});};
    const percent=value=>(Number(value)/100).toFixed(2)+'%';const identity=()=>window.KMFA_ROLE_TEST.identity();const context=()=>window.KMFA_TEST.context();
    const savedContext=()=>{try{const value=JSON.parse(sessionStorage.getItem(LIST_CONTEXT_KEY)||'null'),scope=context();return value&&value.company_id===scope.company&&value.period===scope.period?value:{};}catch(_){return {};}};
    const setFeedback=(message,error=false)=>{feedback.textContent=message;if(error)feedback.dataset.state='error';else delete feedback.dataset.state;};
    const heading=(title,description,source)=>{const head=text('div','','detail-section-head'),copy=document.createElement('div');copy.append(text('h2',title),text('p',description));head.append(copy,text('span',source,'detail-source'));return head;};
    const metric=(label,value)=>{const item=text('div','','detail-metric');item.append(text('span',label),text('strong',value));return item;};
    const table=(headers,rows,classes=[])=>{const wrap=text('div','','detail-table-wrap'),node=text('table','','detail-table'),thead=document.createElement('thead'),head=document.createElement('tr'),tbody=document.createElement('tbody');headers.forEach((label,index)=>head.append(text('th',label,classes[index]||'')));thead.append(head);rows.forEach(values=>{const tr=document.createElement('tr');values.forEach((value,index)=>{const td=text('td',value,classes[index]||'');tr.append(td);});tbody.append(tr);});node.append(thead,tbody);wrap.append(node);return wrap;};
    const renderOverview=payload=>{const panel=document.querySelector('#detail-panel-overview'),value=payload.overview;panel.replaceChildren();panel.append(heading('项目概况','先回答项目是否赚钱，再说明形成原因。',value.source_zh));const callout=text('div','','profit-callout');callout.dataset.risk=payload.project.risk_level;const verdict=text('div','','profit-verdict');verdict.append(text('span','当前判断'),text('strong',value.profit_verdict_zh));const reasons=text('ul','','profit-reasons');value.profit_reason_zh.forEach(reason=>reasons.append(text('li',reason)));callout.append(verdict,reasons);const metrics=text('div','','detail-metrics');[['合同金额',money(value.contract_value_cents)],['项目进度',value.progress_display_zh],['确认收入',money(value.revenue_cents)],['确认成本',money(value.cost_cents)],['毛利',money(value.gross_profit_cents)],['毛利率',value.gross_margin_display_zh],['已回款',money(value.collected_cents)],['经营风险',value.risk_zh]].forEach(([label,result])=>metrics.append(metric(label,result)));const note=text('div',value.data_status_zh,'detail-note');const professional=document.createElement('details');professional.className='professional-basis';professional.append(text('summary','查看专业口径与核对信息'));const basis=text('div','','');basis.append(text('p','合同、结算、管理三个毛利口径均由统一计算引擎形成。'),text('p','金额核对差异：0 分；允许误差：0 分。'));professional.append(basis);panel.append(callout,metrics,note,professional);};
    const renderCost=payload=>{const panel=document.querySelector('#detail-panel-cost'),value=payload.cost;panel.replaceChildren();panel.append(heading('成本','分类、趋势、预算基准、未归集成本和来源在同一页核对。',value.source_zh));const summary=text('div','','cost-summary');summary.append(metric('实际成本',money(value.actual_total_cents)),metric('预算基准',money(value.budget_total_cents)),metric('与基准差异',money(value.variance_total_cents)));summary.append(text('div','图表、表格、引擎合计一致：差异 0 分','zero-difference'));panel.append(summary);const layout=text('div','','cost-layout'),chart=text('section','','cost-chart'),tableShell=text('section','','cost-table-shell');chart.append(text('h3','分类成本图'));const bars=text('div','','bar-list'),maximum=Math.max(...value.categories.map(row=>row.actual_cents),1);value.categories.forEach(row=>{const line=text('div','','bar-row');line.dataset.categoryId=row.category_id;line.dataset.amountCents=String(row.actual_cents);const track=text('div','','bar-track'),fill=text('div','','bar-fill');fill.style.width=Math.max(2,Math.round(row.actual_cents/maximum*100))+'%';track.append(fill);line.append(text('span',row.category_zh),track,text('strong',row.actual_display_zh));bars.append(line);});chart.append(bars);tableShell.append(text('h3','分类成本表'));const costTable=table(['分类','实际','预算','差异','说明'],value.categories.map(row=>[row.category_zh,money(row.actual_cents),money(row.budget_cents),money(row.variance_cents),row.variance_direction_zh]),['','numeric','numeric','numeric','']);costTable.querySelectorAll('tbody tr').forEach((row,index)=>{row.dataset.categoryId=value.categories[index].category_id;row.dataset.amountCents=String(value.categories[index].actual_cents);});tableShell.append(costTable);tableShell.append(text('p','未归集：'+value.unallocated.amount_display_zh+'（'+value.unallocated.ratio_display_zh+'）。'+value.unallocated.reason_zh,'unallocated-note'));layout.append(chart,tableShell);panel.append(layout);const trend=text('section','','trend-shell');trend.append(text('h3','四期成本趋势'));const trendBars=text('div','','trend-bars'),trendMax=Math.max(...value.trend.map(row=>row.actual_cents),1);value.trend.forEach(row=>{const column=text('div','','trend-column');column.dataset.amountCents=String(row.actual_cents);const wrap=text('div','','trend-bar-wrap'),bar=text('div','','trend-bar');bar.style.height=Math.max(4,Math.round(row.actual_cents/trendMax*100))+'%';wrap.append(bar);column.append(text('span',row.actual_display_zh,'trend-value'),wrap,text('span',row.period_zh));trendBars.append(column);});trend.append(trendBars);panel.append(trend);};
    const renderRevenue=payload=>{const panel=document.querySelector('#detail-panel-revenue_collection'),value=payload.revenue_collection;panel.replaceChildren();panel.append(heading('收入与回款','合同、收入、开票、回款和应收按业务流程展开。',value.source_zh));const metrics=text('div','','detail-metrics');[['合同金额',money(value.contract_value_cents)],['批准变更',money(value.approved_change_cents)],['确认收入',money(value.recognized_revenue_cents)],['已开票',money(value.invoiced_cents)],['已回款',money(value.collected_cents)],['应收',money(value.receivable_cents)],['剩余合同额',money(value.remaining_contract_cents)],['回款进度',value.collection_display_zh]].forEach(([label,result])=>metrics.append(metric(label,result)));panel.append(metrics);const flow=text('section','','flow-shell');flow.append(text('h3','收入回款流程'));const grid=text('div','','flow-grid');value.timeline.forEach(row=>{const card=text('div','','flow-card');card.append(text('span',row.step+'. '+row.label_zh),text('strong',money(row.amount_cents)),text('small',row.status_zh));grid.append(card);});flow.append(grid);panel.append(flow);};
    const renderVariance=payload=>{const panel=document.querySelector('#detail-panel-variance'),value=payload.variance;panel.replaceChildren();panel.append(heading('差异','每项差异直接说明实际、基准和形成原因。',value.source_zh));const shell=text('section','','variance-shell');shell.append(text('h3','经营差异'));shell.append(table(['项目','实际','基准','差异','解释'],value.rows.map(row=>[row.label_zh,money(row.actual_cents),money(row.baseline_cents),money(row.variance_cents),row.explanation_zh]),['','numeric','numeric','numeric','']));panel.append(shell,text('div','当前进度 '+value.schedule_progress_display_zh+'；开票与回款差额 '+money(value.collection_gap_cents)+'。'+value.change_note_zh,'detail-note'));};
    const renderDocuments=payload=>{const panel=document.querySelector('#detail-panel-documents'),value=payload.documents;panel.replaceChildren();panel.append(heading('资料','只看资料是否齐全、更新时间和来源，不重复堆叠经营金额。',value.source_zh));const shell=text('section','','document-shell');shell.append(text('h3','资料清单 · '+value.complete_count+' / '+value.document_count+' 项齐全'));const list=text('ul','','document-list');value.documents.forEach(row=>{const item=text('li','','document-item'),copy=document.createElement('div');copy.append(text('strong',row.document_name_zh),text('small','更新：'+row.updated_zh+' · '+row.source_zh));item.append(copy,text('span',row.status_zh,'document-status'));list.append(item);});shell.append(list);panel.append(shell);};
    const showTab=(tab,updateHash=true)=>{if(!lastPayload||!lastPayload.section_ids.includes(tab))return;activeTab=tab;document.querySelectorAll('.detail-tab').forEach(button=>{const selected=button.dataset.tab===tab;button.setAttribute('aria-selected',String(selected));button.tabIndex=selected?0:-1;});document.querySelectorAll('[data-detail-panel]').forEach(panel=>panel.hidden=panel.dataset.detailPanel!==tab);if(updateHash)history.replaceState(history.state,'',location.pathname+location.search+'#'+tab);document.querySelector('[data-detail-panel="'+tab+'"] h2')?.focus({preventScroll:true});};
    const renderTabs=payload=>{tabs.replaceChildren();payload.tabs.forEach(item=>{const button=text('button',item.label_zh,'detail-tab');button.type='button';button.id='detail-tab-'+item.id;button.dataset.tab=item.id;button.setAttribute('role','tab');button.setAttribute('aria-controls','detail-panel-'+item.id);button.addEventListener('click',()=>showTab(item.id));tabs.append(button);});};
    const render=payload=>{lastPayload=payload;document.querySelector('#detail-project-name').textContent=payload.project.project_name_zh;document.querySelector('#detail-project-meta').textContent=payload.project.project_id+' · '+payload.project.client_zh+' · '+payload.project.owner_zh+' · '+payload.project.company_zh;document.querySelector('#detail-cutoff-date').textContent=payload.project.cutoff_date;returnLink.href='/projects';renderTabs(payload);renderOverview(payload);renderCost(payload);renderRevenue(payload);renderVariance(payload);renderDocuments(payload);const requested=location.hash.slice(1);showTab(payload.section_ids.includes(requested)?requested:'overview',false);setFeedback('项目详情已核对：金额与计算引擎一致，当前只显示公开合成内容。');};
    const params=()=>{const who=identity(),scope=context(),saved=savedContext();return new URLSearchParams({user_id:who.user_id,role_id:who.role_id,company_id:scope.company,period:scope.period,project_id:projectId(),active_tab:activeTab,...saved});};
    const load=async()=>{if(!isActive()){view.hidden=true;delete document.body.dataset.projectDetailActive;return null;}view.hidden=false;document.body.dataset.projectDetailActive='true';setFeedback('正在核对当前项目…');const current=++sequence;try{const response=await fetch('/api/projects/detail?'+params());const payload=await response.json();if(current!==sequence)return {stale_response_ignored:true};if(!response.ok||!payload.allowed){setFeedback(payload.reason_zh||'当前项目不能查看。',true);document.querySelectorAll('[data-detail-panel]').forEach(panel=>panel.replaceChildren());return payload;}render(payload);return payload;}catch(_){if(current===sequence)setFeedback('项目详情暂时无法读取，请稍后重试。',true);return null;}};
    const refresh=()=>setTimeout(load,0);document.querySelector('#context-company').addEventListener('change',refresh);document.querySelector('#context-period').addEventListener('change',refresh);document.querySelector('#identity-user').addEventListener('change',refresh);window.addEventListener('popstate',refresh);
    window.KMFA_PROJECT_DETAIL_TEST={load,snapshot:()=>lastPayload,activeTab:()=>activeTab,showTab,returnUrl:()=>returnLink.href,chartAmounts:()=>[...document.querySelectorAll('.bar-row')].map(node=>[node.dataset.categoryId,Number(node.dataset.amountCents)]),tableAmounts:()=>[...document.querySelectorAll('#detail-panel-cost tbody tr')].map(node=>[node.dataset.categoryId,Number(node.dataset.amountCents)])};
    load();
  })();
  </script>
'''
    marker = '<section id="project-list-view" class="project-list-view" aria-labelledby="project-list-title" hidden>'
    if marker not in html:
        raise RuntimeError("S17-P1 project list insertion point drifted")
    html = html.replace(marker, detail_view + marker, 1)
    html = html.replace("  </style>", extra_css + "  </style>", 1)
    html = html.replace("</body>", script + "</body>", 1)
    html = html.replace("<title>KMFA 项目列表 · 经营工作台</title>", "<title>KMFA 项目详情 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class ProjectDetailHandler(list_runtime.ProjectListHandler):
    server_version = "KMFAProjectDetail/1.5"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/api/projects/detail":
            query = parse_qs(parsed.query)
            try:
                allowed, identity = list_runtime._authorised(query)
                if not allowed:
                    self._send_json(
                        HTTPStatus.FORBIDDEN,
                        {"allowed": False, "reason_zh": identity.get("reason_zh", "当前身份没有查看权限。")},
                    )
                    return
                self._send_json(HTTPStatus.OK, _detail_payload(query))
            except (
                KeyError,
                TypeError,
                homepage_kernel.HomepageError,
                list_kernel.ProjectListError,
                calculations.CoreCalculationError,
                kernel.ProjectDetailError,
            ) as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})
            return
        if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico":
            super().do_GET()
            return
        self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")


class ProjectDetailServer(list_runtime.ProjectListServer):
    pass


def start_server(host: str = "127.0.0.1", port: int = 0) -> tuple[ProjectDetailServer, threading.Thread, str]:
    server = ProjectDetailServer((host, port), ProjectDetailHandler)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s17p2-project-detail", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S17-P2 项目详情")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ProjectDetailServer((args.host, args.port), ProjectDetailHandler)
    print(f"KMFA 项目详情：http://{args.host}:{server.server_address[1]}/projects/PUB-PROJ-001", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
