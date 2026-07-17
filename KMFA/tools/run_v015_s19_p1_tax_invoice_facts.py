#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S19-P1 税务与发票事实页面。"""

from __future__ import annotations

import argparse
import threading
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s17_p1_project_list as list_runtime
from KMFA.tools import run_v015_s18_p3_relation_reporting as base_runtime
from KMFA.tools import v015_s16_p1_homepage as homepage_kernel
from KMFA.tools import v015_s17_p1_project_list as list_kernel
from KMFA.tools import v015_s17_p3_project_workflow as workflow_kernel
from KMFA.tools import v015_s18_p2_funds_accounts as funds_kernel
from KMFA.tools import v015_s18_p3_relation_reporting as relation_kernel
from KMFA.tools import v015_s19_p1_tax_invoice_facts as kernel


def _first(query: dict[str, list[str]], key: str, default: str) -> str:
    return query.get(key, [default])[0]


def _payload(query: dict[str, list[str]]) -> dict[str, Any]:
    return kernel.tax_invoice_view(
        company_id=_first(query, "company_id", "demo-north"),
        period=_first(query, "period", "2026-07"),
        project=_first(query, "project", ""),
        business_type=_first(query, "business_type", ""),
        direction=_first(query, "direction", ""),
        invoice_status=_first(query, "invoice_status", ""),
        match_state=_first(query, "match_state", ""),
    )


