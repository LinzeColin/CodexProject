#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic fixtures for ADP-S6-P01-T071 (frequency + seasonality baselines).

Two targets with settled history and a held-out eval set. G1 has a clear seasonal pattern (events
cluster in month 03); G2 is a low base-rate target. A THIRD target (G9) is left with NO history to
exercise the 'no baseline -> may not develop advanced' gate.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
sys.path.insert(0, str(V01 / "tools"))
import baselines as BL

TARGETS = [{"target_id": "G1"}, {"target_id": "G2"}, {"target_id": "G0"}]   # G0 has NO history

# G1: events happen in March (month 03), not otherwise -> seasonality should beat base rate.
HISTORY = {
    "G1": [
        {"observed_at": "2020-03-15", "label": 1}, {"observed_at": "2021-03-10", "label": 1},
        {"observed_at": "2022-03-20", "label": 1}, {"observed_at": "2020-07-01", "label": 0},
        {"observed_at": "2021-09-01", "label": 0}, {"observed_at": "2022-11-01", "label": 0},
        {"observed_at": "2020-01-01", "label": 0}, {"observed_at": "2021-01-01", "label": 0},
    ],
    "G2": [
        {"observed_at": "2020-05-01", "label": 0}, {"observed_at": "2021-06-01", "label": 0},
        {"observed_at": "2022-07-01", "label": 1}, {"observed_at": "2020-08-01", "label": 0},
        {"observed_at": "2021-09-01", "label": 0},
    ],
}
EVAL = {
    "G1": [{"observed_at": "2023-03-12", "label": 1}, {"observed_at": "2023-08-01", "label": 0},
           {"observed_at": "2023-03-30", "label": 1}, {"observed_at": "2023-12-01", "label": 0}],
    "G2": [{"observed_at": "2023-07-01", "label": 0}, {"observed_at": "2023-02-01", "label": 0}],
}


def main():
    report = BL.benchmark(TARGETS, HISTORY, EVAL)
    out = {
        "targets": [t["target_id"] for t in TARGETS],
        "report": report,
        "may_develop": {
            "G1": BL.may_develop_advanced("G1", report),
            "G0_no_history": BL.may_develop_advanced("G0", report),
            "G9_absent": BL.may_develop_advanced("G9", report),
        },
    }
    (HERE / "baselines_report.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for tid, e in report.items():
        print(tid, "freq_rate=", e["baselines"]["frequency"]["rate"],
              "freq_brier=", e["baselines"]["frequency"]["metrics"]["brier"],
              "seas_brier=", e["baselines"]["seasonality"]["metrics"]["brier"])
    print("may_develop G1:", out["may_develop"]["G1"],
          "| G0(no history):", out["may_develop"]["G0_no_history"],
          "| G9(absent):", out["may_develop"]["G9_absent"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
