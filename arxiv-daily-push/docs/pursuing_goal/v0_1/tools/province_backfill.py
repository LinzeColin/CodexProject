#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P03-T050 -- batched provincial (A1) backfill orchestrator.

Expands provincial coverage by COHORT BATCHES using the T049 A1 adapter family. Two guarantees the
acceptance requires:
  1. each batch must PASS its gate before the next batch starts (no big-bang);
  2. a failed province is ISOLATED (recorded, does not block the rest of its batch or the run).

Deterministic orchestration; the per-province fetch is injected (a real HttpFetcher for the live
dev-env run, a fixture fetcher for tests). Identity is content-addressed via the T049 normalize
canonical_hint (ttl:...) so re-running is idempotent. release_mode SHADOW; never the worker.
"""
import sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import adapter_a1_province as A   # T049


def plan_batches(cohort):
    """cohort: [{batch:int, source_id, profile:SiteProfile}]. Returns batches in ascending order."""
    by = {}
    for m in cohort:
        by.setdefault(m["batch"], []).append(m)
    return [by[k] for k in sorted(by)]


def run_province(connector, max_docs, fetched_at):
    """discover -> fetch up to max_docs -> normalize; content-addressed idempotency within the province.
    Any failure is caught and surfaced (never raised) so the caller can isolate it."""
    rec = {"source_id": connector.source_id, "ok": False, "docs": [], "error": None,
           "template_family": connector.profile.template_family}
    try:
        items = connector.discover(None)[:max_docs]
        seen = set()
        for it in items:
            fr = connector.fetch(it.url, fetched_at)
            if not getattr(fr, "ok", False):
                continue
            # A1 must be EARNED via the identity check, not assumed from a class attribute -- only keep
            # documents the connector verifies as official, non-central A1.
            ver = connector.verify(it, fr)
            if not (ver.is_official and ver.authority_level == "A1"):
                rec.setdefault("rejected_non_a1", 0)
                rec["rejected_non_a1"] += 1
                continue
            nd = connector.normalize(it, fr)
            key = nd.canonical_hint
            if key in seen:
                continue
            seen.add(key)
            rec["docs"].append({
                "canonical_id": key, "source_id": nd.source_id, "url": it.url, "title": nd.title,
                "doc_number": nd.doc_number, "doc_date": nd.doc_date,
                "month": nd.doc_date[:7] if nd.doc_date else None,
                "authority_level": ver.authority_level, "attachments": len(nd.attachments)})
        rec["ok"] = True
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
    return rec


def batch_gate(batch_record):
    """A batch PASSES when >=1 province produced >=1 well-formed A1 doc (canonical_id + A1 + month)."""
    good = 0
    for p in batch_record["provinces"]:
        if p["ok"] and any(d["canonical_id"] and d["authority_level"] == "A1" and d["month"] for d in p["docs"]):
            good += 1
    batch_record["provinces_ok"] = good
    return good >= 1


def orchestrate(batches, connector_of, max_docs=3, fetched_at="2026-07-16T00:00:00+10:00"):
    """Run batches IN ORDER; only start batch N+1 if batch N's gate passed. Isolate failed provinces."""
    out = {"batches": [], "isolated_failures": [], "halted_at": None}
    for i, batch in enumerate(batches):
        prov = []
        for m in batch:
            r = run_province(connector_of(m), max_docs, fetched_at)
            prov.append(r)
            if not r["ok"] or not r["docs"]:
                out["isolated_failures"].append(
                    {"batch": i, "source_id": m["source_id"], "reason": r["error"] or "no docs discovered"})
        br = {"batch": i, "source_ids": [m["source_id"] for m in batch], "provinces": prov}
        br["gate_passed"] = batch_gate(br)
        out["batches"].append(br)
        if not br["gate_passed"]:
            out["halted_at"] = i          # a failed batch stops progression (no next batch)
            break
    out["completed_batches"] = sum(1 for b in out["batches"] if b["gate_passed"])
    out["total_docs"] = sum(len(p["docs"]) for b in out["batches"] for p in b["provinces"])
    return out


def coverage_report(run):
    """province x month coverage grid from the run's docs."""
    cov = {}
    for b in run["batches"]:
        for p in b["provinces"]:
            for d in p["docs"]:
                cov.setdefault(d["source_id"], {}).setdefault(d["month"], 0)
                cov[d["source_id"]][d["month"]] += 1
    return {"by_source_month": cov,
            "sources_covered": len(cov),
            "isolated": run["isolated_failures"]}
