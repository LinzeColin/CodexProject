#!/usr/bin/env python3
"""ADP V0.1 A0 backfill cohort selection by user value (ADP-S4-P02-T045).

Covers the high-value central / national-level domains FIRST instead of blindly opening every source
in Registry order. A priority model scores each candidate A0 source by user value, and the selected
cohort is a manifest where every source carries an AUTHORITY ROLE, a HISTORY START point, the EXPECTED
DOCUMENT TYPES, and a STOP RULE, plus the expected benefit. Deterministic; no network. NOT_DEPLOYED.

The Wave-1 cohort is a proposal for the Owner S4 cohort gate (SCALE / HOLD / STOP) -- execution is T046.
"""
from __future__ import annotations
import json, pathlib

# candidate A0 sources (from S3-P02 adapters), with user-value inputs. `live_ok` reflects real access.
CANDIDATES = {
    "gov-cn-policy": {"name": "国务院政策文件", "authority_role": "A0", "domain_value": 1.0,
                      "coverage_gap": 1.0, "stability": 1.0, "live_ok": True,
                      "history_start": "2016-01", "expected_doc_types": ["通知", "规定", "办法", "意见"]},
    "gov-cn-fagui": {"name": "国家法律法规", "authority_role": "A0", "domain_value": 0.95,
                     "coverage_gap": 1.0, "stability": 0.95, "live_ok": True,
                     "history_start": "2016-01", "expected_doc_types": ["法律", "行政法规", "国务院令"]},
    "stats-gov": {"name": "国家统计局", "authority_role": "A0", "domain_value": 0.9,
                  "coverage_gap": 0.9, "stability": 0.9, "live_ok": True,
                  "history_start": "2016-01", "expected_doc_types": ["统计公报", "经济运行", "指标数据"]},
    "ndrc-gov": {"name": "国家发改委", "authority_role": "A0", "domain_value": 0.85,
                 "coverage_gap": 0.9, "stability": 0.85, "live_ok": True,
                 "history_start": "2016-01", "expected_doc_types": ["政策文件", "公告", "规划"]},
    "cac-gov": {"name": "网信办", "authority_role": "A0", "domain_value": 0.85,
                "coverage_gap": 1.0, "stability": 0.8, "live_ok": True,
                "history_start": "2016-01", "expected_doc_types": ["规定", "征求意见稿", "公告"]},
    "nda-gov": {"name": "国家数据局", "authority_role": "A0", "domain_value": 0.8,
                "coverage_gap": 1.0, "stability": 0.4, "live_ok": False,   # TLS/JS-shell blocked (T036)
                "history_start": "2023-10", "expected_doc_types": ["数据政策", "公告"]},
}
WEIGHTS = {"domain_value": 0.4, "coverage_gap": 0.3, "stability": 0.3}


def value_score(c):
    return round(sum(WEIGHTS[k] * c[k] for k in WEIGHTS), 4)


def stop_rule(c):
    # backfill to the history start, then stop; cap per-cohort to protect realtime (T042 lanes)
    return {"until_month": c["history_start"], "stop_when": "shard status=done for every month in range",
            "guardrail": "auto-pause if realtime freshness P95 > baseline+20% (T042)"}


def select_cohort(cohort_id="A0-WAVE-1", require_live=True, top_n=None):
    scored = []
    for sid, c in CANDIDATES.items():
        scored.append((value_score(c), sid, c))
    scored.sort(key=lambda x: (-x[0], x[1]))          # highest value first, NOT registry order
    members, deferred = [], []
    for score, sid, c in scored:
        entry = {"source_id": sid, "name": c["name"], "authority_role": c["authority_role"],
                 "value_score": score, "history_start": c["history_start"],
                 "expected_doc_types": c["expected_doc_types"], "stop_rule": stop_rule(c),
                 "expected_benefit": {"coverage_gain": c["coverage_gap"], "authoritativeness": 1.0 if c["authority_role"] == "A0" else 0.7}}
        if require_live and not c["live_ok"]:
            entry["deferred_reason"] = "live fetch blocked (needs browser / RSS-API); excluded from Wave 1"
            deferred.append(entry)
        else:
            members.append(entry)
    if top_n:
        members = members[:top_n]
    return {"cohort_id": cohort_id, "selection": "by user value (central/national high-value first), not registry order",
            "members": members, "deferred": deferred,
            "member_count": len(members), "priority_weights": WEIGHTS}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args()
    cohort = select_cohort()
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(cohort, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cohort_id": cohort["cohort_id"], "member_count": cohort["member_count"],
                      "members": [(m["source_id"], m["value_score"]) for m in cohort["members"]],
                      "deferred": [d["source_id"] for d in cohort["deferred"]]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
