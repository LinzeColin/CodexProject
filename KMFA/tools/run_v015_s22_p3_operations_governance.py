#!/usr/bin/env python3
"""Run the KMFA v1.5 S22-P3 local operations and recovery workbench."""

from __future__ import annotations

import argparse
import os
import threading
from http import HTTPStatus
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from KMFA.tools import run_v015_s22_p2_security_audit as base_runtime
from KMFA.tools import v015_s22_p1_notifications as notification_kernel
from KMFA.tools import v015_s22_p3_operations_governance as kernel


def render_html() -> str:
    """Extend the accepted S22-P2 workbench with a minimal operations panel."""

    html_text = base_runtime.render_html()
    view = r'''
    <section id="operations-view" class="op-view" aria-labelledby="op-title" hidden>
      <header class="op-head">
        <div><span>长期运行 · 第三步</span><h1 id="op-title">运维、恢复与升级控制</h1><p>只显示运行所需状态；备份必须先验证并完成恢复演练，升级必须可重复执行和回滚。</p></div>
        <a href="/security-audit">返回安全与审计</a>
      </header>
      <nav class="s22-journey" aria-label="长期运行三步流程"><a href="/notification-delivery"><span>1</span>安全通知</a><a href="/security-audit"><span>2</span>登录与审计</a><a href="/operations" aria-current="step"><span>3</span>运维与恢复</a></nav>
      <aside class="op-boundary"><strong>本轮边界</strong><span>仅使用本地公开合成数据，不读取原始资料，不连接外部网络，不上传 GitHub，不重装 App。</span></aside>
      <section class="op-summary" aria-label="运维摘要">
        <article><span>已监控服务</span><strong id="op-monitored">0 / 6</strong></article>
        <article><span>不可用服务</span><strong id="op-unavailable">0</strong></article>
        <article><span>可恢复备份</span><strong id="op-usable">0</strong></article>
        <article><span>待迁移项目</span><strong id="op-pending">4</strong></article>
      </section>
      <div id="op-feedback" class="op-feedback" role="status" aria-live="polite">正在读取运维状态…</div>

      <section class="op-card">
        <div class="op-card-head"><div><h2>1. 健康检查</h2><p>导入、队列、计算、报告、存储和通知均有监控；关键服务失效时自动阻止继续运行。</p></div><span id="op-production">检查中</span></div>
        <div id="op-services" class="op-services"></div>
        <div class="op-actions"><label>故障演练服务<select id="op-service"><option value="STORAGE">本地存储</option><option value="COMPUTATION">计算服务</option><option value="REPORT">报告生成</option></select></label><button id="op-health-drill" type="button">执行故障与恢复演练</button></div>
      </section>

      <section class="op-login op-card">
        <div class="op-card-head"><div><h2>2. 负责人验证</h2><p>备份、恢复和迁移只允许负责人执行；凭据提交后立即清空。</p></div><span id="op-session">未登录</span></div>
        <div class="op-actions"><label>本地账号<select id="op-username"><option value="owner.local">负责人</option><option value="finance.local">财务管理员（无运维权限）</option></select></label><label>本机凭据<input id="op-credential" type="password" autocomplete="off" placeholder="从本机环境获取"></label><button id="op-login" class="op-primary" type="button">验证身份</button></div>
      </section>

      <section class="op-grid">
        <article class="op-card">
          <div class="op-card-head"><div><h2>3. 备份与恢复</h2><p>同时保护私有派生数据、配置和审计事件；未验证、未演练的备份不可用。</p></div><span id="op-backup-state">尚无备份</span></div>
          <ol class="op-steps"><li>创建本地私有备份</li><li>校验内容与权限完整性</li><li>恢复演练并确认零差异</li></ol>
          <div class="op-actions"><button id="op-backup-create" type="button">创建备份</button><button id="op-backup-verify" type="button">验证备份</button><button id="op-backup-restore" class="op-primary" type="button">执行恢复演练</button></div>
          <p id="op-restore-result" class="op-result">尚未执行恢复演练。</p>
        </article>
        <article class="op-card">
          <div class="op-card-head"><div><h2>4. 安全升级与回滚</h2><p>数据库结构、参数、公式和前端共同迁移；重复执行不产生新变化，故障时保持原状态。</p></div><span id="op-migration-state">待迁移</span></div>
          <div class="op-actions"><button id="op-migrate" class="op-primary" type="button">执行迁移</button><button id="op-migration-drill" type="button">执行迁移故障演练</button><button id="op-rollback" type="button">回滚最近迁移</button></div>
          <p id="op-migration-result" class="op-result">尚未执行迁移。</p>
        </article>
      </section>
      <p class="op-stop">S22-P3 正式验收后立即停止；下一步只能进入 S22 总体复审，不能直接开始 S23。</p>
    </section>
    '''
    css = r'''
    body[data-operations-active="true"] main>section:not(#operations-view),body[data-operations-active="true"] #context-status,body[data-operations-active="true"] .identity-shell,body[data-operations-active="true"] .quick-shell{display:none!important}body[data-operations-active="true"] main{max-width:1240px!important}.op-view{padding:18px 10px 50px;color:#243946}.op-head{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;padding:22px;border-radius:12px;background:linear-gradient(135deg,#173f42,#315f80);color:#fff}.op-head span{font-size:11px;font-weight:800;letter-spacing:.08em}.op-head h1{margin:6px 0;font-size:29px;color:#fff!important}.op-head p{margin:0;color:#e4f1f2}.op-head a{display:inline-flex;min-height:44px;align-items:center;padding:0 14px;border:1px solid #b9d8dc;border-radius:8px;color:#fff;text-decoration:none}.op-boundary{display:flex;gap:14px;margin:14px 0;padding:14px 16px;border:1px solid #cfe0e0;border-radius:10px;background:#f2f8f7}.op-boundary strong{white-space:nowrap;color:#296263}.op-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0}.op-summary article{padding:14px;border:1px solid #dce4e8;border-radius:10px;background:#fff}.op-summary span{display:block;font-size:12px;color:#6b7982}.op-summary strong{display:block;margin-top:5px;font-size:22px;color:#235f62}.op-feedback{min-height:44px;padding:12px 14px;border-radius:8px;background:#e8f3f4}.op-feedback.error{background:#fff0ed;color:#982f25}.op-feedback.success{background:#e9f6ef;color:#23673f}.op-card{margin-top:14px;padding:18px;border:1px solid #dce4e8;border-radius:12px;background:#fff;box-shadow:0 5px 18px rgba(22,46,62,.05)}.op-card-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}.op-card-head h2{margin:0;font-size:19px}.op-card-head p{margin:5px 0 0;color:#667782}.op-card-head>span{padding:5px 9px;border-radius:20px;background:#e9f3f3;color:#296263;font-size:12px}.op-services{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:14px}.op-service{display:grid;grid-template-columns:1fr auto;gap:4px 10px;padding:12px;border:1px solid #dce7e8;border-radius:9px;background:#fbfdfd}.op-service strong{font-size:14px}.op-service span{font-weight:750;color:#276344}.op-service small{grid-column:1/-1;color:#6d7d83}.op-service.unavailable span{color:#a1352b}.op-actions{display:flex;gap:10px;align-items:end;flex-wrap:wrap;margin-top:14px}.op-actions label{display:grid;gap:5px;min-width:190px;flex:1;font-size:12px;font-weight:700}.op-actions input,.op-actions select,.op-actions button{min-height:44px;border:1px solid #b9c8cd;border-radius:8px;padding:0 11px;background:#fff}.op-actions button{cursor:pointer;font-weight:750}.op-primary{background:#276266!important;color:#fff;border-color:#276266!important}.op-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.op-grid .op-card{height:calc(100% - 14px)}.op-steps{padding-left:22px;color:#53666f}.op-result{min-height:45px;padding:11px;border-radius:8px;background:#f4f7f8;color:#53666f}.op-stop{margin:18px 2px;color:#667782}@media(max-width:850px){.op-summary{grid-template-columns:repeat(2,1fr)}.op-services{grid-template-columns:repeat(2,1fr)}.op-grid{grid-template-columns:1fr}.op-head{display:block}.op-head a{margin-top:14px}.op-boundary{display:block}.op-actions>*{width:100%;min-width:0}}@media(max-width:480px){.op-view{padding:8px 2px 30px}.op-head{padding:17px}.op-head h1{font-size:24px}.op-services{grid-template-columns:1fr}.op-card{padding:14px}.op-card-head{display:block}.op-card-head>span{display:inline-block;margin-top:8px}}
    '''
    script = r'''
    <script>
    (()=>{const active=['/operations','/operations-governance'].includes(location.pathname);if(!active)return;document.body.dataset.operationsActive='true';const view=document.querySelector('#operations-view');view.hidden=false;const navigationType=performance.getEntriesByType('navigation')[0]?.type||'navigate',cachedSession=navigationType==='reload'?null:(()=>{try{return JSON.parse(sessionStorage.getItem('kmfa_s22_session_meta')||'null')}catch{return null}})(),state={overview:null,token:navigationType==='reload'?null:sessionStorage.getItem('kmfa_s22_session_token'),session:cachedSession,backupId:null,migrationId:null};const feedback=document.querySelector('#op-feedback');const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));const say=(text,kind='')=>{feedback.textContent=text;feedback.className='op-feedback '+kind};const post=async(path,body)=>{const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});const value=await response.json();if(!response.ok)throw Object.assign(new Error(value.message_zh||'操作未通过'),{payload:value});return value};
      const render=()=>{const value=state.overview||{health:{services:[]},backup:{},migration:{}};const health=value.health||{};document.querySelector('#op-monitored').textContent=String(health.monitored_service_count||0)+' / '+String(health.service_count||6);document.querySelector('#op-unavailable').textContent=health.unavailable_service_count||0;document.querySelector('#op-usable').textContent=value.backup?.usable_backup_count||0;document.querySelector('#op-pending').textContent=value.migration?.pending_surface_count||0;document.querySelector('#op-production').textContent=health.production_ready?'可以运行':'已阻止';document.querySelector('#op-services').innerHTML=(health.services||[]).map(row=>'<div class="op-service '+(row.status==='UNAVAILABLE'?'unavailable':'')+'"><strong>'+esc(row.label_zh)+'</strong><span>'+esc(row.status)+'</span><small>'+esc(row.message_zh)+' · '+esc(row.updated_at||'未更新')+'</small></div>').join('');document.querySelector('#op-backup-state').textContent=(value.backup?.usable_backup_count||0)>0?'已验证并可恢复':((value.backup?.verified_backup_count||0)>0?'已验证，待演练':((value.backup?.backup_count||0)>0?'未验证':'尚无备份'));document.querySelector('#op-migration-state').textContent=value.migration?.at_target?'已到目标版本':'待迁移';document.querySelector('#op-session').textContent=state.session?state.session.role+' · 会话有效':'未登录'};
      const load=async()=>{state.overview=await fetch('/api/operations').then(response=>response.json());render();return structuredClone({overview:state.overview,session:state.session,backupId:state.backupId,migrationId:state.migrationId})};
      const requireLogin=()=>{if(!state.token)throw new Error('请先完成负责人验证')};
      const login=async(credential,username=document.querySelector('#op-username').value)=>{const value=await post('/api/security-audit/login',{username,credential});state.token=value.session_token;state.session={role:value.role,company_ref:value.company_ref,session_fingerprint:value.session_fingerprint};sessionStorage.setItem('kmfa_s22_session_token',value.session_token);sessionStorage.setItem('kmfa_s22_session_meta',JSON.stringify(state.session));document.querySelector('#op-credential').value='';await load();say(value.role==='OWNER'?'负责人验证通过。':'身份已验证，但该角色没有运维权限。','success');return {...value,session_token:'[CLIENT_MEMORY_ONLY]'}};
      const healthDrill=async(serviceId=document.querySelector('#op-service').value)=>{requireLogin();const value=await post('/api/operations/health-drill',{session_token:state.token,service_id:serviceId});await load();say('故障被识别并阻断，服务恢复后运行门禁重新开放。','success');return value};
      const createBackup=async()=>{requireLogin();const value=await post('/api/operations/backups',{session_token:state.token});state.backupId=value.backup_id;await load();document.querySelector('#op-restore-result').textContent='备份已创建，但尚未验证，因此当前不可用于恢复。';say('备份已创建，下一步必须验证。','success');return value};
      const verifyBackup=async()=>{requireLogin();const value=await post('/api/operations/backups/verify',{session_token:state.token,backup_id:state.backupId});state.backupId=value.backup_id;await load();document.querySelector('#op-restore-result').textContent='完整性验证通过；完成恢复演练后才可使用。';say('备份验证通过，仍需恢复演练。','success');return value};
      const restoreDrill=async()=>{requireLogin();const value=await post('/api/operations/backups/restore-drill',{session_token:state.token,backup_id:state.backupId});await load();document.querySelector('#op-restore-result').textContent='恢复演练通过：数据差异 0，权限差异 0，备份可用。';say('恢复演练通过，数据与权限均为零差异。','success');return value};
      const migrate=async()=>{requireLogin();const value=await post('/api/operations/migrations',{session_token:state.token});if(value.migration_id)state.migrationId=value.migration_id;await load();document.querySelector('#op-migration-result').textContent=value.status==='NOOP'?'重复执行结果：无变化（幂等）。':'四个迁移面已安全升级；再次执行将不产生变化。';say('迁移操作完成。','success');return value};
      const migrationDrill=async()=>{requireLogin();const value=await post('/api/operations/migrations/failure-drill',{session_token:state.token,surface:'FORMULA'});await load();document.querySelector('#op-migration-result').textContent='故障演练通过：失败被识别，原状态保持不变，差异 0。';say('迁移故障演练通过。','success');return value};
      const rollback=async()=>{requireLogin();const value=await post('/api/operations/migrations/rollback',{session_token:state.token,migration_id:state.migrationId});await load();document.querySelector('#op-migration-result').textContent='回滚完成：状态差异 0，权限差异 0。';say('最近迁移已精确回滚。','success');return value};
      const bind=(selector,action)=>document.querySelector(selector).addEventListener('click',()=>action().catch(error=>say(error.message,'error')));bind('#op-login',()=>login(document.querySelector('#op-credential').value));bind('#op-health-drill',healthDrill);bind('#op-backup-create',createBackup);bind('#op-backup-verify',verifyBackup);bind('#op-backup-restore',restoreDrill);bind('#op-migrate',migrate);bind('#op-migration-drill',migrationDrill);bind('#op-rollback',rollback);window.KMFA_OPERATIONS_TEST={snapshot:()=>structuredClone({overview:state.overview,session:state.session,backupId:state.backupId,migrationId:state.migrationId}),load,login,healthDrill,createBackup,verifyBackup,restoreDrill,migrate,migrationDrill,rollback};load().then(()=>say('运维状态已加载。')).catch(error=>say(error.message,'error'));
    })();
    </script>
    '''
    html_text = html_text.replace("</main>", view + "</main>", 1)
    html_text = html_text.replace("</style>", css + "</style>", 1)
    html_text = html_text.replace("</body>", script + "</body>", 1)
    html_text = html_text.replace(
        '<p class="sa-stop">S22-P2 正式验收后立即停止；健康检查与可观测性属于下一次独立 Run 的 S22-P3。</p>',
        '<p class="sa-stop">安全与审计完成后，可进入 <a href="/operations">运维、恢复与升级控制</a>；关键服务和可恢复性必须先通过门禁。</p>',
    )
    html_text = html_text.replace(
        "<title>KMFA 安全与审计 · 经营工作台</title>",
        "<title>KMFA 运维、恢复与升级 · 经营工作台</title>",
    )
    return "\n".join(line.rstrip() for line in html_text.splitlines()) + "\n"


