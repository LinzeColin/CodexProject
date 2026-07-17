#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S15-P2 身份、角色与最小权限演示。"""

from __future__ import annotations

import argparse
import json
import threading
from datetime import datetime
from http import HTTPStatus
from typing import Any, Mapping
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s15_p1_app_shell as p1_runtime
from KMFA.tools import v015_s15_p2_identity_roles as kernel


def _json_for_html(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_html() -> str:
    html = p1_runtime.render_html()
    users = {
        user_id: {
            "label_zh": value["label_zh"],
            "role_ids": list(value["role_ids"]),
            "company_ids": list(value["company_ids"]),
        }
        for user_id, value in kernel.PUBLIC_USERS.items()
    }
    user_options = "".join(
        f'<option value="{user_id}">{value["label_zh"]}</option>'
        for user_id, value in kernel.PUBLIC_USERS.items()
    )
    identity_bar = f'''
  <section class="identity-shell" aria-label="当前操作身份">
    <div class="identity-bar">
      <div class="identity-heading"><strong>当前操作身份</strong><span>每次查看和确认都会记录当时角色</span></div>
      <label><span>演示用户</span><select id="identity-user">{user_options}</select></label>
      <label><span>准备切换到</span><select id="identity-role"></select></label>
      <label class="identity-reason"><span>切换理由</span><input id="role-switch-reason" value="查看该角色负责的工作" maxlength="80"></label>
      <button id="switch-role" class="secondary-button" type="button">切换角色</button>
    </div>
  </section>'''
    access_workspace = '''
    <section id="access-workspace" class="access-workspace" aria-labelledby="access-title">
      <header class="access-head"><div><h2 id="access-title">当前角色能做什么</h2><p id="active-role-copy">正在核对公开演示权限…</p></div><span id="active-role-chip" class="role-chip">核对中</span></header>
      <div id="role-feedback" class="role-feedback" role="status" aria-live="polite">请选择角色后查看授权范围。</div>
      <div class="access-grid">
        <section class="permission-section" aria-labelledby="permission-title"><h3 id="permission-title">授权范围</h3><div class="permission-table-wrap"><table><thead><tr><th>范围</th><th>当前允许</th></tr></thead><tbody id="permission-body"></tbody></table></div></section>
        <section class="operation-section" aria-labelledby="operation-title"><h3 id="operation-title">受控操作演示</h3><label class="operation-reason"><span>本次理由</span><input id="operation-reason" value="核对公开演示权限" maxlength="100"></label><div class="operation-actions"><button type="button" data-authorize="DATA_SOURCE:VIEW_SENSITIVE">查看敏感来源说明</button><button type="button" data-authorize="PARAMETER:PROPOSE_CHANGE">提出参数变更</button><button id="create-publish" type="button">申请发布报告</button><button id="approve-publish" type="button">确认发布报告</button></div><p id="approval-copy" class="approval-copy">尚无待确认申请。</p></section>
      </div>
      <details class="audit-details"><summary>查看本次操作记录</summary><ol id="audit-list" class="audit-list"><li>尚无操作记录。</li></ol></details>
    </section>'''
    extra_css = '''
    .identity-shell { border-bottom:1px solid var(--line); background:#eaf2f7; }
    .identity-bar { width:min(1240px,100%); margin:auto; padding:12px 24px; display:grid; grid-template-columns:minmax(180px,1.1fr) minmax(150px,.8fr) minmax(150px,.8fr) minmax(220px,1.2fr) auto; gap:12px; align-items:end; }
    .identity-heading { align-self:center; min-width:0; } .identity-heading strong { display:block; color:var(--navy); font-size:14px; } .identity-heading span { display:block; margin-top:3px; color:var(--muted); font-size:12px; }
    .identity-bar label span,.operation-reason span { display:block; margin-bottom:5px; color:var(--muted); font-size:12px; font-weight:650; }
    input { width:100%; min-height:38px; padding:7px 10px; border:1px solid #aebdc8; border-radius:6px; color:var(--text); background:#fff; font:inherit; }
    input:focus,select:focus { border-color:var(--blue); }
    .access-workspace { margin-bottom:20px; padding:18px 20px; border:1px solid var(--line); border-radius:8px; background:#fff; }
    .access-head { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; } .access-head h2 { margin:0; color:var(--navy); font-size:18px; } .access-head p { margin:4px 0 0; color:var(--muted); font-size:13px; }
    .role-chip { flex:none; padding:4px 9px; border:1px solid #91afc4; border-radius:999px; background:#edf6fb; color:var(--blue-dark); font-size:12px; font-weight:700; }
    .role-feedback { margin:14px 0; padding:9px 11px; border:1px solid #c9d8e2; border-radius:6px; background:#f3f8fb; color:#29475d; font-size:13px; }
    .role-feedback[data-state="blocked"] { border-color:#d7a6a6; background:#fff8f7; color:#7f2929; }
    .role-feedback[data-state="allowed"] { border-color:#9bc8b1; background:#f5fbf7; color:#1e6547; }
    .access-grid { display:grid; grid-template-columns:minmax(0,1.15fr) minmax(280px,.85fr); gap:22px; }
    .access-grid h3 { margin:0 0 10px; color:var(--navy); font-size:15px; }
    .permission-table-wrap { overflow:auto; border:1px solid var(--line); border-radius:6px; } table { width:100%; border-collapse:collapse; font-size:13px; } th,td { padding:9px 11px; border-bottom:1px solid #e4eaee; text-align:left; vertical-align:top; } th { background:#f3f6f8; color:#496071; } tr:last-child td { border-bottom:0; } td:first-child { width:120px; color:var(--navy); font-weight:700; }
    .operation-reason { display:block; margin-bottom:10px; } .operation-actions { display:grid; grid-template-columns:1fr 1fr; gap:8px; } .operation-actions button { min-height:38px; padding:8px 10px; border:1px solid #a9bac7; border-radius:6px; background:#fff; color:var(--blue-dark); font:inherit; cursor:pointer; } .operation-actions button:hover { border-color:var(--blue); background:#f4f9fc; }
    .approval-copy { margin:10px 0 0; color:var(--muted); font-size:12px; line-height:1.5; }
    .audit-details { margin-top:16px; border-top:1px solid var(--line); padding-top:12px; } .audit-details summary { color:var(--blue-dark); font-weight:700; cursor:pointer; } .audit-list { margin:10px 0 0; padding-left:22px; color:#42596a; font-size:13px; } .audit-list li { padding:5px 0; }
    @media (max-width:980px) { .identity-bar { grid-template-columns:1fr 1fr; } .identity-heading { grid-column:1/-1; } .identity-reason { min-width:0; } .access-grid { grid-template-columns:1fr; } }
    @media (max-width:520px) { .identity-bar { padding-left:16px; padding-right:16px; grid-template-columns:1fr 1fr; } .identity-heading,.identity-reason,#switch-role { grid-column:1/-1; } .access-workspace { padding:16px; } .access-head { align-items:center; } .operation-actions { grid-template-columns:1fr; } .page-head h1 { font-size:30px; } }
    '''
    role_script = f'''
  <script>
  (() => {{
    'use strict';
    const USERS={_json_for_html(users)};
    const ROLES={_json_for_html(kernel.ROLE_HATS)};
    const IDENTITY_KEY='kmfa.v015.s15p2.identity.v1';
    const userSelect=document.querySelector('#identity-user'); const roleSelect=document.querySelector('#identity-role'); const feedback=document.querySelector('#role-feedback'); const permissionBody=document.querySelector('#permission-body'); const auditList=document.querySelector('#audit-list');
    let latestRequest=''; let snapshotSequence=0;
    const readStored=()=>{{ try {{ const value=JSON.parse(localStorage.getItem(IDENTITY_KEY)||'{{}}'); return value&&typeof value==='object'?value:{{}}; }} catch (_) {{ return {{}}; }} }};
    const stored=readStored(); let identity={{user_id:USERS[stored.user_id]?stored.user_id:'demo-owner',role_id:''}}; identity.role_id=USERS[identity.user_id].role_ids.includes(stored.role_id)?stored.role_id:USERS[identity.user_id].role_ids[0];
    const company=()=>document.querySelector('#context-company').value;
    const identityKey=()=>[identity.user_id,identity.role_id,company()].join('|');
    const reason=()=>document.querySelector('#operation-reason').value.trim()||'核对公开演示权限';
    const persist=()=>localStorage.setItem(IDENTITY_KEY,JSON.stringify(identity));
    const setFeedback=(message,state='')=>{{ feedback.textContent=message; if(state)feedback.dataset.state=state; else delete feedback.dataset.state; }};
    const post=async(path,value)=>{{ const response=await fetch(path,{{method:'POST',headers:{{'Content-Type':'application/json','Accept':'application/json'}},body:JSON.stringify(value)}}); const data=await response.json(); return {{ok:response.ok,status:response.status,data}}; }};
    const roleOptions=()=>{{ roleSelect.replaceChildren(); USERS[identity.user_id].role_ids.forEach(roleId=>{{ const option=document.createElement('option'); option.value=roleId; option.textContent=ROLES[roleId].label_zh; roleSelect.append(option); }}); roleSelect.value=identity.role_id; }};
    const renderPermissions=snapshot=>{{ permissionBody.replaceChildren(); snapshot.permission_summary.forEach(row=>{{ const tr=document.createElement('tr'); const resource=document.createElement('td'); resource.textContent=row.resource_label_zh; const actions=document.createElement('td'); actions.textContent=row.allowed_actions.length?row.allowed_actions.map(item=>item.label_zh).join('、'):'仅显示无权操作已被拦截'; tr.append(resource,actions); permissionBody.append(tr); }}); document.querySelector('#active-role-chip').textContent=snapshot.role_label_zh; document.querySelector('#active-role-copy').textContent=snapshot.user_label_zh+'正以“'+snapshot.role_label_zh+'”处理'+document.querySelector('#context-company').selectedOptions[0].textContent+'的公开演示事项。'; }};
    const normalizeCompanyForUser=()=>{{ const allowedCompanies=USERS[identity.user_id].company_ids; if(allowedCompanies.includes(company()))return false; const select=document.querySelector('#context-company'); select.value=allowedCompanies[0]; select.dispatchEvent(new Event('change',{{bubbles:true}})); return true; }};
    const loadSnapshot=async()=>{{ const sequence=++snapshotSequence; const requestedKey=identityKey(); const query=new URLSearchParams({{user_id:identity.user_id,role_id:identity.role_id,company_id:company()}}); const response=await fetch('/api/identity?'+query); const data=await response.json(); if(sequence!==snapshotSequence||requestedKey!==identityKey())return {{...data,stale_response_ignored:true}}; if(!response.ok||!data.allowed){{ permissionBody.replaceChildren(); document.querySelector('#active-role-chip').textContent='已限制'; document.querySelector('#active-role-copy').textContent=data.reason_zh||'当前身份不可用。'; setFeedback(data.reason_zh||'当前身份不可用。','blocked'); return data; }} renderPermissions(data); setFeedback('当前授权范围已按用户、角色和公司主体重新核对。','allowed'); return data; }};
    const refreshAudit=async()=>{{ const response=await fetch('/api/audit'); const data=await response.json(); auditList.replaceChildren(); if(!data.events.length){{ const li=document.createElement('li'); li.textContent='尚无操作记录。'; auditList.append(li); return data; }} data.events.slice().reverse().forEach((event,index)=>{{ const li=document.createElement('li'); const role=event.actor_role_label_zh||ROLES[event.actor_role]?.label_zh||'未知角色'; li.textContent='第'+String(data.events.length-index)+'条 · '+role+' · '+event.decision_zh+' · '+event.reason_zh+' · 理由：'+(event.request_reason||'未填写'); auditList.append(li); }}); return data; }};
    const switchRole=async(toRole,switchReason)=>{{ const result=await post('/api/role-switch',{{user_id:identity.user_id,from_role:identity.role_id,to_role:toRole,company_id:company(),reason:switchReason}}); const event=result.data.event||result.data; setFeedback(event.reason_zh,event.allowed?'allowed':'blocked'); if(event.allowed){{ identity.role_id=toRole; persist(); roleOptions(); await loadSnapshot(); }} await refreshAudit(); return result; }};
    const authorize=async(resource,action,operationReason=reason())=>{{ const result=await post('/api/authorize',{{user_id:identity.user_id,role_id:identity.role_id,company_id:company(),resource,action,reason:operationReason}}); const event=result.data.event||result.data; setFeedback(event.reason_zh,event.allowed?'allowed':'blocked'); await refreshAudit(); return result; }};
    const createApproval=async(actionType='REPORT_PUBLISH',operationReason=reason())=>{{ const result=await post('/api/approvals',{{mode:'create',action_type:actionType,user_id:identity.user_id,role_id:identity.role_id,company_id:company(),reason:operationReason}}); const event=result.data.event; setFeedback(event.reason_zh,event.allowed?'allowed':'blocked'); if(result.data.request){{ latestRequest=result.data.request.request_id; document.querySelector('#approval-copy').textContent='申请 '+latestRequest+' 正在等待不同的确认角色。'; }} await refreshAudit(); return result; }};
    const approve=async(requestId=latestRequest,operationReason=reason())=>{{ if(!requestId){{ setFeedback('当前没有等待确认的申请。','blocked'); return {{ok:false,status:400,data:{{}}}}; }} const result=await post('/api/approvals',{{mode:'approve',request_id:requestId,user_id:identity.user_id,role_id:identity.role_id,company_id:company(),reason:operationReason}}); const event=result.data.event; setFeedback(event.reason_zh,event.allowed?'allowed':'blocked'); if(result.data.request)document.querySelector('#approval-copy').textContent=result.data.request.action_label_zh+' · '+result.data.request.state_zh; await refreshAudit(); return result; }};
    userSelect.value=identity.user_id; roleOptions();
    userSelect.addEventListener('change',async()=>{{ identity.user_id=userSelect.value; identity.role_id=USERS[identity.user_id].role_ids[0]; persist(); roleOptions(); if(!normalizeCompanyForUser())await loadSnapshot(); }});
    document.querySelector('#switch-role').addEventListener('click',()=>switchRole(roleSelect.value,document.querySelector('#role-switch-reason').value.trim()));
    document.querySelectorAll('[data-authorize]').forEach(button=>button.addEventListener('click',()=>{{ const [resource,action]=button.dataset.authorize.split(':'); authorize(resource,action); }}));
    document.querySelector('#create-publish').addEventListener('click',()=>createApproval()); document.querySelector('#approve-publish').addEventListener('click',()=>approve());
    document.querySelector('#context-company').addEventListener('change',()=>loadSnapshot());
    window.KMFA_ROLE_TEST={{ identity:()=>({{...identity,company_id:company()}}),setIdentity:async(userId,roleId)=>{{ if(USERS[userId]&&USERS[userId].role_ids.includes(roleId)){{ identity={{user_id:userId,role_id:roleId}}; userSelect.value=userId; roleOptions(); persist(); if(normalizeCompanyForUser())return {{allowed:true,company_normalized:true}}; }} return loadSnapshot(); }},switchRole,authorize,createApproval,approve,audit:refreshAudit,latestRequest:()=>latestRequest }};
    persist(); if(!normalizeCompanyForUser())loadSnapshot(); refreshAudit();
  }})();
  </script>
'''
    html = html.replace("<title>KMFA 经营工作台</title>", "<title>KMFA 身份与角色 · 经营工作台</title>")
    html = html.replace(
        "border:1px solid #c9d8e2; border-left:4px solid var(--blue);",
        "border:1px solid #c9d8e2;",
    )
    html = html.replace(
        "border:1px solid #e2b8b8; border-left:4px solid var(--danger);",
        "border:1px solid #e2b8b8;",
    )
    html = html.replace("font-size:clamp(26px,4vw,38px);", "font-size:38px;")
    html = html.replace("  </style>", extra_css + "  </style>", 1)
    html = html.replace("  </section>\n  <main id=\"main-content\"", "  </section>" + identity_bar + "\n  <main id=\"main-content\"", 1)
    status = '<div id="context-status" class="status-line" role="status" aria-live="polite"><span>正在准备演示内容…</span></div>'
    html = html.replace(status, status + access_workspace, 1)
    html = html.replace("</body>", role_script + "</body>", 1)
    return html


class PublicAuthorizationStore:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.events: list[dict[str, Any]] = []
        self.requests: dict[str, dict[str, Any]] = {}
        self.event_sequence = 0
        self.request_sequence = 0

    def _event_identity(self) -> tuple[str, str]:
        self.event_sequence += 1
        return f"AUTH-{self.event_sequence:04d}", datetime.now().astimezone().isoformat()

    def _request_id(self) -> str:
        self.request_sequence += 1
        return f"APR-{self.request_sequence:04d}"

    def switch_role(self, value: Mapping[str, Any]) -> dict[str, Any]:
        with self.lock:
            event_id, occurred_at = self._event_identity()
            event = kernel.role_switch_decision(
                event_id=event_id,
                occurred_at=occurred_at,
                user_id=str(value.get("user_id", "")),
                from_role=str(value.get("from_role", "")),
                to_role=str(value.get("to_role", "")),
                company_id=str(value.get("company_id", "")),
                reason=str(value.get("reason", "")),
            )
            self.events.append(event)
            return {"event": event}

    def authorize(self, value: Mapping[str, Any]) -> dict[str, Any]:
        with self.lock:
            event_id, occurred_at = self._event_identity()
            event = kernel.authorization_decision(
                event_id=event_id,
                occurred_at=occurred_at,
                user_id=str(value.get("user_id", "")),
                role_id=str(value.get("role_id", "")),
                company_id=str(value.get("company_id", "")),
                resource=str(value.get("resource", "")),
                action=str(value.get("action", "")),
                reason=str(value.get("reason", "")),
            )
            self.events.append(event)
            return {"event": event}

    def approval(self, value: Mapping[str, Any]) -> dict[str, Any]:
        with self.lock:
            event_id, occurred_at = self._event_identity()
            mode = str(value.get("mode", ""))
            if mode == "create":
                result = kernel.approval_request_decision(
                    event_id=event_id,
                    request_id=self._request_id(),
                    occurred_at=occurred_at,
                    action_type=str(value.get("action_type", "")),
                    user_id=str(value.get("user_id", "")),
                    role_id=str(value.get("role_id", "")),
                    company_id=str(value.get("company_id", "")),
                    reason=str(value.get("reason", "")),
                )
                if result["request"]:
                    self.requests[result["request"]["request_id"]] = result["request"]
            elif mode == "approve":
                request_id = str(value.get("request_id", ""))
                request = self.requests.get(request_id)
                if not request:
                    event = {
                        "schema_version": "kmfa.v015.s15p2.approval_event.v1",
                        "event_id": event_id,
                        "event_type": "APPROVAL_CONFIRMATION",
                        "occurred_at": occurred_at,
                        "actor_user_id": str(value.get("user_id", "")),
                        "actor_role": str(value.get("role_id", "")),
                        "actor_role_label_zh": kernel.ROLE_HATS.get(str(value.get("role_id", "")), {}).get("label_zh", "未知角色"),
                        "company_id": str(value.get("company_id", "")),
                        "request_id": request_id,
                        "request_reason": str(value.get("reason", "")),
                        "allowed": False,
                        "decision_zh": "已阻止",
                        "reason_code": "REQUEST_NOT_FOUND",
                        "reason_zh": "这项申请不存在。",
                        "operation_performed": False,
                    }
                    result = {"allowed": False, "event": event, "request": None}
                else:
                    result = kernel.approval_confirmation_decision(
                        event_id=event_id,
                        occurred_at=occurred_at,
                        request=request,
                        user_id=str(value.get("user_id", "")),
                        role_id=str(value.get("role_id", "")),
                        company_id=str(value.get("company_id", "")),
                        reason=str(value.get("reason", "")),
                    )
                    if result["allowed"]:
                        self.requests[request_id] = result["request"]
            else:
                event = {
                    "schema_version": "kmfa.v015.s15p2.approval_event.v1",
                    "event_id": event_id,
                    "event_type": "APPROVAL_UNKNOWN",
                    "occurred_at": occurred_at,
                    "actor_user_id": str(value.get("user_id", "")),
                    "actor_role": str(value.get("role_id", "")),
                    "actor_role_label_zh": kernel.ROLE_HATS.get(str(value.get("role_id", "")), {}).get("label_zh", "未知角色"),
                    "company_id": str(value.get("company_id", "")),
                    "request_reason": str(value.get("reason", "")),
                    "allowed": False,
                    "decision_zh": "已阻止",
                    "reason_code": "MODE_NOT_FOUND",
                    "reason_zh": "这个审批操作不存在。",
                    "operation_performed": False,
                }
                result = {"allowed": False, "event": event, "request": None}
            self.events.append(result["event"])
            return result

    def audit_snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "schema_version": "kmfa.v015.s15p2.audit_snapshot.v1",
                "data_classification": "PUBLIC_SYNTHETIC",
                "event_count": len(self.events),
                "events": [dict(item) for item in self.events[-20:]],
                "real_business_action_count": 0,
            }


