#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP 长期稳定 watchdog: make a SILENT ZERO loud.

This session's most-repeated failure is a green cron hiding a pipeline that quietly produces nothing.
This check probes the live system on a schedule and goes RED when it is up but silently not producing.

WHAT IT COVERS (only what a public endpoint actually exposes):
  * the most recent daily run FAILED (失败) -- the pipeline threw;
  * the newest COMPLETED run ingested arXiv=0 (ingest broken) or selected 候选=0 on a run that meant
    to select (selection broken);
  * no completed run in the visible history, or the newest completed run is stale;
  * backfill (P12) degrading (via /api/backfill).

WHAT IT DOES NOT COVER, stated honestly: P08's ACTUAL disease was metadata enrichment returning 0
(matched=0) while arXiv ingest and selection were fine -- a green run with a silent METADATA zero.
`/system` does not render the per-run meta counts, so this watchdog CANNOT see that specific failure.
Closing that gap needs a worker change to expose meta match-rate on a public endpoint; until then this
catches ingest/selection/failure/staleness/backfill silent-zeros, not metadata ones. Do not read it as
"it would have caught P08" -- it would not have.

It hits ONLY public ADP endpoints, read-only, with retries so a transient edge timeout is not a false
alarm. It is deliberately lenient where a zero is legitimate (bioRxiv/board feeds on a given day, or a
弃权/abstain run selecting nothing) and strict where a zero means breakage.

