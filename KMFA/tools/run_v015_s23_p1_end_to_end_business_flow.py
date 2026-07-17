#!/usr/bin/env python3
"""Run the KMFA v1.5 S23-P1 authoritative end-to-end workbench."""

from __future__ import annotations

import argparse
import os
import re
import threading
from http import HTTPStatus
from pathlib import Path
from typing import Mapping
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s22_p3_operations_governance as base_runtime
from KMFA.tools import run_v015_s16_p3_homepage_usability as homepage_runtime
from KMFA.tools import v015_s16_p3_homepage_usability as homepage_usability
from KMFA.tools import v015_s21_p3_report_workflow as workflow_kernel
from KMFA.tools import v015_s21_p2_report_generation as report_generation
from KMFA.tools import v015_s23_p1_end_to_end_business_flow as kernel


_XLSX_ROUTE = re.compile(r"^/api/report-exports/(EXPORT-S23P1-[A-F0-9]{16})/report\.xlsx$")


def render_html() -> str:
    """Add one human-readable end-to-end status page to the accepted workbench."""

    html_text = base_runtime.render_html()
    view = r'''
    <section id="end-to-end-view" class="e2e-view" aria-labelledby="e2e-title" hidden>
      <header class="e2e-head"><div><span>真实业务验收 · 第一步</span><h1 id="e2e-title">一套数字，贯穿首页、项目重算和经营报告</h1><p>当前页面直接核对后端发布版本、首页、项目、报告、审批和四种导出文件；任一分差异都会阻止通过。</p></div><a href="/overview">返回经营首页</a></header>
      <aside class="e2e-boundary"><strong>本轮边界</strong><span>只使用本地公开合成数据；不读取 raw，不连接外部网络，不上传 GitHub，不重装 App。</span></aside>
      <section class="e2e-summary" aria-label="端到端验收摘要">
        <article><span>权威发布版本</span><strong id="e2e-publication">读取中</strong></article>
        <article><span>项目分差异</span><strong id="e2e-project-difference">—</strong></article>
        <article><span>报告版本</span><strong id="e2e-report">尚未生成</strong></article>
        <article><span>导出格式</span><strong id="e2e-formats">0 / 4</strong></article>
        <article><span>审批状态</span><strong id="e2e-workflow">尚未开始</strong></article>
      </section>
      <div id="e2e-feedback" class="e2e-feedback" role="status" aria-live="polite">正在核对权威版本…</div>
      <section class="e2e-card"><h2>完整业务路径</h2><p>按顺序执行即可；每一步都保留后端记录和刷新持久化证据。</p><nav class="e2e-flow" aria-label="端到端业务步骤">
        <a href="/overview"><span>1</span><strong>经营首页</strong><small>看状态与重点事项</small></a>
        <a href="/data-update"><span>2</span><strong>导入项目成本</strong><small>先预览，再确认</small></a>
        <a href="/confirmation-workbench"><span>3</span><strong>处理差异</strong><small>人工确认依据</small></a>
        <a href="/recalculation-publication"><span>4</span><strong>重算并发布</strong><small>四个页面同版本</small></a>
        <a href="/report-model"><span>5</span><strong>建立报告</strong><small>绑定当前发布版本</small></a>
        <a href="/report-generation"><span>6</span><strong>生成报告</strong><small>HTML、PDF、CSV、Excel</small></a>
        <a href="/report-workflow"><span>7</span><strong>复核与修订</strong><small>五步审批并保留旧版</small></a>
      </nav></section>
      <section id="e2e-output-card" class="e2e-card" hidden><div class="e2e-card-head"><div><h2>同一报告的四种文件</h2><p id="e2e-fingerprint">—</p></div><button id="e2e-refresh" type="button">刷新核验</button></div><div id="e2e-downloads" class="e2e-downloads"></div></section>
      <p class="e2e-stop">S23-P1 验收后停止；压力/极限、恢复测试和 Stage 整体复审属于后续独立 Run。</p>
    </section>
    '''
    css = r'''
    body[data-e2e-active="true"] main>section:not(#end-to-end-view),body[data-e2e-active="true"] #context-status,body[data-e2e-active="true"] .identity-shell,body[data-e2e-active="true"] .quick-shell,body[data-e2e-active="true"] #access-workspace,body[data-e2e-active="true"] #experience-workspace{display:none!important}
    .e2e-view{margin:2px 0 32px;color:#29475d}.e2e-head{display:flex;justify-content:space-between;align-items:flex-start;gap:18px}.e2e-head span{font-size:12px;font-weight:800;color:#17648f}.e2e-head h1{margin:4px 0;font-size:30px;color:#173d57}.e2e-head p{max-width:800px;margin:6px 0;color:#607684;font-size:13px}.e2e-head a,.e2e-card button{display:inline-flex;min-height:44px;align-items:center;justify-content:center;padding:0 14px;border:1px solid #9fb8c8;border-radius:7px;background:#fff;color:#245a7a;font:inherit;font-size:12px;font-weight:800;text-decoration:none;cursor:pointer}.e2e-boundary{display:flex;justify-content:space-between;gap:14px;margin:12px 0;padding:12px 14px;border:1px solid #d5b27c;border-left:4px solid #a86a17;border-radius:8px;background:#fffaf2;color:#654519;font-size:12px}.e2e-summary{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:11px 0}.e2e-summary article,.e2e-card{min-width:0;padding:15px;border:1px solid #d8e2e8;border-radius:9px;background:#fff}.e2e-summary span{display:block;color:#607684;font-size:11px}.e2e-summary strong{display:block;margin-top:5px;color:#173d57;font-size:17px;overflow-wrap:anywhere}.e2e-feedback{min-height:44px;padding:11px 13px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:7px;background:#edf6fb;font-size:13px}.e2e-feedback[data-state="pass"]{border-color:#9fc5ae;background:#f3faf5;color:#276346}.e2e-feedback[data-state="pending"]{border-color:#d5b27c;background:#fffaf2;color:#654519}.e2e-card{margin-top:11px}.e2e-card h2{margin:0;color:#214d68;font-size:18px}.e2e-card p{margin:5px 0 0;color:#607684;font-size:11px}.e2e-card-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start}.e2e-card-head>*{min-width:0}.e2e-card-head p{overflow-wrap:anywhere;word-break:break-all}.e2e-flow{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:8px;margin-top:12px}.e2e-flow a{display:grid;grid-template-columns:30px 1fr;grid-template-rows:auto auto;column-gap:7px;min-height:70px;padding:10px;border:1px solid #cbd9e1;border-radius:8px;background:#f8fbfc;color:#31576b;text-decoration:none}.e2e-flow span{grid-row:1/3;display:grid;place-items:center;width:28px;height:28px;border-radius:50%;background:#246c83;color:#fff;font-weight:800}.e2e-flow strong{font-size:11px}.e2e-flow small{color:#657c89;font-size:9px}.e2e-downloads{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}.e2e-downloads a{display:flex;min-height:44px;align-items:center;justify-content:center;border:1px solid #9fb8c8;border-radius:7px;color:#245a7a;font-size:12px;font-weight:800;text-decoration:none}.e2e-stop{color:#607684;font-size:11px}
    @media(max-width:1100px){.e2e-summary{grid-template-columns:repeat(3,1fr)}.e2e-flow{grid-template-columns:repeat(4,1fr)}}
    @media(max-width:620px){.e2e-head,.e2e-boundary,.e2e-card-head{display:grid}.e2e-head h1{font-size:25px}.e2e-summary,.e2e-flow,.e2e-downloads{grid-template-columns:1fr}.e2e-head a,.e2e-card button{width:100%}}
    '''
    script = r'''
    <script>
    (()=>{'use strict';if(location.pathname!=='/end-to-end')return;document.body.dataset.e2eActive='true';document.querySelector('#end-to-end-view').hidden=false;
      let state=null;const feedback=document.querySelector('#e2e-feedback');
      const load=async()=>{const response=await fetch('/api/end-to-end/status'),value=await response.json();if(!response.ok)throw new Error(value.message_zh||'端到端状态读取失败');state=value;document.querySelector('#e2e-publication').textContent=value.publication_version_id;document.querySelector('#e2e-project-difference').textContent=value.project_difference_cents+' 分';document.querySelector('#e2e-report').textContent=value.report_version_id||'尚未生成';document.querySelector('#e2e-formats').textContent=value.format_count+' / 4';document.querySelector('#e2e-workflow').textContent=value.workflow_state_zh;feedback.textContent=value.status_zh;feedback.dataset.state=value.status==='PASS'?'pass':'pending';const card=document.querySelector('#e2e-output-card'),root=document.querySelector('#e2e-downloads');card.hidden=!value.export_id;root.replaceChildren();if(value.export_id){document.querySelector('#e2e-fingerprint').textContent='报告指纹 '+value.report_payload_fingerprint;const items=[['网页报告','html'],['PDF 报告','pdf'],['专业附表 CSV','appendix.csv'],['Excel 报告','report.xlsx']];items.forEach(([label,suffix])=>{const link=document.createElement('a');link.textContent=label;link.href='/api/report-exports/'+value.export_id+'/'+suffix;link.dataset.format=suffix;root.append(link)})}return value};
      document.querySelector('#e2e-refresh').addEventListener('click',()=>load().catch(error=>{feedback.textContent=error.message;feedback.dataset.state='pending'}));window.KMFA_END_TO_END_TEST={load,snapshot:()=>structuredClone(state)};load().catch(error=>{feedback.textContent=error.message;feedback.dataset.state='pending'});
    })();
    </script>
    '''
    html_text = html_text.replace("</main>", view + "</main>", 1)
    html_text = html_text.replace("</style>", css + "</style>", 1)
    html_text = html_text.replace("</body>", script + "</body>", 1)
    html_text = html_text.replace("<title>KMFA 运维、恢复与升级 · 经营工作台</title>", "<title>KMFA 端到端业务验收 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html_text.splitlines()) + "\n"


def _case_for_report(server: "EndToEndServer", report_version_id: str):
    return next(
        (row for row in server.report_workflow_journal.list()["cases"] if row["report_version_id"] == report_version_id),
        None,
    )


def end_to_end_status(server: "EndToEndServer") -> dict[str, object]:
    publication = server.recalculation_workbench.current_publication()
    home = kernel.authoritative_homepage_snapshot(publication)
    reports = server.report_model_journal.list()["reports"]
    exports = server.report_export_journal.list()["exports"]
    report = reports[0] if reports else None
    export = exports[0] if exports else None
    workflow = _case_for_report(server, str(report["report_version_id"])) if report else None
    status = "READY"
    zero = {
        "project_difference_cents": 0,
        "difference_cents": 0,
    }
    if export:
        zero = kernel.assert_authoritative_zero_difference(
            publication, home, export["report_payload_snapshot"]
        )
        status = "PASS" if workflow and workflow["state"] == "PUBLISHED_INTERNAL" else "REPORT_READY"
    state_labels = {
        None: "尚未开始",
        "PREVIEWED": "已预览",
        "IN_REVIEW": "复核中",
        "REVIEWED": "复核通过",
        "APPROVED": "已批准",
        "PUBLISHED_INTERNAL": "已内部发布",
    }
    return {
        "schema_version": "kmfa.v015.s23p1.end_to_end_status.v1",
        "status": status,
        "status_zh": {
            "READY": "权威版本已就绪，请继续完成项目更新与报告流程。",
            "REPORT_READY": "四种报告文件已经零差异生成，请完成审批。",
            "PASS": "首页、项目、报告、审批和四种导出文件全部使用同一权威版本，差异为 0。",
        }[status],
        "publication_version_id": publication["publication_version_id"],
        "shared_metric_fingerprint": publication["consistency"]["shared_metric_fingerprint"],
        "homepage_publication_version_id": home.get("publication_version_id"),
        "report_version_id": report.get("report_version_id") if report else None,
        "report_publication_version_id": export.get("publication_version_id") if export else None,
        "report_payload_fingerprint": export.get("report_payload_fingerprint") if export else None,
        "export_id": export.get("export_id") if export else None,
        "format_count": len(export.get("files", {})) if export else 0,
        "formats": sorted(export.get("files", {})) if export else [],
        "workflow_state": workflow.get("state") if workflow else None,
        "workflow_state_zh": state_labels[workflow.get("state") if workflow else None],
        "project_difference_cents": zero["project_difference_cents"],
        "difference_cents": zero["difference_cents"],
        "refresh_persistence_required": True,
        **kernel.scope_boundary(),
    }


class EndToEndHandler(base_runtime.OperationsHandler):
    server_version = "KMFAEndToEndBusinessFlow/1.5"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path
        try:
            if path == "/api/homepage":
                query = parse_qs(parsed.query)
                usability_state = query.get("usability_state", ["ready"])[0]
                if usability_state != "ready":
                    super().do_GET()
                    return
                value = kernel.authoritative_homepage_snapshot(
                    self.server.recalculation_workbench.current_publication(),  # type: ignore[attr-defined]
                    user_id=query.get("user_id", ["demo-owner"])[0],
                    role_id=query.get("role_id", ["management"])[0],
                    company_id=query.get("company_id", ["demo-north"])[0],
                    period=query.get("period", ["2026-07"])[0],
                    data_state=query.get("data_state", ["complete"])[0],
                )
                if not value.get("allowed"):
                    value = homepage_runtime._permission_state(value)
                self._send_json(HTTPStatus.OK if value.get("allowed") else HTTPStatus.FORBIDDEN, value)
                return
            if path == "/api/end-to-end/status":
                self._send_json(HTTPStatus.OK, end_to_end_status(self.server))  # type: ignore[arg-type]
                return
            match = _XLSX_ROUTE.fullmatch(path)
            if match:
                export = self.server.report_export_journal.get(match.group(1))  # type: ignore[attr-defined]
                report = self.server.report_model_journal.get(export["report_version_id"])  # type: ignore[attr-defined]
                case = _case_for_report(self.server, report["report_version_id"])  # type: ignore[arg-type]
                decision = workflow_kernel.authorize_download(
                    report,
                    case,
                    user_id=self.headers.get("X-KMFA-User", ""),
                    role_id=self.headers.get("X-KMFA-Role", ""),
                    company_id=self.headers.get("X-KMFA-Company", ""),
                    format_name="PDF",
                )
                if not decision["allowed"]:
                    raise workflow_kernel.ReportWorkflowError(str(decision["code"]), str(decision["reason_zh"]), status=403)
                file_path, metadata = self.server.report_export_journal.file_path(match.group(1), "XLSX")  # type: ignore[attr-defined]
                self._send_download(file_path.read_bytes(), metadata["content_type"], metadata["filename"])
                return
            if path == "/end-to-end":
                self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")
                return
            super().do_GET()
        except (
            kernel.EndToEndFlowError,
            report_generation.ReportGenerationError,
            workflow_kernel.ReportWorkflowError,
        ) as error:
            self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})


