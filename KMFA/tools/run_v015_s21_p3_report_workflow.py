#!/usr/bin/env python3
"""Run the KMFA v1.5 S21-P3 local report workflow and report center."""

from __future__ import annotations

import argparse
import re
import threading
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s21_p2_report_generation as base_runtime
from KMFA.tools import v015_s21_p3_report_workflow as kernel


_CASE_ROUTE = re.compile(r"^/api/report-workflows/(CASE-S21P3-[A-F0-9]{12})$")
_CASE_ACTION_ROUTE = re.compile(r"^/api/report-workflows/(CASE-S21P3-[A-F0-9]{12})/(submit|review|approve|publish)$")


def render_html() -> str:
    html_text = base_runtime.render_html()
    view = r'''
    <section id="report-workflow-view" class="rw-view" aria-labelledby="rw-title" hidden>
      <header class="rw-head"><div><span>经营报告 · 第三步</span><h1 id="rw-title">看清变化，按角色复核，再发布到内部报告中心</h1><p>每一步都记录人员、角色、时间和意见；未经质量门禁、复核与批准，不能发布。</p></div><a href="/report-generation">返回报告生成</a></header>
      <nav class="s21-journey" aria-label="经营报告流程步骤"><a href="/report-model"><span>1</span><strong>报告模型</strong><small>期间、版本与受众</small></a><a href="/report-generation"><span>2</span><strong>生成报告</strong><small>网页、PDF 与附表</small></a><a href="/report-workflow" aria-current="step"><span>3</span><strong>复核发布</strong><small>审批、修订与报告中心</small></a></nav>
      <aside class="rw-boundary"><strong>安全边界</strong><span>这里只发布到本机内部报告中心；没有公开链接，不访问原始资料，不上传 GitHub，也不重装 App。</span></aside>
      <section class="rw-summary" aria-label="报告流程摘要"><article><span>待处理流程</span><strong id="rw-case-count">0</strong></article><article><span>报告版本</span><strong id="rw-report-count">0</strong></article><article><span>公开链接</span><strong>0</strong></article></section>
      <div id="rw-feedback" class="rw-feedback" role="status" aria-live="polite">正在读取报告流程…</div>

      <section class="rw-card" aria-labelledby="rw-flow-title"><div class="rw-card-head"><div><h2 id="rw-flow-title">1. 预览、复核、批准和内部发布</h2><p>同一个示例负责人可以切换已分配角色，但系统保留每一步角色，不虚构多人。</p></div><span id="rw-state">尚未开始</span></div>
        <div class="rw-form"><label>报告版本<select id="rw-report-version"></select></label><label>本步意见<input id="rw-comment" value="已核对数字、来源、限制说明和适用范围"></label><button id="rw-preview" class="rw-primary" type="button">开始预览</button></div>
        <div class="rw-actions"><button id="rw-submit" type="button">以财务角色提交</button><button id="rw-review-pass" type="button">以审核角色复核通过</button><button id="rw-review-change" type="button">要求修订</button><button id="rw-approve" type="button">以审核角色批准</button><button id="rw-publish" class="rw-primary" type="button">以经营负责人发布</button></div>
        <div id="rw-history" class="rw-history"></div>
      </section>

      <section class="rw-card" aria-labelledby="rw-revision-title"><div class="rw-card-head"><div><h2 id="rw-revision-title">2. 创建修订并解释变化</h2><p>修订只新增版本，不覆盖旧报告；每项变化都必须有来源和中文原因。</p></div><span id="rw-comparison-status">尚未比较</span></div>
        <div class="rw-form rw-revision"><label>基准版本<select id="rw-revision-base"></select></label><label>重点事项资料新版本<input id="rw-source-version" value="S20P2-CONFIRMATIONS-2026-07-V2"></label><label>修订原因<input id="rw-revision-reason" value="补充本期重点事项复核结果和负责人意见"></label><button id="rw-revise" class="rw-primary" type="button">创建修订版</button></div>
        <div class="rw-compare-form"><label>旧版本<select id="rw-from-version"></select></label><label>新版本<select id="rw-to-version"></select></label><button id="rw-compare" type="button">比较两个版本</button></div><div id="rw-comparison" class="rw-comparison"></div>
      </section>

      <section class="rw-card" aria-labelledby="rw-center-title"><div class="rw-card-head"><div><h2 id="rw-center-title">3. 报告中心</h2><p>按期间、状态和版本检索；查看与下载都按当前角色判断，不生成公开链接。</p></div><span id="rw-center-count">0 份</span></div>
        <div class="rw-center-filters"><label>主体<select id="rw-center-company"></select></label><label>期间<select id="rw-center-period"><option value="">全部期间</option></select></label><label>类型<select id="rw-center-type"><option value="">全部类型</option></select></label><label>状态<select id="rw-center-status"><option value="">全部状态</option><option value="GENERATED">已生成</option><option value="PREVIEWED">已预览</option><option value="IN_REVIEW">复核中</option><option value="REVIEWED">复核通过</option><option value="CHANGES_REQUESTED">需要修订</option><option value="APPROVED">已批准</option><option value="PUBLISHED_INTERNAL">内部已发布</option></select></label><label>版本<select id="rw-center-version"><option value="">全部版本</option></select></label><label>查看角色<select id="rw-center-role"><option value="management">经营负责人</option><option value="finance">财务</option><option value="reviewer">审核</option><option value="tax">税务</option></select></label><button id="rw-center-refresh" type="button">应用筛选</button></div>
        <div id="rw-center" class="rw-center"></div>
      </section>
      <p class="rw-stop">S21-P3 验收后立即停止；下一次独立 Run 只做 S21 整体复审，不进入 S22。</p>
    </section>
    '''
    css = r'''
    body[data-report-workflow-active="true"] main>section:not(#report-workflow-view),body[data-report-workflow-active="true"] #page-view,body[data-report-workflow-active="true"] #loading-view,body[data-report-workflow-active="true"] #error-view,body[data-report-workflow-active="true"] #not-found-view,body[data-report-workflow-active="true"] #homepage-view,body[data-report-workflow-active="true"] #project-list-view,body[data-report-workflow-active="true"] #project-detail-view,body[data-report-workflow-active="true"] #project-workflow-view,body[data-report-workflow-active="true"] #receivables-view,body[data-report-workflow-active="true"] #funds-view,body[data-report-workflow-active="true"] #funds-report-view,body[data-report-workflow-active="true"] #tax-invoice-view,body[data-report-workflow-active="true"] #policy-eligibility-view,body[data-report-workflow-active="true"] #tax-policy-report-view,body[data-report-workflow-active="true"] #data-update-view,body[data-report-workflow-active="true"] #confirmation-workbench-view,body[data-report-workflow-active="true"] #recalculation-publication-view,body[data-report-workflow-active="true"] #report-model-view,body[data-report-workflow-active="true"] #report-generation-view,body[data-report-workflow-active="true"] #context-status,body[data-report-workflow-active="true"] .identity-shell,body[data-report-workflow-active="true"] .quick-shell{display:none!important}body[data-report-workflow-active="true"] main{max-width:1240px!important}.rw-view{padding:18px 10px 50px;color:#263b49}.rw-head{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;padding:22px;border-radius:12px;background:linear-gradient(135deg,#173d57,#246c83);color:#fff}.rw-head span{font-size:11px;font-weight:800;letter-spacing:.08em}.rw-head h1{margin:6px 0;font-size:29px;color:#fff!important}.rw-head p{margin:0;color:#dcebf2}.rw-head a{display:inline-flex;min-height:44px;align-items:center;padding:0 14px;border:1px solid #b9d2df;border-radius:8px;color:#fff;text-decoration:none;font-weight:800}.s21-journey{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}.s21-journey a{display:grid;grid-template-columns:34px 1fr;grid-template-rows:auto auto;column-gap:9px;min-height:52px;padding:9px 11px;border:1px solid #cbd9e1;border-radius:8px;background:#fff;color:#31576b;text-decoration:none}.s21-journey a[aria-current="step"]{border-color:#246c83;background:#edf6f9}.s21-journey span{grid-row:1/3;align-self:center;display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:#246c83;color:#fff;font-weight:800}.s21-journey strong{align-self:end;font-size:12px}.s21-journey small{color:#657c89;font-size:10px}.rw-boundary{display:flex;justify-content:space-between;gap:14px;margin:12px 0;padding:12px 14px;border:1px solid #d5b27c;border-left:4px solid #a86a17;border-radius:8px;background:#fffaf2;color:#654519;font-size:12px}.rw-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:11px 0}.rw-summary article,.rw-card{padding:15px;border:1px solid #d8e2e8;border-radius:9px;background:#fff}.rw-summary span{display:block;color:#607684;font-size:11px}.rw-summary strong{display:block;margin-top:5px;color:#173d57;font-size:20px}.rw-feedback{min-height:44px;padding:11px 13px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:7px;background:#edf6fb;font-size:13px}.rw-feedback[data-state="error"]{border-color:#d7a6a6;background:#fff8f7;color:#7f2929}.rw-feedback[data-state="success"]{border-color:#9fc5ae;background:#f3faf5;color:#276346}.rw-card{margin-top:11px}.rw-card-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;margin-bottom:11px}.rw-card h2{margin:0;color:#214d68;font-size:18px}.rw-card-head p{margin:5px 0 0;color:#607684;font-size:11px}.rw-card-head>span{padding:6px 9px;border-radius:999px;background:#edf4f7;color:#245a70;font-size:11px;font-weight:800}.rw-form{display:grid;grid-template-columns:minmax(220px,.8fr) minmax(280px,1.4fr) auto;gap:9px;align-items:end}.rw-form label,.rw-center-filters label,.rw-compare-form label{display:grid;gap:5px;font-size:11px;font-weight:800}.rw-view input,.rw-view select,.rw-view button{min-height:44px;padding:0 11px;border:1px solid #b9cbd7;border-radius:7px;background:#fff;font:inherit}.rw-view button{font-weight:800;color:#245a70}.rw-primary{border-color:#246c83!important;background:#246c83!important;color:#fff!important}.rw-actions{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-top:10px}.rw-actions button:disabled{opacity:.45}.rw-history{display:grid;gap:7px;margin-top:12px}.rw-event{display:grid;grid-template-columns:150px 140px 1fr;gap:9px;padding:10px;border-left:3px solid #2f7aa4;background:#f7fafc;font-size:11px}.rw-revision{grid-template-columns:.7fr 1fr 1.5fr auto}.rw-compare-form{display:grid;grid-template-columns:1fr 1fr auto;gap:9px;align-items:end;margin-top:12px}.rw-comparison{display:grid;gap:7px;margin-top:10px}.rw-change{display:grid;grid-template-columns:1fr 1fr 1.5fr;gap:8px;padding:10px;border:1px solid #dce5ea;border-radius:7px;font-size:11px}.rw-center-filters{display:grid;grid-template-columns:repeat(3,minmax(150px,1fr)) auto;gap:9px;align-items:end}.rw-center{display:grid;gap:9px;margin-top:11px}.rw-report{padding:13px;border:1px solid #dce5ea;border-radius:8px}.rw-report header{display:flex;justify-content:space-between;gap:12px}.rw-report h3{margin:0;color:#214d68;font-size:14px}.rw-report p{margin:4px 0;color:#607684;font-size:11px}.rw-downloads{display:flex;flex-wrap:wrap;gap:7px;margin-top:9px}.rw-downloads button{min-width:120px}.rw-stop{color:#607684;font-size:11px}
    @media(max-width:780px){.rw-head,.rw-boundary,.rw-card-head{display:grid}.rw-head a{justify-self:start}.s21-journey,.rw-summary,.rw-form,.rw-revision,.rw-actions,.rw-compare-form,.rw-center-filters{grid-template-columns:1fr}.rw-event,.rw-change{grid-template-columns:1fr}.rw-report header{display:grid}.rw-view button{width:100%}}
    '''
    script = r'''
    <script>
    (()=>{'use strict';if(!['/report-workflow','/report-center'].includes(location.pathname))return;document.body.dataset.reportWorkflowActive='true';const view=document.querySelector('#report-workflow-view');view.hidden=false;const state={reports:null,exports:null,workflows:null,current:null,comparison:null,center:null},feedback=document.querySelector('#rw-feedback');let requestNumber=0;
      const api=async(path,init={})=>{const response=await fetch(path,init),type=response.headers.get('content-type')||'',value=type.includes('json')?await response.json():await response.text();if(!response.ok)throw Object.assign(new Error(value.message_zh||value.reason_zh||'请求失败'),{payload:value,status:response.status});return value};
      const post=(path,body)=>api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const say=(text,kind='')=>{feedback.textContent=text;if(kind)feedback.dataset.state=kind;else delete feedback.dataset.state};const key=prefix=>prefix+'-'+Date.now()+'-'+(++requestNumber);
      const fill=(select,rows,label,preferred='')=>{const current=preferred||select.value;select.replaceChildren();rows.forEach(row=>{const option=document.createElement('option');option.value=row.report_version_id;option.textContent=label(row);select.append(option)});if([...select.options].some(o=>o.value===current))select.value=current};
      const fillFilter=(select,rows,valueOf,labelOf)=>{const current=select.value,blank=select.querySelector('option[value=""]')?.textContent||'全部';select.replaceChildren(new Option(blank,''));const seen=new Set();rows.forEach(row=>{const value=String(valueOf(row)||'');if(value&&!seen.has(value)){seen.add(value);select.append(new Option(labelOf(row),value))}});if([...select.options].some(o=>o.value===current))select.value=current};
      const renderReports=(value,preferred='')=>{state.reports=value;const label=row=>(row.company_label_zh||row.company_id)+' · '+row.period.period_label_zh+' · '+row.version_label_zh;['#rw-report-version','#rw-revision-base','#rw-from-version','#rw-to-version'].forEach(selector=>fill(document.querySelector(selector),value.reports,label,selector==='#rw-report-version'?preferred:''));if(value.reports.length>1){document.querySelector('#rw-from-version').value=value.reports[value.reports.length-1].report_version_id;document.querySelector('#rw-to-version').value=value.reports[0].report_version_id}fillFilter(document.querySelector('#rw-center-company'),value.reports,row=>row.company_id,row=>row.company_label_zh||row.company_id);fillFilter(document.querySelector('#rw-center-period'),value.reports,row=>row.period.period_key,row=>row.period.period_label_zh);fillFilter(document.querySelector('#rw-center-type'),value.reports,row=>row.period.period_kind,row=>row.period.period_kind_label_zh);fillFilter(document.querySelector('#rw-center-version'),value.reports,row=>row.report_version_id,row=>(row.company_label_zh||row.company_id)+' · '+row.version_label_zh);if(!document.querySelector('#rw-center-company').value&&value.reports[0])document.querySelector('#rw-center-company').value=value.reports[0].company_id;document.querySelector('#rw-report-count').textContent=value.report_version_count};
      const renderCase=value=>{state.current=value||null;document.querySelector('#rw-state').textContent=value?value.state_zh:'尚未开始';const root=document.querySelector('#rw-history');root.replaceChildren();(value?.events||[]).forEach(row=>{const card=document.createElement('article');card.className='rw-event';[row.event_type,row.actor_label_zh+' · '+row.actor_role,row.occurred_at+' · '+row.comment_zh].forEach(text=>{const span=document.createElement('span');span.textContent=text;card.append(span)});root.append(card)});const allowed={PREVIEWED:['rw-submit'],IN_REVIEW:['rw-review-pass','rw-review-change'],REVIEWED:['rw-approve'],APPROVED:['rw-publish']}[value?.state]||[];['rw-submit','rw-review-pass','rw-review-change','rw-approve','rw-publish'].forEach(id=>document.querySelector('#'+id).disabled=!allowed.includes(id))};
      const renderWorkflows=value=>{state.workflows=value;document.querySelector('#rw-case-count').textContent=value.case_count;const selected=document.querySelector('#rw-report-version').value;renderCase(value.cases.find(row=>row.report_version_id===selected)||null)};
      const renderComparison=value=>{state.comparison=value;document.querySelector('#rw-comparison-status').textContent=value.publication_allowed?'变化可解释':'存在阻塞变化';const root=document.querySelector('#rw-comparison');root.replaceChildren();value.changes.forEach(row=>{const card=document.createElement('article');card.className='rw-change';[row.field,String(row.before)+' → '+String(row.after),row.reason_zh+' · 来源 '+row.source_ref].forEach(text=>{const span=document.createElement('span');span.textContent=text;card.append(span)});root.append(card)})};
      const identityHeaders=role=>({'X-KMFA-User':'demo-owner','X-KMFA-Role':role,'X-KMFA-Company':document.querySelector('#rw-center-company').value});
      const download=async(row,format)=>{const suffix={HTML:'html',PDF:'pdf',CSV:'appendix.csv'}[format],response=await fetch('/api/report-exports/'+row.export_id+'/'+suffix,{headers:identityHeaders(document.querySelector('#rw-center-role').value)});if(!response.ok){const value=await response.json();throw new Error(value.message_zh||value.reason_zh||'下载被阻止')}const blob=await response.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='kmfa-'+row.report_version_id+'-'+suffix;a.click();URL.revokeObjectURL(url)};
      const renderCenter=value=>{state.center=value;document.querySelector('#rw-center-count').textContent=value.result_count+' 份';const root=document.querySelector('#rw-center');root.replaceChildren();value.reports.forEach(row=>{const card=document.createElement('article');card.className='rw-report';const head=document.createElement('header'),copy=document.createElement('div'),title=document.createElement('h3'),meta=document.createElement('p'),status=document.createElement('strong');title.textContent=row.period.period_label_zh+' · '+row.version_label_zh;meta.textContent=row.report_version_id+' · 无公开链接';status.textContent=row.status_zh;copy.append(title,meta);head.append(copy,status);const actions=document.createElement('div');actions.className='rw-downloads';row.download_formats.forEach(format=>{const button=document.createElement('button');button.type='button';button.textContent='受控下载 '+format;button.addEventListener('click',()=>download(row,format).catch(error=>say(error.message,'error')));actions.append(button)});if(!row.download_formats.length){const note=document.createElement('p');note.textContent='当前角色没有下载权限';actions.append(note)}card.append(head,actions);root.append(card)})};
      const loadCenter=async()=>{const role=document.querySelector('#rw-center-role').value,company=document.querySelector('#rw-center-company').value,query=new URLSearchParams({user_id:'demo-owner',role_id:role,company_id:company});[['period_key','#rw-center-period'],['report_type','#rw-center-type'],['status','#rw-center-status'],['version','#rw-center-version']].forEach(([name,selector])=>{const value=document.querySelector(selector).value;if(value)query.set(name,value)});const value=await api('/api/report-center?'+query);renderCenter(value);return value};
      const load=async(preferred='')=>{const [reports,exports,workflows]=await Promise.all([api('/api/report-models'),api('/api/report-exports'),api('/api/report-workflows')]);renderReports(reports,preferred);state.exports=exports;renderWorkflows(workflows);await loadCenter();say(reports.report_version_count?'请选择报告版本开始预览。':'请先完成报告生成。',reports.report_version_count?'success':'error');return state};
      const preview=async()=>{const reportId=document.querySelector('#rw-report-version').value,report=state.reports.reports.find(row=>row.report_version_id===reportId),exportRow=state.exports.exports.find(row=>row.report_version_id===reportId);if(!exportRow)throw new Error('所选版本还没有三格式报告');const value=await post('/api/report-workflows/preview',{report_version_id:reportId,export_id:exportRow.export_id,user_id:'demo-owner',role_id:'finance',company_id:report.company_id,comment_zh:document.querySelector('#rw-comment').value,idempotency_key:key('browser-preview')});await load(reportId);say('预览已记录，可以提交复核。','success');return value};
      const action=async(name,decision=null)=>{if(!state.current)throw new Error('请先开始预览');const reportId=state.current.report_version_id,roles={submit:'finance',review:'reviewer',approve:'reviewer',publish:'management'},body={user_id:'demo-owner',role_id:roles[name],company_id:state.current.company_id,comment_zh:document.querySelector('#rw-comment').value,idempotency_key:key('browser-'+name)};if(decision)body.decision=decision;const value=await post('/api/report-workflows/'+state.current.case_id+'/'+name,body);await load(reportId);say(value.state_zh+'，人员、角色、时间和意见已记录。','success');return value};
      const revise=async()=>{const value=await post('/api/report-revisions',{base_report_version_id:document.querySelector('#rw-revision-base').value,source_version_updates:{key_matters:document.querySelector('#rw-source-version').value},revision_reason_zh:document.querySelector('#rw-revision-reason').value,created_by:'公开演示负责人',idempotency_key:key('browser-revision')});renderComparison(value.comparison);await load(value.report.report_version_id);document.querySelector('#rw-from-version').value=value.comparison.from_version_id;document.querySelector('#rw-to-version').value=value.comparison.to_version_id;say('修订版已新增，旧版本仍保留。','success');return value};
      const compare=async()=>{const query=new URLSearchParams({from:document.querySelector('#rw-from-version').value,to:document.querySelector('#rw-to-version').value}),value=await api('/api/report-comparisons?'+query);renderComparison(value);return value};
      document.querySelector('#rw-preview').addEventListener('click',()=>preview().catch(error=>say(error.message,'error')));document.querySelector('#rw-submit').addEventListener('click',()=>action('submit').catch(error=>say(error.message,'error')));document.querySelector('#rw-review-pass').addEventListener('click',()=>action('review','PASS').catch(error=>say(error.message,'error')));document.querySelector('#rw-review-change').addEventListener('click',()=>action('review','REQUEST_CHANGES').catch(error=>say(error.message,'error')));document.querySelector('#rw-approve').addEventListener('click',()=>action('approve').catch(error=>say(error.message,'error')));document.querySelector('#rw-publish').addEventListener('click',()=>action('publish').catch(error=>say(error.message,'error')));document.querySelector('#rw-revise').addEventListener('click',()=>revise().catch(error=>say(error.message,'error')));document.querySelector('#rw-compare').addEventListener('click',()=>compare().catch(error=>say(error.message,'error')));document.querySelector('#rw-report-version').addEventListener('change',()=>renderWorkflows(state.workflows));['#rw-center-company','#rw-center-period','#rw-center-type','#rw-center-status','#rw-center-version','#rw-center-role'].forEach(selector=>document.querySelector(selector).addEventListener('change',()=>loadCenter().catch(error=>say(error.message,'error'))));document.querySelector('#rw-center-refresh').addEventListener('click',()=>loadCenter().catch(error=>say(error.message,'error')));window.KMFA_REPORT_WORKFLOW_TEST={snapshot:()=>structuredClone(state),load,preview,action,revise,compare,loadCenter};load().catch(error=>say(error.message,'error'));
    })();
    </script>
    '''
    html_text = html_text.replace("</main>", view + "</main>", 1)
    html_text = html_text.replace("</style>", css + "</style>", 1)
    html_text = html_text.replace("</body>", script + "</body>", 1)
    html_text = html_text.replace(
        "<p class=\"rg-stop\">S21-P2 完成本地验收后停止。审批发布属于 S21-P3；GitHub 上传和 App 重装要等全部任务包完成。</p>",
        "<p class=\"rg-stop\">报告生成完成后，可进入 <a href=\"/report-workflow\">报告工作流</a>，进行预览、复核、批准和内部发布。</p>",
    )
    html_text = html_text.replace("<title>KMFA 报告生成 · 经营工作台</title>", "<title>KMFA 报告工作流 · 经营工作台</title>")
    return "\n".join(line.rstrip() for line in html_text.splitlines()) + "\n"


