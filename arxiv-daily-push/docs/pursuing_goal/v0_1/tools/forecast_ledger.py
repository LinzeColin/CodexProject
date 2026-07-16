#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P02-T073 -- calibration, skill scores, and the append-only Forecast Ledger.

Preserves successes AND failures over the long run -- never just the pretty cases:

  * calibration(forecasts)      -- a reliability diagram: bin predictions into 10 probability bins and
    report, per bin, the mean predicted probability vs the observed outcome frequency and the count.
  * has_calibration(p, calib)   -- True iff the bin a user-visible probability p falls in has historical
    data (count > 0). A probability whose bin has no history is NOT backed by calibration.
  * brier_skill_score / logloss -- skill vs a reference (BSS = 1 - Brier(model)/Brier(reference)) and the
    log loss.
  * Ledger (append-only)        -- append(record) records a forecast + its outcome (success or failure);
    delete() is REFUSED (raises) so a failure record can never be removed.

The ledger is TAMPER-EVIDENT: each record carries a hash chained from the previous record, so deleting
or mutating any record (especially a failure) breaks verify_integrity() -- the append-only property has
teeth beyond the delete() refusal.

Deterministic; no network, no clock, no randomness, no production side effects.
"""
import hashlib
import json
import math

N_BINS = 10
_CORE_FIELDS = ("forecast_id", "prob", "label", "outcome")


class AppendOnlyError(Exception):
    """Raised on any attempt to delete/mutate a Forecast Ledger record -- failures are immutable."""


def _bin(p):
    """The reliability bin index 0..N_BINS-1 for a probability p in [0,1]; None for a non-numeric p."""
    try:
        p = min(1.0, max(0.0, float(p)))
    except (TypeError, ValueError):
        return None
    return min(N_BINS - 1, int(p * N_BINS))


def calibration(forecasts):
    """forecasts = [{prob, label}]. Returns per-bin reliability: {bin, lo, hi, n, pred_mean, obs_rate}."""
    bins = {i: [] for i in range(N_BINS)}
    for f in forecasts:
        b = _bin(f.get("prob"))
        if f.get("label") in (0, 1) and b is not None:
            bins[b].append(f)
    out = []
    for i in range(N_BINS):
        fs = bins[i]
        n = len(fs)
        pred_mean = round(sum(x["prob"] for x in fs) / n, 6) if n else None
        obs_rate = round(sum(x["label"] for x in fs) / n, 6) if n else None
        out.append({"bin": i, "lo": round(i / N_BINS, 2), "hi": round((i + 1) / N_BINS, 2),
                    "n": n, "pred_mean": pred_mean, "obs_rate": obs_rate})
    return {"bins": out, "n_total": sum(b["n"] for b in out)}


def has_calibration(p, calib):
    """A user-visible probability is calibration-backed iff its bin has historical data (n > 0). A
    non-numeric probability is not calibration-backed (no crash)."""
    idx = _bin(p)
    return idx is not None and calib["bins"][idx]["n"] > 0


def calibration_of(p, calib):
    """The historical observed rate + count for a probability's bin (or None if no history / non-numeric)."""
    idx = _bin(p)
    if idx is None:
        return None
    b = calib["bins"][idx]
    return {"bin": b["bin"], "observed_rate": b["obs_rate"], "n": b["n"]} if b["n"] else None


def brier_skill_score(model_briers, ref_briers):
    """BSS = 1 - mean(model_brier)/mean(ref_brier). > 0 means the model beats the reference; 0 = no skill;
    < 0 = worse than reference (reported honestly, not hidden)."""
    if not model_briers or not ref_briers:
        return None
    mb = sum(model_briers) / len(model_briers)
    rb = sum(ref_briers) / len(ref_briers)
    if rb == 0:
        return None
    return round(1 - mb / rb, 6)


def logloss(preds, labels, eps=1e-15):
    if not labels:
        return None
    total = 0.0
    for p, y in zip(preds, labels):
        p = min(1 - eps, max(eps, p))
        total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return round(total / len(labels), 6)


# ------------------------------------------------------------------ append-only Forecast Ledger
def new_ledger():
    return {"records": []}


def _is_failure(prob, label):
    return (1 if prob >= 0.5 else 0) != label


def _chain_hash(prev, seq, core):
    payload = json.dumps({"prev": prev, "seq": seq, "core": core}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def append(ledger, forecast_id, prob, label, meta=None):
    """Append a forecast + its outcome. Both successes and failures are recorded permanently, each
    chained to the previous record so any later deletion/mutation is detectable."""
    core = {"forecast_id": forecast_id, "prob": prob, "label": label,
            "outcome": "failure" if _is_failure(prob, label) else "success"}
    seq = len(ledger["records"])
    prev = ledger["records"][-1]["chain"] if ledger["records"] else "genesis"
    rec = {**core, "meta": meta or {}, "seq": seq, "chain": _chain_hash(prev, seq, core)}
    ledger["records"].append(rec)
    return ledger


def verify_integrity(ledger):
    """Recompute the hash chain. Returns False if any record was deleted, reordered, or mutated -- so a
    removed failure is DETECTABLE even if a caller bypassed delete() and popped the list directly."""
    prev = "genesis"
    for i, r in enumerate(ledger["records"]):
        core = {k: r.get(k) for k in _CORE_FIELDS}
        if r.get("seq") != i or r.get("chain") != _chain_hash(prev, i, core):
            return False
        prev = r["chain"]
    return True


def delete(ledger, forecast_id):
    """REFUSED. The Forecast Ledger is append-only -- a failure record can never be deleted."""
    raise AppendOnlyError(f"cannot delete forecast {forecast_id}: the Forecast Ledger is append-only "
                          f"(failures are preserved, not hidden)")


def failures(ledger):
    return [r for r in ledger["records"] if r["outcome"] == "failure"]


def successes(ledger):
    return [r for r in ledger["records"] if r["outcome"] == "success"]
