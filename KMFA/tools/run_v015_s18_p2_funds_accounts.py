#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S18-P2 资金与账户页面。"""

from __future__ import annotations

import argparse
import threading
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s17_p1_project_list as list_runtime
from KMFA.tools import run_v015_s17_p3_project_workflow as base_runtime
from KMFA.tools import run_v015_s18_p1_receivables_collections as receivables_runtime
from KMFA.tools import v015_s16_p1_homepage as homepage_kernel
from KMFA.tools import v015_s17_p1_project_list as list_kernel
from KMFA.tools import v015_s17_p3_project_workflow as workflow_kernel
from KMFA.tools import v015_s18_p2_funds_accounts as kernel


def _first(query: dict[str, list[str]], key: str, default: str) -> str:
    return query.get(key, [default])[0]


def _payload(query: dict[str, list[str]]) -> dict[str, Any]:
    return kernel.funds_view(
        company_id=_first(query, "company_id", "demo-north"),
        period=_first(query, "period", "2026-07"),
        scenario_id=_first(query, "scenario", "base"),
    )


def render_html() -> str:
    html = receivables_runtime.render_html()
    view = '''
    <section id="funds-view" class="funds-view" aria-labelledby="funds-title" hidden>
      <header class="funds-head">
        <div><span>资金与账户</span><h1 id="funds-title">账户先核清，再看未来四周现金</h1><p>余额是演示事实；未来数值分为计划与情景假设，不代表确定结果。</p></div>
        <div class="funds-cutoff"><span>余额日期</span><strong id="funds-cutoff">2026-07-15</strong></div>
      </header>
      <div id="funds-feedback" class="funds-feedback" role="status" aria-live="polite">正在核对当前公司的资金账户…</div>
      <section id="funds-summary" class="funds-summary" aria-label="资金摘要"></section>
      <section class="funds-basis" aria-labelledby="funds-basis-title">
        <div><h2 id="funds-basis-title">先分清三种数字</h2><p><strong>事实</strong>：已有余额或已确认收支。<strong>计划</strong>：预计发生但尚未成为事实。<strong>情景假设</strong>：只用于压力测试，不会写回事实。</p></div>
        <label>查看情景<select id="funds-scenario"><option value="base">基准情景</option><option value="collection_delay">回款延迟</option><option value="cost_pressure">成本压力</option></select></label>
      </section>
      <section class="funds-section" aria-labelledby="accounts-title">
        <div class="funds-section-head"><div><h2 id="accounts-title">银行账户事实</h2><p id="accounts-source">公开合成银行余额与流水</p></div><strong id="accounts-check">账户勾稽中</strong></div>
        <div class="funds-table-wrap"><table class="funds-table"><thead><tr><th>银行 / 账户</th><th>脱敏账号</th><th>期初</th><th>流入</th><th>流出</th><th>余额</th><th>日期 / 来源</th></tr></thead><tbody id="accounts-body"></tbody></table></div>
        <div id="accounts-mobile" class="funds-mobile-list"></div>
        <div id="unknown-warning" class="unknown-warning"></div>
      </section>
      <section class="funds-section" aria-labelledby="forecast-title">
        <div class="funds-section-head"><div><h2 id="forecast-title">未来四周现金预测</h2><p id="forecast-note">每一列都明确标出事实、计划和假设。</p></div><strong id="forecast-check">情景勾稽中</strong></div>
        <div class="funds-table-wrap"><table class="funds-table forecast-table"><thead><tr><th>期间</th><th>事实收 / 支</th><th>计划收 / 支</th><th>情景调整</th><th>事实余额</th><th>计划余额</th><th>情景预计余额</th></tr></thead><tbody id="forecast-body"></tbody></table></div>
        <div id="forecast-mobile" class="funds-mobile-list"></div>
      </section>
      <section class="funds-section" aria-labelledby="loans-title">
        <div class="funds-section-head"><div><h2 id="loans-title">贷款到期与资金缺口</h2><p>只提供内部复核提示，不连接银行、不发起还款或付款。</p></div><strong id="loans-count">0 笔贷款</strong></div>
        <div class="loan-grid"><div><h3>贷款计划</h3><div id="loan-list" class="loan-list"></div></div><div><h3>逐期资金缺口</h3><div id="gap-list" class="gap-list"></div></div></div>
      </section>
      <p class="funds-disclaimer">当前页面只使用公开合成资料验证账户勾稽和情景逻辑，不代表真实资金状况，也不执行任何支付。</p>
    </section>'''
    css = '''
    body[data-funds-active="true"] #page-view,
    body[data-funds-active="true"] #loading-view,
    body[data-funds-active="true"] #error-view,
    body[data-funds-active="true"] #not-found-view,
    body[data-funds-active="true"] #homepage-view,
    body[data-funds-active="true"] #project-list-view,
    body[data-funds-active="true"] #project-detail-view,
    body[data-funds-active="true"] #project-workflow-view,
    body[data-funds-active="true"] #receivables-view,
    body[data-funds-active="true"] #context-status,
    body[data-funds-active="true"] .identity-shell,
    body[data-funds-active="true"] .quick-shell,
    body[data-funds-active="true"] #access-workspace,
    body[data-funds-active="true"] #experience-workspace{display:none!important}
    .funds-view{margin:2px 0 28px}.funds-head{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;margin-bottom:14px}.funds-head>div:first-child>span{color:#17648f;font-size:12px;font-weight:800}.funds-head h1{margin:4px 0 0;color:#173d57;font-size:29px;line-height:1.25}.funds-head p{margin:7px 0 0;color:#607684;font-size:14px}.funds-cutoff{display:grid;justify-items:end;color:#607684;font-size:12px}.funds-cutoff strong{margin-top:4px;color:#173d57;font-size:15px}.funds-feedback{min-height:39px;margin-bottom:13px;padding:9px 12px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:6px;background:#edf6fb;color:#29475d;font-size:13px;line-height:1.5}.funds-feedback[data-state="error"]{border-color:#d7a6a6;background:#fff8f7;color:#7f2929}
    .funds-summary{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-bottom:13px}.funds-metric{padding:14px;border:1px solid #d9e3e9;border-radius:8px;background:#fff}.funds-metric span{display:block;color:#607684;font-size:11px}.funds-metric strong{display:block;margin-top:5px;color:#173d57;font-size:18px}.funds-metric small{display:block;margin-top:4px;color:#607684;font-size:10px;line-height:1.4}.funds-metric[data-alert="true"]{border-left:4px solid #b44741;background:#fff8f7}.funds-metric[data-plan="true"]{border-left:4px solid #b47a20;background:#fffbf2}
    .funds-basis{display:grid;grid-template-columns:1fr 260px;gap:18px;align-items:end;margin-bottom:13px;padding:15px;border:1px solid #cbdbe4;border-radius:8px;background:#f6fafc}.funds-basis h2{margin:0 0 5px;color:#214d68;font-size:16px}.funds-basis p{margin:4px 0;color:#536b7c;font-size:12px;line-height:1.6}.funds-basis label{display:grid;gap:5px;color:#536b7c;font-size:11px;font-weight:750}.funds-basis select{min-height:44px;padding:8px 9px;border:1px solid #b9cbd7;border-radius:6px;background:#fff;color:#29475d;font:inherit;font-size:13px}
    .funds-section{margin-bottom:13px;padding:16px;border:1px solid #d8e2e8;border-radius:8px;background:#fff}.funds-section-head{display:flex;justify-content:space-between;gap:15px;align-items:flex-start;margin-bottom:11px}.funds-section-head h2{margin:0;color:#214d68;font-size:18px}.funds-section-head p{margin:4px 0 0;color:#607684;font-size:12px}.funds-section-head>strong{color:#276346;font-size:12px}.funds-table-wrap{width:100%;overflow:auto;border:1px solid #dce5ea;border-radius:7px}.funds-table{width:100%;border-collapse:collapse;font-size:11px}.funds-table th,.funds-table td{padding:9px 8px;border-bottom:1px solid #e2e9ed;text-align:left;vertical-align:top;white-space:nowrap}.funds-table th{background:#f3f6f8;color:#40596b}.funds-table tr:last-child td{border-bottom:0}.funds-table .numeric{text-align:right}.funds-table strong{display:block;color:#29475d}.funds-table small{display:block;margin-top:3px;color:#607684}.funds-mobile-list{display:none}.unknown-warning{margin-top:11px;padding:11px 12px;border:1px solid #dec897;border-left:4px solid #b47a20;border-radius:7px;background:#fffbf2;color:#624b22;font-size:12px;line-height:1.55}
    .lane{display:inline-block;margin-bottom:4px;padding:3px 6px;border-radius:999px;font-size:10px;font-weight:800}.lane[data-kind="fact"]{background:#e8f7ee;color:#246040}.lane[data-kind="plan"]{background:#fff1d5;color:#76551c}.lane[data-kind="assumption"]{background:#eee9fb;color:#5c438c}.scenario-value{color:#6a4b8e;font-weight:800}.loan-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:14px}.loan-grid h3{margin:0 0 9px;color:#40596b;font-size:14px}.loan-list,.gap-list{display:grid;gap:8px}.loan-card,.gap-card{padding:12px;border:1px solid #dce5ea;border-radius:7px;background:#f8fafb}.loan-card header,.gap-card header{display:flex;justify-content:space-between;gap:8px}.loan-card strong,.gap-card strong{color:#29475d;font-size:13px}.loan-card span,.gap-card span{color:#607684;font-size:11px}.loan-card p,.gap-card p{margin:7px 0 0;color:#536b7c;font-size:11px;line-height:1.55}.gap-card[data-alert="true"]{border-left:4px solid #b44741;background:#fff8f7}.funds-disclaimer{margin:12px 2px 0;color:#607684;font-size:12px}
    @media(max-width:1000px){.funds-summary{grid-template-columns:repeat(3,1fr)}}
    @media(max-width:760px){.funds-head{display:block}.funds-head h1{font-size:25px}.funds-cutoff{justify-items:start;margin-top:10px}.funds-summary,.funds-basis,.loan-grid{grid-template-columns:1fr}.funds-table-wrap{display:none}.funds-mobile-list{display:grid;gap:9px}.funds-mobile-card{padding:12px;border:1px solid #dce5ea;border-radius:7px;background:#fbfcfd}.funds-mobile-card h3{margin:0;color:#29475d;font-size:14px}.funds-mobile-card>p{margin:4px 0 9px;color:#607684;font-size:11px}.funds-mobile-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px}.funds-mobile-grid div{padding:8px;border-radius:5px;background:#f0f5f7}.funds-mobile-grid span{display:block;color:#607684;font-size:10px}.funds-mobile-grid strong{display:block;margin-top:3px;color:#29475d;font-size:11px}.funds-section-head{display:block}.funds-section-head>strong{display:inline-block;margin-top:6px}}
    @media(prefers-reduced-motion:reduce){.funds-view *{transition:none!important;animation:none!important}}
    '''
    script = '''
  <script>
  (()=>{'use strict';
    const view=document.querySelector('#funds-view'),feedback=document.querySelector('#funds-feedback');let last=null,sequence=0;
    const active=()=>location.pathname==='/funds';const text=(tag,value,className='')=>{const node=document.createElement(tag);node.textContent=value==null?'':String(value);if(className)node.className=className;return node;};
    const money=cents=>{const sign=cents<0?'-':'';const value=Math.abs(cents),yuan=Math.floor(value/100),fen=String(value%100).padStart(2,'0');return sign+'¥'+yuan.toLocaleString('zh-CN')+'.'+fen;};
    const identity=()=>window.KMFA_ROLE_TEST.identity(),context=()=>window.KMFA_TEST.context();
    const params=()=>{const who=identity(),scope=context();return new URLSearchParams({user_id:who.user_id,role_id:who.role_id,company_id:scope.company,period:scope.period,scenario:document.querySelector('#funds-scenario').value});};
    const setFeedback=(message,error=false)=>{feedback.textContent=message;if(error)feedback.dataset.state='error';else delete feedback.dataset.state;};
    const metric=(label,result,note,kind='')=>{const node=text('div','','funds-metric');if(kind)node.dataset[kind]='true';node.append(text('span',label),text('strong',result),text('small',note));return node;};
    const renderSummary=payload=>{const s=payload.summary,shell=document.querySelector('#funds-summary');shell.replaceChildren(metric('可汇总余额',money(s.available_cash_cents),s.known_account_count+' 个已确认账户'),metric('排除账户',s.excluded_unknown_account_count+' 个','主体或账户不明，不计合计','plan'),metric('四周情景余额',money(s.four_week_scenario_cash_cents),'情景预计，不是确定值','plan'),metric('90 天内到期',s.loan_due_within_90_days_count+' 笔','仅做内部复核'),metric('最大资金缺口',money(s.maximum_funding_gap_cents),'按当前情景测算',s.maximum_funding_gap_cents?'alert':''));};
    const accountCard=row=>{const card=text('article','','funds-mobile-card');card.append(text('h3',row.bank_name_zh+' · '+row.account_name_zh),text('p',row.masked_account+' · '+row.balance_date));const grid=text('div','','funds-mobile-grid');[['期初',money(row.opening_cents)],['流入',money(row.inflow_cents)],['流出',money(row.outflow_cents)],['余额',money(row.closing_cents)]].forEach(([label,value])=>{const item=document.createElement('div');item.append(text('span',label),text('strong',value));grid.append(item);});card.append(grid);return card;};
    const renderAccounts=payload=>{const a=payload.accounts,body=document.querySelector('#accounts-body'),mobile=document.querySelector('#accounts-mobile');body.replaceChildren();mobile.replaceChildren();a.accounts.forEach(row=>{const tr=document.createElement('tr'),name=document.createElement('td'),source=document.createElement('td');name.append(text('strong',row.bank_name_zh),text('small',row.account_name_zh));source.append(text('strong',row.balance_date),text('small',row.source_zh));tr.append(name,text('td',row.masked_account),text('td',money(row.opening_cents),'numeric'),text('td',money(row.inflow_cents),'numeric'),text('td',money(row.outflow_cents),'numeric'),text('td',money(row.closing_cents),'numeric'),source);body.append(tr);mobile.append(accountCard(row));});document.querySelector('#accounts-check').textContent=a.account_reconciliation_difference_cents===0&&a.bank_reconciliation_difference_cents===0?'账户与银行汇总相差 0 分':'账户勾稽不一致';document.querySelector('#unknown-warning').textContent='有 '+a.unknown_account_count+' 个演示账户的主体或账户尚未确认，已排除在余额合计之外；待确认金额计入合计为 '+money(a.unknown_amount_in_total_cents)+'。';};
    const lane=(label,kind)=>{const node=text('span',label,'lane');node.dataset.kind=kind;return node;};
    const forecastCard=row=>{const card=text('article','','funds-mobile-card');card.append(text('h3',row.period_label_zh),text('p','情景预计余额不是确定值'));const grid=text('div','','funds-mobile-grid');[['事实收 / 支',money(row.fact_inflow_cents)+' / '+money(row.fact_outflow_cents)],['计划收 / 支',money(row.plan_inflow_cents)+' / '+money(row.plan_outflow_cents)],['情景调整',money(row.assumption_adjustment_cents)],['情景预计余额',money(row.scenario_closing_cents)]].forEach(([label,value])=>{const item=document.createElement('div');item.append(text('span',label),text('strong',value));grid.append(item);});card.append(grid);return card;};
    const renderForecast=payload=>{const f=payload.forecast,body=document.querySelector('#forecast-body'),mobile=document.querySelector('#forecast-mobile');body.replaceChildren();mobile.replaceChildren();f.rows.forEach(row=>{const tr=document.createElement('tr'),facts=document.createElement('td'),plans=document.createElement('td'),assumption=document.createElement('td'),scenario=document.createElement('td');facts.append(lane('事实','fact'),text('small',money(row.fact_inflow_cents)+' / '+money(row.fact_outflow_cents)));plans.append(lane('计划','plan'),text('small',money(row.plan_inflow_cents)+' / '+money(row.plan_outflow_cents)));assumption.append(lane('假设','assumption'),text('small',money(row.assumption_adjustment_cents)));scenario.append(text('strong',money(row.scenario_closing_cents),'scenario-value'),text('small','不是确定值'));tr.append(text('td',row.period_label_zh),facts,plans,assumption,text('td',money(row.confirmed_closing_cents),'numeric'),text('td',money(row.planned_closing_cents),'numeric'),scenario);body.append(tr);mobile.append(forecastCard(row));});document.querySelector('#forecast-note').textContent=f.scenario_label_zh+'：'+f.assumption_events[0].assumption_zh;document.querySelector('#forecast-check').textContent=f.scenario_difference_cents===0?'情景计算相差 0 分':'情景计算不一致';};
    const renderLoans=payload=>{const p=payload.funding_plan,loans=document.querySelector('#loan-list'),gaps=document.querySelector('#gap-list');loans.replaceChildren();gaps.replaceChildren();p.loans.forEach(row=>{const card=text('article','','loan-card'),head=document.createElement('header');head.append(text('strong',row.loan_name_zh),text('span',row.days_to_maturity+' 天后到期'));card.append(head,text('p','本金 '+money(row.principal_cents)+' · 预计利息 '+money(row.estimated_interest_cents)+' · 保证金 '+money(row.margin_cents)+' · '+row.annual_rate_zh),text('p','内部下一步：'+row.action_zh));loans.append(card);});p.funding_rows.forEach(row=>{const card=text('article','','gap-card');if(row.funding_gap_cents)card.dataset.alert='true';const head=document.createElement('header');head.append(text('strong',row.period_label_zh),text('span',row.status_zh));card.append(head,text('p','情景余额 '+money(row.scenario_closing_cents)+' · 安全线 '+money(row.minimum_safe_cash_cents)+' · 缺口 '+money(row.funding_gap_cents)),text('p','内部下一步：'+row.action_zh));gaps.append(card);});document.querySelector('#loans-count').textContent=p.loan_count+' 笔贷款';};
    const render=payload=>{last=payload;document.querySelector('#funds-cutoff').textContent=payload.balance_date;renderSummary(payload);renderAccounts(payload);renderForecast(payload);renderLoans(payload);setFeedback('核对完成：账户余额已勾稽，事实、计划和情景假设已分开。');};
    const load=async()=>{if(!active()){view.hidden=true;delete document.body.dataset.fundsActive;return null;}view.hidden=false;document.body.dataset.fundsActive='true';setFeedback('正在核对当前公司的资金账户…');const current=++sequence;try{const response=await fetch('/api/funds?'+params()),payload=await response.json();if(current!==sequence)return {stale_response_ignored:true};if(!response.ok||!payload.allowed){setFeedback(payload.reason_zh||'当前身份不能查看这些资金资料。',true);return payload;}render(payload);return payload;}catch(_){if(current===sequence)setFeedback('资金与账户暂时无法读取，请稍后重试。',true);return null;}};
    document.querySelector('#funds-scenario').addEventListener('change',load);['#context-company','#context-period','#identity-user'].forEach(selector=>document.querySelector(selector).addEventListener('change',()=>setTimeout(load,0)));window.addEventListener('popstate',load);window.KMFA_FUNDS_TEST={load,snapshot:()=>last,params:()=>params().toString(),setScenario:value=>{document.querySelector('#funds-scenario').value=value;return load();}};load();
  })();
  </script>'''
    marker = '<section id="receivables-view" class="receivables-view" aria-labelledby="receivables-title" hidden>'
    if marker not in html:
        raise RuntimeError("S18-P1 insertion point drifted")
    html = html.replace(marker, view + marker, 1)
    html = html.replace("  </style>", css + "  </style>", 1)
    html = html.replace("</body>", script + "</body>", 1)
    html = html.replace("<title>KMFA 回款与应收 · 经营工作台</title>", "<title>KMFA 资金与账户 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class FundsAccountsHandler(receivables_runtime.ReceivablesHandler):
    server_version = "KMFAFundsAccounts/1.5"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/api/funds":
            query = parse_qs(parsed.query)
            try:
                allowed, identity = list_runtime._authorised(query)
                if not allowed:
                    self._send_json(HTTPStatus.FORBIDDEN, {"allowed": False, "reason_zh": identity.get("reason_zh", "当前身份没有查看权限。")})
                    return
                self._send_json(HTTPStatus.OK, _payload(query))
            except (KeyError, TypeError, homepage_kernel.HomepageError, list_kernel.ProjectListError, kernel.FundsAccountsError) as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})
            return
        if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico" or parsed.path in base_runtime.REPORT_FILES:
            super().do_GET()
            return
        self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")


class FundsAccountsServer(base_runtime.ProjectWorkflowServer):
    pass


def start_server(
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    event_path: Path | str = workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
) -> tuple[FundsAccountsServer, threading.Thread, str]:
    server = FundsAccountsServer((host, port), FundsAccountsHandler)
    server.journal = workflow_kernel.EventJournal(event_path)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s18p2-funds", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S18-P2 资金与账户页面")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--event-path", default=str(workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH))
    args = parser.parse_args()
    server = FundsAccountsServer((args.host, args.port), FundsAccountsHandler)
    server.journal = workflow_kernel.EventJournal(args.event_path)
    print(f"KMFA 资金与账户：http://{args.host}:{server.server_address[1]}/funds", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
