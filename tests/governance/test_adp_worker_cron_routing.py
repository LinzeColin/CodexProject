#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: the ADP worker's cron TRIGGERS and its scheduled() ROUTING cannot silently drift apart.

P12 gave the worker a second cron. The daily pipeline runs on `30 20 * * *`; historical backfill runs
on its OWN invocation via a dedicated `30 8 * * *` trigger. The scheduled handler routes by the exact
cron string:

    if (event.cron === '30 8 * * *') ctx.waitUntil(backfillArxiv(env)...);
    else ctx.waitUntil(runDaily(env, 'cron'));

That coupling is byte-fragile and invisible: change the backfill time in `wrangler_cloud.jsonc` but not
in the `event.cron ===` check (or vice versa) and the backfill trigger fires into the `else` branch and
runs the DAILY pipeline instead -- or never runs at all. Nothing would be red; the cron would go green
while backfill silently never happens. That is the exact silent-misroute the P12 reviewer had to check
by hand, and the exact class of failure this project keeps hitting: a claim (this cron runs backfill)
that nothing enforces.

What it asserts, and why only these:
  * Every cron the handler explicitly branches on (`event.cron === '<cron>'`) exists in the deploy
    config's `triggers.crons`. A branch for a cron that isn't scheduled is dead routing.
  * At most ONE configured cron is left to the `else`/default branch (the daily pipeline). If two or
    more configured crons are unhandled, a new trigger was added without routing it -- it would
    silently run the default pipeline.
  * Both sets are non-empty (the guard is not passing vacuously over a parse that found nothing).

It deliberately does NOT hard-code the specific times -- it checks the config and the handler agree,
so it keeps holding if the Owner reschedules either cron, and only fails when they DISAGREE.
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
CLOUD = ROOT / "arxiv-daily-push" / "deploy" / "cloudflare"
WORKER = CLOUD / "worker_cloud.js"
WRANGLER = CLOUD / "wrangler_cloud.jsonc"
CRON_RE = re.compile(r"event\.cron\s*===\s*'([^']+)'")


def _config_crons():
    raw = WRANGLER.read_text(encoding="utf-8")
    # strip // and /* */ comments, then JSON-parse
    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)
    raw = re.sub(r"//.*", "", raw)
    cfg = json.loads(raw)
    return list((cfg.get("triggers") or {}).get("crons") or [])


def _handler_crons():
    src = WORKER.read_text(encoding="utf-8")
    m = re.search(r"async scheduled\s*\(event[^)]*\)\s*\{(.*?)\n  \}", src, re.S)
    body = m.group(1) if m else ""
    return CRON_RE.findall(body)


class TestAdpWorkerCronRouting(unittest.TestCase):
    def setUp(self):
        self.config = _config_crons()
        self.handled = _handler_crons()

    def test_the_worker_and_config_were_parsed(self):
        """Non-vacuity: both files must exist and the config must declare at least one cron."""
        self.assertTrue(WORKER.is_file() and WRANGLER.is_file(), "worker or wrangler config missing")
        self.assertGreaterEqual(len(self.config), 1,
                                "no crons parsed from wrangler_cloud.jsonc -- guard would be vacuous")

    def test_every_handled_cron_is_actually_scheduled(self):
        """A `event.cron === X` branch for a cron not in the config is dead routing (X never fires)."""
        dead = [c for c in self.handled if c not in self.config]
        self.assertEqual(
            dead, [],
            "scheduled() branches on cron(s) not present in wrangler_cloud.jsonc triggers: {}\n"
            "That branch can never run; the intended handler is silently dead. Config crons: {}".format(
                dead, self.config))

    def test_backfill_throughput_policy_two_slots(self):
        """P19 policy pin: coverage debt is paid at TWO backfill invocations per day.

        P12 shipped one backfill cron (30 8 UTC, PAGES=1 ~= 1300 rows ~= 5 days of arXiv per night --
        a ~2-year horizon to fill 2016+). Once the first live run measured ms=11736 (P12's own
        stop-condition gate for scaling), P19 added a second slot (30 2 UTC): each invocation keeps the
        PROVEN per-run profile (own 50-subrequest budget, ~19/50 used, same wall/CPU), and the monotonic
        cursor makes runs idempotent, so two slots is the safe 2x. This pin fails if someone drops back
        to one explicitly-routed cron, halving throughput silently -- the agreement checks above would
        stay green for that regression, so this is the only guard that notices."""
        self.assertGreaterEqual(
            len(set(self.handled)), 2,
            "fewer than 2 crons are explicitly routed (backfill slots): {} -- P19's 2x coverage "
            "throughput was silently reverted; see the P19 evidence bundle before changing this "
            "deliberately.".format(sorted(set(self.handled))))

    def test_at_most_one_configured_cron_falls_to_the_default_branch(self):
        """Every configured cron except the daily default must be explicitly routed.

        The handler routes non-default crons with `event.cron === X` and lets exactly one (the daily
        pipeline) fall through to `else`. If two+ configured crons are unhandled, a trigger was added
        without routing -- it silently runs the DAILY pipeline instead of its intended handler."""
        unhandled = [c for c in self.config if c not in self.handled]
        self.assertLessEqual(
            len(unhandled), 1,
            "{} configured cron(s) are not explicitly routed by scheduled(): {}\n"
            "At most one (the daily default/else) may be implicit. A new trigger was added without a "
            "matching `event.cron === ...` branch, so it would silently run the default pipeline.".format(
                len(unhandled), unhandled))


if __name__ == "__main__":
    unittest.main()
