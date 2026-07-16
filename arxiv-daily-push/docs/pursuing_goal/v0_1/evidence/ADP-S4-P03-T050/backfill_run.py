#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P03-T050 live batched provincial backfill (dev-env; run once).

Runs the T050 orchestrator over real provincial portals via the T049 A1 family, from the DEV
environment (not the worker -> 0 cloud cost, DIR-007 unaffected). Two cohort batches; each must pass
before the next; a real unreachable province (Guangdong, TLS/connection-blocked from this env) is
included to demonstrate failed-province ISOLATION. Idempotency is re-checked by running twice.
Writes province_backfill_docs.json + cohort/coverage/cost/health reports.
"""
import sys, ssl, json, hashlib, pathlib, urllib.request
HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import official_connector as OC
import adapter_a1_province as A
import province_backfill as PB

FETCHED_AT = "2026-07-16T00:00:00+10:00"
_ctx = ssl.create_default_context(); _ctx.check_hostname = False; _ctx.verify_mode = ssl.CERT_NONE
_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/120 Safari/537.36"}

class LiveFetcher:
    """dev-env fetch (browser UA; relaxed TLS for reachability from a server env). Never the worker."""
    def get(self, url, fetched_at):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=15, context=_ctx)
            body = r.read(3_000_000)
            return OC.FetchResult(url, r.status, r.headers.get("Content-Type", ""), body,
                                  hashlib.sha256(body).hexdigest(), fetched_at, 200 <= r.status < 300 and len(body) > 0)
        except Exception:
            return OC.FetchResult(url, 0, "", b"", "", fetched_at, False)

# a real but blocked province (Guangdong), included only to prove failed-province isolation.
GUANGDONG = A.SiteProfile(
    source_id="guangdong-gov", province="广东", template_family="art-cms",
    base_url="https://www.gd.gov.cn", listing_url="https://www.gd.gov.cn/gkmlpt/index.html",
    article_url_re=r'href="(https?://www\.gd\.gov\.cn/[^"]+\.html)"',
    docnum_re=r"(粤[一-龥]{0,6}〔\d{4}〕第?\s*\d+\s*号)",
    title_hook="strip_leading_labels", title_hook_args=(2,), host_org="广东省人民政府")

# cohort plan: batch 0 = art-cms (jiangsu, shandong, + blocked guangdong); batch 1 = beijing-zhengce
COHORT = [
    {"batch": 0, "source_id": "jiangsu-gov", "profile": A.PROFILES["jiangsu-gov"]},
    {"batch": 0, "source_id": "shandong-gov", "profile": A.PROFILES["shandong-gov"]},
    {"batch": 0, "source_id": "guangdong-gov", "profile": GUANGDONG},
    {"batch": 1, "source_id": "beijing-gov", "profile": A.PROFILES["beijing-gov"]},
]

def connector_of(m):
    return A.A1ProvinceConnector(m["profile"], LiveFetcher())

def main():
    batches = PB.plan_batches(COHORT)
    run = PB.orchestrate(batches, connector_of, max_docs=3, fetched_at=FETCHED_AT)
    run2 = PB.orchestrate(batches, connector_of, max_docs=3, fetched_at=FETCHED_AT)  # idempotency
    ids1 = {d["canonical_id"] for b in run["batches"] for p in b["provinces"] for d in p["docs"]}
    ids2 = {d["canonical_id"] for b in run2["batches"] for p in b["provinces"] for d in p["docs"]}
    idempotent = ids1 == ids2
    cov = PB.coverage_report(run)

    (HERE / "province_cohorts.json").write_text(json.dumps(
        {"batches": [[m["source_id"] for m in b] for b in batches],
         "families": {m["source_id"]: m["profile"].template_family for m in COHORT}},
        ensure_ascii=False, indent=2), encoding="utf-8")
    docs = [d for b in run["batches"] for p in b["provinces"] for d in p["docs"]]
    (HERE / "province_backfill_docs.json").write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / "coverage_report.json").write_text(json.dumps({
        "run_summary": {"completed_batches": run["completed_batches"], "halted_at": run["halted_at"],
                        "total_docs": run["total_docs"], "distinct_canonical_ids": len(ids1),
                        "idempotent_rerun_no_new": idempotent},
        "gates": [{"batch": b["batch"], "source_ids": b["source_ids"], "provinces_ok": b.get("provinces_ok"),
                   "gate_passed": b["gate_passed"]} for b in run["batches"]],
        "coverage": cov["by_source_month"], "isolated_failures": run["isolated_failures"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / "cost_report.json").write_text(json.dumps({
        "note": "dev-env fetch (not the worker) -> 0 cloud cost; unknown != 0",
        "production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0,
        "r2_bytes": 0, "r2_ops": 0, "model_calls": 0,
        "human_maintenance": "dev-env batched province backfill"}, ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / "health_report.json").write_text(json.dumps({
        "provinces": [{"source_id": p["source_id"], "reachable_parsed": p["ok"] and bool(p["docs"]),
                       "docs": len(p["docs"]), "error": p["error"]}
                      for b in run["batches"] for p in b["provinces"]],
        "isolated": run["isolated_failures"]}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"completed_batches={run['completed_batches']} halted_at={run['halted_at']} total_docs={run['total_docs']}")
    print(f"distinct_canonical_ids={len(ids1)} idempotent_rerun_no_new={idempotent}")
    print(f"isolated_failures={run['isolated_failures']}")
    for b in run["batches"]:
        print(f"  batch {b['batch']} {b['source_ids']} -> provinces_ok={b.get('provinces_ok')} gate={b['gate_passed']}")

if __name__ == "__main__":
    main()
