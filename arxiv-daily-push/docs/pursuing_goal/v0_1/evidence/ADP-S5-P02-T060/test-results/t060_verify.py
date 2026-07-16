#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P02-T060 acceptance: exact + structured retrieval.

Acceptance (TASK_INDEX): 100 条精确标识第一结果命中率 100%；过滤结果与 SQL 基准一致。
Deterministic. (1) 100 exact identifiers each return the correct document as the FIRST result (100%
hit rate). (2) structured_filter results are byte-identical to a real SQL baseline (an in-memory
sqlite3 query with the equivalent WHERE clause) across a battery of facet/date-range queries.
"""
import sys, json, sqlite3, itertools, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import exact_search as ES

T060 = V01 / "evidence" / "ADP-S5-P02-T060"
docs = json.loads((T060 / "corpus.json").read_text(encoding="utf-8"))
idx = ES.build_index(docs)
fails = []

# --- 1) 100 exact identifiers -> first-result hit rate 100% -----------------------------------
ids = [d["doc_number"] for d in docs][:100]
hits = 0
for ident, expect in zip(ids, docs[:100]):
    res = ES.exact_lookup(idx, ident)
    if res and res[0]["doc_id"] == expect["doc_id"]:
        hits += 1
print(f"exact identifiers={len(ids)} first_result_hits={hits} rate={hits/len(ids):.4f}")
if hits != len(ids):
    fails.append(f"first-result hit rate {hits}/{len(ids)} != 100%")
# normalized-form robustness: a spaced + case-FLIPPED DOI (DOIs are case-insensitive) still hits.
# use a DOI that genuinely contains ASCII letters so the case-fold is actually exercised.
doi_doc = next(d for d in docs if d.get("doi") and any(c.isalpha() and c.isascii() for c in d["doi"]))
flipped = "  " + doi_doc["doi"].swapcase() + " "
if not any(c.isalpha() and c.isascii() for c in doi_doc["doi"]):
    fails.append("chosen DOI has no ASCII letters -> case-fold check is a no-op")
if (ES.exact_lookup(idx, flipped) or [{}])[0].get("doc_id") != doi_doc["doc_id"]:
    fails.append("normalized exact lookup (spaced + case-flipped DOI) missed")
# and a genuinely different DOI must NOT resolve to it (no false hit from over-normalization)
if ES.exact_lookup(idx, doi_doc["doi"] + "9999"):
    fails.append("a non-existent DOI resolved to a document (false exact hit)")

# --- 2) structured_filter == SQL baseline (in-memory sqlite3) --------------------------------
con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE d (doc_id TEXT, doc_number TEXT, agency TEXT, region TEXT, doc_date TEXT, status TEXT)")
con.executemany("INSERT INTO d VALUES (?,?,?,?,?,?)",
                [(d["doc_id"], d.get("doc_number"), d.get("agency"), d.get("region"),
                  d.get("doc_date"), d.get("status")) for d in docs])

def sql_baseline(agency=None, region=None, status=None, date_from=None, date_to=None):
    where, args = [], []
    for col, val in (("agency", agency), ("region", region), ("status", status)):
        if val is not None:
            where.append(f"{col}=?"); args.append(val)
    if date_from is not None:
        where.append("doc_date>=?"); args.append(date_from)
    if date_to is not None:
        where.append("doc_date<=?"); args.append(date_to)
    sql = "SELECT doc_id FROM d" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY doc_id"
    return [r[0] for r in con.execute(sql, args).fetchall()]

# battery of queries: single facets, combinations, date ranges
agencies = sorted({d["agency"] for d in docs})
regions = sorted({d["region"] for d in docs})
statuses = sorted({d["status"] for d in docs})
queries = []
for a in [None] + agencies:
    for st in [None] + statuses:
        queries.append({"agency": a, "status": st})
# date-range queries anchored on REAL corpus dates so they return >0 rows and genuinely exercise the
# inclusive [date_from, date_to] boundaries (a date off-by-one would surface as a SQL mismatch here)
real_dates = sorted({d["doc_date"] for d in docs})
for r in regions:
    queries.append({"region": r, "date_from": real_dates[0], "date_to": real_dates[len(real_dates)//2]})
for anchor in [real_dates[0], real_dates[len(real_dates)//2], real_dates[-1]]:
    queries.append({"date_from": anchor, "date_to": anchor})        # single-day: inclusive boundary
    queries.append({"date_from": anchor})                            # open-ended lower bound
    queries.append({"date_to": anchor})                              # open-ended upper bound
queries.append({"agency": agencies[0], "region": regions[0], "status": statuses[0],
                "date_from": real_dates[0], "date_to": real_dates[-1]})

mismatches = 0
for q in queries:
    mine = [d["doc_id"] for d in ES.structured_filter(docs, **q)]
    base = sql_baseline(**q)
    if mine != base:
        mismatches += 1
        if mismatches <= 3:
            print(f"  MISMATCH q={q}: mine={len(mine)} base={len(base)}")
print(f"structured queries={len(queries)} sql_baseline_mismatches={mismatches}")
if mismatches != 0:
    fails.append(f"{mismatches} structured queries disagree with the SQL baseline")
# the battery must be non-trivial (some queries return >0 and some facet actually filters)
if not any(ES.structured_filter(docs, agency=agencies[0]) for _ in [0]):
    fails.append("agency filter returns nothing -> battery is vacuous")
if len(ES.structured_filter(docs, agency=agencies[0])) == len(docs):
    fails.append("agency filter did not actually filter (returns whole corpus)")
# the inclusive date boundary must be genuinely exercised: a single-day query on a real date returns >0
if not ES.structured_filter(docs, date_from=real_dates[0], date_to=real_dates[0]):
    fails.append("single-day inclusive-boundary query returns nothing -> boundary is untested")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
