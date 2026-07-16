#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P03-T051 -- key city-level (A1) cohort selection by USER VALUE.

Selects which municipal governments to onboard, by value tier, NOT by volume: 直辖市, 副省级 /
计划单列, 省会, and key innovation / manufacturing / finance / trade cities. Deliverables are the
cohort MANIFEST, the OFFICIAL IDENTITY verdict per city, and a 2016 backfill CURSOR per admitted
city -- the config a later batch (the T050 mechanism) executes against. Two hard rules:
  * every admitted city must have a clear value (tier + score + rationale) AND be a verified official
    original publisher (official city .gov.cn, non-central -> A1 via T033; media/search are never A1);
  * a low-value source is NOT enabled just to grow the count -- a stop_rule rejects below threshold.

Value != fetching here (city portals are largely JS/TLS-hardened server-side; the actual original
fetch is the backfill execution, disclosed in known_gaps). Reachability is recorded as honest
metadata, it is not the admission gate -- admission is value + verified official identity.
"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import official_identity as OI   # T033

STOP_THRESHOLD = 0.60            # below this value, a city is NOT admitted (no volume-padding)

# tier weight: administrative authority / policy reach of the city government
TIER_WEIGHT = {
    "municipality": 1.00,          # 直辖市 (city == province-level)
    "sub_provincial_plan": 0.94,   # 副省级 AND 计划单列 (e.g. 深圳/青岛/宁波/大连/厦门)
    "sub_provincial": 0.88,        # 副省级市
    "capital": 0.74,               # 省会
    "key_economic": 0.64,          # 关键 创新/制造/金融/外贸 城市
    "ordinary": 0.30,              # ordinary prefecture city -> below stop threshold
}

# curated key-city candidates. `roles`: innovation/manufacturing/finance/trade/hub raise value.
# host: the official city government .gov.cn portal (an official-original publisher).
CANDIDATES = [
    # 直辖市 (北京 already covered by the province cohort T049/T050)
    {"source_id": "shanghai-gov", "city": "上海", "tier": "municipality", "host": "www.shanghai.gov.cn",
     "roles": ["finance", "trade", "innovation"]},
    {"source_id": "chongqing-gov", "city": "重庆", "tier": "municipality", "host": "www.cq.gov.cn",
     "roles": ["manufacturing", "hub"]},
    {"source_id": "tianjin-gov", "city": "天津", "tier": "municipality", "host": "www.tj.gov.cn",
     "roles": ["manufacturing", "trade"]},
    # 副省级 + 计划单列
    {"source_id": "shenzhen-gov", "city": "深圳", "tier": "sub_provincial_plan", "host": "www.sz.gov.cn",
     "roles": ["innovation", "finance", "trade"]},
    {"source_id": "qingdao-gov", "city": "青岛", "tier": "sub_provincial_plan", "host": "www.qingdao.gov.cn",
     "roles": ["manufacturing", "trade"]},
    {"source_id": "ningbo-gov", "city": "宁波", "tier": "sub_provincial_plan", "host": "www.ningbo.gov.cn",
     "roles": ["trade", "manufacturing"]},
    {"source_id": "xiamen-gov", "city": "厦门", "tier": "sub_provincial_plan", "host": "www.xm.gov.cn",
     "roles": ["trade"]},
    {"source_id": "dalian-gov", "city": "大连", "tier": "sub_provincial_plan", "host": "www.dl.gov.cn",
     "roles": ["trade", "manufacturing"]},
    # 副省级 (省会)
    {"source_id": "guangzhou-gov", "city": "广州", "tier": "sub_provincial", "host": "www.gz.gov.cn",
     "roles": ["trade", "manufacturing", "hub"]},
    {"source_id": "hangzhou-gov", "city": "杭州", "tier": "sub_provincial", "host": "www.hangzhou.gov.cn",
     "roles": ["innovation", "finance"]},
    {"source_id": "nanjing-gov", "city": "南京", "tier": "sub_provincial", "host": "www.nanjing.gov.cn",
     "roles": ["innovation", "hub"]},
    {"source_id": "chengdu-gov", "city": "成都", "tier": "sub_provincial", "host": "www.chengdu.gov.cn",
     "roles": ["hub", "innovation"]},
    {"source_id": "wuhan-gov", "city": "武汉", "tier": "sub_provincial", "host": "www.wuhan.gov.cn",
     "roles": ["innovation", "hub"]},
    {"source_id": "xian-gov", "city": "西安", "tier": "sub_provincial", "host": "www.xa.gov.cn",
     "roles": ["innovation", "hub"]},
    # 关键经济城市 (非副省级)
    {"source_id": "suzhou-gov", "city": "苏州", "tier": "key_economic", "host": "www.suzhou.gov.cn",
     "roles": ["manufacturing", "trade", "innovation"]},
    {"source_id": "dongguan-gov", "city": "东莞", "tier": "key_economic", "host": "www.dg.gov.cn",
     "roles": ["manufacturing", "trade"]},
    {"source_id": "foshan-gov", "city": "佛山", "tier": "key_economic", "host": "www.foshan.gov.cn",
     "roles": ["manufacturing"]},
    {"source_id": "wuxi-gov", "city": "无锡", "tier": "key_economic", "host": "www.wuxi.gov.cn",
     "roles": ["manufacturing", "innovation"]},
    # negative-control examples: an ordinary low-value city, and a NON-official media aggregator
    {"source_id": "ordinary-city-gov", "city": "某地级市", "tier": "ordinary", "host": "www.example-city.gov.cn",
     "roles": []},
    {"source_id": "city-news-portal", "city": "某市新闻网", "tier": "sub_provincial", "host": "news.example.com",
     "roles": ["innovation"], "category": "media"},
]

