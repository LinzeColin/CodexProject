#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P03-T075 acceptance: Shadow topic-acceleration & central->local (A0->A1->A2) diffusion.

Acceptance (TASK_INDEX row 75): 三个窗口优于基线；目标和 horizon 预定义；无确定语气.
  (three windows beat the baseline; targets and horizon are predefined; no deterministic tone.)
Deliverables: two pilot targets, support/counter signals, a lead-time report.

Deterministic. Re-derives from the TOOL (diffusion_predictor) + the fixture, and RE-COMPUTES each
window's Brier with its OWN formula -- it never trusts the report's numbers. Validation windows are
noisy (they carry impurities), so the model is imperfect and could lose; it must win on aggregate.

Load-bearing negative controls (each is non-vacuous -- it fails if the property it checks is broken):
  * REAL feature ablation -- a model refit on signal-BLINDED cases (support=counter=0) collapses to the
    baseline and does NOT beat it, proving the win comes from the support/counter signal, not the harness;
  * anti-correlated probe -- when the signal is INVERTED so it tracks the wrong outcome, the model does
    NOT beat the baseline, proving the win is contingent on the signal actually predicting the label;
  * the deterministic-tone gate REJECTS certainty phrasing (a range of markers) and 0/1 probabilities;
  * a post-hoc (non-predefined) target is refused, both by is_predefined and by rolling_backtest;
  * a time-crossing split is rejected (no leakage).
