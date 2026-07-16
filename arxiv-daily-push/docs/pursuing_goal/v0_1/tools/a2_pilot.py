#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P04-T053 -- first-batch high-value A2 (functional-zone) pilot onboarding.

A2 = important districts / new areas / free-trade zones / hi-tech parks -- official but sub-provincial
FUNCTIONAL zones whose value is INCREMENTAL: they publish first-line LOCAL ACTION signals (project
approvals, procurement/tenders, pilots, industry-landing, investment, planning) that central (A0) and
provincial (A1) sources do not carry. This tool selects the first 10 high-value A2 pilots, each with
a pilot profile, a 2016+ cursor, and its local-action-signal set, and it ADMITS a zone only when it
produces real incremental value beyond the A0/A1 baseline -- a zone that merely re-posts central /
provincial policy (no local action) is NOT promoted.

Selection, not fetching: zone portals are largely JS/TLS-hardened server-side (recon). Reachability is
honest metadata; admission is incremental value + verified official (functional-zone) identity. The
three server-reachable zones (Xiongan, SIP, Hengqin) carry confirmed live local-action signal evidence.
"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import official_identity as OI   # T033

# the A0/A1 baseline signal types -- coverage that central + provincial sources already provide
BASELINE_SIGNALS = {"policy", "regulation", "statistics"}

# A2-specific LOCAL ACTION signal taxonomy (first-line, beyond the baseline)
LOCAL_SIGNAL_TYPES = {
    "project_approval": "项目立项/开工",
    "procurement": "招投标/采购",
    "pilot": "试点/先行先试",
    "industry_landing": "产业落地/签约",
    "investment": "招商引资",
    "planning": "规划公示",
}

# 10 high-value functional zones + negative controls. `signals`: the signal types each zone publishes.
CANDIDATES = [
    {"source_id": "xiongan-newarea", "name": "雄安新区", "zone_type": "national_new_area", "host": "www.xiongan.gov.cn",
     "signals": ["project_approval", "planning", "industry_landing", "policy"], "reach": "confirmed_signals"},
    {"source_id": "sip-suzhou", "name": "苏州工业园区", "zone_type": "national_dev_zone", "host": "www.sipac.gov.cn",
     "signals": ["procurement", "project_approval", "industry_landing", "investment"], "reach": "confirmed_signals"},
    {"source_id": "hengqin-zone", "name": "横琴粤澳深合区", "zone_type": "free_trade_cooperation", "host": "www.hengqin.gov.cn",
     "signals": ["pilot", "investment", "industry_landing", "policy"], "reach": "confirmed_signals"},
    {"source_id": "pudong-newarea", "name": "浦东新区", "zone_type": "national_new_area", "host": "www.pudong.gov.cn",
     "signals": ["pilot", "project_approval", "industry_landing", "investment"], "reach": "tls_blocked"},
    {"source_id": "zgc-park", "name": "中关村示范区", "zone_type": "hi_tech_innovation", "host": "zgcgw.beijing.gov.cn",
     "signals": ["pilot", "project_approval", "industry_landing"], "reach": "tls_blocked"},
    {"source_id": "qianhai-ftz", "name": "前海深港合作区", "zone_type": "free_trade_zone", "host": "www.szqh.gov.cn",
     "signals": ["pilot", "investment", "policy"], "reach": "tls_blocked"},
    {"source_id": "lingang-ftz", "name": "上海临港新片区", "zone_type": "free_trade_zone", "host": "www.lgxc.gov.cn",
     "signals": ["pilot", "industry_landing", "investment", "project_approval"], "reach": "tls_blocked"},
    {"source_id": "tianfu-newarea", "name": "天府新区", "zone_type": "national_new_area", "host": "www.cdtf.gov.cn",
     "signals": ["project_approval", "planning", "industry_landing"], "reach": "tls_blocked"},
    {"source_id": "xian-hitech", "name": "西安高新区", "zone_type": "hi_tech_innovation", "host": "gxq.xa.gov.cn",
     "signals": ["project_approval", "industry_landing", "pilot"], "reach": "tls_blocked"},
    {"source_id": "liangjiang-newarea", "name": "重庆两江新区", "zone_type": "national_new_area", "host": "www.liangjiang.gov.cn",
     "signals": ["project_approval", "industry_landing", "investment"], "reach": "tls_blocked"},
    # negative controls
    {"source_id": "policy-repost-zone", "name": "某区(仅转政策)", "zone_type": "ordinary_district", "host": "www.repost.gov.cn",
     "signals": ["policy", "regulation"], "reach": "unknown"},                     # 0 incremental -> reject
    {"source_id": "zone-media", "name": "某园区资讯号", "zone_type": "hi_tech_innovation", "host": "news.zone.com",
     "signals": ["project_approval", "industry_landing"], "reach": "unknown", "category": "media"},  # non-official -> reject
]


def incremental_signals(zone):
    """The LOCAL ACTION signal types a zone provides beyond the A0/A1 baseline -- its incremental value."""
    return sorted(s for s in zone.get("signals", []) if s in LOCAL_SIGNAL_TYPES and s not in BASELINE_SIGNALS)


def verify_official(zone):
    """Official functional-zone publisher check via T033: official .gov.cn, non-central; media never A1/A2."""
    return OI.verify_identity({"source_id": zone["source_id"], "url": "https://" + zone["host"],
                               "category": zone.get("category", "official"),
                               "gov_directory_listed": zone.get("category", "official") == "official"})


def cursor_2016(source_id):
    return {"source_id": source_id, "start_month": "2016-01", "last_confirmed_month": None,
            "last_confirmed_id": None, "status": "pending"}


def select_pilot(candidates=CANDIDATES):
    """Admit a zone ONLY if it has incremental local-action value AND verifies as an official
    non-central publisher (-> A2 functional zone). No-incremental or non-official zones are rejected."""
    admitted, rejected = [], []
    for z in candidates:
        inc = incremental_signals(z)
        idv = verify_official(z)
        is_official = idv["verified"] and idv["authority_level"] in ("A1", "A0")  # official non-central domain
        if not inc:
            rejected.append({"source_id": z["source_id"], "reason": "no incremental value beyond A0/A1 baseline"})
            continue
        if not is_official:
            rejected.append({"source_id": z["source_id"], "reason": f"not a verified official publisher ({idv['authority_level']})"})
            continue
        admitted.append({
            "source_id": z["source_id"], "name": z["name"], "zone_type": z["zone_type"],
            "authority_level": "A2", "official_host": z["host"],
            "local_action_signals": [LOCAL_SIGNAL_TYPES[s] for s in z["signals"] if s in LOCAL_SIGNAL_TYPES],
            "incremental_signal_types": inc,
            "incremental_value": len(inc),
            "reachable_server_side": z.get("reach", "unknown"),
            "cursor_2016": cursor_2016(z["source_id"]),
            "value_rationale": f"{z['zone_type']} publishes {len(inc)} local-action signal type(s) absent from A0/A1",
        })
    admitted.sort(key=lambda x: x["incremental_value"], reverse=True)
    return {"admitted": admitted, "rejected": rejected, "candidates": len(candidates),
            "baseline_signals": sorted(BASELINE_SIGNALS)}
