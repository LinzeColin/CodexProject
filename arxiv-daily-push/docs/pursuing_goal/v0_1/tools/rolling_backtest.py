#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P02-T072 -- 2016+ rolling-origin backtest.

Validates generalization and lead-time in TRUE time order. For each rolling origin O:

  * train  = settled outcomes OBSERVED at/before O (the known past, leak-checked with the T070 guard);
  * fit    = the T071 frequency / seasonality baselines on that training history;
  * val    = outcomes observed strictly AFTER O within the validation window (O, O+horizon];
  * score  = Brier / accuracy of the baseline on the validation outcomes.

Train and validation never cross in time (train observed <= O < val observed), so no future leaks into
a fitted baseline. Rolling the origin forward yields several windows (>= 3). Everything is deterministic,
so a run is reproducible and carries a run manifest hash.

Deterministic; no network, no clock (origins are passed in), no randomness, no production side effects.
"""
import datetime
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import coverage_asof as CA       # T056 _parse_date
import dataset_snapshot as DS    # T070 assert_no_leakage
import baselines as BL           # T071 frequency / seasonality baselines + evaluate


def _d(s):
    p = CA._parse_date(s)
    if not p:
        return None
    try:
        return datetime.date(p[0], p[1], p[2])
    except ValueError:
        return None                       # a calendar-invalid date (e.g. 2019-02-30) is unparseable


def rolling_splits(outcomes, origins, horizon_days):
    """Split generator: for each origin O, train = outcomes observed <= O; val = outcomes observed in
    (O, O+horizon]. Train and val are disjoint in time by construction."""
    splits = []
    for o in origins:
        od = _d(o)
        if od is None:
            raise ValueError(f"malformed origin {o!r}")
        endd = od + datetime.timedelta(days=horizon_days)
        train, val = [], []
        for x in outcomes:
            xd = _d(x.get("observed_at"))
            if xd is None:
                continue
            if xd <= od:
                train.append(x)
            elif od < xd <= endd:
                val.append(x)
        splits.append({"origin": o, "val_end": endd.isoformat(), "train": train, "val": val})
    return splits


def assert_no_time_crossing(split):
    """Every training sample must be observed at/before the origin and every validation sample strictly
    after it (within the window). Raises on any temporal crossing."""
    od = _d(split["origin"])
    for x in split["train"]:
        if _d(x["observed_at"]) > od:
            raise AssertionError(f"training sample observed after origin: {x}")
    endd = _d(split["val_end"])
    for x in split["val"]:
        xd = _d(x["observed_at"])
        if not (od < xd <= endd):
            raise AssertionError(f"validation sample outside (origin, origin+horizon]: {x}")
    return True


def run_manifest(target_id, origins, horizon_days, windows, min_history=1):
    key = {"target": target_id, "origins": list(origins), "horizon": horizon_days,
           "min_history": min_history,
           "windows": [[w["origin"], w["train_n"], w["val_n"], w["trainable"],
                        w["freq_metrics"], w["seas_metrics"]] for w in windows]}
    return "bt:" + hashlib.sha256(json.dumps(key, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def run_backtest(target_id, outcomes, origins, horizon_days, min_history=1):
    """Rolling-origin backtest over a target's settled outcome time series. Returns per-window metrics +
    a reproducible manifest. Leak-checks each training set with the T070 guard and refuses time crossing."""
    splits = rolling_splits(outcomes, origins, horizon_days)
    windows = []
    for sp in splits:
        assert_no_time_crossing(sp)
        DS.assert_no_leakage({"docs": sp["train"]}, sp["origin"])   # T070: training is leak-proof as of O
        freq = BL.frequency_baseline(sp["train"])
        seas = BL.seasonality_baseline(sp["train"])
        ev = [{"observed_at": x["observed_at"], "label": x["label"]} for x in sp["val"]]
        n_hist = sum(1 for x in sp["train"] if x.get("label") in (0, 1))
        windows.append({
            "origin": sp["origin"], "val_end": sp["val_end"],
            "train_n": len(sp["train"]), "val_n": len(sp["val"]),
            "trainable": n_hist >= min_history,
            "freq_metrics": BL.evaluate(freq, ev),
            "seas_metrics": BL.evaluate(seas, ev),
        })
    return {"target": target_id, "n_windows": len(windows), "windows": windows,
            "manifest": run_manifest(target_id, origins, horizon_days, windows, min_history)}
