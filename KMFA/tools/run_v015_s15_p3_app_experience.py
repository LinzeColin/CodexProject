#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S15-P3 应用基础体验演示。"""

from __future__ import annotations

import argparse
import json
import threading
from http import HTTPStatus
from typing import Any, Mapping
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s15_p2_identity_roles as p2_runtime
from KMFA.tools import v015_s15_p1_app_shell as app_shell
from KMFA.tools import v015_s15_p2_identity_roles as identity_roles
from KMFA.tools import v015_s15_p3_app_experience as kernel


def _json_for_html(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_html() -> str:
    html = p2_runtime.render_html()
    utility_bar = '''
  <section class="quick-shell" aria-label="快速工作入口">
    <div class="quick-bar">
      <form id="global-search-form" class="global-search" role="search">
        <label class="visually-hidden" for="global-search">全局搜索</label>
        <input id="global-search" name="query" type="search" autocomplete="off" maxlength="60" placeholder="搜索项目、客户、报告或待办">
        <label class="visually-hidden" for="search-kind">结果类型</label>
        <select id="search-kind" name="kind"><option value="ALL">全部类型</option><option value="PROJECT">项目</option><option value="CUSTOMER">客户</option><option value="REPORT">报告</option><option value="TODO">待办</option></select>
        <button class="primary-button" type="submit">搜索</button>
      </form>
      <div class="quick-actions" aria-label="个人工作入口">
        <button type="button" data-open-experience="search">最近访问</button>
        <button type="button" data-open-experience="notifications">通知与待办 <span id="notification-count" class="count-chip">0</span></button>
        <button type="button" data-open-experience="preferences">偏好设置</button>
      </div>
    </div>
  </section>'''
    experience_workspace = '''
    <section id="experience-workspace" class="experience-workspace" data-columns="source updated_at status" aria-labelledby="experience-title">
      <header class="experience-head"><div><h2 id="experience-title">快速找到并继续工作</h2><p>搜索结果、提醒和偏好都会按当前用户、角色与公司重新核对。</p></div><span class="shortcut-copy">⌘ / Ctrl + K 搜索</span></header>
      <div class="experience-tabs" role="tablist" aria-label="应用基础体验">
        <button id="tab-search" type="button" role="tab" aria-selected="true" aria-controls="panel-search" data-experience-tab="search">搜索与最近</button>
        <button id="tab-notifications" type="button" role="tab" aria-selected="false" aria-controls="panel-notifications" data-experience-tab="notifications" tabindex="-1">通知与待办</button>
        <button id="tab-preferences" type="button" role="tab" aria-selected="false" aria-controls="panel-preferences" data-experience-tab="preferences" tabindex="-1">偏好设置</button>
      </div>
      <div id="experience-feedback" class="experience-feedback" role="status" aria-live="polite">输入关键词，或从最近访问继续。</div>
      <section id="panel-search" class="experience-panel" role="tabpanel" aria-labelledby="tab-search">
        <div class="search-layout">
          <div class="result-area"><h3>搜索结果</h3><div class="result-table-wrap"><table class="result-table"><thead><tr><th>结果</th><th data-column="source">来源</th><th data-column="updated_at">更新时间</th><th data-column="status">状态</th><th>操作</th></tr></thead><tbody id="search-results"><tr><td colspan="5" class="empty-cell">输入名称或事项，例如“报告”“回款”“项目”。</td></tr></tbody></table></div></div>
          <aside class="recent-area"><h3>最近访问</h3><ol id="recent-list" class="recent-list"><li class="empty-copy">打开搜索结果后会显示在这里。</li></ol></aside>
        </div>
      </section>
      <section id="panel-notifications" class="experience-panel" role="tabpanel" aria-labelledby="tab-notifications" hidden>
        <div class="panel-heading"><div><h3>通知与待办</h3><p>只显示当前身份可以处理的公开演示事项。</p></div><button id="refresh-notifications" class="secondary-button" type="button">重新核对</button></div>
        <div id="notification-list" class="notification-list"><p class="empty-copy">正在核对待办…</p></div>
      </section>
      <section id="panel-preferences" class="experience-panel" role="tabpanel" aria-labelledby="tab-preferences" hidden>
        <form id="preference-form" class="preference-form">
          <fieldset><legend>常用查看范围</legend><div class="preference-grid"><label><span>常用公司</span><select id="preference-company" name="company"></select></label><label><span>常用期间</span><select id="preference-period" name="period"></select></label><label><span>显示密度</span><select id="preference-density" name="density"><option value="compact">紧凑</option><option value="comfortable">宽松</option></select></label></div></fieldset>
          <fieldset><legend>搜索结果显示列</legend><div id="preference-columns" class="column-options"><label><input type="checkbox" value="source" checked> 来源</label><label><input type="checkbox" value="updated_at" checked> 更新时间</label><label><input type="checkbox" value="status" checked> 状态</label></div></fieldset>
          <p class="preference-note">这些设置只影响当前用户的查看方式，不会修改经营事实，也不会影响其他人。</p>
          <div class="preference-actions"><button class="primary-button" type="submit">保存偏好</button><button id="apply-preferred-context" class="secondary-button" type="button" disabled>应用常用范围</button></div>
        </form>
      </section>
    </section>'''
    extra_css = '''
    .visually-hidden { position:absolute!important; width:1px!important; height:1px!important; padding:0!important; margin:-1px!important; overflow:hidden!important; clip:rect(0,0,0,0)!important; white-space:nowrap!important; border:0!important; }
    .quick-shell { border-bottom:1px solid var(--line); background:#f7f9fa; }
    .quick-bar { width:min(1240px,100%); margin:auto; padding:10px 24px; display:flex; align-items:center; gap:14px; }
    .global-search { flex:1 1 620px; display:grid; grid-template-columns:minmax(220px,1fr) 130px auto; gap:8px; }
    .global-search input,.global-search select { min-height:40px; }
    .quick-actions { flex:none; display:flex; gap:7px; }
    .quick-actions button { min-height:40px; padding:8px 11px; border:1px solid #a9bac7; border-radius:6px; background:#fff; color:var(--blue-dark); font:inherit; cursor:pointer; }
    .quick-actions button:hover { border-color:var(--blue); background:#edf6fb; }
    .count-chip { display:inline-flex; min-width:20px; height:20px; margin-left:4px; align-items:center; justify-content:center; border-radius:999px; background:#edf6fb; color:var(--blue-dark); font-size:12px; font-weight:700; }
    .experience-workspace { margin-bottom:20px; padding:18px 20px; border:1px solid var(--line); border-radius:8px; background:#fff; }
    .experience-head { display:flex; justify-content:space-between; gap:18px; align-items:flex-start; }
    .experience-head h2 { margin:0; color:var(--navy); font-size:18px; }
    .experience-head p { margin:4px 0 0; color:var(--muted); font-size:13px; }
    .shortcut-copy { flex:none; color:var(--muted); font-size:12px; }
    .experience-tabs { display:flex; gap:4px; margin:15px 0 0; padding-bottom:8px; border-bottom:1px solid var(--line); overflow:auto; }
    .experience-tabs button { min-height:36px; padding:7px 11px; border:1px solid transparent; border-radius:6px; background:transparent; color:#42596a; font:inherit; font-weight:650; white-space:nowrap; cursor:pointer; }
    .experience-tabs button[aria-selected="true"] { border-color:#9cb7c9; background:#edf6fb; color:var(--blue-dark); }
    .experience-feedback { margin:12px 0; padding:8px 10px; border:1px solid #c9d8e2; border-radius:6px; background:#f3f8fb; color:#29475d; font-size:13px; }
    .experience-feedback[data-state="blocked"] { border-color:#d7a6a6; background:#fff8f7; color:#7f2929; }
    .experience-feedback[data-state="saved"] { border-color:#9bc8b1; background:#f5fbf7; color:#1e6547; }
    .experience-panel h3 { margin:0 0 10px; color:var(--navy); font-size:15px; }
    .search-layout { display:grid; grid-template-columns:minmax(0,1.55fr) minmax(240px,.55fr); gap:20px; }
    .result-table-wrap { overflow:auto; border:1px solid var(--line); border-radius:6px; }
    .result-table { width:100%; border-collapse:collapse; font-size:13px; }
    .result-table th,.result-table td { padding:9px 10px; border-bottom:1px solid #e4eaee; text-align:left; vertical-align:top; }
    .result-table td:first-child { width:auto; color:inherit; font-weight:400; }
    .result-table th { background:#f3f6f8; color:#496071; white-space:nowrap; }
    .result-table tr:last-child td { border-bottom:0; }
    .result-title { display:block; color:var(--navy); font-weight:700; }
    .result-summary { display:block; margin-top:3px; color:var(--muted); line-height:1.45; }
    .result-kind { display:inline-block; margin-right:6px; color:var(--blue-dark); font-size:12px; font-weight:700; }
    .result-action { display:inline-flex; min-height:32px; align-items:center; padding:5px 9px; border:1px solid #a9bac7; border-radius:6px; color:var(--blue-dark); text-decoration:none; white-space:nowrap; }
    .result-action:hover { border-color:var(--blue); background:#edf6fb; }
    .empty-cell,.empty-copy { color:var(--muted); line-height:1.55; }
    .recent-area { border-left:1px solid var(--line); padding-left:18px; }
    .recent-list { margin:0; padding:0; list-style:none; }
    .recent-list li { padding:8px 0; border-top:1px solid #e4eaee; }
    .recent-list li:first-child { border-top:0; padding-top:0; }
    .recent-list a { color:var(--blue-dark); font-weight:650; text-decoration:none; }
    .recent-list small { display:block; margin-top:3px; color:var(--muted); }
    .panel-heading { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; }
    .panel-heading p { margin:-5px 0 10px; color:var(--muted); font-size:13px; }
    .notification-list { border-top:1px solid var(--line); }
    .notification-row { display:grid; grid-template-columns:100px minmax(0,1fr) 100px auto; gap:12px; align-items:center; padding:12px 2px; border-bottom:1px solid #e4eaee; }
    .notice-category { color:var(--blue-dark); font-size:12px; font-weight:700; }
    .notice-copy strong { display:block; color:var(--text); }
    .notice-copy span { display:block; margin-top:3px; color:var(--muted); font-size:13px; }
    .notice-status { color:#42596a; font-size:13px; }
    .preference-form { max-width:920px; }
    .preference-form fieldset { margin:0 0 16px; padding:0; border:0; }
    .preference-form legend { margin-bottom:9px; color:var(--navy); font-size:15px; font-weight:700; }
    .preference-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
    .preference-grid label span { display:block; margin-bottom:5px; color:var(--muted); font-size:12px; font-weight:650; }
    .column-options { display:flex; flex-wrap:wrap; gap:8px 18px; }
    .column-options label { display:flex; align-items:center; gap:7px; color:#42596a; }
    .column-options input { width:auto; min-height:auto; }
    .preference-note { max-width:70ch; margin:0 0 14px; color:var(--muted); font-size:13px; }
    .preference-actions { display:flex; gap:8px; }
    .preference-actions button:disabled { opacity:.58; cursor:not-allowed; }
    .experience-workspace:not([data-columns~="source"]) [data-column="source"],.experience-workspace:not([data-columns~="updated_at"]) [data-column="updated_at"],.experience-workspace:not([data-columns~="status"]) [data-column="status"] { display:none; }
    body[data-density="comfortable"] .result-table th,body[data-density="comfortable"] .result-table td { padding-top:13px; padding-bottom:13px; }
    @media (max-width:1040px) { .quick-bar { align-items:stretch; flex-direction:column; } .global-search { flex:auto; } .quick-actions { align-self:flex-start; } }
    @media (max-width:760px) { .quick-bar { padding-left:16px; padding-right:16px; } .global-search { grid-template-columns:minmax(0,1fr) auto; } .global-search select { grid-column:1/-1; grid-row:2; } .search-layout { grid-template-columns:1fr; } .recent-area { border-left:0; border-top:1px solid var(--line); padding:14px 0 0; } .notification-row { grid-template-columns:88px minmax(0,1fr); } .notification-row .notice-status,.notification-row .result-action { grid-column:2; justify-self:start; } .preference-grid { grid-template-columns:1fr; } .experience-head p,.shortcut-copy,.notice-category,.notice-copy span,.notice-status,.preference-grid label span,.preference-note,.result-table,.result-kind,.identity-heading span,.identity-bar label span,.operation-reason span,.approval-copy,.role-chip { font-size:14px; } }
    @media (pointer:coarse) { .global-search input,.global-search select,.global-search button,.quick-actions button,.experience-tabs button,.result-action,.preference-actions button,.identity-bar input,.identity-bar select,#switch-role,.operation-actions button { min-height:44px; } }
    @media (max-width:430px) { .quick-actions { width:100%; display:grid; grid-template-columns:1fr; } .experience-workspace { padding:16px; } .experience-head { display:block; } .shortcut-copy { display:block; margin-top:6px; } .preference-actions { flex-direction:column; } }
    '''
    experience_script = f'''
  <script>
  (() => {{
    'use strict';
    const COMPANY_OPTIONS={_json_for_html(app_shell.CONTEXT_OPTIONS['company'])};
    const PERIOD_OPTIONS={_json_for_html(app_shell.CONTEXT_OPTIONS['period'])};
    const workspace=document.querySelector('#experience-workspace'); const feedback=document.querySelector('#experience-feedback'); const searchInput=document.querySelector('#global-search'); const kindSelect=document.querySelector('#search-kind'); const searchBody=document.querySelector('#search-results'); const recentList=document.querySelector('#recent-list'); const noticeList=document.querySelector('#notification-list'); const applyPreferredButton=document.querySelector('#apply-preferred-context');
    let currentPreferences=null; let lastIdentityKey=''; let preferenceFormDirty=false; const requestSequences={{search:0,recent:0,notifications:0,preferences:0,save:0}};
    const identity=()=>window.KMFA_ROLE_TEST.identity();
    const queryIdentity=()=>{{ const value=identity(); return {{actor_user_id:value.user_id,target_user_id:value.user_id,user_id:value.user_id,role_id:value.role_id,company_id:value.company_id,current_company_id:value.company_id}}; }};
    const identityKey=()=>{{ const who=queryIdentity(); return [who.user_id,who.role_id,who.company_id].join('|'); }};
    const beginRequest=channel=>({{channel,sequence:++requestSequences[channel],identity_key:identityKey()}});
    const requestIsCurrent=token=>token.sequence===requestSequences[token.channel]&&token.identity_key===identityKey();
    const setFeedback=(message,state='')=>{{ feedback.textContent=message; if(state)feedback.dataset.state=state; else delete feedback.dataset.state; }};
    const requestJson=async(path,options={{}})=>{{ try {{ const response=await fetch(path,options); const data=await response.json(); return {{ok:response.ok,status:response.status,data}}; }} catch (_) {{ return {{ok:false,status:0,data:{{allowed:false,reason_zh:'暂时无法读取，请重新尝试。'}}}}; }} }};
    const openPanel=(name,focusTab=false)=>{{ document.querySelectorAll('[data-experience-tab]').forEach(tab=>{{ const active=tab.dataset.experienceTab===name; tab.setAttribute('aria-selected',String(active)); tab.tabIndex=active?0:-1; if(active&&focusTab)tab.focus(); }}); document.querySelectorAll('.experience-panel').forEach(panel=>panel.hidden=panel.id!=='panel-'+name); if(name==='notifications')loadNotifications(); if(name==='preferences')loadPreferences(); }};
    const emptyRow=message=>{{ searchBody.replaceChildren(); const tr=document.createElement('tr'); const td=document.createElement('td'); td.colSpan=5; td.className='empty-cell'; td.textContent=message; tr.append(td); searchBody.append(tr); }};
    const invalidateExperience=()=>{{ Object.keys(requestSequences).forEach(channel=>requestSequences[channel]++); currentPreferences=null; applyPreferredButton.disabled=true; emptyRow('正在按新的用户、角色和公司重新核对…'); recentList.replaceChildren(); const recent=document.createElement('li'); recent.className='empty-copy'; recent.textContent='正在重新核对最近访问…'; recentList.append(recent); noticeList.replaceChildren(); const notice=document.createElement('p'); notice.className='empty-copy'; notice.textContent='正在重新核对通知与待办…'; noticeList.append(notice); }};
    const recordRecent=async(itemId)=>{{ const who=queryIdentity(); await requestJson('/api/recent',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{user_id:who.user_id,role_id:who.role_id,company_id:who.company_id,item_id:itemId}})}}); await loadRecent(); }};
    const renderSearch=payload=>{{ searchBody.replaceChildren(); if(!payload.allowed){{ emptyRow(payload.reason_zh||'当前身份不能搜索。'); setFeedback(payload.reason_zh||'当前身份不能搜索。','blocked'); return; }} if(!payload.results.length){{ emptyRow(payload.query?'没有找到当前身份可以查看的结果。':'输入名称或事项，例如“报告”“回款”“项目”。'); setFeedback(payload.query?'没有可查看的匹配结果。':'输入关键词，或从最近访问继续。'); return; }} payload.results.forEach(item=>{{ const tr=document.createElement('tr'); const main=document.createElement('td'); const title=document.createElement('span'); title.className='result-title'; title.textContent=item.title_zh; const summary=document.createElement('span'); summary.className='result-summary'; const kind=document.createElement('span'); kind.className='result-kind'; kind.textContent=item.kind_zh; summary.append(kind,document.createTextNode(item.summary_zh)); main.append(title,summary); const source=document.createElement('td'); source.dataset.column='source'; source.textContent=item.source_zh; const updated=document.createElement('td'); updated.dataset.column='updated_at'; updated.textContent=item.updated_at_zh; const status=document.createElement('td'); status.dataset.column='status'; status.textContent='● '+item.status_zh; const action=document.createElement('td'); const link=document.createElement('a'); link.className='result-action'; link.href=item.route; link.dataset.route=item.route; link.dataset.recentItem=item.item_id; link.textContent=item.action_zh; action.append(link); tr.append(main,source,updated,status,action); searchBody.append(tr); }}); setFeedback('找到 '+payload.result_count+' 项当前身份可以查看的结果。'); }};
    const search=async(query=searchInput.value,kind=kindSelect.value)=>{{ openPanel('search'); const token=beginRequest('search'); const who=queryIdentity(); const params=new URLSearchParams({{user_id:who.user_id,role_id:who.role_id,company_id:who.company_id,query,kind}}); const result=await requestJson('/api/search?'+params); if(!requestIsCurrent(token))return {{...result,stale_response_ignored:true}}; renderSearch(result.data); return result; }};
    const loadRecent=async()=>{{ const token=beginRequest('recent'); const who=queryIdentity(); const params=new URLSearchParams({{user_id:who.user_id,role_id:who.role_id,company_id:who.company_id}}); const result=await requestJson('/api/recent?'+params); if(!requestIsCurrent(token))return {{...result,stale_response_ignored:true}}; recentList.replaceChildren(); const items=result.data.items||[]; if(!result.ok||!items.length){{ const li=document.createElement('li'); li.className='empty-copy'; li.textContent=result.ok?'打开搜索结果后会显示在这里。':(result.data.reason_zh||'最近访问暂时不可用。'); recentList.append(li); return result; }} items.forEach(item=>{{ const li=document.createElement('li'); const link=document.createElement('a'); link.href=item.route; link.dataset.route=item.route; link.dataset.recentItem=item.item_id; link.textContent=item.title_zh; const small=document.createElement('small'); small.textContent=item.kind_zh+' · '+item.source_zh; li.append(link,small); recentList.append(li); }}); return result; }};
    const loadNotifications=async()=>{{ const token=beginRequest('notifications'); const who=queryIdentity(); const params=new URLSearchParams({{user_id:who.user_id,role_id:who.role_id,company_id:who.company_id}}); const result=await requestJson('/api/notifications?'+params); if(!requestIsCurrent(token))return {{...result,stale_response_ignored:true}}; noticeList.replaceChildren(); const items=result.data.items||[]; document.querySelector('#notification-count').textContent=String(items.length); if(!result.ok||!items.length){{ const p=document.createElement('p'); p.className='empty-copy'; p.textContent=result.ok?'当前没有需要处理的提醒。':(result.data.reason_zh||'提醒暂时不可用。'); noticeList.append(p); return result; }} items.forEach(item=>{{ const row=document.createElement('div'); row.className='notification-row'; const category=document.createElement('span'); category.className='notice-category'; category.textContent=item.category_zh; const copy=document.createElement('div'); copy.className='notice-copy'; const strong=document.createElement('strong'); strong.textContent=item.title_zh; const detail=document.createElement('span'); detail.textContent=item.summary_zh; copy.append(strong,detail); const status=document.createElement('span'); status.className='notice-status'; status.textContent='● '+item.status_zh; const link=document.createElement('a'); link.className='result-action'; link.href=item.route; link.dataset.route=item.route; link.textContent=item.action_zh; row.append(category,copy,status,link); noticeList.append(row); }}); if(document.querySelector('#tab-notifications').getAttribute('aria-selected')==='true')setFeedback('已按当前身份核对 '+items.length+' 项通知和待办。'); return result; }};
    const setOptions=(select,options,selected)=>{{ select.replaceChildren(); options.forEach(item=>{{ const option=document.createElement('option'); option.value=item.value; option.textContent=item.label; select.append(option); }}); select.value=selected; }};
    const applyDisplayPreferences=prefs=>{{ currentPreferences=prefs; workspace.dataset.columns=(prefs.table_columns||[]).join(' '); document.body.dataset.density=prefs.density||'compact'; document.querySelectorAll('#preference-columns input').forEach(input=>input.checked=(prefs.table_columns||[]).includes(input.value)); }};
    const loadPreferences=async()=>{{ const token=beginRequest('preferences'); const who=queryIdentity(); const params=new URLSearchParams({{actor_user_id:who.user_id,target_user_id:who.user_id,role_id:who.role_id,current_company_id:who.company_id}}); const result=await requestJson('/api/preferences?'+params); if(!requestIsCurrent(token))return {{...result,stale_response_ignored:true}}; if(!result.ok){{ applyPreferredButton.disabled=true; setFeedback(result.data.reason_zh||'偏好暂时不可用。','blocked'); return result; }} if(preferenceFormDirty)return result; const prefs=result.data.preferences; setOptions(document.querySelector('#preference-company'),result.data.company_options,prefs.company); setOptions(document.querySelector('#preference-period'),result.data.period_options,prefs.period); document.querySelector('#preference-density').value=prefs.density; applyDisplayPreferences(prefs); applyPreferredButton.disabled=false; return result; }};
    const savePreferences=async()=>{{ const token=beginRequest('save'); const who=queryIdentity(); const preferences={{company:document.querySelector('#preference-company').value,period:document.querySelector('#preference-period').value,table_columns:[...document.querySelectorAll('#preference-columns input:checked')].map(input=>input.value),density:document.querySelector('#preference-density').value}}; const result=await requestJson('/api/preferences',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{actor_user_id:who.user_id,target_user_id:who.user_id,role_id:who.role_id,current_company_id:who.company_id,preferences}})}}); if(!requestIsCurrent(token))return {{...result,stale_response_ignored:true}}; if(result.ok){{ preferenceFormDirty=false; applyDisplayPreferences(result.data.preferences); applyPreferredButton.disabled=false; setFeedback('偏好已保存，只影响当前用户的查看方式。','saved'); }} else setFeedback(result.data.reason_zh||'偏好没有保存。','blocked'); return result; }};
    const applyPreferredContext=()=>{{ if(!currentPreferences)return; const company=document.querySelector('#context-company'); const period=document.querySelector('#context-period'); company.value=currentPreferences.company; company.dispatchEvent(new Event('change',{{bubbles:true}})); period.value=currentPreferences.period; period.dispatchEvent(new Event('change',{{bubbles:true}})); setFeedback('常用公司和期间已应用到当前查看范围。','saved'); }};
    const refreshForIdentity=async()=>{{ const key=identityKey(); if(key===lastIdentityKey)return; if(lastIdentityKey&&key!==lastIdentityKey)preferenceFormDirty=false; invalidateExperience(); lastIdentityKey=key; const work=[]; if(searchInput.value.trim())work.push(search()); else emptyRow('输入名称或事项，例如“报告”“回款”“项目”。'); work.push(loadRecent(),loadNotifications(),loadPreferences()); await Promise.all(work); }};
    document.querySelector('#global-search-form').addEventListener('submit',event=>{{ event.preventDefault(); search(); }});
    document.querySelectorAll('[data-open-experience]').forEach(button=>button.addEventListener('click',()=>{{ const name=button.dataset.openExperience; openPanel(name); document.querySelector('#experience-workspace').scrollIntoView({{block:'nearest'}}); }}));
    document.querySelectorAll('[data-experience-tab]').forEach(tab=>tab.addEventListener('click',()=>openPanel(tab.dataset.experienceTab,true)));
    document.querySelector('.experience-tabs').addEventListener('keydown',event=>{{ if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return; event.preventDefault(); const tabs=[...document.querySelectorAll('[data-experience-tab]')]; const current=tabs.indexOf(document.activeElement); let next=current<0?0:current; if(event.key==='Home')next=0; else if(event.key==='End')next=tabs.length-1; else next=(current+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length; openPanel(tabs[next].dataset.experienceTab,true); }});
    document.querySelector('#refresh-notifications').addEventListener('click',loadNotifications);
    document.querySelector('#preference-form').addEventListener('submit',event=>{{ event.preventDefault(); savePreferences(); }});
    document.querySelector('#preference-form').addEventListener('change',()=>{{ preferenceFormDirty=true; }});
    document.querySelector('#apply-preferred-context').addEventListener('click',applyPreferredContext);
    document.addEventListener('click',event=>{{ const link=event.target.closest('[data-recent-item]'); if(link)void recordRecent(link.dataset.recentItem); }},true);
    document.addEventListener('keydown',event=>{{ if((event.metaKey||event.ctrlKey)&&event.key.toLowerCase()==='k'){{ event.preventDefault(); openPanel('search'); searchInput.focus(); }} }});
    document.querySelector('#identity-user').addEventListener('change',()=>setTimeout(()=>{{ lastIdentityKey=''; refreshForIdentity(); }},0));
    document.querySelector('#context-company').addEventListener('change',()=>setTimeout(()=>{{ lastIdentityKey=''; refreshForIdentity(); }},0));
    new MutationObserver(()=>{{ lastIdentityKey=''; refreshForIdentity(); }}).observe(document.querySelector('#active-role-chip'),{{childList:true,subtree:true}});
    window.KMFA_EXPERIENCE_TEST={{search,loadRecent,loadNotifications,loadPreferences,savePreferences,recordRecent,openPanel,preferences:()=>currentPreferences,refreshForIdentity}};
    openPanel('search'); refreshForIdentity();
  }})();
  </script>
'''
    html = html.replace("<title>KMFA 身份与角色 · 经营工作台</title>", "<title>KMFA 快速工作 · 经营工作台</title>")
    html = html.replace("  </style>", extra_css + "  </style>", 1)
    html = html.replace("  </section>\n  <main id=\"main-content\"", "  </section>" + utility_bar + "\n  <main id=\"main-content\"", 1)
    status = '<div id="context-status" class="status-line" role="status" aria-live="polite"><span>正在准备演示内容…</span></div>'
    html = html.replace(status, status + experience_workspace, 1)
    html = html.replace("</body>", experience_script + "</body>", 1)
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


class PublicExperienceStore:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.recent_by_user: dict[str, list[str]] = {}
        self.preferences_by_user: dict[str, dict[str, Any]] = {}
        self.preference_revision: dict[str, int] = {}

    def record_recent(self, value: Mapping[str, Any]) -> dict[str, Any]:
        with self.lock:
            decision = kernel.record_recent_decision(
                user_id=str(value.get("user_id", "")),
                role_id=str(value.get("role_id", "")),
                company_id=str(value.get("company_id", "")),
                item_id=str(value.get("item_id", "")),
            )
            if decision["allowed"]:
                user_id = decision["user_id"]
                items = self.recent_by_user.setdefault(user_id, [])
                item_id = str(decision["item_id"])
                if item_id in items:
                    items.remove(item_id)
                items.insert(0, item_id)
                del items[8:]
            return {"event": decision}

    def recent_snapshot(self, *, user_id: str, role_id: str, company_id: str) -> dict[str, Any]:
        with self.lock:
            return kernel.recent_snapshot(
                user_id=user_id,
                role_id=role_id,
                company_id=company_id,
                item_ids=list(self.recent_by_user.get(user_id, [])),
            )

    def preferences_snapshot(
        self, *, actor_user_id: str, target_user_id: str, role_id: str, current_company_id: str
    ) -> dict[str, Any]:
        with self.lock:
            decision = kernel.preference_read_decision(
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
                role_id=role_id,
                current_company_id=current_company_id,
            )
            if not decision["allowed"]:
                return decision
            user = identity_roles.PUBLIC_USERS[target_user_id]
            preferences = dict(self.preferences_by_user.get(target_user_id, kernel.default_preferences(target_user_id)))
            preferences["table_columns"] = list(preferences["table_columns"])
            company_labels = {item["value"]: item["label"] for item in app_shell.CONTEXT_OPTIONS["company"]}
            return {
                **decision,
                "schema_version": "kmfa.v015.s15p3.preference_response.v1",
                "preferences": preferences,
                "revision": self.preference_revision.get(target_user_id, 0),
                "company_options": [
                    {"value": company_id, "label": company_labels[company_id]} for company_id in user["company_ids"]
                ],
                "period_options": [dict(item) for item in app_shell.CONTEXT_OPTIONS["period"]],
                "table_column_options": dict(kernel.TABLE_COLUMN_OPTIONS),
                "density_options": dict(kernel.DENSITY_OPTIONS),
                "fact_layer_write_count": 0,
                "raw_write_count": 0,
            }

    def save_preferences(self, value: Mapping[str, Any]) -> dict[str, Any]:
        with self.lock:
            preferences = value.get("preferences")
            decision = kernel.preference_save_decision(
                actor_user_id=str(value.get("actor_user_id", "")),
                target_user_id=str(value.get("target_user_id", "")),
                role_id=str(value.get("role_id", "")),
                current_company_id=str(value.get("current_company_id", "")),
                preferences=preferences if isinstance(preferences, Mapping) else {},
            )
            if decision["allowed"]:
                user_id = decision["target_user_id"]
                saved = dict(decision["preferences"])
                saved["table_columns"] = list(saved["table_columns"])
                self.preferences_by_user[user_id] = saved
                self.preference_revision[user_id] = self.preference_revision.get(user_id, 0) + 1
                return {**decision, "preferences": saved, "revision": self.preference_revision[user_id]}
            return decision


class AppExperienceHandler(p2_runtime.IdentityRoleHandler):
    server_version = "KMFAAppExperience/1.5"

    @property
    def experience_store(self) -> PublicExperienceStore:
        return self.server.experience_store  # type: ignore[attr-defined,no-any-return]

    def _read_json_object(self) -> dict[str, Any] | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > 16_384:
            return None
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        query = parse_qs(parsed.query)
        if parsed.path == "/api/search":
            value = kernel.search_results(
                user_id=query.get("user_id", [""])[0],
                role_id=query.get("role_id", [""])[0],
                company_id=query.get("company_id", [""])[0],
                query=query.get("query", [""])[0],
                kind=query.get("kind", ["ALL"])[0],
            )
            self._send_json(HTTPStatus.OK if value["allowed"] else HTTPStatus.FORBIDDEN, value)
            return
        if parsed.path == "/api/recent":
            value = self.experience_store.recent_snapshot(
                user_id=query.get("user_id", [""])[0],
                role_id=query.get("role_id", [""])[0],
                company_id=query.get("company_id", [""])[0],
            )
            self._send_json(HTTPStatus.OK if value["allowed"] else HTTPStatus.FORBIDDEN, value)
            return
        if parsed.path == "/api/notifications":
            value = kernel.notification_snapshot(
                user_id=query.get("user_id", [""])[0],
                role_id=query.get("role_id", [""])[0],
                company_id=query.get("company_id", [""])[0],
            )
            self._send_json(HTTPStatus.OK if value["allowed"] else HTTPStatus.FORBIDDEN, value)
            return
        if parsed.path == "/api/preferences":
            value = self.experience_store.preferences_snapshot(
                actor_user_id=query.get("actor_user_id", [""])[0],
                target_user_id=query.get("target_user_id", [""])[0],
                role_id=query.get("role_id", [""])[0],
                current_company_id=query.get("current_company_id", [""])[0],
            )
            self._send_json(HTTPStatus.OK if value["allowed"] else HTTPStatus.FORBIDDEN, value)
            return
        if parsed.path in {"/favicon.ico", "/api/context", "/api/identity", "/api/audit"}:
            super().do_GET()
            return
        self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path not in {"/api/recent", "/api/preferences"}:
            super().do_POST()
            return
        value = self._read_json_object()
        if value is None:
            self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": "请求内容无效。"})
            return
        if path == "/api/recent":
            result = self.experience_store.record_recent(value)
            allowed = bool(result["event"]["allowed"])
        else:
            result = self.experience_store.save_preferences(value)
            allowed = bool(result["allowed"])
        self._send_json(HTTPStatus.OK if allowed else HTTPStatus.FORBIDDEN, result)


class AppExperienceServer(p2_runtime.IdentityRoleServer):
    def __init__(self, server_address: tuple[str, int], handler: type[AppExperienceHandler]) -> None:
        self.experience_store = PublicExperienceStore()
        super().__init__(server_address, handler)


def start_server(host: str = "127.0.0.1", port: int = 0) -> tuple[AppExperienceServer, threading.Thread, str]:
    server = AppExperienceServer((host, port), AppExperienceHandler)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-s15p3-app-experience", daemon=True)
    thread.start()
    actual_host, actual_port = server.server_address[:2]
    return server, thread, f"http://{actual_host}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S15-P3 应用基础体验公开演示")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost"}:
        parser.error("S15-P3 只允许 localhost")
    server = AppExperienceServer((args.host, args.port), AppExperienceHandler)
    print(f"KMFA 应用基础体验：http://{args.host}:{server.server_address[1]}/overview", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
