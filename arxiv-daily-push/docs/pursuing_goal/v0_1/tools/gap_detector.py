#!/usr/bin/env python3
"""ADP V0.1 Source-Year-Month gap detector (ADP-S4-P01-T043).

Turns comprehensiveness from a source COUNT into a visible time-coverage grid: for every enabled
source x year-month cell there is either an item COUNT or an explicit gap REASON -- there must be
ZERO silently-unexplained holes. Cells that cannot be explained raise an ALERT.

Gap reasons (exhaustive, deterministic):
  - covered              : count > 0
  - source_not_yet_active : the month precedes the source's first activity
  - no_publications       : the source is active and the month is backfilled but genuinely had 0 items
  - not_backfilled        : the month is in scope but its backfill shard is not done yet
  - fetch_failed          : the backfill shard failed for that month
  - UNEXPLAINED           : none of the above -> an alert (target: 0)

No network. Input: item rows (source_id, month) + source activity windows + backfilled/failed month sets.
"""
from __future__ import annotations
import collections, json, pathlib


def month_range(start, end):
    sy, sm = (int(x) for x in start.split("-")); ey, em = (int(x) for x in end.split("-"))
    out, y, m = [], sy, sm
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1; y += 1
    return out


def build_coverage(items):
    """(source_id, month) -> count, from item rows with a 'source_id' and a 'month' (YYYY-MM)."""
    cov = collections.Counter()
    for it in items:
        cov[(it["source_id"], it["month"])] += 1
    return cov


def classify(source_id, month, count, active_from, active_to, backfilled, failed):
    if count > 0:
        return "covered"
    if active_from and month < active_from:
        return "source_not_yet_active"
    if (source_id, month) in failed:
        return "fetch_failed"
    if (source_id, month) in backfilled:
        return "no_publications"           # backfilled + genuinely empty (explained)
    if active_from and active_to and active_from <= month <= active_to:
        return "not_backfilled"            # in the active span but its shard is not done yet
    if active_from and month > active_to:
        return "not_backfilled"            # future-of-last-seen but still in the plan window
    return "UNEXPLAINED"                   # cannot explain -> alert


def detect(items, sources, months, backfilled=None, failed=None):
    """sources: {source_id: {active_from, active_to}}. Returns the coverage grid + gap summary + alerts.
    Every enabled source x month cell is classified; UNEXPLAINED cells are alerts (must be 0)."""
    backfilled = backfilled or set()
    failed = failed or set()
    cov = build_coverage(items)
    grid, reasons, alerts = [], collections.Counter(), []
    for sid in sorted(sources):
        af = sources[sid].get("active_from")
        at = sources[sid].get("active_to")
        for mo in months:
            c = cov.get((sid, mo), 0)
            r = classify(sid, mo, c, af, at, backfilled, failed)
            reasons[r] += 1
            cell = {"source_id": sid, "month": mo, "count": c, "status": r}
            grid.append(cell)
            if r == "UNEXPLAINED":
                alerts.append(cell)
    total = len(grid)
    explained = total - reasons["UNEXPLAINED"]
    return {
        "cells": total, "sources": len(sources), "months": len(months),
        "reason_counts": dict(reasons),
        "explained": explained, "unexplained": reasons["UNEXPLAINED"],
        "every_cell_has_count_or_reason": reasons["UNEXPLAINED"] == 0,
        "alerts": alerts[:50], "alert_count": len(alerts),
        "grid_sample": grid[:5],
    }


def infer_source_windows(items):
    """Derive each source's active window [first month, last month] from the ingested items."""
    by = collections.defaultdict(list)
    for it in items:
        by[it["source_id"]].append(it["month"])
    return {sid: {"active_from": min(ms), "active_to": max(ms)} for sid, ms in by.items()}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--start", default="2016-01")
    ap.add_argument("--end", default="2026-07")
    ap.add_argument("--out")
    args = ap.parse_args()
    items = json.loads(pathlib.Path(args.items).read_text(encoding="utf-8"))
    months = month_range(args.start, args.end)
    sources = infer_source_windows(items)
    rep = detect(items, sources, months)
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("cells", "sources", "months", "reason_counts", "unexplained",
                                          "every_cell_has_count_or_reason", "alert_count")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
