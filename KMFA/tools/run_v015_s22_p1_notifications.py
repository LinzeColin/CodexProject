#!/usr/bin/env python3
"""Run the KMFA v1.5 S22-P1 local notification workbench."""

from __future__ import annotations

import argparse
import re
import threading
from http import HTTPStatus
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from KMFA.tools import run_v015_s21_p3_report_workflow as base_runtime
from KMFA.tools import v015_s22_p1_notifications as kernel


_RULE_ACTION_ROUTE = re.compile(
    r"^/api/notification-delivery/rules/(RULE-[A-Z0-9-]+)/(silence|resume)$"
)
_RETRY_ROUTE = re.compile(
    r"^/api/notification-delivery/(NOTICE-S22P1-[A-F0-9]{12})/retry$"
)


def render_html() -> str:
    html_text = base_runtime.render_html()
    view = r'''
    <section id="notification-delivery-view" class="nd-view" aria-labelledby="nd-title" hidden>
      <header class="nd-head"><div><span>长期运行 · 第一步</span><h1 id="nd-title">通知只负责提醒，敏感内容留在 KMFA 内查看</h1><p>报告完成、重大风险和数据异常均写入本地邮件沙箱；当前阶段不会连接外部邮箱。</p></div><a href="/report-center">返回报告中心</a></header>
      <nav class="s22-journey" aria-label="长期运行三步流程"><a href="/notification-delivery" aria-current="step"><span>1</span>安全通知</a><a href="/security-audit"><span>2</span>登录与审计</a><a href="/operations"><span>3</span>运维与恢复</a></nav>
      <aside class="nd-boundary"><strong>当前安全边界</strong><span>收件人固定；正文只有提醒类型、期间、状态和应用内入口。无完整报告、金额、附件、密码、外部网络、原始资料、GitHub 或 App 操作。</span></aside>
      <section class="nd-summary" aria-label="通知摘要"><article><span>沙箱已接收</span><strong id="nd-sent-count">0</strong></article><article><span>已拦截重复/静默</span><strong id="nd-suppressed-count">0</strong></article><article><span>可重试失败</span><strong id="nd-failed-count">0</strong></article><article><span>外部发送</span><strong id="nd-external-count">0</strong></article></section>
      <div id="nd-feedback" class="nd-feedback" role="status" aria-live="polite">正在读取通知记录…</div>

      <section class="nd-card"><div class="nd-card-head"><div><h2>1. 报告完成提醒</h2><p>只发送报告类型、期间、状态和“报告中心”入口。</p></div><span id="nd-recipient"></span></div>
        <div class="nd-form"><label>报告类型<select id="nd-report-type"><option value="WEEKLY">周度经营报告</option><option value="MONTHLY" selected>月度经营报告</option><option value="QUARTERLY">季度经营报告</option><option value="SEMIANNUAL">半年度经营报告</option><option value="ANNUAL">年度经营报告</option></select></label><label>期间<input id="nd-report-period" value="2026年7月"></label><label>状态<select id="nd-report-status"><option value="GENERATED">已生成</option><option value="APPROVED">已批准</option><option value="PUBLISHED_INTERNAL" selected>内部已发布</option></select></label><button id="nd-send-report" class="nd-primary" type="button">写入邮件沙箱</button></div>
      </section>

      <section class="nd-card"><div class="nd-card-head"><div><h2>2. 风险与数据异常提醒</h2><p>现金、回款、税务、数据过期和导入失败五类规则已确认；未确认规则保持关闭。</p></div><span>每天每类最多 3 次</span></div>
        <div class="nd-form nd-alert-form"><label>提醒规则<select id="nd-alert-rule"></select></label><label>期间<input id="nd-alert-period" value="2026年7月"></label><label>状态<input id="nd-alert-status" value="需要查看"></label><label class="nd-check"><input id="nd-simulate-failure" type="checkbox">模拟一次可重试失败</label><button id="nd-send-alert" class="nd-primary" type="button">生成安全提醒</button></div>
        <div id="nd-rules" class="nd-rules"></div>
      </section>

      <section class="nd-card"><div class="nd-card-head"><div><h2>3. 投递、失败与重试记录</h2><p>重复请求不会重复投递；失败原因、下一次重试时间和每次尝试都保留在防篡改记录中。</p></div><span id="nd-event-count">0 条事件</span></div><div id="nd-history" class="nd-history"></div></section>
      <p class="nd-stop">S22-P1 验收后立即停止；权限、安全和审计属于下一次独立 Run 的 S22-P2。</p>
    </section>
    '''
    css = r'''
    body[data-notification-delivery-active="true"] main>section:not(#notification-delivery-view),body[data-notification-delivery-active="true"] #page-view,body[data-notification-delivery-active="true"] #loading-view,body[data-notification-delivery-active="true"] #error-view,body[data-notification-delivery-active="true"] #not-found-view,body[data-notification-delivery-active="true"] #homepage-view,body[data-notification-delivery-active="true"] #project-list-view,body[data-notification-delivery-active="true"] #project-detail-view,body[data-notification-delivery-active="true"] #project-workflow-view,body[data-notification-delivery-active="true"] #receivables-view,body[data-notification-delivery-active="true"] #funds-view,body[data-notification-delivery-active="true"] #funds-report-view,body[data-notification-delivery-active="true"] #tax-invoice-view,body[data-notification-delivery-active="true"] #policy-eligibility-view,body[data-notification-delivery-active="true"] #tax-policy-report-view,body[data-notification-delivery-active="true"] #data-update-view,body[data-notification-delivery-active="true"] #confirmation-workbench-view,body[data-notification-delivery-active="true"] #recalculation-publication-view,body[data-notification-delivery-active="true"] #report-model-view,body[data-notification-delivery-active="true"] #report-generation-view,body[data-notification-delivery-active="true"] #report-workflow-view,body[data-notification-delivery-active="true"] #context-status,body[data-notification-delivery-active="true"] .identity-shell,body[data-notification-delivery-active="true"] .quick-shell{display:none!important}body[data-notification-delivery-active="true"] main{max-width:1240px!important}.nd-view{padding:18px 10px 50px;color:#253b48}.nd-head{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;padding:22px;border-radius:12px;background:linear-gradient(135deg,#163b50,#25766f);color:#fff}.nd-head span{font-size:11px;font-weight:800;letter-spacing:.08em}.nd-head h1{margin:6px 0;font-size:29px;color:#fff!important}.nd-head p{margin:0;color:#ddf0ec}.nd-head a{display:inline-flex;min-height:44px;align-items:center;padding:0 14px;border:1px solid #b8d8d2;border-radius:8px;color:#fff;text-decoration:none;font-weight:800}.s22-journey{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}.s22-journey a{display:flex;align-items:center;gap:8px;min-height:44px;padding:8px 12px;border:1px solid #cddcdf;border-radius:8px;background:#fff;color:#36515e;text-decoration:none;font-weight:800}.s22-journey a span{display:grid;place-items:center;width:24px;height:24px;border-radius:50%;background:#e8f1f2;color:#285f61}.s22-journey a[aria-current="step"]{border-color:#25766f;background:#edf8f6;color:#174f56}.nd-boundary{display:flex;justify-content:space-between;gap:14px;margin:12px 0;padding:12px 14px;border:1px solid #d7b574;border-left:4px solid #ad7214;border-radius:8px;background:#fffaf0;color:#654817;font-size:12px}.nd-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:11px 0}.nd-summary article,.nd-card{padding:15px;border:1px solid #d8e3e7;border-radius:9px;background:#fff}.nd-summary span{display:block;color:#607783;font-size:11px}.nd-summary strong{display:block;margin-top:5px;color:#174f56;font-size:20px}.nd-feedback{min-height:44px;padding:11px 13px;border:1px solid #b9d7d2;border-left:4px solid #25766f;border-radius:7px;background:#eff9f7;font-size:13px}.nd-feedback[data-state="error"]{border-color:#d8a7a7;background:#fff8f7;color:#7f2929}.nd-feedback[data-state="success"]{color:#276346}.nd-card{margin-top:11px}.nd-card-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;margin-bottom:11px}.nd-card h2{margin:0;color:#20545a;font-size:18px}.nd-card-head p{margin:5px 0 0;color:#607783;font-size:11px}.nd-card-head>span{padding:6px 9px;border-radius:999px;background:#edf6f4;color:#245f59;font-size:11px;font-weight:800}.nd-form{display:grid;grid-template-columns:repeat(3,minmax(150px,1fr)) auto;gap:9px;align-items:end}.nd-alert-form{grid-template-columns:1.4fr .7fr .8fr auto auto}.nd-form label{display:grid;gap:5px;font-size:11px;font-weight:800}.nd-view input,.nd-view select,.nd-view button{min-height:44px;padding:0 11px;border:1px solid #b9cdd3;border-radius:7px;background:#fff;font:inherit}.nd-view button{font-weight:800;color:#245f59}.nd-primary{border-color:#25766f!important;background:#25766f!important;color:#fff!important}.nd-check{grid-template-columns:auto 1fr!important;align-items:center;min-height:44px;font-weight:600!important}.nd-check input{width:20px;min-height:20px}.nd-rules,.nd-history{display:grid;gap:8px;margin-top:12px}.nd-rule,.nd-event{display:grid;grid-template-columns:1.4fr .8fr auto;gap:10px;align-items:center;padding:10px;border:1px solid #dce7e9;border-radius:7px;background:#f8fbfb;font-size:11px}.nd-rule strong,.nd-event strong{display:block;color:#24575d}.nd-rule small,.nd-event small{color:#617983}.nd-event{grid-template-columns:1fr .7fr 1.2fr auto}.nd-event button{min-width:88px}.nd-stop{color:#607783;font-size:11px}
    @media(max-width:820px){.nd-head,.nd-boundary,.nd-card-head{display:grid}.nd-head a{justify-self:start}.s22-journey{grid-template-columns:1fr}.nd-summary,.nd-form,.nd-alert-form,.nd-rule,.nd-event{grid-template-columns:1fr}.nd-view button{width:100%}}
    '''
    script = r'''
    <script>
    (()=>{'use strict';if(!['/notification-delivery','/notifications'].includes(location.pathname))return;document.body.dataset.notificationDeliveryActive='true';document.querySelector('#notification-delivery-view').hidden=false;const state={options:null,snapshot:null},feedback=document.querySelector('#nd-feedback');let sequence=0;
      const api=async(path,init={})=>{const response=await fetch(path,init),value=await response.json();if(!response.ok)throw Object.assign(new Error(value.message_zh||'请求失败'),{payload:value,status:response.status});return value};const post=(path,body)=>{const sessionToken=sessionStorage.getItem('kmfa_s22_session_token'),payload={...(body||{})};if(sessionToken)payload.session_token=sessionToken;return api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})};const key=prefix=>prefix+'-'+Date.now()+'-'+(++sequence);const say=(text,kind='')=>{feedback.textContent=text;if(kind)feedback.dataset.state=kind;else delete feedback.dataset.state};
      const render=value=>{state.snapshot=value;document.querySelector('#nd-sent-count').textContent=value.sent_sandbox_count;document.querySelector('#nd-suppressed-count').textContent=value.suppressed_count;document.querySelector('#nd-failed-count').textContent=value.failed_retryable_count;document.querySelector('#nd-external-count').textContent=value.external_network_request_count;document.querySelector('#nd-event-count').textContent=value.event_count+' 条事件';const rules=document.querySelector('#nd-rules');rules.replaceChildren();value.rules.forEach(row=>{const card=document.createElement('article');card.className='nd-rule';const copy=document.createElement('div'),title=document.createElement('strong'),meta=document.createElement('small'),status=document.createElement('span'),button=document.createElement('button');title.textContent=row.category_zh;meta.textContent=row.confirmed?(row.enabled?'规则已确认':'规则已关闭'):'规则未确认，禁止发送';status.textContent=row.enabled?(row.silenced?'已静默':'运行中'):'未启用';copy.append(title,meta);button.type='button';button.textContent=row.silenced?'恢复提醒':'静默规则';button.disabled=!row.enabled;button.addEventListener('click',()=>setSilenced(row.rule_id,!row.silenced).catch(error=>say(error.message,'error')));card.append(copy,status,button);rules.append(card)});const history=document.querySelector('#nd-history');history.replaceChildren();value.notifications.forEach(row=>{const card=document.createElement('article');card.className='nd-event';const copy=document.createElement('div'),title=document.createElement('strong'),meta=document.createElement('small'),status=document.createElement('span'),reason=document.createElement('span');title.textContent=row.message.subject_zh;meta.textContent=row.message.body_text.replaceAll('\n',' · ');status.textContent=row.status;reason.textContent=row.failure_code||row.suppression_reason||'本地沙箱已记录';card.append(copy,status,reason);copy.append(title,meta);if(row.status==='FAILED_RETRYABLE'){const button=document.createElement('button');button.type='button';button.textContent='幂等重试';button.addEventListener('click',()=>retry(row.notification_id).catch(error=>say(error.message,'error')));card.append(button)}history.append(card)})};
      const load=async()=>{const [options,snapshot]=await Promise.all([api('/api/notification-delivery/options'),api('/api/notification-delivery')]);state.options=options;document.querySelector('#nd-recipient').textContent='固定收件人：'+options.recipient;const select=document.querySelector('#nd-alert-rule'),current=select.value;select.replaceChildren();options.rules.filter(row=>row.category!=='REPORT').forEach(row=>{const option=new Option(row.category_zh+(row.enabled?'':'（未启用）'),row.rule_id);option.disabled=!row.enabled;select.append(option)});if([...select.options].some(row=>row.value===current))select.value=current;render(snapshot);say('本地邮件沙箱可用；外部发送保持 0。','success');return state};
      const sendReport=async()=>{const value=await post('/api/notification-delivery/report',{report_version_id:'REPORT-BROWSER-'+Date.now(),report_type:document.querySelector('#nd-report-type').value,period_label:document.querySelector('#nd-report-period').value,report_status:document.querySelector('#nd-report-status').value,idempotency_key:key('browser-report')});await load();say(value.status==='SENT_SANDBOX'?'报告提醒已写入本地邮件沙箱。':'提醒已被安全策略拦截。','success');return value};
      const sendAlert=async()=>{const value=await post('/api/notification-delivery/alert',{rule_id:document.querySelector('#nd-alert-rule').value,alert_ref:'ALERT-BROWSER-'+Date.now(),period_label:document.querySelector('#nd-alert-period').value,alert_status:document.querySelector('#nd-alert-status').value,simulate_failure:document.querySelector('#nd-simulate-failure').checked,idempotency_key:key('browser-alert')});await load();say(value.status==='FAILED_RETRYABLE'?'已记录失败原因，可点击重试。':'安全提醒已处理。','success');return value};
      const setSilenced=async(ruleId,silenced)=>{const value=await post('/api/notification-delivery/rules/'+ruleId+'/'+(silenced?'silence':'resume'),{idempotency_key:key('browser-rule')});await load();say(silenced?'规则已静默。':'规则已恢复。','success');return value};const retry=async(noticeId)=>{const value=await post('/api/notification-delivery/'+noticeId+'/retry',{idempotency_key:key('browser-retry')});await load();say('重试成功，仍只写入本地邮件沙箱。','success');return value};
      document.querySelector('#nd-send-report').addEventListener('click',()=>sendReport().catch(error=>say(error.message,'error')));document.querySelector('#nd-send-alert').addEventListener('click',()=>sendAlert().catch(error=>say(error.message,'error')));window.KMFA_NOTIFICATION_TEST={snapshot:()=>structuredClone(state),load,sendReport,sendAlert,setSilenced,retry};load().catch(error=>say(error.message,'error'));
    })();
    </script>
    '''
    html_text = html_text.replace("</main>", view + "</main>", 1)
    html_text = html_text.replace("</style>", css + "</style>", 1)
    html_text = html_text.replace("</body>", script + "</body>", 1)
    html_text = html_text.replace(
        '<p class="rw-stop">S21-P3 验收后立即停止；下一次独立 Run 只做 S21 整体复审，不进入 S22。</p>',
        '<p class="rw-stop">报告发布后，可进入 <a href="/notification-delivery">通知中心</a>；提醒只写入本地邮件沙箱。</p>',
    )
    html_text = html_text.replace(
        "<title>KMFA 报告工作流 · 经营工作台</title>",
        "<title>KMFA 安全通知 · 经营工作台</title>",
    )
    return "\n".join(line.rstrip() for line in html_text.splitlines()) + "\n"


