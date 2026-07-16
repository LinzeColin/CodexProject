#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P03-T076 generator -- full-horizon Shadow closeout over the real S6-P03 predictors.

Skill dimension  : the six rolling-origin windows of the two T075 pilots (ACCEL + DIFFUSION), each with a
                   model Brier vs an unconditional baseline Brier (sustained skill = every window positive).
Calibration      : the reliability of the pooled T075 validation predictions (ECE).
Lead value       : the earliest actionable horizon (90d) with the net human value of the correct early
                   catches, including T074's source-silence catches.

Renders the honest go/stop release decision + disable flag. Deterministic; no network / clock / randomness.
"""
import json
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import diffusion_predictor as DP
import rolling_backtest as RB
import horizon_shadow_closeout as HC
import silence_predictor as SP

import importlib.util
_b = importlib.util.spec_from_file_location(
    "bdp", str(V01 / "evidence" / "ADP-S6-P03-T075" / "build_diffusion_predictor.py"))
bdp = importlib.util.module_from_spec(_b); _b.loader.exec_module(bdp)
_s = importlib.util.spec_from_file_location(
    "bsp", str(V01 / "evidence" / "ADP-S6-P03-T074" / "build_silence_predictor.py"))
bsp = importlib.util.module_from_spec(_s); _s.loader.exec_module(bsp)


def gather_shadow():
    """Pool the real S6-P03 shadow: per-window Brier (skill) + pooled predictions (calibration) from the
    two T075 pilots, plus T074's source-silence human value (lead)."""
    windows, forecasts, correct, false_alarms = [], [], 0, 0
    for tid, pil in bdp.PILOTS.items():
        h = DP.PREDEFINED_TARGETS[tid]["horizon_days"]
        for sp in RB.rolling_splits(pil["cases"], pil["origins"], h):
            y = [c["label"] for c in sp["val"]]
            m = DP.fit_model(sp["train"])
            mb = sum((DP.predict(m, c) - t) ** 2 for c, t in zip(sp["val"], y)) / len(y)
            bb = sum((DP.baseline_predict(m, c) - t) ** 2 for c, t in zip(sp["val"], y)) / len(y)
            windows.append({"target": tid, "origin": sp["origin"],
                            "model_brier": round(mb, 6), "baseline_brier": round(bb, 6)})
            for c in sp["val"]:
                p = DP.predict(m, c)
                forecasts.append({"prob": round(p, 6), "label": c["label"]})
                if p > 0.5:                                # a surfaced "likely" call
                    correct += (c["label"] == 1)
                    false_alarms += (c["label"] == 0)
    # T074 source-silence contributes real early catches (abnormal silence / collection failure caught).
    t074 = SP.evaluate(bsp.CASES)["model"]
    correct += t074.get("correct_catches", t074.get("human_value", 0))
    return {"windows": windows, "forecasts": forecasts,
            "correct_catches": correct, "false_alarms": false_alarms,
            "earliest_horizon_days": min(DP.PREDEFINED_TARGETS[t]["horizon_days"] for t in DP.PREDEFINED_TARGETS)}


def build():
    sh = gather_shadow()
    result = HC.closeout(sh["windows"], sh["forecasts"], lead_days=sh["earliest_horizon_days"],
                         correct_catches=sh["correct_catches"], false_alarms=sh["false_alarms"], tol=0.15)
    report = {"iteration": "ITER-20260716-ADP-V01-FINAL-EXECUTION", "task": "ADP-S6-P03-T076",
              "release_mode": "SHADOW",
              "shadow_inputs": {"n_windows": len(sh["windows"]), "n_forecasts": len(sh["forecasts"]),
                                "correct_catches": sh["correct_catches"], "false_alarms": sh["false_alarms"],
                                "earliest_horizon_days": sh["earliest_horizon_days"],
                                "predictors": ["T074 source-silence", "T075 ACCEL-PILOT", "T075 DIFFUSION-A0-A1"]},
              "windows": sh["windows"], **result}
    return report


if __name__ == "__main__":
    rep = build()
    d = rep["release_decision"]
    print("skill:", {k: rep["skill"][k] for k in ("aggregate_bss", "min_window_bss", "positive", "sustained", "skill_ok")})
    print("calibration:", {k: rep["calibration"][k] for k in ("ece", "max_reliability_error", "acceptable")})
    print("lead_value:", rep["lead_value"])
    print("DECISION:", d["decision"], "| show_to_users:", d["show_to_users"],
          "| disable_flag:", d["disable_flag"], "| failed:", d["failed_criteria"])
    out = V01 / "evidence" / "ADP-S6-P03-T076" / "horizon_shadow_closeout_report.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)
