#!/usr/bin/env python3
"""Run the KMFA v1.5 S21-P1 local report-model workbench."""

from __future__ import annotations

import argparse
import re
import threading
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s20_p3_recalculation_publication as base_runtime
from KMFA.tools import v015_s21_p1_report_model as kernel


_REPORT_ROUTE = re.compile(r"^/api/report-models/(REPORT-[A-Z0-9-]+-V\d{4})$")
_AUDIENCE_ROUTE = re.compile(r"^/api/report-models/(REPORT-[A-Z0-9-]+-V\d{4})/audiences/(management|professional)$")
_REVISION_ROUTE = re.compile(r"^/api/report-models/(REPORT-[A-Z0-9-]+-V\d{4})/revisions$")


def render_html() -> str:
    html = base_runtime.render_html()
    view = r'''
    <section id="report-model-view" class="rm-view" aria-labelledby="rm-title" hidden>
      <header class="rm-head"><div><span>经营报告 · 第一步</span><h1 id="rm-title">先确定报告期间、版本和阅读层次</h1><p>每个版本都保留当时使用的资料与计算口径。修订会新增版本，不会覆盖历史。</p></div><a href="/recalculation-publication">返回数据更新结果</a></header>
      <nav class="s21-journey" aria-label="经营报告流程步骤"><a href="/report-model" aria-current="step"><span>1</span><strong>报告模型</strong><small>期间、版本与受众</small></a><a href="/report-generation"><span>2</span><strong>生成报告</strong><small>网页、PDF 与附表</small></a><a href="/report-workflow"><span>3</span><strong>复核发布</strong><small>审批、修订与报告中心</small></a></nav>
      <aside class="rm-boundary"><strong>本步骤的边界</strong><span>这里只建立报告模型，不生成网页、PDF 或表格，也不审批或发布报告。</span></aside>
      <section class="rm-summary" aria-label="报告模型概览"><article><span>报告期间</span><strong>周 · 月 · 季 · 半年 · 年</strong></article><article><span>报告系列</span><strong id="rm-family-count">0</strong></article><article><span>保留版本</span><strong id="rm-version-count">0</strong></article></section>
      <div id="rm-feedback" class="rm-feedback" role="status" aria-live="polite">正在读取报告模型…</div>
      <section class="rm-card" aria-labelledby="rm-create-title"><div class="rm-card-head"><div><h2 id="rm-create-title">1. 新建报告初版</h2><p>先选公司、期间和资料完整情况。相同期间已有版本时，只能创建修订。</p></div></div><form id="rm-create-form" class="rm-form">
        <label>公司<select id="rm-company"><option value="demo-north">北区示例公司</option><option value="demo-west">西区示例公司</option></select></label>
        <label>报告类型<select id="rm-period-kind"><option value="WEEKLY">周报</option><option value="MONTHLY" selected>月报</option><option value="QUARTERLY">季报</option><option value="HALF_YEAR">半年报</option><option value="YEARLY">年报</option></select></label>
        <label>报告期间<input id="rm-period-key" value="2026-07" aria-describedby="rm-period-help"><small id="rm-period-help">例如 2026-07</small></label>
        <label>资料情况<select id="rm-readiness"><option value="COMPLETE">六类关键资料齐备</option><option value="PENDING">税务与政策资料待确认</option><option value="MISSING">财务与资金资料缺失</option></select></label>
        <button class="rm-primary" type="submit">建立报告初版</button>
      </form></section>
      <div class="rm-layout">
        <section class="rm-card rm-history-card" aria-labelledby="rm-history-title"><div class="rm-card-head"><div><h2 id="rm-history-title">2. 版本历史</h2><p>所有版本按时间倒序保留。</p></div><span id="rm-history-count">0 个版本</span></div><div id="rm-history" class="rm-history"></div></section>
        <section id="rm-detail-card" class="rm-card" aria-labelledby="rm-detail-title" hidden><div class="rm-card-head"><div><h2 id="rm-detail-title">3. 查看报告结构与限制</h2><p id="rm-version-label">—</p></div><span id="rm-period-label">—</span></div>
          <section class="rm-binding" aria-label="版本绑定"><div><span>已绑定资料</span><strong id="rm-source-count">0 / 6</strong></div><div><span>已绑定计算口径</span><strong id="rm-formula-count">0</strong></div><div><span>历史处理</span><strong>新增版本，不覆盖</strong></div></section>
          <aside id="rm-trust" class="rm-trust"><strong id="rm-trust-status">—</strong><p id="rm-trust-copy"></p><ul id="rm-limitations"></ul></aside>
          <nav class="rm-audience" aria-label="报告阅读层次"><button type="button" data-audience="MANAGEMENT" aria-pressed="true">管理摘要</button><button type="button" data-audience="PROFESSIONAL" aria-pressed="false">专业附表</button></nav>
          <div id="rm-sections" class="rm-sections"></div>
          <form id="rm-revision-form" class="rm-revision"><label>修订原因<input id="rm-revision-reason" value="补充本期管理说明并保留上一版本"></label><button type="submit">创建新修订版本</button></form>
        </section>
      </div>
      <p class="rm-stop">本次只完成报告模型。报告生成与可视化、导出、复核、批准和发布留到后续独立步骤。</p>
    </section>
    '''
    css = r'''
    body[data-report-model-active="true"] main>section:not(#report-model-view),body[data-report-model-active="true"] #context-status,body[data-report-model-active="true"] .identity-shell,body[data-report-model-active="true"] .quick-shell,body[data-report-model-active="true"] #access-workspace,body[data-report-model-active="true"] #experience-workspace{display:none!important}
    .s21-journey{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}.s21-journey a{display:grid;grid-template-columns:34px 1fr;grid-template-rows:auto auto;column-gap:9px;min-height:52px;padding:9px 11px;border:1px solid #cbd9e1;border-radius:8px;background:#fff;color:#31576b;text-decoration:none}.s21-journey a[aria-current="step"]{border-color:#246c83;background:#edf6f9}.s21-journey span{grid-row:1/3;align-self:center;display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:#246c83;color:#fff;font-weight:800}.s21-journey strong{align-self:end;font-size:12px}.s21-journey small{color:#657c89;font-size:10px}
    .rm-view{margin:2px 0 32px;color:#29475d}.rm-head{display:flex;justify-content:space-between;align-items:flex-start;gap:18px}.rm-head span{font-size:12px;font-weight:800;color:#17648f}.rm-head h1{margin:4px 0;font-size:30px;color:#173d57}.rm-head p{max-width:760px;margin:6px 0;color:#607684;font-size:13px}.rm-head a,.rm-view button{display:inline-flex;min-height:44px;align-items:center;justify-content:center;padding:0 14px;border:1px solid #9fb8c8;border-radius:7px;background:#fff;color:#245a7a;font:inherit;font-size:12px;font-weight:800;text-decoration:none;cursor:pointer}.rm-boundary{display:flex;justify-content:space-between;gap:14px;margin:12px 0;padding:12px 14px;border:1px solid #d5b27c;border-left:4px solid #a86a17;border-radius:8px;background:#fffaf2;color:#654519;font-size:12px}.rm-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:11px 0}.rm-summary article,.rm-card{padding:15px;border:1px solid #d8e2e8;border-radius:9px;background:#fff}.rm-summary span,.rm-binding span{display:block;color:#607684;font-size:11px}.rm-summary strong{display:block;margin-top:5px;color:#173d57;font-size:20px}.rm-feedback{min-height:44px;padding:11px 13px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:7px;background:#edf6fb;font-size:13px}.rm-feedback[data-state="error"]{border-color:#d7a6a6;background:#fff8f7;color:#7f2929}.rm-feedback[data-state="success"]{border-color:#9fc5ae;background:#f3faf5;color:#276346}.rm-card{margin-top:11px}.rm-card-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;margin-bottom:11px}.rm-card h2{margin:0;color:#214d68;font-size:18px}.rm-card-head p{margin:5px 0 0;color:#607684;font-size:11px}.rm-form{display:grid;grid-template-columns:1fr 1fr 1fr 1.2fr auto;gap:9px;align-items:end}.rm-form label,.rm-revision label{display:grid;gap:5px;font-size:11px;font-weight:800}.rm-form select,.rm-form input,.rm-revision input{min-height:44px;padding:0 10px;border:1px solid #b9cbd7;border-radius:7px;background:#fff;font:inherit}.rm-form small{color:#607684;font-weight:400}.rm-primary{border:0!important;background:#246c83!important;color:#fff!important}.rm-layout{display:grid;grid-template-columns:minmax(280px,.8fr) minmax(440px,1.4fr);gap:11px}.rm-history{display:grid;gap:7px}.rm-history button{display:grid;width:100%;height:auto;min-height:64px;justify-content:start;text-align:left;padding:10px;background:#f8fbfc}.rm-history button[aria-current="true"]{border-color:#246c83;background:#edf7fa}.rm-history strong,.rm-history span{display:block}.rm-history span{margin-top:4px;color:#607684;font-size:10px}.rm-binding{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.rm-binding div{padding:10px;border-radius:7px;background:#f7fafb}.rm-binding strong{display:block;margin-top:4px;color:#214d68;font-size:13px}.rm-trust{margin:10px 0;padding:12px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:7px;background:#f7fbfd}.rm-trust[data-complete="false"]{border-color:#d5b27c;background:#fffaf2}.rm-trust p,.rm-trust li{font-size:11px;line-height:1.55}.rm-trust ul{margin:6px 0 0;padding-left:18px}.rm-audience{display:flex;gap:8px;margin:10px 0}.rm-audience button[aria-pressed="true"]{border-color:#246c83;background:#246c83;color:#fff}.rm-sections{display:grid;gap:7px}.rm-section{padding:11px;border:1px solid #dce5ea;border-radius:7px}.rm-section h3{margin:0;color:#214d68;font-size:13px}.rm-section p{margin:5px 0 0;color:#607684;font-size:11px;line-height:1.5}.rm-revision{display:grid;grid-template-columns:1fr auto;gap:9px;align-items:end;margin-top:12px;padding-top:12px;border-top:1px solid #dce5ea}.rm-stop{color:#607684;font-size:11px}
    @media(max-width:1000px){.rm-form{grid-template-columns:1fr 1fr}.rm-layout{grid-template-columns:1fr}.rm-head,.rm-boundary{display:grid}.rm-head a{justify-self:start}}
    @media(max-width:520px){.s21-journey,.rm-summary,.rm-form,.rm-binding,.rm-revision{grid-template-columns:1fr}.rm-head h1{font-size:25px}.rm-view button{width:100%}.rm-audience{display:grid;grid-template-columns:1fr 1fr}}
    '''
    script = r'''
    <script>
    (()=>{'use strict';if(location.pathname!=='/report-model')return;document.body.dataset.reportModelActive='true';const view=document.querySelector('#report-model-view');view.hidden=false;
      const state={list:null,current:null,audience:null},feedback=document.querySelector('#rm-feedback');let requestNumber=0;
      const api=async(path,init={})=>{const response=await fetch(path,init),value=await response.json();if(!response.ok)throw Object.assign(new Error(value.message_zh||'请求失败'),{payload:value,status:response.status});return value};
      const post=(path,body)=>api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const say=(text,kind='')=>{feedback.textContent=text;if(kind)feedback.dataset.state=kind;else delete feedback.dataset.state};
      const examples={WEEKLY:['2026-W29','例如 2026-W29'],MONTHLY:['2026-07','例如 2026-07'],QUARTERLY:['2026-Q3','例如 2026-Q3'],HALF_YEAR:['2026-H1','例如 2026-H1'],YEARLY:['2026','例如 2026']};
      const renderAudience=value=>{state.audience=value;document.querySelectorAll('.rm-audience button').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.audience===value.audience)));const root=document.querySelector('#rm-sections');root.replaceChildren();value.sections.forEach(row=>{const card=document.createElement('article');card.className='rm-section';const title=document.createElement('h3'),copy=document.createElement('p');title.textContent=row.visible_order+'. '+row.title_zh;copy.textContent=row.purpose_zh;card.append(title,copy);root.append(card)})};
      const loadAudience=async audience=>{if(!state.current)return null;const value=await api('/api/report-models/'+state.current.report_version_id+'/audiences/'+audience.toLowerCase());renderAudience(value);return value};
      const renderDetail=async report=>{state.current=report;document.querySelector('#rm-detail-card').hidden=false;document.querySelector('#rm-version-label').textContent=report.report_version_id+' · '+report.version_label_zh;document.querySelector('#rm-period-label').textContent=report.period.period_label_zh;document.querySelector('#rm-source-count').textContent=report.trust_and_limitations.available_input_count+' / 6';document.querySelector('#rm-formula-count').textContent=String(report.formula_bindings.length);const trust=report.trust_and_limitations,box=document.querySelector('#rm-trust');box.dataset.complete=String(trust.complete_report_claim_allowed);document.querySelector('#rm-trust-status').textContent=trust.status_zh;document.querySelector('#rm-trust-copy').textContent=trust.explanation_zh;const limits=document.querySelector('#rm-limitations');limits.replaceChildren();trust.limitations_zh.forEach(text=>{const li=document.createElement('li');li.textContent=text;limits.append(li)});await loadAudience('MANAGEMENT')};
      const renderList=value=>{state.list=value;document.querySelector('#rm-family-count').textContent=String(value.report_family_count);document.querySelector('#rm-version-count').textContent=String(value.report_version_count);document.querySelector('#rm-history-count').textContent=value.report_version_count+' 个版本';const root=document.querySelector('#rm-history');root.replaceChildren();value.reports.forEach(row=>{const button=document.createElement('button');button.type='button';button.dataset.version=row.report_version_id;button.setAttribute('aria-current',String(state.current?.report_version_id===row.report_version_id));const title=document.createElement('strong'),copy=document.createElement('span');title.textContent=row.period.period_label_zh+' · '+row.version_label_zh;copy.textContent=row.trust_and_limitations.status_zh+' · '+row.recorded_at;button.append(title,copy);button.addEventListener('click',()=>renderDetail(row).catch(error=>say(error.message,'error')));root.append(button)});};
      const load=async preferred=>{const value=await api('/api/report-models?company_id='+encodeURIComponent(document.querySelector('#rm-company').value));renderList(value);const target=preferred?value.reports.find(row=>row.report_version_id===preferred):value.reports[0];if(target)await renderDetail(target);else{state.current=null;document.querySelector('#rm-detail-card').hidden=true}say(value.report_version_count?'报告模型已读取，历史版本均保留。':'尚无报告版本，请建立初版。','success');return value};
      const create=async()=>{const value=await post('/api/report-models',{company_id:document.querySelector('#rm-company').value,period_kind:document.querySelector('#rm-period-kind').value,period_key:document.querySelector('#rm-period-key').value,readiness_case:document.querySelector('#rm-readiness').value,created_by:'公开演示负责人',idempotency_key:'browser-create-'+Date.now()+'-'+(++requestNumber)});await load(value.report_version_id);say('报告初版已建立；资料和计算口径已绑定。','success');return value};
      const revise=async()=>{if(!state.current)return null;const value=await post('/api/report-models/'+state.current.report_version_id+'/revisions',{revision_reason_zh:document.querySelector('#rm-revision-reason').value,created_by:'公开演示负责人',idempotency_key:'browser-revise-'+Date.now()+'-'+(++requestNumber)});await load(value.report_version_id);say('新修订版本已建立；上一版本保持不变。','success');return value};
      document.querySelector('#rm-create-form').addEventListener('submit',event=>{event.preventDefault();create().catch(error=>say(error.message,'error'))});document.querySelector('#rm-revision-form').addEventListener('submit',event=>{event.preventDefault();revise().catch(error=>say(error.message,'error'))});document.querySelector('#rm-period-kind').addEventListener('change',event=>{const [value,help]=examples[event.target.value];document.querySelector('#rm-period-key').value=value;document.querySelector('#rm-period-help').textContent=help});document.querySelector('#rm-company').addEventListener('change',()=>load().catch(error=>say(error.message,'error')));document.querySelectorAll('.rm-audience button').forEach(button=>button.addEventListener('click',()=>loadAudience(button.dataset.audience).catch(error=>say(error.message,'error'))));
      window.KMFA_REPORT_MODEL_TEST={snapshot:()=>structuredClone(state),load,create,revise,loadAudience};load().catch(error=>say(error.message,'error'));
    })();
    </script>
    '''
    html = html.replace("</main>", view + "</main>", 1)
    html = html.replace("</style>", css + "</style>", 1)
    html = html.replace("</body>", script + "</body>", 1)
    html = html.replace(
        '<p class="rp-stop">S20-P3 在本地验收后停止。S20 整体复审、GitHub 上传与 App 重装均不在本页面执行。</p>',
        '<p class="rp-stop">数据更新完成后，可进入 <a href="/report-model">报告模型</a>，先确定期间、版本和阅读层次。</p>',
    )
    html = html.replace("<title>KMFA 重新计算与发布联动</title>", "<title>KMFA 报告模型 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


def _readiness_sources(value: str, publication_version: str) -> list[dict[str, Any]]:
    case = str(value or "COMPLETE").upper()
    if case == "COMPLETE":
        return kernel.default_source_bindings(publication_version=publication_version)
    if case == "PENDING":
        return kernel.default_source_bindings(publication_version=publication_version, pending=("tax_and_policy",))
    if case == "MISSING":
        return kernel.default_source_bindings(publication_version=publication_version, missing=("finance_and_funds",))
    raise kernel.ReportModelError("READINESS_CASE_INVALID", "资料情况不正确")


class ReportModelHandler(base_runtime.RecalculationHandler):
    server_version = "KMFAReportModel/1.5"

    @property
    def report_models(self) -> kernel.ReportModelJournal:
        return self.server.report_model_journal  # type: ignore[attr-defined,no-any-return]

    def _publication_version(self) -> str:
        return str(self.server.recalculation_workbench.current_publication()["publication_version_id"])  # type: ignore[attr-defined,no-any-return]

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path, query = parsed.path, parse_qs(parsed.query)
        try:
            if path == "/api/report-model/options":
                self._send_json(HTTPStatus.OK, kernel.options_contract())
                return
            if path == "/api/report-models":
                self._send_json(HTTPStatus.OK, self.report_models.list(company_id=str(query.get("company_id", [""])[0]) or None))
                return
            match = _AUDIENCE_ROUTE.fullmatch(path)
            if match:
                self._send_json(HTTPStatus.OK, self.report_models.audience(match.group(1), match.group(2)))
                return
            match = _REPORT_ROUTE.fullmatch(path)
            if match:
                self._send_json(HTTPStatus.OK, self.report_models.get(match.group(1)))
                return
            if path.startswith("/api/report-models/"):
                raise kernel.ReportModelError("REPORT_VERSION_NOT_FOUND", "没有找到这个报告版本", status=404)
            if path.startswith("/api/") or path == "/favicon.ico" or path.startswith("/reports/"):
                super().do_GET()
                return
            self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")
        except kernel.ReportModelError as error:
            self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            if path == "/api/report-models":
                body = self._json_body()
                sources = body.get("source_bindings")
                if sources is None:
                    sources = _readiness_sources(str(body.get("readiness_case", "COMPLETE")), self._publication_version())
                formulas = body.get("formula_bindings") or kernel.default_formula_bindings()
                value = self.report_models.create(
                    company_id=str(body.get("company_id", "")), period_kind=str(body.get("period_kind", "")),
                    period_key=str(body.get("period_key", "")), source_bindings=sources,
                    formula_bindings=formulas, created_by=str(body.get("created_by", "")),
                    idempotency_key=str(body.get("idempotency_key", "")),
                )
                self._send_json(HTTPStatus.CREATED, value)
                return
            match = _REVISION_ROUTE.fullmatch(path)
            if match:
                body = self._json_body()
                sources = body.get("source_bindings")
                if sources is None and body.get("readiness_case"):
                    sources = _readiness_sources(str(body["readiness_case"]), self._publication_version())
                value = self.report_models.revise(
                    match.group(1), source_bindings=sources, formula_bindings=body.get("formula_bindings"),
                    revision_reason_zh=str(body.get("revision_reason_zh", "")),
                    created_by=str(body.get("created_by", "")), idempotency_key=str(body.get("idempotency_key", "")),
                )
                self._send_json(HTTPStatus.CREATED, value)
                return
            super().do_POST()
        except (TypeError, kernel.ReportModelError) as error:
            if isinstance(error, kernel.ReportModelError):
                self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})
            else:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "code": "INVALID_REQUEST", "message_zh": "请求格式不正确"})


