#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P04-T054 -- emit the A2 registry expansion (cohorts + marginal value report + health)."""
import sys, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import a2_registry as R

def main():
    r = R.expand()
    (HERE / "a2_expansion.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"baseline_rate={r['baseline']['rate']} new_rate={r['new_cohort_useful_signal_rate']} "
          f"meets_baseline={r['meets_baseline']} admitted={r['admitted_count']} rejected={r['rejected_count']}")

if __name__ == "__main__":
    main()
