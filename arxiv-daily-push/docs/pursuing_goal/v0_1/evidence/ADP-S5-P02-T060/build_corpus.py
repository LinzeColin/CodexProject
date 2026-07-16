#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P02-T060 -- deterministic test corpus + exact-lookup report (>=100 exact identifiers)."""
import sys, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import exact_search as ES

# deterministic corpus: 120 docs across agencies/regions/dates/statuses, each with a unique exact id
AGENCIES = [("江苏省人民政府办公厅", "江苏", "苏政办函"), ("山东省科学技术厅", "山东", "鲁科字"),
            ("北京市科学技术委员会", "北京", "京科发"), ("国务院办公厅", "中央", "国办发"),
            ("国家发展和改革委员会", "中央", "发改")]
STATUSES = ["现行有效", "已修订", "已废止"]

def build_corpus():
    docs = []
    n = 0
    for ai, (agency, region, prefix) in enumerate(AGENCIES):
        for i in range(24):                                  # 5 * 24 = 120 docs
            n += 1
            year = 2016 + (i % 11)
            month = 1 + (i % 12)
            day = 1 + (i % 28)
            docnum = f"{prefix}〔{year}〕{100 + i}号"
            doc = {"doc_id": f"doc-{n:03d}", "doc_number": docnum, "agency": agency, "region": region,
                   "doc_date": f"{year}-{month:02d}-{day:02d}", "status": STATUSES[i % 3],
                   # DOIs carry ASCII letters (case-insensitive per the DOI spec) for the shandong subset
                   "doi": f"10.1016/J.STATS.{year}.{100 + i}" if ai == 1 else None}
            docs.append(doc)
    return docs

def main():
    docs = build_corpus()
    idx = ES.build_index(docs)
    # 100 exact-identifier lookups (docnum for all; DOI for the ones that have it)
    ids = [d["doc_number"] for d in docs][:100]
    hits = 0
    for ident, expect in [(i, d) for i, d in zip(ids, docs[:100])]:
        res = ES.exact_lookup(idx, ident)
        if res and res[0]["doc_id"] == expect["doc_id"]:
            hits += 1
    # also verify DOI lookups (shandong docs)
    doi_docs = [d for d in docs if d.get("doi")]
    doi_hits = sum(1 for d in doi_docs if (ES.exact_lookup(idx, d["doi"]) or [{}])[0].get("doc_id") == d["doc_id"])
    report = {
        "task": "ADP-S5-P02-T060",
        "corpus_docs": len(docs),
        "exact_identifier_lookups": len(ids), "first_result_hits": hits,
        "first_result_hit_rate": round(hits / len(ids), 4),
        "doi_lookups": len(doi_docs), "doi_hits": doi_hits,
        "facets": {"agencies": len(AGENCIES), "statuses": len(STATUSES)},
        "cost": {"production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0, "r2_bytes": 0,
                 "r2_ops": 0, "model_calls": 0, "human_maintenance": "exact-search + corpus authoring"},
        "deployment": "NOT_DEPLOYED",
    }
    (HERE / "corpus.json").write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / "search_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"corpus={len(docs)} exact_lookups={len(ids)} first_result_hits={hits} rate={report['first_result_hit_rate']} "
          f"doi_hits={doi_hits}/{len(doi_docs)}")

if __name__ == "__main__":
    main()
