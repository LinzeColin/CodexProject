#!/usr/bin/env python3
"""Run the KMFA v1.5 S20-P2 confirmation workbench on localhost."""

from __future__ import annotations

import argparse
import re
import threading
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s20_p1_data_update as base_runtime
from KMFA.tools import v015_s17_p3_project_workflow as workflow_kernel
from KMFA.tools import v015_s19_p2_policy_eligibility as policy_kernel
from KMFA.tools import v015_s19_p3_tax_policy_reporting as reporting_kernel
from KMFA.tools import v015_s20_p1_data_update as data_update_kernel
from KMFA.tools import v015_s20_p2_confirmation_workbench as kernel


_ISSUE_ROUTE = re.compile(r"^/api/confirmation/issues/(ISSUE-S20P2-\d{3})$")
_ISSUE_ACTION_ROUTE = re.compile(r"^/api/confirmation/issues/(ISSUE-S20P2-\d{3})/(preview|confirm)$")
_EVENT_ACTION_ROUTE = re.compile(r"^/api/confirmation/events/(CTRL-S20P2-\d{4})/(undo-preview|undo)$")


def render_html() -> str:
    html = base_runtime.render_html()
    view = r'''
    <section id="confirmation-workbench-view" class="cw-view" aria-labelledby="cw-title" hidden>
      <header class="cw-head"><div><span>数据更新 · 人工确认</span><h1 id="cw-title">先看业务影响，再决定怎么处理</h1><p>这里只显示需要人处理的业务问题。所有动作写入可撤销记录，不修改原始值。</p></div><a class="cw-back" href="/data-update" data-route="/data-update">返回数据更新</a></header>
      <aside class="cw-boundary"><strong>本阶段边界</strong><span>只登记控制事件；不编辑原始值、不重算、不刷新或发布报告。</span></aside>
      <section class="cw-summary" aria-label="问题概况"><article><span>待处理</span><strong id="cw-open-count">0</strong></article><article><span>最高影响</span><strong id="cw-highest-impact">—</strong></article><article><span>处理历史</span><strong id="cw-history-count">0</strong></article></section>
      <div id="cw-feedback" class="cw-feedback" role="status" aria-live="polite">正在读取需要处理的事项…</div>
      <section class="cw-toolbar" aria-label="问题筛选"><label><input id="cw-include-resolved" type="checkbox"> 同时显示已处理事项</label><button id="cw-refresh" type="button">刷新</button></section>
      <div class="cw-layout">
        <section class="cw-card cw-list-card" aria-labelledby="cw-list-title"><div class="cw-card-head"><div><h2 id="cw-list-title">需要处理的问题</h2><p>按影响、紧急度、来源和负责人排列。</p></div><span id="cw-list-count">0 项</span></div><div id="cw-list" class="cw-list"></div></section>
        <section id="cw-detail-card" class="cw-card cw-detail-card" aria-labelledby="cw-detail-title" hidden>
          <div class="cw-card-head"><div><span id="cw-detail-badges" class="cw-badges"></span><h2 id="cw-detail-title">问题详情</h2><p id="cw-detail-owner"></p></div><button id="cw-close-detail" type="button">关闭</button></div>
          <div class="cw-compare"><section><h3>当前资料</h3><dl id="cw-current-data"></dl></section><section><h3>参考资料</h3><dl id="cw-reference-data"></dl></section></div>
          <section class="cw-explanation"><h3>业务说明</h3><p id="cw-business-explanation"></p><strong>可能影响</strong><p id="cw-impact-copy"></p></section>
          <fieldset id="cw-actions"><legend>建议处理方式</legend></fieldset>
          <label class="cw-reason">处理理由<textarea id="cw-reason" rows="2">已核对两侧资料、业务解释和影响后确认</textarea></label>
          <button id="cw-preview" class="cw-primary" type="button">先看影响预览</button>
          <details id="cw-technical"><summary>查看技术依据</summary><dl id="cw-technical-data"></dl></details>
        </section>
      </div>
      <section id="cw-preview-card" class="cw-card cw-preview-card" aria-labelledby="cw-preview-title" hidden><div class="cw-card-head"><div><h2 id="cw-preview-title">确认前影响预览</h2><p>预览与当前问题和处理方式绑定，内容变化后必须重新预览。</p></div><span id="cw-preview-risk">—</span></div><dl id="cw-preview-data"></dl><p id="cw-preview-impact"></p><div class="cw-actions"><button id="cw-confirm" class="cw-primary" type="button">确认处理</button><button id="cw-preview-cancel" type="button">取消</button></div></section>
      <section class="cw-card cw-history-card" aria-labelledby="cw-history-title"><div class="cw-card-head"><div><h2 id="cw-history-title">处理与撤销历史</h2><p>旧记录永不覆盖；撤销会追加一条新记录。</p></div><span id="cw-history-label">0 条</span></div><div class="cw-table-wrap"><table><thead><tr><th>顺序</th><th>事项</th><th>处理</th><th>操作人</th><th>状态</th><th></th></tr></thead><tbody id="cw-history"></tbody></table></div></section>
      <p class="cw-disclaimer">S20-P2 只完成人工确认闭环。受影响链重算、前后对比、跨页面同步和发布属于 S20-P3，本阶段没有执行。</p>
    </section>
    '''
    css = r'''
    body[data-confirmation-active="true"] #page-view,body[data-confirmation-active="true"] #loading-view,body[data-confirmation-active="true"] #error-view,body[data-confirmation-active="true"] #not-found-view,body[data-confirmation-active="true"] #homepage-view,body[data-confirmation-active="true"] #project-list-view,body[data-confirmation-active="true"] #project-detail-view,body[data-confirmation-active="true"] #project-workflow-view,body[data-confirmation-active="true"] #receivables-view,body[data-confirmation-active="true"] #funds-view,body[data-confirmation-active="true"] #funds-report-view,body[data-confirmation-active="true"] #tax-invoice-view,body[data-confirmation-active="true"] #policy-eligibility-view,body[data-confirmation-active="true"] #tax-policy-report-view,body[data-confirmation-active="true"] #data-update-view,body[data-confirmation-active="true"] #context-status,body[data-confirmation-active="true"] .identity-shell,body[data-confirmation-active="true"] .quick-shell,body[data-confirmation-active="true"] #access-workspace,body[data-confirmation-active="true"] #experience-workspace{display:none!important}
    .cw-view{margin:2px 0 30px;color:#29475d}.cw-head{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;margin-bottom:12px}.cw-head span{color:#17648f;font-size:12px;font-weight:800}.cw-head h1{margin:4px 0;color:#173d57;font-size:30px}.cw-head p{margin:6px 0;max-width:780px;color:#607684;font-size:13px}.cw-back,.cw-toolbar button,.cw-card-head button,.cw-actions button{display:inline-flex;min-height:44px;align-items:center;justify-content:center;padding:0 14px;border:1px solid #9fb8c8;border-radius:7px;background:#fff;color:#245a7a;font:inherit;font-size:12px;font-weight:800;text-decoration:none;cursor:pointer}.cw-boundary{display:flex;justify-content:space-between;gap:16px;padding:12px 14px;border:1px solid #d5b27c;border-left:4px solid #a86a17;border-radius:8px;background:#fffaf2;color:#654519}.cw-boundary span{font-size:12px}.cw-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:11px 0}.cw-summary article{padding:13px;border:1px solid #d8e2e8;border-radius:8px;background:#fff}.cw-summary span{display:block;color:#607684;font-size:11px}.cw-summary strong{display:block;margin-top:5px;color:#173d57;font-size:23px}.cw-feedback{min-height:44px;padding:10px 12px;border:1px solid #bfd2df;border-left:4px solid #2f7aa4;border-radius:7px;background:#edf6fb;font-size:13px}.cw-feedback[data-state="error"]{border-color:#d7a6a6;background:#fff8f7;color:#7f2929}.cw-feedback[data-state="success"]{border-color:#9fc5ae;background:#f3faf5;color:#276346}.cw-toolbar{display:flex;justify-content:space-between;align-items:center;margin:10px 0}.cw-toolbar label{min-height:44px;display:flex;align-items:center;gap:8px;font-size:12px}.cw-layout{display:grid;grid-template-columns:minmax(320px,.78fr) minmax(420px,1.22fr);gap:12px}.cw-card{padding:16px;border:1px solid #d8e2e8;border-radius:9px;background:#fff}.cw-card-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;margin-bottom:12px}.cw-card-head h2{margin:0;color:#214d68;font-size:18px}.cw-card-head p{margin:5px 0 0;color:#607684;font-size:11px}.cw-card-head>span{font-size:11px;font-weight:800}.cw-list{display:grid;gap:8px}.cw-issue{width:100%;padding:12px;border:1px solid #dce5ea;border-radius:8px;background:#fbfcfd;text-align:left;cursor:pointer}.cw-issue:hover,.cw-issue:focus{border-color:#5d95b1;background:#f0f7fa}.cw-issue-head{display:flex;justify-content:space-between;gap:10px}.cw-issue strong{color:#29475d;font-size:13px}.cw-issue p{margin:7px 0 0;color:#607684;font-size:11px}.cw-tags,.cw-badges{display:flex;flex-wrap:wrap;gap:5px}.cw-tag{display:inline-flex;padding:3px 7px;border-radius:999px;background:#edf3f6;color:#40596b;font-size:9px;font-weight:800}.cw-tag[data-impact="CRITICAL"],.cw-tag[data-impact="HIGH"]{background:#fff0ed;color:#923b33}.cw-tag[data-status="RESOLVED"]{background:#eaf7ee;color:#276346}.cw-compare{display:grid;grid-template-columns:1fr 1fr;gap:10px}.cw-compare section{padding:11px;border:1px solid #dce5ea;border-radius:7px;background:#fafcfd}.cw-compare h3,.cw-explanation h3{margin:0 0 7px;color:#40596b;font-size:13px}.cw-compare dl,.cw-technical-data{margin:0}.cw-compare dl div,#cw-technical-data div{display:flex;justify-content:space-between;gap:8px;padding:6px 0;border-bottom:1px solid #e5ebef}.cw-compare dl div:last-child,#cw-technical-data div:last-child{border-bottom:0}.cw-compare dt,#cw-technical-data dt{color:#607684;font-size:10px}.cw-compare dd,#cw-technical-data dd{margin:0;text-align:right;font-size:11px;font-weight:800}.cw-explanation{margin:10px 0;padding:11px;border-radius:7px;background:#f3f8fb}.cw-explanation p{margin:5px 0 9px;font-size:12px;line-height:1.5}.cw-explanation strong{font-size:11px}.cw-detail-card fieldset{display:grid;gap:7px;margin:10px 0;padding:11px;border:1px solid #d6e0e6;border-radius:7px}.cw-detail-card legend{padding:0 6px;font-size:12px;font-weight:800}.cw-action-option{display:grid;grid-template-columns:auto 1fr;gap:8px;align-items:start;padding:8px;border:1px solid #e0e7eb;border-radius:6px}.cw-action-option strong{display:block;font-size:11px}.cw-action-option small{display:block;margin-top:3px;color:#607684;font-size:10px}.cw-reason{display:grid;gap:5px;margin-bottom:9px;font-size:11px;font-weight:800}.cw-reason textarea{min-height:58px;padding:8px;border:1px solid #b9cbd7;border-radius:7px;font:inherit}.cw-primary{border:0!important;background:#246c83!important;color:#fff!important}.cw-detail-card>.cw-primary{width:100%;min-height:44px;border-radius:7px;font:inherit;font-size:12px;font-weight:800;cursor:pointer}.cw-detail-card>.cw-primary:disabled{background:#a9b6bd!important}.cw-detail-card details{margin-top:10px;padding:10px;border:1px solid #dce5ea;border-radius:7px}.cw-detail-card summary{cursor:pointer;font-size:11px;font-weight:800}.cw-preview-card{margin-top:12px;border-color:#d5b27c;background:#fffdf8}.cw-preview-card dl{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:0}.cw-preview-card dl div{padding:9px;border-radius:6px;background:#fff}.cw-preview-card dt{font-size:10px;color:#607684}.cw-preview-card dd{margin:4px 0 0;font-size:12px;font-weight:800}.cw-preview-card>p{font-size:12px}.cw-actions{display:flex;gap:8px}.cw-history-card{margin-top:12px}.cw-table-wrap{overflow:auto;border:1px solid #dce5ea;border-radius:7px}.cw-history-card table{width:100%;border-collapse:collapse;font-size:10px}.cw-history-card th,.cw-history-card td{padding:8px;border-bottom:1px solid #e3e9ed;text-align:left;white-space:nowrap}.cw-history-card th{background:#f3f6f8}.cw-history-card button{min-height:44px;padding:0 9px;border:1px solid #9fb8c8;border-radius:6px;background:#fff;color:#245a7a;font:inherit;font-size:10px;font-weight:800;cursor:pointer}.cw-disclaimer{color:#607684;font-size:11px;line-height:1.5}
    @media(max-width:850px){.cw-layout{grid-template-columns:1fr}.cw-head,.cw-boundary{display:grid}.cw-head h1{font-size:25px}.cw-back{justify-self:start}.cw-summary{grid-template-columns:1fr 1fr 1fr}.cw-compare{grid-template-columns:1fr}.cw-preview-card dl{grid-template-columns:1fr}.cw-card{padding:13px}}
    @media(max-width:480px){.cw-summary{grid-template-columns:1fr}.cw-toolbar{display:grid;gap:6px}.cw-toolbar button{width:100%}.cw-actions{display:grid}.cw-actions button{width:100%}}
    '''
    script = r'''
  <script>
  (()=>{'use strict';
    const view=document.querySelector('#confirmation-workbench-view'),feedback=document.querySelector('#cw-feedback');let listSnapshot=null,detailSnapshot=null,historySnapshot=null,previewSnapshot=null,previewMode='confirm';
    const active=()=>location.pathname==='/confirmation-workbench';const role='ROLE::DATA_STEWARD',actor='public-demo-owner';const key=prefix=>prefix+'-'+Date.now()+'-'+Math.floor(Math.random()*100000);
    const api=async(path,init={})=>{const response=await fetch(path,init),payload=await response.json();if(!response.ok)throw Object.assign(new Error(payload.message_zh||payload.reason_zh||'请求失败'),{payload,status:response.status});return payload;};
    const post=(path,body)=>api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const setFeedback=(message,state='')=>{feedback.textContent=message;if(state)feedback.dataset.state=state;else delete feedback.dataset.state;};
    const tag=(value,kind,valueKey='')=>{const node=document.createElement('span');node.className='cw-tag';node.textContent=value;if(valueKey)node.dataset[kind]=valueKey;return node;};
    const fillDl=(root,rows)=>{root.replaceChildren();rows.forEach(row=>{const wrap=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=row.label_zh;dd.textContent=row.value_zh;wrap.append(dt,dd);root.append(wrap);});};
    const renderList=payload=>{listSnapshot=payload;const root=document.querySelector('#cw-list');root.replaceChildren();payload.issues.forEach(row=>{const button=document.createElement('button');button.type='button';button.className='cw-issue';button.dataset.issueId=row.issue_id;const head=document.createElement('div');head.className='cw-issue-head';const title=document.createElement('strong');title.textContent=row.title_zh;const tags=document.createElement('span');tags.className='cw-tags';tags.append(tag(row.impact,'impact',row.impact),tag(row.status==='OPEN'?'待处理':'已处理','status',row.status));head.append(title,tags);const meta=document.createElement('p');meta.textContent=row.source_label_zh+' · '+row.owner_label_zh+' · '+({TODAY:'今天',THREE_DAYS:'三天内',THIS_WEEK:'本周',WHEN_CONVENIENT:'可安排'}[row.urgency]||row.urgency);button.append(head,meta);button.addEventListener('click',()=>openIssue(row.issue_id));root.append(button);});if(!payload.issues.length){const empty=document.createElement('p');empty.textContent='当前筛选下没有需要处理的事项。';root.append(empty);}document.querySelector('#cw-list-count').textContent=payload.issue_count+' 项';document.querySelector('#cw-open-count').textContent=String(payload.issues.filter(row=>row.status==='OPEN').length);document.querySelector('#cw-highest-impact').textContent=payload.issues[0]?.impact||'无';};
    const renderDetail=payload=>{detailSnapshot=payload;document.querySelector('#cw-detail-card').hidden=false;document.querySelector('#cw-detail-title').textContent=payload.title_zh;document.querySelector('#cw-detail-owner').textContent=payload.source_label_zh+' · '+payload.owner_label_zh;const badges=document.querySelector('#cw-detail-badges');badges.replaceChildren(tag(payload.impact,'impact',payload.impact),tag(payload.status==='OPEN'?'待处理':'已处理','status',payload.status));fillDl(document.querySelector('#cw-current-data'),payload.current_data);fillDl(document.querySelector('#cw-reference-data'),payload.reference_data);document.querySelector('#cw-business-explanation').textContent=payload.business_explanation_zh;document.querySelector('#cw-impact-copy').textContent=payload.impact_zh;const fieldset=document.querySelector('#cw-actions');fieldset.replaceChildren();const legend=document.createElement('legend');legend.textContent='建议处理方式';fieldset.append(legend);payload.suggested_actions.forEach((row,index)=>{const label=document.createElement('label');label.className='cw-action-option';const input=document.createElement('input'),copy=document.createElement('span'),strong=document.createElement('strong'),small=document.createElement('small');input.type='radio';input.name='cw-action';input.value=row.action_id;input.checked=index===0;strong.textContent=row.label_zh+(row.high_impact?' · 高影响':'');small.textContent=row.description_zh;copy.append(strong,small);label.append(input,copy);fieldset.append(label);});document.querySelector('#cw-preview').disabled=payload.status!=='OPEN';const tech=Object.entries(payload.technical_details).map(([label,value])=>({label_zh:label,value_zh:Array.isArray(value)?value.join('、'):String(value)}));fillDl(document.querySelector('#cw-technical-data'),tech);document.querySelector('#cw-technical').open=false;document.querySelector('#cw-preview-card').hidden=true;};
    const renderPreview=(payload,mode)=>{previewSnapshot=payload;previewMode=mode;document.querySelector('#cw-preview-card').hidden=false;document.querySelector('#cw-preview-title').textContent=mode==='undo'?'撤销前影响预览':'确认前影响预览';document.querySelector('#cw-preview-risk').textContent=payload.high_impact?'高影响，必须明确确认':'普通影响';fillDl(document.querySelector('#cw-preview-data'),[{label_zh:'处理方式',value_zh:payload.action_label_zh},{label_zh:'处理前',value_zh:payload.before_status},{label_zh:'处理后',value_zh:payload.after_status}]);document.querySelector('#cw-preview-impact').textContent=payload.business_impact_zh;document.querySelector('#cw-confirm').textContent=mode==='undo'?'确认撤销':'确认处理';document.querySelector('#cw-preview-card').scrollIntoView({block:'nearest'});};
    const renderHistory=payload=>{historySnapshot=payload;const body=document.querySelector('#cw-history');body.replaceChildren();payload.events.forEach(row=>{const tr=document.createElement('tr');[row.sequence,row.issue_id,row.action_label_zh,row.actor_id,row.active?'当前有效':row.event_type==='ACTION_UNDONE'?'撤销记录':'历史'].forEach(value=>{const td=document.createElement('td');td.textContent=String(value);tr.append(td);});const action=document.createElement('td');if(row.active){const button=document.createElement('button');button.type='button';button.textContent='先看撤销影响';button.addEventListener('click',()=>undoPreview(row.event_id));action.append(button);}tr.append(action);body.append(tr);});document.querySelector('#cw-history-count').textContent=String(payload.event_count);document.querySelector('#cw-history-label').textContent=payload.event_count+' 条';};
    const loadList=async()=>{const include=document.querySelector('#cw-include-resolved').checked;const payload=await api('/api/confirmation/issues?include_resolved='+(include?'true':'false'));renderList(payload);return payload;};const loadHistory=async()=>{const payload=await api('/api/confirmation/history');renderHistory(payload);return payload;};
    const openIssue=async issueId=>{try{const payload=await api('/api/confirmation/issues/'+issueId);renderDetail(payload);setFeedback('已打开问题详情。技术依据默认收起，请先看业务说明和影响。');return payload;}catch(error){setFeedback(error.message,'error');return null;}};
    const preview=async()=>{if(!detailSnapshot)return null;const selected=document.querySelector('input[name="cw-action"]:checked');if(!selected){setFeedback('请选择处理方式。','error');return null;}try{const payload=await post('/api/confirmation/issues/'+detailSnapshot.issue_id+'/preview',{action_id:selected.value,actor_role:role});renderPreview(payload,'confirm');setFeedback('影响预览已生成；请再次核对后确认。');return payload;}catch(error){setFeedback(error.message,'error');return null;}};
    const confirm=async()=>{if(!previewSnapshot)return null;const reason=document.querySelector('#cw-reason').value.trim();if(!reason){setFeedback('请填写处理理由。','error');return null;}try{let payload;if(previewMode==='undo'){payload=await post('/api/confirmation/events/'+previewSnapshot.binding.target_event_id+'/undo',{actor_id:actor,actor_role:role,reason_zh:reason,preview_id:previewSnapshot.preview_id,preview_token:previewSnapshot.preview_token,idempotency_key:key('ui-undo')});}else{payload=await post('/api/confirmation/issues/'+previewSnapshot.binding.issue_id+'/confirm',{action_id:previewSnapshot.binding.action_id,actor_id:actor,actor_role:role,reason_zh:reason,preview_id:previewSnapshot.preview_id,preview_token:previewSnapshot.preview_token,idempotency_key:key('ui-confirm')});}document.querySelector('#cw-preview-card').hidden=true;previewSnapshot=null;await Promise.all([loadList(),loadHistory()]);renderDetail(payload.detail);setFeedback(previewMode==='undo'?'已撤销；旧记录保留，问题重新进入待处理列表。':'处理已登记；原始值未修改，可从历史中撤销。','success');return payload;}catch(error){setFeedback(error.message,'error');return null;}};
    const undoPreview=async eventId=>{try{const payload=await post('/api/confirmation/events/'+eventId+'/undo-preview',{actor_role:role});renderPreview(payload,'undo');document.querySelector('#cw-reason').value='复核后撤销本次处理并恢复待处理状态';setFeedback('撤销影响已生成；确认后会追加记录，不会删除旧记录。');return payload;}catch(error){setFeedback(error.message,'error');return null;}};
    const start=async()=>{if(!active()){view.hidden=true;delete document.body.dataset.confirmationActive;return;}view.hidden=false;document.body.dataset.confirmationActive='true';try{await Promise.all([loadList(),loadHistory()]);setFeedback('只显示需要你处理的业务问题；治理日志不会混入列表。');}catch(error){setFeedback(error.message,'error');}};
    document.querySelector('#cw-refresh').addEventListener('click',()=>Promise.all([loadList(),loadHistory()]));document.querySelector('#cw-include-resolved').addEventListener('change',loadList);document.querySelector('#cw-close-detail').addEventListener('click',()=>{document.querySelector('#cw-detail-card').hidden=true;document.querySelector('#cw-preview-card').hidden=true;});document.querySelector('#cw-preview').addEventListener('click',preview);document.querySelector('#cw-confirm').addEventListener('click',confirm);document.querySelector('#cw-preview-cancel').addEventListener('click',()=>{document.querySelector('#cw-preview-card').hidden=true;previewSnapshot=null;});window.addEventListener('popstate',start);document.addEventListener('click',event=>{if(event.target.closest('a[data-route]'))setTimeout(start,0);});window.KMFA_CONFIRMATION_TEST={start,loadList,loadHistory,openIssue,preview,confirm,undoPreview,snapshot:()=>({list:listSnapshot,detail:detailSnapshot,history:historySnapshot,preview:previewSnapshot})};start();
  })();
  </script>'''
    marker = '<section id="data-update-view" class="du-view" aria-labelledby="du-title" hidden>'
    if marker not in html:
        raise RuntimeError("S20-P1 insertion point drifted")
    html = html.replace(marker, view + marker, 1)
    html = html.replace(
        '<a class="du-home" href="/overview" data-route="/overview">返回经营首页</a>',
        '<div class="du-actions"><a class="du-home" href="/confirmation-workbench" data-route="/confirmation-workbench">打开人工确认工作台</a><a class="du-home" href="/overview" data-route="/overview">返回经营首页</a></div>',
        1,
    )
    html = html.replace("  </style>", css + "  </style>", 1)
    html = html.replace("</body>", script + "</body>", 1)
    html = html.replace("<title>KMFA 数据更新 · 经营工作台</title>", "<title>KMFA 人工确认工作台</title>")
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class ConfirmationHandler(base_runtime.DataUpdateHandler):
    server_version = "KMFAConfirmationWorkbench/1.5"

    @property
    def workbench(self) -> kernel.ConfirmationWorkbench:
        return self.server.confirmation_workbench  # type: ignore[attr-defined,no-any-return]

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        try:
            if parsed.path == "/api/confirmation/issues":
                include = parse_qs(parsed.query).get("include_resolved", ["false"])[0].lower() == "true"
                self._send_json(HTTPStatus.OK, self.workbench.list_issues(include_resolved=include))
                return
            if parsed.path == "/api/confirmation/history":
                self._send_json(HTTPStatus.OK, self.workbench.history())
                return
            match = _ISSUE_ROUTE.fullmatch(parsed.path)
            if match:
                self._send_json(HTTPStatus.OK, self.workbench.detail(match.group(1)))
                return
            if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico" or parsed.path.startswith("/reports/"):
                super().do_GET()
                return
            self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")
        except kernel.ConfirmationError as error:
            self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        try:
            match = _ISSUE_ACTION_ROUTE.fullmatch(parsed.path)
            if match:
                issue_id, action = match.groups()
                body = self._json_body()
                if action == "preview":
                    value = self.workbench.preview(issue_id, str(body.get("action_id", "")), actor_role=str(body.get("actor_role", "")))
                else:
                    value = self.workbench.confirm(
                        issue_id, str(body.get("action_id", "")), actor_id=str(body.get("actor_id", "")),
                        actor_role=str(body.get("actor_role", "")), reason_zh=str(body.get("reason_zh", "")),
                        preview_id=str(body.get("preview_id", "")), preview_token=str(body.get("preview_token", "")),
                        idempotency_key=str(body.get("idempotency_key", "")),
                    )
                self._send_json(HTTPStatus.OK, value)
                return
            match = _EVENT_ACTION_ROUTE.fullmatch(parsed.path)
            if match:
                event_id, action = match.groups()
                body = self._json_body()
                if action == "undo-preview":
                    value = self.workbench.undo_preview(event_id, actor_role=str(body.get("actor_role", "")))
                else:
                    value = self.workbench.undo(
                        event_id, actor_id=str(body.get("actor_id", "")), actor_role=str(body.get("actor_role", "")),
                        reason_zh=str(body.get("reason_zh", "")), preview_id=str(body.get("preview_id", "")),
                        preview_token=str(body.get("preview_token", "")), idempotency_key=str(body.get("idempotency_key", "")),
                    )
                self._send_json(HTTPStatus.OK, value)
                return
            super().do_POST()
        except kernel.ConfirmationError as error:
            self._send_json(error.status, {"allowed": False, "code": error.code, "message_zh": error.message_zh})


