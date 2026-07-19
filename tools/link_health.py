#!/usr/bin/env python3
"""STAGE-15.4 死链巡检: 探测 home 卡片全部 liveUrl/fallbackUrl, 报告不可达项。
用法: python3 tools/link_health.py [--projects <path|url>] [--json]
退出码: 0 全通; 1 存在死链(供 cron 告警)"""
import argparse, json, sys, urllib.request, urllib.error

DEFAULT_SRC = "https://raw.githubusercontent.com/LinzeColin/LinzeHomeHub/main/src/data/projects.json"
UA = "Mozilla/5.0 (linze-link-health)"

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def probe(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        # 302 到 Cloudflare Access 登录 = 受保护但存活, 视为健康
        return e.code, e.reason
    except Exception as e:
        return 0, type(e).__name__

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", default=DEFAULT_SRC)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    raw = fetch(a.projects) if a.projects.startswith("http") else open(a.projects, "rb").read()
    cards = json.loads(raw)
    results, bad = [], 0
    for c in cards:
        for field in ("liveUrl", "fallbackUrl"):
            u = c.get(field)
            if not u:
                continue
            code, err = probe(u)
            # 2xx/3xx 健康; 401/403 = 受鉴权保护但存活
            ok = (200 <= code < 400) or code in (401, 403)
            if not ok:
                bad += 1
            results.append({"id": c.get("id"), "field": field, "url": u, "code": code, "ok": ok, "err": err})
    if a.json:
        print(json.dumps({"checked": len(results), "dead": bad, "results": results}, ensure_ascii=False, indent=1))
    else:
        for r in results:
            print(("  OK  " if r["ok"] else "  DEAD") + f" [{r['code']:>3}] {r['id']}.{r['field']} {r['url']}")
        print(f"\n合计 {len(results)} 条, 死链 {bad} 条")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
