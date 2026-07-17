#!/usr/bin/env python3
"""在 localhost 运行 KMFA v1.5 S16-P3 首页人类可用验收演示。"""

from __future__ import annotations

import argparse
import json
import threading
from http import HTTPStatus
from typing import Any
from urllib.parse import parse_qs, urlsplit

from KMFA.tools import run_v015_s16_p2_drilldown_explanation as p2_runtime
from KMFA.tools import v015_s16_p1_homepage as homepage_kernel
from KMFA.tools import v015_s16_p3_homepage_usability as kernel


def _json_for_html(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_html() -> str:
    html = p2_runtime.render_html()
    scan_and_state = '''
      <section id="ten-second-overview" class="ten-second-overview" aria-labelledby="ten-second-title">
        <div class="scan-copy">
          <div class="scan-heading"><h2 id="ten-second-title">经营状态</h2><span id="scan-status" class="scan-status">正在核对</span></div>
          <p id="scan-summary">正在整理当前状态和最需要处理的事项…</p>
        </div>
        <div class="priority-preview-wrap">
          <strong>先处理这 3 项</strong>
          <ol id="priority-preview" class="priority-preview"></ol>
        </div>
      </section>
      <section id="homepage-state-panel" class="homepage-state-panel" aria-labelledby="homepage-state-title" aria-live="polite" hidden>
        <div class="state-symbol" aria-hidden="true">!</div>
        <div class="state-copy">
          <span id="homepage-state-label">当前状态</span>
          <h2 id="homepage-state-title">正在核对资料…</h2>
          <p id="homepage-state-reason"></p>
          <p id="homepage-state-impact" class="state-impact"></p>
          <a id="homepage-state-action" class="state-action" href="/overview" data-route="/overview">重新加载</a>
        </div>
      </section>'''
    extra_css = '''
    body[data-homepage-active="true"] .identity-shell,
    body[data-homepage-active="true"] .quick-shell,
    body[data-homepage-active="true"] #access-workspace,
    body[data-homepage-active="true"] #experience-workspace,
    body[data-homepage-active="true"] #main-content > nav[aria-label="当前位置"],
    body[data-homepage-active="true"] #context-status { display:none!important; }
    .ten-second-overview { display:grid; grid-template-columns:minmax(0,1.25fr) minmax(320px,.75fr); gap:22px; margin:0 0 14px; padding:15px 17px; border-top:1px solid #a9c4d6; border-bottom:1px solid #a9c4d6; background:#edf6fb; }
    .scan-heading { display:flex; align-items:center; gap:10px; }
    .scan-heading h2 { margin:0; color:var(--navy); font-size:17px; line-height:1.35; }
    .scan-status { display:inline-flex; min-height:25px; padding:3px 8px; align-items:center; border:1px solid #9eb9c9; border-radius:999px; color:#114b74; background:#fff; font-size:12px; font-weight:750; }
    .scan-status::before { content:'!'; margin-right:5px; }
    .scan-status[data-state="INCOMPLETE"] { color:#6b4c11; border-color:#d7bc80; }
    .scan-copy p { max-width:68ch; margin:7px 0 0; color:#263d4e; font-size:14px; line-height:1.6; }
    .priority-preview-wrap { min-width:0; padding-left:20px; border-left:1px solid #bfd1dd; }
    .priority-preview-wrap > strong { color:#355064; font-size:12px; }
    .priority-preview { display:grid; gap:5px; margin:7px 0 0; padding:0; list-style:none; }
    .priority-preview li { display:grid; grid-template-columns:22px minmax(0,1fr); gap:7px; align-items:start; color:var(--text); font-size:13px; line-height:1.4; }
    .priority-preview-rank { display:flex; width:21px; height:21px; align-items:center; justify-content:center; border:1px solid #9eb9c9; border-radius:50%; color:#114b74; background:#fff; font-size:11px; font-weight:750; }
    .homepage-state-panel { display:grid; grid-template-columns:36px minmax(0,1fr); gap:13px; margin:0 0 14px; padding:16px 17px; border:1px solid #d7bc80; border-radius:8px; background:#fffaf0; }
    .homepage-state-panel[hidden] { display:none; }
    .state-symbol { display:flex; width:34px; height:34px; align-items:center; justify-content:center; border:1px solid #c39b4f; border-radius:50%; color:#6b4c11; font-weight:800; }
    .state-copy > span { color:#6b4c11; font-size:12px; font-weight:750; }
    .state-copy h2 { margin:2px 0 0; color:var(--navy); font-size:18px; line-height:1.4; }
    .state-copy p { max-width:72ch; margin:5px 0 0; color:#4d6070; font-size:13px; line-height:1.55; }
    .state-copy .state-impact { color:#263d4e; }
    .state-action { display:inline-flex; min-height:38px; margin-top:11px; padding:7px 11px; align-items:center; border:1px solid #8ca9bc; border-radius:6px; color:#114b74; background:#fff; font-size:13px; font-weight:750; text-decoration:none; }
    .state-action:hover { border-color:#17679b; background:#edf6fb; }
    @media (max-width:760px) { .ten-second-overview { grid-template-columns:1fr; gap:12px; padding:14px 15px; } .priority-preview-wrap { padding:11px 0 0; border-top:1px solid #bfd1dd; border-left:0; } .scan-copy p,.priority-preview li,.state-copy p,.state-action { font-size:14px; } .homepage-state-panel { padding:15px; } .state-action { min-height:44px; } }
    @media (pointer:coarse) { .context-bar select { min-height:44px; } }
    @media (prefers-reduced-motion:reduce) { .ten-second-overview *, .homepage-state-panel * { scroll-behavior:auto!important; transition:none!important; animation:none!important; } }
    '''
    prelude = '''
  <script>
  (() => {
    'use strict';
    const allowed=__USABILITY_STATES__;
    const params=new URLSearchParams(location.search);
    let state=allowed.includes(params.get('demo_home_state'))?params.get('demo_home_state'):'ready'; let homepageResponseSequence=0; let staleResponseIgnoredCount=0;
    const nativeFetch=window.fetch.bind(window);
    const notify=payload=>{ window.__KMFA_USABILITY_LAST_PAYLOAD__=payload; window.dispatchEvent(new CustomEvent('kmfa:homepage-response',{detail:payload})); };
    window.fetch=async(input,init)=>{
      const raw=typeof input==='string'?input:input instanceof URL?input.href:input?.url||'';
      const url=new URL(raw,location.origin);
      if(url.origin===location.origin&&url.pathname==='/api/homepage'){
        const sequence=++homepageResponseSequence;
        url.searchParams.set('usability_state',state);
        const response=await nativeFetch(url.pathname+url.search,init);
        response.clone().json().then(payload=>{ if(sequence!==homepageResponseSequence){ staleResponseIgnoredCount+=1; return; } notify(payload); }).catch(()=>{});
        return response;
      }
      return nativeFetch(input,init);
    };
    const updateUrl=next=>{ const url=new URL(location.href); if(next==='ready')url.searchParams.delete('demo_home_state'); else url.searchParams.set('demo_home_state',next); history.replaceState(history.state,'',url.pathname+url.search+url.hash); };
    window.KMFA_HOMEPAGE_USABILITY_STATE={get:()=>state,set:async value=>{ state=allowed.includes(value)?value:'ready'; updateUrl(state); return window.KMFA_HOMEPAGE_TEST?.load(); },ignoredStaleResponses:()=>staleResponseIgnoredCount};
  })();
  </script>
'''
    postscript = '''
  <script>
  (() => {
    'use strict';
    const overview=document.querySelector('#ten-second-overview'); const scanSummary=document.querySelector('#scan-summary'); const scanStatus=document.querySelector('#scan-status'); const priority=document.querySelector('#priority-preview'); const statePanel=document.querySelector('#homepage-state-panel'); const stateLabel=document.querySelector('#homepage-state-label'); const stateTitle=document.querySelector('#homepage-state-title'); const stateReason=document.querySelector('#homepage-state-reason'); const stateImpact=document.querySelector('#homepage-state-impact'); const stateAction=document.querySelector('#homepage-state-action'); const homepageFeedback=document.querySelector('#homepage-feedback');
    const businessNodes=[document.querySelector('#business-summary-section'),document.querySelector('#homepage-columns'),document.querySelector('#portfolio-section'),document.querySelector('#homepage-disclaimer')].filter(Boolean);
    let lastPayload=null;
    const text=(tag,value,className='')=>{ const node=document.createElement(tag); node.textContent=value==null?'':String(value); if(className)node.className=className; return node; };
    const showBusiness=visible=>businessNodes.forEach(node=>node.hidden=!visible);
    const renderPriority=rows=>{ priority.replaceChildren(); rows.forEach(row=>{ const li=document.createElement('li'); li.append(text('span',row.rank,'priority-preview-rank'),text('span',row.title_zh)); priority.append(li); }); };
    const renderReady=payload=>{ statePanel.hidden=true; overview.hidden=false; homepageFeedback.hidden=false; showBusiness(true); scanSummary.textContent=payload.scan_summary_zh; scanStatus.textContent=payload.scan_status_zh; scanStatus.dataset.state=payload.scan_status; renderPriority(payload.priority_preview||[]); };
    const renderFault=payload=>{ const contract=payload.state_contract||{state_zh:'暂不可用',title_zh:payload.reason_zh||'当前不能显示经营摘要',reason_zh:'当前没有得到可核对的资料。',impact_zh:'页面没有展示未经确认的数字。',action_zh:'返回经营首页',action_route:'/overview'}; overview.hidden=true; statePanel.hidden=false; homepageFeedback.hidden=true; showBusiness(false); stateLabel.textContent=contract.state_zh; stateTitle.textContent=contract.title_zh; stateReason.textContent='原因：'+contract.reason_zh; stateImpact.textContent='影响：'+contract.impact_zh; stateAction.textContent=contract.action_zh; stateAction.href=contract.action_route; stateAction.dataset.route=contract.action_route; };
    const render=payload=>{ lastPayload=payload; if(payload?.allowed&&payload.usability_state==='ready'&&payload.scan_summary_available)renderReady(payload); else renderFault(payload||{}); };
    window.addEventListener('kmfa:homepage-response',event=>render(event.detail));
    stateAction.addEventListener('click',event=>{ if(lastPayload?.usability_state==='error'){ event.preventDefault(); event.stopImmediatePropagation(); window.KMFA_HOMEPAGE_USABILITY_STATE.set('ready'); } },true);
    window.KMFA_HOMEPAGE_USABILITY_TEST={setState:value=>window.KMFA_HOMEPAGE_USABILITY_STATE.set(value),state:()=>window.KMFA_HOMEPAGE_USABILITY_STATE.get(),snapshot:()=>lastPayload};
    if(window.__KMFA_USABILITY_LAST_PAYLOAD__)render(window.__KMFA_USABILITY_LAST_PAYLOAD__);
  })();
  </script>
'''
    prelude = prelude.replace("__USABILITY_STATES__", _json_for_html(list(kernel.USABILITY_STATES)))
    html = html.replace("<title>KMFA 经营明细 · 经营工作台</title>", "<title>KMFA 经营首页可用验收 · 经营工作台</title>")
    html = html.replace("  </style>", extra_css + "  </style>", 1)
    feedback_marker = '      <div id="homepage-feedback" class="homepage-feedback" role="status" aria-live="polite">正在加载经营摘要…</div>'
    if feedback_marker not in html:
        raise RuntimeError("S16-P1 homepage feedback insertion point drifted")
    html = html.replace(feedback_marker, scan_and_state + "\n" + feedback_marker, 1)
    html = html.replace(
        '<section class="homepage-section" aria-labelledby="business-summary-title">',
        '<section id="business-summary-section" class="homepage-section" aria-labelledby="business-summary-title">',
        1,
    )
    html = html.replace('<div class="homepage-columns">', '<div id="homepage-columns" class="homepage-columns">', 1)
    html = html.replace(
        '<section class="homepage-section portfolio-section" aria-labelledby="portfolio-title">',
        '<section id="portfolio-section" class="homepage-section portfolio-section" aria-labelledby="portfolio-title">',
        1,
    )
    html = html.replace(
        '<p class="demo-disclaimer">当前均为公开演示内容，用于验证页面和工作顺序，不代表任何真实公司的经营结论。</p>',
        '<p id="homepage-disclaimer" class="demo-disclaimer">当前均为公开演示内容，用于验证页面和工作顺序，不代表任何真实公司的经营结论。</p>',
        1,
    )
    homepage_script_marker = "  <script>\n  (() => {\n    'use strict';\n    const homepage=document.querySelector('#homepage-view');"
    if homepage_script_marker not in html:
        raise RuntimeError("S16-P1 homepage script insertion point drifted")
    html = html.replace(homepage_script_marker, prelude + homepage_script_marker, 1)
    html = html.replace("</body>", postscript + "</body>", 1)
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


def _permission_state(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result.update(
        {
            "usability_state": "permission",
            "state_contract": {
                "state_zh": "权限受限",
                "title_zh": "当前身份不能查看这个公司",
                "reason_zh": value.get("reason_zh", "当前身份没有所选公司权限。"),
                "impact_zh": "页面没有显示该公司的经营数字或重点事项。",
                "action_zh": "返回经营首页",
                "action_route": "/overview",
            },
            "external_human_participant_count": 0,
            "external_human_study_claimed": False,
        }
    )
    return result


class HomepageUsabilityHandler(p2_runtime.DrilldownHandler):
    server_version = "KMFAHomepageUsability/1.5"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/api/homepage":
            query = parse_qs(parsed.query)
            usability_state = query.get("usability_state", ["ready"])[0]
            if usability_state in kernel.FAULT_STATES:
                value = kernel.fault_state_response(usability_state)
                self._send_json(HTTPStatus(value["state_contract"]["http_status"]), value)
                return
            if usability_state != "ready":
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": "未知的首页演示状态。"})
                return
            try:
                value = homepage_kernel.homepage_snapshot(
                    user_id=query.get("user_id", ["demo-owner"])[0],
                    role_id=query.get("role_id", ["management"])[0],
                    company_id=query.get("company_id", ["demo-north"])[0],
                    period=query.get("period", ["2026-07"])[0],
                    data_state=query.get("data_state", ["complete"])[0],
                )
                value = kernel.enhance_homepage_snapshot(value) if value["allowed"] else _permission_state(value)
            except (homepage_kernel.HomepageError, kernel.HomepageUsabilityError) as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"allowed": False, "reason_zh": str(error)})
                return
            self._send_json(HTTPStatus.OK if value["allowed"] else HTTPStatus.FORBIDDEN, value)
            return
        if parsed.path.startswith("/api/") or parsed.path == "/favicon.ico":
            super().do_GET()
            return
        self._send(HTTPStatus.OK, render_html().encode("utf-8"), "text/html; charset=utf-8")


class HomepageUsabilityServer(p2_runtime.DrilldownServer):
    pass


def start_server(host: str = "127.0.0.1", port: int = 0) -> tuple[HomepageUsabilityServer, threading.Thread, str]:
    server = HomepageUsabilityServer((host, port), HomepageUsabilityHandler)
    thread = threading.Thread(target=server.serve_forever, name="kmfa-v015-s16p3-homepage-usability", daemon=True)
    thread.start()
    address, actual_port = server.server_address[:2]
    return server, thread, f"http://{address}:{actual_port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S16-P3 首页人类可用验收公开演示")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = HomepageUsabilityServer((args.host, args.port), HomepageUsabilityHandler)
    print(f"KMFA S16-P3 首页可用验收：http://{args.host}:{server.server_address[1]}/overview", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
