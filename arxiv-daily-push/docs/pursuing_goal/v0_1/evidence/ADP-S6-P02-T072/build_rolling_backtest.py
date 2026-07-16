#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic fixtures for ADP-S6-P02-T072 (2016+ rolling-origin backtest).

A settled-outcome time series for one target spanning 2016-2022 (events cluster in March), and three
rolling origins (2019/2020/2021-01-01) with a one-year validation window. The split generator must
produce >= 3 windows with train/val disjoint in time.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
sys.path.insert(0, str(V01 / "tools"))
import rolling_backtest as RB

# settled outcomes, observed across 2016-2022 (label 1 clusters in March)
OUTCOMES = []
for year in range(2016, 2023):
    OUTCOMES.append({"observed_at": f"{year}-03-15", "label": 1})   # March event
    OUTCOMES.append({"observed_at": f"{year}-07-01", "label": 0})   # non-event
    OUTCOMES.append({"observed_at": f"{year}-11-01", "label": 0})   # non-event

ORIGINS = ["2019-01-01", "2020-01-01", "2021-01-01"]   # 3 rolling origins
HORIZON = 365   # 1-year validation window
TARGET = "G1"


def main():
    result = RB.run_backtest(TARGET, OUTCOMES, ORIGINS, HORIZON)
    report = {
        "target": result["target"], "n_windows": result["n_windows"],
        "manifest": result["manifest"],
        "windows": [{"origin": w["origin"], "val_end": w["val_end"], "train_n": w["train_n"],
                     "val_n": w["val_n"], "freq_brier": w["freq_metrics"]["brier"],
                     "seas_brier": w["seas_metrics"]["brier"]} for w in result["windows"]],
    }
    (HERE / "rolling_backtest_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("n_windows:", result["n_windows"], "manifest:", result["manifest"])
    for w in report["windows"]:
        print(f"  origin {w['origin']} -> val_end {w['val_end']}: train_n={w['train_n']} val_n={w['val_n']} "
              f"freq_brier={w['freq_brier']} seas_brier={w['seas_brier']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
