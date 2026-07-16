#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic fixtures for ADP-S6-P02-T073 (calibration + skill + Forecast Ledger).

A well-calibrated forecast set (predicted probability tracks the observed frequency per bin), a model
that beats a base-rate reference, and a ledger with both a success and a failure record.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
sys.path.insert(0, str(V01 / "tools"))
import forecast_ledger as FL

# A well-calibrated set: within each 0.1 bin, the observed rate ~= the predicted probability.
# bin 0.2: 10 forecasts at 0.2, 2 positives (obs 0.2); bin 0.8: 10 at 0.8, 8 positives (obs 0.8); etc.
FORECASTS = []
for prob, n_pos, n in [(0.2, 2, 10), (0.5, 5, 10), (0.8, 8, 10), (0.9, 9, 10)]:
    for i in range(n):
        FORECASTS.append({"prob": prob, "label": 1 if i < n_pos else 0})

# model vs reference Brier (per rolling window, from T072-style backtests)
MODEL_BRIERS = [0.08, 0.09, 0.07]
REF_BRIERS = [0.22, 0.22, 0.22]


def build_ledger():
    lg = FL.new_ledger()
    FL.append(lg, "f1", 0.85, 1)   # success (predicted high, happened)
    FL.append(lg, "f2", 0.80, 0)   # FAILURE (predicted high, did not happen)
    FL.append(lg, "f3", 0.10, 0)   # success (predicted low, did not happen)
    return lg


def main():
    calib = FL.calibration(FORECASTS)
    lg = build_ledger()
    report = {
        "calibration_bins": [b for b in calib["bins"] if b["n"] > 0],
        "brier_skill_score": FL.brier_skill_score(MODEL_BRIERS, REF_BRIERS),
        "logloss": FL.logloss([f["prob"] for f in FORECASTS], [f["label"] for f in FORECASTS]),
        "ledger": {"n": len(lg["records"]), "failures": [r["forecast_id"] for r in FL.failures(lg)],
                   "successes": [r["forecast_id"] for r in FL.successes(lg)]},
    }
    (HERE / "forecast_ledger_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("calibration bins (n>0):", [(b["bin"], b["pred_mean"], b["obs_rate"], b["n"]) for b in report["calibration_bins"]])
    print("BSS:", report["brier_skill_score"], "logloss:", report["logloss"])
    print("ledger:", report["ledger"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
