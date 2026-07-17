#!/usr/bin/env python3
"""Run the KMFA v1.5 S22-P2 local security and audit workbench."""

from __future__ import annotations

import argparse
import base64
import copy
import os
import threading
from http import HTTPStatus
from pathlib import Path
from typing import Mapping
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s22_p1_notifications as base_runtime
from KMFA.tools import v015_s22_p2_security_audit as kernel


def render_html() -> str:
    html_text = base_runtime.render_html()
    view = r'''
    <section id="security-audit-view" class="sa-view" aria-labelledby="sa-title" hidden>
      <header class="sa-head"><div><span>长期运行 · 第二步</span><h1 id="sa-title">安全与审计必须先于生产操作</h1><p>登录、敏感查看、处理、参数修改、发布和敏感下载均受权限控制并写入防篡改审计链。</p></div><a href="/notification-delivery">返回通知中心</a></header>
      <nav class="s22-journey" aria-label="长期运行三步流程"><a href="/notification-delivery"><span>1</span>安全通知</a><a href="/security-audit" aria-current="step"><span>2</span>登录与审计</a><a href="/operations"><span>3</span>运维与恢复</a></nav>
      <aside class="sa-boundary"><strong>当前安全边界</strong><span>秘密只从本机运行环境读取，不写入代码、页面或审计日志；危险输入和公开敏感下载失败关闭。</span></aside>
      <section class="sa-summary" aria-label="安全摘要"><article><span>审计完整性</span><strong id="sa-integrity">通过</strong></article><article><span>审计事件</span><strong id="sa-event-count">0</strong></article><article><span>已拦截攻击</span><strong id="sa-rejected-count">0</strong></article><article><span>秘密暴露</span><strong id="sa-secret-count">0</strong></article><article><span>高危漏洞</span><strong id="sa-high-count">0</strong></article></section>
      <div id="sa-feedback" class="sa-feedback" role="status" aria-live="polite">正在读取安全状态…</div>

      <section class="sa-card"><div class="sa-card-head"><div><h2>1. 本机身份验证与权限</h2><p>测试凭据只在本机运行环境中提供；输入框会在提交后立即清空。</p></div><span id="sa-session-state">未登录</span></div>
        <div class="sa-form"><label>本地账号<select id="sa-username"><option value="finance.local">财务管理员</option><option value="reviewer.local">复核人员</option><option value="readonly.local">只读人员</option></select></label><label>本机凭据<input id="sa-credential" type="password" autocomplete="off" placeholder="从本机环境获取"></label><button id="sa-login" class="sa-primary" type="button">验证并建立会话</button></div>
        <div class="sa-form sa-action-form"><label>受保护动作<select id="sa-action"><option value="SENSITIVE_VIEW">查看敏感内容</option><option value="PROCESSING">执行处理</option><option value="PARAMETER_CHANGE">修改参数</option><option value="PUBLICATION">内部发布</option></select></label><button id="sa-run-action" type="button">执行权限检查并记录</button><button id="sa-download" type="button">验证敏感下载</button></div>
      </section>

      <section class="sa-grid"><article class="sa-card"><div class="sa-card-head"><div><h2>2. 秘密配置</h2><p>只显示引用、来源和是否已配置，永不显示值。</p></div><span>环境秘密</span></div><div id="sa-secrets" class="sa-secrets"></div></article>
        <article class="sa-card"><div class="sa-card-head"><div><h2>3. 攻击样本</h2><p>注入、路径穿越、恶意文件、公式注入和公开敏感下载必须全部被拒绝。</p></div><span>5 类</span></div><div id="sa-attacks" class="sa-attacks"></div><button id="sa-tamper" type="button">验证审计篡改阻断</button></article></section>

      <section class="sa-card"><div class="sa-card-head"><div><h2>4. 审计查询</h2><p>按动作和结果查询；日志只保留安全引用、角色、时间和结果。</p></div><span id="sa-query-count">0 条</span></div>
        <div class="sa-form"><label>动作<select id="sa-query-action"><option value="">全部动作</option><option value="LOGIN">登录</option><option value="SENSITIVE_VIEW">敏感查看</option><option value="PROCESSING">处理</option><option value="PARAMETER_CHANGE">参数修改</option><option value="PUBLICATION">发布</option><option value="SENSITIVE_DOWNLOAD">敏感下载</option></select></label><label>结果<select id="sa-query-result"><option value="">全部结果</option><option value="SUCCESS">通过</option><option value="DENIED">已拒绝</option></select></label><button id="sa-query" type="button">查询审计</button></div><div id="sa-history" class="sa-history"></div>
      </section>
      <p class="sa-stop">S22-P2 正式验收后立即停止；健康检查与可观测性属于下一次独立 Run 的 S22-P3。</p>
    </section>
    '''
    css = r'''
    body[data-security-audit-active="true"] main>section:not(#security-audit-view),body[data-security-audit-active="true"] #context-status,body[data-security-audit-active="true"] .identity-shell,body[data-security-audit-active="true"] .quick-shell{display:none!important}body[data-security-audit-active="true"] main{max-width:1240px!important}.sa-view{padding:18px 10px 50px;color:#243946}.sa-head{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;padding:22px;border-radius:12px;background:linear-gradient(135deg,#17354b,#4b4d88);color:#fff}.sa-head span{font-size:11px;font-weight:800;letter-spacing:.08em}.sa-head h1{margin:6px 0;font-size:29px;color:#fff!important}.sa-head p{margin:0;color:#e4e5f5}.sa-head a{display:inline-flex;min-height:44px;align-items:center;padding:0 14px;border:1px solid #c9c9e9;border-radius:8px;color:#fff;text-decoration:none}.sa-boundary{display:flex;gap:14px;margin:14px 0;padding:14px 16px;border:1px solid #d8d7ee;border-radius:10px;background:#f6f5fb}.sa-boundary strong{white-space:nowrap;color:#474b89}.sa-summary{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:14px 0}.sa-summary article{padding:14px;border:1px solid #dce4e8;border-radius:10px;background:#fff}.sa-summary span{display:block;font-size:12px;color:#6b7982}.sa-summary strong{display:block;margin-top:5px;font-size:22px;color:#283f78}.sa-feedback{min-height:44px;padding:12px 14px;border-radius:8px;background:#eaf3f7}.sa-feedback.error{background:#fff0ed;color:#982f25}.sa-feedback.success{background:#e9f6ef;color:#23673f}.sa-card{margin-top:14px;padding:18px;border:1px solid #dce4e8;border-radius:12px;background:#fff;box-shadow:0 5px 18px rgba(22,46,62,.05)}.sa-card-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}.sa-card-head h2{margin:0;font-size:19px}.sa-card-head p{margin:5px 0 0;color:#667782}.sa-card-head>span{padding:5px 9px;border-radius:20px;background:#eff0fa;color:#484c88;font-size:12px}.sa-form{display:flex;gap:10px;align-items:end;flex-wrap:wrap;margin-top:14px}.sa-form label{display:grid;gap:5px;min-width:190px;flex:1;font-size:12px;font-weight:700}.sa-form input,.sa-form select,.sa-form button,.sa-card button{min-height:44px;border:1px solid #bdc9d0;border-radius:8px;padding:0 11px;background:#fff}.sa-form button,.sa-card button{cursor:pointer;font-weight:750}.sa-primary{background:#384b86!important;color:#fff;border-color:#384b86!important}.sa-action-form{padding-top:12px;border-top:1px solid #e6ecef}.sa-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.sa-grid .sa-card{height:calc(100% - 14px)}.sa-secrets,.sa-attacks{display:grid;gap:8px;margin-top:14px}.sa-secret,.sa-attack{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:11px;border:1px solid #e0e7eb;border-radius:8px;background:#fafcfd}.sa-secret code{font-size:11px}.sa-attack button{min-width:120px}.sa-history{display:grid;gap:8px;margin-top:14px}.sa-event{display:grid;grid-template-columns:130px 120px 1fr auto;gap:10px;padding:11px;border:1px solid #e1e8ec;border-radius:8px}.sa-event strong{color:#263f77}.sa-event small{color:#6a7a84}.sa-stop{margin:18px 2px;color:#667782}@media(max-width:850px){.sa-summary{grid-template-columns:repeat(2,1fr)}.sa-grid{grid-template-columns:1fr}.sa-event{grid-template-columns:1fr}.sa-head{display:block}.sa-head a{margin-top:14px}.sa-boundary{display:block}.sa-form>*{width:100%;min-width:0}.sa-summary article:last-child{grid-column:span 2}}@media(max-width:480px){.sa-view{padding:8px 2px 30px}.sa-head{padding:17px}.sa-head h1{font-size:24px}.sa-summary{grid-template-columns:1fr 1fr}.sa-card{padding:14px}.sa-card-head{display:block}.sa-card-head>span{display:inline-block;margin-top:8px}.sa-secret{align-items:flex-start;flex-direction:column}}
    '''
    script = r'''
    <script>
    (()=>{const active=['/security-audit','/security'].includes(location.pathname);if(!active)return;document.body.dataset.securityAuditActive='true';const view=document.querySelector('#security-audit-view');view.hidden=false;const state={options:null,snapshot:null,sessionToken:sessionStorage.getItem('kmfa_s22_session_token'),session:null};const feedback=document.querySelector('#sa-feedback');const say=(text,kind='')=>{feedback.textContent=text;feedback.className='sa-feedback '+kind};const post=async(path,body)=>{const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const value=await response.json();if(!response.ok)throw Object.assign(new Error(value.message_zh||'操作未通过'),{payload:value});return value};const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
      const render=()=>{const snap=state.snapshot||{audit:{events:[],chain_valid:true},query:{events:[],query_result_count:0}};document.querySelector('#sa-integrity').textContent=snap.audit.chain_valid?'通过':'已阻断';document.querySelector('#sa-event-count').textContent=snap.audit.audit_event_count||0;document.querySelector('#sa-rejected-count').textContent=snap.rejected_attack_count||0;document.querySelector('#sa-secret-count').textContent=snap.secret_exposure_count||0;document.querySelector('#sa-high-count').textContent=snap.high_vulnerability_count||0;document.querySelector('#sa-query-count').textContent=(snap.query.query_result_count||0)+' 条';document.querySelector('#sa-secrets').innerHTML=(state.options?.secret_inventory||[]).map(row=>`<div class="sa-secret"><div><strong>${esc(row.reference)}</strong><br><small>${esc(row.source)} · ${row.configured?'已配置':'未配置'}</small></div><code>${esc(row.fingerprint||'不显示值')}</code></div>`).join('');document.querySelector('#sa-history').innerHTML=(snap.query.events||[]).slice().reverse().map(row=>`<div class="sa-event"><strong>${esc(row.action_type)}</strong><span>${esc(row.result)}</span><div>${esc(row.subject_ref)}<br><small>${esc(row.actor_ref)} · ${esc(row.reason_code)}</small></div><small>${esc(row.occurred_at)}</small></div>`).join('')||'<p>还没有符合条件的审计记录。</p>';document.querySelector('#sa-session-state').textContent=state.session?`${state.session.role} · 会话有效`:'未登录'};
      const load=async(filters={})=>{if(!state.options)state.options=await fetch('/api/security-audit/options').then(r=>r.json());const query=new URLSearchParams(Object.entries(filters).filter(([,v])=>v)),headers=state.sessionToken?{'X-KMFA-Session':state.sessionToken}:{},url='/api/security-audit'+(query.size?'?'+query:'');let response=await fetch(url,{headers});if(response.status===403&&state.sessionToken)response=await fetch(url);state.snapshot=await response.json();if(!response.ok)throw new Error(state.snapshot.message_zh||'审计查询未通过');render();return structuredClone({options:state.options,snapshot:state.snapshot,session:state.session})};
      const login=async(credential,username=document.querySelector('#sa-username').value)=>{const value=await post('/api/security-audit/login',{username,credential});state.sessionToken=value.session_token;state.session={role:value.role,company_ref:value.company_ref,session_fingerprint:value.session_fingerprint};sessionStorage.setItem('kmfa_s22_session_token',value.session_token);sessionStorage.setItem('kmfa_s22_session_meta',JSON.stringify(state.session));document.querySelector('#sa-credential').value='';await load();say('身份验证通过，会话已建立且登录已写入审计。','success');return {...value,session_token:'[CLIENT_MEMORY_ONLY]'}};
      const action=async(actionType=document.querySelector('#sa-action').value)=>{if(!state.sessionToken||!state.session)throw new Error('请先完成本机身份验证');const value=await post('/api/security-audit/action',{session_token:state.sessionToken,action_type:actionType,subject_ref:'SUBJECT::BROWSER-'+actionType,company_ref:state.session.company_ref});await load();say('权限检查通过，动作已写入防篡改审计。','success');return value};
      const attack=async(category)=>{const value=await post('/api/security-audit/attack-probe',{category});await load();say(category+' 危险样本已拒绝。','success');return value};const tamper=async()=>{const value=await post('/api/security-audit/tamper-probe',{});say('审计篡改已识别，生产继续运行被阻止。','success');return value};
      const download=async(mode='AUTHENTICATED')=>{if(!state.sessionToken||!state.session)throw new Error('请先完成本机身份验证');const value=await post('/api/security-audit/download',{session_token:state.sessionToken,artifact_ref:'ARTIFACT::BROWSER-SENSITIVE',company_ref:state.session.company_ref,classification:'SENSITIVE',delivery_mode:mode});await load();say('敏感下载已通过身份、角色和主体范围检查。','success');return value};
      const query=async()=>load({action_type:document.querySelector('#sa-query-action').value,result:document.querySelector('#sa-query-result').value});document.querySelector('#sa-login').addEventListener('click',()=>login(document.querySelector('#sa-credential').value).catch(error=>{document.querySelector('#sa-credential').value='';say(error.message,'error')}));document.querySelector('#sa-run-action').addEventListener('click',()=>action().catch(error=>say(error.message,'error')));document.querySelector('#sa-download').addEventListener('click',()=>download().catch(error=>say(error.message,'error')));document.querySelector('#sa-query').addEventListener('click',()=>query().catch(error=>say(error.message,'error')));document.querySelector('#sa-tamper').addEventListener('click',()=>tamper().catch(error=>say(error.message,'error')));const attackRoot=document.querySelector('#sa-attacks');['INJECTION','PATH_TRAVERSAL','MALICIOUS_FILE','FORMULA_INJECTION'].forEach(category=>{const row=document.createElement('div');row.className='sa-attack';row.innerHTML=`<span>${category}</span><button type="button">运行拒绝测试</button>`;row.querySelector('button').addEventListener('click',()=>attack(category).catch(error=>say(error.message,'error')));attackRoot.append(row)});window.KMFA_SECURITY_TEST={snapshot:()=>structuredClone({options:state.options,snapshot:state.snapshot,session:state.session}),load,login,action,attack,tamper,download};load().then(()=>say('安全状态已加载。')).catch(error=>say(error.message,'error'));
    })();
    </script>
    '''
    html_text = html_text.replace("</main>", view + "</main>", 1)
    html_text = html_text.replace("</style>", css + "</style>", 1)
    html_text = html_text.replace("</body>", script + "</body>", 1)
    html_text = html_text.replace(
        '<p class="nd-stop">S22-P1 验收后立即停止；权限、安全和审计属于下一次独立 Run 的 S22-P2。</p>',
        '<p class="nd-stop">通知设置完成后，可进入 <a href="/security-audit">安全与审计</a>；所有受保护动作必须先通过权限门禁。</p>',
    )
    html_text = html_text.replace("<title>KMFA 安全通知 · 经营工作台</title>", "<title>KMFA 安全与审计 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html_text.splitlines()) + "\n"


class SecurityHandler(base_runtime.NotificationHandler):
    server_version = "KMFASecurityAudit/1.5"

    @property
    def security(self) -> kernel.SecurityWorkbench:
        return self.server.security_workbench  # type: ignore[attr-defined,no-any-return]

    def _authorize_notification(
        self,
        body: Mapping[str, object],
        *,
        action_type: str,
        subject_ref: str,
    ) -> None:
        token = body.get("session_token")
        payload = self.security.sessions.decode(token)
        self.security.sessions.perform(
            token,
            action_type=action_type,
            subject_ref=subject_ref,
            company_ref=str(payload["company_ref"]),
        )

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path); path = parsed.path
        try:
            if path == "/api/security-audit/options":
                self._send_json(HTTPStatus.OK, self.security.options()); return
            if path == "/api/security-audit":
                query = parse_qs(parsed.query)
                filters = {
                    "action_type": query.get("action_type", [None])[0],
                    "result": query.get("result", [None])[0],
                    "actor_ref": query.get("actor_ref", [None])[0],
                    "limit": min(int(query.get("limit", ["100"])[0]), 200),
                }
                token = self.headers.get("X-KMFA-Session")
                if token:
                    self.security.sessions.authorize(token, "QUERY_AUDIT")
                    value = self.security.snapshot(**filters)
                    value["authentication_required"] = False
                else:
                    value = copy.deepcopy(self.security.snapshot())
                    value["audit"]["events"] = []
                    value["query"] = {
                        "query_result_count": 0,
                        "events": [],
                        "query_filters": {},
                    }
                    value["authentication_required"] = True
                self._send_json(HTTPStatus.OK, value); return
            if path.startswith("/api/security-audit/"):
                raise kernel.SecurityError("RESOURCE_NOT_FOUND", "没有找到这项安全资源", status=404)
            if path in {"/security-audit", "/security", "/notification-delivery", "/notifications", "/report-workflow", "/report-center"}:
                self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8"); return
            super().do_GET()
        except (TypeError, ValueError, kernel.SecurityError) as error:
            if isinstance(error, kernel.SecurityError):
                self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})
            else:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "code": "QUERY_INVALID", "message_zh": "查询条件不正确"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            if path == "/api/security-audit/login":
                body = self._json_body(); value = self.security.sessions.authenticate(body.get("username"), body.get("credential"))
                self._send_json(HTTPStatus.CREATED, value); return
            if path == "/api/security-audit/action":
                body = self._json_body(); value = self.security.sessions.perform(
                    body.get("session_token"), action_type=body.get("action_type"),
                    subject_ref=body.get("subject_ref"), company_ref=body.get("company_ref"),
                )
                self._send_json(HTTPStatus.CREATED, value); return
            if path == "/api/security-audit/attack-probe":
                body = self._json_body(); self._send_json(HTTPStatus.OK, self.security.attack_probe(body.get("category"))); return
            if path == "/api/security-audit/tamper-probe":
                self._json_body(); self._send_json(HTTPStatus.OK, self.security.tamper_probe()); return
            if path == "/api/security-audit/download":
                body = self._json_body(); value = self.security.guard.authorize_download(
                    body.get("session_token"), artifact_ref=body.get("artifact_ref"),
                    company_ref=body.get("company_ref"), classification=body.get("classification"),
                    delivery_mode=body.get("delivery_mode"),
                )
                self._send_json(HTTPStatus.OK, value); return
            if path == "/api/security-audit/input":
                body = self._json_body(); kind = str(body.get("kind", "")).upper()
                if kind == "TEXT": value = self.security.guard.validate_text(body.get("value"))
                elif kind == "PATH": value = self.security.guard.validate_relative_path(body.get("value"))
                elif kind == "FORMULA": value = self.security.guard.validate_csv_cell(body.get("value"))
                elif kind == "FILE": value = self.security.guard.validate_file(body.get("filename"), base64.b64decode(str(body.get("content_base64", "")), validate=True))
                else: raise kernel.SecurityError("INPUT_KIND_INVALID", "输入安全类型不受支持")
                self._send_json(HTTPStatus.OK, value); return
            if path.startswith("/api/security-audit/"):
                raise kernel.SecurityError("RESOURCE_NOT_FOUND", "没有找到这项安全操作", status=404)
            super().do_POST()
        except (TypeError, ValueError, kernel.SecurityError) as error:
            if isinstance(error, kernel.SecurityError):
                self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})
            else:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "code": "INVALID_REQUEST", "message_zh": "请求格式不正确"})


