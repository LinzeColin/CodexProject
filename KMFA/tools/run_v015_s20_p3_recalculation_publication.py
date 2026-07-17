#!/usr/bin/env python3
"""Run the KMFA v1.5 S20-P3 local recalculation/publication workbench."""

from __future__ import annotations

import argparse
import re
import threading
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlsplit

from KMFA.tools import run_v015_s20_p2_confirmation_workbench as base_runtime
from KMFA.tools import v015_s20_p3_recalculation_publication as kernel


_JOB_ROUTE = re.compile(r"^/api/recalculation/jobs/(JOB-S20P3-\d{4})$")
_JOB_ACTION_ROUTE = re.compile(r"^/api/recalculation/jobs/(JOB-S20P3-\d{4})/(comparison|preview|decide)$")
_VIEW_ROUTE = re.compile(r"^/api/recalculation/views/(project|homepage|report|check-board)$")


def render_html() -> str:
    html = base_runtime.render_html()
    journey_p1 = r'''<nav class="s20-journey" aria-label="数据更新流程步骤"><a href="/data-update" aria-current="step">1 数据更新</a><a class="s20-next" href="/confirmation-workbench">2 人工确认</a><a href="/recalculation-publication">3 重算发布</a></nav>'''
    journey_p2 = r'''<nav class="s20-journey" aria-label="数据更新流程步骤"><a class="s20-prev" href="/data-update">1 数据更新</a><a href="/confirmation-workbench" aria-current="step">2 人工确认</a><a class="s20-next" href="/recalculation-publication">3 重算发布</a></nav>'''
    journey_p3 = r'''<nav class="s20-journey" aria-label="数据更新流程步骤"><a href="/data-update">1 数据更新</a><a class="s20-prev" href="/confirmation-workbench">2 人工确认</a><a href="/recalculation-publication" aria-current="step">3 重算发布</a></nav>'''
    view = r'''
    <section id="recalculation-publication-view" class="rp-view" aria-labelledby="rp-title" hidden>
      <header class="rp-head"><div><span>数据更新 · 重新计算与发布联动</span><h1 id="rp-title">只更新受影响的数字，一次同步四个页面</h1><p>每次重算先展示新旧数字和报告变化。你可以发布候选版本，也可以保留旧版本。</p></div><a href="/confirmation-workbench">返回人工确认</a></header>
      __S20_JOURNEY_P3__
      <aside class="rp-boundary"><strong>安全边界</strong><span>重算失败、说明缺失或页面不一致时一律不发布，旧版本保持可用；这里只做本地产品发布。</span></aside>
      <section class="rp-summary" aria-label="当前发布状态"><article><span>当前版本</span><strong id="rp-current-version">—</strong></article><article><span>同步页面</span><strong id="rp-view-count">0 / 4</strong></article><article><span>待发布任务</span><strong id="rp-awaiting-count">0</strong></article></section>
      <div id="rp-feedback" class="rp-feedback" role="status" aria-live="polite">正在读取发布状态…</div>
      <section class="rp-card" aria-labelledby="rp-start-title"><div class="rp-card-head"><div><h2 id="rp-start-title">1. 选择已确认事项并重算</h2><p>系统沿已登记影响图，只计算关联事实、指标和页面。</p></div></div><div class="rp-form"><label>人工确认<select id="rp-confirmation"></select></label><button id="rp-start" class="rp-primary" type="button">开始受影响链重算</button></div><div id="rp-impact" class="rp-impact"></div></section>
      <section id="rp-comparison-card" class="rp-card" aria-labelledby="rp-comparison-title" hidden><div class="rp-card-head"><div><h2 id="rp-comparison-title">2. 核对重算前后变化</h2><p>每一项变化都有中文原因；缺少说明时发布按钮不会生效。</p></div><span id="rp-job-id"></span></div><div class="rp-compare"><section><h3>数字变化</h3><div id="rp-number-changes"></div></section><section><h3>报告变化</h3><div id="rp-report-changes"></div></section></div><div class="rp-decision"><label>决定<select id="rp-decision"><option value="PUBLISH_CANDIDATE">发布候选版本</option><option value="KEEP_CURRENT">保留当前版本</option></select></label><label>理由<input id="rp-reason" value="已核对数字、报告变化和四个页面一致性"></label><button id="rp-preview" type="button">先看发布预览</button><button id="rp-confirm" class="rp-primary" type="button" disabled>确认决定</button></div><div id="rp-preview-box" class="rp-preview" hidden></div></section>
      <section class="rp-card" aria-labelledby="rp-sync-title"><div class="rp-card-head"><div><h2 id="rp-sync-title">3. 四个页面同步结果</h2><p>项目、首页、经营报告、资料检查板必须使用同一版本和同一组数字。</p></div><button id="rp-refresh" type="button">刷新核验</button></div><div id="rp-views" class="rp-views"></div></section>
      <section class="rp-card" aria-labelledby="rp-history-title"><div class="rp-card-head"><div><h2 id="rp-history-title">重算与发布历史</h2><p>只追加、不覆盖，可在刷新或重启后恢复。</p></div><span id="rp-history-count">0 条</span></div><div id="rp-history" class="rp-history"></div></section>
      <p class="rp-stop">S20-P3 在本地验收后停止。S20 整体复审、GitHub 上传与 App 重装均不在本页面执行。</p>
    </section>
    '''
    css = r'''
    body[data-recalc-active="true"] #page-view,body[data-recalc-active="true"] #loading-view,body[data-recalc-active="true"] #error-view,body[data-recalc-active="true"] #not-found-view,body[data-recalc-active="true"] #homepage-view,body[data-recalc-active="true"] #project-list-view,body[data-recalc-active="true"] #project-detail-view,body[data-recalc-active="true"] #project-workflow-view,body[data-recalc-active="true"] #receivables-view,body[data-recalc-active="true"] #funds-view,body[data-recalc-active="true"] #funds-report-view,body[data-recalc-active="true"] #tax-invoice-view,body[data-recalc-active="true"] #policy-eligibility-view,body[data-recalc-active="true"] #tax-policy-report-view,body[data-recalc-active="true"] #data-update-view,body[data-recalc-active="true"] #confirmation-workbench-view,body[data-recalc-active="true"] #context-status,body[data-recalc-active="true"] .identity-shell,body[data-recalc-active="true"] .quick-shell,body[data-recalc-active="true"] #access-workspace,body[data-recalc-active="true"] #experience-workspace{display:none!important}
    .s20-journey{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:12px 0}.s20-journey a{display:flex;min-height:44px;align-items:center;justify-content:center;padding:0 12px;border:1px solid #b9cbd7;border-radius:7px;background:#f7fafb;color:#245a7a;font-size:12px;font-weight:800;text-decoration:none}.s20-journey a[aria-current="step"]{border-color:#246c83;background:#246c83;color:#fff}.rp-view{margin:2px 0 32px;color:#29475d}.rp-head{display:flex;justify-content:space-between;align-items:flex-start;gap:18px}.rp-head span{font-size:12px;font-weight:800;color:#17648f}.rp-head h1{margin:4px 0;font-size:30px;color:#173d57}.rp-head p{max-width:760px;margin:6px 0;color:#607684;font-size:13px}.rp-head a,.rp-card button{display:inline-flex;min-height:44px;align-items:center;justify-content:center;padding:0 14px;border:1px solid #9fb8c8;border-radius:7px;background:#fff;color:#245a7a;font:inherit;font-size:12px;font-weight:800;text-decoration:none;cursor:pointer}.rp-boundary{display:flex;justify-content:space-between;gap:14px;margin:12px 0;padding:12px 14px;border:1px solid #d5b27c;border-left:4px solid #a86a17;border-radius:8px;background:#fffaf2;color:#654519;font-size:12px}.rp-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:11px 0}.rp-summary article,.rp-card{padding:15px;border:1px solid #d8e2e8;border-radius:9px;background:#fff}.rp-summary span{display:block;color:#607684;font-size:11px}.rp-summary strong{display:block;margin-top:5px;color:#173d57;font-size:22px}.rp-feedback{min-height:44px;padding:11px 13px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:7px;background:#edf6fb;font-size:13px}.rp-feedback[data-state="error"]{border-color:#d7a6a6;background:#fff8f7;color:#7f2929}.rp-feedback[data-state="success"]{border-color:#9fc5ae;background:#f3faf5;color:#276346}.rp-card{margin-top:11px}.rp-card-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;margin-bottom:11px}.rp-card h2{margin:0;color:#214d68;font-size:18px}.rp-card h3{margin:0 0 8px;font-size:13px}.rp-card-head p{margin:5px 0 0;color:#607684;font-size:11px}.rp-form,.rp-decision{display:grid;grid-template-columns:minmax(240px,1fr) auto;gap:9px;align-items:end}.rp-decision{grid-template-columns:180px minmax(260px,1fr) auto auto}.rp-form label,.rp-decision label{display:grid;gap:5px;font-size:11px;font-weight:800}.rp-form select,.rp-decision select,.rp-decision input{min-height:44px;padding:0 10px;border:1px solid #b9cbd7;border-radius:7px;background:#fff;font:inherit}.rp-primary{border:0!important;background:#246c83!important;color:#fff!important}.rp-primary:disabled{background:#a9b6bd!important}.rp-impact{margin-top:10px;color:#607684;font-size:11px}.rp-compare{display:grid;grid-template-columns:1fr 1fr;gap:10px}.rp-compare>section{padding:12px;border-radius:7px;background:#f7fafb}.rp-change{padding:8px 0;border-bottom:1px solid #dce5ea;font-size:11px}.rp-change:last-child{border:0}.rp-change strong{display:block;color:#214d68}.rp-change small{display:block;margin-top:3px;color:#607684;line-height:1.45}.rp-preview{margin-top:10px;padding:11px;border:1px solid #d5b27c;border-radius:7px;background:#fffdf8;font-size:12px}.rp-views{display:grid;grid-template-columns:repeat(4,1fr);gap:9px}.rp-view-card{padding:11px;border:1px solid #dce5ea;border-radius:7px;background:#fafcfd}.rp-view-card strong{display:block;color:#214d68;font-size:12px}.rp-view-card span{display:block;margin-top:5px;color:#607684;font-size:10px}.rp-history{display:grid;gap:6px}.rp-history-row{display:grid;grid-template-columns:50px 130px 1fr 150px;gap:8px;padding:8px;border-bottom:1px solid #e3e9ed;font-size:10px}.rp-stop{color:#607684;font-size:11px}.rp-card button:disabled{cursor:not-allowed}
    @media(max-width:900px){.rp-views{grid-template-columns:1fr 1fr}.rp-decision{grid-template-columns:1fr 1fr}.rp-head,.rp-boundary{display:grid}.rp-head a{justify-self:start}.rp-compare{grid-template-columns:1fr}}
    @media(max-width:520px){.rp-summary,.rp-views,.rp-form,.rp-decision{grid-template-columns:1fr}.rp-head h1{font-size:25px}.rp-card button{width:100%}.rp-history-row{grid-template-columns:42px 1fr}.rp-history-row span:nth-child(n+3){grid-column:2}}
    '''
    script = r'''
    <script>
    (()=>{'use strict';
      const active=()=>location.pathname==='/recalculation-publication';if(!active())return;
      document.body.dataset.recalcActive='true';const view=document.querySelector('#recalculation-publication-view');view.hidden=false;
      let state={eligible:null,current:null,jobs:null,comparison:null,preview:null,views:null,history:null,activeJob:null};
      const feedback=document.querySelector('#rp-feedback'),key=p=>p+'-'+Date.now()+'-'+Math.floor(Math.random()*100000);
      const api=async(path,init={})=>{const r=await fetch(path,init),v=await r.json();if(!r.ok)throw Object.assign(new Error(v.message_zh||'请求失败'),{payload:v,status:r.status});return v};
      const post=(path,body)=>api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const say=(text,kind='')=>{feedback.textContent=text;if(kind)feedback.dataset.state=kind;else delete feedback.dataset.state};
      const money=n=>'¥'+(n/100).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
      const renderEligible=v=>{state.eligible=v;const s=document.querySelector('#rp-confirmation');s.replaceChildren();v.confirmations.forEach(row=>{const o=document.createElement('option');o.value=row.event_id;o.textContent=row.issue_id+' · '+row.action_label_zh;s.append(o)});if(!v.confirmations.length){const o=document.createElement('option');o.textContent='暂无可重算的确认记录';o.value='';s.append(o)}document.querySelector('#rp-start').disabled=!v.confirmations.length};
      const renderCurrent=v=>{state.current=v;document.querySelector('#rp-current-version').textContent=v.publication_version_id;document.querySelector('#rp-view-count').textContent=v.consistency.view_count+' / 4'};
      const changeNode=row=>{const d=document.createElement('div');d.className='rp-change';const s=document.createElement('strong'),x=document.createElement('small');s.textContent=row.label_zh?row.label_zh+'：'+(row.unit==='cent'?money(row.before)+' → '+money(row.after):row.before+' → '+row.after):row.view_id+'：'+row.before_version+' → '+row.after_version;x.textContent=row.explanation_zh;d.append(s,x);return d};
      const renderComparison=(job,c)=>{state.activeJob=job;state.comparison=c;document.querySelector('#rp-comparison-card').hidden=false;document.querySelector('#rp-job-id').textContent=job.job_id;const n=document.querySelector('#rp-number-changes'),r=document.querySelector('#rp-report-changes');n.replaceChildren(...c.numeric_changes.map(changeNode));r.replaceChildren(...c.report_changes.map(changeNode));document.querySelector('#rp-impact').textContent='受影响 '+job.affected_node_count+' 个节点；未受影响 '+job.unaffected_refs.length+' 个节点保持原值。';document.querySelector('#rp-confirm').disabled=true;document.querySelector('#rp-preview-box').hidden=true;state.preview=null};
      const renderViews=v=>{state.views=v;const root=document.querySelector('#rp-views');root.replaceChildren();Object.entries(v).forEach(([id,row])=>{const d=document.createElement('article');d.className='rp-view-card';const a=document.createElement('strong'),b=document.createElement('span'),c=document.createElement('span');a.textContent=row.title_zh;b.textContent=row.publication_version_id+' · '+row.sync_status;c.textContent='毛利 '+money(row.project_margin_cents)+' · 回款率 '+(row.collection_ratio_bps/100).toFixed(2)+'%';d.append(a,b,c);root.append(d)})};
      const renderHistory=v=>{state.history=v;document.querySelector('#rp-history-count').textContent=v.event_count+' 条';const root=document.querySelector('#rp-history');root.replaceChildren();v.events.forEach(row=>{const d=document.createElement('div');d.className='rp-history-row';[row.sequence,row.event_type,row.job_id,row.recorded_at].forEach(x=>{const s=document.createElement('span');s.textContent=String(x);d.append(s)});root.append(d)})};
      const renderJobs=v=>{state.jobs=v;document.querySelector('#rp-awaiting-count').textContent=String(v.jobs.filter(row=>row.decision_status==='AWAITING_DECISION').length)};
      const load=async()=>{try{const [eligible,current,jobs,history,...views]=await Promise.all([api('/api/recalculation/eligible'),api('/api/recalculation/current'),api('/api/recalculation/jobs'),api('/api/recalculation/history'),...['project','homepage','report','check-board'].map(id=>api('/api/recalculation/views/'+id))]);renderEligible(eligible);renderCurrent(current);renderJobs(jobs);renderHistory(history);renderViews(Object.fromEntries(['project','homepage','report','check-board'].map((id,i)=>[id,views[i]])));say('发布状态已核验：四个页面使用同一版本。','success');return state}catch(e){say(e.message,'error');throw e}};
      const start=async()=>{const eventId=document.querySelector('#rp-confirmation').value;if(!eventId)return null;try{const job=await post('/api/recalculation/start',{control_event_id:eventId,actor_id:'public-demo-steward',actor_role:'ROLE::DATA_STEWARD',idempotency_key:key('browser-recalculate')});renderComparison(job,job.comparison);await load();renderComparison(job,job.comparison);say('重算完成。请核对数字和报告变化。','success');return job}catch(e){say(e.message,'error');throw e}};
      const preview=async()=>{if(!state.activeJob)return null;try{const decision=document.querySelector('#rp-decision').value,v=await post('/api/recalculation/jobs/'+state.activeJob.job_id+'/preview',{decision,actor_role:'ROLE::MANAGEMENT'});state.preview=v;const box=document.querySelector('#rp-preview-box');box.hidden=false;box.textContent=(decision==='PUBLISH_CANDIDATE'?'将发布 '+v.candidate_version:'将保留 '+v.before_version)+'；数字变化 '+v.numeric_change_count+' 项，报告变化 '+v.report_change_count+' 项，四页面一致性已通过。';document.querySelector('#rp-confirm').disabled=false;say('预览已绑定当前版本，可以确认决定。');return v}catch(e){say(e.message,'error');throw e}};
      const decide=async()=>{if(!state.activeJob||!state.preview)return null;try{const decision=document.querySelector('#rp-decision').value,v=await post('/api/recalculation/jobs/'+state.activeJob.job_id+'/decide',{decision,actor_id:'public-demo-manager',actor_role:'ROLE::MANAGEMENT',reason_zh:document.querySelector('#rp-reason').value,preview_id:state.preview.preview_id,preview_token:state.preview.preview_token,idempotency_key:key('browser-publication')});await load();document.querySelector('#rp-comparison-card').hidden=true;state.activeJob=null;state.preview=null;say(decision==='PUBLISH_CANDIDATE'?'新版本已在本地同步发布到四个页面。':'已保留旧版本。','success');return v}catch(e){say(e.message,'error');throw e}};
      document.querySelector('#rp-start').addEventListener('click',()=>start().catch(()=>{}));document.querySelector('#rp-preview').addEventListener('click',()=>preview().catch(()=>{}));document.querySelector('#rp-confirm').addEventListener('click',()=>decide().catch(()=>{}));document.querySelector('#rp-refresh').addEventListener('click',()=>load().catch(()=>{}));document.querySelector('#rp-decision').addEventListener('change',()=>{state.preview=null;document.querySelector('#rp-confirm').disabled=true;document.querySelector('#rp-preview-box').hidden=true});
      window.KMFA_RECALCULATION_TEST={snapshot:()=>structuredClone(state),load,start,preview,decide};load().catch(()=>{});
    })();
    </script>
    '''
    view = view.replace("__S20_JOURNEY_P3__", journey_p3)
    html = html.replace("</main>", view + "</main>", 1)
    html = html.replace("</style>", css + "</style>", 1)
    html = html.replace("</body>", script + "</body>", 1)
    html = html.replace(
        '<p class="cw-disclaimer">S20-P2 只完成人工确认闭环。受影响链重算、前后对比、跨页面同步和发布属于 S20-P3，本阶段没有执行。</p>',
        journey_p2 + '<p class="cw-disclaimer">人工确认完成后，可进入 <a href="/recalculation-publication">重新计算与发布联动</a>。</p>',
    )
    html = html.replace('<p class="du-disclaimer">', journey_p1 + '<p class="du-disclaimer">', 1)
    html = html.replace("<title>KMFA 人工确认工作台</title>", "<title>KMFA 重新计算与发布联动</title>")
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class RecalculationHandler(base_runtime.ConfirmationHandler):
    server_version = "KMFARecalculationPublication/1.5"

    @property
    def recalculation(self) -> kernel.RecalculationPublicationWorkbench:
        return self.server.recalculation_workbench  # type: ignore[attr-defined,no-any-return]

    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            routes = {
                "/api/recalculation/eligible": self.recalculation.eligible_confirmations,
                "/api/recalculation/current": self.recalculation.current_publication,
                "/api/recalculation/jobs": self.recalculation.jobs,
                "/api/recalculation/history": self.recalculation.history,
            }
            if path in routes:
                self._send_json(HTTPStatus.OK, routes[path]())
                return
            match = _VIEW_ROUTE.fullmatch(path)
            if match:
                self._send_json(HTTPStatus.OK, self.recalculation.view(match.group(1)))
                return
            match = _JOB_ACTION_ROUTE.fullmatch(path)
            if match and match.group(2) == "comparison":
                self._send_json(HTTPStatus.OK, self.recalculation.comparison(match.group(1)))
                return
            match = _JOB_ROUTE.fullmatch(path)
            if match:
                self._send_json(HTTPStatus.OK, self.recalculation.job(match.group(1)))
                return
            if path.startswith("/api/recalculation/views/"):
                raise kernel.RecalculationError("VIEW_NOT_FOUND", "没有找到这个同步页面。", status=404)
            if path.startswith("/api/recalculation/jobs/"):
                raise kernel.RecalculationError("JOB_NOT_FOUND", "没有找到重算任务。", status=404)
            if path.startswith("/api/") or path == "/favicon.ico" or path.startswith("/reports/"):
                super().do_GET()
                return
            self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")
        except kernel.RecalculationError as error:
            self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            if path == "/api/recalculation/start":
                body = self._json_body()
                value = self.recalculation.start_recalculation(
                    str(body.get("control_event_id", "")), actor_id=str(body.get("actor_id", "")),
                    actor_role=str(body.get("actor_role", "")), idempotency_key=str(body.get("idempotency_key", "")),
                )
                self._send_json(HTTPStatus.OK, value)
                return
            match = _JOB_ACTION_ROUTE.fullmatch(path)
            if match and match.group(2) in {"preview", "decide"}:
                job_id, action = match.groups()
                body = self._json_body()
                if action == "preview":
                    value = self.recalculation.publication_preview(
                        job_id, str(body.get("decision", "")), actor_role=str(body.get("actor_role", "")),
                    )
                else:
                    value = self.recalculation.decide(
                        job_id, str(body.get("decision", "")), actor_id=str(body.get("actor_id", "")),
                        actor_role=str(body.get("actor_role", "")), reason_zh=str(body.get("reason_zh", "")),
                        preview_id=str(body.get("preview_id", "")), preview_token=str(body.get("preview_token", "")),
                        idempotency_key=str(body.get("idempotency_key", "")),
                    )
                self._send_json(HTTPStatus.OK, value)
                return
            super().do_POST()
        except kernel.RecalculationError as error:
            self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})