"""
import importlib.util
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import diffusion_predictor as DP
import rolling_backtest as RB

T075 = V01 / "evidence" / "ADP-S6-P03-T075"
spec = importlib.util.spec_from_file_location("bdp", str(T075 / "build_diffusion_predictor.py"))
bdp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bdp)

fails = []


def brier(preds, labels):                     # the verifier's OWN scoring formula (independent)
    return sum((p - y) ** 2 for p, y in zip(preds, labels)) / len(labels)


def _blind(cases):                            # strip the support/counter signal -> every net_signal == 0
    return [dict(c, support_signals=0, counter_signals=0) for c in cases]


def _invert(cases):                           # invert the signal so it tracks the WRONG outcome
    return [dict(c, support_signals=c["counter_signals"], counter_signals=c["support_signals"])
            for c in cases]


# ================================================ 2) 目标和 horizon 预定义
for tid in ("ACCEL-PILOT", "DIFFUSION-A0-A1"):
    if not DP.is_predefined(tid):
        fails.append(f"pilot target {tid} is not predefined")
    if not isinstance(DP.PREDEFINED_TARGETS[tid]["horizon_days"], int):
        fails.append(f"{tid} has no predefined integer horizon")
# negative control: a target invented after seeing the data is NOT predefined -> refused two ways.
if DP.is_predefined("POST-HOC-CHERRY-PICK"):
    fails.append("control broken: a post-hoc target must not count as predefined")
try:
    DP.rolling_backtest(bdp.ACCEL_CASES, bdp.ACCEL_ORIGINS, 90, target_id="POST-HOC-CHERRY-PICK")
    fails.append("control broken: rolling_backtest must refuse a non-predefined target")
except ValueError:
    pass
print("predefined:", {t: DP.PREDEFINED_TARGETS[t]["horizon_days"] for t in DP.PREDEFINED_TARGETS})

# ================================================ 1) 三个窗口优于基线 (re-derived independently)
per_pilot_briers = {}
for tid, pilot in bdp.PILOTS.items():
    horizon = DP.PREDEFINED_TARGETS[tid]["horizon_days"]
    splits = RB.rolling_splits(pilot["cases"], pilot["origins"], horizon)
    if len(splits) < 3:
        fails.append(f"{tid}: fewer than three rolling windows ({len(splits)})")
    n_beats, profile = 0, []
    for sp in splits:
        RB.assert_no_time_crossing(sp)                          # time safety per window
        y = [c["label"] for c in sp["val"]]
        if not y:
            fails.append(f"{tid} @ {sp['origin']}: empty validation window")
            continue
        model = DP.fit_model(sp["train"])
        m = brier([DP.predict(model, c) for c in sp["val"]], y)          # verifier-computed Brier
        b = brier([DP.baseline_predict(model, c) for c in sp["val"]], y)
        profile.append((round(m, 4), round(b, 4)))

        # REAL FEATURE-ABLATION control: refit on signal-blinded cases -> collapses to the baseline
        # (every case falls in one bucket, whose rate equals the global rate). It must NOT beat baseline.
        bmodel = DP.fit_model(_blind(sp["train"]))
        abl = brier([DP.predict(bmodel, c) for c in _blind(sp["val"])], y)
        if abl < b - 1e-9:
            fails.append(f"{tid} @ {sp['origin']}: signal-blind model beat the baseline (ablation broke)")
        if abs(abl - b) > 1e-9:
            fails.append(f"{tid} @ {sp['origin']}: signal-blind model {abl} should equal baseline {b}")

        # CORRUPTED-SIGNAL probe: keep the TRUE model but flip the signal on the validation cases only
        # (train stays honest). The model, which genuinely uses the signal, now mispredicts and must NOT
        # beat the baseline -- proving it depends on the signal being right, not on the harness.
        inv = brier([DP.predict(model, c) for c in _invert(sp["val"])], y)
        if inv < b - 1e-9:
            fails.append(f"{tid} @ {sp['origin']}: a corrupted validation signal still beat the baseline")

        if m < b:
            n_beats += 1
        else:
            fails.append(f"{tid} @ {sp['origin']}: model Brier {m:.4f} did not beat baseline {b:.4f}")
    per_pilot_briers[tid] = profile
    print(f"{tid}: {n_beats}/{len(splits)} windows beat baseline (h{horizon}d) profile={profile}")
    if n_beats < 3:
        fails.append(f"{tid}: only {n_beats} windows beat the baseline (need 3)")
    bt = DP.rolling_backtest(pilot["cases"], pilot["origins"], horizon, target_id=tid)
    if not (bt["n_windows"] >= 3 and bt["beats_all"]):
        fails.append(f"{tid}: tool rolling_backtest does not report beats_all over >=3 windows")

# the two pilots are DISTINCT demonstrations, not the same numbers relabeled.
if per_pilot_briers.get("ACCEL-PILOT") == per_pilot_briers.get("DIFFUSION-A0-A1"):
    fails.append("the two pilots produced identical Brier profiles -- they are clones, not independent")

# ================================================ 3) 无确定语气
rep = bdp.build()
for tid, p in rep["pilots"].items():
    for s in p["surfaced_predictions"]:
        if not (0.0 < s["prob"] < 1.0):
            fails.append(f"{tid}: surfaced prob {s['prob']} is not strictly inside (0,1)")
        DP.assert_no_deterministic_tone(s["statement"], s["prob"])       # hedged statements pass
# negative controls: the gate REJECTS a range of certainty markers and over-confident probabilities.
for bad_stmt in ("该中央政策必然扩散到各省", "this topic will definitely accelerate",
                 "该主题百分之百会加速", "扩散势必发生", "毫无疑问会扩散", "diffusion is inevitable"):
    try:
        DP.assert_no_deterministic_tone(bad_stmt, 0.7)
        fails.append(f"control broken: deterministic statement accepted: {bad_stmt!r}")
    except ValueError:
        pass
for bad_prob in (1.0, 0.0):
    try:
        DP.assert_no_deterministic_tone("估计概率", bad_prob)
        fails.append(f"control broken: over-confident probability {bad_prob} accepted")
    except ValueError:
        pass
print("no-deterministic-tone: hedged statements pass; certainty markers and 0/1 probs rejected")

# ================================================ deliverables: support/counter signals + lead time
for tid, pilot in bdp.PILOTS.items():
    if not all(("support_signals" in c and "counter_signals" in c) for c in pilot["cases"]):
        fails.append(f"{tid}: cases missing support/counter signals")
if DP.lead_time("2019-06-30", "2019-09-28") != 90:
    fails.append("lead_time miscomputed for the 90-day ACCEL horizon")
if DP.lead_time("2019-12-31", "2020-06-28") != 180:
    fails.append("lead_time miscomputed for the 180-day DIFFUSION horizon")
print("lead time:", rep["lead_time_report"])

# ================================================ time-crossing negative control
bad_split = {"origin": "2019-06-30", "val_end": "2019-09-28",
             "train": [{"observed_at": "2019-08-01", "label": 1}], "val": []}    # train AFTER origin
try:
    RB.assert_no_time_crossing(bad_split)
    fails.append("control broken: a training sample observed after the origin must raise")
except AssertionError:
    pass

# ================================================ reproducible
if DP.rolling_backtest(bdp.ACCEL_CASES, bdp.ACCEL_ORIGINS, 90) != \
   DP.rolling_backtest(bdp.ACCEL_CASES, bdp.ACCEL_ORIGINS, 90):
    fails.append("rolling_backtest is not reproducible")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