class ConfirmationServer(base_runtime.DataUpdateServer):
    confirmation_workbench: kernel.ConfirmationWorkbench


def start_server(
    host: str = "127.0.0.1", port: int = 0, *, event_path: Path | str = workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH,
    data_root: Path | str = data_update_kernel.DEFAULT_RUNTIME_ROOT, confirmation_event_path: Path | str = kernel.DEFAULT_EVENT_PATH,
) -> tuple[ConfirmationServer, threading.Thread, str]:
    event_file = Path(event_path)
    server = ConfirmationServer((host, port), ConfirmationHandler)
    server.journal = workflow_kernel.EventJournal(event_file)
    server.policy_journal = policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = reporting_kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    server.data_update_store = data_update_kernel.DataUpdateStore(data_root)
    server.confirmation_workbench = kernel.ConfirmationWorkbench(confirmation_event_path)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s20p2-confirmation", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S20-P2 人工确认工作台")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--event-path", default=str(workflow_kernel.DEFAULT_RUNTIME_EVENT_PATH))
    parser.add_argument("--data-root", default=str(data_update_kernel.DEFAULT_RUNTIME_ROOT))
    parser.add_argument("--confirmation-event-path", default=str(kernel.DEFAULT_EVENT_PATH))
    args = parser.parse_args()
    event_file = Path(args.event_path)
    server = ConfirmationServer((args.host, args.port), ConfirmationHandler)
    server.journal = workflow_kernel.EventJournal(event_file)
    server.policy_journal = policy_kernel.PolicyTaskJournal(event_file.with_name("policy_tasks.jsonl"))
    server.review_journal = reporting_kernel.ProfessionalReviewJournal(event_file.with_name("professional_reviews.jsonl"))
    server.data_update_store = data_update_kernel.DataUpdateStore(args.data_root)
    server.confirmation_workbench = kernel.ConfirmationWorkbench(args.confirmation_event_path)
    print(f"KMFA 人工确认工作台：http://{args.host}:{server.server_address[1]}/confirmation-workbench", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
