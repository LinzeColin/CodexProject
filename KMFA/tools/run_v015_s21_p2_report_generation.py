#!/usr/bin/env python3
"""Run the KMFA v1.5 S21-P2 local report-generation workbench."""

from __future__ import annotations

import argparse
import json
import re
import threading
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlsplit

from KMFA.tools import run_v015_s21_p1_report_model as base_runtime
from KMFA.tools import v015_s21_p2_report_generation as kernel


_EXPORT_ROUTE = re.compile(r"^/api/report-exports/(EXPORT-[A-Z0-9-]+)$")
_FILE_ROUTE = re.compile(r"^/api/report-exports/(EXPORT-[A-Z0-9-]+)/(html|pdf|appendix\.csv)$")


def render_html() -> str:
    html_text = base_runtime.render_html()
    view = r'''
    <section id="report-generation-view" class="rg-view" aria-labelledby="rg-title" hidden>
      <header class="rg-head"><div><span>经营报告 · 第二步</span><h1 id="rg-title">一份事实数据，生成三种一致的报告</h1><p>网页适合阅读和打印，PDF 适合归档，专业附表保留整数值、口径、来源和差异。</p></div><a href="/report-model">返回报告模型</a></header>
      <nav class="s21-journey" aria-label="经营报告流程步骤"><a href="/report-model"><span>1</span><strong>报告模型</strong><small>期间、版本与受众</small></a><a href="/report-generation" aria-current="step"><span>2</span><strong>生成报告</strong><small>网页、PDF 与附表</small></a><a href="/report-workflow"><span>3</span><strong>复核发布</strong><small>审批、修订与报告中心</small></a></nav>
      <aside class="rg-boundary"><strong>本步骤的边界</strong><span>只生成内部复核文件；不审批、不发布，也不读取原始财务文件。</span></aside>
      <section class="rg-summary" aria-label="导出能力"><article><span>网页报告</span><strong>响应式 · 可打印</strong></article><article><span>PDF 报告</span><strong>分页 · 页码 · 来源</strong></article><article><span>专业附表</span><strong>CSV · 整数零差异</strong></article></section>
      <div id="rg-feedback" class="rg-feedback" role="status" aria-live="polite">正在读取报告版本…</div>
      <section class="rg-card"><div class="rg-card-head"><div><h2>1. 选择报告版本</h2><p>只能选择资料齐备的公开合成报告版本；生成后不会覆盖历史文件。</p></div></div><form id="rg-create-form" class="rg-form"><label>报告版本<select id="rg-report-version"></select></label><button class="rg-primary" type="submit">生成三种报告</button></form></section>
      <section class="rg-card"><div class="rg-card-head"><div><h2>2. 下载与核对</h2><p id="rg-export-count">0 份导出</p></div></div><div id="rg-empty" class="rg-empty">尚未生成报告。</div><div id="rg-list" class="rg-list"></div></section>
      <p class="rg-stop">S21-P2 完成本地验收后停止。审批发布属于 S21-P3；GitHub 上传和 App 重装要等全部任务包完成。</p>
    </section>
    '''
    css = r'''
    body[data-report-generation-active="true"] main>section:not(#report-generation-view){display:none!important}body[data-report-generation-active="true"] main{max-width:1240px!important}.rg-view{padding:18px 10px 50px;color:#263b49}.rg-head{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;padding:22px;border-radius:12px;background:linear-gradient(135deg,#173d57,#246c83);color:#fff}.rg-head span{font-size:11px;font-weight:800;letter-spacing:.08em}.rg-head h1{margin:6px 0;font-size:30px}.rg-head p{margin:0;color:#dcebf2}.rg-head a{display:inline-flex;min-height:44px;align-items:center;padding:0 14px;border:1px solid #b9d2df;border-radius:8px;color:#fff;text-decoration:none;font-weight:800}.s21-journey{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}.s21-journey a{display:grid;grid-template-columns:34px 1fr;grid-template-rows:auto auto;column-gap:9px;min-height:52px;padding:9px 11px;border:1px solid #cbd9e1;border-radius:8px;background:#fff;color:#31576b;text-decoration:none}.s21-journey a[aria-current="step"]{border-color:#246c83;background:#edf6f9}.s21-journey span{grid-row:1/3;align-self:center;display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:#246c83;color:#fff;font-weight:800}.s21-journey strong{align-self:end;font-size:12px}.s21-journey small{color:#657c89;font-size:10px}.rg-boundary{display:flex;justify-content:space-between;gap:14px;margin:12px 0;padding:12px 14px;border:1px solid #d5b27c;border-left:4px solid #a86a17;border-radius:8px;background:#fffaf2;color:#654519;font-size:12px}.rg-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:11px 0}.rg-summary article,.rg-card{padding:15px;border:1px solid #d8e2e8;border-radius:9px;background:#fff}.rg-summary span{display:block;color:#607684;font-size:11px}.rg-summary strong{display:block;margin-top:5px;color:#173d57;font-size:16px}.rg-feedback{min-height:44px;padding:11px 13px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:7px;background:#edf6fb;font-size:13px}.rg-feedback[data-state="error"]{border-color:#d7a6a6;background:#fff8f7;color:#7f2929}.rg-feedback[data-state="success"]{border-color:#9fc5ae;background:#f3faf5;color:#276346}.rg-card{margin-top:11px}.rg-card-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;margin-bottom:11px}.rg-card h2{margin:0;color:#214d68;font-size:18px}.rg-card-head p{margin:5px 0 0;color:#607684;font-size:11px}.rg-form{display:grid;grid-template-columns:minmax(240px,1fr) auto;gap:10px;align-items:end}.rg-form label{display:grid;gap:5px;font-size:11px;font-weight:800}.rg-form select,.rg-view button{min-height:44px;padding:0 12px;border:1px solid #b9cbd7;border-radius:7px;background:#fff;font:inherit}.rg-primary{border:0!important;background:#246c83!important;color:#fff!important;font-weight:800}.rg-empty{padding:18px;border:1px dashed #b9cbd7;border-radius:8px;color:#607684;text-align:center}.rg-list{display:grid;gap:9px}.rg-export{padding:14px;border:1px solid #dce5ea;border-radius:8px}.rg-export header{display:flex;justify-content:space-between;gap:12px}.rg-export h3{margin:0;color:#214d68;font-size:14px}.rg-export p{margin:4px 0;color:#607684;font-size:11px}.rg-downloads{display:flex;flex-wrap:wrap;gap:8px;margin-top:11px}.rg-downloads a{display:inline-flex;min-height:44px;align-items:center;padding:0 13px;border:1px solid #9fb8c8;border-radius:7px;color:#245a7a;text-decoration:none;font-weight:800}.rg-pass{color:#276346;font-weight:800}.rg-stop{color:#607684;font-size:11px}
    @media(max-width:700px){.rg-head,.rg-boundary{display:grid}.rg-head a{justify-self:start}.s21-journey,.rg-summary,.rg-form{grid-template-columns:1fr}.rg-view button{width:100%}.rg-export header{display:grid}.rg-downloads{display:grid}.rg-downloads a{justify-content:center}}
    '''
    script = r'''
    <script>
    (()=>{'use strict';if(location.pathname!=='/report-generation')return;document.body.dataset.reportGenerationActive='true';const view=document.querySelector('#report-generation-view');view.hidden=false;const state={reports:null,exports:null,current:null},feedback=document.querySelector('#rg-feedback');let requestNumber=0;
      const api=async(path,init={})=>{const response=await fetch(path,init),type=response.headers.get('content-type')||'',value=type.includes('json')?await response.json():await response.text();if(!response.ok)throw Object.assign(new Error(value.message_zh||'请求失败'),{payload:value,status:response.status});return value};
      const say=(text,kind='')=>{feedback.textContent=text;if(kind)feedback.dataset.state=kind;else delete feedback.dataset.state};
      const renderReports=value=>{state.reports=value;const select=document.querySelector('#rg-report-version');select.replaceChildren();value.reports.forEach(row=>{const option=document.createElement('option');option.value=row.report_version_id;option.textContent=row.period.period_label_zh+' · '+row.version_label_zh+' · '+row.trust_and_limitations.status_zh;option.disabled=!row.trust_and_limitations.complete_report_claim_allowed;select.append(option)});document.querySelector('#rg-create-form button').disabled=!value.reports.some(row=>row.trust_and_limitations.complete_report_claim_allowed)};
      const renderExports=value=>{state.exports=value;document.querySelector('#rg-export-count').textContent=value.export_count+' 份导出';document.querySelector('#rg-empty').hidden=value.export_count>0;const root=document.querySelector('#rg-list');root.replaceChildren();value.exports.forEach(row=>{const card=document.createElement('article');card.className='rg-export';const head=document.createElement('header'),copy=document.createElement('div'),title=document.createElement('h3'),meta=document.createElement('p'),pass=document.createElement('span');title.textContent=row.report_version_id;meta.textContent='生成于 '+row.recorded_at+' · 21 个整数核对值';pass.className='rg-pass';pass.textContent=row.cross_format_consistency.difference_integer===0?'三种格式数字一致':'数字不一致';copy.append(title,meta);head.append(copy,pass);const links=document.createElement('div');links.className='rg-downloads';[['网页报告','html'],['PDF 报告','pdf'],['专业附表 CSV','appendix.csv']].forEach(([label,suffix])=>{const link=document.createElement('a');link.href='/api/report-exports/'+row.export_id+'/'+suffix;link.target=suffix==='html'?'_blank':'_self';link.textContent=label;links.append(link)});card.append(head,links);root.append(card)});state.current=value.exports[0]||null};
      const load=async()=>{const [reports,exports]=await Promise.all([api('/api/report-models'),api('/api/report-exports')]);renderReports(reports);renderExports(exports);say(reports.report_version_count?'请选择资料齐备的报告版本。':'请先返回报告模型建立版本。',reports.report_version_count?'success':'error');return state};
      const create=async()=>{const reportVersion=document.querySelector('#rg-report-version').value;if(!reportVersion)throw new Error('没有可生成的报告版本');const value=await api('/api/report-exports',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({report_version_id:reportVersion,idempotency_key:'browser-export-'+Date.now()+'-'+(++requestNumber)})});await load();say('网页、PDF 和专业附表已生成，三种格式数字一致。','success');return value};
      document.querySelector('#rg-create-form').addEventListener('submit',event=>{event.preventDefault();create().catch(error=>say(error.message,'error'))});window.KMFA_REPORT_GENERATION_TEST={snapshot:()=>structuredClone(state),load,create};load().catch(error=>say(error.message,'error'));
    })();
    </script>
    '''
    html_text = html_text.replace("</main>", view + "</main>", 1)
    html_text = html_text.replace("</style>", css + "</style>", 1)
    html_text = html_text.replace("</body>", script + "</body>", 1)
    html_text = html_text.replace(
        "本步骤的边界</strong><span>这里只建立报告模型，不生成网页、PDF 或表格，也不审批或发布报告。",
        "本步骤的边界</strong><span>报告模型建立后，可进入 <a href=\"/report-generation\">报告生成</a>，制作网页、PDF 和专业附表。",
    )
    html_text = html_text.replace("<title>KMFA 报告模型 · 经营工作台</title>", "<title>KMFA 报告生成 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html_text.splitlines()) + "\n"


class ReportGenerationHandler(base_runtime.ReportModelHandler):
    server_version = "KMFAReportGeneration/1.5"

    @property
    def report_exports(self) -> kernel.ReportExportJournal:
        return self.server.report_export_journal  # type: ignore[attr-defined,no-any-return]

    def _send_download(self, body: bytes, content_type: str, filename: str, *, inline: bool = False) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Disposition", f'{"inline" if inline else "attachment"}; filename="{filename}"')
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            if path == "/api/report-exports/options":
                self._send_json(HTTPStatus.OK, {
                    "schema_version": "kmfa.v015.s21p2.report_export_options.v1",
                    "formats": [
                        {"value": "HTML", "label_zh": "网页报告", "printable": True},
                        {"value": "PDF", "label_zh": "PDF 报告", "paginated": True},
                        {"value": "CSV", "label_zh": "专业附表", "exact_integer_values": True},
                    ],
                    "approval_or_publication_in_scope": False,
                })
                return
            if path == "/api/report-exports":
                self._send_json(HTTPStatus.OK, self.report_exports.list())
                return
            file_match = _FILE_ROUTE.fullmatch(path)
            if file_match:
                suffix = file_match.group(2)
                format_name = {"html": "HTML", "pdf": "PDF", "appendix.csv": "CSV"}[suffix]
                file_path, metadata = self.report_exports.file_path(file_match.group(1), format_name)
                self._send_download(file_path.read_bytes(), metadata["content_type"], metadata["filename"], inline=format_name == "HTML")
                return
            match = _EXPORT_ROUTE.fullmatch(path)
            if match:
                self._send_json(HTTPStatus.OK, self.report_exports.get(match.group(1)))
                return
            if path.startswith("/api/report-exports/"):
                raise kernel.ReportGenerationError("EXPORT_NOT_FOUND", "没有找到这份报告导出", status=404)
            if path.startswith("/api/") or path == "/favicon.ico" or path.startswith("/reports/"):
                super().do_GET()
                return
            self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")
        except kernel.ReportGenerationError as error:
            self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            if path == "/api/report-exports":
                body = self._json_body()
                report = self.report_models.get(str(body.get("report_version_id", "")))
                value = self.report_exports.create(report, idempotency_key=str(body.get("idempotency_key", "")))
                self._send_json(HTTPStatus.CREATED, value)
                return
            super().do_POST()
        except (TypeError, base_runtime.kernel.ReportModelError, kernel.ReportGenerationError) as error:
            if isinstance(error, (base_runtime.kernel.ReportModelError, kernel.ReportGenerationError)):
                self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})
            else:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "code": "INVALID_REQUEST", "message_zh": "请求格式不正确"})


