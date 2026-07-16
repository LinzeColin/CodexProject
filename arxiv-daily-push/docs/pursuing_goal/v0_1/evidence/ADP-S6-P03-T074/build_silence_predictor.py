#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic fixtures for ADP-S6-P03-T074 (Shadow source-silence prediction).

Labeled cases (dates are day ordinals) where the model beats the simple publication-cycle baseline:
a naturally-variable source the baseline false-alarms on, and a collection failure the baseline cannot
tell apart from source silence.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
sys.path.insert(0, str(V01 / "tools"))
import silence_predictor as SP

REGULAR = [10, 40, 70, 100]                          # every 30d, MAD 0 -> threshold == median
VARIABLE = [10, 40, 100, 125, 180, 215]              # intervals 30/60/25/55/35 -> median 35, MAD 10

CASES = [
    # 1) regular source genuinely overdue (gap 60 > 30) -> abnormal; both agree
    {"source": {"history": REGULAR, "recent_fetch_errors": 0}, "as_of": 160, "truth": "abnormal_silence"},
    # 2) VARIABLE source at 45d silence -> NORMAL within its variability; baseline false-alarms, model correct
    {"source": {"history": VARIABLE, "recent_fetch_errors": 0}, "as_of": 260, "truth": "normal"},
    # 3) COLLECTION FAILURE (fetch errors) -> model classifies collection_failure; baseline says silence
    {"source": {"history": REGULAR, "recent_fetch_errors": 2}, "as_of": 200, "truth": "collection_failure"},
    # 4) regular source recently published (gap 15 < 30) -> normal; both agree
    {"source": {"history": REGULAR, "recent_fetch_errors": 0}, "as_of": 115, "truth": "normal"},
    # 5) another genuinely-overdue regular source -> abnormal; both agree
    {"source": {"history": REGULAR, "recent_fetch_errors": 0}, "as_of": 200, "truth": "abnormal_silence"},
    # 6) VARIABLE source silent FAR beyond even its variability (gap 80 > median 35 + 3*MAD 10 = 65) ->
    #    genuinely abnormal; the model catches it too (its wide threshold is not over-conservative)
    {"source": {"history": VARIABLE, "recent_fetch_errors": 0}, "as_of": 295, "truth": "abnormal_silence"},
]


def main():
    ev = SP.evaluate(CASES)
    report = {
        "n_cases": ev["n_cases"],
        "model": ev["model"],
        "baseline": ev["baseline"],
        "beats_baseline": ev["model"]["accuracy"] > ev["baseline"]["accuracy"],
        "classifications": [(SP.classify(c["source"], c["as_of"]), c["truth"]) for c in CASES],
    }
    (HERE / "silence_predictor_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("model:", ev["model"])
    print("baseline:", ev["baseline"])
    print("beats_baseline:", report["beats_baseline"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
