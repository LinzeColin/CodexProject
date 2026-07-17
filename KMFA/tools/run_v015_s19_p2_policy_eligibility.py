#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S19-P2 政策资格与证据准备页面。"""

from __future__ import annotations

import argparse
import threading
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s17_p1_project_list as list_runtime
from KMFA.tools import run_v015_s19_p1_tax_invoice_facts as base_runtime
from KMFA.tools import v015_s17_p1_project_list as list_kernel
from KMFA.tools import v015_s17_p3_project_workflow as workflow_kernel
from KMFA.tools import v015_s19_p2_policy_eligibility as kernel


def _first(query: dict[str, list[str]], key: str, default: str) -> str:
    return query.get(key, [default])[0]


def _payload(query: dict[str, list[str]], events: list[dict[str, Any]]) -> dict[str, Any]:
    return kernel.policy_view(
        company_id=_first(query, "company_id", "demo-north"),
        period=_first(query, "period", "2026-07"),
        policy_id=_first(query, "policy_id", "POLICY-HIGH-TECH"),
        events=events,
    )


def render_html() -> str:
    html = base_runtime.render_html()
    view = r'''
    <section id="policy-eligibility-view" class="policy-eligibility-view" aria-labelledby="pe-title" hidden>
      <header class="pe-head">
        <div><span>税务与政策 · 政策资格</span><h1 id="pe-title">先核对规则和材料，再安排补证任务</h1><p>记录政策版本、来源日期和有效性；把知识产权、研发、人员、费用、收入和专项材料缺口交给明确负责人。</p></div>
        <nav class="s19-journey" aria-label="税务与政策步骤"><a class="pe-back" href="/tax-policy">上一步：税票事实</a><strong aria-current="step">2 政策材料</strong><a class="s19-next" href="/tax-policy-report">下一步：周期报告</a></nav>
      </header>
      <aside id="pe-boundary" class="pe-boundary"><strong>只提示缺口和风险，不判断申报资格</strong><span>不得伪造、倒签或包装材料；过期规则停用，没有已核验来源的任务不能完成。</span></aside>
      <div id="pe-feedback" class="pe-feedback" role="status" aria-live="polite">正在核对政策与材料…</div>
      <section class="pe-controls" aria-label="政策查看条件">
        <label>查看政策<select id="pe-policy-select"></select></label>
        <div><span>公司和期间</span><strong id="pe-scope">正在读取…</strong></div>
      </section>
      <section class="pe-section" aria-labelledby="pe-registry-title">
        <div class="pe-section-head"><div><h2 id="pe-registry-title">政策注册表</h2><p>每条规则保留版本、官方来源、来源日期、复核日期和使用状态。</p></div><strong id="pe-policy-count">0 条</strong></div>
        <div id="pe-registry" class="pe-registry"></div>
      </section>
      <section class="pe-section" aria-labelledby="pe-readiness-title">
        <div class="pe-section-head"><div><h2 id="pe-readiness-title">证据准备度</h2><p id="pe-readiness-summary">只列缺口和风险，不产生“符合”或“不符合”结论。</p></div><strong id="pe-gap-count">0 项待处理</strong></div>
        <div id="pe-readiness" class="pe-readiness"></div>
      </section>
      <section class="pe-section" aria-labelledby="pe-task-title">
        <div class="pe-section-head"><div><h2 id="pe-task-title">材料任务清单</h2><p>每项都显示负责人、期限、目标证据位置和来源状态。</p></div><strong id="pe-task-count">0 项</strong></div>
        <div id="pe-task-list" class="pe-tasks"></div>
      </section>
      <p class="pe-disclaimer">政策内容是截至 2026-07-16 核验的官方公开快照；企业材料是公开合成演示。运行时不联网、不访问原始资料、不替代主管部门、税务或专业签字。</p>
    </section>
    '''
    css = r'''
    body[data-policy-eligibility-active="true"] #page-view,
    body[data-policy-eligibility-active="true"] #loading-view,
    body[data-policy-eligibility-active="true"] #error-view,
    body[data-policy-eligibility-active="true"] #not-found-view,
    body[data-policy-eligibility-active="true"] #homepage-view,
    body[data-policy-eligibility-active="true"] #project-list-view,
    body[data-policy-eligibility-active="true"] #project-detail-view,
    body[data-policy-eligibility-active="true"] #project-workflow-view,
    body[data-policy-eligibility-active="true"] #receivables-view,
    body[data-policy-eligibility-active="true"] #funds-view,
    body[data-policy-eligibility-active="true"] #funds-report-view,
    body[data-policy-eligibility-active="true"] #tax-invoice-view,
    body[data-policy-eligibility-active="true"] #context-status,
    body[data-policy-eligibility-active="true"] .identity-shell,
    body[data-policy-eligibility-active="true"] .quick-shell,
    body[data-policy-eligibility-active="true"] #access-workspace,
    body[data-policy-eligibility-active="true"] #experience-workspace{display:none!important}
    .policy-eligibility-view{margin:2px 0 28px}.pe-head{display:flex;justify-content:space-between;gap:22px;align-items:flex-start;margin-bottom:12px}.pe-head>div>span{color:#245f75;font-size:12px;font-weight:800}.pe-head h1{margin:4px 0 0;color:#183f51;font-size:29px;line-height:1.25}.pe-head p{margin:7px 0 0;color:#607684;font-size:14px}.pe-back{display:inline-flex;min-height:44px;align-items:center;justify-content:center;padding:0 13px;border:1px solid #9fb8c8;border-radius:7px;background:#fff;color:#245a7a;font-size:12px;font-weight:800;text-decoration:none}.pe-boundary{display:flex;justify-content:space-between;gap:16px;margin-bottom:10px;padding:13px 15px;border:1px solid #d5b27c;border-left:4px solid #a86a17;border-radius:8px;background:#fffaf2;color:#654519}.pe-boundary strong{font-size:14px}.pe-boundary span{font-size:12px}.pe-feedback{min-height:40px;margin-bottom:11px;padding:9px 12px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:7px;background:#edf6fb;color:#29475d;font-size:13px;line-height:1.5}.pe-feedback[data-state="error"]{border-color:#d7a6a6;background:#fff8f7;color:#7f2929}.pe-controls{display:grid;grid-template-columns:minmax(260px,1fr) minmax(200px,.7fr);gap:10px;margin-bottom:11px;padding:13px;border:1px solid #d8e2e8;border-radius:8px;background:#fff}.pe-controls label,.pe-controls div{display:grid;gap:5px;color:#536b7c;font-size:11px;font-weight:750}.pe-controls select{min-height:44px;padding:8px;border:1px solid #b9cbd7;border-radius:6px;background:#fff;color:#29475d;font-size:12px}.pe-controls strong{display:flex;min-height:44px;align-items:center;color:#29475d;font-size:13px}.pe-section{margin-bottom:11px;padding:15px;border:1px solid #d8e2e8;border-radius:8px;background:#fff}.pe-section-head{display:flex;justify-content:space-between;gap:15px;align-items:flex-start;margin-bottom:10px}.pe-section-head h2{margin:0;color:#214d68;font-size:18px}.pe-section-head p{margin:4px 0 0;color:#607684;font-size:12px}.pe-section-head>strong{color:#276346;font-size:12px}.pe-registry{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.pe-policy-card{padding:12px;border:1px solid #d9e3e9;border-left:4px solid #3c7b96;border-radius:7px;background:#fbfcfd}.pe-policy-card[data-selected="true"]{background:#edf6fb;border-color:#82abc0}.pe-policy-card[data-refresh="BLOCKED_SUPERSEDED"],.pe-policy-card[data-refresh="REVIEW_OVERDUE"]{border-left-color:#a94747;background:#fff8f7}.pe-policy-card header{display:flex;justify-content:space-between;gap:8px}.pe-policy-card h3{margin:0;color:#29475d;font-size:14px}.pe-policy-card header strong{color:#276346;font-size:11px}.pe-policy-card[data-refresh="BLOCKED_SUPERSEDED"] header strong,.pe-policy-card[data-refresh="REVIEW_OVERDUE"] header strong{color:#9a3131}.pe-policy-card p{margin:6px 0 0;color:#607684;font-size:11px;line-height:1.5}.pe-policy-card a{display:inline-flex;min-height:44px;align-items:center;color:#17648f;font-size:11px;font-weight:800}.pe-readiness{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}.pe-readiness-card{padding:12px;border:1px solid #d9e3e9;border-radius:7px;background:#fbfcfd}.pe-readiness-card h3{margin:0;color:#29475d;font-size:14px}.pe-readiness-card strong{display:block;margin-top:7px;color:#8a5712;font-size:17px}.pe-readiness-card p{margin:5px 0 0;color:#607684;font-size:11px}.pe-tasks{display:grid;gap:8px}.pe-task-card{display:grid;grid-template-columns:minmax(190px,1.2fr) repeat(3,minmax(115px,.65fr)) auto;gap:10px;align-items:center;padding:12px;border:1px solid #d9e3e9;border-radius:7px;background:#fbfcfd}.pe-task-card h3{margin:0;color:#29475d;font-size:13px}.pe-task-card span{display:block;color:#607684;font-size:10px}.pe-task-card strong{display:block;margin-top:3px;color:#29475d;font-size:11px;overflow-wrap:anywhere}.pe-task-card button{min-height:44px;min-width:104px;padding:0 12px;border:0;border-radius:6px;background:#246c83;color:#fff;font-size:11px;font-weight:800;cursor:pointer}.pe-task-card[data-status="COMPLETED"]{background:#f1f8f4}.pe-task-card[data-status="COMPLETED"] button{background:#6d8176;cursor:default}.pe-empty{padding:14px;border:1px dashed #c7d5de;border-radius:7px;color:#607684;text-align:center}.pe-disclaimer{color:#607684;font-size:11px;line-height:1.5}
    @media(max-width:1050px){.pe-registry{grid-template-columns:1fr}.pe-readiness{grid-template-columns:repeat(2,1fr)}.pe-task-card{grid-template-columns:1fr 1fr 1fr}.pe-task-card>div:first-child{grid-column:1/-1}}
    @media(max-width:720px){.pe-head,.pe-boundary,.pe-section-head{display:grid}.pe-head h1{font-size:24px}.pe-back{justify-self:start}.pe-controls,.pe-readiness{grid-template-columns:1fr}.pe-section{padding:12px}.pe-task-card{grid-template-columns:1fr 1fr}.pe-task-card>div:first-child{grid-column:1/-1}.pe-task-card button{width:100%}}
    '''
    script = r'''
  <script>
  (()=>{
    const view=document.querySelector('#policy-eligibility-view');let last=null,sequence=0;
    const active=()=>location.pathname==='/policy-eligibility';
    const node=(tag,value='',className='')=>{const item=document.createElement(tag);item.textContent=value;if(className)item.className=className;return item;};
    const query=()=>new URLSearchParams({user_id:document.querySelector('#identity-user').value,role_id:document.querySelector('#identity-user').selectedOptions[0].dataset.role||'management',company_id:document.querySelector('#context-company').value,period:document.querySelector('#context-period').value,policy_id:document.querySelector('#pe-policy-select').value||'POLICY-HIGH-TECH'});
    const feedback=(message,error=false)=>{const target=document.querySelector('#pe-feedback');target.textContent=message;if(error)target.dataset.state='error';else delete target.dataset.state;};
    const renderRegistry=payload=>{const select=document.querySelector('#pe-policy-select'),selected=select.value,target=document.querySelector('#pe-registry');if(!select.options.length){payload.policy_registry.forEach(row=>select.append(new Option(row.policy_name_zh,row.policy_id)));select.value=payload.selected_policy_id;}else if(selected!==payload.selected_policy_id)select.value=payload.selected_policy_id;target.replaceChildren();payload.policy_registry.forEach(row=>{const card=node('article','','pe-policy-card');card.dataset.refresh=row.refresh_state;card.dataset.policyId=row.policy_id;card.dataset.selected=String(row.policy_id===payload.selected_policy_id);const head=document.createElement('header');head.append(node('h3',row.policy_name_zh),node('strong',row.refresh_state_zh));const source=document.createElement('a');source.href=row.source_url;source.target='_blank';source.rel='noreferrer';source.textContent='查看官方原文';card.append(head,node('p','版本：'+row.rule_version),node('p','来源日期：'+row.source_date+' · 生效：'+row.effective_from),node('p','最近核验：'+row.reviewed_at+' · 下次复核：'+row.next_review_due),source);target.append(card);});document.querySelector('#pe-policy-count').textContent=payload.summary.policy_count+' 条（'+payload.summary.blocked_policy_count+' 条停用）';};
    const renderReadiness=payload=>{const target=document.querySelector('#pe-readiness');target.replaceChildren();payload.readiness_categories.forEach(row=>{const card=node('article','','pe-readiness-card');card.dataset.category=row.category_id;card.append(node('h3',row.category_zh),node('strong',row.available_count+'/'+row.required_count+' 份来源可用'),node('p','缺失 '+row.missing_count+' · 待复核 '+row.review_count),node('p',row.guidance_zh));target.append(card);});const ready=payload.policy_readiness;document.querySelector('#pe-readiness-summary').textContent=ready.status_zh+'；不产生资格结论。'+payload.scope_limitation_zh;document.querySelector('#pe-gap-count').textContent=ready.missing_or_review_count+' 项待处理';};
    const renderTasks=payload=>{const target=document.querySelector('#pe-task-list');target.replaceChildren();payload.tasks.forEach(row=>{const card=node('article','','pe-task-card');card.dataset.taskId=row.task_id;card.dataset.status=row.status;const title=document.createElement('div');title.append(node('h3',row.title_zh),node('span',row.status_zh));const owner=document.createElement('div');owner.append(node('span','负责人'),node('strong',row.owner_zh));const due=document.createElement('div');due.append(node('span','期限'),node('strong',row.due_date));const source=document.createElement('div');source.append(node('span','证据位置'),node('strong',row.source_evidence_ref||'尚无来源材料'));const button=node('button',row.status==='COMPLETED'?'已完成':'核验并完成');button.type='button';button.dataset.completeTask=row.task_id;button.dataset.source=row.source_evidence_ref||'';button.disabled=row.status==='COMPLETED';card.append(title,owner,due,source,button);target.append(card);});if(!payload.tasks.length)target.append(node('div','该政策当前没有材料任务。','pe-empty'));document.querySelector('#pe-task-count').textContent=payload.tasks.length+' 项';};
    const render=payload=>{last=payload;document.querySelector('#pe-scope').textContent=payload.company_zh+' · '+payload.period;renderRegistry(payload);renderReadiness(payload);renderTasks(payload);feedback('核对完成：政策时效、材料缺口和负责人任务已对齐。');};
    const load=async()=>{if(!active()){view.hidden=true;delete document.body.dataset.policyEligibilityActive;return null;}view.hidden=false;document.body.dataset.policyEligibilityActive='true';feedback('正在核对政策与材料…');const current=++sequence;try{const response=await fetch('/api/policy-eligibility?'+query()),payload=await response.json();if(current!==sequence)return {stale_response_ignored:true};if(!response.ok||!payload.allowed){feedback(payload.reason_zh||'当前身份不能查看政策材料。',true);return payload;}render(payload);return payload;}catch(_){if(current===sequence)feedback('政策材料暂时无法读取，请稍后重试。',true);return null;}};
    const complete=async button=>{feedback('正在核验任务来源…');const params=query();const body={user_id:params.get('user_id'),role_id:params.get('role_id'),company_id:params.get('company_id'),period:params.get('period'),task_id:button.dataset.completeTask,source_evidence_ref:button.dataset.source,actor_ref:'public-demo-owner',idempotency_key:'ui-'+button.dataset.completeTask+'-'+params.get('company_id')+'-'+params.get('period')};const response=await fetch('/api/policy-tasks/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),payload=await response.json();if(!response.ok||!payload.allowed){feedback(payload.reason_zh||'任务不能完成。',true);return payload;}await load();feedback('任务已完成，来源和完成记录已绑定。');return payload;};
    document.querySelector('#pe-policy-select').addEventListener('change',()=>setTimeout(load,0));['#context-company','#context-period','#identity-user'].forEach(selector=>document.querySelector(selector).addEventListener('change',()=>setTimeout(load,0)));document.querySelector('#pe-task-list').addEventListener('click',event=>{const button=event.target.closest('button[data-complete-task]');if(button&&!button.disabled)complete(button);});window.addEventListener('popstate',load);window.KMFA_POLICY_ELIGIBILITY_TEST={load,complete,snapshot:()=>last,query:()=>query().toString()};load();
  })();
  </script>'''
    marker = '<section id="tax-invoice-view" class="tax-invoice-view" aria-labelledby="tax-invoice-title" hidden>'
    if marker not in html:
        raise RuntimeError("S19-P1 insertion point drifted")
    html = html.replace(marker, view + marker, 1)
    html = html.replace("  </style>", css + "  </style>", 1)
    html = html.replace("</body>", script + "</body>", 1)
    html = html.replace("<title>KMFA 税务与发票 · 经营工作台</title>", "<title>KMFA 政策资格 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class PolicyEligibilityHandler(base_runtime.TaxInvoiceHandler):
    server_version = "KMFAPolicyEligibility/1.5"

    def _authorised_query(self, query: dict[str, list[str]]) -> bool:
        allowed, identity = list_runtime._authorised(query)
        if not allowed:
            self._send_json(HTTPStatus.FORBIDDEN, {"allowed": False, "reason_zh": identity.get("reason_zh", "当前身份没有查看权限。")})
        return allowed

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == "/api/policy-eligibility":
                if not self._authorised_query(query):
                    return
                self._send_json(HTTPStatus.OK, _payload(query, self.server.policy_journal.read()))
                return
            if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico" or parsed.path.startswith("/reports/"):
                super().do_GET()
                return
            self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")
        except (KeyError, TypeError, list_kernel.ProjectListError, kernel.PolicyEligibilityError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})

    def do_POST(self) -> None:  # noqa: N802
        if urlsplit(self.path).path != "/api/policy-tasks/complete":
            super().do_POST()
            return
        try:
            value = self._json_body()
            query = self._body_query(value)
            if not self._authorised_query(query):
                return
            result = kernel.complete_policy_task(
                self.server.policy_journal,
                task_id=str(value.get("task_id", "")),
                company_id=str(value.get("company_id", "demo-north")),
                period=str(value.get("period", "2026-07")),
                source_evidence_ref=str(value.get("source_evidence_ref", "")),
                actor_ref=str(value.get("actor_ref", "public-demo-owner")),
                idempotency_key=str(value.get("idempotency_key", "")),
            )
            self._send_json(HTTPStatus.OK, {"allowed": True, **result})
        except (KeyError, TypeError, kernel.PolicyEligibilityError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})


class PolicyEligibilityServer(base_runtime.TaxInvoiceServer):
    policy_journal: kernel.PolicyTaskJournal


def start_server(host: str = "127.0.0.1", port: int = 0, *, event_path: Path | str = workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH) -> tuple[PolicyEligibilityServer, threading.Thread, str]:
    event_file = Path(event_path)
    server = PolicyEligibilityServer((host, port), PolicyEligibilityHandler)
    server.journal = workflow_kernel.EventJournal(event_file)
    server.policy_journal = kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s19p2-policy-eligibility", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S19-P2 政策资格页面")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--event-path", default=str(workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH))
    args = parser.parse_args()
    event_file = Path(args.event_path)
    server = PolicyEligibilityServer((args.host, args.port), PolicyEligibilityHandler)
    server.journal = workflow_kernel.EventJournal(event_file)
    server.policy_journal = kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    print(f"KMFA 政策资格：http://{args.host}:{server.server_address[1]}/policy-eligibility", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
