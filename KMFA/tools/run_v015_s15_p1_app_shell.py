#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S15-P1 应用外壳。"""

from __future__ import annotations

import argparse
import json
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import v015_s15_p1_app_shell as kernel


def _json_for_html(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_html() -> str:
    routes = {
        node["route"]: {
            "route": node["route"],
            "nav_id": node["nav_id"],
            "page_type": node["page_type"],
            "parent_route": node["parent_route"],
            "title_zh": node["title_zh"],
            "eyebrow_zh": node["eyebrow_zh"],
            "summary_zh": node["summary_zh"],
            "facts_zh": list(node["facts_zh"]),
            "next_routes": list(node["next_routes"]),
        }
        for node in kernel.PAGE_NODES
    }
    nav_html = "".join(
        f'<a href="{item["route"]}" data-route="{item["route"]}" data-nav-id="{item["nav_id"]}">{item["label_zh"]}</a>'
        for item in kernel.NAV_ITEMS
    )
    select_html = []
    labels = {
        "company": "公司主体",
        "period": "查看期间",
        "project_status": "项目状态",
        "report_version": "报告版本",
    }
    for key, options in kernel.CONTEXT_OPTIONS.items():
        options_html = "".join(
            f'<option value="{item["value"]}">{item["label"]}</option>' for item in options
        )
        select_html.append(
            f'<label><span>{labels[key]}</span><select id="context-{key}" data-context-key="{key}">{options_html}</select></label>'
        )
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>KMFA 经营工作台</title>
  <style>
    :root {{ --navy:#102f50; --blue:#17679b; --blue-dark:#0f527e; --page:#f3f6f8; --surface:#fff; --line:#d8e1e7; --text:#1a2b3b; --muted:#5b6b79; --success:#287557; --warning:#9a5b13; --danger:#a23a3a; --focus:#ffbf47; --radius:8px; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; color:var(--text); background:var(--page); }}
    * {{ box-sizing:border-box; }} body {{ margin:0; min-width:320px; background:var(--page); }}
    a {{ color:var(--blue); }} button,select {{ font:inherit; }}
    .skip-link {{ position:absolute; left:12px; top:-48px; z-index:20; padding:10px 14px; background:#fff; color:var(--navy); }} .skip-link:focus {{ top:8px; }}
    .topbar {{ background:var(--navy); color:#fff; }}
    .topbar-inner {{ width:min(1240px,100%); margin:auto; padding:16px 24px 0; }}
    .brand-row {{ display:flex; align-items:center; justify-content:space-between; gap:16px; padding-bottom:14px; }}
    .brand {{ display:flex; align-items:center; gap:12px; min-width:0; }} .brand-mark {{ display:grid; place-items:center; width:34px; height:34px; border:1px solid #7ea2bf; border-radius:6px; font-weight:750; }}
    .brand strong {{ display:block; font-size:17px; }} .brand small {{ display:block; color:#c9d7e3; margin-top:2px; }} .demo-chip {{ border:1px solid #7696b0; border-radius:999px; padding:5px 9px; color:#e6eef4; font-size:12px; white-space:nowrap; }}
    .primary-nav {{ display:flex; gap:2px; overflow-x:auto; scrollbar-width:thin; }}
    .primary-nav a {{ flex:0 0 auto; color:#dce8f0; text-decoration:none; padding:11px 13px 12px; border-bottom:3px solid transparent; }}
    .primary-nav a:hover {{ background:#173f64; color:#fff; }} .primary-nav a[aria-current="page"] {{ color:#fff; border-bottom-color:#70b8e8; background:#173f64; }}
    .context-shell {{ border-bottom:1px solid var(--line); background:var(--surface); }}
    .context-bar {{ width:min(1240px,100%); margin:auto; padding:14px 24px; display:grid; grid-template-columns:repeat(4,minmax(145px,1fr)); gap:12px; }}
    .context-bar label span {{ display:block; margin-bottom:5px; color:var(--muted); font-size:12px; font-weight:650; }}
    select {{ width:100%; min-height:38px; padding:7px 32px 7px 10px; border:1px solid #aebdc8; border-radius:6px; color:var(--text); background:#fff; }}
    .workspace {{ width:min(1240px,100%); margin:auto; padding:22px 24px 48px; }}
    .breadcrumb {{ display:flex; flex-wrap:wrap; align-items:center; gap:7px; margin:0 0 16px; padding:0; list-style:none; font-size:13px; color:var(--muted); }} .breadcrumb a {{ text-decoration:none; }}
    .status-line {{ display:flex; justify-content:space-between; gap:12px; align-items:center; min-height:36px; padding:8px 11px; border:1px solid #c9d8e2; border-left:4px solid var(--blue); background:#edf5fa; color:#29475d; font-size:13px; }}
    .status-line strong {{ flex:none; white-space:nowrap; }}
    .page-head {{ margin:24px 0 18px; max-width:850px; }} .eyebrow {{ color:var(--blue-dark); font-weight:700; font-size:13px; }} h1 {{ margin:6px 0 9px; color:var(--navy); font-size:clamp(26px,4vw,38px); line-height:1.18; letter-spacing:-.015em; }} .lead {{ margin:0; color:#465d6e; font-size:16px; line-height:1.65; }}
    .metrics {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); border:1px solid var(--line); border-radius:var(--radius); background:var(--surface); overflow:hidden; }} .metric {{ padding:17px 18px; border-right:1px solid var(--line); }} .metric:last-child {{ border-right:0; }} .metric span {{ display:block; color:var(--muted); font-size:13px; }} .metric strong {{ display:block; margin-top:7px; color:var(--navy); font-size:25px; }}
    .content-grid {{ display:grid; grid-template-columns:minmax(0,1.55fr) minmax(260px,.75fr); gap:18px; margin-top:18px; }}
    .panel {{ background:var(--surface); border:1px solid var(--line); border-radius:var(--radius); padding:20px; }} .panel h2 {{ margin:0 0 14px; color:var(--navy); font-size:18px; }}
    .item-list {{ list-style:none; margin:0; padding:0; }} .item-list li {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:12px; padding:13px 0; border-top:1px solid #e6ecef; }} .item-list li:first-child {{ border-top:0; padding-top:0; }} .item-list strong {{ display:block; }} .item-list small {{ display:block; color:var(--muted); margin-top:4px; }} .status-text {{ align-self:center; color:var(--success); font-size:13px; font-weight:650; }}
    .next-list {{ display:grid; gap:9px; }} .route-button,.primary-button,.secondary-button {{ display:inline-flex; align-items:center; justify-content:center; min-height:38px; border-radius:6px; padding:8px 13px; text-decoration:none; cursor:pointer; }} .route-button,.secondary-button {{ border:1px solid #a9bac7; background:#fff; color:var(--blue-dark); }} .primary-button {{ border:1px solid var(--blue); background:var(--blue); color:#fff; }} .primary-button:hover {{ background:var(--blue-dark); }}
    .loading {{ margin-top:18px; }} .skeleton {{ height:18px; margin:10px 0; border-radius:4px; background:linear-gradient(90deg,#e5ebef 25%,#f3f6f8 37%,#e5ebef 63%); background-size:400% 100%; animation:skeleton 1.2s ease-in-out infinite; }} .skeleton.short {{ width:55%; }} @keyframes skeleton {{ from {{ background-position:100% 0; }} to {{ background-position:0 0; }} }}
    .error-panel,.not-found {{ margin-top:20px; border:1px solid #e2b8b8; border-left:4px solid var(--danger); background:#fff8f7; padding:20px; border-radius:var(--radius); }} .error-panel h2,.not-found h1 {{ margin:0 0 8px; color:#7f2929; font-size:22px; }} .error-panel p,.not-found p {{ margin:0 0 16px; color:#5e4242; }}
    [hidden] {{ display:none !important; }} :focus-visible {{ outline:3px solid var(--focus); outline-offset:2px; }}
    @media (max-width:760px) {{ .topbar-inner,.context-bar,.workspace {{ padding-left:16px; padding-right:16px; }} .brand small {{ display:none; }} .context-bar {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .content-grid {{ grid-template-columns:1fr; }} .metrics {{ grid-template-columns:1fr; }} .metric {{ border-right:0; border-bottom:1px solid var(--line); }} .metric:last-child {{ border-bottom:0; }} .workspace {{ padding-top:18px; }} button,select,input:not([type="checkbox"]):not([type="radio"]):not([type="file"]),.route-button,.primary-button,.secondary-button {{ min-height:44px; }} }}
    @media (max-width:430px) {{ .context-bar {{ grid-template-columns:1fr 1fr; gap:10px; }} .demo-chip {{ display:none; }} .primary-nav a {{ padding-left:11px; padding-right:11px; }} }}
    @media print {{ :root,body {{ background:#fff; color:#000; }} .topbar,.context-shell,.identity-shell,.quick-shell,#access-workspace,#experience-workspace,.skip-link {{ display:none !important; }} .workspace {{ width:auto; max-width:none; margin:0; padding:0; }} main,#page-view {{ display:block !important; }} .breadcrumb {{ margin-bottom:10px; }} .content-grid {{ grid-template-columns:1fr; }} .panel,.metrics,.metric,.status-line {{ box-shadow:none; break-inside:avoid; }} a {{ color:inherit; text-decoration:none; }} }}
    @media (prefers-reduced-motion:reduce) {{ *,*::before,*::after {{ animation-duration:.01ms !important; animation-iteration-count:1 !important; scroll-behavior:auto !important; transition-duration:.01ms !important; }} }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">跳到主要内容</a>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand-row"><div class="brand"><span class="brand-mark" aria-hidden="true">K</span><div><strong>KMFA 经营工作台</strong><small>把经营事项放在一个清楚的位置</small></div></div><span class="demo-chip">公开演示</span></div>
      <nav id="primary-nav" class="primary-nav" aria-label="主要功能">{nav_html}</nav>
    </div>
  </header>
  <section class="context-shell" aria-label="全局筛选">
    <form id="context-form" class="context-bar">{''.join(select_html)}</form>
  </section>
  <main id="main-content" class="workspace" tabindex="-1">
    <nav aria-label="当前位置"><ol id="breadcrumbs" class="breadcrumb"></ol></nav>
    <div id="context-status" class="status-line" role="status" aria-live="polite"><span>正在准备演示内容…</span></div>
    <section id="loading-view" class="loading" aria-busy="true" aria-label="正在加载"><div class="skeleton short"></div><div class="skeleton"></div><div class="skeleton"></div></section>
    <section id="error-view" class="error-panel" role="alert" hidden><h2 id="error-title"></h2><p id="error-message"></p><button id="error-action" class="primary-button" type="button"></button></section>
    <section id="not-found-view" class="not-found" hidden><h1>这个页面暂时找不到</h1><p>地址可能已经改变。你可以返回经营首页继续查看。</p><a class="primary-button" href="/overview" data-route="/overview">返回经营首页</a></section>
    <section id="page-view" hidden>
      <header class="page-head"><div id="page-eyebrow" class="eyebrow"></div><h1 id="page-title"></h1><p id="page-lead" class="lead"></p></header>
      <div class="metrics" aria-label="当前筛选摘要"><div class="metric"><span>当前事项</span><strong id="metric-visible">—</strong></div><div class="metric"><span>需要关注</span><strong id="metric-attention">—</strong></div><div class="metric"><span>待更新</span><strong id="metric-update">—</strong></div></div>
      <div class="content-grid"><section class="panel"><h2>当前重点</h2><ul id="item-list" class="item-list"></ul></section><aside class="panel"><h2>接下来可以做</h2><div id="next-list" class="next-list"></div></aside></div>
    </section>
  </main>
  <script>
  (() => {{
    'use strict';
    const ROUTES={_json_for_html(routes)};
    const NAV={_json_for_html(kernel.NAV_ITEMS)};
    const OPTIONS={_json_for_html(kernel.CONTEXT_OPTIONS)};
    const DEFAULTS={_json_for_html(kernel.DEFAULT_CONTEXT)};
    const STORAGE_KEY='kmfa.v015.s15p1.context.v1';
    const els={{ page:document.querySelector('#page-view'), loading:document.querySelector('#loading-view'), error:document.querySelector('#error-view'), notFound:document.querySelector('#not-found-view'), status:document.querySelector('#context-status'), breadcrumbs:document.querySelector('#breadcrumbs') }};
    let requestSequence=0; let activeController=null; let testFault=''; let testDelay=0;
    const allowed=(key,value)=>(OPTIONS[key]||[]).some(option=>option.value===value);
    const safeStored=()=>{{ try {{ const value=JSON.parse(localStorage.getItem(STORAGE_KEY)||'{{}}'); return value&&typeof value==='object'?value:{{}}; }} catch (_) {{ return {{}}; }} }};
    const params=new URLSearchParams(location.search); const stored=safeStored();
    let context={{}};
    Object.keys(DEFAULTS).forEach(key=>{{ const candidate=params.get(key)||stored[key]||DEFAULTS[key]; context[key]=allowed(key,candidate)?candidate:DEFAULTS[key]; }});
    const labels=()=>Object.fromEntries(Object.entries(context).map(([key,value])=>[key,OPTIONS[key].find(option=>option.value===value).label]));
    const syncControls=()=>document.querySelectorAll('[data-context-key]').forEach(select=>select.value=context[select.dataset.contextKey]);
    const contextQuery=()=>{{ const query=new URLSearchParams(); Object.entries(context).forEach(([key,value])=>query.set(key,value)); return query; }};
    const persist=(replace=true)=>{{ localStorage.setItem(STORAGE_KEY,JSON.stringify(context)); const url=location.pathname+'?'+contextQuery().toString(); history[replace?'replaceState':'pushState']({{path:location.pathname,context}},'',url); }};
    const routeChain=route=>{{ const chain=[]; let current=ROUTES[route]; const seen=new Set(); while(current&&!seen.has(current.route)){{ seen.add(current.route); chain.unshift(current); current=current.parent_route?ROUTES[current.parent_route]:null; }} return chain; }};
    const renderRoute=()=>{{
      const route=ROUTES[location.pathname];
      document.querySelectorAll('#primary-nav a').forEach(link=>{{ const active=route&&route.nav_id===link.dataset.navId; if(active) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current'); }});
      els.breadcrumbs.replaceChildren();
      if(!route){{ els.page.hidden=true; els.loading.hidden=true; els.error.hidden=true; els.notFound.hidden=false; document.title='页面未找到 · KMFA 经营工作台'; return false; }}
      els.notFound.hidden=true; routeChain(route.route).forEach((node,index,all)=>{{ const li=document.createElement('li'); if(index<all.length-1){{ const a=document.createElement('a'); a.href=node.route; a.dataset.route=node.route; a.textContent=node.title_zh; li.append(a); const sep=document.createElement('span'); sep.textContent='›'; sep.setAttribute('aria-hidden','true'); li.append(sep); }} else {{ li.textContent=node.title_zh; li.setAttribute('aria-current','page'); }} els.breadcrumbs.append(li); }});
      document.querySelector('#page-eyebrow').textContent=route.eyebrow_zh; document.querySelector('#page-title').textContent=route.title_zh; document.querySelector('#page-lead').textContent=route.summary_zh; document.title=route.title_zh+' · KMFA 经营工作台';
      const next=document.querySelector('#next-list'); next.replaceChildren(); route.next_routes.slice(0,3).forEach(nextRoute=>{{ const target=ROUTES[nextRoute]; if(!target)return; const a=document.createElement('a'); a.className='route-button'; a.href=nextRoute; a.dataset.route=nextRoute; a.textContent=target.title_zh; next.append(a); }});
      return true;
    }};
    const showLoading=()=>{{ els.notFound.hidden=true; els.error.hidden=true; els.page.hidden=true; els.loading.hidden=false; els.loading.setAttribute('aria-busy','true'); els.status.innerHTML='<span>正在更新当前查看范围…</span>'; }};
    const errorCopy=(kind)=>({{
      network:['暂时无法连接','演示服务暂时没有响应。请稍后重试。','重新加载'],
      parse:['返回内容无法读取','收到的内容格式不完整。请重新加载。','重新加载'],
      calculation:['暂时无法完成计算','当前筛选条件下无法形成结果。请调整条件或重试。','重新加载'],
      permission:['当前账号不能查看','你没有查看这个演示范围的权限。请返回经营首页。','返回经营首页'],
      isolation:['已阻止主体数据混用','返回内容与当前公司主体不一致，页面没有展示这批内容。','重新加载']
    }}[kind]||['内容暂时不可用','请重新加载。','重新加载']);
    const showError=kind=>{{ const copy=errorCopy(kind); els.loading.hidden=true; els.page.hidden=true; els.error.hidden=false; document.querySelector('#error-title').textContent=copy[0]; document.querySelector('#error-message').textContent=copy[1]; document.querySelector('#error-action').textContent=copy[2]; document.querySelector('#error-action').dataset.errorKind=kind; els.status.innerHTML='<span>未展示不完整内容 · '+copy[0]+'</span>'; }};
    const classify=(response,error)=>{{ if(error&&error.name==='SyntaxError')return'parse'; if(response&&response.status===403)return'permission'; if(response&&response.status===422)return'calculation'; return'network'; }};
    const renderData=payload=>{{
      document.querySelector('#metric-visible').textContent=String(payload.summary.visible_item_count); document.querySelector('#metric-attention').textContent=String(payload.summary.attention_count); document.querySelector('#metric-update').textContent=String(payload.summary.update_count);
      const list=document.querySelector('#item-list'); list.replaceChildren(); payload.items.forEach(item=>{{ const li=document.createElement('li'); const copy=document.createElement('div'); const strong=document.createElement('strong'); strong.textContent=item.title_zh; const small=document.createElement('small'); small.textContent=item.next_step_zh; copy.append(strong,small); const status=document.createElement('span'); status.className='status-text'; status.textContent='● '+item.status_zh; li.append(copy,status); list.append(li); }});
      els.status.innerHTML='<span>'+payload.summary.message_zh+'</span><strong>已更新</strong>'; els.loading.hidden=true; els.error.hidden=true; els.page.hidden=false;
    }};
    const loadData=async()=>{{
      if(!ROUTES[location.pathname])return; showLoading(); const sequence=++requestSequence; if(activeController)activeController.abort(); activeController=new AbortController();
      const requested={{...context}}; const query=contextQuery(); if(testFault)query.set('fault',testFault); if(testDelay)query.set('delay_ms',String(testDelay)); let response=null;
      try {{ response=await fetch('/api/context?'+query.toString(),{{signal:activeController.signal,headers:{{'Accept':'application/json'}}}}); const text=await response.text(); const payload=JSON.parse(text); if(!response.ok)throw Object.assign(new Error(payload.message_zh||'request failed'),{{response}}); if(sequence!==requestSequence)return; const contextExact=Object.keys(requested).every(key=>payload.context&&payload.context[key]===requested[key]); const itemsExact=Array.isArray(payload.items)&&payload.items.every(item=>item.company_id===requested.company); if(!contextExact||!itemsExact){{ showError('isolation'); return; }} renderData(payload); }} catch(error){{ if(error.name==='AbortError'||sequence!==requestSequence)return; showError(classify(error.response||response,error)); }}
    }};
    const navigate=(path,push=true)=>{{ const state=ROUTES[path]||path==='/overview'?{{path,context}}:{{path}}; history[push?'pushState':'replaceState'](state,'',path+'?'+contextQuery().toString()); dispatchEvent(new PopStateEvent('popstate',{{state:history.state}})); document.querySelector('#main-content').focus({{preventScroll:true}}); }};
    document.addEventListener('click',event=>{{ const link=event.target.closest('a[data-route]'); if(!link||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return; event.preventDefault(); navigate(link.dataset.route,true); }});
    document.querySelector('#context-form').addEventListener('change',event=>{{ const select=event.target.closest('[data-context-key]'); if(!select)return; context={{...context,[select.dataset.contextKey]:select.value}}; persist(true); loadData(); }});
    document.querySelector('#error-action').addEventListener('click',event=>{{ const kind=event.currentTarget.dataset.errorKind; testFault=''; testDelay=0; if(kind==='permission')navigate('/overview',true); else loadData(); }});
    addEventListener('popstate',()=>{{ const query=new URLSearchParams(location.search); Object.keys(DEFAULTS).forEach(key=>{{ const value=query.get(key); if(value&&allowed(key,value))context[key]=value; }}); syncControls(); renderRoute(); loadData(); }});
    window.KMFA_TEST={{ setFault:value=>{{ testFault=value||''; }}, setDelay:value=>{{ testDelay=Math.max(0,Number(value)||0); }}, load:()=>loadData(), context:()=>({{...context}}), setContext:(next)=>{{ Object.entries(next||{{}}).forEach(([key,value])=>{{ if(allowed(key,value))context[key]=value; }}); syncControls(); persist(true); return loadData(); }} }};
    syncControls(); persist(true); if(renderRoute())loadData();
  }})();
  </script>
</body>
</html>'''


class AppShellHandler(BaseHTTPRequestHandler):
    server_version = "KMFAAppShell/1.5"

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, value: dict[str, Any]) -> None:
        body = (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/favicon.ico":
            self._send(HTTPStatus.NO_CONTENT, b"", "image/x-icon")
            return
        if parsed.path == "/api/context":
            self._context_api(parse_qs(parsed.query))
            return
        body = render_html().encode("utf-8")
        self._send(HTTPStatus.OK, body, "text/html; charset=utf-8")

    def _context_api(self, query: dict[str, list[str]]) -> None:
        delay_text = query.get("delay_ms", ["0"])[0]
        try:
            delay_ms = min(max(int(delay_text), 0), 1500)
        except ValueError:
            delay_ms = 0
        if delay_ms:
            time.sleep(delay_ms / 1000)
        fault = query.get("fault", [""])[0]
        if fault == "parse":
            self._send(HTTPStatus.OK, b'{"incomplete":', "application/json; charset=utf-8")
            return
        if fault in {"network", "calculation", "permission"}:
            contract = kernel.FAULT_CONTRACT[fault]
            self._send_json(
                contract["http_status"],
                {
                    "schema_version": "kmfa.v015.s15p1.error.v1",
                    "error_type": fault,
                    "title_zh": contract["title_zh"],
                    "message_zh": contract["message_zh"],
                    "action_zh": contract["action_zh"],
                },
            )
            return
        context = kernel.normalize_context({key: query.get(key, [None])[0] for key in kernel.CONTEXT_OPTIONS})
        self._send_json(HTTPStatus.OK, kernel.public_context_result(context).as_dict())


class AppShellServer(ThreadingHTTPServer):
    daemon_threads = True


def start_server(host: str = "127.0.0.1", port: int = 0) -> tuple[AppShellServer, threading.Thread, str]:
    server = AppShellServer((host, port), AppShellHandler)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-s15p1-app-shell", daemon=True)
    thread.start()
    actual_host, actual_port = server.server_address[:2]
    return server, thread, f"http://{actual_host}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S15-P1 localhost 应用外壳")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost"}:
        parser.error("S15-P1 只允许 localhost")
    server = AppShellServer((args.host, args.port), AppShellHandler)
    print(f"KMFA 应用外壳：http://{args.host}:{server.server_address[1]}/overview", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