class ReportWorkflowHandler(base_runtime.ReportGenerationHandler):
    server_version = "KMFAReportWorkflow/1.5"

    @property
    def workflows(self) -> kernel.ReportWorkflowJournal:
        return self.server.report_workflow_journal  # type: ignore[attr-defined,no-any-return]

    def _case_for_report(self, report_version_id: str):
        return next((row for row in self.workflows.list()["cases"] if row["report_version_id"] == report_version_id), None)

    def _identity_headers(self) -> tuple[str, str, str]:
        return (
            self.headers.get("X-KMFA-User", ""),
            self.headers.get("X-KMFA-Role", ""),
            self.headers.get("X-KMFA-Company", ""),
        )

    def _report_center(self, query: dict[str, list[str]]) -> dict:
        value = lambda name: query.get(name, [None])[0]
        return kernel.report_center(
            self.report_models.list()["reports"], self.report_exports.list()["exports"], self.workflows.list()["cases"],
            user_id=str(value("user_id") or ""), role_id=str(value("role_id") or ""), company_id=str(value("company_id") or ""),
            period_kind=value("period_kind"), period_key=value("period_key"), status=value("status"),
            version=value("version"), report_type=value("report_type"),
        )

    def do_GET(self) -> None:  # noqa: N802
        parsed, path = urlsplit(self.path), urlsplit(self.path).path
        try:
            if path == "/api/report-workflows/options":
                self._send_json(HTTPStatus.OK, kernel.options_contract())
                return
            if path == "/api/report-workflows":
                self._send_json(HTTPStatus.OK, self.workflows.list())
                return
            case_match = _CASE_ROUTE.fullmatch(path)
            if case_match:
                self._send_json(HTTPStatus.OK, self.workflows.get(case_match.group(1)))
                return
            if path == "/api/report-comparisons":
                query = parse_qs(parsed.query)
                left = self.report_models.get(str(query.get("from", [""])[0]))
                right = self.report_models.get(str(query.get("to", [""])[0]))
                self._send_json(HTTPStatus.OK, kernel.compare_versions(left, right))
                return
            if path == "/api/report-center":
                self._send_json(HTTPStatus.OK, self._report_center(parse_qs(parsed.query)))
                return
            file_match = base_runtime._FILE_ROUTE.fullmatch(path)
            if file_match:
                export = self.report_exports.get(file_match.group(1))
                report = self.report_models.get(export["report_version_id"])
                user_id, role_id, company_id = self._identity_headers()
                format_name = {"html": "HTML", "pdf": "PDF", "appendix.csv": "CSV"}[file_match.group(2)]
                decision = kernel.authorize_download(
                    report, self._case_for_report(report["report_version_id"]), user_id=user_id,
                    role_id=role_id, company_id=company_id, format_name=format_name,
                )
                if not decision["allowed"]:
                    raise kernel.ReportWorkflowError(str(decision["code"]), str(decision["reason_zh"]), status=403)
                file_path, metadata = self.report_exports.file_path(export["export_id"], format_name)
                self._send_download(file_path.read_bytes(), metadata["content_type"], metadata["filename"], inline=format_name == "HTML")
                return
            if path.startswith("/api/report-workflows/") or path.startswith("/api/report-center/"):
                raise kernel.ReportWorkflowError("RESOURCE_NOT_FOUND", "没有找到这条报告流程或报告", status=404)
            if path.startswith("/api/") or path == "/favicon.ico" or path.startswith("/reports/"):
                super().do_GET()
                return
            self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")
        except (base_runtime.base_runtime.kernel.ReportModelError, base_runtime.kernel.ReportGenerationError, kernel.ReportWorkflowError) as error:
            self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            if path == "/api/report-workflows/preview":
                body = self._json_body()
                report = self.report_models.get(str(body.get("report_version_id", "")))
                export = self.report_exports.get(str(body.get("export_id", "")))
                for format_name in kernel.FORMATS:
                    self.report_exports.file_path(export["export_id"], format_name)
                value = self.workflows.preview(
                    report, export, user_id=str(body.get("user_id", "")), role_id=str(body.get("role_id", "")),
                    company_id=str(body.get("company_id", "")), comment_zh=str(body.get("comment_zh", "")),
                    idempotency_key=str(body.get("idempotency_key", "")),
                )
                self._send_json(HTTPStatus.CREATED, value)
                return
            action_match = _CASE_ACTION_ROUTE.fullmatch(path)
            if action_match:
                body = self._json_body()
                kwargs = {
                    "user_id": str(body.get("user_id", "")), "role_id": str(body.get("role_id", "")),
                    "company_id": str(body.get("company_id", "")), "comment_zh": str(body.get("comment_zh", "")),
                    "idempotency_key": str(body.get("idempotency_key", "")),
                }
                action = action_match.group(2)
                if action == "review":
                    kwargs["decision"] = str(body.get("decision", ""))
                value = getattr(self.workflows, action)(action_match.group(1), **kwargs)
                self._send_json(HTTPStatus.OK, value)
                return
            if path == "/api/report-revisions":
                body = self._json_body()
                base = self.report_models.get(str(body.get("base_report_version_id", "")))
                bindings = kernel.revision_bindings(base, body.get("source_version_updates") or {})
                key = str(body.get("idempotency_key", ""))
                revised = self.report_models.revise(
                    base["report_version_id"], source_bindings=bindings,
                    revision_reason_zh=str(body.get("revision_reason_zh", "")), created_by=str(body.get("created_by", "")),
                    idempotency_key=key + "-model",
                )
                export = self.report_exports.create(revised, idempotency_key=key + "-export")
                self._send_json(HTTPStatus.CREATED, {
                    "schema_version": "kmfa.v015.s21p3.revision_result.v1",
                    "report": revised, "export": export, "comparison": kernel.compare_versions(base, revised),
                })
                return
            super().do_POST()
        except (TypeError, base_runtime.base_runtime.kernel.ReportModelError, base_runtime.kernel.ReportGenerationError, kernel.ReportWorkflowError) as error:
            if isinstance(error, (base_runtime.base_runtime.kernel.ReportModelError, base_runtime.kernel.ReportGenerationError, kernel.ReportWorkflowError)):
                self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})
            else:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "code": "INVALID_REQUEST", "message_zh": "请求格式不正确"})