class IdentityRoleHandler(p1_runtime.AppShellHandler):
    server_version = "KMFAIdentityRoles/1.5"

    @property
    def store(self) -> PublicAuthorizationStore:
        return self.server.authorization_store  # type: ignore[attr-defined,no-any-return]

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/favicon.ico":
            self._send(HTTPStatus.NO_CONTENT, b"", "image/x-icon")
            return
        if parsed.path == "/api/context":
            self._context_api(parse_qs(parsed.query))
            return
        if parsed.path == "/api/identity":
            query = parse_qs(parsed.query)
            snapshot = kernel.identity_snapshot(
                query.get("user_id", [""])[0],
                query.get("role_id", [""])[0],
                query.get("company_id", [""])[0],
            )
            self._send_json(HTTPStatus.OK if snapshot["allowed"] else HTTPStatus.FORBIDDEN, snapshot)
            return
        if parsed.path == "/api/audit":
            self._send_json(HTTPStatus.OK, self.store.audit_snapshot())
            return
        self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        length_text = self.headers.get("Content-Length", "0")
        try:
            length = int(length_text)
        except ValueError:
            length = 0
        if length <= 0 or length > 16_384:
            self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": "请求内容无效。"})
            return
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": "请求内容无法读取。"})
            return
        if not isinstance(value, dict):
            self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": "请求必须是对象。"})
            return
        if parsed.path == "/api/role-switch":
            result = self.store.switch_role(value)
        elif parsed.path == "/api/authorize":
            result = self.store.authorize(value)
        elif parsed.path == "/api/approvals":
            result = self.store.approval(value)
        else:
            self._send_json(HTTPStatus.NOT_FOUND, {"allowed": False, "reason_zh": "接口不存在。"})
            return
        allowed = bool(result.get("event", {}).get("allowed"))
        self._send_json(HTTPStatus.OK if allowed else HTTPStatus.FORBIDDEN, result)


class IdentityRoleServer(p1_runtime.AppShellServer):
    def __init__(self, server_address: tuple[str, int], handler: type[IdentityRoleHandler]) -> None:
        self.authorization_store = PublicAuthorizationStore()
        super().__init__(server_address, handler)


def start_server(host: str = "127.0.0.1", port: int = 0) -> tuple[IdentityRoleServer, threading.Thread, str]:
    server = IdentityRoleServer((host, port), IdentityRoleHandler)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-s15p2-identity-roles", daemon=True)
    thread.start()
    actual_host, actual_port = server.server_address[:2]
    return server, thread, f"http://{actual_host}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S15-P2 身份与角色公开演示")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost"}:
        parser.error("S15-P2 只允许 localhost")
    server = IdentityRoleServer((args.host, args.port), IdentityRoleHandler)
    print(f"KMFA 身份与角色演示：http://{args.host}:{server.server_address[1]}/overview", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