class ReportGenerationServer(base_runtime.ReportModelServer):
    report_export_journal: kernel.ReportExportJournal


def start_server(
    host: str = "127.0.0.1", port: int = 0, *,
    event_path: Path | str = base_runtime.base_runtime.base_runtime.workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
    data_root: Path | str = base_runtime.base_runtime.base_runtime.data_update_kernel.DEFAULT_RUNTIME_ROOT,
    confirmation_event_path: Path | str = base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    publication_event_path: Path | str = base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    report_model_event_path: Path | str = base_runtime.kernel.DEFAULT_EVENT_PATH,
    export_event_path: Path | str = kernel.DEFAULT_EVENT_PATH,
    export_bundle_root: Path | str = kernel.DEFAULT_BUNDLE_ROOT,
) -> tuple[ReportGenerationServer, threading.Thread, str]:
    event_file = Path(event_path)
    server = ReportGenerationServer((host, port), ReportGenerationHandler)
    server.journal = base_runtime.base_runtime.base_runtime.workflow_kernel.EventJournal(event_file)
    server.policy_journal = base_runtime.base_runtime.base_runtime.policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = base_runtime.base_runtime.base_runtime.reporting_kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    server.data_update_store = base_runtime.base_runtime.base_runtime.data_update_kernel.DataUpdateStore(data_root)
    server.confirmation_workbench = base_runtime.base_runtime.base_runtime.kernel.ConfirmationWorkbench(confirmation_event_path)
    server.recalculation_workbench = base_runtime.base_runtime.kernel.RecalculationPublicationWorkbench(confirmation_event_path, publication_event_path)
    server.report_model_journal = base_runtime.kernel.ReportModelJournal(report_model_event_path)
    server.report_export_journal = kernel.ReportExportJournal(export_event_path, export_bundle_root)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s21p2-report-generation", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S21-P2 报告生成工作台")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--event-path", default=str(base_runtime.base_runtime.base_runtime.workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH))
    parser.add_argument("--data-root", default=str(base_runtime.base_runtime.base_runtime.data_update_kernel.DEFAULT_RUNTIME_ROOT))
    parser.add_argument("--confirmation-event-path", default=str(base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH))
    parser.add_argument("--publication-event-path", default=str(base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH))
    parser.add_argument("--report-model-event-path", default=str(base_runtime.kernel.DEFAULT_EVENT_PATH))
    parser.add_argument("--export-event-path", default=str(kernel.DEFAULT_EVENT_PATH))
    parser.add_argument("--export-bundle-root", default=str(kernel.DEFAULT_BUNDLE_ROOT))
    args = parser.parse_args()
    server, thread, url = start_server(
        args.host, args.port, event_path=args.event_path, data_root=args.data_root,
        confirmation_event_path=args.confirmation_event_path, publication_event_path=args.publication_event_path,
        report_model_event_path=args.report_model_event_path, export_event_path=args.export_event_path,
        export_bundle_root=args.export_bundle_root,
    )
    print(f"KMFA 报告生成：{url}/report-generation", flush=True)
    try:
        thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
