#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S17-P3 项目处理流程。"""

from __future__ import annotations

import argparse
import json
import threading
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s17_p1_project_list as list_runtime
from KMFA.tools import run_v015_s17_p2_project_detail as detail_runtime
from KMFA.tools import v015_s12_p2_core_calculations as calculations
from KMFA.tools import v015_s16_p1_homepage as homepage_kernel
from KMFA.tools import v015_s17_p1_project_list as list_kernel
from KMFA.tools import v015_s17_p2_project_detail as detail_kernel
from KMFA.tools import v015_s17_p3_project_workflow as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORT_ROOT = REPO_ROOT / "KMFA" / "stage_artifacts" / kernel.RUN_PHASE_ID / "exports"
REPORT_FILES = {
    "/reports/project-cost.html": (EXPORT_ROOT / "html" / "kmfa_project_cost_report.html", "text/html; charset=utf-8"),
    "/reports/project-cost.pdf": (EXPORT_ROOT / "pdf" / "kmfa_project_cost_report.pdf", "application/pdf"),
    "/reports/project-cost.xlsx": (
        EXPORT_ROOT / "xlsx" / "kmfa_project_cost_report.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ),
}


def _first(query: dict[str, list[str]], key: str, default: str) -> str:
    return query.get(key, [default])[0]


def _workflow_payload(query: dict[str, list[str]], journal: kernel.EventJournal) -> dict[str, Any]:
    return kernel.workflow_snapshot(
        project_id=_first(query, "project_id", "PUB-PROJ-001"),
        company_id=_first(query, "company_id", "demo-north"),
        period=_first(query, "period", "2026-07"),
        events=journal.read(),
    )


def _detail_payload(query: dict[str, list[str]], journal: kernel.EventJournal) -> dict[str, Any]:
    base = detail_runtime._detail_payload(query)
    projection = kernel.project_projection(
        project_id=_first(query, "project_id", "PUB-PROJ-001"),
        company_id=_first(query, "company_id", "demo-north"),
        period=_first(query, "period", "2026-07"),
        events=journal.read(),
    )
    for key in ("version", "schema_version", "project", "overview", "cost", "variance", "workflow_projection"):
        base[key] = projection[key]
    base["sections"].update(
        {
            "overview": projection["overview"],
            "cost": projection["cost"],
            "variance": projection["variance"],
        }
    )
    return base


def _projected_catalog_from_events(
    company_id: str,
    period: str,
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base in list_kernel.project_catalog(company_id, period):
        projection = kernel.project_projection(
            project_id=base["project_id"],
            company_id=company_id,
            period=period,
            events=events,
        )
        row = dict(projection["project"])
        workflow = projection["workflow_projection"]
        if workflow["active_event_ids"]:
            row.update(
                {
                    "source_zh": "公开合成项目台账与已确认处理事件",
                    "projection_ref": workflow["report_version"],
                    "processing_projection_applied": True,
                }
            )
        else:
            row.update({"projection_ref": None, "processing_projection_applied": False})
        rows.append(row)
    return rows


def _projected_catalog(query: dict[str, list[str]], journal: kernel.EventJournal) -> list[dict[str, Any]]:
    return _projected_catalog_from_events(
        _first(query, "company_id", "demo-north"),
        _first(query, "period", "2026-07"),
        journal.read(),
    )


def _list_payload(query: dict[str, list[str]], journal: kernel.EventJournal) -> dict[str, Any]:
    payload = list_runtime._list_payload(query, catalog_rows=_projected_catalog(query, journal))
    payload["source_note_zh"] = "项目列表、详情和处理记录使用同一当前投影；全部内容为公开合成数据。"
    return payload


def _compare_payload(query: dict[str, list[str]], journal: kernel.EventJournal) -> dict[str, Any]:
    project_ids = [item for item in _first(query, "project_ids", "").split(",") if item]
    company_id = _first(query, "company_id", "demo-north")
    period = _first(query, "period", "2026-07")
    return list_kernel.batch_compare(
        project_ids,
        company_id=company_id,
        period=period,
        catalog_rows=_projected_catalog(query, journal),
    )


def _export_payload(query: dict[str, list[str]], journal: kernel.EventJournal) -> str:
    project_ids = [item for item in _first(query, "project_ids", "").split(",") if item]
    company_id = _first(query, "company_id", "demo-north")
    period = _first(query, "period", "2026-07")
    return list_kernel.export_csv(
        project_ids,
        company_id=company_id,
        period=period,
        catalog_rows=_projected_catalog(query, journal),
    )


def _report_payload(query: dict[str, list[str]], journal: kernel.EventJournal) -> dict[str, Any]:
    return kernel.project_cost_report(_workflow_payload(query, journal))


def render_html() -> str:
    html_text = detail_runtime.render_html()
    workflow_view = '''
      <section id="project-workflow-view" class="workflow-view" aria-labelledby="workflow-title">
        <div class="workflow-head"><div><span>项目处理</span><h2 id="workflow-title">先看依据和影响，再确认处理</h2><p>所有动作都写入可撤销记录，不修改原始数据。</p></div><strong id="workflow-sync-state">正在核对…</strong></div>
        <div id="workflow-feedback" class="workflow-feedback" role="status" aria-live="polite">正在读取处理记录…</div>
        <div class="workflow-grid">
          <section class="workflow-card" aria-labelledby="unallocated-title"><h3 id="unallocated-title">处理未归集成本</h3><p id="unallocated-summary"></p><div id="candidate-list" class="candidate-list"></div><div id="assignment-preview" class="workflow-preview"></div><button id="confirm-assignment" class="workflow-primary" type="button">确认归集</button></section>
          <section class="workflow-card" aria-labelledby="variance-title"><h3 id="variance-title">处理项目差异</h3><p id="variance-summary"></p><div id="variance-sources"></div><label class="workflow-label">报告采用口径<select id="variance-option"><option value="KEEP_PROJECT_LEDGER">保留项目成本分类账</option><option value="USE_SETTLEMENT_SUPPORT">采用已确认结算口径</option></select></label><div id="variance-preview" class="workflow-preview"></div><button id="confirm-variance" class="workflow-primary" type="button">确认并重算页面与报告</button></section>
        </div>
        <section class="workflow-card workflow-history" aria-labelledby="workflow-history-title"><div class="workflow-section-head"><div><h3 id="workflow-history-title">处理记录</h3><p>撤销不会删除旧记录，而是追加一条撤销记录。</p></div><span id="workflow-count">0 条</span></div><div class="workflow-table-wrap"><table><thead><tr><th>顺序</th><th>处理</th><th>原因</th><th>状态</th><th></th></tr></thead><tbody id="workflow-events"></tbody></table></div></section>
        <section class="workflow-card workflow-reports" aria-labelledby="workflow-report-title"><div><h3 id="workflow-report-title">项目成本专题报告</h3><p>当前 HTML 按处理记录实时重算；PDF 与 Excel 是本阶段已验收样例，版本写在文件内。</p></div><div><a data-report-format="html" href="/reports/project-cost.html" target="_blank" rel="noopener">打开当前 HTML</a><a data-report-format="pdf" href="/reports/project-cost.pdf">下载验收样例 PDF</a><a data-report-format="xlsx" href="/reports/project-cost.xlsx">下载验收样例 Excel</a></div></section>
      </section>'''
    extra_css = '''
    .workflow-view{margin:16px 0 0;padding:20px;border:1px solid #c6d8e3;border-radius:9px;background:#f4f8fa}
    .workflow-head,.workflow-section-head,.workflow-reports{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}.workflow-head span{color:#17648f;font-size:12px;font-weight:800}.workflow-head h2{margin:4px 0;color:#173d57;font-size:21px}.workflow-head p,.workflow-section-head p,.workflow-reports p{margin:5px 0 0;color:#607684;font-size:12px;line-height:1.55}.workflow-head>strong{padding:7px 10px;border-radius:999px;background:#e8f7ee;color:#246040;font-size:12px;white-space:nowrap}.workflow-head>strong[data-state="pending"]{background:#fff6e5;color:#76551c}
    .workflow-feedback{margin:14px 0;padding:10px 12px;border-left:4px solid #2f7aa4;background:#fff;color:#35566c;font-size:13px}.workflow-feedback[data-state="error"]{border-left-color:#b44741;color:#7f2929;background:#fff7f6}
    .workflow-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.workflow-card{padding:16px;border:1px solid #d4e0e7;border-radius:8px;background:#fff}.workflow-card h3{margin:0;color:#214d68;font-size:16px}.workflow-card>p{margin:6px 0 12px;color:#607684;font-size:12px;line-height:1.5}.candidate-list{display:grid;gap:8px}.candidate-option{display:grid;grid-template-columns:auto 1fr auto;gap:9px;align-items:start;padding:10px;border:1px solid #dbe4e9;border-radius:7px;background:#fafcfd;font-size:12px}.candidate-option strong{display:block;color:#29475d}.candidate-option small{display:block;margin-top:3px;color:#607684;line-height:1.45}.candidate-confidence{color:#246040;font-weight:800}.workflow-preview{min-height:44px;margin:11px 0;padding:10px;border-radius:6px;background:#f2f7fa;color:#40596b;font-size:12px;line-height:1.55}.workflow-primary,.workflow-undo{min-height:42px;border:0;border-radius:6px;font:inherit;font-weight:800;cursor:pointer}.workflow-primary{width:100%;padding:9px 13px;background:#17648f;color:#fff}.workflow-primary:disabled{background:#9aabb5;cursor:not-allowed}.workflow-undo{min-height:34px;padding:6px 9px;background:#edf3f6;color:#27546e;font-size:11px}.workflow-label{display:grid;gap:5px;margin-top:10px;color:#40596b;font-size:12px;font-weight:750}.workflow-label select{min-height:42px;padding:7px 9px;border:1px solid #bccdd8;border-radius:6px;background:#fff;color:#29475d;font:inherit}.workflow-table-wrap{margin-top:12px;overflow:auto;border:1px solid #dce5ea;border-radius:6px}.workflow-history{margin-top:14px}.workflow-history table{width:100%;border-collapse:collapse;font-size:11px}.workflow-history th,.workflow-history td{padding:8px 9px;border-bottom:1px solid #e3e9ed;text-align:left;vertical-align:top}.workflow-history th{background:#f3f6f8;color:#40596b}.workflow-history tr:last-child td{border-bottom:0}.workflow-reports{margin-top:14px;align-items:center}.workflow-reports>div:last-child{display:flex;gap:8px;flex-wrap:wrap}.workflow-reports a{min-height:38px;padding:8px 11px;border:1px solid #9bb8ca;border-radius:6px;color:#155f8d;font-size:12px;font-weight:800;text-decoration:none}.workflow-reports a:hover{background:#eef7fb}.source-compare{width:100%;border-collapse:collapse;font-size:11px}.source-compare th,.source-compare td{padding:7px;border-bottom:1px solid #e4eaee;text-align:left}.source-compare th{color:#607684}.source-compare td:last-child{text-align:right;font-weight:750}
    @media(max-width:820px){.workflow-view{padding:14px}.workflow-grid{grid-template-columns:1fr}.workflow-head,.workflow-reports{display:block}.workflow-head>strong{display:inline-block;margin-top:9px}.workflow-reports>div:last-child{margin-top:12px}.workflow-reports a{display:inline-flex;align-items:center}.workflow-table-wrap{max-width:100%}}
    @media(prefers-reduced-motion:reduce){.workflow-view *{transition:none!important;animation:none!important}}
    '''
    script = '''
  <script>
  (()=>{'use strict';
    const view=document.querySelector('#project-workflow-view'),feedback=document.querySelector('#workflow-feedback'),syncState=document.querySelector('#workflow-sync-state');let last=null;let selectedCandidate='CAND-S17P3-001';let sequence=0;
    const active=()=>location.pathname.startsWith('/projects/')&&location.pathname.split('/').filter(Boolean).length===2;const projectId=()=>decodeURIComponent(location.pathname.split('/').filter(Boolean).pop()||'');const text=(tag,value,className='')=>{const node=document.createElement(tag);node.textContent=value==null?'':String(value);if(className)node.className=className;return node;};
    const money=cents=>{const sign=cents<0?'-':'';const absolute=Math.abs(cents),yuan=Math.floor(absolute/100),fen=String(absolute%100).padStart(2,'0');return sign+'¥'+yuan.toLocaleString('zh-CN')+'.'+fen;};
    const identity=()=>window.KMFA_ROLE_TEST.identity();const scope=()=>window.KMFA_TEST.context();const query=()=>{const who=identity(),ctx=scope();return new URLSearchParams({user_id:who.user_id,role_id:who.role_id,company_id:ctx.company,period:ctx.period,project_id:projectId()});};
    const body=extra=>{const who=identity(),ctx=scope();return {user_id:who.user_id,role_id:who.role_id,company_id:ctx.company,period:ctx.period,project_id:projectId(),actor_ref:'public-demo-owner',...extra};};
    const setFeedback=(message,error=false)=>{feedback.textContent=message;if(error)feedback.dataset.state='error';else delete feedback.dataset.state;};const key=prefix=>prefix+'-'+Date.now()+'-'+Math.floor(Math.random()*100000);
    const post=async(path,payload)=>{const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body(payload))});const value=await response.json();if(!response.ok)throw new Error(value.reason_zh||'处理失败');return value;};
    const candidatePreview=row=>{const target=last.unallocated_work_item.candidates.find(item=>item.candidate_id===selectedCandidate)||row;const same=target.candidate_project_id===projectId();return '候选：'+target.candidate_project_name_zh+'；依据：'+target.basis_zh.join('、')+'。影响：'+(same?'项目总成本不变，未归集转入'+target.target_category_zh:'项目不一致，禁止自动归集')+'。';};
    const renderCandidates=payload=>{const list=document.querySelector('#candidate-list');list.replaceChildren();payload.unallocated_work_item.candidates.forEach(row=>{const label=text('label','','candidate-option'),input=document.createElement('input'),copy=document.createElement('span');input.type='radio';input.name='candidate';input.value=row.candidate_id;input.checked=row.candidate_id===selectedCandidate;input.addEventListener('change',()=>{selectedCandidate=row.candidate_id;document.querySelector('#assignment-preview').textContent=candidatePreview(row);});copy.append(text('strong',row.candidate_project_name_zh),text('small',row.basis_zh.join('；')));label.append(input,copy,text('span',row.confidence_zh+' · '+(row.confidence_bps/100).toFixed(0)+'%','candidate-confidence'));list.append(label);});document.querySelector('#assignment-preview').textContent=candidatePreview(payload.unallocated_work_item.candidates[0]);};
    const renderSources=payload=>{const shell=document.querySelector('#variance-sources'),table=text('table','','source-compare'),head=document.createElement('tr');['来源','依据','金额'].forEach(value=>head.append(text('th',value)));const thead=document.createElement('thead');thead.append(head);const tbody=document.createElement('tbody');payload.variance_work_item.sources.forEach(row=>{const tr=document.createElement('tr');tr.append(text('td',row.source_name_zh),text('td',row.basis_zh),text('td',money(row.amount_cents)));tbody.append(tr);});table.append(thead,tbody);shell.replaceChildren(table);};
    const renderEvents=payload=>{const tbody=document.querySelector('#workflow-events');tbody.replaceChildren();const activeIds=new Set(payload.projection.workflow_projection.active_event_ids);payload.events.forEach(row=>{const tr=document.createElement('tr');tr.dataset.eventId=row.event_id;const activeRow=activeIds.has(row.event_id),status=activeRow?'有效':row.event_type==='RERUN_COMPLETED'?'重算完成':row.event_type==='EVENT_REVERSED'?'撤销记录':'历史';tr.append(text('td',row.event_sequence),text('td',row.event_type_zh),text('td',row.reason_zh),text('td',status));const action=document.createElement('td');if(activeRow&&row.reversible){const button=text('button','撤销','workflow-undo');button.type='button';button.addEventListener('click',()=>reverse(row.event_id));action.append(button);}tr.append(action);tbody.append(tr);});document.querySelector('#workflow-count').textContent=payload.event_count+' 条';};
    const render=payload=>{last=payload;view.hidden=!active();const unallocated=payload.projection.cost.unallocated.amount_cents;document.querySelector('#unallocated-summary').textContent=unallocated===0?'当前未归集成本已处理；可在下方记录中撤销。':'待处理 '+money(unallocated)+'，必须确认候选和依据。';renderCandidates(payload);const assignment=document.querySelector('#confirm-assignment');assignment.disabled=unallocated===0;assignment.textContent=unallocated===0?'已完成归集':'确认归集';document.querySelector('#variance-summary').textContent=payload.variance_work_item.explanation_zh+' 当前差异 '+money(payload.variance_work_item.difference_cents)+'。';renderSources(payload);const option=document.querySelector('#variance-option'),chosen=payload.variance_work_item.resolution_options.find(row=>row.option_id===option.value)||payload.variance_work_item.resolution_options[0];document.querySelector('#variance-preview').textContent='确认后成本为 '+money(chosen.selected_cost_cents)+'；页面、毛利和专题报告将一起重算。';renderEvents(payload);const reportQuery=query().toString();document.querySelectorAll('.workflow-reports a').forEach(link=>{const base=link.getAttribute('href').split('?')[0];link.setAttribute('href',base+'?'+reportQuery);});const synced=payload.projection.workflow_projection.report_sync_status==='PASS';syncState.textContent=synced?'页面与报告一致':'等待报告重算';syncState.dataset.state=synced?'pass':'pending';setFeedback('处理记录已读取。确认前可查看依据和金额影响；确认后仍可撤销。');};
    const load=async()=>{if(!active()){view.hidden=true;return null;}view.hidden=false;const current=++sequence;try{const response=await fetch('/api/projects/workflow?'+query()),payload=await response.json();if(current!==sequence)return {stale_response_ignored:true};if(!response.ok||!payload.allowed){setFeedback(payload.reason_zh||'当前项目不能处理。',true);return payload;}render(payload);return payload;}catch(error){if(current===sequence)setFeedback('处理记录暂时无法读取。',true);return null;}};
    const refreshDetail=async()=>{if(window.KMFA_PROJECT_DETAIL_TEST)await window.KMFA_PROJECT_DETAIL_TEST.load();return load();};
    const assign=async(candidateId=selectedCandidate,idempotencyKey=key('ui-assignment'))=>{setFeedback('正在确认归集…');try{const value=await post('/api/projects/workflow/assignment',{candidate_id:candidateId,reason_zh:'已核对候选项目、依据和金额影响后确认归集',idempotency_key:idempotencyKey});await refreshDetail();setFeedback('未归集成本已确认；源数据没有修改，可从处理记录撤销。');return value;}catch(error){setFeedback(error.message,true);throw error;}};
    const resolveVariance=async(optionId=document.querySelector('#variance-option').value,idempotencyKey=key('ui-variance'))=>{setFeedback('正在重算页面与专题报告…');try{const value=await post('/api/projects/workflow/variance',{option_id:optionId,reason_zh:'已并排核对两项来源和影响后确认报告口径',idempotency_key:idempotencyKey});await refreshDetail();setFeedback('差异已处理，页面与专题报告已同步重算。');return value;}catch(error){setFeedback(error.message,true);throw error;}};
    const reverse=async(eventId,idempotencyKey=key('ui-reversal'))=>{setFeedback('正在追加撤销记录…');try{const value=await post('/api/projects/workflow/reverse',{event_id:eventId,reason_zh:'复核后撤销本次处理并恢复上一版投影',idempotency_key:idempotencyKey});await refreshDetail();setFeedback('已撤销；旧记录仍保留，页面已恢复并重算。');return value;}catch(error){setFeedback(error.message,true);throw error;}};
    document.querySelector('#confirm-assignment').addEventListener('click',()=>assign().catch(()=>{}));document.querySelector('#confirm-variance').addEventListener('click',()=>resolveVariance().catch(()=>{}));document.querySelector('#variance-option').addEventListener('change',()=>{if(last)render(last);});
    const refresh=()=>setTimeout(load,0);document.querySelector('#context-company').addEventListener('change',refresh);document.querySelector('#context-period').addEventListener('change',refresh);document.querySelector('#identity-user').addEventListener('change',refresh);window.addEventListener('popstate',refresh);
    window.KMFA_PROJECT_WORKFLOW_TEST={load,snapshot:()=>last,assign,resolveVariance,reverse,selectedCandidate:value=>{if(value){selectedCandidate=value;document.querySelector('input[value="'+value+'"]').checked=true;}return selectedCandidate;},reportLinks:()=>[...document.querySelectorAll('.workflow-reports a')].map(node=>node.getAttribute('href'))};load();
  })();
  </script>
'''
    marker = '      <p class="detail-disclaimer">当前详情只使用公开合成项目，用于验证项目成本、收入、回款、差异和资料流程，不代表任何真实公司的经营情况。</p>'
    if marker not in html_text:
        raise RuntimeError("S17-P2 项目详情插入点发生变化")
    html_text = html_text.replace(marker, workflow_view + "\n" + marker, 1)
    html_text = html_text.replace("  </style>", extra_css + "  </style>", 1)
    html_text = html_text.replace("</body>", script + "</body>", 1)
    html_text = html_text.replace("<title>KMFA 项目详情 · 经营工作台</title>", "<title>KMFA 项目处理 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html_text.splitlines()) + "\n"


class ProjectWorkflowHandler(detail_runtime.ProjectDetailHandler):
    server_version = "KMFAProjectWorkflow/1.5"

    @property
    def journal(self) -> kernel.EventJournal:
        return self.server.journal  # type: ignore[attr-defined,no-any-return]

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"allowed": False, "reason_zh": "专题报告尚未生成。"})
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 65_536:
            raise kernel.ProjectWorkflowError("处理请求大小不正确")
        value = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(value, dict):
            raise kernel.ProjectWorkflowError("处理请求必须是对象")
        return value

    @staticmethod
    def _body_query(value: dict[str, Any]) -> dict[str, list[str]]:
        keys = ("user_id", "role_id", "company_id", "period", "project_id")
        return {key: [str(value[key])] for key in keys if key in value}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path in REPORT_FILES:
            query = parse_qs(parsed.query)
            allowed, identity = list_runtime._authorised(query)
            if not allowed:
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {"allowed": False, "reason_zh": identity.get("reason_zh", "当前身份没有查看权限。")},
                )
                return
            if parsed.path.endswith(".html"):
                body = kernel.render_report_html(_report_payload(query, self.journal)).encode("utf-8")
                self._send(HTTPStatus.OK, body, "text/html; charset=utf-8")
            else:
                path, content_type = REPORT_FILES[parsed.path]
                self._send_file(path, content_type)
            return
        if parsed.path in {
            "/api/projects",
            "/api/projects/compare",
            "/api/projects/export",
            "/api/projects/workflow",
            "/api/projects/workflow/report",
            "/api/projects/detail",
        }:
            query = parse_qs(parsed.query)
            try:
                allowed, identity = list_runtime._authorised(query)
                if not allowed:
                    self._send_json(
                        HTTPStatus.FORBIDDEN,
                        {"allowed": False, "reason_zh": identity.get("reason_zh", "当前身份没有处理权限。")},
                    )
                    return
                if parsed.path == "/api/projects":
                    self._send_json(HTTPStatus.OK, _list_payload(query, self.journal))
                    return
                if parsed.path == "/api/projects/compare":
                    self._send_json(HTTPStatus.OK, _compare_payload(query, self.journal))
                    return
                if parsed.path == "/api/projects/export":
                    self._send_csv(_export_payload(query, self.journal))
                    return
                if parsed.path == "/api/projects/workflow":
                    payload = _workflow_payload(query, self.journal)
                elif parsed.path == "/api/projects/workflow/report":
                    payload = _report_payload(query, self.journal)
                else:
                    payload = _detail_payload(query, self.journal)
                self._send_json(HTTPStatus.OK, payload)
            except (
                KeyError,
                TypeError,
                json.JSONDecodeError,
                homepage_kernel.HomepageError,
                list_kernel.ProjectListError,
                calculations.CoreCalculationError,
                detail_kernel.ProjectDetailError,
                kernel.ProjectWorkflowError,
            ) as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})
            return
        if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico":
            super().do_GET()
            return
        self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path not in {
            "/api/projects/workflow/assignment",
            "/api/projects/workflow/variance",
            "/api/projects/workflow/reverse",
        }:
            # Keep earlier app-shell/identity/experience POST routes reachable
            # after the project workflow layer is composed into later runtimes.
            # The lower handler remains responsible for the final 404 response.
            super().do_POST()
            return
        try:
            value = self._json_body()
            query = self._body_query(value)
            allowed, identity = list_runtime._authorised(query)
            if not allowed:
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {"allowed": False, "reason_zh": identity.get("reason_zh", "当前身份没有处理权限。")},
                )
                return
            common = {
                "project_id": str(value.get("project_id", "PUB-PROJ-001")),
                "company_id": str(value.get("company_id", "demo-north")),
                "period": str(value.get("period", "2026-07")),
                "actor_ref": str(value.get("actor_ref", "public-demo-owner")),
                "reason_zh": str(value.get("reason_zh", "")),
                "idempotency_key": str(value.get("idempotency_key", "")),
            }
            if parsed.path.endswith("assignment"):
                result = kernel.confirm_unallocated_assignment(
                    self.journal, candidate_id=str(value.get("candidate_id", "")), **common
                )
            elif parsed.path.endswith("variance"):
                result = kernel.confirm_variance_resolution(
                    self.journal, option_id=str(value.get("option_id", "")), **common
                )
            else:
                result = kernel.reverse_processing_event(
                    self.journal,
                    event_id=str(value.get("event_id", "")),
                    company_id=common["company_id"],
                    period=common["period"],
                    actor_ref=common["actor_ref"],
                    reason_zh=common["reason_zh"],
                    idempotency_key=common["idempotency_key"],
                )
            self._send_json(HTTPStatus.OK, {"allowed": True, **result})
        except (
            KeyError,
            TypeError,
            json.JSONDecodeError,
            homepage_kernel.HomepageError,
            list_kernel.ProjectListError,
            calculations.CoreCalculationError,
            detail_kernel.ProjectDetailError,
            kernel.ProjectWorkflowError,
        ) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})


class ProjectWorkflowServer(detail_runtime.ProjectDetailServer):
    journal: kernel.EventJournal


def start_server(
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    event_path: Path | str = kernel.DEFAULT_RUNTIME_EVENT_PATH,
) -> tuple[ProjectWorkflowServer, threading.Thread, str]:
    server = ProjectWorkflowServer((host, port), ProjectWorkflowHandler)
    server.journal = kernel.EventJournal(event_path)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s17p3-project-workflow", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S17-P3 项目处理流程")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--event-path", default=str(kernel.DEFAULT_RUNTIME_EVENT_PATH))
    args = parser.parse_args()
    server = ProjectWorkflowServer((args.host, args.port), ProjectWorkflowHandler)
    server.journal = kernel.EventJournal(args.event_path)
    print(f"KMFA 项目处理：http://{args.host}:{server.server_address[1]}/projects/PUB-PROJ-001", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
