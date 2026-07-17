#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S17-P1 项目列表。"""

from __future__ import annotations

import argparse
import json
import threading
from http import HTTPStatus
from typing import Any, Mapping, Sequence
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s16_p3_homepage_usability as base_runtime
from KMFA.tools import v015_s16_p1_homepage as homepage_kernel
from KMFA.tools import v015_s17_p1_project_list as kernel


def _first(query: dict[str, list[str]], key: str, default: str) -> str:
    return query.get(key, [default])[0]


def _int_query(query: dict[str, list[str]], key: str, default: int) -> int:
    try:
        return int(_first(query, key, str(default)))
    except ValueError as error:
        raise kernel.ProjectListError(f"{key} must be an integer") from error


def _authorised(query: dict[str, list[str]]) -> tuple[bool, dict[str, Any]]:
    value = homepage_kernel.homepage_snapshot(
        user_id=_first(query, "user_id", "demo-owner"),
        role_id=_first(query, "role_id", "management"),
        company_id=_first(query, "company_id", "demo-north"),
        period=_first(query, "period", "2026-07"),
    )
    return bool(value.get("allowed")), value


def _list_payload(
    query: dict[str, list[str]],
    *,
    catalog_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    columns_raw = _first(query, "columns", "")
    columns = [item for item in columns_raw.split(",") if item] if columns_raw else None
    return kernel.project_list(
        company_id=_first(query, "company_id", "demo-north"),
        period=_first(query, "period", "2026-07"),
        project_status=_first(query, "project_status", "all"),
        client=_first(query, "client", "all"),
        owner=_first(query, "owner", "all"),
        margin_band=_first(query, "margin_band", "all"),
        collection_band=_first(query, "collection_band", "all"),
        risk=_first(query, "risk", "all"),
        group_by=_first(query, "group_by", "none"),
        sort_by=_first(query, "sort_by", "risk"),
        page=_int_query(query, "page", 1),
        page_size=_int_query(query, "page_size", kernel.DEFAULT_PAGE_SIZE),
        columns=columns,
        catalog_rows=catalog_rows,
    )


def render_html() -> str:
    html = base_runtime.render_html()
    project_view = '''
    <section id="project-list-view" class="project-list-view" aria-labelledby="project-list-title" hidden>
      <header class="project-list-head">
        <div><span class="project-kicker">项目管理</span><h1 id="project-list-title">项目列表</h1><p>按客户、负责人、毛利、回款和风险找到项目；排序依据直接写在页面上。</p></div>
        <div class="project-cutoff"><span>公开演示 · 数据截止</span><strong>2026-07-15</strong></div>
      </header>
      <div id="project-feedback" class="project-feedback" role="status" aria-live="polite">正在核对项目…</div>
      <section class="project-tools" aria-labelledby="project-filter-title">
        <div class="project-section-head"><div><h2 id="project-filter-title">筛选和排列</h2><p>公司、期间和项目状态使用上方全局筛选；这里继续缩小范围。</p></div><button id="project-reset" class="quiet-button" type="button">恢复默认</button></div>
        <div class="project-filter-grid">
          <label><span>客户</span><select id="project-client"><option value="all">全部客户</option></select></label>
          <label><span>负责人</span><select id="project-owner"><option value="all">全部负责人</option></select></label>
          <label><span>毛利率</span><select id="project-margin"><option value="all">全部毛利</option><option value="low">低于 22%</option><option value="medium">22% 至 27.99%</option><option value="high">28% 及以上</option></select></label>
          <label><span>回款进度</span><select id="project-collection"><option value="all">全部回款</option><option value="low">低于 80%</option><option value="medium">80% 至 92.99%</option><option value="high">93% 及以上</option></select></label>
          <label><span>风险</span><select id="project-risk"><option value="all">全部风险</option><option value="HIGH">高风险</option><option value="MEDIUM">需关注</option><option value="LOW">低风险</option></select></label>
          <label><span>分组</span><select id="project-group"><option value="none">不分组</option><option value="risk">按风险</option><option value="margin">按毛利率</option><option value="collection">按回款进度</option><option value="industry">按行业</option><option value="period">按项目期间</option></select></label>
          <label><span>排序</span><select id="project-sort"><option value="risk">风险最高优先</option><option value="margin">毛利率最低优先</option><option value="collection">回款最慢优先</option><option value="industry">按行业</option><option value="period">期间最新优先</option></select></label>
        </div>
        <div id="project-order-explanation" class="order-explanation"></div>
      </section>
      <section class="project-table-shell" aria-labelledby="project-table-title">
        <div class="project-section-head table-head-row">
          <div><h2 id="project-table-title">项目总表</h2><p id="project-result-summary">正在整理当前范围…</p></div>
          <details id="project-columns" class="column-picker"><summary>设置显示列</summary><fieldset><legend>选择表格列</legend><div id="project-column-options"></div></fieldset></details>
        </div>
        <div id="project-batch-bar" class="project-batch-bar" hidden><strong><span id="project-selected-count">0</span> 个项目已选</strong><span>只读操作，不会修改项目事实。</span><div><button id="project-compare" class="quiet-button" type="button">对比所选</button><button id="project-export" class="primary-action" type="button">导出附表</button><button id="project-clear" class="text-button" type="button">取消选择</button></div></div>
        <div class="project-table-wrap">
          <table id="project-table"><caption class="visually-hidden">公开演示项目总表</caption><thead><tr id="project-table-head"><th class="select-column"><span class="visually-hidden">选择</span></th></tr></thead><tbody id="project-table-body"></tbody></table>
        </div>
        <div id="project-mobile-list" class="project-mobile-list" aria-label="手机项目列表"></div>
        <nav class="project-pagination" aria-label="项目分页"><button id="project-prev" class="quiet-button" type="button">上一页</button><span id="project-page-label">第 1 / 1 页</span><button id="project-next" class="quiet-button" type="button">下一页</button></nav>
      </section>
      <section id="project-comparison" class="project-comparison" aria-labelledby="project-comparison-title" hidden>
        <div class="project-section-head"><div><span class="comparison-kicker">只读对比</span><h2 id="project-comparison-title">所选项目对比</h2><p>金额和比例直接来自上方项目事实，没有重新打分或改写。</p></div><button id="project-comparison-close" class="quiet-button" type="button">关闭对比</button></div>
        <div id="project-comparison-summary" class="comparison-summary"></div>
        <div class="project-table-wrap"><table class="comparison-table"><thead><tr><th>项目</th><th>收入</th><th>成本</th><th>毛利率</th><th>回款进度</th><th>风险</th><th>来源</th></tr></thead><tbody id="project-comparison-body"></tbody></table></div>
      </section>
      <p class="project-disclaimer">当前页面只使用公开合成项目，用于验证列表、对比和导出流程，不代表任何真实公司的经营情况。</p>
    </section>'''
    extra_css = '''
    body[data-project-list-active="true"] #page-view,
    body[data-project-list-active="true"] #loading-view,
    body[data-project-list-active="true"] #error-view,
    body[data-project-list-active="true"] #not-found-view,
    body[data-project-list-active="true"] #homepage-view,
    body[data-project-list-active="true"] #context-status,
    body[data-project-list-active="true"] .identity-shell,
    body[data-project-list-active="true"] .quick-shell,
    body[data-project-list-active="true"] #access-workspace,
    body[data-project-list-active="true"] #experience-workspace { display:none!important; }
    .project-list-view { margin-bottom:28px; }
    .project-list-head { display:flex; justify-content:space-between; gap:24px; align-items:flex-start; margin:5px 0 16px; }
    .project-kicker,.comparison-kicker { display:block; margin-bottom:5px; color:var(--blue-dark); font-size:12px; font-weight:750; letter-spacing:.04em; }
    .project-list-head h1 { margin:0; color:var(--navy); font-size:28px; line-height:1.25; }
    .project-list-head p { max-width:68ch; margin:7px 0 0; color:var(--muted); font-size:14px; line-height:1.6; }
    .project-cutoff { display:grid; justify-items:end; flex:none; color:var(--muted); font-size:12px; }
    .project-cutoff strong { margin-top:3px; color:var(--text); font-size:14px; }
    .project-feedback { min-height:39px; margin-bottom:14px; padding:9px 12px; border:1px solid #bfd2df; border-left:4px solid var(--blue); border-radius:6px; background:#edf6fb; color:#29475d; font-size:13px; line-height:1.5; }
    .project-feedback[data-state="error"] { border-color:#d7a6a6; background:#fff8f7; color:#7f2929; }
    .project-tools,.project-table-shell,.project-comparison { margin-bottom:16px; padding:17px 18px; border:1px solid var(--line); border-radius:8px; background:#fff; }
    .project-section-head { display:flex; justify-content:space-between; gap:18px; align-items:flex-start; margin-bottom:13px; }
    .project-section-head h2 { margin:0; color:var(--navy); font-size:18px; line-height:1.35; }
    .project-section-head p { margin:4px 0 0; color:var(--muted); font-size:13px; line-height:1.5; }
    .project-filter-grid { display:grid; grid-template-columns:repeat(4,minmax(145px,1fr)); gap:11px; }
    .project-filter-grid label span { display:block; margin-bottom:5px; color:#4e6271; font-size:12px; font-weight:700; }
    .order-explanation { margin-top:12px; padding:10px 12px; border:1px solid #dbe5eb; border-radius:6px; background:#f7f9fa; color:#40596b; font-size:12px; line-height:1.55; }
    .quiet-button,.primary-action,.text-button { min-height:38px; padding:7px 11px; border-radius:6px; font:inherit; font-size:13px; font-weight:700; cursor:pointer; }
    .quiet-button { border:1px solid #9fb3c1; background:#fff; color:#114f79; }
    .quiet-button:hover { border-color:var(--blue); background:#edf6fb; }
    .primary-action { border:1px solid var(--blue); background:var(--blue); color:#fff; }
    .primary-action:hover { background:var(--blue-dark); }
    .text-button { border:1px solid transparent; background:transparent; color:#40596b; }
    .text-button:hover { text-decoration:underline; }
    .column-picker { position:relative; flex:none; }
    .column-picker summary { min-height:38px; padding:8px 11px; border:1px solid #9fb3c1; border-radius:6px; color:#114f79; background:#fff; cursor:pointer; font-size:13px; font-weight:700; list-style:none; }
    .column-picker summary::-webkit-details-marker { display:none; }
    .column-picker fieldset { position:absolute; right:0; z-index:5; width:260px; margin:6px 0 0; padding:12px; border:1px solid #aebdc8; border-radius:7px; background:#fff; box-shadow:0 8px 22px rgba(16,47,80,.12); }
    .column-picker legend { padding:0 4px; color:var(--navy); font-size:13px; font-weight:750; }
    #project-column-options { display:grid; grid-template-columns:1fr 1fr; gap:5px 9px; }
    #project-column-options label { display:flex; min-height:34px; gap:7px; align-items:center; color:#334c5e; font-size:12px; }
    .project-batch-bar { display:flex; gap:13px; align-items:center; margin-bottom:12px; padding:10px 12px; border:1px solid #9ec1d8; border-radius:7px; background:#edf6fb; color:#29475d; font-size:12px; }
    .project-batch-bar strong { color:var(--navy); font-size:13px; }
    .project-batch-bar > span { flex:1; }
    .project-batch-bar > div { display:flex; gap:6px; }
    .project-table-wrap { width:100%; max-width:100%; overflow:auto; border:1px solid #dce5ea; border-radius:7px; }
    #project-table,.comparison-table { width:100%; border-collapse:collapse; font-size:12px; }
    #project-table th,#project-table td,.comparison-table th,.comparison-table td { padding:9px 10px; border-bottom:1px solid #e2e9ed; text-align:left; vertical-align:middle; white-space:nowrap; }
    #project-table th,.comparison-table th { position:sticky; top:0; z-index:1; background:#f3f6f8; color:#40596b; font-weight:750; }
    #project-table tbody tr:last-child td,.comparison-table tbody tr:last-child td { border-bottom:0; }
    #project-table tbody tr:hover { background:#f8fbfc; }
    .select-column { width:46px; text-align:center!important; }
    .row-select { width:18px; height:18px; accent-color:var(--blue); }
    .project-name-cell strong { display:block; color:var(--text); font-size:13px; }
    .project-name-cell small { display:block; margin-top:2px; color:var(--muted); font-size:11px; }
    .project-status,.project-risk { display:inline-flex; align-items:center; gap:5px; font-weight:700; }
    .project-status::before,.project-risk::before { content:'●'; font-size:9px; }
    .project-status[data-state="ATTENTION"],.project-risk[data-state="MEDIUM"] { color:#825811; }
    .project-status[data-state="NORMAL"],.project-risk[data-state="LOW"] { color:#236347; }
    .project-risk[data-state="HIGH"] { color:#982e2e; }
    .project-group-row th { position:static!important; padding:8px 10px!important; border-top:1px solid #b8cad6; background:#edf3f7!important; color:#29475d!important; font-size:12px; }
    .source-cell { max-width:230px; white-space:normal!important; color:#536b7c; line-height:1.4; }
    .project-pagination { display:flex; justify-content:flex-end; align-items:center; gap:11px; margin-top:12px; color:#526979; font-size:12px; }
    .project-pagination button:disabled { opacity:.45; cursor:not-allowed; }
    .project-mobile-list { display:none; }
    .comparison-summary { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); margin-bottom:12px; border:1px solid #dce5ea; border-radius:7px; overflow:hidden; }
    .comparison-summary div { padding:12px; border-right:1px solid #dce5ea; background:#f8fafb; }
    .comparison-summary div:last-child { border-right:0; }
    .comparison-summary span { display:block; color:var(--muted); font-size:11px; }
    .comparison-summary strong { display:block; margin-top:5px; color:var(--navy); font-size:17px; }
    .project-disclaimer { margin:3px 2px 0; color:var(--muted); font-size:12px; line-height:1.5; }
    @media (max-width:980px) { .project-filter-grid { grid-template-columns:repeat(3,minmax(140px,1fr)); } .project-batch-bar { align-items:flex-start; flex-wrap:wrap; } .project-batch-bar > span { min-width:45%; } }
    @media (max-width:760px) {
      .project-list-head { display:block; } .project-cutoff { justify-items:start; margin-top:10px; }
      .project-tools,.project-table-shell,.project-comparison { padding:15px; }
      .project-filter-grid { grid-template-columns:1fr 1fr; }
      .project-filter-grid select,.quiet-button,.primary-action,.text-button,.column-picker summary { min-height:44px; font-size:14px; }
      .table-head-row { align-items:flex-start; } .column-picker fieldset { position:fixed; top:18%; right:16px; left:16px; width:auto; }
      .project-table-wrap:has(#project-table) { display:none; }
      .project-mobile-list { display:grid; gap:10px; }
      .project-card { padding:13px; border:1px solid #d6e0e6; border-radius:7px; background:#fbfcfd; }
      .project-card-head { display:grid; grid-template-columns:28px minmax(0,1fr); gap:8px; align-items:start; }
      .project-card h3 { margin:0; color:var(--navy); font-size:15px; line-height:1.4; }
      .project-card-id { display:block; margin-top:2px; color:var(--muted); font-size:11px; }
      .project-card-grid { display:grid; grid-template-columns:1fr 1fr; gap:9px 12px; margin-top:11px; }
      .project-card-grid span { display:block; color:var(--muted); font-size:11px; }
      .project-card-grid strong { display:block; margin-top:2px; color:var(--text); font-size:13px; }
      .mobile-group-label { padding:7px 9px; border-left:3px solid #7da8c3; background:#edf3f7; color:#29475d; font-size:12px; font-weight:750; }
      .project-pagination { justify-content:space-between; }
      .project-batch-bar > div { width:100%; display:grid; grid-template-columns:1fr 1fr; }
      .project-batch-bar .text-button { grid-column:1/-1; }
      .comparison-summary { grid-template-columns:1fr 1fr; }
      .comparison-summary div:nth-child(2) { border-right:0; } .comparison-summary div:nth-child(n+3) { border-top:1px solid #dce5ea; }
    }
    @media (max-width:430px) { .project-filter-grid { grid-template-columns:1fr; } .project-section-head { gap:10px; } }
    @media (pointer:coarse) { .row-select { width:22px; height:22px; } }
    @media (prefers-reduced-motion:reduce) { .project-list-view * { scroll-behavior:auto!important; transition:none!important; animation:none!important; } }
    '''
    script = '''
  <script>
  (() => {
    'use strict';
    const view=document.querySelector('#project-list-view'); const feedback=document.querySelector('#project-feedback'); const tableHead=document.querySelector('#project-table-head'); const tableBody=document.querySelector('#project-table-body'); const mobileList=document.querySelector('#project-mobile-list'); const resultSummary=document.querySelector('#project-result-summary'); const explanation=document.querySelector('#project-order-explanation'); const batchBar=document.querySelector('#project-batch-bar'); const selectedCount=document.querySelector('#project-selected-count'); const comparison=document.querySelector('#project-comparison'); const comparisonBody=document.querySelector('#project-comparison-body'); const comparisonSummary=document.querySelector('#project-comparison-summary');
    const controls={client:document.querySelector('#project-client'),owner:document.querySelector('#project-owner'),margin_band:document.querySelector('#project-margin'),collection_band:document.querySelector('#project-collection'),risk:document.querySelector('#project-risk'),group_by:document.querySelector('#project-group'),sort_by:document.querySelector('#project-sort')};
    const state={client:'all',owner:'all',margin_band:'all',collection_band:'all',risk:'all',group_by:'none',sort_by:'risk',page:1,page_size:4,columns:['project','client','owner','status','margin','collection','risk']};
    const selected=new Set(); let lastPayload=null; let sequence=0; const LIST_CONTEXT_KEY='kmfa.v015.s17p1.return-context.v1';
    const labels={project:'项目',client:'客户',owner:'负责人',status:'状态',margin:'毛利率',collection:'回款进度',risk:'风险',revenue:'收入',cost:'成本',industry:'行业',period:'项目期间',source:'来源'};
    const isActive=()=>location.pathname==='/projects'; const text=(tag,value,className='')=>{const node=document.createElement(tag);node.textContent=value==null?'':String(value);if(className)node.className=className;return node;};
    const identity=()=>window.KMFA_ROLE_TEST.identity(); const context=()=>window.KMFA_TEST.context();
    const setFeedback=(message,error=false)=>{feedback.textContent=message;if(error)feedback.dataset.state='error';else delete feedback.dataset.state;};
    const money=value=>{const sign=value<0?'-':'';const absolute=Math.abs(value);return sign+'¥'+(absolute/100).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});};
    const percent=value=>(value/100).toFixed(2)+'%';
    const populate=(select,items,label)=>{const current=select.value||'all';select.replaceChildren(new Option(label,'all'));items.forEach(value=>select.append(new Option(value,value)));select.value=items.includes(current)?current:'all';};
    const saveColumns=()=>{try{localStorage.setItem('kmfa.v015.s17p1.columns.v1',JSON.stringify(state.columns));}catch(_){}};
    const restoreColumns=available=>{try{const value=JSON.parse(localStorage.getItem('kmfa.v015.s17p1.columns.v1')||'null');if(Array.isArray(value)&&value.length&&value.every(item=>available.includes(item)))state.columns=value;}catch(_){}};
    const saveListContext=()=>{try{const scope=context();sessionStorage.setItem(LIST_CONTEXT_KEY,JSON.stringify({company_id:scope.company,period:scope.period,project_status:scope.project_status,...state,columns:state.columns.join(',')}));}catch(_){}};
    const restoreListContext=()=>{try{const saved=JSON.parse(sessionStorage.getItem(LIST_CONTEXT_KEY)||'null'),scope=context();if(!saved||saved.company_id!==scope.company||saved.period!==scope.period)return;['client','owner','margin_band','collection_band','risk','group_by','sort_by'].forEach(key=>{if(typeof saved[key]==='string')state[key]=saved[key];});['page','page_size'].forEach(key=>{const value=Number(saved[key]);if(Number.isInteger(value)&&value>0)state[key]=value;});if(typeof saved.columns==='string'&&saved.columns)state.columns=saved.columns.split(',').filter(Boolean);}catch(_){}};
    const detailHref=row=>{const who=identity(),scope=context();const query=new URLSearchParams({user_id:who.user_id,role_id:who.role_id,company_id:scope.company,period:scope.period,project_status:scope.project_status,...state,columns:state.columns.join(',')});return row.route+'?'+query;};
    const projectLink=row=>{const link=text('a',row.project_name_zh,'project-detail-link');link.href=detailHref(row);link.addEventListener('click',saveListContext);return link;};
    const cell=(row,column)=>{if(column==='project'){const td=text('td','','project-name-cell');td.append(projectLink(row),text('small',row.project_id));return td;} if(column==='client')return text('td',row.client_zh);if(column==='owner')return text('td',row.owner_zh);if(column==='status'){const td=document.createElement('td'),tag=text('span',row.status_zh,'project-status');tag.dataset.state=row.status;td.append(tag);return td;}if(column==='margin')return text('td',row.gross_margin_display_zh);if(column==='collection')return text('td',row.collection_display_zh);if(column==='risk'){const td=document.createElement('td'),tag=text('span',row.risk_zh,'project-risk');tag.dataset.state=row.risk_level;tag.title=row.risk_reasons_zh.join('；');td.append(tag);return td;}if(column==='revenue')return text('td',row.revenue_display_zh);if(column==='cost')return text('td',row.cost_display_zh);if(column==='industry')return text('td',row.industry_zh);if(column==='period')return text('td',row.project_period);const td=text('td','来源：'+row.source_zh+'；截止：'+row.cutoff_date,'source-cell');td.title=row.source_ref;return td;};
    const checkbox=row=>{const input=document.createElement('input');input.type='checkbox';input.className='row-select';input.dataset.projectId=row.project_id;input.checked=selected.has(row.project_id);input.setAttribute('aria-label','选择 '+row.project_name_zh);return input;};
    const renderColumns=payload=>{const available=payload.available_columns.map(item=>item.id);restoreColumns(available);const options=document.querySelector('#project-column-options');options.replaceChildren();payload.available_columns.forEach(item=>{const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.value=item.id;input.checked=state.columns.includes(item.id);input.addEventListener('change',()=>{const next=[...options.querySelectorAll('input:checked')].map(node=>node.value);if(!next.length){input.checked=true;return;}state.columns=next;saveColumns();renderRows(lastPayload);});label.append(input,text('span',item.label_zh));options.append(label);});};
    const syncSelection=()=>{document.querySelectorAll('.row-select').forEach(input=>input.checked=selected.has(input.dataset.projectId));selectedCount.textContent=String(selected.size);batchBar.hidden=selected.size===0;document.querySelector('#project-compare').disabled=selected.size<2;document.querySelector('#project-export').disabled=selected.size<2;};
    const renderRows=payload=>{tableHead.replaceChildren(text('th','', 'select-column'));state.columns.forEach(column=>tableHead.append(text('th',labels[column])));tableBody.replaceChildren();mobileList.replaceChildren();let desktopGroup='',mobileGroup='';payload.rows.forEach(row=>{if(payload.group_by!=='none'&&row.group_id!==desktopGroup){desktopGroup=row.group_id;const tr=document.createElement('tr');tr.className='project-group-row';const th=text('th',row.group_label_zh);th.colSpan=state.columns.length+1;tr.append(th);tableBody.append(tr);}const tr=document.createElement('tr');tr.dataset.projectId=row.project_id;const selectCell=text('td','', 'select-column');selectCell.append(checkbox(row));tr.append(selectCell);state.columns.forEach(column=>tr.append(cell(row,column)));tableBody.append(tr);if(payload.group_by!=='none'&&row.group_id!==mobileGroup){mobileGroup=row.group_id;mobileList.append(text('div',row.group_label_zh,'mobile-group-label'));}const card=document.createElement('article');card.className='project-card';card.dataset.projectId=row.project_id;const head=text('div','', 'project-card-head');head.append(checkbox(row));const title=document.createElement('div'),heading=document.createElement('h3');heading.append(projectLink(row));title.append(heading,text('span',row.project_id,'project-card-id'));head.append(title);const grid=text('div','', 'project-card-grid');[['客户',row.client_zh],['负责人',row.owner_zh],['状态',row.status_zh],['风险',row.risk_zh],['毛利率',row.gross_margin_display_zh],['回款进度',row.collection_display_zh]].forEach(([label,value])=>{const item=document.createElement('div');item.append(text('span',label),text('strong',value));grid.append(item);});card.append(head,grid);mobileList.append(card);});syncSelection();};
    const render=payload=>{lastPayload=payload;state.page=payload.page;populate(controls.client,payload.filter_options.clients,'全部客户');populate(controls.owner,payload.filter_options.owners,'全部负责人');Object.entries(controls).forEach(([key,node])=>node.value=state[key]);renderColumns(payload);renderRows(payload);resultSummary.textContent='共 '+payload.filtered_count+' 个项目，本页 '+payload.visible_count+' 个；第 '+payload.page+' / '+payload.page_count+' 页。';explanation.textContent='分组：'+payload.group_explanation_zh+' 排序：'+payload.sort_explanation_zh;document.querySelector('#project-page-label').textContent='第 '+payload.page+' / '+payload.page_count+' 页';document.querySelector('#project-prev').disabled=payload.page<=1;document.querySelector('#project-next').disabled=payload.page>=payload.page_count;saveListContext();setFeedback('项目已核对：'+payload.source_note_zh);};
    const params=()=>{const who=identity(),scope=context();return new URLSearchParams({user_id:who.user_id,role_id:who.role_id,company_id:scope.company,period:scope.period,project_status:scope.project_status,...state,columns:state.columns.join(',')});};
    const load=async()=>{if(!isActive()){view.hidden=true;delete document.body.dataset.projectListActive;return null;}view.hidden=false;document.body.dataset.projectListActive='true';setFeedback('正在核对当前公司的项目…');const current=++sequence;try{const response=await fetch('/api/projects?'+params());const payload=await response.json();if(current!==sequence)return {stale_response_ignored:true};if(!response.ok||!payload.allowed){setFeedback(payload.reason_zh||'当前身份不能查看这些项目。',true);tableBody.replaceChildren();mobileList.replaceChildren();return payload;}render(payload);return payload;}catch(_){if(current===sequence)setFeedback('项目暂时无法读取，请稍后重试。',true);return null;}};
    const change=()=>{state.page=1;comparison.hidden=true;Object.entries(controls).forEach(([key,node])=>state[key]=node.value);load();};
    Object.values(controls).forEach(node=>node.addEventListener('change',change));
    document.querySelector('#project-reset').addEventListener('click',()=>{Object.assign(state,{client:'all',owner:'all',margin_band:'all',collection_band:'all',risk:'all',group_by:'none',sort_by:'risk',page:1,columns:['project','client','owner','status','margin','collection','risk']});Object.entries(controls).forEach(([key,node])=>node.value=state[key]);selected.clear();saveColumns();comparison.hidden=true;load();});
    document.querySelector('#project-prev').addEventListener('click',()=>{if(lastPayload&&state.page>1){state.page-=1;load();}});document.querySelector('#project-next').addEventListener('click',()=>{if(lastPayload&&state.page<lastPayload.page_count){state.page+=1;load();}});
    document.addEventListener('change',event=>{const input=event.target.closest('.row-select');if(!input)return;if(input.checked)selected.add(input.dataset.projectId);else selected.delete(input.dataset.projectId);syncSelection();});
    document.querySelector('#project-clear').addEventListener('click',()=>{selected.clear();comparison.hidden=true;syncSelection();});
    const selectedParams=()=>{const who=identity(),scope=context();return new URLSearchParams({user_id:who.user_id,role_id:who.role_id,company_id:scope.company,period:scope.period,project_ids:[...selected].join(',')});};
    const compare=async()=>{if(selected.size<2)return;setFeedback('正在生成只读对比…');const response=await fetch('/api/projects/compare?'+selectedParams());const payload=await response.json();if(!response.ok){setFeedback(payload.reason_zh||'无法生成项目对比。',true);return;}comparisonSummary.replaceChildren();[['项目数',payload.project_count+' 个'],['收入合计',money(payload.totals.revenue_cents)],['加权毛利率',payload.totals.weighted_margin_display_zh],['加权回款',payload.totals.weighted_collection_display_zh]].forEach(([label,value])=>{const item=document.createElement('div');item.append(text('span',label),text('strong',value));comparisonSummary.append(item);});comparisonBody.replaceChildren();payload.rows.forEach(row=>{const tr=document.createElement('tr');[row.project_name_zh,row.revenue_display_zh,row.cost_display_zh,row.gross_margin_display_zh,row.collection_display_zh,row.risk_zh,'来源：'+row.source_zh+'；截止：'+row.cutoff_date].forEach(value=>tr.append(text('td',value)));comparisonBody.append(tr);});comparison.hidden=false;comparison.scrollIntoView({block:'start'});setFeedback('只读对比已生成，没有修改项目事实。');return payload;};
    document.querySelector('#project-compare').addEventListener('click',compare);document.querySelector('#project-comparison-close').addEventListener('click',()=>comparison.hidden=true);
    document.querySelector('#project-export').addEventListener('click',async()=>{if(selected.size<2)return;const response=await fetch('/api/projects/export?'+selectedParams());if(!response.ok){const payload=await response.json();setFeedback(payload.reason_zh||'导出失败。',true);return;}const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='KMFA_项目对比附表.csv';document.body.append(link);link.click();link.remove();URL.revokeObjectURL(url);setFeedback('附表已导出；每行都包含来源说明和数据截止日。');});
    const refresh=()=>setTimeout(()=>{if(isActive()){selected.clear();comparison.hidden=true;state.page=1;}load();},0);document.querySelector('#context-company').addEventListener('change',refresh);document.querySelector('#context-period').addEventListener('change',refresh);document.querySelector('#context-project_status').addEventListener('change',refresh);document.querySelector('#identity-user').addEventListener('change',refresh);window.addEventListener('popstate',refresh);new MutationObserver(refresh).observe(document.querySelector('#page-title'),{childList:true,subtree:true});
    window.KMFA_PROJECT_LIST_TEST={load,snapshot:()=>lastPayload,state:()=>({...state}),selected:()=>[...selected],compare,saveListContext,detailUrl:id=>detailHref({project_id:id,route:'/projects/'+id}),select:ids=>{selected.clear();(ids||[]).forEach(id=>selected.add(id));syncSelection();}};
    restoreListContext();load();
  })();
  </script>
'''
    marker = '<div id="context-status" class="status-line" role="status" aria-live="polite"><span>正在准备演示内容…</span></div>'
    if marker not in html:
        raise RuntimeError("S15 application shell insertion point drifted")
    html = html.replace(marker, marker + project_view, 1)
    html = html.replace("  </style>", extra_css + "  </style>", 1)
    html = html.replace("</body>", script + "</body>", 1)
    html = html.replace("<title>KMFA 经营首页可用验收 · 经营工作台</title>", "<title>KMFA 项目列表 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class ProjectListHandler(base_runtime.HomepageUsabilityHandler):
    server_version = "KMFAProjectList/1.5"

    def _send_csv(self, content: str) -> None:
        body = content.encode("utf-8-sig")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="KMFA-projects.csv"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path in {"/api/projects", "/api/projects/compare", "/api/projects/export"}:
            query = parse_qs(parsed.query)
            try:
                allowed, identity = _authorised(query)
                if not allowed:
                    self._send_json(
                        HTTPStatus.FORBIDDEN,
                        {"allowed": False, "reason_zh": identity.get("reason_zh", "当前身份没有查看权限。")},
                    )
                    return
                if parsed.path == "/api/projects":
                    self._send_json(HTTPStatus.OK, _list_payload(query))
                    return
                project_ids = [item for item in _first(query, "project_ids", "").split(",") if item]
                company_id = _first(query, "company_id", "demo-north")
                period = _first(query, "period", "2026-07")
                if parsed.path == "/api/projects/compare":
                    self._send_json(
                        HTTPStatus.OK,
                        kernel.batch_compare(project_ids, company_id=company_id, period=period),
                    )
                    return
                self._send_csv(kernel.export_csv(project_ids, company_id=company_id, period=period))
                return
            except (KeyError, TypeError, homepage_kernel.HomepageError, kernel.ProjectListError) as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})
                return
        if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico":
            super().do_GET()
            return
        self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")


class ProjectListServer(base_runtime.HomepageUsabilityServer):
    pass


def start_server(host: str = "127.0.0.1", port: int = 0) -> tuple[ProjectListServer, threading.Thread, str]:
    server = ProjectListServer((host, port), ProjectListHandler)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s17p1-project-list", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S17-P1 项目列表")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ProjectListServer((args.host, args.port), ProjectListHandler)
    print(f"KMFA 项目列表：http://{args.host}:{server.server_address[1]}/projects", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
