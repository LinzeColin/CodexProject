#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P03-T081 -- RUM / Core Web Vitals query + p75 baseline, segmented by theme / route / device /
network.

Acceptance (TASK_INDEX row 81): LCP/INP/CLS 可按主题、路由、设备和网络查询；无数据不声称达标.
  (LCP/INP/CLS must be queryable by theme, route, device and network; do NOT claim the bar is met without
   data.)

This is the OFFLINE analysis side of the RUM pipeline (the worker collects cn_rum rows in the browser and
POSTs them to /api/rum). Every segment/overall assessment is GATED on a minimum sample count: below the gate
the result is `insufficient_data` with rating=None and meets_bar=None -- so an empty or thin dataset claims
NOTHING (this is the load-bearing "无数据不声称达标" rule, enforced by a negative control in the verifier).

Deterministic; pure functions over a list of rows. No network / clock / randomness.
"""

# Google Core Web Vitals p75 thresholds: (good_max, needs_improvement_max). Above needs_improvement_max = poor.
THRESHOLDS = {"LCP": (2500.0, 4000.0), "INP": (200.0, 500.0), "CLS": (0.1, 0.25)}
DIMENSIONS = ("theme", "route", "device", "network")
DEFAULT_MIN_SAMPLES = 30   # floor below which we do NOT report a p75 rating (honest baseline; tune with traffic)


def p75(values):
    """Nearest-rank 75th percentile of a non-empty list (deterministic). Returns None for an empty list."""
    xs = sorted(v for v in values if isinstance(v, (int, float)))
    if not xs:
        return None
    import math
    rank = max(1, math.ceil(0.75 * len(xs)))     # 1-based nearest-rank
    return float(xs[rank - 1])


def rate(metric, value):
    """Classify a metric p75 value as good / needs-improvement / poor. None if metric/value unknown."""
    t = THRESHOLDS.get(metric)
    if t is None or value is None:
        return None
    good_max, ni_max = t
    if value <= good_max:
        return "good"
    if value <= ni_max:
        return "needs-improvement"
    return "poor"


def _assess(values, metric, min_samples):
    """Assess one metric over a list of values, GATED on min_samples. Never claims a rating below the gate."""
    n = len(values)
    if n < min_samples:
        return {"n": n, "status": "insufficient_data", "p75": None, "rating": None, "meets_bar": None}
    v = p75(values, )
    r = rate(metric, v)
    return {"n": n, "status": "ok", "p75": v, "rating": r, "meets_bar": (r == "good")}


def overall_baseline(rows, metrics=("LCP", "INP", "CLS"), min_samples=DEFAULT_MIN_SAMPLES):
    """Overall p75 baseline per metric, gated. With no rows every metric is insufficient_data (claims nothing)."""
    out = {}
    for m in metrics:
        vals = [r["value"] for r in rows if r.get("metric") == m]
        out[m] = _assess(vals, m, min_samples)
    return out


def query(rows, dimension, metrics=("LCP", "INP", "CLS"), min_samples=DEFAULT_MIN_SAMPLES):
    """Segment the CWV p75 by ONE dimension (theme/route/device/network). Returns {dim_value: {metric: assess}}.
    Every segment is gated -- a thin segment reports insufficient_data, not a rating."""
    if dimension not in DIMENSIONS:
        raise ValueError(f"unknown dimension {dimension!r}; expected one of {DIMENSIONS}")
    buckets = {}
    for r in rows:
        buckets.setdefault(r.get(dimension, "unknown"), []).append(r)
    out = {}
    for key, rs in sorted(buckets.items(), key=lambda kv: str(kv[0])):
        out[key] = {m: _assess([r["value"] for r in rs if r.get("metric") == m], m, min_samples) for m in metrics}
    return out


def query_multi(rows, dimensions=DIMENSIONS, metrics=("LCP", "INP", "CLS"), min_samples=DEFAULT_MIN_SAMPLES):
    """Full cross-segment query: group by the tuple of ALL dimensions, gated per (segment, metric)."""
    buckets = {}
    for r in rows:
        key = tuple(r.get(d, "unknown") for d in dimensions)
        buckets.setdefault(key, []).append(r)
    out = {}
    for key, rs in sorted(buckets.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        seg = dict(zip(dimensions, key))
        seg["metrics"] = {m: _assess([r["value"] for r in rs if r.get("metric") == m], m, min_samples) for m in metrics}
        out[" | ".join(str(x) for x in key)] = seg
    return out


def claims_any_compliance(assessment_tree):
    """True iff ANY assessed metric anywhere in the tree claims meets_bar (used by the verifier's negative
    control: on an empty/thin dataset this MUST be False -- 无数据不声称达标)."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            if "meets_bar" in node and node.get("status") == "ok":
                found.append(node["meets_bar"] is True)
            else:
                for v in node.values():
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(assessment_tree)
    return any(found)