class OperationsHandler(base_runtime.SecurityHandler):
    server_version = "KMFAOperationsGovernance/1.5"

    @property
    def operations(self) -> kernel.OperationsWorkbench:
        return self.server.operations_workbench  # type: ignore[attr-defined,no-any-return]

    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            if path == "/api/operations":
                self._send_json(HTTPStatus.OK, self.operations.overview())
                return
            if path == "/api/operations/options":
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "schema_version": "kmfa.v015.s22p3.operations_options.v1",
                        "services": [
                            {
                                "service_id": service_id,
                                "label_zh": value["label_zh"],
                                "critical": value["critical"],
                            }
                            for service_id, value in kernel.SERVICE_DEFINITIONS.items()
                        ],
                        "backup_datasets": list(kernel.BACKUP_DATASETS),
                        "migration_surfaces": list(kernel.MIGRATION_SURFACES),
                        "necessary_status_only": True,
                    },
                )
                return
            if path.startswith("/api/operations/"):
                raise kernel.OperationsError("RESOURCE_NOT_FOUND", "没有找到这项运维资源", status=404)
            if path in {
                "/operations",
                "/operations-governance",
                "/security-audit",
                "/security",
                "/notification-delivery",
                "/notifications",
                "/report-workflow",
                "/report-center",
            }:
                self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")
                return
            super().do_GET()
        except kernel.OperationsError as error:
            self._send_json(
                error.status,
                {"allowed": False, "code": error.code, "message_zh": error.message_zh},
            )

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            if path == "/api/operations/health-drill":
                body = self._json_body()
                self._send_json(
                    HTTPStatus.OK,
                    self.operations.failure_probe(body.get("session_token"), body.get("service_id")),
                )
                return
            if path == "/api/operations/backups":
                body = self._json_body()
                self._send_json(
                    HTTPStatus.CREATED,
                    self.operations.create_backup(body.get("session_token")),
                )
                return
            if path == "/api/operations/backups/verify":
                body = self._json_body()
                self._send_json(
                    HTTPStatus.OK,
                    self.operations.verify_backup(body.get("session_token"), body.get("backup_id")),
                )
                return
            if path == "/api/operations/backups/restore-drill":
                body = self._json_body()
                self._send_json(
                    HTTPStatus.OK,
                    self.operations.restore_drill(body.get("session_token"), body.get("backup_id")),
                )
                return
            if path == "/api/operations/migrations":
                body = self._json_body()
                self._send_json(
                    HTTPStatus.OK,
                    self.operations.migrate(body.get("session_token")),
                )
                return
            if path == "/api/operations/migrations/failure-drill":
                body = self._json_body()
                self._send_json(
                    HTTPStatus.OK,
                    self.operations.migration_failure_probe(
                        body.get("session_token"), body.get("surface", "FORMULA")
                    ),
                )
                return
            if path == "/api/operations/migrations/rollback":
                body = self._json_body()
                self._send_json(
                    HTTPStatus.OK,
                    self.operations.rollback(body.get("session_token"), body.get("migration_id")),
                )
                return
            if path.startswith("/api/operations/"):
                raise kernel.OperationsError("RESOURCE_NOT_FOUND", "没有找到这项运维操作", status=404)
            super().do_POST()
        except (TypeError, ValueError, kernel.OperationsError) as error:
            if isinstance(error, kernel.OperationsError):
                self._send_json(
                    error.status,
                    {"allowed": False, "code": error.code, "message_zh": error.message_zh},
                )
            else:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"allowed": False, "code": "INVALID_REQUEST", "message_zh": "请求格式不正确"},
                )


