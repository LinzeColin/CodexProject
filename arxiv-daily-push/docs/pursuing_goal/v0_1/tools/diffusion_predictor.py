#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P03-T075 -- Shadow topic-acceleration & central->local (A0->A1->A2) diffusion prediction.

Two PILOT targets, predefined with a fixed horizon (a target may not be fitted post-hoc):

  * ACCEL-PILOT       -- will a research topic ACCELERATE within the horizon?
  * DIFFUSION-A0-A1   -- will a central (A0) policy DIFFUSE to a province (A1) within the horizon?

Each prediction conditions on leading SUPPORT / COUNTER signals from the 2016+ event chain (e.g. how
many A1 provinces already echo the A0 policy, minus contradicting/superseding events). The model beats
an unconditional base-rate baseline over three rolling windows (train observed <= origin < validation,
via the T072 split), and every surfaced statement is PROBABILISTIC -- never a deterministic tone.

release_mode SHADOW: dev/shadow env only; production untouched; realtime build unchanged. Deterministic;
no network, no clock (dates passed in), no randomness.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rolling_backtest as RB   # T072 rolling_splits / assert_no_time_crossing

# predefined pilot targets + horizon (days). A target NOT in here may not enter the backtest.
PREDEFINED_TARGETS = {
    "ACCEL-PILOT": {"horizon_days": 90, "kind": "topic_acceleration"},
    "DIFFUSION-A0-A1": {"horizon_days": 180, "kind": "central_local_diffusion"},
}
# words that assert certainty -- forbidden in a shadow forecast (无确定语气). A porous list would let a
# deterministic claim through, so cover the common certainty markers in both languages.
_DETERMINISTIC = ("必然", "必定", "必将", "一定", "肯定会", "势必", "注定", "铁定", "百分之百",
                  "毫无疑问", "无疑", "十拿九稳", "板上钉钉", "100%", "definitely", "certainly",
                  "will surely", "guaranteed", "inevitable", "inevitably", "assured", "for sure",
                  "certain to", "sure to", "no doubt")


def is_predefined(target_id):
    return target_id in PREDEFINED_TARGETS


def _net_signal(case):
    return case.get("support_signals", 0) - case.get("counter_signals", 0)


def fit_model(train, alpha=1.0):
    """Fit P(event | net_signal bucket) with Laplace shrinkage toward the global rate. The bucket is
    sign(net_signal): a positive net support signal is a leading indicator of acceleration/diffusion."""
    labels = [c["label"] for c in train if c.get("label") in (0, 1)]
    glob = (sum(labels) / len(labels)) if labels else 0.5
    buckets = {}
    for c in train:
        if c.get("label") not in (0, 1):
            continue
        b = 1 if _net_signal(c) > 0 else 0
        e, n = buckets.get(b, (0, 0))
        buckets[b] = (e + c["label"], n + 1)
    rates = {b: (e + alpha * glob) / (n + alpha) for b, (e, n) in buckets.items()}
    return {"global": glob, "bucket_rates": rates, "alpha": alpha}


def predict(model, case):
    """Conditional probability for a case, clamped strictly inside (0,1) -- a shadow forecast is never
    a certainty."""
    b = 1 if _net_signal(case) > 0 else 0
    p = model["bucket_rates"].get(b, model["global"])
    return min(0.98, max(0.02, p))


def baseline_predict(model, _case):
    """Unconditional base-rate baseline: ignores the signals (the same global rate for every case)."""
    return min(0.98, max(0.02, model["global"]))


def _brier(preds, labels):
    return round(sum((p - y) ** 2 for p, y in zip(preds, labels)) / len(labels), 6) if labels else None


def rolling_backtest(cases, origins, horizon_days, target_id=None):
    """Three-window rolling backtest: for each origin, fit the model + baseline on the training cases
    (observed <= origin) and score both on the validation window (origin, origin+horizon]. Returns a
    per-window comparison; train and validation never cross in time (T072 split). When target_id is
    given it must be predefined -- a post-hoc target may not be backtested through this entry point."""
    if target_id is not None and not is_predefined(target_id):
        raise ValueError(f"target {target_id!r} is not predefined; a post-hoc target may not be backtested")
    splits = RB.rolling_splits(cases, origins, horizon_days)
    windows = []
    for sp in splits:
        RB.assert_no_time_crossing(sp)
        model = fit_model(sp["train"])
        val = sp["val"]
        y = [c["label"] for c in val]
        m_brier = _brier([predict(model, c) for c in val], y)
        b_brier = _brier([baseline_predict(model, c) for c in val], y)
        windows.append({"origin": sp["origin"], "train_n": len(sp["train"]), "val_n": len(val),
                        "model_brier": m_brier, "baseline_brier": b_brier,
                        "model_beats": m_brier is not None and b_brier is not None and m_brier < b_brier})
    return {"n_windows": len(windows), "windows": windows,
            "beats_all": all(w["model_beats"] for w in windows) if windows else False}


def phrase(prob):
    """A hedged, probabilistic surfaced statement -- never a deterministic tone."""
    pct = round(prob * 100)
    return f"该目标在预定 horizon 内发生的估计概率约为 {pct}%（基于历史信号，非确定预测）"


def assert_no_deterministic_tone(statement, prob=None):
    """Reject a surfaced forecast that uses certainty language or an over-confident 0/1 probability."""
    low = (statement or "").lower()
    if any(w.lower() in low for w in _DETERMINISTIC):
        raise ValueError(f"deterministic tone forbidden in a shadow forecast: {statement!r}")
    if prob is not None and (prob <= 0.0 or prob >= 1.0):
        raise ValueError(f"over-confident probability {prob} (must be strictly inside (0,1))")
    return True


def lead_time(origin_date, outcome_date):
    """Lead time (days) between when the prediction is made (origin) and when the outcome settles."""
    od = RB._d(origin_date)
    oc = RB._d(outcome_date)
    return (oc - od).days if (od and oc) else None
