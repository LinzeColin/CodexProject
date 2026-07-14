#!/usr/bin/env python3
"""
KMFA HTML human-flow audit.
Purpose: open local HTML files, click visible buttons/links, type in search inputs, capture console errors,
and report whether each user-facing control produces visible feedback or a safe local navigation.
"""
from __future__ import annotations
import argparse, csv, os, sys, hashlib, threading, socketserver, http.server, time
from pathlib import Path
from urllib.parse import urlparse, unquote, quote
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

CHROMIUM = os.environ.get("KMFA_CHROMIUM", "/usr/bin/chromium")

def file_url(path: Path, root: Path|None=None, base_url: str|None=None) -> str:
    if root is not None and base_url is not None:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
        return base_url.rstrip('/') + '/' + quote(rel)
    return path.resolve().as_uri()

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def start_server(root: Path):
    handler = lambda *a, **kw: QuietHandler(*a, directory=str(root), **kw)
    httpd = socketserver.TCPServer(('127.0.0.1', 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, f'http://127.0.0.1:{port}'

def norm_text(s: str, n: int = 90) -> str:
    return " ".join((s or "").split())[:n]

def safe_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def audit_file(browser, html_path: Path, root: Path, base_url: str|None=None):
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
    console_errors=[]
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type in ("error", "warning") else None)
    page.on("pageerror", lambda exc: console_errors.append(str(exc)))
    results=[]
    page.set_content(html_path.read_text(encoding="utf-8", errors="ignore"), wait_until="load")
    page.wait_for_timeout(120)
    title=page.title()
    # links: verify local href exists or is empty/hash safe
    link_count=page.locator("a").count()
    for i in range(link_count):
        loc=page.locator("a").nth(i)
        try:
            href=loc.get_attribute("href") or ""
            text=norm_text(loc.inner_text(timeout=1000))
            ok=True; reason="local link ok"
            if href.startswith("http"):
                ok=True; reason="external link not clicked"
            elif href.startswith("#") or href.strip()=="":
                ok=True; reason="hash/empty link"
            else:
                target=(html_path.parent / unquote(href.split('#')[0])).resolve()
                ok=target.exists()
                reason="exists" if ok else f"missing target: {target}"
            results.append([html_path.name,title,"link",i,text,href,"PASS" if ok else "FAIL",reason,"; ".join(console_errors[-3:])])
        except Exception as e:
            results.append([html_path.name,title,"link",i,"","","FAIL",f"link inspect error: {e}","; ".join(console_errors[-3:])])
    # inputs: type and observe body or visible rows change
    inp_count=page.locator("input:visible").count()
    for i in range(inp_count):
        loc=page.locator("input:visible").nth(i)
        try:
            before=page.locator("body").inner_text(timeout=1000)
            loc.fill("金蝶")
            page.wait_for_timeout(120)
            after=page.locator("body").inner_text(timeout=1000)
            ok = before != after or (page.evaluate("document.body.dataset.lastAction || ''") != "")
            results.append([html_path.name,title,"input",i,norm_text(loc.get_attribute('placeholder') or ''),"type=金蝶","PASS" if ok else "WARN","input accepted; feedback expected" if ok else "input accepts text but no visible feedback detected","; ".join(console_errors[-3:])])
        except Exception as e:
            results.append([html_path.name,title,"input",i,"","","FAIL",f"input interaction error: {e}","; ".join(console_errors[-3:])])
    # buttons: click visible buttons one by one; use a fresh page so inline scripts do not redeclare variables.
    page.close()
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type in ("error", "warning") else None)
    page.on("pageerror", lambda exc: console_errors.append(str(exc)))
    page.set_content(html_path.read_text(encoding="utf-8", errors="ignore"), wait_until="load")
    page.wait_for_timeout(120)
    clicked=0
    max_clicks=min(page.locator("button:visible").count(), 80)
    for i in range(max_clicks):
        try:
            # Recompute visible buttons each time. If index vanished, break.
            count=page.locator("button:visible").count()
            if i>=count: break
            loc=page.locator("button:visible").nth(i)
            label=norm_text(loc.inner_text(timeout=1000)) or norm_text(loc.get_attribute("aria-label") or loc.get_attribute("title") or "")
            before_text=page.locator("body").inner_text(timeout=1000)
            before_url=page.url
            before_action=page.evaluate("document.body.dataset.lastAction || ''")
            before_panel=page.locator(".panel.open").count()
            # handle downloads gracefully only for explicit export/download buttons
            try:
                if any(k in label for k in ("导出", "下载")):
                    try:
                        with page.expect_download(timeout=1200) as download_info:
                            loc.click(timeout=2500)
                        _ = download_info.value.suggested_filename
                    except PlaywrightTimeoutError:
                        loc.click(timeout=2500)
                else:
                    loc.click(timeout=2500)
            except Exception as click_e:
                results.append([html_path.name,title,"button",i,label,"click","FAIL",f"click failed: {click_e}","; ".join(console_errors[-3:])])
                continue
            page.wait_for_timeout(160)
            after_text=page.locator("body").inner_text(timeout=1000)
            after_url=page.url
            after_action=page.evaluate("document.body.dataset.lastAction || ''")
            after_panel=page.locator(".panel.open").count()
            if after_panel:
                page.evaluate("document.querySelectorAll('.panel.open,.overlay.open').forEach(e=>e.classList.remove('open'))")
            changed = (before_text != after_text) or (before_url != after_url) or (before_action != after_action) or (before_panel != after_panel)
            status="PASS" if changed else "WARN"
            reason="visible feedback / navigation / state change" if changed else "no visible state change detected"
            results.append([html_path.name,title,"button",i,label,"click",status,reason,"; ".join(console_errors[-3:])])
            clicked+=1
        except Exception as e:
            results.append([html_path.name,title,"button",i,"","click","FAIL",f"button audit error: {e}","; ".join(console_errors[-3:])])
    if console_errors:
        results.append([html_path.name,title,"console",-1,"console/errors","","WARN","console warnings/errors captured","; ".join(console_errors[:10])])
    page.close()
    return results

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--glob", default="*.html")
    args=ap.parse_args()
    htmls=sorted(args.root.rglob(args.glob))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    httpd=None; base_url=None
    all_rows=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True, executable_path=CHROMIUM, args=["--no-sandbox","--disable-dev-shm-usage"])
        for hp in htmls:
            try:
                all_rows.extend(audit_file(browser,hp,args.root,base_url))
            except Exception as e:
                all_rows.append([hp.name,"","file",-1,"","","FAIL",f"file audit crashed: {e}",""])
        browser.close()
    if httpd: httpd.shutdown()
    with args.out.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f)
        w.writerow(["file","title","control_type","index","label","action","status","reason","console"])
        w.writerows(all_rows)
    total=len(all_rows); fail=sum(1 for r in all_rows if r[6]=="FAIL"); warn=sum(1 for r in all_rows if r[6]=="WARN"); passed=sum(1 for r in all_rows if r[6]=="PASS")
    print(f"HTML audit complete: files={len(htmls)} rows={total} pass={passed} warn={warn} fail={fail} out={args.out}")
    return 1 if fail else 0
if __name__=="__main__":
    raise SystemExit(main())