class OperationsServer(base_runtime.SecurityServer):
    operations_workbench: kernel.OperationsWorkbench


def _live_backup_state(server: OperationsServer) -> dict[str, object]:
    """Capture the current local runtime state without raw files or secret values."""

    notification_events = server.notification_journal.read()
    security_events = server.security_workbench.audit.events()
    operations_events = (
        server.operations_workbench.journal.events()
        if hasattr(server, "operations_workbench")
        else []
    )
    notification_options = notification_kernel.options_contract()
    return {
        "state_version": kernel.VERSION,
        "datasets": {
            "PRIVATE_DERIVED": {
                "source": "LIVE_RUNTIME",
                "notification_event_count": len(notification_events),
                "notification_events": notification_events,
            },
            "CONFIGURATION": {
                "source": "LIVE_RUNTIME",
                "notification_rules": notification_options["rules"],
                "service_definitions": kernel.SERVICE_DEFINITIONS,
                "migration_targets": kernel.TARGET_VERSIONS,
                "secret_value_count": 0,
            },
            "AUDIT_EVENTS": {
                "source": "LIVE_RUNTIME",
                "security_event_count": len(security_events),
                "operations_event_count": len(operations_events),
                "security_events": security_events,
                "operations_events": operations_events,
            },
        },
        "permissions": {
            key: list(items)
            for key, items in base_runtime.kernel.ROLE_PERMISSIONS.items()
        },
    }