class ReportWorkflowServer(base_runtime.ReportGenerationServer):
    report_workflow_journal: kernel.ReportWorkflowJournal


def start_server(
    host: str = "127.0.0.1", port: int = 0, *,
    event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
    data_root: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.data_update_kernel.DEFAULT_RUNTIME_ROOT,
    confirmation_event_path: Path | str = base_runtime.base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    publication_event_path: Path | str = base_runtime.base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    report_model_event_path: Path | str = base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH,
    export_event_path: Path | str = base_runtime.kernel.DEFAULT_EVENT_PATH,
    export_bundle_root: Path | str = base_runtime.kernel.DEFAULT_BUNDLE_ROOT,
    workflow_event_path: Path | str = kernel.DEFAULT_EVENT_PATH,
) -> tuple[ReportWorkflowServer, threading.Thread, str]:
    event_file = Path(event_path)
    server = ReportWorkflowServer((host, port), ReportWorkflowHandler)
    server.journal = base_runtime.base_runtime.base_runtime.base_runtime.workflow_kernel.EventJournal(event_file)
    server.policy_journal = base_runtime.base_runtime.base_runtime.base_runtime.policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = base_runtime.base_runtime.base_runtime.base_runtime.reporting_kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    server.data_update_store = base_runtime.base_runtime.base_runtime.base_runtime.data_update_kernel.DataUpdateStore(data_root)
    server.confirmation_workbench = base_runtime.base_runtime.base_runtime.base_runtime.kernel.ConfirmationWorkbench(confirmation_event_path)
    server.recalculation_workbench = base_runtime.base_runtime.base_runtime.kernel.RecalculationPublicationWorkbench(confirmation_event_path, publication_event_path)
    server.report_model_journal = base_runtime.base_runtime.kernel.ReportModelJournal(report_model_event_path)
    server.report_export_journal = base_runtime.kernel.ReportExportJournal(export_event_path, export_bundle_root)
    server.report_workflow_journal = kernel.ReportWorkflowJournal(workflow_event_path)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s21p3-report-workflow", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S21-P3 报告工作流")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--report-model-event-path", default=str(base_runtime.base_runtime.kernel.DEFAULT_EVENT_PATH))
    parser.add_argument("--export-event-path", default=str(base_runtime.kernel.DEFAULT_EVENT_PATH))
    parser.add_argument("--export-bundle-root", default=str(base_runtime.kernel.DEFAULT_BUNDLE_ROOT))
    parser.add_argument("--workflow-event-path", default=str(kernel.DEFAULT_EVENT_PATH))
    args = parser.parse_args()
    server, thread, url = start_server(
        args.host, args.port, report_model_event_path=args.report_model_event_path,
        export_event_path=args.export_event_path, export_bundle_root=args.export_bundle_root,
        workflow_event_path=args.workflow_event_path,
    )
    print(f"KMFA 报告工作流：{url}/report-workflow", flush=True)
    try:
        thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