class NotificationHandler(base_runtime.ReportWorkflowHandler):
    server_version = "KMFANotificationDelivery/1.5"

    @property
    def notifications(self) -> kernel.NotificationJournal:
        return self.server.notification_journal  # type: ignore[attr-defined,no-any-return]

    def _authorize_notification(
        self,
        body: Mapping[str, object],
        *,
        action_type: str,
        subject_ref: str,
    ) -> None:
        """P1 is local-sandbox only; later security runtimes override this hook."""

        del body, action_type, subject_ref

    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            if path == "/api/notification-delivery/options":
                self._send_json(HTTPStatus.OK, kernel.options_contract())
                return
            if path == "/api/notification-delivery":
                self._send_json(HTTPStatus.OK, self.notifications.snapshot())
                return
            if path.startswith("/api/notification-delivery/"):
                raise kernel.NotificationError("RESOURCE_NOT_FOUND", "没有找到这条通知记录", status=404)
            if path in {"/notification-delivery", "/notifications", "/report-workflow", "/report-center"}:
                self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")
                return
            super().do_GET()
        except kernel.NotificationError as error:
            self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            if path == "/api/notification-delivery/report":
                body = self._json_body()
                self._authorize_notification(
                    body, action_type="PROCESSING", subject_ref="NOTIFICATION::REPORT"
                )
                value = self.notifications.dispatch_report(
                    report_version_id=body.get("report_version_id"), report_type=body.get("report_type"),
                    period_label=body.get("period_label"), report_status=body.get("report_status"),
                    idempotency_key=body.get("idempotency_key"), occurred_at=body.get("occurred_at"),
                    simulate_failure=bool(body.get("simulate_failure", False)),
                )
                self._send_json(HTTPStatus.CREATED, value)
                return
            if path == "/api/notification-delivery/alert":
                body = self._json_body()
                self._authorize_notification(
                    body, action_type="PROCESSING", subject_ref="NOTIFICATION::ALERT"
                )
                value = self.notifications.dispatch_alert(
                    rule_id=body.get("rule_id"), alert_ref=body.get("alert_ref"),
                    period_label=body.get("period_label"), alert_status=body.get("alert_status"),
                    idempotency_key=body.get("idempotency_key"), occurred_at=body.get("occurred_at"),
                    simulate_failure=bool(body.get("simulate_failure", False)),
                )
                self._send_json(HTTPStatus.CREATED, value)
                return
            rule_match = _RULE_ACTION_ROUTE.fullmatch(path)
            if rule_match:
                body = self._json_body()
                self._authorize_notification(
                    body,
                    action_type="PARAMETER_CHANGE",
                    subject_ref=f"NOTIFICATION::{rule_match.group(1)}",
                )
                value = self.notifications.set_rule_silenced(
                    rule_match.group(1), rule_match.group(2) == "silence",
                    idempotency_key=body.get("idempotency_key"), occurred_at=body.get("occurred_at"),
                )
                self._send_json(HTTPStatus.OK, value)
                return
            retry_match = _RETRY_ROUTE.fullmatch(path)
            if retry_match:
                body = self._json_body()
                self._authorize_notification(
                    body,
                    action_type="PROCESSING",
                    subject_ref=f"NOTIFICATION::{retry_match.group(1)}",
                )
                value = self.notifications.retry(
                    retry_match.group(1), idempotency_key=body.get("idempotency_key"),
                    occurred_at=body.get("occurred_at"), simulate_failure=bool(body.get("simulate_failure", False)),
                )
                self._send_json(HTTPStatus.OK, value)
                return
            if path.startswith("/api/notification-delivery/"):
                raise kernel.NotificationError("RESOURCE_NOT_FOUND", "没有找到这条通知操作", status=404)
            super().do_POST()
        except (TypeError, kernel.NotificationError) as error:
            if isinstance(error, kernel.NotificationError):
                self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})
            else:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "code": "INVALID_REQUEST", "message_zh": "请求格式不正确"})