class ReportModelServer(base_runtime.RecalculationServer):
    report_model_journal: kernel.ReportModelJournal


def start_server(
    host: str = "127.0.0.1", port: int = 0, *,
    event_path: Path | str = base_runtime.base_runtime.workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
    data_root: Path | str = base_runtime.base_runtime.data_update_kernel.DEFAULT_RUNTIME_ROOT,
    confirmation_event_path: Path | str = base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    publication_event_path: Path | str = base_runtime.kernel.DEFAULT_EVENT_PATH,
    report_model_event_path: Path | str = kernel.DEFAULT_EVENT_PATH,
) -> tuple[ReportModelServer, threading.Thread, str]:
    event_file = Path(event_path)
    server = ReportModelServer((host, port), ReportModelHandler)
    server.journal = base_runtime.base_runtime.workflow_kernel.EventJournal(event_file)
    server.policy_journal = base_runtime.base_runtime.policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = base_runtime.base_runtime.reporting_kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    server.data_update_store = base_runtime.base_runtime.data_update_kernel.DataUpdateStore(data_root)
    server.confirmation_workbench = base_runtime.base_runtime.kernel.ConfirmationWorkbench(confirmation_event_path)
    server.recalculation_workbench = base_runtime.kernel.RecalculationPublicationWorkbench(confirmation_event_path, publication_event_path)
    server.report_model_journal = kernel.ReportModelJournal(report_model_event_path)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s21p1-report-model", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S21-P1 报告模型工作台")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--event-path", default=str(base_runtime.base_runtime.workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH))
    parser.add_argument("--data-root", default=str(base_runtime.base_runtime.data_update_kernel.DEFAULT_RUNTIME_ROOT))
    parser.add_argument("--confirmation-event-path", default=str(base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH))
    parser.add_argument("--publication-event-path", default=str(base_runtime.kernel.DEFAULT_EVENT_PATH))
    parser.add_argument("--report-model-event-path", default=str(kernel.DEFAULT_EVENT_PATH))
    args = parser.parse_args()
    server, thread, url = start_server(
        args.host, args.port, event_path=args.event_path, data_root=args.data_root,
        confirmation_event_path=args.confirmation_event_path, publication_event_path=args.publication_event_path,
        report_model_event_path=args.report_model_event_path,
    )
    print(f"KMFA 报告模型：{url}/report-model", flush=True)
    try:
        thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
