#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic fixtures for ADP-S6-P01-T069 (prediction target catalog + settlement).

The catalog mixes SETTLEABLE targets (objective official-evidence predicates) with AMBIGUOUS ones
(subjective / missing-field / no-horizon) that must be rejected. The evidence set includes an official
match, a MEDIA look-alike (must not settle), and a FUTURE official match (must not leak).
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
sys.path.insert(0, str(V01 / "tools"))
import prediction_targets as PT

CATALOG = [
    # settleable: an official 数据共享 policy from 国务院办公厅 within 180 days
    PT.make_target("G1", "国务院办公厅将在半年内发布数据共享政策", 180, "policy",
                   {"type": "official_doc_exists", "agency": "国务院办公厅", "topic": "数据共享"}),
    # settleable: at least 2 official 统计 releases from 国家统计局 within a year
    PT.make_target("G2", "国家统计局一年内至少发布2次统计公报", 365, "statistics",
                   {"type": "count_at_least", "agency": "国家统计局", "topic": "统计", "n": 2}),
    # settleable: a specific document transitions to 'revoked' within 90 days
    PT.make_target("G3", "某规定90天内被废止", 90, "status",
                   {"type": "status_transition", "canonical_id": "doc-X", "to_status": "revoked"}),
    # AMBIGUOUS: subjective predicate (not a recognized objective type) -> reject
    PT.make_target("B1", "该政策将会很重要", 180, "vibes",
                   {"type": "is_important", "note": "significant"}),
    # AMBIGUOUS: official_doc_exists but the topic field is empty -> reject
    PT.make_target("B2", "某机构会发文", 180, "policy",
                   {"type": "official_doc_exists", "agency": "国务院办公厅", "topic": ""}),
    # AMBIGUOUS: no finite horizon -> reject
    PT.make_target("B3", "迟早会发布", 0, "policy",
                   {"type": "official_doc_exists", "agency": "国务院办公厅", "topic": "数据共享"}),
]

# evidence (canonical_id, authority_level, agency, topics, status, observed_at)
E_OFFICIAL_MATCH = {"canonical_id": "d1", "authority_level": "A0", "agency": "国务院办公厅",
                    "topics": ["数据共享"], "status": "published", "observed_at": "2026-03-01"}
E_MEDIA_MATCH = {"canonical_id": "d2", "authority_level": "media", "agency": "国务院办公厅",
                 "topics": ["数据共享"], "status": "published", "observed_at": "2026-03-05"}
E_FUTURE_MATCH = {"canonical_id": "d3", "authority_level": "A0", "agency": "国务院办公厅",
                  "topics": ["数据共享"], "status": "published", "observed_at": "2026-09-01"}
E_STATS_1 = {"canonical_id": "s1", "authority_level": "A0", "agency": "国家统计局",
             "topics": ["统计"], "status": "published", "observed_at": "2026-02-10"}
E_STATS_2 = {"canonical_id": "s2", "authority_level": "A0", "agency": "国家统计局",
             "topics": ["统计"], "status": "published", "observed_at": "2026-05-10"}
E_STATUS = {"canonical_id": "doc-X", "authority_level": "A0", "agency": "某部",
            "topics": ["规定"], "status": "revoked", "observed_at": "2026-02-15"}
ORIGIN = "2026-01-01"


def main():
    adm = PT.admit_targets(CATALOG)
    report = {
        "admitted": [t["target_id"] for t in adm["admitted"]],
        "rejected": [r["target_id"] for r in adm["rejected"]],
        "settlements": {
            "G1_official": PT.settle(CATALOG[0], [E_OFFICIAL_MATCH, E_FUTURE_MATCH], ORIGIN)["label"],
            "G1_media_and_future_only": PT.settle(CATALOG[0], [E_MEDIA_MATCH, E_FUTURE_MATCH], ORIGIN)["label"],
            "G1_future_only": PT.settle(CATALOG[0], [E_FUTURE_MATCH], ORIGIN)["label"],
            "G2_two_stats": PT.settle(CATALOG[1], [E_STATS_1, E_STATS_2, E_FUTURE_MATCH], ORIGIN)["label"],
            "G3_revoked": PT.settle(CATALOG[2], [E_STATUS, E_FUTURE_MATCH], ORIGIN)["label"],
        },
    }
    (HERE / "prediction_targets_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("admitted:", report["admitted"], "rejected:", report["rejected"])
    print("settlements:", report["settlements"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