Exit 0 = healthy. Exit 1 = a real invariant is broken (prints which). Exit 2 = could not reach the
site after retries (infra/network, reported separately so it is not confused with a silent-zero).
"""
import argparse
import json
import re
import sys
import time
import urllib.request

BASE = "https://adp.linzezhang.com"
ROUTES = ["/", "/review", "/radar", "/library", "/watchlist", "/system", "/api/backfill"]
BUILD_RE = re.compile(r"^[0-9a-f]{12}$")
# a /system run row: date | result | arXiv N · bio N · 板块流 N · 候选 N | note
RUN_ROW = re.compile(
    r"(\d{4}-\d{2}-\d{2})\D*?(正常|降级|弃权|未运行|失败)\D*?arXiv\s*(\d+)\D*?bio\s*(\d+)\D*?板块流\s*(\d+)\D*?候选\s*(\d+)",
    re.S)


# Run-result taxonomy (worker_cloud.js): a run either executes the pipeline to completion, throws, or
# is an idempotent skip. RAN = executed and ingested (弃权/abstain is a HEALTHY completed run that
# chose not to select). 失败 = threw. 未运行 = idempotent skip (a prior run already succeeded today).
RAN = ("正常", "降级", "弃权")


def evaluate_runs(sysbody, max_run_age_days, today):
    """Pure logic (no network): given the /system HTML and today's UTC date, return (ok, fail) lists.

    The worker renders `SELECT * FROM cn_run_log ORDER BY at DESC LIMIT 14` and prints counts on EVERY
    row (defaulting to 0), so a fresh 失败/未运行 row appears at the top with zero counts. The checks
    therefore must (a) alert when the NEWEST row is itself 失败 -- the single most important case: the
    pipeline threw tonight -- and (b) base silent-zero and staleness on the newest run that actually
    RAN, never letting a fresh failure/skip row masquerade as freshness. `today` is a datetime.date.
    Guarded by tests/governance/test_adp_liveness_check.py, including the fresh-failure-on-top case."""
    import datetime
    ok, fail = [], []
    runs = RUN_ROW.findall(sysbody)  # [(date,result,arxiv,bio,board,cand), ...] newest-first
    if not runs:
        fail.append("/system shows no parseable run rows -- page shape changed or pipeline never ran")
        return ok, fail

    # (a) the most recent execution FAILED -- the case the pipeline being "green" hides. Alert now,
    #     not after the whole 14-row window turns non-executed.
    newest = runs[0]
    if newest[1] == "失败":
        fail.append("latest run {} FAILED (失败) -- pipeline threw on its most recent execution".format(newest[0]))
    elif newest[1] == "未运行":
        ok.append("latest row {} is 未运行 (idempotent skip -- a prior run already succeeded)".format(newest[0]))

    # (b) newest run that actually RAN (executed the pipeline). Silent-zero + staleness key off THIS,
    #     not off render order or a fresh 失败/未运行 zero row.
    ran = [r for r in runs if r[1] in RAN]
    if not ran:
        fail.append("no completed run (正常/降级/弃权) in the visible {}-row history -- pipeline not producing".format(len(runs)))
        return ok, fail
    date, result, arx, bio, board, cand = ran[0]
    arx, cand = int(arx), int(cand)
    if arx == 0:
        fail.append("SILENT ZERO: newest completed run {} ({}) ingested arXiv=0 -- ingest broken "
                    "(P08-class silent failure behind a green cron)".format(date, result))
    elif result in ("正常", "降级") and cand == 0:
        # 候选=0 is only anomalous on a run that meant to select; 弃权 (abstain) legitimately selects none.
        fail.append("SILENT ZERO: newest completed run {} ({}) produced 候选=0 -- selection broken".format(date, result))
    else:
        ok.append("newest completed run {} ({}) arXiv={} 候选={} (ingest ok)".format(date, result, arx, cand))
    age = (today - datetime.date.fromisoformat(date)).days   # staleness on the newest COMPLETED run
    if age > max_run_age_days:
        fail.append("stale: newest completed run is {} ({} days old > {}) -- fresh 失败/未运行 rows do not "
                    "count as production".format(date, age, max_run_age_days))
    else:
        ok.append("freshness ok (newest completed run {}, {}d)".format(date, age))
    return ok, fail


def _get(path, tries=3, timeout=25):
    """GET with retries; returns (status, body) or (None, error) on total failure."""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(BASE + path, headers={"User-Agent": "adp-liveness/1"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except Exception as e:  # transient edge timeout / 5xx -> retry
            last = "{}: {}".format(type(e).__name__, e)
            time.sleep(2 * (i + 1))
    return None, last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-run-age-days", type=int, default=3,
                    help="alert if the most recent ACTUAL run is older than this")
    args = ap.parse_args()

    infra_fail, health_fail, ok = [], [], []

    # 1. every route reachable (retries absorb transient timeouts)
    bodies = {}
    for p in ROUTES:
        st, body = _get(p)
        if st is None:
            infra_fail.append("route {} unreachable after retries ({})".format(p, body))
        elif st != 200:
            health_fail.append("route {} returned HTTP {}".format(p, st))
        else:
            bodies[p] = body
            ok.append("route {} 200".format(p))

    # 2. /build.json names a real 12-hex build (worker is actually serving, not a Cloudflare error page)
    st, body = _get("/build.json")
    if st == 200:
        try:
            bid = json.loads(body).get("build_id", "")
            if BUILD_RE.match(bid):
                ok.append("build_id {} live".format(bid))
            else:
                health_fail.append("/build.json build_id not a 12-hex stamp: {!r}".format(bid))
        except Exception as e:
            health_fail.append("/build.json did not parse: {}".format(e))
    elif st is None:
        infra_fail.append("/build.json unreachable ({})".format(body))
    else:
        health_fail.append("/build.json HTTP {}".format(st))

    # 3. run health: recent-failure, silent-zero (ingest/selection), and staleness -- all keyed off the
    #    newest run that actually RAN. See evaluate_runs (RAN includes 弃权/abstain as a healthy run).
    sysbody = bodies.get("/system")
    if sysbody:
        import datetime
        today = datetime.datetime.now(datetime.timezone.utc).date()
        r_ok, r_fail = evaluate_runs(sysbody, args.max_run_age_days, today)
        ok.extend(r_ok); health_fail.extend(r_fail)
    # (if /system was unreachable it is already recorded in infra_fail above)

    # 4. /api/backfill: once the backfill cron has run, its last_run must not be erroring every time.
    bf = bodies.get("/api/backfill")
    if bf:
        try:
            d = json.loads(bf)
            last = d.get("last_run")
            if last is None:
                ok.append("backfill not yet run (cursor {}), nothing to assert".format(d.get("cursor")))
            elif last.get("degraded"):
                health_fail.append("backfill last_run degraded: {} (cursor {})".format(
                    last.get("degraded"), d.get("cursor")))
            else:
                ok.append("backfill last_run ok (cursor {}, rows {}, {}ms)".format(
                    d.get("cursor"), last.get("rows"), last.get("ms")))
        except Exception as e:
            health_fail.append("/api/backfill did not parse: {}".format(e))

    # ---- report ----
    for line in ok:
        print("  ok    " + line)
    for line in health_fail:
        print("  FAIL  " + line)
    for line in infra_fail:
        print("  UNREACHABLE  " + line)

    if health_fail:
        print("\nRED: {} health invariant(s) broken".format(len(health_fail)))
        return 1
    if infra_fail:
        print("\nUNREACHABLE: {} endpoint(s) down after retries (infra/network, not a silent-zero)".format(len(infra_fail)))
        return 2
    print("\nOK: ADP live and producing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
