#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P02-T072 acceptance: 2016+ rolling-origin backtest.

Acceptance (TASK_INDEX row 72): 至少三个滚动窗口；训练/验证时间不交叉；结果可重跑。
  (at least three rolling windows; train/validation do not cross in time; results are reproducible.)

Deterministic. Re-derives from the TOOL (rolling_backtest) + fixtures -- never trusts the report.
Negative control proves discrimination: a temporally-crossing split (a train sample observed after the
origin, or a val sample observed at/before it) must trip assert_no_time_crossing.
"""
import copy
import importlib.util
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import rolling_backtest as RB

T072 = V01 / "evidence" / "ADP-S6-P02-T072"
spec = importlib.util.spec_from_file_location("brb", str(T072 / "build_rolling_backtest.py"))
brb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brb)

fails = []
result = RB.run_backtest(brb.TARGET, brb.OUTCOMES, brb.ORIGINS, brb.HORIZON)
windows = result["windows"]
splits = RB.rolling_splits(brb.OUTCOMES, brb.ORIGINS, brb.HORIZON)
print("n_windows:", result["n_windows"], "manifest:", result["manifest"])

# =============================================================== 1) 至少三个滚动窗口
if result["n_windows"] < 3:
    fails.append(f"fewer than 3 rolling windows: {result['n_windows']}")
if len(windows) != len(brb.ORIGINS):
    fails.append("one window per rolling origin expected")

# =============================================================== 2) 训练/验证时间不交叉
def _d(s):
    return RB._d(s)
for sp in splits:
    # the tool's own check passes
    RB.assert_no_time_crossing(sp)
    od = _d(sp["origin"])
    endd = _d(sp["val_end"])
    # every train observed <= origin; every val in (origin, val_end]; disjoint sets
    if any(_d(x["observed_at"]) > od for x in sp["train"]):
        fails.append(f"{sp['origin']}: a training sample is observed after the origin")
    if any(not (od < _d(x["observed_at"]) <= endd) for x in sp["val"]):
        fails.append(f"{sp['origin']}: a validation sample is outside (origin, origin+horizon]")
    train_ids = {id(x) for x in sp["train"]}
    if any(id(x) in train_ids for x in sp["val"]):
        fails.append(f"{sp['origin']}: a sample is in both train and val (temporal overlap)")
    # each training set is leak-proof as of its origin (T070)
    import dataset_snapshot as DS
    DS.assert_no_leakage({"docs": sp["train"]}, sp["origin"])
print("no time crossing: every window has train observed<=origin < val observed, train leak-proof")

# NEGATIVE CONTROL: a crossing split must be CAUGHT. Move a training sample to after the origin.
bad = copy.deepcopy(splits[0])
bad["train"] = bad["train"] + [{"observed_at": "2019-06-01", "label": 1}]   # after origin 2019-01-01
try:
    RB.assert_no_time_crossing(bad)
    fails.append("assert_no_time_crossing did NOT catch a training sample observed after the origin")
except AssertionError:
    pass
# a val sample observed at/before the origin must also be caught
bad2 = copy.deepcopy(splits[0])
bad2["val"] = bad2["val"] + [{"observed_at": "2018-06-01", "label": 1}]   # before origin
try:
    RB.assert_no_time_crossing(bad2)
    fails.append("assert_no_time_crossing did NOT catch a validation sample at/before the origin")
except AssertionError:
    pass
print("crossing control: a post-origin train sample and a pre-origin val sample both trip the guard")

# =============================================================== 3) 结果可重跑
result2 = RB.run_backtest(brb.TARGET, brb.OUTCOMES, brb.ORIGINS, brb.HORIZON)
if result != result2:
    fails.append("rolling backtest is not reproducible across runs")
if result["manifest"] != result2["manifest"]:
    fails.append("run manifest hash differs across identical runs")
# manifest is content-sensitive: a changed horizon changes the manifest
alt = RB.run_backtest(brb.TARGET, brb.OUTCOMES, brb.ORIGINS, 180)
if alt["manifest"] == result["manifest"]:
    fails.append("a changed horizon did not change the run manifest")
print(f"reproducible: two runs identical (manifest {result['manifest']}); changed horizon -> different manifest")
# the manifest also reflects min_history (runs differing only in it must not collide)
mh = RB.run_backtest(brb.TARGET, brb.OUTCOMES, brb.ORIGINS, brb.HORIZON, min_history=99)
if mh["manifest"] == result["manifest"]:
    fails.append("a changed min_history did not change the run manifest")

# DEDICATED LEAK-GUARD CONTROL: a training set containing a future-observed sample must trip the T070
# guard (independent of assert_no_time_crossing).
import dataset_snapshot as DS2
try:
    DS2.assert_no_leakage({"docs": splits[0]["train"] + [{"canonical_id": "x", "observed_at": "2025-01-01"}]},
                          splits[0]["origin"])
    fails.append("the T070 leakage guard did not catch a future-observed training sample")
except DS2.LeakageError:
    pass
# a calendar-invalid date is excluded (not a crash): an outcome dated 2019-02-30 lands in neither split
weird = brb.OUTCOMES + [{"observed_at": "2019-02-30", "label": 1}]
sp0 = RB.rolling_splits(weird, ["2019-01-01"], 365)[0]
if any(x.get("observed_at") == "2019-02-30" for x in sp0["train"] + sp0["val"]):
    fails.append("a calendar-invalid date was not excluded from the splits")
print("robustness: manifest reflects min_history; T070 leak guard catches a future train sample; calendar-invalid date excluded (no crash)")

# rolling forward is genuine time-order validation: train grows with the origin, and the seasonality
# baseline generalizes better as more March history accumulates (Brier non-increasing).
train_ns = [w["train_n"] for w in windows]
if train_ns != sorted(train_ns) or len(set(train_ns)) < 2:
    fails.append(f"training window did not grow as the origin rolled forward: {train_ns}")
seas_briers = [w["seas_metrics"]["brier"] for w in windows]
if any(b is None for b in seas_briers):
    fails.append("a window had no validation metric")
elif not all(seas_briers[i] >= seas_briers[i + 1] for i in range(len(seas_briers) - 1)):
    fails.append(f"seasonality Brier did not improve (non-increasing) across rolling windows: {seas_briers}")
print(f"time-order: train_n grows {train_ns}; seasonality Brier improves across windows {seas_briers}")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
