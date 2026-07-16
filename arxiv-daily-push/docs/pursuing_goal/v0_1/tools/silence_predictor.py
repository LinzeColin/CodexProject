#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P03-T074 -- Shadow source-silence prediction.

Predicts whether an official source's current quiet is ABNORMAL (it should have published by now) or
NORMAL (within its usual cadence), and DISTINGUISHES abnormal source silence from a collection failure
(our fetcher broke, not the source). Beats a simple publication-cycle baseline and quantifies false
alarms and human value.

  * simple_cycle_overdue(history, as_of) -- the baseline: overdue if the gap since the last publication
    exceeds the median inter-publication interval. Cheap, but over-alerts on naturally-variable sources.
  * classify(source, as_of) -- the model: a robust threshold (median + k * MAD) accounts for a source's
    own variability, so a variable source is not falsely flagged; and a fetch-error signal is classified
    as `collection_failure`, not `abnormal_silence`. Returns normal / abnormal_silence / collection_failure.
  * evaluate(cases) -- scores the model AND the baseline against labeled truth; reports accuracy, the
    false-alarm rate, and the human value (correct early catches).

release_mode SHADOW: predictions are computed in the dev/shadow environment only; no production
worker/cron/data is touched and the realtime build is unchanged. Deterministic; no network, no clock
(as_of and dates are passed in), no randomness.
"""


def _intervals(dates_ordinal):
    d = sorted(dates_ordinal)
    return [d[i + 1] - d[i] for i in range(len(d) - 1)]


def _median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _mad(xs, med):
    if not xs or med is None:
        return 0.0
    return _median([abs(x - med) for x in xs]) or 0.0


def cadence(history):
    """Median inter-publication interval and MAD (robust dispersion) from a source's publication days."""
    ivals = _intervals(history)
    med = _median(ivals)
    return {"median_interval": med, "mad": _mad(ivals, med), "n_intervals": len(ivals),
            "last_pub": max(history) if history else None}


def simple_cycle_overdue(history, as_of):
    """Baseline: overdue iff gap since last publication > the median interval (no variability allowance)."""
    c = cadence(history)
    if c["median_interval"] is None or c["last_pub"] is None:
        return False
    return (as_of - c["last_pub"]) > c["median_interval"]


def classify(source, as_of, k=3.0):
    """Model. source = {history:[day ordinals], recent_fetch_errors:int}. A fetch error is a collection
    failure (not source silence). Otherwise, abnormal only if the gap exceeds median + k*MAD (a robust
    allowance for the source's own variability). Returns one of normal/abnormal_silence/collection_failure."""
    if source.get("recent_fetch_errors", 0) > 0:
        return "collection_failure"
    c = cadence(source["history"])
    if c["median_interval"] is None or c["last_pub"] is None:
        return "normal"
    gap = as_of - c["last_pub"]
    threshold = c["median_interval"] + k * c["mad"]
    return "abnormal_silence" if gap > threshold else "normal"


def _baseline_classify(source, as_of):
    """The baseline's classification: it only knows cadence, so it cannot tell silence from a fetch
    failure and it uses the simple-cycle overdue rule."""
    return "abnormal_silence" if simple_cycle_overdue(source["history"], as_of) else "normal"


def evaluate(cases, value_per_catch=1.0):
    """cases = [{source, as_of, truth}] with truth in {normal, abnormal_silence, collection_failure}.
    Scores the model and the baseline: accuracy, false-alarm rate (predicted a problem where truth is
    normal), and human value (correct abnormal_silence / collection_failure catches * value)."""
    def score(fn):
        correct = fa = normal_total = catches = 0
        for cse in cases:
            pred = fn(cse["source"], cse["as_of"])
            truth = cse["truth"]
            if pred == truth:
                correct += 1
                if truth in ("abnormal_silence", "collection_failure"):
                    catches += 1
            if truth == "normal":
                normal_total += 1
                if pred != "normal":
                    fa += 1
        return {"accuracy": round(correct / len(cases), 6) if cases else None,
                "false_alarms": fa, "false_alarm_rate": round(fa / normal_total, 6) if normal_total else 0.0,
                "correct_catches": catches, "human_value": round(catches * value_per_catch, 6)}
    return {"model": score(classify), "baseline": score(_baseline_classify),
            "n_cases": len(cases)}