class NotificationServer(base_runtime.ReportWorkflowServer):
    notification_journal: kernel.NotificationJournal


def start_server(
    host: str = "127.0.0.1", port: int = 0, *,
    event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
    data_root: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.data_update_kernel.DEFAULT_RUNTIME_ROOT,
    confirmation_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    publication_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    report_model_event_path: Path | str = base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    export_event_path: Path | str = base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    export_bundle_root: Path | str = base_runtime.base_runtime.kernel.DEFAULT_BUNDLE_ROOT,
    workflow_event_path: Path | str = base_runtime.kernel.DEFAULT_EVENT_PATH,
    notification_event_path: Path | str = kernel.DEFAULT_EVENT_PATH,
) -> tuple[NotificationServer, threading.Thread, str]:
    event_file = Path(event_path)
    server = NotificationServer((host, port), NotificationHandler)
    server.journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.workflow_kernel.EventJournal(event_file)
    server.policy_journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.reporting_kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    server.data_update_store = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.data_update_kernel.DataUpdateStore(data_root)
    server.confirmation_workbench = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.ConfirmationWorkbench(confirmation_event_path)
    server.recalculation_workbench = base_runtime.base_runtime.base_runtime.base_runtime.kernel.RecalculationPublicationWorkbench(confirmation_event_path, publication_event_path)
    server.report_model_journal = base_runtime.base_runtime.base_runtime.kernel.ReportModelJournal(report_model_event_path)
    server.report_export_journal = base_runtime.base_runtime.kernel.ReportExportJournal(export_event_path, export_bundle_root)
    server.report_workflow_journal = base_runtime.kernel.ReportWorkflowJournal(workflow_event_path)
    server.notification_journal = kernel.NotificationJournal(notification_event_path)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s22p1-notifications", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S22-P1 安全通知中心")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--notification-event-path", default=str(kernel.DEFAULT_EVENT_PATH))
    args = parser.parse_args()
    server, thread, url = start_server(args.host, args.port, notification_event_path=args.notification_event_path)
    print(f"KMFA 安全通知中心：{url}/notification-delivery", flush=True)
    try:
        thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