ROLE_WEIGHT = {"innovation": 0.05, "finance": 0.04, "trade": 0.035, "manufacturing": 0.03, "hub": 0.03}

def value_score(c):
    """TIER_WEIGHT[tier] authority + role bonus (capped at +0.12, total capped at 1.0). Deterministic."""
    base = TIER_WEIGHT.get(c["tier"], 0.3)
    role_bonus = min(0.12, sum(ROLE_WEIGHT.get(r, 0) for r in c.get("roles", [])))
    return round(min(1.0, base + role_bonus), 4)

def verify_official(c):
    """Official-original publisher check via T033: official city .gov.cn, non-central -> A1;
    a media/aggregator category is discovery-only and can never be A1 (so never admitted)."""
    return OI.verify_identity({"source_id": c["source_id"], "url": "https://" + c["host"],
                               "category": c.get("category", "official"),
                               "gov_directory_listed": c.get("category", "official") == "official"})

def cursor_2016(source_id):
    """A resumable 2016+ backfill cursor (T041 shape) for an admitted city; execution is a later batch."""
    return {"source_id": source_id, "start_month": "2016-01", "last_confirmed_month": None,
            "last_confirmed_id": None, "status": "pending"}

def select_cohort(candidates=CANDIDATES, reachability=None):
    """Rank by value; admit a city ONLY if value >= STOP_THRESHOLD AND it verifies as an official
    non-central A1 publisher. Everything else is rejected with a reason (never volume-padded)."""
    reachability = reachability or {}
    admitted, rejected = [], []
    for c in candidates:
        v = value_score(c)
        idv = verify_official(c)
        is_a1 = idv["authority_level"] == "A1" and idv["verified"]
        if v < STOP_THRESHOLD:
            rejected.append({"source_id": c["source_id"], "value": v, "reason": f"value {v} < stop {STOP_THRESHOLD}"})
            continue
        if not is_a1:
            rejected.append({"source_id": c["source_id"], "value": v,
                             "reason": f"not a verified A1 official publisher ({idv['authority_level']})"})
            continue
        reach = reachability.get(c["source_id"], "unknown")
        admitted.append({
            "source_id": c["source_id"], "city": c["city"], "tier": c["tier"], "roles": c.get("roles", []),
            "value": v, "authority_level": "A1", "official_host": c["host"],
            "identity_reasons": idv["reasons"],
            "reachable_server_side": reach,
            # honest: an original is CONFIRMED only when fetchable; server-side stdlib cannot reach these
            # city portals yet (JS/TLS), so they are pending a headless fetcher. The municipality tier is
            # proven real by Beijing (fetched in the T049/T050 province cohort).
            "original_fetch_status": "pending_headless" if reach in ("js_rendered", "tls_blocked", "reachable_news_only", "unknown") else "confirmed",
            "cursor_2016": cursor_2016(c["source_id"]),
            "value_rationale": f"{c['tier']} + roles {c.get('roles', [])} -> value {v}",
        })
    admitted.sort(key=lambda x: x["value"], reverse=True)
    return {"admitted": admitted, "rejected": rejected,
            "stop_threshold": STOP_THRESHOLD, "candidates": len(candidates)}


# batch (分批) admission by value tier: highest-authority first, so each wave is gated before the next.
_WAVE_OF_TIER = {"municipality": 1, "sub_provincial_plan": 1, "sub_provincial": 2, "key_economic": 3}

def plan_waves(admitted):
    """Group admitted cities into value-tiered onboarding waves (the T050 batch mechanism runs each)."""
    waves = {}
    for a in admitted:
        w = _WAVE_OF_TIER.get(a["tier"], 3)
        waves.setdefault(w, []).append(a["source_id"])
    return {f"wave_{w}": sorted(waves[w]) for w in sorted(waves)}
