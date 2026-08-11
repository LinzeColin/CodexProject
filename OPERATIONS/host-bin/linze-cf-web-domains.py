#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出 linzezhang.com 下所有**网站类**子域,给验收脚本当域名清单用。

单独成文件而不是内嵌进 shell:2026-08-11 第一版把这段 python 用 `python3 -c '...'`
嵌在 bash 里,外层又套了 ssh 的引号 —— 引号被逐层吞掉,脚本静默取不到清单、
退回内置列表。**嵌套引号是这类脚本最常见的静默失效点**,拆成文件就没有这个问题。

排除 DKIM / 邮件用记录(_domainkey、bounces.、track.、send.):它们不是 HTTP 服务,
拿 curl 去打必然 000,会制造永远修不掉的假红。
"""
import json
import os
import sys
import urllib.request

EXCLUDE = ("_domainkey", "bounces.", "track.", "send.")


def main():
    tok, zone = os.environ.get("CF_API_TOKEN"), os.environ.get("CF_ZONE_ID")
    if not tok or not zone:
        return 1
    url = ("https://api.cloudflare.com/client/v4/zones/%s/dns_records?per_page=100" % zone)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
    except Exception:
        return 1
    if not d.get("success"):
        return 1
    names = {
        r["name"] for r in (d.get("result") or [])
        if r.get("type") in ("A", "AAAA", "CNAME")
        and r.get("name", "").endswith("linzezhang.com")
        and not any(b in r["name"] for b in EXCLUDE)
    }
    if not names:
        return 1
    print("\n".join(sorted(names)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
