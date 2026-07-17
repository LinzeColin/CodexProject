#!/usr/bin/env python3
"""Run the KMFA v1.5 S20-P1 data-update workspace on localhost."""

from __future__ import annotations

import argparse
import re
import threading
from email import policy
from email.parser import BytesParser
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from KMFA.tools import run_v015_s19_p3_tax_policy_reporting as base_runtime
from KMFA.tools import v015_s17_p3_project_workflow as workflow_kernel
from KMFA.tools import v015_s19_p2_policy_eligibility as policy_kernel
from KMFA.tools import v015_s19_p3_tax_policy_reporting as reporting_kernel
from KMFA.tools import v015_s20_p1_data_update as kernel


_JOB_ROUTE = re.compile(r"^/api/data-update/jobs/(DU-[a-f0-9]{24})$")
_ACTION_ROUTE = re.compile(r"^/api/data-update/jobs/(DU-[a-f0-9]{24})/(confirm|resume|cancel)$")


def render_html() -> str:
    html = base_runtime.render_html()
    view = r'''
    <section id="data-update-view" class="du-view" aria-labelledby="du-title" hidden>
      <header class="du-head">
        <div><span>数据更新 · 三步完成</span><h1 id="du-title">先上传检查，再确认处理</h1><p>所有上传内容只进入隔离工作区。原始资料不改动；未确认前不会导入。</p></div>
        <a class="du-home" href="/overview" data-route="/overview">返回经营首页</a>
      </header>
      <aside class="du-boundary"><strong>安全边界</strong><span>不会写入原始只读目录，不会自动重算或发布报告。</span></aside>
      <ol id="du-stepper" class="du-stepper" aria-label="更新步骤">
        <li data-step="1"><strong>1</strong><span>选择并上传</span></li>
        <li data-step="2"><strong>2</strong><span>预览并确认</span></li>
        <li data-step="3"><strong>3</strong><span>处理与结果</span></li>
      </ol>
      <div id="du-feedback" class="du-feedback" role="status" aria-live="polite">正在准备更新向导…</div>

      <section id="du-upload-panel" class="du-card" aria-labelledby="du-upload-title">
        <div class="du-card-head"><div><h2 id="du-upload-title">1. 选择资料范围并上传</h2><p>来源、公司、账户或板块、月份都由你明确选择。</p></div><span>可随时取消</span></div>
        <form id="du-upload-form" class="du-form">
          <label>资料来源<select id="du-source" name="source_id" required></select></label>
          <label>公司主体<select id="du-entity" name="entity_id" required></select></label>
          <label>账户或板块<select id="du-scope" name="scope_id" required></select></label>
          <label>资料月份<input id="du-period" name="period" type="month" value="2026-07" required></label>
          <label class="du-file">选择文件<input id="du-file" name="file" type="file" accept=".zip,.xlsx,.xls,.csv,.pdf,.wps,.et,.dps" required><small id="du-file-note">支持 ZIP、Excel、CSV、PDF、WPS；单个文件不超过 16 MB。</small></label>
          <div class="du-actions"><button id="du-upload" class="du-primary" type="submit">上传并检查</button><button class="du-secondary" type="reset">清空</button></div>
        </form>
      </section>

      <section id="du-preview-panel" class="du-card" aria-labelledby="du-preview-title" hidden>
        <div class="du-card-head"><div><h2 id="du-preview-title">2. 核对识别预览</h2><p>自动识别的内容会单独标出。只有你确认后才进入处理。</p></div><span id="du-preview-state">等待检查</span></div>
        <div id="du-file-summary" class="du-file-summary"></div>
        <dl id="du-preview-fields" class="du-fields"></dl>
        <div id="du-issues" class="du-issues" hidden></div>
        <div class="du-confirm-note"><strong>请确认</strong><span>文件、来源、公司、账户或板块、月份均正确；系统自动识别的文件类型也正确。</span></div>
        <div class="du-actions"><button id="du-confirm" class="du-primary" type="button">确认并开始处理</button><button id="du-back" class="du-secondary" type="button">返回修改</button><button id="du-cancel" class="du-danger" type="button">取消本次更新</button></div>
      </section>

      <section id="du-result-panel" class="du-card" aria-labelledby="du-result-title" hidden>
        <div class="du-card-head"><div><h2 id="du-result-title">3. 处理进度与结果</h2><p>这里显示后端实际完成的步骤；刷新页面后仍可恢复。</p></div><button id="du-refresh" class="du-link-button" type="button">刷新状态</button></div>
        <ol id="du-progress" class="du-progress"></ol>
        <section id="du-impact" class="du-impact" hidden><h3>这次资料会影响什么</h3><p id="du-recalc-impact"></p><div><strong>可能受影响的页面和报告</strong><ul id="du-report-impact"></ul></div><p id="du-next-step"></p></section>
        <div class="du-actions"><button id="du-resume" class="du-primary" type="button" hidden>继续处理</button><button id="du-new" class="du-secondary" type="button" hidden>开始另一项更新</button><button id="du-result-cancel" class="du-danger" type="button">取消本次更新</button></div>
      </section>
      <p class="du-disclaimer">S20-P1 只完成上传、识别、人工确认、隔离导入和结果校验。重算与报告刷新只显示影响范围，不在本阶段执行。</p>
    </section>
    '''
    css = r'''
    body[data-data-update-active="true"] #page-view,
    body[data-data-update-active="true"] #loading-view,
    body[data-data-update-active="true"] #error-view,
    body[data-data-update-active="true"] #not-found-view,
    body[data-data-update-active="true"] #homepage-view,
    body[data-data-update-active="true"] #project-list-view,
    body[data-data-update-active="true"] #project-detail-view,
    body[data-data-update-active="true"] #project-workflow-view,
    body[data-data-update-active="true"] #receivables-view,
    body[data-data-update-active="true"] #funds-view,
    body[data-data-update-active="true"] #funds-report-view,
    body[data-data-update-active="true"] #tax-invoice-view,
    body[data-data-update-active="true"] #policy-eligibility-view,
    body[data-data-update-active="true"] #tax-policy-report-view,
    body[data-data-update-active="true"] #context-status,
    body[data-data-update-active="true"] .identity-shell,
    body[data-data-update-active="true"] .quick-shell,
    body[data-data-update-active="true"] #access-workspace,
    body[data-data-update-active="true"] #experience-workspace{display:none!important}
    .du-view{margin:2px 0 30px}.du-head{display:flex;justify-content:space-between;align-items:flex-start;gap:22px;margin-bottom:12px}.du-head>div>span{color:#17648f;font-size:12px;font-weight:800}.du-head h1{margin:4px 0 0;color:#173d57;font-size:30px;line-height:1.2}.du-head p{margin:7px 0 0;max-width:800px;color:#607684;font-size:14px}.du-home{display:inline-flex;min-height:44px;align-items:center;padding:0 14px;border:1px solid #9fb8c8;border-radius:7px;background:#fff;color:#245a7a;font-size:12px;font-weight:800;text-decoration:none}.du-boundary{display:flex;justify-content:space-between;gap:16px;margin-bottom:12px;padding:13px 15px;border:1px solid #d5b27c;border-left:4px solid #a86a17;border-radius:8px;background:#fffaf2;color:#654519}.du-boundary strong{font-size:14px}.du-boundary span{font-size:12px}.du-stepper{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin:0 0 11px;padding:0;list-style:none}.du-stepper li{display:flex;align-items:center;gap:9px;min-height:54px;padding:9px 12px;border:1px solid #d6e0e6;border-radius:8px;background:#fff;color:#607684}.du-stepper li strong{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;background:#e9eff3;color:#40596b}.du-stepper li[data-state="active"]{border-color:#4382a0;background:#edf6fb;color:#173d57}.du-stepper li[data-state="active"] strong{background:#246c83;color:#fff}.du-stepper li[data-state="done"]{border-color:#9fc5ae;background:#f3faf5;color:#276346}.du-stepper li[data-state="done"] strong{background:#34805a;color:#fff}.du-feedback{min-height:44px;margin-bottom:11px;padding:10px 12px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:7px;background:#edf6fb;color:#29475d;font-size:13px}.du-feedback[data-state="error"]{border-color:#d7a6a6;background:#fff8f7;color:#7f2929}.du-feedback[data-state="success"]{border-color:#9fc5ae;background:#f3faf5;color:#276346}.du-card{margin-bottom:11px;padding:17px;border:1px solid #d8e2e8;border-radius:9px;background:#fff}.du-card-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;margin-bottom:14px}.du-card-head h2{margin:0;color:#214d68;font-size:19px}.du-card-head p{margin:5px 0 0;color:#607684;font-size:12px}.du-card-head>span{color:#276346;font-size:11px;font-weight:800}.du-form{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.du-form label{display:grid;gap:6px;color:#536b7c;font-size:11px;font-weight:800}.du-form select,.du-form input[type="month"],.du-form input[type="file"]{width:100%;min-height:44px;padding:8px 10px;border:1px solid #b9cbd7;border-radius:7px;background:#fff;color:#29475d;font:inherit}.du-file{grid-column:1/-1}.du-file small{color:#607684;font-size:10px;font-weight:500}.du-actions{display:flex;flex-wrap:wrap;gap:9px;grid-column:1/-1}.du-actions button,.du-link-button{min-height:44px;padding:0 15px;border-radius:7px;font-size:12px;font-weight:800;cursor:pointer}.du-primary{border:0;background:#246c83;color:#fff}.du-secondary{border:1px solid #9fb8c8;background:#fff;color:#245a7a}.du-danger{border:1px solid #d2a5a5;background:#fff8f7;color:#8b3030}.du-link-button{border:1px solid #9fb8c8;background:#fff;color:#245a7a}.du-actions button:disabled{border-color:#c8d1d6;background:#e7ecef;color:#7b8a93;cursor:not-allowed}.du-file-summary{margin-bottom:10px;padding:12px;border:1px solid #bfd2df;border-radius:7px;background:#f3f8fb;color:#29475d}.du-file-summary strong{display:block}.du-file-summary span{display:block;margin-top:4px;color:#607684;font-size:11px}.du-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:0 0 11px}.du-fields>div{padding:11px;border:1px solid #dce5ea;border-radius:7px;background:#fbfcfd}.du-fields dt{color:#607684;font-size:10px}.du-fields dd{margin:5px 0 0;color:#29475d;font-size:13px;font-weight:800}.du-origin{display:inline-block;margin-left:6px;padding:2px 6px;border-radius:999px;background:#edf6fb;color:#245f75;font-size:9px;font-weight:800}.du-origin[data-origin="AUTO_DETECTED"]{background:#fff3d9;color:#80530f}.du-issues{margin-bottom:10px;padding:12px;border:1px solid #d7a6a6;border-radius:7px;background:#fff8f7;color:#7f2929;font-size:12px}.du-confirm-note{display:flex;gap:12px;margin-bottom:12px;padding:12px;border:1px solid #d5b27c;border-radius:7px;background:#fffaf2;color:#654519}.du-confirm-note span{font-size:11px}.du-progress{display:grid;gap:8px;margin:0 0 12px;padding:0;list-style:none}.du-progress li{display:grid;grid-template-columns:34px minmax(150px,.55fr) minmax(260px,1.45fr);gap:10px;align-items:center;padding:10px 12px;border:1px solid #dce5ea;border-radius:7px;background:#fbfcfd}.du-progress li>strong{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;background:#e9eff3;color:#526b7b}.du-progress li[data-status="COMPLETED"]{border-color:#a8cbb5;background:#f4faf6}.du-progress li[data-status="COMPLETED"]>strong{background:#34805a;color:#fff}.du-progress li[data-status="IN_PROGRESS"]{border-color:#7eaac0;background:#edf6fb}.du-progress li[data-status="IN_PROGRESS"]>strong{background:#246c83;color:#fff}.du-progress li[data-status="FAILED"],.du-progress li[data-status="BLOCKED"]{border-color:#d7a6a6;background:#fff8f7}.du-progress b{color:#29475d;font-size:12px}.du-progress span{color:#607684;font-size:11px}.du-impact{margin-bottom:12px;padding:14px;border:1px solid #bfd2df;border-radius:8px;background:#f3f8fb}.du-impact h3{margin:0 0 8px;color:#214d68;font-size:16px}.du-impact p{margin:6px 0;color:#42596a;font-size:12px}.du-impact ul{margin:6px 0 0;padding-left:20px;color:#42596a;font-size:11px}.du-disclaimer{color:#607684;font-size:11px;line-height:1.5}
    @media(max-width:900px){.du-form{grid-template-columns:1fr 1fr}.du-fields{grid-template-columns:1fr 1fr}}
    @media(max-width:680px){.du-head,.du-boundary,.du-card-head{display:grid}.du-head h1{font-size:25px}.du-home{justify-self:start}.du-stepper{gap:5px}.du-stepper li{display:grid;justify-items:center;padding:8px 4px;text-align:center;font-size:10px}.du-form,.du-fields{grid-template-columns:1fr}.du-file{grid-column:auto}.du-progress li{grid-template-columns:30px 1fr}.du-progress li span{grid-column:2}.du-card{padding:13px}.du-actions{display:grid;grid-template-columns:1fr}.du-actions button{width:100%}}
    '''
    script = r'''
  <script>
  (()=>{
    const view=document.querySelector('#data-update-view'),storageKey='kmfa.v015.s20p1.data-update-job.v1';let options=null,last=null,pollTimer=null;
    const active=()=>location.pathname==='/data-update';
    const feedback=(message,state='')=>{const node=document.querySelector('#du-feedback');node.textContent=message;if(state)node.dataset.state=state;else delete node.dataset.state;};
    const api=async(path,init={})=>{const response=await fetch(path,init),payload=await response.json();if(!response.ok)throw Object.assign(new Error(payload.message_zh||payload.reason_zh||'请求失败'),{payload,status:response.status});return payload;};
    const fill=(id,items)=>{const select=document.querySelector(id);select.replaceChildren();items.forEach(item=>select.append(new Option(item.label_zh,item.value)));};
    const setStep=step=>document.querySelectorAll('#du-stepper li').forEach(item=>{const value=Number(item.dataset.step);item.dataset.state=value<step?'done':value===step?'active':'pending';});
    const statusText=status=>({NOT_STARTED:'尚未开始',WAITING_USER:'等待确认',IN_PROGRESS:'处理中',COMPLETED:'已完成',FAILED:'失败',BLOCKED:'已阻止',PAUSED:'已暂停',CANCELLED:'已取消',NOT_EXECUTED:'本阶段不执行'}[status]||status);
    const showPanel=name=>{document.querySelector('#du-upload-panel').hidden=name!=='upload';document.querySelector('#du-preview-panel').hidden=name!=='preview';document.querySelector('#du-result-panel').hidden=name!=='result';};
    const clearJob=()=>{localStorage.removeItem(storageKey);last=null;showPanel('upload');setStep(1);document.querySelector('#du-upload-form').reset();document.querySelector('#du-period').value='2026-07';feedback('请选择资料范围和文件。');};
    const renderPreview=job=>{const preview=job.preview,blocked=job.status==='PREVIEW_BLOCKED';document.querySelector('#du-preview-state').textContent=blocked?'发现问题，不能处理':'检查通过，等待你确认';const summary=document.querySelector('#du-file-summary');summary.replaceChildren();const strong=document.createElement('strong');strong.textContent=job.file_display_name;const small=document.createElement('span');small.textContent=preview?preview.format_label_zh+' · '+new Intl.NumberFormat('zh-CN').format(preview.file_size_bytes)+' 字节':'文件未通过安全识别';summary.append(strong,small);const fields=document.querySelector('#du-preview-fields');fields.replaceChildren();(preview?.fields||[]).forEach(row=>{const wrap=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd'),badge=document.createElement('span');dt.textContent=row.label_zh;dd.textContent=row.value;badge.className='du-origin';badge.dataset.origin=row.origin;badge.textContent=row.origin_zh;dd.append(badge);wrap.append(dt,dd);fields.append(wrap);});const issues=document.querySelector('#du-issues');issues.replaceChildren();issues.hidden=!job.issues.length;job.issues.forEach(row=>{const p=document.createElement('p');p.textContent=row.message_zh;p.style.margin='0';issues.append(p);});document.querySelector('#du-confirm').disabled=blocked||!preview;};
    const renderProgress=job=>{const target=document.querySelector('#du-progress');target.replaceChildren();job.progress.forEach((row,index)=>{const li=document.createElement('li');li.dataset.status=row.status;const number=document.createElement('strong');number.textContent=String(index+1);const label=document.createElement('b');label.textContent=row.label_zh+' · '+statusText(row.status);const detail=document.createElement('span');detail.textContent=row.detail_zh;li.append(number,label,detail);target.append(li);});const impact=document.querySelector('#du-impact'),result=job.result;if(result){impact.hidden=false;document.querySelector('#du-recalc-impact').textContent='需要核对的重算范围：'+result.impact.recalculation_scope_zh+'。本阶段未执行重算。';const list=document.querySelector('#du-report-impact');list.replaceChildren();result.impact.report_labels_zh.forEach(label=>{const li=document.createElement('li');li.textContent=label;list.append(li);});document.querySelector('#du-next-step').textContent=result.impact.next_step_zh;}else impact.hidden=true;document.querySelector('#du-resume').hidden=job.status!=='INTERRUPTED';document.querySelector('#du-new').hidden=job.status!=='COMPLETED';document.querySelector('#du-result-cancel').hidden=job.status==='COMPLETED';};
    const render=job=>{last=job;if(job.status==='CANCELLED'){clearJob();feedback('本次更新已取消，隔离副本已删除。','success');return;}localStorage.setItem(storageKey,job.job_id);if(['AWAITING_CONFIRMATION','PREVIEW_BLOCKED'].includes(job.status)){showPanel('preview');setStep(2);renderPreview(job);feedback(job.status==='PREVIEW_BLOCKED'?'文件存在问题，请返回重新选择。':'检查完成。请核对所有内容后再确认。',job.status==='PREVIEW_BLOCKED'?'error':'');return;}showPanel('result');setStep(3);renderProgress(job);if(job.status==='COMPLETED')feedback('资料已完成隔离导入和结果校验；重算与报告刷新尚未执行。','success');else if(job.status==='INTERRUPTED')feedback('处理已安全暂停，没有暴露半成品；可以继续。','error');else if(job.status==='FAILED')feedback(job.issues[0]?.message_zh||'处理失败。','error');else feedback('正在按后端真实状态处理，请稍候…');};
    const loadJob=async(silent=false)=>{const id=localStorage.getItem(storageKey);if(!id)return null;try{const job=await api('/api/data-update/jobs/'+id);render(job);return job;}catch(error){if(error.status===404){localStorage.removeItem(storageKey);if(!silent)clearJob();return null;}if(!silent)feedback(error.message,'error');return null;}};
    const upload=async event=>{event.preventDefault();const file=document.querySelector('#du-file').files[0];if(!file){feedback('请选择文件。','error');return;}if(options&&file.size>options.max_upload_bytes){feedback('文件超过 16 MB，请拆分后再上传。','error');return;}const data=new FormData();data.set('source_id',document.querySelector('#du-source').value);data.set('entity_id',document.querySelector('#du-entity').value);data.set('scope_id',document.querySelector('#du-scope').value);data.set('period',document.querySelector('#du-period').value);data.set('file',file,file.name);document.querySelector('#du-upload').disabled=true;feedback('正在把文件写入隔离工作区并执行安全检查…');try{render(await api('/api/data-update/jobs',{method:'POST',body:data}));}catch(error){feedback(error.message,'error');}finally{document.querySelector('#du-upload').disabled=false;}};
    const confirm=async()=>{if(!last?.preview)return;document.querySelector('#du-confirm').disabled=true;feedback('已收到确认，正在执行隔离导入和校验…');pollTimer=setInterval(()=>loadJob(true),200);try{const body={preview_id:last.preview.preview_id,confirm_token:last.preview.confirm_token,operator_role:'ROLE::DATA_STEWARD'};render(await api('/api/data-update/jobs/'+last.job_id+'/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}));}catch(error){feedback(error.message,'error');}finally{clearInterval(pollTimer);pollTimer=null;document.querySelector('#du-confirm').disabled=false;}};
    const cancel=async()=>{if(!last){clearJob();return;}try{render(await api('/api/data-update/jobs/'+last.job_id+'/cancel',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}));}catch(error){feedback(error.message,'error');}};
    const resume=async()=>{if(!last)return;feedback('正在从安全暂停点继续…');try{render(await api('/api/data-update/jobs/'+last.job_id+'/resume',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}));}catch(error){feedback(error.message,'error');}};
    const start=async()=>{if(!active()){view.hidden=true;delete document.body.dataset.dataUpdateActive;return;}view.hidden=false;document.body.dataset.dataUpdateActive='true';try{options=await api('/api/data-update/options');fill('#du-source',options.sources);fill('#du-entity',options.entities);fill('#du-scope',options.scopes);const restored=await loadJob(true);if(!restored)clearJob();}catch(error){feedback(error.message,'error');}};
    document.querySelector('#du-upload-form').addEventListener('submit',upload);document.querySelector('#du-confirm').addEventListener('click',confirm);document.querySelector('#du-cancel').addEventListener('click',cancel);document.querySelector('#du-back').addEventListener('click',cancel);document.querySelector('#du-result-cancel').addEventListener('click',cancel);document.querySelector('#du-resume').addEventListener('click',resume);document.querySelector('#du-refresh').addEventListener('click',()=>loadJob());document.querySelector('#du-new').addEventListener('click',clearJob);window.addEventListener('popstate',start);document.addEventListener('click',event=>{if(event.target.closest('a[data-route]'))setTimeout(start,0);});window.KMFA_DATA_UPDATE_TEST={start,loadJob,upload:()=>document.querySelector('#du-upload-form').requestSubmit(),confirm,cancel,resume,snapshot:()=>last,clearJob};start();
  })();
  </script>'''
    marker = '<section id="tax-policy-report-view" class="tpr-view" aria-labelledby="tpr-title" hidden>'
    if marker not in html:
        raise RuntimeError("S19-P3 insertion point drifted")
    html = html.replace(marker, view + marker, 1)
    html = html.replace("  </style>", css + "  </style>", 1)
    html = html.replace("</body>", script + "</body>", 1)
    html = html.replace("<title>KMFA 税务与政策报告 · 经营工作台</title>", "<title>KMFA 数据更新 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class DataUpdateHandler(base_runtime.TaxPolicyReportingHandler):
    server_version = "KMFADataUpdate/1.5"

    def _multipart_upload(self) -> tuple[dict[str, str], str, bytes]:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.lower().startswith("multipart/form-data;"):
            raise kernel.DataUpdateError("UPLOAD_CONTENT_TYPE_INVALID", "请通过文件选择器上传。")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise kernel.DataUpdateError("UPLOAD_LENGTH_INVALID", "上传长度不正确。") from error
        if length <= 0 or length > kernel.MAX_UPLOAD_BYTES + 256 * 1024:
            raise kernel.DataUpdateError("UPLOAD_REQUEST_TOO_LARGE", "上传请求超过 16 MB 限制。", status=413)
        raw = self.rfile.read(length)
        message = BytesParser(policy=policy.default).parsebytes(
            ("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode("ascii") + raw
        )
        fields: dict[str, str] = {}
        file_name = ""
        file_bytes: bytes | None = None
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            filename = part.get_filename()
            payload = part.get_payload(decode=True) or b""
            if filename is not None:
                if file_bytes is not None or name != "file":
                    raise kernel.DataUpdateError("UPLOAD_FILE_COUNT_INVALID", "每次只能上传一个文件。")
                file_name = filename
                file_bytes = payload
            elif name in {"source_id", "entity_id", "scope_id", "period"}:
                try:
                    value = payload.decode(part.get_content_charset() or "utf-8").strip()
                except UnicodeDecodeError as error:
                    raise kernel.DataUpdateError("UPLOAD_FIELD_ENCODING_INVALID", "选择信息无法读取。") from error
                if len(value) > 100:
                    raise kernel.DataUpdateError("UPLOAD_FIELD_TOO_LONG", "选择信息过长。")
                fields[name] = value
        if file_bytes is None:
            raise kernel.DataUpdateError("UPLOAD_FILE_REQUIRED", "请选择文件。")
        return fields, file_name, file_bytes

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        try:
            if parsed.path == "/api/data-update/options":
                self._send_json(HTTPStatus.OK, kernel.options_contract())
                return
            match = _JOB_ROUTE.fullmatch(parsed.path)
            if match:
                self._send_json(HTTPStatus.OK, self.server.data_update_store.read(match.group(1)))
                return
            if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico" or parsed.path.startswith("/reports/"):
                super().do_GET()
                return
            self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")
        except kernel.DataUpdateError as error:
            self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        try:
            if parsed.path == "/api/data-update/jobs":
                fields, filename, content = self._multipart_upload()
                self._send_json(HTTPStatus.CREATED, self.server.data_update_store.create(fields, filename, content))
                return
            match = _ACTION_ROUTE.fullmatch(parsed.path)
            if not match:
                super().do_POST()
                return
            job_id, action = match.groups()
            if action == "confirm":
                body = self._json_body()
                value = self.server.data_update_store.confirm(
                    job_id,
                    preview_id=str(body.get("preview_id", "")),
                    confirm_token=str(body.get("confirm_token", "")),
                    operator_role=str(body.get("operator_role", "ROLE::DATA_STEWARD")),
                )
            elif action == "resume":
                value = self.server.data_update_store.resume(job_id)
            else:
                value = self.server.data_update_store.cancel(job_id)
            self._send_json(HTTPStatus.OK, value)
        except kernel.DataUpdateError as error:
            self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})


class DataUpdateServer(base_runtime.TaxPolicyReportingServer):
    data_update_store: kernel.DataUpdateStore


def start_server(
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    event_path: Path | str = workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
    data_root: Path | str = kernel.DEFAULT_RUNTIME_ROOT,
) -> tuple[DataUpdateServer, threading.Thread, str]:
    event_file = Path(event_path)
    server = DataUpdateServer((host, port), DataUpdateHandler)
    server.journal = workflow_kernel.EventJournal(event_file)
    server.policy_journal = policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = reporting_kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    server.data_update_store = kernel.DataUpdateStore(data_root)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s20p1-data-update", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S20-P1 数据更新工作台")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--event-path", default=str(workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH))
    parser.add_argument("--data-root", default=str(kernel.DEFAULT_RUNTIME_ROOT))
    args = parser.parse_args()
    event_file = Path(args.event_path)
    server = DataUpdateServer((args.host, args.port), DataUpdateHandler)
    server.journal = workflow_kernel.EventJournal(event_file)
    server.policy_journal = policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = reporting_kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    server.data_update_store = kernel.DataUpdateStore(args.data_root)
    print(f"KMFA 数据更新：http://{args.host}:{server.server_address[1]}/data-update", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
