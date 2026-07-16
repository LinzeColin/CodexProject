#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P02-T048 attachment discovery + readback driver (dev-env, live, run once).

Gathers REAL attachment URLs from real A0 sources (stats.gov.cn monthly statistical
releases carry .xlsx data tables; gov.cn policy pages carry .zip/.pdf/.doc bundles),
fetches each, and verifies it is genuinely READABLE -- HTTP 200 + non-empty bytes +
recognized file magic (not a 404 / HTML error page) + a real sha256. Writes the cached
readback to attachment_readback.json so the deterministic verifier needs no network.

Not the worker: runs from the dev environment -> 0 cloud cost, DIR-007 unaffected.
"""
import urllib.request, re, ssl, json, time, hashlib, pathlib, sys
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120 Safari/537.36"}
T0 = time.time()
DISCOVER_DEADLINE = T0 + 240     # phase 1: collect candidate URLs
READBACK_DEADLINE = T0 + 520     # phase 2: fetch + verify (separate budget)
DEADLINE = DISCOVER_DEADLINE     # back-compat for get_text callers
TARGET = 100
STATS_INDEX_PAGES = 30

# magic-byte signatures that prove a real, readable binary office/pdf/archive artifact
MAGIC = {
    b"PK\x03\x04": "zip/ooxml",        # .xlsx .docx .pptx .zip (OOXML is a zip)
    b"%PDF": "pdf",
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": "ole/msoffice",  # legacy .doc .xls
    b"\xd7\xcd\xc6\x9a": "wmf",
}
def magic_kind(b: bytes):
    for sig, k in MAGIC.items():
        if b.startswith(sig):
            return k
    return None

def http_get(u, cap=8_000_000, t=12):
    req = urllib.request.Request(u, headers=UA)
    r = urllib.request.urlopen(req, timeout=t, context=ctx)
    data = r.read(cap)
    return r.status, data, r.geturl(), dict(r.headers)

def get_text(u, t=12, cap=600_000):
    try:
        st, data, fin, _ = http_get(u, cap=cap, t=t)
        return st, data.decode("utf-8", "ignore"), fin
    except Exception as e:
        return None, f"ERR {type(e).__name__}", u

def norm(base, x):
    if x.startswith("http"): return x
    if x.startswith("//"):   return "https:" + x
    if x.startswith("/"):    return "https://" + base.split("/")[2] + x
    if x.startswith("./"):   return base.rsplit("/", 1)[0] + "/" + x[2:]
    return base.rsplit("/", 1)[0] + "/" + x

ATT_RE = re.compile(r'(?:href|src)="([^"]+\.(?:xlsx?|docx?|pdf|wps|zip))"', re.I)

def discover_stats(pages=STATS_INDEX_PAGES):
    """stats.gov.cn zxfb monthly releases -> article pages -> .xlsx data tables."""
    urls = []
    idxs = ["https://www.stats.gov.cn/sj/zxfb/index.html"] + \
           [f"https://www.stats.gov.cn/sj/zxfb/index_{i}.html" for i in range(1, pages)]
    arts = []
    def idx_probe(iu):
        st, h, _ = get_text(iu, t=10)
        if st != 200: return []
        return ["https://www.stats.gov.cn/sj/zxfb/" + a
                for a in re.findall(r'href="\.?/?((?:\d{6})/t\d{8}_\d+\.html)"', h)]
    with ThreadPoolExecutor(max_workers=12) as ex:
        for res in ex.map(idx_probe, idxs):
            arts += res
    arts = list(dict.fromkeys(arts))
    def probe(au):
        if time.time() > DISCOVER_DEADLINE: return []
        st, h, fin = get_text(au, t=10)
        if st != 200: return []
        out = []
        for x in dict.fromkeys(ATT_RE.findall(h)):
            nu = norm(fin, x)
            # prefer the direct /sj/zxfb/... form over the /protect/ mirror (404s; same bytes)
            if "/protect/" in nu: continue
            m = re.search(r'/(\d{6})/', au)
            out.append({"url": nu, "source_id": "stats-gov", "month": (m.group(1)[:4] + "-" + m.group(1)[4:6]) if m else None, "from_page": au})
        return out
    with ThreadPoolExecutor(max_workers=16) as ex:
        for res in ex.map(probe, arts):
            urls += res
    # de-dup by url
    seen = set(); uniq = []
    for a in urls:
        if a["url"] in seen: continue
        seen.add(a["url"]); uniq.append(a)
    return uniq

def discover_from_corpus():
    """Attachments embedded in our already-backfilled A0 doc pages (Wave 1 + Wave 2)."""
    out = []
    for ev in ["ADP-S4-P02-T046/wave1_backfill_docs.json", "ADP-S4-P02-T047/wave2_backfill_docs.json"]:
        p = V01 / "evidence" / ev
        if not p.exists(): continue
        for d in json.loads(p.read_text(encoding="utf-8")):
            u = d.get("url", "")
            if not u.startswith("http"): continue
            st, h, fin = get_text(u)
            if st != 200: continue
            for x in dict.fromkeys(ATT_RE.findall(h)):
                out.append({"url": norm(fin, x), "source_id": d.get("source_id"), "month": d.get("month"), "from_page": u})
    return out

def readback(a):
    """Fetch one attachment and verify it is a genuinely readable binary artifact."""
    rec = dict(a); rec.update(http_status=None, bytes=0, sha256=None, magic=None, readable=False, err=None)
    if time.time() > READBACK_DEADLINE:
        rec["err"] = "deadline"; return rec
    try:
        st, data, fin, hdr = http_get(a["url"])
        rec["http_status"] = st; rec["bytes"] = len(data)
        rec["sha256"] = hashlib.sha256(data).hexdigest()
        rec["magic"] = magic_kind(data)
        rec["content_type"] = hdr.get("Content-Type", "")
        rec["ext"] = a["url"].rsplit(".", 1)[-1].lower()
        # readable == real file: 200 + non-trivial bytes + recognized binary magic (not HTML error page)
        rec["readable"] = bool(st == 200 and len(data) > 64 and rec["magic"] is not None)
    except Exception as e:
        rec["err"] = f"{type(e).__name__}: {e}"
    return rec

def main():
    cand = discover_from_corpus() + discover_stats()
    # de-dup by url
    seen = set(); uniq = []
    for a in cand:
        if a["url"] in seen: continue
        seen.add(a["url"]); uniq.append(a)
    print(f"discovered {len(uniq)} distinct candidate attachment URLs (t={time.time()-T0:.0f}s)")
    results = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        for r in ex.map(readback, uniq):
            results.append(r)
    readable = [r for r in results if r["readable"]]
    distinct = {r["sha256"] for r in readable}
    print(f"attempted {len(results)}, readable {len(readable)}, distinct-sha256 {len(distinct)} (t={time.time()-T0:.0f}s)")
    out = {
        "task": "ADP-S4-P02-T048",
        "generated_from": "dev-env live fetch (not the worker; 0 cloud cost)",
        "target_readable": TARGET,
        "distinct_candidates": len(uniq),
        "attempted": len(results),
        "readable_count": len(readable),
        "by_source": {},
        "by_magic": {},
        "attachments": results,
    }
    for r in readable:
        out["by_source"][r["source_id"]] = out["by_source"].get(r["source_id"], 0) + 1
        out["by_magic"][r["magic"]] = out["by_magic"].get(r["magic"], 0) + 1
    out["distinct_readable_sha256"] = len(distinct)
    (HERE / "attachment_readback.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("by_source:", out["by_source"], "| by_magic:", out["by_magic"])
    print(f"WROTE attachment_readback.json ; readable={len(readable)} distinct={len(distinct)}")

if __name__ == "__main__":
    main()
