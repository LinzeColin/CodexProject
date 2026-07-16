#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic fixtures for ADP-S6-P01-T070 (Dataset Snapshot + observed_at leakage guard).

The corpus deliberately includes a 2016 policy that was only BACKFILLED (observed) in 2026, plus a
document observed in the future relative to a 2018 prediction -- so a snapshot keyed on observed_at
must exclude both from the 2018 dataset, and the leakage tripwire must fire if either is injected.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
sys.path.insert(0, str(V01 / "tools"))
import dataset_snapshot as DS

# doc_date = when it issued; observed_at = when ADP actually fetched/knew it.
CORPUS = [
    {"canonical_id": "a", "doc_date": "2017-03-01", "observed_at": "2017-03-02",
     "content_hash": "h-a", "agency": "国务院办公厅"},
    {"canonical_id": "b", "doc_date": "2017-11-01", "observed_at": "2017-11-05",
     "content_hash": "h-b", "agency": "国家统计局"},
    # BACKFILLED: a 2016 policy, but ADP only observed it in 2026 -> NOT known in 2018
    {"canonical_id": "backfill16", "doc_date": "2016-05-01", "observed_at": "2026-07-01",
     "content_hash": "h-bf", "agency": "国务院办公厅"},
    # observed in 2019 -> known by 2019 but not by 2018
    {"canonical_id": "c", "doc_date": "2019-02-01", "observed_at": "2019-02-03",
     "content_hash": "h-c", "agency": "国家发改委"},
]
PREDICTION = {"target_id": "G1", "origin_date": "2018-01-01"}


def main():
    snap = DS.snapshot(CORPUS, "2018-01-01")
    rebuilt = DS.rebuild_for_prediction(CORPUS, PREDICTION)
    report = {
        "as_of": "2018-01-01",
        "snapshot_ids": [d["canonical_id"] for d in snap["docs"]],
        "snapshot_id": snap["snapshot_id"],
        "rebuilt_matches": rebuilt["snapshot_id"] == snap["snapshot_id"],
        "excluded_backfill16": "backfill16" not in [d["canonical_id"] for d in snap["docs"]],
    }
    (HERE / "dataset_snapshot_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("as-of 2018-01-01 snapshot ids:", report["snapshot_ids"])
    print("backfilled-2016 excluded:", report["excluded_backfill16"])
    print("rebuild matches:", report["rebuilt_matches"], "snapshot_id:", snap["snapshot_id"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
