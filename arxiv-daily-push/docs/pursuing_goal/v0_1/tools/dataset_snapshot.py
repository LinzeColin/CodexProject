#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P01-T070 -- Dataset Snapshot + observed_at leakage guard.

A backtest must only see what was KNOWN at the prediction time. A document has two dates: its doc_date
(when the policy/paper issued -- possibly 2016) and its observed_at (when ADP actually fetched it --
possibly 2026 during backfill). A 2026-backfilled 2016 document was NOT known in 2018, even though its
doc_date is 2016. Snapshots therefore key on observed_at, never doc_date, so backfilled history cannot
pretend to have been known at a historical point in time.

  * snapshot(corpus, as_of) -- the dataset KNOWN as of `as_of`: exactly the docs with observed_at <=
    as_of (parsed dates), deterministically ordered, with a reproducible snapshot_id.
  * assert_no_leakage(dataset, as_of) -- RAISE if any doc in the dataset was observed AFTER as_of (a
    future document leaked in). This is the leakage tripwire that a backtest test must exercise.
  * rebuild_for_prediction(corpus, prediction) -- rebuild the exact as-of dataset for a prediction's
    origin_date; reproducible (same origin -> same snapshot_id), so any prediction can reconstruct the
    dataset it was made on.

Deterministic; no network, no clock (as_of is passed in), no randomness, no production side effects.
"""
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import coverage_asof as CA   # T056: _parse_date (YYYY-MM-DD as-of parser)


class LeakageError(AssertionError):
    """Raised when a dataset contains a document observed AFTER its as-of time (future leakage)."""


def _obs(doc):
    return CA._parse_date(doc.get("observed_at"))


def snapshot(corpus, as_of):
    """The dataset known as of `as_of`: docs with a parsed observed_at <= as_of. Docs with a missing or
    malformed observed_at are EXCLUDED (we cannot claim they were known). Deterministic order."""
    q = CA._parse_date(as_of)
    if q is None:
        raise ValueError(f"malformed as_of date {as_of!r}")
    kept = [d for d in corpus if _obs(d) is not None and _obs(d) <= q]
    kept.sort(key=lambda d: (d["observed_at"], d.get("canonical_id", "")))
    return {"as_of": as_of, "docs": kept,
            "snapshot_id": snapshot_id(kept), "n": len(kept)}


def _doc_fingerprint(d):
    """A per-doc content fingerprint: prefer an explicit content_hash/version, else a stable digest of
    the whole doc -- so two docs with the same id + observed_at but different content never collide."""
    cv = d.get("content_hash") or d.get("version")
    if cv:
        return cv
    return "doc:" + hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def snapshot_id(docs):
    """A reproducible, content-sensitive id over the included docs (canonical_id + observed_at + a
    per-doc content fingerprint). Order-independent; distinct datasets get distinct ids."""
    key = [[d.get("canonical_id"), d.get("observed_at"), _doc_fingerprint(d)]
           for d in sorted(docs, key=lambda d: (d.get("observed_at", ""), d.get("canonical_id", "")))]
    return "snap:" + hashlib.sha256(json.dumps(key, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def assert_no_leakage(dataset, as_of):
    """Tripwire: every doc must have been observed at or before as_of. A future-observed doc -> raise.
    A doc with a missing/malformed observed_at is also a leak (its knowledge time is unverifiable)."""
    q = CA._parse_date(as_of)
    if q is None:
        raise ValueError(f"malformed as_of date {as_of!r}")
    docs = dataset["docs"] if isinstance(dataset, dict) and "docs" in dataset else dataset
    offenders = []
    for d in docs:
        ob = _obs(d)
        if ob is None or ob > q:
            offenders.append({"canonical_id": d.get("canonical_id"), "observed_at": d.get("observed_at")})
    if offenders:
        raise LeakageError(f"future/unknown documents leaked into the as-of {as_of} dataset: {offenders}")
    return True


def rebuild_for_prediction(corpus, prediction):
    """Rebuild the exact dataset a prediction was made on (as of its origin_date). Reproducible."""
    return snapshot(corpus, prediction["origin_date"])