def render_html() -> str:
    html = base_runtime.render_html()
    view = '''
    <section id="tax-invoice-view" class="tax-invoice-view" aria-labelledby="tax-invoice-title" hidden>
      <header class="ti-head">
        <div><span>税务与政策</span><h1 id="tax-invoice-title">先把税票事实对齐，再看项目税负</h1><p>逐张展示销项、进项、税率、含税状态和发票状态；异常保留证据，只交给人工复核。</p></div>
        <nav class="s19-journey" aria-label="税务与政策步骤"><a class="ti-back" href="/funds-report">返回关联与报告</a><strong aria-current="step">1 税票事实</strong><a class="s19-next" href="/policy-eligibility">下一步：政策材料</a></nav>
      </header>
      <aside id="ti-boundary" class="ti-boundary"><strong>管理分析，不是正式申报</strong><span>页面不猜税率、不自动调税，也不生成报税结论。</span></aside>
      <div id="ti-feedback" class="ti-feedback" role="status" aria-live="polite">正在核对税票事实…</div>
      <section id="ti-metrics" class="ti-metrics" aria-label="税票事实摘要"></section>
      <section class="ti-controls" aria-label="税票查看条件">
        <label>项目<select id="ti-project"><option value="">全部项目</option><option value="PUB-PROJ-001">厂房升级项目</option><option value="PUB-PROJ-002">设备交付项目</option><option value="PUB-PROJ-003">运维服务项目</option></select></label>
        <label>业务类型<select id="ti-business"><option value="">全部类型</option><option value="工程实施">工程实施</option><option value="设备服务">设备服务</option><option value="运维咨询">运维咨询</option></select></label>
        <label>进销项<select id="ti-direction"><option value="">全部</option><option value="OUTPUT">销项</option><option value="INPUT">进项</option></select></label>
        <label>发票状态<select id="ti-status"><option value="">全部状态</option><option value="ISSUED">已开具</option><option value="RECEIVED">已收到</option><option value="PENDING_CONFIRMATION">待确认</option></select></label>
        <label>匹配结果<select id="ti-match"><option value="">全部结果</option><option value="MATCHED">已匹配</option><option value="REVIEW_REQUIRED">需复核</option></select></label>
      </section>
      <section class="ti-section" aria-labelledby="ti-facts-title">
        <div class="ti-section-head"><div><h2 id="ti-facts-title">税票事实</h2><p id="ti-rate-note">税率只采用票据里的明确记录。</p></div><strong id="ti-fact-count">0 条</strong></div>
        <div class="ti-table-wrap"><table class="ti-table"><thead><tr><th>票据</th><th>项目与业务</th><th>税率与含税</th><th>未税金额</th><th>税额</th><th>价税合计</th><th>匹配结果</th></tr></thead><tbody id="ti-fact-body"></tbody></table></div>
        <div id="ti-fact-mobile" class="ti-mobile-list"></div>
      </section>
      <section class="ti-section" aria-labelledby="ti-anomaly-title">
        <div class="ti-section-head"><div><h2 id="ti-anomaly-title">需要人工复核的异常</h2><p>每项同时显示票据依据、合同依据和具体差异，不产生自动调整。</p></div><strong id="ti-anomaly-count">0 项</strong></div>
        <div id="ti-anomaly-list" class="ti-anomaly-list"></div>
      </section>
      <section class="ti-section" aria-labelledby="ti-burden-title">
        <div class="ti-section-head"><div><h2 id="ti-burden-title">项目税负管理视图</h2><p>只纳入已匹配且税率明确的公开合成票据；待复核资料全部排除。</p></div><strong>当前公司与期间</strong></div>
        <div class="ti-table-wrap"><table class="ti-table"><thead><tr><th>项目</th><th>业务类型</th><th>销项税额</th><th>可用进项税额</th><th>管理净税负</th><th>完整性</th><th>范围</th></tr></thead><tbody id="ti-burden-body"></tbody></table></div>
        <div id="ti-burden-mobile" class="ti-mobile-list"></div>
      </section>
      <p class="ti-disclaimer">所有内容均为公开合成演示，用于验证事实、匹配和页面口径；不连接税务平台，不开票，不申报，不替代税务专业人员判断。</p>
    </section>
    '''
    css = '''
    body[data-tax-invoice-active="true"] #page-view,
    body[data-tax-invoice-active="true"] #loading-view,
    body[data-tax-invoice-active="true"] #error-view,
    body[data-tax-invoice-active="true"] #not-found-view,
    body[data-tax-invoice-active="true"] #homepage-view,
    body[data-tax-invoice-active="true"] #project-list-view,
    body[data-tax-invoice-active="true"] #project-detail-view,
    body[data-tax-invoice-active="true"] #project-workflow-view,
    body[data-tax-invoice-active="true"] #receivables-view,
    body[data-tax-invoice-active="true"] #funds-view,
    body[data-tax-invoice-active="true"] #funds-report-view,
    body[data-tax-invoice-active="true"] #context-status,
    body[data-tax-invoice-active="true"] .identity-shell,
    body[data-tax-invoice-active="true"] .quick-shell,
    body[data-tax-invoice-active="true"] #access-workspace,
    body[data-tax-invoice-active="true"] #experience-workspace{display:none!important}
    .tax-invoice-view{margin:2px 0 28px}.ti-head{display:flex;justify-content:space-between;gap:22px;align-items:flex-start;margin-bottom:12px}.ti-head>div>span{color:#17648f;font-size:12px;font-weight:800}.ti-head h1{margin:4px 0 0;color:#173d57;font-size:29px;line-height:1.25}.ti-head p{margin:7px 0 0;color:#607684;font-size:14px}.ti-back{display:inline-flex;min-height:44px;align-items:center;justify-content:center;padding:0 13px;border:1px solid #9fb8c8;border-radius:6px;background:#fff;color:#245a7a;font-size:12px;font-weight:800;text-decoration:none}.ti-boundary{display:flex;justify-content:space-between;gap:16px;margin-bottom:10px;padding:13px 15px;border:1px solid #d5b27c;border-left:4px solid #a86a17;border-radius:7px;background:#fffaf2;color:#654519}.ti-boundary strong{font-size:14px}.ti-boundary span{font-size:12px}.ti-feedback{min-height:40px;margin-bottom:11px;padding:9px 12px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:6px;background:#edf6fb;color:#29475d;font-size:13px;line-height:1.5}.ti-feedback[data-state="error"]{border-color:#d7a6a6;background:#fff8f7;color:#7f2929}.ti-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-bottom:11px}.ti-metric{padding:13px;border:1px solid #d9e3e9;border-radius:7px;background:#fff}.ti-metric span{display:block;color:#607684;font-size:11px}.ti-metric strong{display:block;margin-top:5px;color:#173d57;font-size:19px}.ti-metric small{display:block;margin-top:4px;color:#607684;font-size:10px}.ti-controls{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px;margin-bottom:11px;padding:13px;border:1px solid #d8e2e8;border-radius:8px;background:#fff}.ti-controls label{display:grid;gap:5px;color:#536b7c;font-size:11px;font-weight:750}.ti-controls select{min-height:44px;padding:8px;border:1px solid #b9cbd7;border-radius:6px;background:#fff;color:#29475d;font-size:12px}.ti-section{margin-bottom:11px;padding:15px;border:1px solid #d8e2e8;border-radius:8px;background:#fff}.ti-section-head{display:flex;justify-content:space-between;gap:15px;align-items:flex-start;margin-bottom:10px}.ti-section-head h2{margin:0;color:#214d68;font-size:18px}.ti-section-head p{margin:4px 0 0;color:#607684;font-size:12px}.ti-section-head>strong{color:#276346;font-size:12px}.ti-table-wrap{width:100%;overflow:auto;border:1px solid #dce5ea;border-radius:7px}.ti-table{width:100%;border-collapse:collapse;font-size:11px}.ti-table th,.ti-table td{padding:9px 8px;border-bottom:1px solid #e2e9ed;text-align:left;vertical-align:top;white-space:nowrap}.ti-table th{background:#f3f6f8;color:#40596b}.ti-table td:first-child,.ti-table td:nth-child(2),.ti-table td:last-child{white-space:normal;min-width:130px}.ti-table td:last-child{min-width:190px}.ti-table strong{display:block;color:#29475d}.ti-table small{display:block;margin-top:3px;color:#607684;line-height:1.45}.ti-review{color:#8a5712;font-weight:800}.ti-match{color:#276346;font-weight:800}.ti-unknown{color:#8a5712;font-weight:800}.ti-anomaly-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.ti-anomaly-card{padding:12px;border:1px solid #e2d5bd;border-left:4px solid #a86a17;border-radius:7px;background:#fffaf2}.ti-anomaly-card header{display:flex;justify-content:space-between;gap:8px}.ti-anomaly-card strong{color:#654519;font-size:13px}.ti-anomaly-card span{color:#7a684b;font-size:10px}.ti-anomaly-card p{margin:7px 0 0;color:#5d5447;font-size:11px;line-height:1.5}.ti-empty{grid-column:1/-1;padding:14px;border:1px dashed #c7d5de;border-radius:7px;color:#607684;text-align:center}.ti-mobile-list{display:none}.ti-mobile-card{padding:12px;border:1px solid #dce5ea;border-radius:7px;background:#f8fafb}.ti-mobile-card h3{margin:0 0 8px;color:#29475d;font-size:14px}.ti-mobile-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.ti-mobile-grid div{padding:8px;border:1px solid #e1e8ec;border-radius:6px;background:#fff}.ti-mobile-grid span{display:block;color:#607684;font-size:10px}.ti-mobile-grid strong{display:block;margin-top:3px;color:#29475d;font-size:12px}.ti-mobile-card p,.ti-disclaimer{color:#607684;font-size:11px;line-height:1.5}
    .s19-journey{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:7px;max-width:430px}.s19-journey a,.s19-journey strong{display:inline-flex;min-height:44px;align-items:center;justify-content:center;padding:0 13px;border:1px solid #9fb8c8;border-radius:6px;background:#fff;color:#245a7a;font-size:12px;font-weight:800;text-decoration:none}.s19-journey strong{border-color:#5c91aa;background:#edf6fb;color:#173d57}.s19-next{border-color:#5c91aa!important;background:#245f75!important;color:#fff!important}
    @media(max-width:1050px){.ti-controls{grid-template-columns:repeat(3,1fr)}.ti-metrics{grid-template-columns:repeat(2,1fr)}.ti-anomaly-list{grid-template-columns:1fr}}
    @media(max-width:720px){.ti-head,.ti-boundary,.ti-section-head{display:grid}.ti-head h1{font-size:24px}.s19-journey{justify-content:flex-start;max-width:none}.ti-back{justify-self:start}.ti-controls{grid-template-columns:1fr 1fr}.ti-table-wrap{display:none}.ti-mobile-list{display:grid;gap:8px}.ti-section{padding:12px}.ti-metrics{grid-template-columns:1fr 1fr}.ti-metric{padding:10px}.ti-anomaly-list{grid-template-columns:1fr}}
    '''
    script = '''
  <script>
  (()=>{
    const view=document.querySelector('#tax-invoice-view');let last=null,sequence=0;
    const active=()=>location.pathname==='/tax-policy';
    const node=(tag,value='',className='')=>{const item=document.createElement(tag);item.textContent=value;if(className)item.className=className;return item;};
    const money=value=>value===null||value===undefined?'待确认':new Intl.NumberFormat('zh-CN',{style:'currency',currency:'CNY'}).format(value/100);
    const params=()=>new URLSearchParams({user_id:document.querySelector('#identity-user').value,role_id:document.querySelector('#identity-user').selectedOptions[0].dataset.role||'management',company_id:document.querySelector('#context-company').value,period:document.querySelector('#context-period').value,project:document.querySelector('#ti-project').value,business_type:document.querySelector('#ti-business').value,direction:document.querySelector('#ti-direction').value,invoice_status:document.querySelector('#ti-status').value,match_state:document.querySelector('#ti-match').value});
    const feedback=(message,error=false)=>{const target=document.querySelector('#ti-feedback');target.textContent=message;if(error)target.dataset.state='error';else delete target.dataset.state;};
    const metric=(label,value,note)=>{const item=node('article','','ti-metric');item.append(node('span',label),node('strong',value),node('small',note));return item;};
    const renderMetrics=payload=>{const summary=payload.summary,target=document.querySelector('#ti-metrics');target.replaceChildren(metric('当前票据',String(summary.fact_count),'筛选后的公开合成事实'),metric('已匹配',String(summary.matched_count),'主体、项目、期间、税率一致'),metric('需复核',String(summary.review_count),'保持原值，不自动调整'),metric('未知税率',String(summary.unknown_rate_count),'显示待确认，不推断'));};
    const factCard=row=>{const card=node('article','','ti-mobile-card');card.append(node('h3',row.direction_zh+' · '+row.invoice_id));const grid=node('div','','ti-mobile-grid');[['项目',row.project_name_zh],['状态',row.invoice_status_zh],['税率',row.tax_rate_display_zh],['匹配',row.match_state_zh],['税额',money(row.tax_cents)],['价税合计',money(row.gross_cents)]].forEach(([label,value])=>{const item=document.createElement('div');item.append(node('span',label),node('strong',value));grid.append(item);});card.append(grid,node('p',row.anomaly_labels_zh.length?row.anomaly_labels_zh.join('、'):'四项匹配通过'));return card;};
    const renderFacts=payload=>{const body=document.querySelector('#ti-fact-body'),mobile=document.querySelector('#ti-fact-mobile');body.replaceChildren();mobile.replaceChildren();payload.rows.forEach(row=>{const tr=document.createElement('tr'),invoice=document.createElement('td'),project=document.createElement('td'),rate=document.createElement('td'),match=document.createElement('td');invoice.append(node('strong',row.direction_zh+' · '+row.invoice_id),node('small',row.invoice_status_zh));project.append(node('strong',row.project_name_zh),node('small',row.business_type_zh));rate.append(node('strong',row.tax_rate_display_zh,row.tax_rate_bps===null?'ti-unknown':''),node('small',row.tax_inclusive_zh));match.append(node('strong',row.match_state_zh,row.match_state==='MATCHED'?'ti-match':'ti-review'),node('small',row.anomaly_labels_zh.length?row.anomaly_labels_zh.join('、'):'四项匹配通过'));tr.append(invoice,project,rate,node('td',money(row.net_cents)),node('td',money(row.tax_cents)),node('td',money(row.gross_cents)),match);body.append(tr);mobile.append(factCard(row));});if(!payload.rows.length){const tr=document.createElement('tr'),td=node('td','当前筛选没有票据。');td.colSpan=7;tr.append(td);body.append(tr);mobile.append(node('div','当前筛选没有票据。','ti-empty'));}document.querySelector('#ti-fact-count').textContent=payload.summary.fact_count+' 条';document.querySelector('#ti-rate-note').textContent=payload.policy.rate_note_zh;};
    const renderAnomalies=payload=>{const target=document.querySelector('#ti-anomaly-list');target.replaceChildren();payload.anomalies.forEach(row=>{const card=node('article','','ti-anomaly-card'),head=document.createElement('header');head.append(node('strong',row.label_zh),node('span',row.anomaly_type));card.append(head,node('p',row.fact_zh),node('p','证据：票据事实与合同事实已关联；下一步仅人工核对。'));target.append(card);});if(!payload.anomalies.length)target.append(node('div','当前筛选没有待复核异常。','ti-empty'));document.querySelector('#ti-anomaly-count').textContent=payload.anomaly_count+' 项';};
    const burdenCard=row=>{const card=node('article','','ti-mobile-card');card.append(node('h3',row.project_name_zh+' · '+row.business_type_zh));const grid=node('div','','ti-mobile-grid');[['销项税额',money(row.output_tax_cents)],['可用进项',money(row.eligible_input_tax_cents)],['管理净税负',money(row.management_net_tax_pressure_cents)],['完整性',row.completeness_zh]].forEach(([label,value])=>{const item=document.createElement('div');item.append(node('span',label),node('strong',value));grid.append(item);});card.append(grid,node('p',row.scope_limitation_zh));return card;};
    const renderBurden=payload=>{const body=document.querySelector('#ti-burden-body'),mobile=document.querySelector('#ti-burden-mobile');body.replaceChildren();mobile.replaceChildren();payload.project_burden.forEach(row=>{const tr=document.createElement('tr'),project=document.createElement('td');project.append(node('strong',row.project_name_zh),node('small',row.project_id));tr.append(project,node('td',row.business_type_zh),node('td',money(row.output_tax_cents)),node('td',money(row.eligible_input_tax_cents)),node('td',money(row.management_net_tax_pressure_cents)),node('td',row.completeness_zh),node('td',row.scope_limitation_zh));body.append(tr);mobile.append(burdenCard(row));});};
    const render=payload=>{last=payload;renderMetrics(payload);renderFacts(payload);renderAnomalies(payload);renderBurden(payload);feedback('核对完成：税率、含税状态、发票状态、异常证据和项目税负已对齐。');};
    const load=async()=>{if(!active()){view.hidden=true;delete document.body.dataset.taxInvoiceActive;return null;}view.hidden=false;document.body.dataset.taxInvoiceActive='true';feedback('正在核对税票事实…');const current=++sequence;try{const response=await fetch('/api/tax-invoices?'+params()),payload=await response.json();if(current!==sequence)return {stale_response_ignored:true};if(!response.ok||!payload.allowed){feedback(payload.reason_zh||'当前身份不能查看税票资料。',true);return payload;}render(payload);return payload;}catch(_){if(current===sequence)feedback('税票事实暂时无法读取，请稍后重试。',true);return null;}};
    ['#ti-project','#ti-business','#ti-direction','#ti-status','#ti-match','#context-company','#context-period','#identity-user'].forEach(selector=>document.querySelector(selector).addEventListener('change',()=>setTimeout(load,0)));window.addEventListener('popstate',load);window.KMFA_TAX_INVOICE_TEST={load,snapshot:()=>last,params:()=>params().toString()};load();
  })();
  </script>'''
    marker = '<section id="funds-report-view" class="funds-report-view" aria-labelledby="funds-report-title" hidden>'
    if marker not in html:
        raise RuntimeError("S18-P3 insertion point drifted")
    html = html.replace(marker, view + marker, 1)
    html = html.replace("  </style>", css + "  </style>", 1)
    html = html.replace("</body>", script + "</body>", 1)
    html = html.replace("<title>KMFA 关联与报告 · 经营工作台</title>", "<title>KMFA 税务与发票 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class TaxInvoiceHandler(base_runtime.RelationReportingHandler):
    server_version = "KMFATaxInvoice/1.5"

    def _authorised_query(self, query: dict[str, list[str]]) -> bool:
        allowed, identity = list_runtime._authorised(query)
        if not allowed:
            self._send_json(HTTPStatus.FORBIDDEN, {"allowed": False, "reason_zh": identity.get("reason_zh", "当前身份没有查看权限。")})
        return allowed

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == "/api/tax-invoices":
                if not self._authorised_query(query):
                    return
                self._send_json(HTTPStatus.OK, _payload(query))
                return
            if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico" or parsed.path.startswith("/reports/"):
                super().do_GET()
                return
            self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")
        except (KeyError, TypeError, homepage_kernel.HomepageError, list_kernel.ProjectListError, funds_kernel.FundsAccountsError, relation_kernel.RelationReportingError, kernel.TaxInvoiceError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})


class TaxInvoiceServer(base_runtime.RelationReportingServer):
    pass


def start_server(host: str = "127.0.0.1", port: int = 0, *, event_path: Path | str = workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH) -> tuple[TaxInvoiceServer, threading.Thread, str]:
    server = TaxInvoiceServer((host, port), TaxInvoiceHandler)
    server.journal = workflow_kernel.EventJournal(event_path)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s19p1-tax-invoice", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S19-P1 税务与发票页面")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--event-path", default=str(workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH))
    args = parser.parse_args()
    server = TaxInvoiceServer((args.host, args.port), TaxInvoiceHandler)
    server.journal = workflow_kernel.EventJournal(args.event_path)
    print(f"KMFA 税务与发票：http://{args.host}:{server.server_address[1]}/tax-policy", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
