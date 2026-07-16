#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P03-T076 -- full-horizon Shadow closeout & go/stop release decision.

Only a shadow forecaster that shows SUSTAINED skill across the whole horizon may ever be shown to users.
This module aggregates the S6-P03 shadow predictors (T074 source-silence, T075 topic-acceleration &
A0->A1 diffusion) over their full rolling horizon and renders an HONEST go/stop decision:

  GO (show to users)  iff  Brier skill is positive AND stable (every window keeps positive skill --
                            sustained, not one lucky window)
                      AND  calibration is acceptable (reliability error within tolerance)
                      AND  user lead value is clear (predictions arrive early enough with net value)
  STOP (disable)      otherwise -- with a disable flag and the list of failed criteria.

The gate must be able to STOP: a shadow whose skill regresses in any window, or is miscalibrated, or has
no lead value, returns STOP. release_mode SHADOW; no production side effects; deterministic (no network,
clock, or randomness). Reuses T073 forecast_ledger (brier_skill_score, calibration).
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import forecast_ledger as FL   # T073: brier_skill_score, calibration


def skill_assessment(windows):
    """windows = [{model_brier, baseline_brier}] across the full horizon. Skill is SUSTAINED only when
    every window keeps positive Brier skill (no window regresses) and the aggregate skill is positive."""
    per_window = []
    for w in windows:
        bss = FL.brier_skill_score([w["model_brier"]], [w["baseline_brier"]])
        per_window.append(bss)
    valid = [b for b in per_window if b is not None]
    aggregate = FL.brier_skill_score([w["model_brier"] for w in windows],
                                     [w["baseline_brier"] for w in windows])
    positive = aggregate is not None and aggregate > 0
    sustained = bool(valid) and len(valid) == len(per_window) and min(valid) > 0   # every window > 0
    return {"per_window_bss": per_window, "aggregate_bss": aggregate,
            "min_window_bss": (min(valid) if valid else None),
            "positive": positive, "sustained": sustained,
            "skill_ok": positive and sustained, "n_windows": len(windows)}


def calibration_assessment(forecasts, tol=0.15):
    """forecasts = [{prob, label}]. Primary metric = Expected Calibration Error (ECE): the count-weighted
    mean absolute gap between a bin's predicted mean and its observed rate -- the standard reliability
    measure, robust to sparse bins. Acceptable iff ECE <= tol. max_reliability_error (the worst single
    bin, noise-dominated for tiny bins) is reported as a diagnostic only, not the gate."""
    calib = FL.calibration(forecasts)
    filled = [b for b in calib["bins"] if b["n"] > 0]
    n_total = calib["n_total"]
    if not filled or n_total == 0:
        return {"ece": None, "max_reliability_error": None, "tol": tol, "acceptable": False,
                "n_total": n_total, "bins": []}
    ece = round(sum(b["n"] * abs(b["pred_mean"] - b["obs_rate"]) for b in filled) / n_total, 6)
    max_error = round(max(abs(b["pred_mean"] - b["obs_rate"]) for b in filled), 6)
    return {"ece": ece, "max_reliability_error": max_error, "tol": tol,
            "acceptable": ece <= tol, "n_total": n_total, "bins": filled}


def lead_value_assessment(lead_days, correct_catches, false_alarms=0, value_per_catch=1, fa_penalty=1):
    """Lead value is clear iff the prediction arrives with positive lead time AND yields positive net
    human value (correct early catches, net of false alarms)."""
    net_value = correct_catches * value_per_catch - false_alarms * fa_penalty
    clear = (lead_days is not None and lead_days > 0) and net_value > 0
    return {"lead_days": lead_days, "correct_catches": correct_catches, "false_alarms": false_alarms,
            "net_human_value": net_value, "clear": clear}


def release_decision(skill, calib, lead):
    """GO only when every criterion passes; otherwise STOP with a disable flag and the failed criteria."""
    failed = []
    if not skill.get("skill_ok"):
        failed.append("brier_skill_not_positive_and_stable")
    if not calib.get("acceptable"):
        failed.append("calibration_not_acceptable")
    if not lead.get("clear"):
        failed.append("user_lead_value_not_clear")
    go = not failed
    return {"decision": "GO" if go else "STOP",
            "show_to_users": go,
            "disable_flag": not go,               # rollback/disable flag: True means keep it hidden
            "failed_criteria": failed,
            "criteria": {"skill_ok": bool(skill.get("skill_ok")),
                         "calibration_acceptable": bool(calib.get("acceptable")),
                         "lead_value_clear": bool(lead.get("clear"))}}


def closeout(windows, forecasts, lead_days, correct_catches, false_alarms=0, tol=0.15):
    """One-shot full-horizon closeout: assess skill + calibration + lead value, then decide go/stop.
    tol is the calibration ECE gate and defaults to 0.15, matching calibration_assessment and the docs."""
    skill = skill_assessment(windows)
    calib = calibration_assessment(forecasts, tol=tol)
    lead = lead_value_assessment(lead_days, correct_catches, false_alarms)
    decision = release_decision(skill, calib, lead)
    return {"skill": skill, "calibration": calib, "lead_value": lead, "release_decision": decision}
