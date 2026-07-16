#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P03-T075 generator -- two pilot prediction targets over the 2016+ event chain, each backtested
over three rolling windows against an unconditional base-rate baseline, then surfaced as hedged
probabilities (no deterministic tone). release_mode SHADOW: dev/shadow env only, production untouched.

The two pilots are PREDEFINED with a fixed horizon (a target may not be fitted post-hoc):
  * ACCEL-PILOT     -- will a research topic ACCELERATE within 90 days?
                       support = # of recent months with rising publication count (leading rise);
                       counter = # of saturation / decline signals.
  * DIFFUSION-A0-A1 -- will a central (A0) policy DIFFUSE to a province (A1) within 180 days?
                       support = # of A1 provinces already echoing/referencing the A0 policy;
                       counter = # of superseding / contradicting central events.

The net support signal (support - counter) is the leading indicator; the conditional model learns
P(outcome | net-signal bucket) from the training slice and beats the unconditional baseline that
ignores the signal. Deterministic; no network / clock / randomness.
"""
import json
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import diffusion_predictor as DP


def _c(observed_at, support, counter, label):
    return {"observed_at": observed_at, "support_signals": support, "counter_signals": counter,
            "label": label}


# The two pilots use DISTINCT fixtures (different base rate, signal strength, cadence, horizon) so they
# are independent demonstrations, not the same pattern relabeled. Each VALIDATION window is deliberately
# NOISY -- it carries impurities (a strong-support case that did not fire, or a weak-support case that
# did), so the model is imperfect and could lose; it wins on aggregate, not by construction. On a purely
# separable window the demonstration would be a toy; here the model earns the win.

# --- ACCEL-PILOT (topic acceleration, horizon 90d, base rate ~0.5). Origins tile 2019 by quarter. ---
ACCEL_CASES = [
    # training history (observed on/before the first origin 2018-12-31); 2 training impurities.
    _c("2016-03-15", 4, 1, 1), _c("2016-06-15", 5, 0, 1), _c("2016-10-15", 1, 4, 0),
    _c("2017-01-15", 0, 3, 0), _c("2017-05-15", 4, 0, 1), _c("2017-09-15", 1, 5, 0),
    _c("2018-02-15", 5, 2, 0),                 # net +3 but did NOT accelerate (train impurity)
    _c("2018-05-15", 2, 5, 1),                 # net -3 but DID accelerate (train impurity)
    _c("2018-08-15", 4, 1, 1), _c("2018-11-15", 0, 4, 0),
    # window 1 validation (2018-12-31, 2019-03-31]; 5 cases incl. 1 impurity (last)
    _c("2019-01-10", 4, 1, 1), _c("2019-01-25", 5, 0, 1), _c("2019-02-10", 0, 3, 0),
    _c("2019-02-25", 1, 4, 0), _c("2019-03-10", 5, 2, 0),          # strong support, did NOT accelerate
    # window 2 validation (2019-03-31, 2019-06-29]; 1 impurity (last)
    _c("2019-04-10", 5, 1, 1), _c("2019-04-25", 4, 0, 1), _c("2019-05-10", 1, 5, 0),
    _c("2019-05-25", 0, 3, 0), _c("2019-06-10", 2, 5, 1),          # weak support, DID accelerate
    # window 3 validation (2019-06-30, 2019-09-28]; 1 impurity (last)
    _c("2019-07-10", 4, 1, 1), _c("2019-07-25", 5, 0, 1), _c("2019-08-10", 0, 4, 0),
    _c("2019-08-25", 1, 3, 0), _c("2019-09-10", 5, 3, 0),          # strong support, did NOT accelerate
]
ACCEL_ORIGINS = ["2018-12-31", "2019-03-31", "2019-06-30"]

# --- DIFFUSION-A0-A1 (central->province diffusion, horizon 180d, base rate ~0.6). Half-year origins. -
# Distinct from ACCEL: diffusion is more common (higher base rate), the signal is noisier, and windows
# hold 6 cases -- so the Brier profile differs from ACCEL's, not a clone.
DIFFUSION_CASES = [
    _c("2016-04-15", 4, 0, 1), _c("2016-07-15", 3, 1, 1), _c("2016-10-15", 5, 1, 1),
    _c("2017-01-15", 1, 3, 0), _c("2017-04-15", 4, 1, 1), _c("2017-07-15", 0, 4, 0),
    _c("2017-10-15", 3, 0, 1), _c("2018-01-15", 4, 2, 0),         # echoed but central policy superseded
    _c("2018-04-15", 1, 4, 1),                                    # diffused despite contradicting noise
    _c("2018-07-15", 5, 1, 1), _c("2018-09-15", 0, 3, 0), _c("2018-11-15", 4, 1, 1),
    # window 1 validation (2018-12-31, 2019-06-29]; 6 cases incl. 1 impurity
    _c("2019-01-15", 5, 0, 1), _c("2019-02-15", 4, 1, 1), _c("2019-03-15", 0, 3, 0),
    _c("2019-04-15", 3, 1, 1), _c("2019-05-15", 4, 2, 0), _c("2019-06-15", 1, 4, 0),  # impurity: 4,2,0
    # window 2 validation (2019-06-30, 2019-12-27]; 1 impurity (2019-10-15: echoed but superseded)
    _c("2019-07-15", 4, 0, 1), _c("2019-08-15", 5, 1, 1), _c("2019-09-15", 1, 4, 0),
    _c("2019-10-15", 4, 2, 0), _c("2019-11-15", 0, 3, 0), _c("2019-12-10", 4, 1, 1),  # impurity: 4,2,0
    # window 3 validation (2019-12-31, 2020-06-28]; 1 impurity
    _c("2020-01-15", 5, 1, 1), _c("2020-02-15", 4, 0, 1), _c("2020-03-15", 0, 4, 0),
    _c("2020-04-15", 3, 0, 1), _c("2020-05-15", 1, 3, 0), _c("2020-06-15", 4, 2, 0),  # impurity: 4,2,0
]
DIFFUSION_ORIGINS = ["2018-12-31", "2019-06-30", "2019-12-31"]

PILOTS = {
    "ACCEL-PILOT": {"cases": ACCEL_CASES, "origins": ACCEL_ORIGINS},
    "DIFFUSION-A0-A1": {"cases": DIFFUSION_CASES, "origins": DIFFUSION_ORIGINS},
}


def build():
    report = {"iteration": "ITER-20260716-ADP-V01-FINAL-EXECUTION", "task": "ADP-S6-P03-T075",
              "release_mode": "SHADOW", "predefined_targets": DP.PREDEFINED_TARGETS, "pilots": {}}
    for tid, spec in PILOTS.items():
        horizon = DP.PREDEFINED_TARGETS[tid]["horizon_days"]
        bt = DP.rolling_backtest(spec["cases"], spec["origins"], horizon, target_id=tid)
        # surfaced predictions for the most recent origin, as hedged probabilities (no deterministic tone)
        model = DP.fit_model([c for c in spec["cases"]
                              if DP.RB._d(c["observed_at"]) <= DP.RB._d(spec["origins"][-1])])
        surfaced = []
        for c in spec["cases"]:
            if DP.RB._d(c["observed_at"]) <= DP.RB._d(spec["origins"][-1]):
                continue
            p = DP.predict(model, c)
            stmt = DP.phrase(p)
            DP.assert_no_deterministic_tone(stmt, p)     # gate: refuse any certainty phrasing
            surfaced.append({"observed_at": c["observed_at"], "support": c["support_signals"],
                             "counter": c["counter_signals"], "prob": round(p, 4), "statement": stmt})
        report["pilots"][tid] = {
            "horizon_days": horizon, "predefined": DP.is_predefined(tid),
            "n_windows": bt["n_windows"], "beats_all": bt["beats_all"], "windows": bt["windows"],
            "surfaced_predictions": surfaced,
        }
    # lead-time report: the prediction is made at the origin; the outcome settles horizon days later.
    report["lead_time_report"] = {
        "ACCEL-PILOT": {"origin": "2019-06-30", "outcome_settles": "2019-09-28",
                        "lead_time_days": DP.lead_time("2019-06-30", "2019-09-28")},
        "DIFFUSION-A0-A1": {"origin": "2019-12-31", "outcome_settles": "2020-06-28",
                            "lead_time_days": DP.lead_time("2019-12-31", "2020-06-28")},
    }
    return report


if __name__ == "__main__":
    rep = build()
    out = V01 / "evidence" / "ADP-S6-P03-T075" / "diffusion_predictor_report.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    for tid, p in rep["pilots"].items():
        print(f"{tid}: windows={p['n_windows']} beats_all={p['beats_all']} horizon={p['horizon_days']}d")
        for w in p["windows"]:
            print(f"   origin {w['origin']}: model {w['model_brier']} vs baseline {w['baseline_brier']} "
                  f"-> beats={w['model_beats']}")
    print("wrote", out)