class EndToEndServer(base_runtime.OperationsServer):
    report_export_journal: kernel.AuthoritativeReportExportJournal


def start_server(
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
    data_root: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.data_update_kernel.DEFAULT_RUNTIME_ROOT,
    confirmation_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    publication_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    report_model_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    export_event_path: Path | str = kernel.DEFAULT_EVENT_PATH,
    export_bundle_root: Path | str = kernel.DEFAULT_BUNDLE_ROOT,
    workflow_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    notification_event_path: Path | str = base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    audit_event_path: Path | str = base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    operations_root: Path | str = base_runtime.kernel.DEFAULT_RUNTIME_ROOT,
    xlsx_preview_root: Path | str = kernel.DEFAULT_XLSX_PREVIEW_ROOT,
    secret_values: Mapping[str, str] | None = None,
    security_environment: str = "LOCAL_SANDBOX",
) -> tuple[EndToEndServer, threading.Thread, str]:
    event_file = Path(event_path)
    server = EndToEndServer((host, port), EndToEndHandler)
    server.journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.workflow_kernel.EventJournal(event_file)
    server.policy_journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.reporting_kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    server.data_update_store = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.data_update_kernel.DataUpdateStore(data_root)
    server.confirmation_workbench = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.ConfirmationWorkbench(confirmation_event_path)
    server.recalculation_workbench = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.RecalculationPublicationWorkbench(confirmation_event_path, publication_event_path)
    server.report_model_journal = base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.base_runtime.kernel.ReportModelJournal(report_model_event_path)
    server.report_export_journal = kernel.AuthoritativeReportExportJournal(
        export_event_path,
        export_bundle_root,
        publication_provider=server.recalculation_workbench.current_publication,
        preview_root=xlsx_preview_root,
    )
    server.report_workflow_journal = base_runtime.base_runtime.base_runtime.base_runtime.kernel.ReportWorkflowJournal(workflow_event_path)
    server.notification_journal = base_runtime.base_runtime.base_runtime.kernel.NotificationJournal(notification_event_path)
    server.security_workbench = base_runtime.base_runtime.kernel.SecurityWorkbench(
        audit_event_path, secret_values=secret_values, environment=security_environment
    )
    server.operations_workbench = base_runtime.kernel.OperationsWorkbench(
        operations_root,
        server.security_workbench,
        state_provider=lambda: base_runtime._live_backup_state(server),
    )
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s23p1-end-to-end", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S23-P1 端到端业务验收")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    secret_values = {name: os.environ.get(name, "") for name in base_runtime.base_runtime.kernel.SECRET_REFERENCES}
    server, thread, url = start_server(args.host, args.port, secret_values=secret_values)
    print(f"KMFA 端到端业务验收：{url}/end-to-end", flush=True)
    try:
        thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
