#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P02-T048 attachment readback TOP-UP (dev-env).

The first pass verified 93/150 candidates readable; the remaining failures were dominated by
transient SSL handshake timeouts under high concurrency (real .xlsx that simply timed out).
This retries only the not-yet-readable candidates at LOW concurrency with a longer timeout and
one retry, drops permanent /protect 404 mirrors, and merges recovered readables back into
attachment_readback.json. Deterministic checks stay in a0_qa_gate.py; this only refreshes the cache.
"""
import urllib.request, ssl, json, time, hashlib, pathlib
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120 Safari/537.36"}
MAGIC = {b"PK\x03\x04": "zip/ooxml", b"%PDF": "pdf",
         b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": "ole/msoffice", b"\xd7\xcd\xc6\x9a": "wmf"}
def magic_kind(b):
    for sig, k in MAGIC.items():
        if b.startswith(sig): return k
    return None

def readable_rec(a):
    return bool(a.get("http_status") == 200 and (a.get("bytes") or 0) > 64
                and a.get("magic") and isinstance(a.get("sha256"), str) and len(a["sha256"]) == 64)

def fetch(a):
    rec = dict(a)
    for attempt in range(2):
        try:
            r = urllib.request.urlopen(urllib.request.Request(a["url"], headers=UA), timeout=22, context=ctx)
            data = r.read(8_000_000)
            rec.update(http_status=r.status, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                       magic=magic_kind(data), content_type=r.headers.get("Content-Type", ""), err=None)
            rec["readable"] = bool(r.status == 200 and len(data) > 64 and rec["magic"] is not None)
            if rec["readable"]:
                return rec
        except Exception as e:
            rec["err"] = f"{type(e).__name__}: {e}"
        time.sleep(0.5)
    rec["readable"] = readable_rec(rec)
    return rec

def main():
    data = json.loads((HERE / "attachment_readback.json").read_text(encoding="utf-8"))
    atts = data["attachments"]
    todo = [a for a in atts if not readable_rec(a) and "/protect/" not in a["url"]]
    print(f"loaded {len(atts)} records, {sum(1 for a in atts if readable_rec(a))} already readable, retrying {len(todo)}")
    recovered = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        for rec in ex.map(fetch, todo):
            if rec["readable"]:
                recovered[rec["url"]] = rec
    # merge
    out = []
    for a in atts:
        out.append(recovered.get(a["url"], a))
    readable = [a for a in out if readable_rec(a)]
    distinct = {a["sha256"] for a in readable}
    by_source, by_magic = {}, {}
    for a in readable:
        by_source[a["source_id"]] = by_source.get(a["source_id"], 0) + 1
        by_magic[a["magic"]] = by_magic.get(a["magic"], 0) + 1
    data.update(attachments=out, readable_count=len(readable), distinct_readable_sha256=len(distinct),
                by_source=by_source, by_magic=by_magic)
    (HERE / "attachment_readback.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"recovered {len(recovered)}; now readable={len(readable)} distinct={len(distinct)}")
    print("by_source:", by_source, "| by_magic:", by_magic)

if __name__ == "__main__":
    main()
