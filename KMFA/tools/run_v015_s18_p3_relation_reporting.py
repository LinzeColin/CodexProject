#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S18-P3 关联与报告页面。"""

from __future__ import annotations

import argparse
import threading
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s17_p1_project_list as list_runtime
from KMFA.tools import run_v015_s17_p3_project_workflow as base_runtime
from KMFA.tools import run_v015_s18_p2_funds_accounts as funds_runtime
from KMFA.tools import v015_s16_p1_homepage as homepage_kernel
from KMFA.tools import v015_s17_p1_project_list as list_kernel
from KMFA.tools import v015_s17_p3_project_workflow as workflow_kernel
from KMFA.tools import v015_s18_p2_funds_accounts as funds_kernel
from KMFA.tools import v015_s18_p3_relation_reporting as kernel


def _first(query: dict[str, list[str]], key: str, default: str) -> str:
    return query.get(key, [default])[0]


def _payload(query: dict[str, list[str]], project_events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return kernel.relation_report_view(
        company_id=_first(query, "company_id", "demo-north"),
        period=_first(query, "period", "2026-07"),
        scenario_id=_first(query, "scenario", kernel.REPORT_SCENARIO_ID),
        verification_state=_first(query, "verification", "VERIFIED"),
        project_events=project_events,
    )


def _report_payload(query: dict[str, list[str]], project_events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return kernel.periodic_report(
        company_id=_first(query, "company_id", "demo-north"),
        period=_first(query, "period", "2026-07"),
        scenario_id=_first(query, "scenario", kernel.REPORT_SCENARIO_ID),
        verification_state=_first(query, "verification", "VERIFIED"),
        project_events=project_events,
    )


def render_html() -> str:
    html = funds_runtime.render_html()
    view = '''
    <section id="funds-report-view" class="funds-report-view" aria-labelledby="funds-report-title" hidden>
      <header class="rr-head">
        <div><span>关联与报告</span><h1 id="funds-report-title">利润和现金分开看，再决定内部复核顺序</h1><p>同一项目同时展示利润与资金占用；预警只显示必要信息，未核验资料自动降级。</p></div>
        <a class="rr-back" href="/funds">返回资金账户</a>
      </header>
      <div id="rr-feedback" class="rr-feedback" role="status" aria-live="polite">正在形成项目现金双视图…</div>
      <section id="rr-status" class="rr-status" aria-label="报告状态"></section>
      <section class="rr-controls" aria-label="报告查看条件">
        <label>资金情景<select id="rr-scenario"><option value="base">基准情景</option><option value="collection_delay" selected>回款延迟</option><option value="cost_pressure">成本压力</option></select></label>
        <label>资料状态<select id="rr-verification"><option value="VERIFIED">公开演示资料已核验</option><option value="UNVERIFIED">未核验降级演示</option></select></label>
        <div class="rr-export"><a id="rr-html-export" href="#">打开周期报告</a><a id="rr-csv-export" href="#">下载附表 CSV</a></div>
      </section>
      <section class="rr-basis" aria-labelledby="rr-basis-title"><div><h2 id="rr-basis-title">两套口径，不能互相替代</h2><p><strong>项目利润</strong>＝项目收入－项目成本。<strong>资金占用</strong>＝已开票未回款＋未开票节点金额；这里只覆盖应收与未开票，不代表完整项目现金流。</p></div><strong id="rr-basis-check">正在交叉核对</strong></section>
      <section class="rr-section" aria-labelledby="rr-dual-title">
        <div class="rr-section-head"><div><h2 id="rr-dual-title">项目利润与资金占用双视图</h2><p>利润好不等于现金充足；每个项目都单独显示口径限制。</p></div><strong id="rr-project-count">0 个项目</strong></div>
        <div class="rr-table-wrap"><table class="rr-table"><thead><tr><th>项目</th><th>收入</th><th>成本</th><th>毛利</th><th>已开票未回款</th><th>未开票节点</th><th>资金占用</th><th>口径限制</th></tr></thead><tbody id="rr-dual-body"></tbody></table></div>
        <div id="rr-dual-mobile" class="rr-mobile-list"></div>
      </section>
      <section class="rr-section" aria-labelledby="rr-alert-title">
        <div class="rr-section-head"><div><h2 id="rr-alert-title">回款、资金缺口与贷款到期预警</h2><p id="rr-threshold-version">阈值版本读取中</p></div><strong id="rr-alert-count">0 条提醒</strong></div>
        <div id="rr-alert-list" class="rr-alert-list"></div>
        <p class="rr-alert-note">提醒只用于内部复核，不显示完整客户、账户、合同、发票或金额明细，也不会自动发送。</p>
      </section>
      <p class="rr-disclaimer">当前页面和导出只使用公开合成资料验证口径、预警和一致性，不是正式经营报告，不发送提醒，也不执行付款。</p>
    </section>
    '''
    css = '''
    body[data-relation-active="true"] #page-view,
    body[data-relation-active="true"] #loading-view,
    body[data-relation-active="true"] #error-view,
    body[data-relation-active="true"] #not-found-view,
    body[data-relation-active="true"] #homepage-view,
    body[data-relation-active="true"] #project-list-view,
    body[data-relation-active="true"] #project-detail-view,
    body[data-relation-active="true"] #project-workflow-view,
    body[data-relation-active="true"] #receivables-view,
    body[data-relation-active="true"] #funds-view,
    body[data-relation-active="true"] #context-status,
    body[data-relation-active="true"] .identity-shell,
    body[data-relation-active="true"] .quick-shell,
    body[data-relation-active="true"] #access-workspace,
    body[data-relation-active="true"] #experience-workspace{display:none!important}
    .funds-report-view{margin:2px 0 28px}.rr-head{display:flex;justify-content:space-between;gap:22px;align-items:flex-start;margin-bottom:14px}.rr-head>div>span{color:#17648f;font-size:12px;font-weight:800}.rr-head h1{margin:4px 0 0;color:#173d57;font-size:29px;line-height:1.25}.rr-head p{margin:7px 0 0;color:#607684;font-size:14px}.rr-back,.rr-export a,.rr-alert-action{display:inline-flex;min-height:44px;align-items:center;justify-content:center;padding:0 13px;border:1px solid #9fb8c8;border-radius:6px;background:#fff;color:#245a7a;font-size:12px;font-weight:800;text-decoration:none}.rr-feedback{min-height:39px;margin-bottom:12px;padding:9px 12px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:6px;background:#edf6fb;color:#29475d;font-size:13px;line-height:1.5}.rr-feedback[data-state="error"]{border-color:#d7a6a6;background:#fff8f7;color:#7f2929}.rr-status{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:12px}.rr-metric{padding:14px;border:1px solid #d9e3e9;border-radius:8px;background:#fff}.rr-metric span{display:block;color:#607684;font-size:11px}.rr-metric strong{display:block;margin-top:5px;color:#173d57;font-size:17px}.rr-metric small{display:block;margin-top:4px;color:#607684;font-size:10px;line-height:1.4}.rr-metric[data-degraded="true"]{border-left:4px solid #b47a20;background:#fffbf2}.rr-controls{display:grid;grid-template-columns:220px 250px 1fr;gap:12px;align-items:end;margin-bottom:12px;padding:14px;border:1px solid #d8e2e8;border-radius:8px;background:#fff}.rr-controls label{display:grid;gap:5px;color:#536b7c;font-size:11px;font-weight:750}.rr-controls select{min-height:44px;padding:8px 9px;border:1px solid #b9cbd7;border-radius:6px;background:#fff;color:#29475d;font:inherit;font-size:13px}.rr-export{display:flex;justify-content:flex-end;gap:8px}.rr-export a:first-child{background:#245a7a;color:#fff}.rr-basis{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;margin-bottom:12px;padding:15px;border:1px solid #cbdbe4;border-left:4px solid #2f7aa4;border-radius:8px;background:#f6fafc}.rr-basis h2{margin:0 0 5px;color:#214d68;font-size:16px}.rr-basis p{margin:4px 0;color:#536b7c;font-size:12px;line-height:1.6}.rr-basis>strong{color:#276346;font-size:12px;white-space:nowrap}.rr-section{margin-bottom:12px;padding:16px;border:1px solid #d8e2e8;border-radius:8px;background:#fff}.rr-section-head{display:flex;justify-content:space-between;gap:15px;align-items:flex-start;margin-bottom:11px}.rr-section-head h2{margin:0;color:#214d68;font-size:18px}.rr-section-head p{margin:4px 0 0;color:#607684;font-size:12px}.rr-section-head>strong{color:#276346;font-size:12px}.rr-table-wrap{width:100%;overflow:auto;border:1px solid #dce5ea;border-radius:7px}.rr-table{width:100%;border-collapse:collapse;font-size:11px}.rr-table th,.rr-table td{padding:9px 8px;border-bottom:1px solid #e2e9ed;text-align:left;vertical-align:top;white-space:nowrap}.rr-table th{background:#f3f6f8;color:#40596b}.rr-table td:last-child{min-width:240px;white-space:normal;color:#607684}.rr-table strong{display:block;color:#29475d}.rr-table small{display:block;margin-top:3px;color:#607684}.rr-mobile-list{display:none}.rr-alert-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.rr-alert-card{padding:12px;border:1px solid #dce5ea;border-left:4px solid #b47a20;border-radius:7px;background:#fffbf2}.rr-alert-card[data-severity="HIGH"]{border-left-color:#b44741;background:#fff8f7}.rr-alert-card header{display:flex;justify-content:space-between;gap:8px}.rr-alert-card strong{color:#29475d;font-size:13px}.rr-alert-card span{color:#607684;font-size:10px}.rr-alert-card p{margin:7px 0 0;color:#536b7c;font-size:11px;line-height:1.55}.rr-alert-action{margin-top:9px;border-color:#6f9ab4;background:#f6fbfe}.rr-alert-note,.rr-disclaimer{color:#607684;font-size:12px;line-height:1.55}.rr-empty{padding:15px;border:1px dashed #c7d5de;border-radius:7px;color:#607684;text-align:center}.rr-mobile-card{padding:12px;border:1px solid #dce5ea;border-radius:7px;background:#f8fafb}.rr-mobile-card h3{margin:0 0 8px;color:#29475d;font-size:14px}.rr-mobile-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.rr-mobile-grid div{padding:8px;border:1px solid #e1e8ec;border-radius:6px;background:#fff}.rr-mobile-grid span{display:block;color:#607684;font-size:10px}.rr-mobile-grid strong{display:block;margin-top:3px;color:#29475d;font-size:12px}.rr-mobile-card p{margin:8px 0 0;color:#607684;font-size:11px;line-height:1.5}
    @media(max-width:1000px){.rr-status{grid-template-columns:repeat(2,1fr)}.rr-controls{grid-template-columns:1fr 1fr}.rr-export{grid-column:1/-1;justify-content:flex-start}.rr-alert-list{grid-template-columns:1fr}}
    @media(max-width:720px){.rr-head{display:grid}.rr-head h1{font-size:24px}.rr-back{justify-self:start}.rr-status{grid-template-columns:1fr 1fr}.rr-controls{grid-template-columns:1fr}.rr-export{display:grid;grid-template-columns:1fr 1fr}.rr-basis,.rr-section-head{display:grid}.rr-table-wrap{display:none}.rr-mobile-list{display:grid;gap:8px}.rr-alert-list{grid-template-columns:1fr}.rr-section{padding:13px}.rr-metric{padding:11px}.rr-metric strong{font-size:15px}}
    '''
    script = '''
  <script>
  (()=>{
    const view=document.querySelector('#funds-report-view');let last=null,sequence=0;
    const active=()=>location.pathname==='/funds-report';
    const text=(tag,value,className='')=>{const node=document.createElement(tag);node.textContent=value;if(className)node.className=className;return node;};
    const money=value=>value===null||value===undefined?'暂不可用':new Intl.NumberFormat('zh-CN',{style:'currency',currency:'CNY'}).format(value/100);
    const params=()=>{const value=new URLSearchParams({user_id:document.querySelector('#identity-user').value,role_id:document.querySelector('#identity-user').selectedOptions[0].dataset.role||'management',company_id:document.querySelector('#context-company').value,period:document.querySelector('#context-period').value,scenario:document.querySelector('#rr-scenario').value,verification:document.querySelector('#rr-verification').value});return value;};
    const setFeedback=(message,error=false)=>{const node=document.querySelector('#rr-feedback');node.textContent=message;if(error)node.dataset.state='error';else delete node.dataset.state;};
    const metric=(label,value,note,degraded=false)=>{const card=text('article','','rr-metric');if(degraded)card.dataset.degraded='true';card.append(text('span',label),text('strong',value),text('small',note));return card;};
    const renderStatus=payload=>{const r=payload.report,d=payload.dual_view,node=document.querySelector('#rr-status');node.replaceChildren(metric('报告状态',r.report_status_zh,r.report_degraded?'金额已隐藏':'公开演示资料',r.report_degraded),metric('项目',String(d.project_count),'利润与现金双视图'),metric('内部提醒',String(payload.alert_view.alert_count),'不自动发送'),metric('页面与附表差异',money(r.report_page_export_difference_cents),'允许差异 0 分'));};
    const projectCard=row=>{const card=text('article','','rr-mobile-card');card.append(text('h3',row.project_name_zh+' · '+row.project_id));const grid=text('div','','rr-mobile-grid');[['收入',money(row.revenue_cents)],['毛利',money(row.gross_profit_cents)],['未回款',money(row.open_receivable_cents)],['资金占用',money(row.cash_occupied_cents)]].forEach(([label,value])=>{const item=document.createElement('div');item.append(text('span',label),text('strong',value));grid.append(item);});card.append(grid,text('p',row.scope_limitation_zh));return card;};
    const renderDual=payload=>{const d=payload.dual_view,body=document.querySelector('#rr-dual-body'),mobile=document.querySelector('#rr-dual-mobile');body.replaceChildren();mobile.replaceChildren();d.rows.forEach(row=>{const tr=document.createElement('tr'),name=document.createElement('td');name.append(text('strong',row.project_name_zh),text('small',row.project_id+' · '+row.owner_zh));tr.append(name,text('td',money(row.revenue_cents)),text('td',money(row.cost_cents)),text('td',money(row.gross_profit_cents)),text('td',money(row.open_receivable_cents)),text('td',money(row.unbilled_cents)),text('td',money(row.cash_occupied_cents)),text('td',row.scope_limitation_zh));body.append(tr);mobile.append(projectCard(row));});document.querySelector('#rr-project-count').textContent=d.project_count+' 个项目';document.querySelector('#rr-basis-check').textContent=d.profit_cash_substitution_count===0&&d.cash_occupancy_reconciliation_difference_cents===0?'利润未替代现金，金额相差 0 分':'双视图口径不一致';};
    const renderAlerts=payload=>{const a=payload.alert_view,list=document.querySelector('#rr-alert-list');list.replaceChildren();if(!a.alerts.length){list.append(text('div',payload.verification_state==='UNVERIFIED'?'资料未核验，预警已暂停并隐藏明细。':'当前阈值下没有提醒。','rr-empty'));}a.alerts.forEach(row=>{const card=text('article','','rr-alert-card');card.dataset.severity=row.severity;const head=document.createElement('header');head.append(text('strong',row.title_zh),text('span',row.severity==='HIGH'?'高优先级':'需关注'));const route=new URL(row.detail_route,location.origin);const context=params();['user_id','role_id','company_id','period'].forEach(key=>route.searchParams.set(key,context.get(key)));const action=text('a',row.alert_type==='MAJOR_OVERDUE'?'打开回款明细':'打开资金明细','rr-alert-action');action.href=route.pathname+'?'+route.searchParams.toString();card.append(head,text('p',row.summary_zh),text('p',row.amount_band_zh+' · '+row.time_band_zh),text('p','内部下一步：'+row.internal_action_zh),action);list.append(card);});document.querySelector('#rr-alert-count').textContent=a.alert_count+' 条提醒';document.querySelector('#rr-threshold-version').textContent='阈值版本 '+a.threshold_version+'；变更后必须完整复测。';};
    const renderExports=()=>{const query=params().toString();document.querySelector('#rr-html-export').href='/reports/funds-receivables.html?'+query;document.querySelector('#rr-csv-export').href='/reports/funds-receivables.csv?'+query;};
    const render=payload=>{last=payload;renderStatus(payload);renderDual(payload);renderAlerts(payload);renderExports();setFeedback(payload.report.report_degraded?'资料未核验：报告已降级，金额和预警明细已隐藏。':'核对完成：利润、现金占用、预警、页面和附表已经逐项对齐。');};
    const load=async()=>{if(!active()){view.hidden=true;delete document.body.dataset.relationActive;return null;}view.hidden=false;document.body.dataset.relationActive='true';setFeedback('正在形成项目现金双视图…');const current=++sequence;try{const response=await fetch('/api/funds-report?'+params()),payload=await response.json();if(current!==sequence)return {stale_response_ignored:true};if(!response.ok||!payload.allowed){setFeedback(payload.reason_zh||'当前身份不能查看这些报告资料。',true);return payload;}render(payload);return payload;}catch(_){if(current===sequence)setFeedback('关联与报告暂时无法读取，请稍后重试。',true);return null;}};
    ['#rr-scenario','#rr-verification','#context-company','#context-period','#identity-user'].forEach(selector=>document.querySelector(selector).addEventListener('change',()=>setTimeout(load,0)));window.addEventListener('popstate',load);window.KMFA_RELATION_TEST={load,snapshot:()=>last,params:()=>params().toString(),setVerification:value=>{document.querySelector('#rr-verification').value=value;return load();},setScenario:value=>{document.querySelector('#rr-scenario').value=value;return load();}};load();
  })();
  </script>'''
    marker = '<section id="funds-view" class="funds-view" aria-labelledby="funds-title" hidden>'
    if marker not in html:
        raise RuntimeError("S18-P2 insertion point drifted")
    html = html.replace(marker, view + marker, 1)
    html = html.replace("  </style>", css + "  </style>", 1)
    html = html.replace("</body>", script + "</body>", 1)
    html = html.replace("<title>KMFA 资金与账户 · 经营工作台</title>", "<title>KMFA 关联与报告 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class RelationReportingHandler(funds_runtime.FundsAccountsHandler):
    server_version = "KMFARelationReporting/1.5"

    def _authorised_query(self, query: dict[str, list[str]]) -> bool:
        allowed, identity = list_runtime._authorised(query)
        if not allowed:
            self._send_json(
                HTTPStatus.FORBIDDEN,
                {"allowed": False, "reason_zh": identity.get("reason_zh", "当前身份没有查看权限。")},
            )
        return allowed

    def _send_download(self, body: bytes, content_type: str, filename: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == "/api/funds-report":
                if not self._authorised_query(query):
                    return
                self._send_json(HTTPStatus.OK, _payload(query, self.server.journal.read()))
                return
            if parsed.path == "/reports/funds-receivables.html":
                if not self._authorised_query(query):
                    return
                body = kernel.render_report_html(_report_payload(query, self.server.journal.read())).encode("utf-8")
                self._send(HTTPStatus.OK, body, "text/html; charset=utf-8")
                return
            if parsed.path == "/reports/funds-receivables.csv":
                if not self._authorised_query(query):
                    return
                body = kernel.export_appendix_csv(_report_payload(query, self.server.journal.read())).encode("utf-8-sig")
                self._send_download(body, "text/csv; charset=utf-8", "kmfa_funds_receivables_appendix.csv")
                return
            if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico" or parsed.path in base_runtime.REPORT_FILES:
                super().do_GET()
                return
            self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")
        except (
            KeyError,
            TypeError,
            homepage_kernel.HomepageError,
            list_kernel.ProjectListError,
            funds_kernel.FundsAccountsError,
            kernel.RelationReportingError,
        ) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})


class RelationReportingServer(funds_runtime.FundsAccountsServer):
    pass


def start_server(
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    event_path: Path | str = workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
) -> tuple[RelationReportingServer, threading.Thread, str]:
    server = RelationReportingServer((host, port), RelationReportingHandler)
    server.journal = workflow_kernel.EventJournal(event_path)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s18p3-relation", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S18-P3 关联与报告页面")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--event-path", default=str(workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH))
    args = parser.parse_args()
    server = RelationReportingServer((args.host, args.port), RelationReportingHandler)
    server.journal = workflow_kernel.EventJournal(args.event_path)
    print(f"KMFA 关联与报告：http://{args.host}:{server.server_address[1]}/funds-report", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