def start_server(
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
    data_root: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.data_update_kernel.DEFAULT_RUNTIME_ROOT,
    confirmation_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    publication_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    report_model_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    export_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    export_bundle_root: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_BUNDLE_ROOT,
    workflow_event_path: Path | str = base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    notification_event_path: Path | str = base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    audit_event_path: Path | str = base_runtime.kernel.DEFAULT_EVENT_PATH,
    operations_root: Path | str = kernel.DEFAULT_RUNTIME_ROOT,
    secret_values: Mapping[str, str] | None = None,
    security_environment: str = "LOCAL_SANDBOX",
) -> tuple[OperationsServer, threading.Thread, str]:
    event_file = Path(event_path)
    server = OperationsServer((host, port), OperationsHandler)
    server.journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.workflow_kernel.EventJournal(event_file)
    server.policy_journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.reporting_kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    server.data_update_store = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.data_update_kernel.DataUpdateStore(data_root)
    server.confirmation_workbench = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.ConfirmationWorkbench(confirmation_event_path)
    server.recalculation_workbench = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.RecalculationPublicationWorkbench(confirmation_event_path, publication_event_path)
    server.report_model_journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.ReportModelJournal(report_model_event_path)
    server.report_export_journal = base_runtime.base_runtime.base_runtime.base_runtime.kernel.ReportExportJournal(export_event_path, export_bundle_root)
    server.report_workflow_journal = base_runtime.base_runtime.base_runtime.kernel.ReportWorkflowJournal(workflow_event_path)
    server.notification_journal = base_runtime.base_runtime.kernel.NotificationJournal(notification_event_path)
    server.security_workbench = base_runtime.kernel.SecurityWorkbench(
        audit_event_path,
        secret_values=secret_values,
        environment=security_environment,
    )
    server.operations_workbench = kernel.OperationsWorkbench(
        operations_root,
        server.security_workbench,
        state_provider=lambda: _live_backup_state(server),
    )
    thread = threading.Thread(
        target=server.serve_forever,
        name="kmfa-v015-s22p3-operations-governance",
        daemon=True,
    )
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S22-P3 运维、恢复与升级工作台")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--audit-event-path", default=str(base_runtime.kernel.DEFAULT_EVENT_PATH))
    parser.add_argument("--operations-root", default=str(kernel.DEFAULT_RUNTIME_ROOT))
    args = parser.parse_args()
    secret_values = {
        name: os.environ.get(name, "")
        for name in base_runtime.kernel.SECRET_REFERENCES
    }
    server, thread, url = start_server(
        args.host,
        args.port,
        audit_event_path=args.audit_event_path,
        operations_root=args.operations_root,
        secret_values=secret_values,
    )
    print(f"KMFA 运维、恢复与升级工作台：{url}/operations", flush=True)
    try:
        thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
