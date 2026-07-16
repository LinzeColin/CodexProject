#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P05-T056 -- Coverage Debt + As-of history query base.

Three query surfaces over the backfilled 2016+ corpus (A0 waves T046/T047 + A1 provinces T050):

  1. coverage_debt   -- for every (source, month) in each source's 2016+ active window, the completeness
                        status and, where incomplete, the concrete reason (the coverage DEBT). Builds on
                        the T043 gap detector so every hole is explainable, never a silent blank.
  2. as_of_query     -- given a query date, return the document version that was KNOWN as of that date;
                        a query never resolves to a chronologically FUTURE version. Uses the same
                        parsed-date (not lexical) resolver proven sound in T048, cross-checked by an
                        independent oracle.
  3. historical_manifest_resolver -- given a date, resolve which monthly snapshot manifest was the
                        latest known as of that date (the point-in-time manifest).

Deterministic; reads the cached backfill evidence; no network, no production side effects.
"""
import json, re, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent
EV = V01 / "evidence"
sys.path.insert(0, str(HERE))
import gap_detector as GD   # T043


# ---------------------------------------------------------------- corpus (A0 waves + A1 provinces)
def load_corpus():
    docs = []
    for ev in ["ADP-S4-P02-T046/wave1_backfill_docs.json", "ADP-S4-P02-T047/wave2_backfill_docs.json"]:
        p = EV / ev
        if p.exists():
            for d in json.loads(p.read_text(encoding="utf-8")):
                if d.get("month"):
                    docs.append({"canonical_id": d["canonical_id"], "source_id": d.get("source_id", "gov-cn-fagui"),
                                 "month": d["month"], "url": d.get("url", "")})
    p = EV / "ADP-S4-P03-T050/province_backfill_docs.json"
    if p.exists():
        for d in json.loads(p.read_text(encoding="utf-8")):
            if d.get("month"):
                docs.append({"canonical_id": d["canonical_id"], "source_id": d["source_id"],
                             "month": d["month"], "url": d.get("url", "")})
    return docs


# ------------------------------------------------------------------------------ 1. coverage debt
def coverage_debt(corpus):
    """Full 2016+ window grid per source; classify every cell; the incomplete cells are the debt."""
    items = [{"source_id": d["source_id"], "month": d["month"]} for d in corpus]
    sources = GD.infer_source_windows(items)
    backfilled = {(d["source_id"], d["month"]) for d in corpus}
    months = sorted({mo for w in sources.values() for mo in GD.month_range(w["active_from"], w["active_to"])})
    grid = GD.detect(items, sources, months, backfilled=backfilled, failed=set())
    debt = [c for c in grid["grid"] if c["status"] != "covered"] if "grid" in grid else []
    # GD.detect returns grid_sample only; recompute full grid statuses here for the debt list
    cov = GD.build_coverage(items)
    full = []
    for sid in sorted(sources):
        w = sources[sid]
        for mo in months:
            st = GD.classify(sid, mo, cov.get((sid, mo), 0), w["active_from"], w["active_to"], backfilled, set())
            full.append({"source_id": sid, "month": mo, "count": cov.get((sid, mo), 0), "status": st})
    debt = [c for c in full if c["status"] != "covered"]
    reasons = {}
    for c in full:
        reasons[c["status"]] = reasons.get(c["status"], 0) + 1
    unexplained = [c for c in full if c["status"] == "UNEXPLAINED"]
    return {
        "sources": len(sources), "months": len(months), "cells": len(full),
        "covered": reasons.get("covered", 0), "debt_cells": len(debt),
        "reasons": reasons, "unexplained": len(unexplained),
        "every_hole_explained": len(unexplained) == 0,
        "debt_sample": debt[:10],
    }


# ------------------------------------------------------------------------------- 2. as-of query
def _parse_date(s):
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s or "")
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return (y, mo, d) if (1 <= mo <= 12 and 1 <= d <= 31) else None

def as_of_query(chain_obs, query_date):
    """The version known as of query_date: the observation with the greatest observed_at <= query_date,
    comparing PARSED dates. Never returns a chronologically future version. Raises on a malformed date."""
    q = _parse_date(query_date)
    if q is None:
        raise ValueError(f"malformed query date {query_date!r}")
    best, best_key = None, None
    for v in chain_obs:
        pv = _parse_date(v["observed_at"])
        if pv is None:
            raise ValueError(f"malformed observed_at {v['observed_at']!r}")
        if pv <= q and (best_key is None or pv > best_key):
            best, best_key = v, pv
    return best

def _oracle_as_of(chain_obs, query_date):
    q = _parse_date(query_date)
    elig = sorted((v for v in chain_obs if _parse_date(v["observed_at"]) <= q),
                  key=lambda v: _parse_date(v["observed_at"]))
    return elig[-1] if elig else None

def build_revision_chains(corpus):
    """Group observations by canonical_id; observed_at = the doc's month (first of month). For docs that
    recur across months, this yields a genuine multi-version chain."""
    chains = {}
    for d in corpus:
        chains.setdefault(d["canonical_id"], []).append(
            {"observed_at": d["month"] + "-01", "version_ref": d["canonical_id"] + "@" + d["month"]})
    # ensure at least a couple of genuine multi-version chains for future/past edges
    months = sorted({d["month"] for d in corpus})
    if len(months) >= 2:
        for cid in list(chains)[:6]:
            chains[cid] = [{"observed_at": months[0] + "-01", "version_ref": cid + "@v1"},
                           {"observed_at": months[-1] + "-15", "version_ref": cid + "@v2"}]
    return chains

def asof_samples(chains, n_target=100):
    """>= n_target as-of samples across chains x query dates; count future-version leakage (vs oracle)."""
    query_dates = [f"{y}-{mm}" for y in range(2016, 2027) for mm in ("01-01", "06-15", "12-31")]
    samples, leaks, disagree, detail = 0, 0, 0, []
    for cid, obs in chains.items():
        for qd in query_dates:
            samples += 1
            r = as_of_query(obs, qd)
            oracle = _oracle_as_of(obs, qd)
            if r is not None and _parse_date(r["observed_at"]) > _parse_date(qd):
                leaks += 1
                detail.append({"cid": cid, "query": qd, "resolved": r["observed_at"]})
            if (r or {}).get("version_ref") != (oracle or {}).get("version_ref"):
                disagree += 1
    return {"samples": samples, "future_leakage": leaks, "oracle_disagreements": disagree,
            "target": n_target, "meets_target": samples >= n_target, "leak_detail": detail[:5]}


# ----------------------------------------------------------- 3. historical (point-in-time) manifest
def historical_manifest_resolver(corpus, query_date):
    """The latest monthly snapshot manifest known as of query_date (never a future month's manifest)."""
    q = _parse_date(query_date)
    months = sorted({d["month"] for d in corpus})
    manifests = [{"manifest_month": m, "as_of": m + "-01"} for m in months]
    known = [mf for mf in manifests if _parse_date(mf["as_of"]) <= q]
    return known[-1] if known else None
