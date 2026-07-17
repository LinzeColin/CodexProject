#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S18-P1 回款与应收页面。"""

from __future__ import annotations

import argparse
import threading
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s17_p1_project_list as list_runtime
from KMFA.tools import run_v015_s17_p3_project_workflow as base_runtime
from KMFA.tools import v015_s16_p1_homepage as homepage_kernel
from KMFA.tools import v015_s17_p1_project_list as list_kernel
from KMFA.tools import v015_s17_p3_project_workflow as workflow_kernel
from KMFA.tools import v015_s18_p1_receivables_collections as kernel


def _first(query: dict[str, list[str]], key: str, default: str) -> str:
    return query.get(key, [default])[0]


def _payload(query: dict[str, list[str]]) -> dict[str, Any]:
    return kernel.receivables_view(
        company_id=_first(query, "company_id", "demo-north"),
        period=_first(query, "period", "2026-07"),
        project=_first(query, "project", "all"),
        customer=_first(query, "customer", "all"),
        invoice_period=_first(query, "invoice_period", "all"),
        owner=_first(query, "owner", "all"),
        aging_bucket=_first(query, "aging_bucket", "all"),
        priority=_first(query, "priority", "all"),
        group_by=_first(query, "group_by", "project"),
    )


def render_html() -> str:
    html = base_runtime.render_html()
    view = '''
    <section id="receivables-view" class="receivables-view" aria-labelledby="receivables-title" hidden>
      <header class="receivables-head">
        <div><span>回款与应收</span><h1 id="receivables-title">先看欠款，再决定内部复核顺序</h1><p>只统计已开票未回款；不会自动联系客户，也不会执行付款。</p></div>
        <div class="receivables-cutoff"><span>账龄截止日</span><strong id="receivables-cutoff">2026-07-15</strong></div>
      </header>
      <div id="receivables-feedback" class="receivables-feedback" role="status" aria-live="polite">正在核对回款与应收…</div>
      <section id="receivables-summary" class="receivables-summary" aria-label="回款与应收汇总"></section>
      <section class="receivables-basis" aria-labelledby="receivables-basis-title"><div><h2 id="receivables-basis-title">这页怎么算</h2><p id="receivables-definition"></p><p id="receivables-aging-basis"></p></div><details><summary>查看催收排序规则</summary><p id="receivables-priority-formula"></p><p id="receivables-priority-boundaries"></p></details></section>
      <section class="receivables-filters" aria-label="应收筛选">
        <label>项目<select id="receivables-project"><option value="all">全部项目</option></select></label>
        <label>客户<select id="receivables-customer"><option value="all">全部客户</option></select></label>
        <label>开票期间<select id="receivables-period"><option value="all">全部期间</option></select></label>
        <label>负责人<select id="receivables-owner"><option value="all">全部负责人</option></select></label>
        <label>账龄<select id="receivables-aging"><option value="all">全部账龄</option></select></label>
        <label>复核顺序<select id="receivables-priority"><option value="all">全部顺序</option></select></label>
        <label>汇总方式<select id="receivables-group"><option value="project">按项目</option><option value="customer">按客户</option><option value="period">按期间</option><option value="owner">按负责人</option></select></label>
      </section>
      <section class="receivables-groups" aria-labelledby="receivables-groups-title"><div class="receivables-section-head"><h2 id="receivables-groups-title">多维汇总</h2><span id="receivables-group-check">明细与汇总核对中</span></div><div id="receivables-group-list" class="receivables-group-list"></div></section>
      <section class="receivables-detail" aria-labelledby="receivables-detail-title">
        <div class="receivables-section-head"><div><h2 id="receivables-detail-title">应收明细</h2><p>按公开、逐项可解释的分数从高到低排列。</p></div><strong id="receivables-row-count">0 笔</strong></div>
        <div class="receivables-table-wrap"><table class="receivables-table"><thead><tr><th>内部复核顺序</th><th>客户 / 项目</th><th>负责人</th><th>发票</th><th>已回款</th><th>应收</th><th>账龄</th><th>争议 / 质保</th><th>依据与内部下一步</th></tr></thead><tbody id="receivables-table-body"></tbody></table></div>
        <div id="receivables-mobile-list" class="receivables-mobile-list"></div>
      </section>
      <section class="unbilled-section" aria-labelledby="unbilled-title"><div class="receivables-section-head"><div><h2 id="unbilled-title">未开票节点</h2><p>单独列示，不计入应收，也不进入催收顺序。</p></div><strong id="unbilled-count">0 项</strong></div><div id="unbilled-list" class="unbilled-list"></div></section>
      <p class="receivables-disclaimer">当前页面只使用公开合成资料验证口径、排序和页面一致性，不代表任何真实公司或客户。</p>
    </section>'''
    css = '''
    body[data-receivables-active="true"] #page-view,
    body[data-receivables-active="true"] #loading-view,
    body[data-receivables-active="true"] #error-view,
    body[data-receivables-active="true"] #not-found-view,
    body[data-receivables-active="true"] #homepage-view,
    body[data-receivables-active="true"] #project-list-view,
    body[data-receivables-active="true"] #project-detail-view,
    body[data-receivables-active="true"] #project-workflow-view,
    body[data-receivables-active="true"] #context-status,
    body[data-receivables-active="true"] .identity-shell,
    body[data-receivables-active="true"] .quick-shell,
    body[data-receivables-active="true"] #access-workspace,
    body[data-receivables-active="true"] #experience-workspace{display:none!important}
    .receivables-view{margin:2px 0 28px}.receivables-head{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;margin-bottom:14px}.receivables-head>div:first-child>span{color:#17648f;font-size:12px;font-weight:800}.receivables-head h1{margin:4px 0 0;color:#173d57;font-size:29px;line-height:1.25}.receivables-head p{margin:7px 0 0;color:#607684;font-size:14px}.receivables-cutoff{display:grid;justify-items:end;color:#607684;font-size:12px}.receivables-cutoff strong{margin-top:4px;color:#173d57;font-size:15px}.receivables-feedback{min-height:39px;margin-bottom:13px;padding:9px 12px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:6px;background:#edf6fb;color:#29475d;font-size:13px;line-height:1.5}.receivables-feedback[data-state="error"]{border-color:#d7a6a6;background:#fff8f7;color:#7f2929}
    .receivables-summary{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-bottom:13px}.receivables-metric{padding:14px;border:1px solid #d9e3e9;border-radius:8px;background:#fff}.receivables-metric span{display:block;color:#607684;font-size:11px}.receivables-metric strong{display:block;margin-top:5px;color:#173d57;font-size:19px}.receivables-metric small{display:block;margin-top:4px;color:#607684;font-size:10px;line-height:1.4}.receivables-metric[data-alert="true"]{border-left:4px solid #b44741;background:#fff8f7}.receivables-metric[data-separate="true"]{border-left:4px solid #b47a20;background:#fffbf2}
    .receivables-basis{display:grid;grid-template-columns:1.3fr .9fr;gap:16px;margin-bottom:13px;padding:15px;border:1px solid #cbdbe4;border-radius:8px;background:#f6fafc}.receivables-basis h2{margin:0 0 5px;color:#214d68;font-size:16px}.receivables-basis p{margin:4px 0;color:#536b7c;font-size:12px;line-height:1.55}.receivables-basis details{border:1px solid #d8e3e9;border-radius:7px;background:#fff}.receivables-basis summary{min-height:42px;padding:10px 12px;color:#29475d;font-size:12px;font-weight:800;cursor:pointer}.receivables-basis details p{padding:0 12px}.receivables-basis details p:last-child{padding-bottom:10px}
    .receivables-filters{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-bottom:13px;padding:13px;border:1px solid #d8e2e8;border-radius:8px;background:#fff}.receivables-filters label{display:grid;gap:5px;color:#536b7c;font-size:11px;font-weight:750}.receivables-filters select{min-height:42px;padding:8px 9px;border:1px solid #b9cbd7;border-radius:6px;background:#fff;color:#29475d;font:inherit;font-size:12px}
    .receivables-groups,.receivables-detail,.unbilled-section{margin-bottom:13px;padding:16px;border:1px solid #d8e2e8;border-radius:8px;background:#fff}.receivables-section-head{display:flex;justify-content:space-between;gap:15px;align-items:flex-start;margin-bottom:11px}.receivables-section-head h2{margin:0;color:#214d68;font-size:18px}.receivables-section-head p{margin:4px 0 0;color:#607684;font-size:12px}.receivables-section-head>span,.receivables-section-head>strong{color:#276346;font-size:12px}.receivables-group-list{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}.receivables-group-card{padding:12px;border:1px solid #dce5ea;border-radius:7px;background:#f8fafb}.receivables-group-card strong{display:block;color:#29475d;font-size:13px}.receivables-group-card span{display:block;margin-top:5px;color:#173d57;font-size:17px;font-weight:800}.receivables-group-card small{display:block;margin-top:4px;color:#607684;font-size:10px;line-height:1.45}
    .receivables-table-wrap{width:100%;overflow:auto;border:1px solid #dce5ea;border-radius:7px}.receivables-table{width:100%;border-collapse:collapse;font-size:11px}.receivables-table th,.receivables-table td{padding:9px 8px;border-bottom:1px solid #e2e9ed;text-align:left;vertical-align:top;white-space:nowrap}.receivables-table th{background:#f3f6f8;color:#40596b}.receivables-table tr:last-child td{border-bottom:0}.receivables-table .numeric{text-align:right}.receivables-party strong{display:block;color:#29475d}.receivables-party small{display:block;margin-top:3px;color:#607684}.priority-badge{display:inline-block;padding:4px 7px;border-radius:999px;background:#edf3f6;color:#40596b;font-weight:800}.priority-badge[data-tier="HIGH"]{background:#fde8e6;color:#8a2f2a}.priority-badge[data-tier="MEDIUM"]{background:#fff1d5;color:#76551c}.priority-badge[data-tier="LOW"]{background:#e8f7ee;color:#246040}.priority-badge[data-tier="EVIDENCE_MISSING"]{background:#eef0f2;color:#5e6870}.priority-score{display:block;margin-top:4px;color:#607684;font-size:10px}.priority-details{max-width:255px;white-space:normal}.priority-details summary{min-height:32px;color:#155f8d;font-weight:750;cursor:pointer}.priority-details ul{margin:5px 0;padding-left:17px;line-height:1.45}.internal-step{display:block;margin-top:5px;color:#40596b;font-weight:750}.receivables-mobile-list{display:none}.unbilled-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.unbilled-card{padding:12px;border:1px solid #dec897;border-radius:7px;background:#fffbf2}.unbilled-card strong{display:block;color:#624b22;font-size:13px}.unbilled-card span,.unbilled-card small{display:block;margin-top:4px;color:#765d31;font-size:11px}.receivables-disclaimer{margin:12px 2px 0;color:#607684;font-size:12px}
    @media(max-width:1000px){.receivables-summary{grid-template-columns:repeat(3,1fr)}.receivables-filters{grid-template-columns:repeat(3,1fr)}.receivables-group-list{grid-template-columns:repeat(2,1fr)}}
    @media(max-width:760px){.receivables-head{display:block}.receivables-head h1{font-size:25px}.receivables-cutoff{justify-items:start;margin-top:10px}.receivables-summary,.receivables-filters,.receivables-group-list,.unbilled-list{grid-template-columns:1fr}.receivables-basis{grid-template-columns:1fr}.receivables-filters select{min-height:44px;font-size:14px}.receivables-table-wrap{display:none}.receivables-mobile-list{display:grid;gap:10px}.receivables-mobile-card{padding:13px;border:1px solid #dce5ea;border-radius:7px;background:#fbfcfd}.receivables-mobile-card h3{margin:0;color:#29475d;font-size:15px}.receivables-mobile-card>p{margin:4px 0 10px;color:#607684;font-size:12px}.receivables-mobile-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.receivables-mobile-grid div{padding:8px;border-radius:5px;background:#f0f5f7}.receivables-mobile-grid span{display:block;color:#607684;font-size:10px}.receivables-mobile-grid strong{display:block;margin-top:3px;color:#29475d;font-size:12px}.priority-details{max-width:none;margin-top:9px}.receivables-section-head{display:block}.receivables-section-head>span,.receivables-section-head>strong{display:inline-block;margin-top:6px}}
    @media(prefers-reduced-motion:reduce){.receivables-view *{transition:none!important;animation:none!important}}
    '''
    script = '''
  <script>
  (()=>{'use strict';
    const view=document.querySelector('#receivables-view'),feedback=document.querySelector('#receivables-feedback');let last=null,sequence=0,optionsBound=false;
    const active=()=>location.pathname==='/collections';const text=(tag,value,className='')=>{const node=document.createElement(tag);node.textContent=value==null?'':String(value);if(className)node.className=className;return node;};
    const money=cents=>{const sign=cents<0?'-':'';const value=Math.abs(cents),yuan=Math.floor(value/100),fen=String(value%100).padStart(2,'0');return sign+'¥'+yuan.toLocaleString('zh-CN')+'.'+fen;};
    const identity=()=>window.KMFA_ROLE_TEST.identity(),context=()=>window.KMFA_TEST.context();const value=id=>document.querySelector(id).value;
    const params=()=>{const who=identity(),scope=context();return new URLSearchParams({user_id:who.user_id,role_id:who.role_id,company_id:scope.company,period:scope.period,project:value('#receivables-project'),customer:value('#receivables-customer'),invoice_period:value('#receivables-period'),owner:value('#receivables-owner'),aging_bucket:value('#receivables-aging'),priority:value('#receivables-priority'),group_by:value('#receivables-group')});};
    const setFeedback=(message,error=false)=>{feedback.textContent=message;if(error)feedback.dataset.state='error';else delete feedback.dataset.state;};
    const metric=(label,result,note,kind='')=>{const node=text('div','','receivables-metric');if(kind)node.dataset[kind]='true';node.append(text('span',label),text('strong',result),text('small',note));return node;};
    const option=(value,label)=>{const node=document.createElement('option');node.value=value;node.textContent=label;return node;};
    const bind=(selector,rows)=>{const select=document.querySelector(selector),current=select.value;select.replaceChildren(option('all',select.options[0]?.textContent||'全部'));rows.forEach(row=>select.append(option(Array.isArray(row)?row[0]:row,Array.isArray(row)?row[1]:row)));select.value=[...select.options].some(row=>row.value===current)?current:'all';};
    const bindOptions=payload=>{if(optionsBound)return;const o=payload.filter_options;bind('#receivables-project',o.projects);bind('#receivables-customer',o.customers);bind('#receivables-period',o.invoice_periods);bind('#receivables-owner',o.owners);bind('#receivables-aging',o.aging_buckets);bind('#receivables-priority',o.priorities);optionsBound=true;};
    const renderSummary=payload=>{const s=payload.summary,shell=document.querySelector('#receivables-summary');shell.replaceChildren(metric('已开票',money(s.invoice_cents),'当前主体全部发票'),metric('已回款',money(s.collected_cents),'银行回款演示事实'),metric('筛选后应收',money(s.receivable_cents),s.receivable_count+' 笔已开票未回款'),metric('筛选后逾期',money(s.overdue_cents),s.high_priority_count+' 笔优先复核','alert'),metric('未开票节点',money(s.unbilled_cents),'单独列示，不计应收','separate'));};
    const renderGroups=payload=>{const shell=document.querySelector('#receivables-group-list');shell.replaceChildren();payload.groups.forEach(row=>{const card=text('div','','receivables-group-card');card.append(text('strong',row.group_label_zh),text('span',money(row.receivable_cents)),text('small','逾期 '+money(row.overdue_cents)+' · '+row.receivable_count+' 笔 · 优先复核 '+row.high_priority_count+' 笔'));shell.append(card);});document.querySelector('#receivables-group-check').textContent=payload.group_difference_cents===0?'明细与汇总相差 0 分':'明细与汇总不一致';};
    const badge=row=>{const node=text('span',row.priority_label_zh,'priority-badge');node.dataset.tier=row.priority_tier;return node;};
    const details=row=>{const node=document.createElement('details');node.className='priority-details';node.append(text('summary',row.priority_supported?'查看 '+row.priority_reasons_zh.length+' 项依据':'查看缺失原因'));const list=document.createElement('ul');row.priority_reasons_zh.forEach(reason=>list.append(text('li',reason)));node.append(list);if(row.recommended_internal_step_zh)node.append(text('span','内部下一步：'+row.recommended_internal_step_zh,'internal-step'));return node;};
    const renderRows=payload=>{const body=document.querySelector('#receivables-table-body'),mobile=document.querySelector('#receivables-mobile-list');body.replaceChildren();mobile.replaceChildren();payload.rows.forEach(row=>{const tr=document.createElement('tr'),priority=document.createElement('td');priority.append(badge(row),text('span',row.priority_score==null?'不评分':row.priority_score+' 分','priority-score'));const party=text('td','','receivables-party');party.append(text('strong',row.customer_zh),text('small',row.project_name_zh+' · '+row.milestone_zh));const basis=document.createElement('td');basis.append(details(row));tr.append(priority,party,text('td',row.owner_zh),text('td',money(row.invoice_cents),'numeric'),text('td',money(row.collected_cents),'numeric'),text('td',money(row.receivable_cents),'numeric'),text('td',row.aging_bucket_zh+' · '+row.overdue_days+' 天'),text('td','争议 '+money(row.dispute_cents)+' / 质保 '+money(row.retention_cents)),basis);body.append(tr);
        const card=text('article','','receivables-mobile-card');card.append(text('h3',row.customer_zh+' · '+row.project_name_zh),text('p',row.owner_zh+' · '+row.milestone_zh));const grid=text('div','','receivables-mobile-grid');[['复核顺序',row.priority_label_zh+(row.priority_score==null?'':' · '+row.priority_score+' 分')],['应收',money(row.receivable_cents)],['账龄',row.aging_bucket_zh+' · '+row.overdue_days+' 天'],['争议 / 质保',money(row.dispute_cents)+' / '+money(row.retention_cents)]].forEach(([label,result])=>{const item=document.createElement('div');item.append(text('span',label),text('strong',result));grid.append(item);});card.append(grid,details(row));mobile.append(card);});document.querySelector('#receivables-row-count').textContent=payload.rows.length+' 笔';};
    const renderUnbilled=payload=>{const shell=document.querySelector('#unbilled-list');shell.replaceChildren();payload.unbilled_items.forEach(row=>{const card=text('div','','unbilled-card');card.append(text('strong',row.customer_zh+' · '+row.project_name_zh),text('span',row.milestone_zh+' · '+money(row.unbilled_cents)),text('small','未开票，应收 0.00 元，不进入催收顺序'));shell.append(card);});document.querySelector('#unbilled-count').textContent=payload.unbilled_items.length+' 项';};
    const render=payload=>{last=payload;bindOptions(payload);document.querySelector('#receivables-cutoff').textContent=payload.cutoff_date;document.querySelector('#receivables-definition').textContent=payload.receivable_definition_zh;document.querySelector('#receivables-aging-basis').textContent=payload.aging_basis_zh;document.querySelector('#receivables-priority-formula').textContent=payload.priority_formula_zh;document.querySelector('#receivables-priority-boundaries').textContent=payload.priority_boundaries_zh;renderSummary(payload);renderGroups(payload);renderRows(payload);renderUnbilled(payload);setFeedback(payload.summary.evidence_missing_count?'核对完成：'+payload.summary.evidence_missing_count+' 笔资料不足，系统未给出催收建议。':'核对完成：全部催收顺序均有逐项依据。');};
    const load=async()=>{if(!active()){view.hidden=true;delete document.body.dataset.receivablesActive;return null;}view.hidden=false;document.body.dataset.receivablesActive='true';setFeedback('正在核对当前公司的回款与应收…');const current=++sequence;try{const response=await fetch('/api/receivables?'+params()),payload=await response.json();if(current!==sequence)return {stale_response_ignored:true};if(!response.ok||!payload.allowed){setFeedback(payload.reason_zh||'当前身份不能查看这些应收。',true);return payload;}render(payload);return payload;}catch(_){if(current===sequence)setFeedback('回款与应收暂时无法读取，请稍后重试。',true);return null;}};
    document.querySelectorAll('.receivables-filters select').forEach(node=>node.addEventListener('change',load));['#context-company','#context-period','#identity-user'].forEach(selector=>document.querySelector(selector).addEventListener('change',()=>{optionsBound=false;setTimeout(load,0);}));window.addEventListener('popstate',load);window.KMFA_RECEIVABLES_TEST={load,snapshot:()=>last,params:()=>params().toString(),setFilter:(id,value)=>{document.querySelector(id).value=value;return load();}};load();
  })();
  </script>'''
    marker = '<section id="project-list-view" class="project-list-view" aria-labelledby="project-list-title" hidden>'
    if marker not in html:
        raise RuntimeError("S17 project insertion point drifted")
    html = html.replace(marker, view + marker, 1)
    html = html.replace("  </style>", css + "  </style>", 1)
    html = html.replace("</body>", script + "</body>", 1)
    html = html.replace("<title>KMFA 项目处理 · 经营工作台</title>", "<title>KMFA 回款与应收 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class ReceivablesHandler(base_runtime.ProjectWorkflowHandler):
    server_version = "KMFAReceivables/1.5"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/api/receivables":
            query = parse_qs(parsed.query)
            try:
                allowed, identity = list_runtime._authorised(query)
                if not allowed:
                    self._send_json(HTTPStatus.FORBIDDEN, {"allowed": False, "reason_zh": identity.get("reason_zh", "当前身份没有查看权限。")})
                    return
                self._send_json(HTTPStatus.OK, _payload(query))
            except (KeyError, TypeError, homepage_kernel.HomepageError, list_kernel.ProjectListError, kernel.ReceivablesError) as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})
            return
        if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico" or parsed.path in base_runtime.REPORT_FILES:
            super().do_GET()
            return
        self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")


class ReceivablesServer(base_runtime.ProjectWorkflowServer):
    pass


def start_server(
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    event_path: Path | str = workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
) -> tuple[ReceivablesServer, threading.Thread, str]:
    server = ReceivablesServer((host, port), ReceivablesHandler)
    server.journal = workflow_kernel.EventJournal(event_path)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s18p1-receivables", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S18-P1 回款与应收页面")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--event-path", default=str(workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH))
    args = parser.parse_args()
    server = ReceivablesServer((args.host, args.port), ReceivablesHandler)
    server.journal = workflow_kernel.EventJournal(args.event_path)
    print(f"KMFA 回款与应收：http://{args.host}:{server.server_address[1]}/collections", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
