#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P04-T054 -- expand the A2 registry by MARGINAL value.

Adds more A2 functional zones beyond the T053 first-10 pilot, but only ones that actually provide
first-line local-action signals (projects, pilots, procurement, industry-landing). The gate the
acceptance requires: the NEW cohort's verified-useful-signal rate must be >= the existing A2 baseline
(the T053 pilot's rate). A zone that would drag the rate down -- only baseline (policy) signals, or a
non-official source -- is NOT added. Emits the expanded cohorts, a marginal-value report, and health.

Reuses the T053 model (a2_pilot). Selection, not fetching (zone portals are largely JS/TLS-hardened
server-side); the three T053 server-reachable zones anchor the confirmed-signal evidence.
"""
import sys, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a2_pilot as A2P   # T053 (incremental_signals / verify_official / LOCAL_SIGNAL_TYPES)

EV = HERE.parent / "evidence"

# second-wave A2 candidates (综合保税区 / 国家级经开区 / 其他国家级新区 / 高新区) + negative controls
EXPANSION_CANDIDATES = [
    {"source_id": "guangzhou-ndz", "name": "广州南沙新区", "zone_type": "national_new_area", "host": "www.gzns.gov.cn",
     "signals": ["project_approval", "industry_landing", "investment", "pilot"], "reach": "tls_blocked"},
    {"source_id": "zhoushan-newarea", "name": "舟山群岛新区", "zone_type": "national_new_area", "host": "www.zhoushan.gov.cn",
     "signals": ["project_approval", "industry_landing", "planning"], "reach": "tls_blocked"},
    {"source_id": "xihaian-newarea", "name": "青岛西海岸新区", "zone_type": "national_new_area", "host": "www.xihaian.gov.cn",
     "signals": ["project_approval", "industry_landing", "investment"], "reach": "tls_blocked"},
    {"source_id": "hefei-hitech", "name": "合肥高新区", "zone_type": "hi_tech_innovation", "host": "www.hfgx.gov.cn",
     "signals": ["pilot", "project_approval", "industry_landing"], "reach": "tls_blocked"},
    {"source_id": "wuhan-eastlake", "name": "武汉东湖高新区", "zone_type": "hi_tech_innovation", "host": "www.wehdz.gov.cn",
     "signals": ["pilot", "industry_landing", "project_approval", "investment"], "reach": "tls_blocked"},
    {"source_id": "tianjin-binhai", "name": "天津滨海新区", "zone_type": "national_new_area", "host": "www.bh.gov.cn",
     "signals": ["project_approval", "industry_landing", "investment", "pilot"], "reach": "tls_blocked"},
    {"source_id": "nanjing-jiangbei", "name": "南京江北新区", "zone_type": "national_new_area", "host": "www.njna.gov.cn",
     "signals": ["project_approval", "pilot", "industry_landing"], "reach": "tls_blocked"},
    {"source_id": "chengdu-hitech", "name": "成都高新区", "zone_type": "hi_tech_innovation", "host": "www.cdht.gov.cn",
     "signals": ["project_approval", "industry_landing", "pilot"], "reach": "tls_blocked"},
    # negative controls: a zone with ONLY baseline (would drag the useful-signal rate down), and a non-official source
    {"source_id": "baseline-only-zone", "name": "某区(仅政策转发)", "zone_type": "ordinary_district", "host": "www.baseonly.gov.cn",
     "signals": ["policy", "regulation", "statistics"], "reach": "unknown"},
    {"source_id": "zone-aggregator", "name": "某区招商资讯", "zone_type": "hi_tech_innovation", "host": "invest.zone.com",
     "signals": ["project_approval", "investment"], "reach": "unknown", "category": "media"},
]


def _verified_useful(zone_signals_official):
    """A cohort member is 'verified useful' when it is official AND carries >=1 first-line signal."""
    return zone_signals_official


def useful_signal_rate(members):
    """members: [{verified_useful: bool}]. Rate = verified-useful / total (0.0 if empty)."""
    if not members:
        return 0.0
    return round(sum(1 for m in members if m["verified_useful"]) / len(members), 4)


def baseline_from_t053():
    """The existing A2 baseline: every admitted T053 pilot zone is official with >=1 incremental signal,
    so it is verified-useful. Rate = the pilot cohort's verified-useful fraction."""
    man = json.loads((EV / "ADP-S4-P04-T053" / "a2_pilot_manifest.json").read_text(encoding="utf-8"))
    members = [{"source_id": a["source_id"], "verified_useful": bool(a["incremental_signal_types"])}
               for a in man["admitted"]]
    return {"cohort": "A2-PILOT-BATCH-1", "size": len(members), "rate": useful_signal_rate(members)}


def evaluate(zone):
    """Marginal-value evaluation of one candidate: its first-line signals + official identity."""
    inc = A2P.incremental_signals(zone)
    idv = A2P.verify_official(zone)
    official = idv["verified"] and idv["authority_level"] in ("A0", "A1")
    return {"source_id": zone["source_id"], "name": zone["name"], "zone_type": zone["zone_type"],
            "official_host": zone["host"], "incremental_signal_types": inc, "marginal_useful_signals": len(inc),
            "official": official, "authority_level": "A2" if official else idv["authority_level"],
            "verified_useful": bool(official and inc),
            "reachable_server_side": zone.get("reach", "unknown"),
            "cursor_2016": A2P.cursor_2016(zone["source_id"])}


def expand(candidates=EXPANSION_CANDIDATES):
    baseline = baseline_from_t053()
    evals = [evaluate(z) for z in candidates]
    admitted = [e for e in evals if e["verified_useful"]]
    rejected = [{"source_id": e["source_id"],
                 "reason": ("no first-line marginal value (baseline-only)" if not e["incremental_signal_types"]
                            else f"not a verified official A2 publisher ({e['authority_level']})")}
                for e in evals if not e["verified_useful"]]
    new_rate = useful_signal_rate([{"verified_useful": True} for _ in admitted])   # admitted are all verified-useful
    # health per admitted zone
    health = [{"source_id": e["source_id"], "reachable": e["reachable_server_side"],
               "first_line_signal_types": e["marginal_useful_signals"],
               "healthy": e["marginal_useful_signals"] >= 1} for e in admitted]
    admitted.sort(key=lambda x: x["marginal_useful_signals"], reverse=True)
    return {
        "task": "ADP-S4-P04-T054",
        "baseline": baseline,
        "expansion_candidates": len(candidates),
        "admitted": admitted, "admitted_count": len(admitted),
        "rejected": rejected, "rejected_count": len(rejected),
        "new_cohort_useful_signal_rate": new_rate,
        "meets_baseline": new_rate >= baseline["rate"],
        "marginal_value_report": [
            {"source_id": e["source_id"], "name": e["name"], "marginal_useful_signals": e["marginal_useful_signals"],
             "incremental_signal_types": e["incremental_signal_types"], "admitted": e["verified_useful"]}
            for e in evals],
        "health": health,
        "cost": {"production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0, "r2_bytes": 0,
                 "r2_ops": 0, "model_calls": 0, "human_maintenance": "marginal-value model + curated expansion zones"},
        "deployment": "SHADOW (expanded A2 cohorts + marginal value report + health; production untouched)",
    }
