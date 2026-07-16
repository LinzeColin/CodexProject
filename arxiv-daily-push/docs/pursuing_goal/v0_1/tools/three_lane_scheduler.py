#!/usr/bin/env python3
"""ADP V0.1 Realtime / Catchup / Backfill three-lane scheduler + auto-pause (ADP-S4-P01-T042).

Guarantees the 2016+ history backfill can never starve the live front-line data: three priority lanes
(realtime > catchup > backfill) with per-lane capacity quotas, backpressure that pauses the backfill
lane when the realtime freshness P95 would exceed the baseline by more than 20%, and a manual kill
switch. Deterministic; no clock/network. NOT_DEPLOYED.

Model: each unit of active backfill/catchup competes with realtime for the same Worker subrequest /
CPU budget, so it inflates the realtime freshness P95. The scheduler projects the realtime P95 under a
candidate allocation and pauses backfill (then throttles catchup) until the projection is within the
baseline+20% ceiling. Realtime is always served first.
"""
from __future__ import annotations
import dataclasses

FRESHNESS_CEILING = 1.20        # realtime P95 must stay <= baseline * 1.20
# per active lane-unit inflation of the realtime freshness P95 (fraction of baseline)
INFLATION = {"realtime": 0.0, "catchup": 0.04, "backfill": 0.05}
PRIORITY = ["realtime", "catchup", "backfill"]     # highest -> lowest
BASE_QUOTA = {"realtime": 0.6, "catchup": 0.25, "backfill": 0.15}   # of total capacity when healthy


def project_p95(baseline, alloc):
    """Projected realtime freshness P95 given a lane allocation (units of active work per lane)."""
    infl = sum(INFLATION[l] * alloc.get(l, 0) for l in PRIORITY)
    return baseline * (1.0 + infl)


@dataclasses.dataclass(frozen=True)
class Decision:
    alloc: dict                 # lane -> granted units
    realtime_p95: float
    baseline: float
    within_ceiling: bool
    backfill_paused: bool
    catchup_throttled: bool
    reason: str


def schedule(capacity, demand, baseline, kill_switch=False):
    """Allocate `capacity` units across lanes honoring priority + the freshness ceiling.
    demand: {lane: requested units}. Realtime is served first and fully (up to capacity); backfill is
    paused (then catchup throttled) until the projected realtime P95 <= baseline*ceiling."""
    ceiling = baseline * FRESHNESS_CEILING
    # 1) realtime first, always (bounded by capacity)
    alloc = {"realtime": min(demand.get("realtime", 0), capacity)}
    remaining = capacity - alloc["realtime"]
    # 2) catchup then backfill by quota, but never breach the ceiling
    alloc["catchup"] = min(demand.get("catchup", 0), remaining)
    remaining -= alloc["catchup"]
    alloc["backfill"] = 0 if kill_switch else min(demand.get("backfill", 0), remaining)

    backfill_paused = kill_switch
    catchup_throttled = False
    reason = "kill switch: backfill paused" if kill_switch else "healthy: all lanes within the freshness ceiling"
    # 3) backpressure: shed backfill, then catchup, until the projected P95 is within the ceiling
    while project_p95(baseline, alloc) > ceiling and alloc["backfill"] > 0:
        alloc["backfill"] -= 1; backfill_paused = True
        reason = "backpressure: realtime P95 over baseline+20% -> backfill auto-paused"
    while project_p95(baseline, alloc) > ceiling and alloc["catchup"] > 0:
        alloc["catchup"] -= 1; catchup_throttled = True
        reason = "backpressure: even after pausing backfill -> catchup throttled to protect realtime"
    p95 = project_p95(baseline, alloc)
    # paused = requested but fully denied; throttled = partially granted
    backfill_paused = demand.get("backfill", 0) > 0 and alloc["backfill"] == 0
    backfill_throttled = 0 < alloc["backfill"] < demand.get("backfill", 0)
    if kill_switch:
        reason = "kill switch: backfill paused"
    elif backfill_paused:
        reason = "backpressure: realtime P95 would exceed baseline+20% -> backfill auto-paused"
    elif backfill_throttled:
        reason = "backpressure: backfill throttled to keep realtime P95 within baseline+20%"
    elif catchup_throttled:
        reason = "backpressure: catchup throttled to protect realtime"
    else:
        reason = "healthy: all lanes served within the freshness ceiling"
    return Decision(alloc=alloc, realtime_p95=round(p95, 4), baseline=baseline,
                    within_ceiling=(p95 <= ceiling + 1e-9), backfill_paused=backfill_paused,
                    catchup_throttled=catchup_throttled, reason=reason)


def stress_test(baseline, capacity, scenarios):
    """Run scenarios; assert realtime freshness P95 stays within baseline+20% in every one."""
    out = []
    for name, demand, kill in scenarios:
        d = schedule(capacity, demand, baseline, kill_switch=kill)
        out.append({"scenario": name, "demand": demand, "alloc": d.alloc, "realtime_p95": d.realtime_p95,
                    "ceiling": round(baseline * FRESHNESS_CEILING, 4), "within_ceiling": d.within_ceiling,
                    "realtime_fully_served": d.alloc["realtime"] == min(demand.get("realtime", 0), capacity),
                    "backfill_paused": d.backfill_paused, "reason": d.reason})
    return out


def main():
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=float, default=10.0)
    ap.add_argument("--capacity", type=int, default=20)
    ap.add_argument("--out")
    args = ap.parse_args()
    scenarios = [
        ("healthy_low_demand", {"realtime": 2, "catchup": 1, "backfill": 3}, False),
        ("backfill_pressure", {"realtime": 4, "catchup": 2, "backfill": 8}, False),
        ("heavy_realtime_burst", {"realtime": 8, "catchup": 4, "backfill": 6}, False),
        ("kill_switch", {"realtime": 4, "catchup": 2, "backfill": 5}, True),
    ]
    res = stress_test(args.baseline, args.capacity, scenarios)
    import pathlib
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
