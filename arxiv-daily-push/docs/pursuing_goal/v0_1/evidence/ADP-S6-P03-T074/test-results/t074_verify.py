#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P03-T074 acceptance: Shadow source-silence prediction.

Acceptance (TASK_INDEX row 74): 优于简单发布周期基线；误报和人工价值可量化。
  (beats a simple publication-cycle baseline; false alarms and human value are quantifiable.)
Objective also requires distinguishing abnormal source silence from a collection failure.

Deterministic. Re-derives from the TOOL (silence_predictor) + fixtures -- never trusts the report.
Negative controls: the baseline false-alarms on a variable source (model does not); the baseline cannot
distinguish a collection failure from source silence (model does).
"""
import importlib.util
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import silence_predictor as SP

T074 = V01 / "evidence" / "ADP-S6-P03-T074"
spec = importlib.util.spec_from_file_location("bsp", str(T074 / "build_silence_predictor.py"))
bsp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bsp)

fails = []
ev = SP.evaluate(bsp.CASES)
m, b = ev["model"], ev["baseline"]
print("model:", m)
print("baseline:", b)

# =============================================================== 1) 优于简单发布周期基线
if not (m["accuracy"] > b["accuracy"]):
    fails.append(f"model accuracy {m['accuracy']} does not beat baseline {b['accuracy']}")
if not (m["false_alarm_rate"] < b["false_alarm_rate"]):
    fails.append(f"model false-alarm rate {m['false_alarm_rate']} not lower than baseline {b['false_alarm_rate']}")
if not (m["human_value"] >= b["human_value"]):
    fails.append("model human value does not beat/equal the baseline")

# =============================================================== 2) 误报和人工价值可量化
for name, s in (("model", m), ("baseline", b)):
    if not isinstance(s["false_alarm_rate"], (int, float)):
        fails.append(f"{name} false_alarm_rate not quantified")
    if not isinstance(s["human_value"], (int, float)):
        fails.append(f"{name} human_value not quantified")
    if not isinstance(s["false_alarms"], int):
        fails.append(f"{name} false_alarms count not quantified")
print(f"quantified: model false_alarm_rate={m['false_alarm_rate']} human_value={m['human_value']}; "
      f"baseline false_alarm_rate={b['false_alarm_rate']} human_value={b['human_value']}")

# =============================================================== 3) distinguish silence vs collection failure
# the collection-failure case (recent_fetch_errors > 0) is classified collection_failure by the model,
# and the baseline (cadence-only) canNOT distinguish it -- it calls it source silence or normal.
cf = next(c for c in bsp.CASES if c["truth"] == "collection_failure")
if SP.classify(cf["source"], cf["as_of"]) != "collection_failure":
    fails.append("the model did not classify a fetch failure as collection_failure")
# non-vacuous control: the cadence-only baseline actively MISCLASSIFIES the collection failure as
# source silence (it gets it WRONG), which is the model's advantage.
b_cf = SP._baseline_classify(cf["source"], cf["as_of"])
if b_cf == cf["truth"]:
    fails.append("control broken: the baseline should NOT correctly identify the collection failure")
if b_cf != "abnormal_silence":
    fails.append(f"the baseline should misclassify the fetch failure as abnormal_silence, got {b_cf!r}")
# NEGATIVE CONTROL: the variable source at 45d silence is NORMAL (model), but the baseline false-alarms.
var_case = next(c for c in bsp.CASES if c["truth"] == "normal" and c["source"]["history"] == bsp.VARIABLE)
if SP.classify(var_case["source"], var_case["as_of"]) != "normal":
    fails.append("model wrongly flagged a naturally-variable source as abnormal (false alarm)")
if SP._baseline_classify(var_case["source"], var_case["as_of"]) != "abnormal_silence":
    fails.append("control broken: the baseline should false-alarm on the variable source")
# a genuinely-overdue regular source IS abnormal_silence (model catches real silence)
ab = next(c for c in bsp.CASES if c["truth"] == "abnormal_silence")
if SP.classify(ab["source"], ab["as_of"]) != "abnormal_silence":
    fails.append("model missed a genuinely abnormal silence")
print("distinguish: collection_failure caught by model not baseline; variable source normal (model) vs "
      "false-alarm (baseline); real silence caught")

# BORDERLINE RECALL PROBE: the model's threshold is not blindly wide -- for the VARIABLE source
# (median 35 + 3*MAD 10 = 65) it flips at the boundary of the source's own variability: a gap just
# ABOVE the threshold is abnormal, just below is normal.
var_src = {"history": bsp.VARIABLE, "recent_fetch_errors": 0}
last = max(bsp.VARIABLE)
if SP.classify(var_src, last + 66) != "abnormal_silence":
    fails.append("model did not flag a gap just above its variability threshold as abnormal")
if SP.classify(var_src, last + 65) != "normal":
    fails.append("model flagged a gap at/below its variability threshold (over-eager)")
print("recall boundary: variable source flips normal->abnormal right at its variability threshold (65/66)")

# reproducible
if SP.evaluate(bsp.CASES) != ev:
    fails.append("evaluate is not reproducible")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
