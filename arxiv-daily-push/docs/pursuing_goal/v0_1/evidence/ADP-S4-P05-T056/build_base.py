#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P05-T056 -- emit the coverage-debt + as-of query base report (deterministic)."""
import sys, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import coverage_asof as CA

def main():
    corpus = CA.load_corpus()
    cd = CA.coverage_debt(corpus)
    chains = CA.build_revision_chains(corpus)
    asof = CA.asof_samples(chains)
    # historical manifest resolver: a few point-in-time resolutions, proving no future manifest
    pit = []
    for qd in ["2015-01-01", "2019-12-31", "2020-06-15", "2022-01-15", "2099-01-01"]:
        mf = CA.historical_manifest_resolver(corpus, qd)
        pit.append({"query_date": qd, "manifest_month": (mf["manifest_month"] if mf else None)})
    out = {
        "task": "ADP-S4-P05-T056",
        "corpus_docs": len(corpus),
        "coverage_debt": cd,
        "as_of": asof,
        "historical_manifest_resolutions": pit,
        "cost": {"production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0, "r2_bytes": 0,
                 "r2_ops": 0, "model_calls": 0, "human_maintenance": "coverage-debt + as-of base authoring"},
        "deployment": "NOT_DEPLOYED",
    }
    (HERE / "coverage_asof_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"coverage cells={cd['cells']} covered={cd['covered']} debt={cd['debt_cells']} unexplained={cd['unexplained']}; "
          f"as_of samples={asof['samples']} leakage={asof['future_leakage']} meets_target={asof['meets_target']}")

if __name__ == "__main__":
    main()
