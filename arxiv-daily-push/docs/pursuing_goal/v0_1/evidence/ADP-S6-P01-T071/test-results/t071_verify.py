#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P01-T071 acceptance: historical frequency + seasonality statistical baselines.

Acceptance (TASK_INDEX row 71): 每个目标至少有一个可重跑基线；无基线不得开发高级模型。
  (every target has at least one reproducible baseline; no advanced model without a baseline.)

Deterministic. Re-derives from the TOOL (baselines) + fixtures -- never trusts the report. Negative
control: a target with NO baseline must be refused advanced-model development; and the baselines must be
genuine (frequency == the actual base rate; probabilities in [0,1]; reproducible across runs).
"""
import importlib.util
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import baselines as BL

T071 = V01 / "evidence" / "ADP-S6-P01-T071"
spec = importlib.util.spec_from_file_location("bbl", str(T071 / "build_baselines.py"))
bbl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bbl)

fails = []
report = BL.benchmark(bbl.TARGETS, bbl.HISTORY, bbl.EVAL)

# =============================================================== 1) 每个目标至少有一个可重跑基线
# targets WITH history each get a reproducible frequency + seasonality baseline with valid metrics
WITH_HISTORY = ("G1", "G2")
for tid in WITH_HISTORY:
    e = report.get(tid)
    if not e or not e.get("has_reproducible_baseline") or not e.get("baselines"):
        fails.append(f"{tid} has no reproducible baseline")
        continue
    for kind in BL.BASELINE_KINDS:
        if kind not in e["baselines"]:
            fails.append(f"{tid} missing the {kind} baseline")
        m = e["baselines"].get(kind, {}).get("metrics", {})
        if m.get("brier") is None or not (0.0 <= m["brier"] <= 1.0):
            fails.append(f"{tid}.{kind} brier out of range: {m.get('brier')}")

# reproducible: a second benchmark run is identical (numeric report, no hidden state)
report2 = BL.benchmark(bbl.TARGETS, bbl.HISTORY, bbl.EVAL)
if report != report2:
    fails.append("benchmark is not reproducible across runs")
print(f"baselines: every target has frequency+seasonality with in-range Brier; benchmark reproducible")

# the frequency baseline equals the ACTUAL historical base rate (interpretable + correct)
g1_rate = sum(h["label"] for h in bbl.HISTORY["G1"]) / len(bbl.HISTORY["G1"])
if abs(report["G1"]["baselines"]["frequency"]["rate"] - g1_rate) > 1e-9:
    fails.append(f"G1 frequency rate {report['G1']['baselines']['frequency']['rate']} != base rate {g1_rate}")

# every predicted probability is a valid probability in [0,1]
freq = BL.frequency_baseline(bbl.HISTORY["G1"])
seas = BL.seasonality_baseline(bbl.HISTORY["G1"])
for o in ["2023-03-01", "2023-08-01", "2019-06-15", "malformed", "2023-13-40"]:
    for b in (freq, seas):
        p = b["predict"](o)
        if not (0.0 <= p <= 1.0):
            fails.append(f"{b['kind']} produced an invalid probability {p} for {o!r}")
# an unseen month falls back to the (smoothed) global rate, not a hard 0/1
p_unseen = seas["predict"]("2023-06-15")   # June never appears in G1 history
if not (0.0 < p_unseen < 1.0):
    fails.append(f"seasonality did not fall back to a smoothed global rate for an unseen month: {p_unseen}")
print(f"correctness: frequency == base rate ({g1_rate}); probabilities in [0,1]; unseen month -> smoothed global {p_unseen}")

# the baselines are meaningful, not trivial: on a seasonal target the seasonality baseline BEATS the
# base-rate baseline (lower Brier) -- so a cheap interpretable baseline captures real signal.
if not (report["G1"]["baselines"]["seasonality"]["metrics"]["brier"]
        < report["G1"]["baselines"]["frequency"]["metrics"]["brier"]):
    fails.append("seasonality did not beat frequency on a seasonal target -> baselines not meaningful")
print("meaningful: seasonality beats base-rate on the seasonal target (a cheap baseline captures signal)")

# =============================================================== 2) 无基线不得开发高级模型
if not BL.may_develop_advanced("G1", report):
    fails.append("a target WITH a reproducible baseline was refused advanced development")
# NEGATIVE CONTROL: a target with NO HISTORY (G0, in the benchmark) has no reproducible baseline and
# must be refused advanced development -- this is the 无基线不得开发高级模型 case, in-benchmark.
if report["G0"]["has_reproducible_baseline"]:
    fails.append("a no-history target was marked as having a reproducible baseline")
if report["G0"]["n_history"] != 0:
    fails.append("G0 should have zero history")
if BL.may_develop_advanced("G0", report):
    fails.append("a no-history target (no real baseline) was allowed advanced development (gate vacuous)")
# a target absent from the report is refused
if BL.may_develop_advanced("G9", report):
    fails.append("a target absent from the benchmark was allowed advanced development")
if BL.may_develop_advanced("does-not-exist", report):
    fails.append("an unknown target was allowed advanced development")
# a report entry stripped of its baselines must also be refused (gate keys on the baseline, not the key)
if BL.may_develop_advanced("G1", {"G1": {"has_reproducible_baseline": True, "baselines": {}}}):
    fails.append("a target with an empty baselines set was allowed advanced development")
print("gate: G1 (has baseline) may develop advanced; G0(no history) / G9(absent) / unknown / empty-baselines refused")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
