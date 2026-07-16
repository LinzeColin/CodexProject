#!/usr/bin/env python3
"""ADP V0.1 Source-Year unit-cost + maintenance dashboard (ADP-S4-P01-T044).

Before scaling each cohort, know the fetch / storage / AI / failure / manual-maintenance cost per
source-year. Hard rule (DIR pattern): an UNKNOWN cost is never silently 0 -- it is the literal string
"UNKNOWN" and any derived unit cost that depends on it is also "UNKNOWN". For source-years whose costs
are all measured, the dashboard computes cost per 1000 artifacts and per accepted material event.

Cost is tracked in RESOURCE units (Worker subrequests for fetch, R2 bytes for storage, model calls for
AI) because the account is free-tier (DIR-007, ~$0 recurring); the resource is the real constraint.
Deterministic; no network. NOT_DEPLOYED.
"""
from __future__ import annotations
import collections, json, pathlib

UNKNOWN = "UNKNOWN"
COST_FIELDS = ("fetch_subrequests", "storage_bytes", "model_calls")
OPS_FIELDS = ("failures", "manual_interventions")


def _known(v):
    return isinstance(v, (int, float))


def build_facts(items, measured):
    """items: [{source_id, year, accepted?}]; measured: {(source_id,year): {field: value|UNKNOWN}}.
    Throughput (artifacts, accepted_events) is counted from items; costs come from `measured`, and any
    field not present in `measured` is UNKNOWN -- never 0."""
    art = collections.Counter()
    acc = collections.Counter()
    for it in items:
        k = (it["source_id"], it["year"])
        art[k] += 1
        if it.get("accepted"):
            acc[k] += 1
    facts = []
    for k in sorted(art):
        sid, yr = k
        m = measured.get(k, {})
        fact = {"source_id": sid, "year": yr,
                "artifacts": art[k], "accepted_events": acc.get(k, 0)}
        for f in COST_FIELDS + OPS_FIELDS:
            fact[f] = m.get(f, UNKNOWN)          # unknown -> UNKNOWN, NEVER 0
        facts.append(fact)
    return facts


def unit_costs(fact):
    """Per-RESOURCE cost per 1000 artifacts and per accepted event (no heterogeneous sum: subrequests,
    bytes, and model calls are different units). Each resource that is UNKNOWN, or lacks a denominator,
    yields UNKNOWN (never 0)."""
    per_1000, per_acc = {}, {}
    for f in COST_FIELDS:
        v = fact[f]
        if not _known(v):
            per_1000[f] = UNKNOWN; per_acc[f] = UNKNOWN
        else:
            per_1000[f] = round(v / fact["artifacts"] * 1000, 4) if fact["artifacts"] else UNKNOWN
            per_acc[f] = round(v / fact["accepted_events"], 4) if fact["accepted_events"] else UNKNOWN
    return {"cost_per_1000_artifacts": per_1000, "cost_per_accepted_event": per_acc,
            "recurring_usd_month": 0}    # free tier (DIR-007); resource units are the real constraint


def dashboard(items, measured):
    facts = build_facts(items, measured)
    rows = []
    for f in facts:
        uc = unit_costs(f)
        # a source-year is "computable" only if none of its costs are UNKNOWN
        computable = all(_known(f[c]) for c in COST_FIELDS)
        rows.append({**f, **uc, "cost_computable": computable})
    # invariant: no cost field is ever the number 0 for an unmeasured field (it must be UNKNOWN)
    unknown_costs = sum(1 for f in facts for c in COST_FIELDS if f[c] == UNKNOWN)
    zero_costs = sum(1 for f in facts for c in COST_FIELDS if f[c] == 0)
    return {
        "source_years": len(rows),
        "computable_rows": sum(1 for r in rows if r["cost_computable"]),
        "rows_with_unknown_cost": sum(1 for r in rows if not r["cost_computable"]),
        "unknown_cost_cells": unknown_costs, "zero_cost_cells": zero_costs,
        "no_unknown_cost_shown_as_zero": True,   # by construction: UNKNOWN is never 0
        "rows": rows,
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--measured", help="JSON: {'source_id|year': {field: value}}")
    ap.add_argument("--out")
    args = ap.parse_args()
    items = json.loads(pathlib.Path(args.items).read_text(encoding="utf-8"))
    measured = {}
    if args.measured:
        for k, v in json.loads(pathlib.Path(args.measured).read_text(encoding="utf-8")).items():
            sid, yr = k.rsplit("|", 1); measured[(sid, int(yr))] = v
    d = dashboard(items, measured)
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: d[k] for k in ("source_years", "computable_rows", "rows_with_unknown_cost",
                                        "unknown_cost_cells", "zero_cost_cells", "no_unknown_cost_shown_as_zero")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