class SecurityServer(base_runtime.NotificationServer):
    security_workbench: kernel.SecurityWorkbench


def start_server(
    host: str = "127.0.0.1", port: int = 0, *,
    event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
    data_root: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.data_update_kernel.DEFAULT_RUNTIME_ROOT,
    confirmation_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    publication_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    report_model_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    export_event_path: Path | str = base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    export_bundle_root: Path | str = base_runtime.base_runtime.base_runtime.kernel.DEFAULT_BUNDLE_ROOT,
    workflow_event_path: Path | str = base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    notification_event_path: Path | str = base_runtime.kernel.DEFAULT_EVENT_PATH,
    audit_event_path: Path | str = kernel.DEFAULT_EVENT_PATH,
    secret_values: Mapping[str, str] | None = None,
    security_environment: str = "LOCAL_SANDBOX",
) -> tuple[SecurityServer, threading.Thread, str]:
    event_file = Path(event_path)
    server = SecurityServer((host, port), SecurityHandler)
    server.journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.workflow_kernel.EventJournal(event_file)
    server.policy_journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.reporting_kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    server.data_update_store = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.data_update_kernel.DataUpdateStore(data_root)
    server.confirmation_workbench = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.ConfirmationWorkbench(confirmation_event_path)
    server.recalculation_workbench = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.RecalculationPublicationWorkbench(confirmation_event_path, publication_event_path)
    server.report_model_journal = base_runtime.base_runtime.base_runtime.base_runtime.kernel.ReportModelJournal(report_model_event_path)
    server.report_export_journal = base_runtime.base_runtime.base_runtime.kernel.ReportExportJournal(export_event_path, export_bundle_root)
    server.report_workflow_journal = base_runtime.base_runtime.kernel.ReportWorkflowJournal(workflow_event_path)
    server.notification_journal = base_runtime.kernel.NotificationJournal(notification_event_path)
    server.security_workbench = kernel.SecurityWorkbench(
        audit_event_path, secret_values=secret_values, environment=security_environment,
    )
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s22p2-security-audit", daemon=True)
    thread.start(); address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S22-P2 安全与审计工作台")
    parser.add_argument("--host", default="127.0.0.1"); parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--audit-event-path", default=str(kernel.DEFAULT_EVENT_PATH))
    args = parser.parse_args(); secret_values = {name: os.environ.get(name, "") for name in kernel.SECRET_REFERENCES}
    server, thread, url = start_server(args.host, args.port, audit_event_path=args.audit_event_path, secret_values=secret_values)
    print(f"KMFA 安全与审计工作台：{url}/security-audit", flush=True)
    try: thread.join()
    except KeyboardInterrupt: pass
    finally: server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