class RecalculationServer(base_runtime.ConfirmationServer):
    recalculation_workbench: kernel.RecalculationPublicationWorkbench


def start_server(
    host: str = "127.0.0.1", port: int = 0, *,
    event_path: Path | str = base_runtime.workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
    data_root: Path | str = base_runtime.data_update_kernel.DEFAULT_RUNTIME_ROOT,
    confirmation_event_path: Path | str = base_runtime.kernel.DEFAULT_EVENT_PATH,
    publication_event_path: Path | str = kernel.DEFAULT_EVENT_PATH,
) -> tuple[RecalculationServer, threading.Thread, str]:
    event_file = Path(event_path)
    server = RecalculationServer((host, port), RecalculationHandler)
    server.journal = base_runtime.workflow_kernel.EventJournal(event_file)
    server.policy_journal = base_runtime.policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = base_runtime.reporting_kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    server.data_update_store = base_runtime.data_update_kernel.DataUpdateStore(data_root)
    server.confirmation_workbench = base_runtime.kernel.ConfirmationWorkbench(confirmation_event_path)
    server.recalculation_workbench = kernel.RecalculationPublicationWorkbench(confirmation_event_path, publication_event_path)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s20p3-recalculation", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S20-P3 重新计算与发布联动工作台")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--event-path", default=str(base_runtime.workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH))
    parser.add_argument("--data-root", default=str(base_runtime.data_update_kernel.DEFAULT_RUNTIME_ROOT))
    parser.add_argument("--confirmation-event-path", default=str(base_runtime.kernel.DEFAULT_EVENT_PATH))
    parser.add_argument("--publication-event-path", default=str(kernel.DEFAULT_EVENT_PATH))
    args = parser.parse_args()
    server, thread, url = start_server(
        args.host, args.port, event_path=args.event_path, data_root=args.data_root,
        confirmation_event_path=args.confirmation_event_path, publication_event_path=args.publication_event_path,
    )
    print(f"KMFA 重新计算与发布联动：{url}/recalculation-publication", flush=True)
    try:
        thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
