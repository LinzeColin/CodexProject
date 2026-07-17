#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S19-P3 税务与政策报告页面。"""

from __future__ import annotations

import argparse
import threading
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s19_p2_policy_eligibility as base_runtime
from KMFA.tools import v015_s17_p3_project_workflow as workflow_kernel
from KMFA.tools import v015_s19_p2_policy_eligibility as policy_kernel
from KMFA.tools import v015_s19_p3_tax_policy_reporting as kernel


def _first(query: dict[str, list[str]], key: str, default: str) -> str:
    return query.get(key, [default])[0]


def _payload(query: dict[str, list[str]], events: list[dict[str, Any]]) -> dict[str, Any]:
    return kernel.report_view(
        company_id=_first(query, "company_id", "demo-north"),
        period=_first(query, "period", "2026-07"),
        user_id=_first(query, "user_id", "demo-owner"),
        role_id=_first(query, "role_id", "management"),
        events=events,
    )


def render_html() -> str:
    html = base_runtime.render_html()
    view = r'''
    <section id="tax-policy-report-view" class="tpr-view" aria-labelledby="tpr-title" hidden>
      <header class="tpr-head">
        <div><span>税务与政策 · 周期报告</span><h1 id="tpr-title">先看需要确认什么，再由专业人员留下意见</h1><p>把税票异常和政策材料缺口放到同一份内部报告中，普通用户看结论边界，专业人员按需查看依据。</p></div>
        <nav class="s19-journey" aria-label="税务与政策步骤"><a class="tpr-back" href="/policy-eligibility">上一步：政策材料</a><strong aria-current="step">3 周期报告</strong></nav>
      </header>
      <aside id="tpr-boundary" class="tpr-boundary"><strong>仅供内部管理复核</strong><span>不是税务申报、资格认定或结果承诺；不会自动调税，也不会修改原始事实。</span></aside>
      <div id="tpr-feedback" class="tpr-feedback" role="status" aria-live="polite">正在整理本期报告…</div>
      <section id="tpr-metrics" class="tpr-metrics" aria-label="报告摘要"></section>

      <section class="tpr-section" aria-labelledby="tpr-tax-title">
        <div class="tpr-section-head"><div><h2 id="tpr-tax-title">税票：本期需要确认的事项</h2><p id="tpr-tax-copy">只解释事实差异和下一步，不计算补税或处罚。</p></div><strong id="tpr-tax-count">0 张</strong></div>
        <div id="tpr-risk-list" class="tpr-risk-list"></div>
      </section>

      <section class="tpr-section" aria-labelledby="tpr-policy-title">
        <div class="tpr-section-head"><div><h2 id="tpr-policy-title">政策：本周期材料准备报告</h2><p id="tpr-policy-copy">只报告已有、缺失和待核对材料，不给资格结论。</p></div><strong id="tpr-cycle">正在读取</strong></div>
        <div id="tpr-policy-summary" class="tpr-policy-summary"></div>
        <div id="tpr-category-list" class="tpr-category-list"></div>
      </section>

      <section class="tpr-section tpr-review-section" aria-labelledby="tpr-review-title">
        <div class="tpr-section-head"><div><h2 id="tpr-review-title">专业复核意见</h2><p>税务或审核角色可选择报告依据并追加意见；历史意见不能覆盖或删除。</p></div><strong id="tpr-review-count">0 条</strong></div>
        <div id="tpr-permission" class="tpr-permission">正在核对当前角色…</div>
        <form id="tpr-review-form" class="tpr-review-form">
          <label>报告依据<select id="tpr-basis" required></select></label>
          <label>复核意见<select id="tpr-opinion" required><option value="NEEDS_SOURCE_CHECK">需要补充或核对来源</option><option value="CONFIRMED_FOR_INTERNAL_USE">可继续用于内部管理复核</option><option value="REQUIRES_SPECIALIST_FOLLOWUP">需要专业人员继续跟进</option></select></label>
          <label class="tpr-comment">复核说明<textarea id="tpr-comment" minlength="4" maxlength="500" required>请核对当前报告依据后再继续处理。</textarea></label>
          <button id="tpr-submit" type="submit">追加复核意见</button>
        </form>
        <ol id="tpr-events" class="tpr-events"><li>尚无复核意见。</li></ol>
      </section>
      <p class="tpr-disclaimer">本页面只组合 S19-P1/P2 已验收的公开合成资料和官方政策快照；运行时不联网、不读取 raw、不执行开票、申报、认定或其他真实业务动作。</p>
    </section>
    '''
    css = r'''
    body[data-tax-policy-report-active="true"] #page-view,
    body[data-tax-policy-report-active="true"] #loading-view,
    body[data-tax-policy-report-active="true"] #error-view,
    body[data-tax-policy-report-active="true"] #not-found-view,
    body[data-tax-policy-report-active="true"] #homepage-view,
    body[data-tax-policy-report-active="true"] #project-list-view,
    body[data-tax-policy-report-active="true"] #project-detail-view,
    body[data-tax-policy-report-active="true"] #project-workflow-view,
    body[data-tax-policy-report-active="true"] #receivables-view,
    body[data-tax-policy-report-active="true"] #funds-view,
    body[data-tax-policy-report-active="true"] #funds-report-view,
    body[data-tax-policy-report-active="true"] #tax-invoice-view,
    body[data-tax-policy-report-active="true"] #policy-eligibility-view,
    body[data-tax-policy-report-active="true"] #context-status,
    body[data-tax-policy-report-active="true"] .quick-shell,
    body[data-tax-policy-report-active="true"] #access-workspace,
    body[data-tax-policy-report-active="true"] #experience-workspace{display:none!important}
    .tpr-view{margin:2px 0 30px}.tpr-head{display:flex;justify-content:space-between;align-items:flex-start;gap:22px;margin-bottom:12px}.tpr-head>div>span{color:#245f75;font-size:12px;font-weight:800}.tpr-head h1{margin:4px 0 0;color:#173d57;font-size:29px;line-height:1.25}.tpr-head p{margin:7px 0 0;max-width:850px;color:#607684;font-size:14px}.tpr-back{display:inline-flex;min-height:44px;align-items:center;justify-content:center;padding:0 13px;border:1px solid #9fb8c8;border-radius:7px;background:#fff;color:#245a7a;font-size:12px;font-weight:800;text-decoration:none}.tpr-boundary{display:flex;justify-content:space-between;gap:16px;margin-bottom:10px;padding:13px 15px;border:1px solid #d5b27c;border-left:4px solid #a86a17;border-radius:8px;background:#fffaf2;color:#654519}.tpr-boundary strong{font-size:14px}.tpr-boundary span{font-size:12px}.tpr-feedback{min-height:44px;margin-bottom:11px;padding:10px 12px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:7px;background:#edf6fb;color:#29475d;font-size:13px}.tpr-feedback[data-state="error"]{border-color:#d7a6a6;background:#fff8f7;color:#7f2929}.tpr-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-bottom:11px}.tpr-metric{padding:13px;border:1px solid #d9e3e9;border-radius:8px;background:#fff}.tpr-metric span{display:block;color:#607684;font-size:11px}.tpr-metric strong{display:block;margin-top:5px;color:#173d57;font-size:21px}.tpr-metric small{display:block;margin-top:4px;color:#607684;font-size:10px;line-height:1.45}.tpr-section{margin-bottom:11px;padding:15px;border:1px solid #d8e2e8;border-radius:8px;background:#fff}.tpr-section-head{display:flex;justify-content:space-between;gap:15px;align-items:flex-start;margin-bottom:11px}.tpr-section-head h2{margin:0;color:#214d68;font-size:18px}.tpr-section-head p{margin:4px 0 0;color:#607684;font-size:12px}.tpr-section-head>strong{color:#276346;font-size:12px}.tpr-risk-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.tpr-risk-card{padding:13px;border:1px solid #e2d5bd;border-left:4px solid #a86a17;border-radius:7px;background:#fffaf2}.tpr-risk-card header{display:flex;justify-content:space-between;gap:8px}.tpr-risk-card h3{margin:0;color:#654519;font-size:14px}.tpr-risk-card header span{color:#7a684b;font-size:10px}.tpr-risk-card p{margin:7px 0 0;color:#5d5447;font-size:11px;line-height:1.55}.tpr-risk-card details{margin-top:8px}.tpr-risk-card summary{min-height:44px;display:flex;align-items:center;color:#245f75;font-size:11px;font-weight:800;cursor:pointer}.tpr-risk-card ul{margin:3px 0 0;padding-left:18px;color:#607684;font-size:10px;overflow-wrap:anywhere}.tpr-policy-summary{margin-bottom:10px;padding:12px;border:1px solid #bfd2df;border-radius:7px;background:#f3f8fb;color:#29475d;font-size:13px}.tpr-policy-summary strong{display:block;margin-bottom:4px}.tpr-policy-summary span{display:block;color:#607684;font-size:11px}.tpr-category-list{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.tpr-category-card{padding:12px;border:1px solid #d9e3e9;border-radius:7px;background:#fbfcfd}.tpr-category-card h3{margin:0;color:#29475d;font-size:13px}.tpr-category-card strong{display:block;margin-top:7px;color:#8a5712;font-size:16px}.tpr-category-card p{margin:5px 0 0;color:#607684;font-size:10px;line-height:1.5}.tpr-review-section{border-color:#b9ccd8}.tpr-permission{margin-bottom:10px;padding:10px 12px;border:1px solid #c9d8e2;border-radius:7px;background:#f3f8fb;color:#29475d;font-size:12px}.tpr-permission[data-allowed="false"]{border-color:#d7c7aa;background:#fffaf2;color:#654519}.tpr-review-form{display:grid;grid-template-columns:minmax(180px,.8fr) minmax(220px,1fr) minmax(260px,1.4fr) auto;gap:10px;align-items:end}.tpr-review-form label{display:grid;gap:5px;color:#536b7c;font-size:11px;font-weight:750}.tpr-review-form select,.tpr-review-form textarea{width:100%;min-height:44px;padding:8px 10px;border:1px solid #b9cbd7;border-radius:6px;background:#fff;color:#29475d;font:inherit}.tpr-review-form textarea{height:72px;resize:vertical}.tpr-review-form button{min-height:44px;padding:0 14px;border:0;border-radius:6px;background:#246c83;color:#fff;font-size:12px;font-weight:800;cursor:pointer}.tpr-review-form button:disabled{background:#8599a5;cursor:not-allowed}.tpr-events{margin:14px 0 0;padding:12px 12px 12px 32px;border-top:1px solid #e1e8ec;color:#42596a;font-size:11px}.tpr-events li{padding:4px 0}.tpr-disclaimer{color:#607684;font-size:11px;line-height:1.5}
    @media(max-width:1050px){.tpr-metrics{grid-template-columns:repeat(2,1fr)}.tpr-category-list{grid-template-columns:repeat(2,1fr)}.tpr-review-form{grid-template-columns:1fr 1fr}.tpr-comment{grid-column:1/-1}.tpr-review-form button{justify-self:start}}
    @media(max-width:720px){.tpr-head,.tpr-boundary,.tpr-section-head{display:grid}.tpr-head h1{font-size:24px}.tpr-back{justify-self:start}.tpr-risk-list,.tpr-category-list,.tpr-review-form{grid-template-columns:1fr}.tpr-comment{grid-column:auto}.tpr-review-form button{width:100%}.tpr-section{padding:12px}.tpr-metrics{grid-template-columns:1fr 1fr}.tpr-metric{padding:10px}}
    '''
    script = r'''
  <script>
  (()=>{
    const view=document.querySelector('#tax-policy-report-view');let last=null,sequence=0,submitSequence=0;
    const active=()=>location.pathname==='/tax-policy-report';
    const node=(tag,value='',className='')=>{const item=document.createElement(tag);item.textContent=value;if(className)item.className=className;return item;};
    const identity=()=>window.KMFA_ROLE_TEST?.identity?.()||{user_id:'demo-owner',role_id:'management',company_id:document.querySelector('#context-company').value};
    const query=()=>{const who=identity();return new URLSearchParams({user_id:who.user_id,role_id:who.role_id,company_id:document.querySelector('#context-company').value,period:document.querySelector('#context-period').value});};
    const feedback=(message,error=false)=>{const target=document.querySelector('#tpr-feedback');target.textContent=message;if(error)target.dataset.state='error';else delete target.dataset.state;};
    const metric=(label,value,note)=>{const card=node('article','','tpr-metric');card.append(node('span',label),node('strong',value),node('small',note));return card;};
    const renderMetrics=payload=>{const tax=payload.tax_risk_summary,policy=payload.policy_preparation_report,target=document.querySelector('#tpr-metrics');target.replaceChildren(metric('需核对票据',String(tax.review_invoice_count),'另有 '+tax.matched_invoice_count+' 张已匹配'),metric('事实差异',String(tax.anomaly_count),'均保留两侧依据'),metric('政策材料待办',String(policy.missing_evidence_count+policy.review_evidence_count),policy.missing_evidence_count+' 份缺失 · '+policy.review_evidence_count+' 份待核对'),metric('当前可用规则',String(policy.current_policy_count),policy.blocked_policy_count+' 条历史规则已停用'));};
    const renderRisks=payload=>{const tax=payload.tax_risk_summary,target=document.querySelector('#tpr-risk-list');target.replaceChildren();tax.items.forEach(row=>{const card=node('article','','tpr-risk-card'),head=document.createElement('header');head.append(node('h3',row.issue_zh),node('span',row.invoice_id+' · '+row.project_name_zh));const details=document.createElement('details'),summary=node('summary','查看报告依据'),refs=document.createElement('ul');row.basis_refs.forEach(ref=>refs.append(node('li',ref)));details.append(summary,refs);card.append(head,node('p',row.impact_zh),node('p','下一步：'+row.next_step_zh),details);target.append(card);});document.querySelector('#tpr-tax-count').textContent=tax.review_invoice_count+' 张';document.querySelector('#tpr-tax-copy').textContent=tax.headline_zh+' '+tax.plain_language_zh;};
    const renderPolicy=payload=>{const policy=payload.policy_preparation_report,summary=document.querySelector('#tpr-policy-summary'),target=document.querySelector('#tpr-category-list');summary.replaceChildren(node('strong',policy.headline_zh),node('span',policy.scope_limitation_zh));target.replaceChildren();policy.categories.forEach(row=>{const card=node('article','','tpr-category-card');card.append(node('h3',row.category_zh),node('strong',row.available_count+'/'+row.required_count+' 份已有来源'),node('p','缺失 '+row.missing_count+' · 待核对 '+row.review_count),node('p',row.next_step_zh));target.append(card);});document.querySelector('#tpr-cycle').textContent=policy.cycle_zh+' · 截至 '+policy.report_as_of;};
    const renderReview=payload=>{const permission=payload.review_permission,banner=document.querySelector('#tpr-permission'),button=document.querySelector('#tpr-submit'),basis=document.querySelector('#tpr-basis'),events=document.querySelector('#tpr-events');banner.dataset.allowed=String(permission.allowed);banner.textContent=permission.role_label_zh+'：'+permission.reason_zh+' 意见只追加事件，不改原始事实。';button.disabled=!permission.allowed;basis.disabled=!permission.allowed;document.querySelector('#tpr-opinion').disabled=!permission.allowed;document.querySelector('#tpr-comment').disabled=!permission.allowed;const selected=basis.value;basis.replaceChildren();payload.review_basis.forEach(row=>basis.append(new Option(row.label_zh,row.basis_ref)));if([...basis.options].some(option=>option.value===selected))basis.value=selected;events.replaceChildren();if(!payload.review_events.length)events.append(node('li','尚无复核意见。'));else payload.review_events.slice().reverse().forEach(row=>events.append(node('li',row.actor_role_label_zh+' · '+row.opinion_zh+' · '+row.comment_zh+' · 依据 '+row.basis_refs.length+' 项')));document.querySelector('#tpr-review-count').textContent=payload.review_event_count+' 条';};
    const render=payload=>{last=payload;renderMetrics(payload);renderRisks(payload);renderPolicy(payload);renderReview(payload);feedback('报告已整理：税票事项、政策缺口和专业复核权限均已对齐。');};
    const load=async()=>{if(!active()){view.hidden=true;delete document.body.dataset.taxPolicyReportActive;return null;}view.hidden=false;document.body.dataset.taxPolicyReportActive='true';feedback('正在整理本期报告…');const current=++sequence;try{const response=await fetch('/api/tax-policy-report?'+query()),payload=await response.json();if(current!==sequence)return {stale_response_ignored:true};if(!response.ok||!payload.allowed){feedback(payload.reason_zh||'当前身份不能查看报告。',true);return payload;}render(payload);return payload;}catch(_){if(current===sequence)feedback('报告暂时无法读取，请稍后重试。',true);return null;}};
    const submit=async()=>{if(!last||!last.review_permission.allowed)return null;const who=identity(),body={report_id:last.report_id,company_id:last.company_id,period:last.period,user_id:who.user_id,role_id:who.role_id,opinion_code:document.querySelector('#tpr-opinion').value,comment_zh:document.querySelector('#tpr-comment').value,basis_refs:[document.querySelector('#tpr-basis').value],idempotency_key:'ui-'+last.report_id+'-'+String(++submitSequence)+'-'+String(Date.now())};feedback('正在追加复核意见…');const response=await fetch('/api/tax-policy-reviews',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),payload=await response.json();if(!response.ok||!payload.allowed){feedback(payload.reason_zh||'复核意见未记录。',true);return payload;}await load();feedback('复核意见已追加；原始事实没有改变。');return payload;};
    document.querySelector('#tpr-review-form').addEventListener('submit',event=>{event.preventDefault();submit();});['#context-company','#context-period','#identity-user'].forEach(selector=>document.querySelector(selector).addEventListener('change',()=>setTimeout(load,80)));document.querySelector('#switch-role').addEventListener('click',()=>setTimeout(load,160));window.addEventListener('popstate',load);window.KMFA_TAX_POLICY_REPORT_TEST={load,submit,snapshot:()=>last,query:()=>query().toString()};load();
  })();
  </script>'''
    marker = '<section id="policy-eligibility-view" class="policy-eligibility-view" aria-labelledby="pe-title" hidden>'
    if marker not in html:
        raise RuntimeError("S19-P2 insertion point drifted")
    html = html.replace(marker, view + marker, 1)
    html = html.replace("  </style>", css + "  </style>", 1)
    html = html.replace("</body>", script + "</body>", 1)
    html = html.replace("<title>KMFA 政策资格 · 经营工作台</title>", "<title>KMFA 税务与政策报告 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class TaxPolicyReportingHandler(base_runtime.PolicyEligibilityHandler):
    server_version = "KMFATaxPolicyReporting/1.5"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == "/api/tax-policy-report":
                value = _payload(query, self.server.review_journal.read())
                self._send_json(HTTPStatus.OK if value.get("allowed") else HTTPStatus.FORBIDDEN, value)
                return
            if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico" or parsed.path.startswith("/reports/"):
                super().do_GET()
                return
            self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")
        except (KeyError, TypeError, kernel.TaxPolicyReportingError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})

    def do_POST(self) -> None:  # noqa: N802
        if urlsplit(self.path).path != "/api/tax-policy-reviews":
            super().do_POST()
            return
        try:
            value = self._json_body()
            refs = value.get("basis_refs", [])
            if not isinstance(refs, list):
                raise kernel.TaxPolicyReportingError("复核依据格式不正确")
            result = kernel.record_professional_review(
                self.server.review_journal,
                report_id=str(value.get("report_id", "")),
                company_id=str(value.get("company_id", "demo-north")),
                period=str(value.get("period", "2026-07")),
                user_id=str(value.get("user_id", "")),
                role_id=str(value.get("role_id", "")),
                opinion_code=str(value.get("opinion_code", "")),
                comment_zh=str(value.get("comment_zh", "")),
                basis_refs=[str(item) for item in refs],
                idempotency_key=str(value.get("idempotency_key", "")),
            )
            self._send_json(HTTPStatus.OK, result)
        except (KeyError, TypeError, kernel.TaxPolicyReportingError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})


class TaxPolicyReportingServer(base_runtime.PolicyEligibilityServer):
    review_journal: kernel.ProfessionalReviewJournal


def start_server(
    host: str = "127.0.0.1", port: int = 0,
    *, event_path: Path | str = workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
) -> tuple[TaxPolicyReportingServer, threading.Thread, str]:
    event_file = Path(event_path)
    server = TaxPolicyReportingServer((host, port), TaxPolicyReportingHandler)
    server.journal = workflow_kernel.EventJournal(event_file)
    server.policy_journal = policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s19p3-tax-policy-reporting", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S19-P3 税务与政策报告")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--event-path", default=str(workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH))
    args = parser.parse_args()
    event_file = Path(args.event_path)
    server = TaxPolicyReportingServer((args.host, args.port), TaxPolicyReportingHandler)
    server.journal = workflow_kernel.EventJournal(event_file)
    server.policy_journal = policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    print(f"KMFA 税务与政策报告：http://{args.host}:{server.server_address[1]}/tax-policy-report", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
