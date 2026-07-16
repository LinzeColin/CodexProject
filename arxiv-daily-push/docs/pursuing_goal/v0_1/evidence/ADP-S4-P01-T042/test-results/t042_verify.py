#!/usr/bin/env python3
"""ADP-S4-P01-T042 acceptance: Realtime/Catchup/Backfill three-lane scheduler + auto-pause.

Acceptance (TASK_INDEX): 压力测试时 realtime freshness P95 <=基线+20%；超阈值自动暂停 backfill。
Deterministic. Backfill (2016+ history) must never starve the live front-line data.
"""
import sys, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import three_lane_scheduler as S  # noqa: E402

BASELINE, CAP = 10.0, 20
SCEN = [
    ("healthy_low_demand", {"realtime": 2, "catchup": 1, "backfill": 3}, False),
    ("backfill_pressure", {"realtime": 4, "catchup": 2, "backfill": 8}, False),
    ("heavy_realtime_burst", {"realtime": 8, "catchup": 4, "backfill": 6}, False),
    ("kill_switch", {"realtime": 4, "catchup": 2, "backfill": 5}, True),
]
res = S.stress_test(BASELINE, CAP, SCEN)
ceiling = BASELINE * S.FRESHNESS_CEILING
fails = []
for r in res:
    print(f"{r['scenario']}: bf {r['demand']['backfill']}->{r['alloc']['backfill']} rt_full={r['realtime_fully_served']} "
          f"p95={r['realtime_p95']}<= {r['ceiling']} within={r['within_ceiling']} bf_paused={r['backfill_paused']}")

# --- 1) INVARIANT: realtime freshness P95 <= baseline+20% in EVERY scenario -----------------
for r in res:
    if not r["within_ceiling"] or r["realtime_p95"] > ceiling + 1e-9:
        fails.append(f"{r['scenario']}: realtime P95 {r['realtime_p95']} exceeds ceiling {ceiling}")
    if not r["realtime_fully_served"]:
        fails.append(f"{r['scenario']}: realtime not fully served (starved by lower lanes)")

byname = {r["scenario"]: r for r in res}
# --- 2) healthy -> backfill runs; --- 3) pressure/burst -> backfill auto-paused/throttled ----
if byname["healthy_low_demand"]["alloc"]["backfill"] <= 0:
    fails.append("backfill did not run in the healthy scenario")
if byname["healthy_low_demand"]["backfill_paused"]:
    fails.append("backfill wrongly paused when healthy")
if not byname["heavy_realtime_burst"]["backfill_paused"] or byname["heavy_realtime_burst"]["alloc"]["backfill"] != 0:
    fails.append("realtime burst did not auto-pause backfill")
# backfill granted decreases monotonically as pressure rises
granted = [byname["healthy_low_demand"]["alloc"]["backfill"],
           byname["backfill_pressure"]["alloc"]["backfill"],
           byname["heavy_realtime_burst"]["alloc"]["backfill"]]
if not (granted[0] >= granted[1] >= granted[2]):
    fails.append(f"backfill grant not monotonic under rising pressure: {granted}")
print(f"\nbackfill grant under rising realtime pressure: {granted} (monotonic non-increasing)")

# --- 4) kill switch -> backfill fully paused ------------------------------------------------
if byname["kill_switch"]["alloc"]["backfill"] != 0 or not byname["kill_switch"]["backfill_paused"]:
    fails.append("kill switch did not pause backfill")

# priority rules + quotas present
if S.PRIORITY != ["realtime", "catchup", "backfill"]:
    fails.append("priority order wrong")
if set(S.BASE_QUOTA) != {"realtime", "catchup", "backfill"}:
    fails.append("queue quotas missing a lane")
print("priority realtime>catchup>backfill; per-lane quotas + backpressure + kill switch present")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
