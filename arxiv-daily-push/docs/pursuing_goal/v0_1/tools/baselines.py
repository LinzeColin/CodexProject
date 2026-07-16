#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P01-T071 -- cheap, interpretable statistical baselines for prediction targets.

A complex model must first beat a cheap, interpretable baseline. This module fits two such baselines
per target from its HISTORY of settled outcomes (0/1 labels from the T069 settlement rules, on the
leak-proof T070 snapshots):

  * frequency_baseline  -- the base rate: P(event) = (# events) / (# opportunities). The simplest honest
    predictor.
  * seasonality_baseline -- a month-of-year base rate: P(event | month) with Laplace smoothing so an
    unseen month falls back toward the global rate rather than a hard 0/1.

Metrics are the Brier score (mean squared error of the probability) and accuracy at a 0.5 threshold.
`benchmark` fits at least one reproducible baseline per target; `may_develop_advanced` refuses to let an
advanced model be built for a target that has no reproducible baseline yet.

This is a MODEL (statistics). Its formal spec is evidence/ADP-S6-P01-T071/MODEL_baselines.md. Release
mode NOT_DEPLOYED -- operational MODEL_SPEC/formula_registry registration is gated to promotion.

Deterministic; no network, no clock, no randomness, no production side effects.
"""

BASELINE_KINDS = ("frequency", "seasonality")


def _month(observed_at):
    # observed_at is "YYYY-MM-DD"; the month bucket is its MM (1-12). None on malformed.
    if not (isinstance(observed_at, str) and len(observed_at) >= 7 and observed_at[4] == "-"):
        return None
    try:
        m = int(observed_at[5:7])
    except ValueError:
        return None
    return m if 1 <= m <= 12 else None


def frequency_baseline(history):
    """Fit the base rate P(event) from history = [{label:0|1, ...}]. Returns a predictor + its rate."""
    labels = [h["label"] for h in history if h.get("label") in (0, 1)]
    n = len(labels)
    rate = (sum(labels) / n) if n else 0.0
    return {"kind": "frequency", "n": n, "rate": round(rate, 6),
            "predict": (lambda _obs, _r=rate: _r)}


def seasonality_baseline(history, alpha=1.0):
    """Fit a month-of-year base rate with Laplace smoothing. P(event|m) = (events_m + alpha*global) /
    (n_m + alpha). Unseen months fall back to the global rate."""
    labels = [h["label"] for h in history if h.get("label") in (0, 1)]
    glob = (sum(labels) / len(labels)) if labels else 0.0
    by_m = {}
    for h in history:
        if h.get("label") not in (0, 1):
            continue
        m = _month(h.get("observed_at"))
        if m is None:
            continue
        e, c = by_m.get(m, (0, 0))
        by_m[m] = (e + h["label"], c + 1)
    rates = {m: round((e + alpha * glob) / (c + alpha), 6) for m, (e, c) in by_m.items()}

    def predict(obs, _rates=rates, _glob=glob, _a=alpha):
        m = _month(obs)
        if m in _rates:
            return _rates[m]
        return round(_a * _glob / _a, 6) if _a else _glob   # unseen month -> smoothed global

    return {"kind": "seasonality", "global_rate": round(glob, 6), "month_rates": rates, "predict": predict}


def brier_score(predictions, labels):
    """Mean squared error of the probability vs the 0/1 outcome. Lower is better; 0.25 = always-0.5."""
    if not labels:
        return None
    return round(sum((p - y) ** 2 for p, y in zip(predictions, labels)) / len(labels), 6)


def accuracy(predictions, labels, threshold=0.5):
    if not labels:
        return None
    return round(sum(1 for p, y in zip(predictions, labels) if (1 if p >= threshold else 0) == y) / len(labels), 6)


def evaluate(baseline, eval_set):
    """Score a fitted baseline on eval_set = [{observed_at, label}]. Deterministic."""
    obs = [e.get("observed_at") for e in eval_set]
    labels = [e["label"] for e in eval_set]
    preds = [baseline["predict"](o) for o in obs]
    return {"brier": brier_score(preds, labels), "accuracy": accuracy(preds, labels), "n": len(labels)}


def benchmark(targets, history_by_target, eval_by_target, min_history=1):
    """Fit baselines per target and score them. A baseline is only a REPRODUCIBLE baseline when the
    target actually has history (>= min_history labeled outcomes) -- a target with no history has no
    real baseline (rate would be a meaningless 0.0), so has_reproducible_baseline is False and the
    advanced-model gate refuses it."""
    report = {}
    for t in targets:
        tid = t["target_id"]
        hist = history_by_target.get(tid, [])
        ev = eval_by_target.get(tid, [])
        n_valid = sum(1 for h in hist if h.get("label") in (0, 1))
        freq = frequency_baseline(hist)
        seas = seasonality_baseline(hist)
        report[tid] = {
            "n_history": n_valid,
            "baselines": {
                "frequency": {"rate": freq["rate"], "metrics": evaluate(freq, ev)},
                "seasonality": {"global_rate": seas["global_rate"], "month_rates": seas["month_rates"],
                                "metrics": evaluate(seas, ev)},
            },
            "has_reproducible_baseline": n_valid >= min_history,
        }
    return report


def may_develop_advanced(target_id, benchmark_report):
    """An advanced model may be developed for a target ONLY if it already has a reproducible baseline.
    No baseline -> refuse (a complex model must first beat a cheap one)."""
    entry = benchmark_report.get(target_id)
    return bool(entry and entry.get("has_reproducible_baseline") and entry.get("baselines"))
