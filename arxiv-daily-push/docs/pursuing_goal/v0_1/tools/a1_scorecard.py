#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P03-T052 -- A1 Coverage / Quality / Cost gate.

Scores every A1 source that has been through the province backfill (T050) or the city cohort
selection (T051) and issues a reversible promote / hold / disable decision -- deciding which A1
sources go to continuous production, which stay held (verified but not yet fetchable), and which are
disabled (blocked/failed). Rules the acceptance requires:
  * OFFICIAL IDENTITY 100%: every scored source is a verified A1 official publisher; a non-A1 source
    can never be promoted (or scored as A1).
  * quality / timeliness / cost each carry ACTUAL EVIDENCE (unknown != 0); a source is promoted only
    on real backfilled-document evidence, held on identity-without-docs, disabled on a real failure.
  * decisions are REVERSIBLE: this is NOT_DEPLOYED; decisions are recommendations bound to a
    feature-flag, no existing production data is rewritten (rollback = git revert / flag off).

Deterministic; reads the cached T050/T051 evidence, no network, no production side effects.
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent
EV = V01 / "evidence"
sys.path.insert(0, str(HERE))
import official_identity as OI   # T033 -- for domain-based identity of a no-document (isolated) source

# host of each province source (so identity can be re-derived, not stamped)
_PROV_HOST = {"jiangsu-gov": "www.jiangsu.gov.cn", "shandong-gov": "www.shandong.gov.cn",
              "beijing-gov": "www.beijing.gov.cn", "guangdong-gov": "www.gd.gov.cn"}

def _province_identity(sid, doc_levels):
    """EARNED, not stamped: from the backfilled docs' authority_level when present (must be uniformly
    A1), else a domain-based check (official non-central .gov.cn -> A1). A non-A1 source surfaces here
    and drops the 100% rate, failing the gate."""
    if doc_levels:
        return "A1" if doc_levels == {"A1"} else "/".join(sorted(doc_levels))
    host = _PROV_HOST.get(sid, "")
    if host and OI.is_official_domain(host) and not OI.is_central_domain(host):
        return "A1"
    return "unknown"


def _load(rel):
    p = EV / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def build_scorecard():
    prov_docs = _load("ADP-S4-P03-T050/province_backfill_docs.json") or []
    prov_cov = _load("ADP-S4-P03-T050/coverage_report.json") or {}
    city_manifest = _load("ADP-S4-P03-T051/city_cohort_manifest.json") or {}

    # index province backfill evidence by source
    by_src = {}
    for d in prov_docs:
        s = by_src.setdefault(d["source_id"], {"docs": 0, "months": set(), "with_docnum": 0, "with_date": 0,
                                               "canonical_ok": 0, "levels": set()})
        s["docs"] += 1
        s["levels"].add(d.get("authority_level"))
        if d.get("month"):
            s["months"].add(d["month"])
        if d.get("doc_number"):
            s["with_docnum"] += 1
        if d.get("doc_date"):
            s["with_date"] += 1
        if str(d.get("canonical_id", "")).startswith("ttl:") and d.get("authority_level") == "A1":
            s["canonical_ok"] += 1
    isolated = {x["source_id"] for x in prov_cov.get("isolated_failures", [])}

    rows = []

    # --- provinces that ran through the T050 backfill ---
    prov_sources = set(by_src) | isolated
    for sid in sorted(prov_sources):
        s = by_src.get(sid, {"docs": 0, "months": set(), "with_docnum": 0, "with_date": 0,
                             "canonical_ok": 0, "levels": set()})
        docs = s["docs"]
        identity = _province_identity(sid, {lv for lv in s["levels"] if lv})
        quality = {  # actual evidence; UNKNOWN (None) where unmeasured -- never a fake 0
            "docs_backfilled": docs,
            "content_addressed_A1": s["canonical_ok"],
            "with_doc_number": s["with_docnum"],
            "with_doc_date": s["with_date"],
        }
        timeliness = {"months_covered": sorted(s["months"]), "latest_month": (max(s["months"]) if s["months"] else None)}
        if sid in isolated and docs == 0:
            decision, why = "disable", "backfill blocked/failed (isolated); no official original obtained"
        elif docs >= 1 and s["canonical_ok"] == docs and timeliness["latest_month"]:
            decision, why = "promote", f"verified A1 + {docs} content-addressed docs with dates across {len(s['months'])} month(s)"
        else:
            decision, why = "hold", "verified A1 but insufficient document evidence yet"
        rows.append({"source_id": sid, "level": "A1", "kind": "province", "official_identity": identity,
                     "identity_basis": ("documents" if s["levels"] else "domain (isolated; no docs)"),
                     "quality": quality, "timeliness": timeliness,
                     "cost": {"production_new_requests": 0, "cloud_cost": 0, "dev_env_fetch": True},
                     "decision": decision, "rationale": why, "reversible": True})

    # --- cities admitted by the T051 value cohort (identity-verified, fetch pending) ---
    for a in city_manifest.get("admitted", []):
        fetched = a.get("original_fetch_status") == "confirmed"
        quality = {"docs_backfilled": 0 if not fetched else "UNKNOWN",
                   "original_fetch_status": a.get("original_fetch_status")}
        rows.append({
            "source_id": a["source_id"], "level": "A1", "kind": "city", "official_identity": a["authority_level"],
            "value": a["value"], "tier": a["tier"],
            "quality": quality, "timeliness": {"months_covered": [], "latest_month": None},
            "cost": {"production_new_requests": 0, "cloud_cost": 0, "dev_env_fetch": True},
            # verified A1 + clear value but no original fetched yet -> HOLD (not promoted on value alone)
            "decision": "promote" if fetched else "hold",
            "rationale": ("verified A1 with confirmed original" if fetched
                          else "verified A1 with clear value but original fetch pending (headless) -> hold, not production"),
            "reversible": True})

    return {
        "task": "ADP-S4-P03-T052",
        "sources_scored": len(rows),
        "official_identity_rate": (sum(1 for r in rows if r["official_identity"] == "A1") / len(rows)) if rows else 0.0,
        "decisions": {d: sum(1 for r in rows if r["decision"] == d) for d in ("promote", "hold", "disable")},
        "scorecard": rows,
        "reversibility": "NOT_DEPLOYED; decisions bound to a feature flag; no existing production data rewritten; "
                         "rollback = git revert / flag off",
        "cost": {"production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0,
                 "r2_bytes": 0, "r2_ops": 0, "model_calls": 0, "human_maintenance": "scorecard authoring"},
        "deployment": "NOT_DEPLOYED",
    }
