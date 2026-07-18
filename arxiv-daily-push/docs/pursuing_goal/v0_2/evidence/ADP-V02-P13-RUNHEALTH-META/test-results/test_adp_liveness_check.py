#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: the ADP liveness watchdog's silent-zero detection actually detects a silent zero.

`scripts/adp_liveness_check.py` is the 长期稳定 watchdog whose whole job is to go RED when the live
system is up but silently producing nothing (P08's disease: a green cron enriching 0 rows for weeks).
A watchdog that can't tell a healthy run from a 补0 run is worse than none -- it manufactures false
confidence. This test pins the decision logic (`evaluate_runs`, extracted to be network-free) against
fixtures, so the detection cannot silently rot.

These are unit tests over pure logic; the workflow does the actual live probing on a schedule.
"""
import datetime
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
CHECK = ROOT / "scripts" / "adp_liveness_check.py"


def _load():
    spec = importlib.util.spec_from_file_location("adp_liveness_check", CHECK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


HEALTHY = "2026-07-16 | 降级 | arXiv 220 · bio 30 · 板块流 189 · 候选 546 |"
HEALTHY2 = "2026-07-15 | 降级 | arXiv 210 · bio 28 · 板块流 180 · 候选 500 |"
FAILED_TOP = "2026-07-17 | 失败 | arXiv 0 · bio 0 · 板块流 0 · 候选 0 | RuntimeError"
ZERO_ARXIV = "2026-07-17 | 降级 | arXiv 0 · bio 0 · 板块流 0 · 候选 0 |"
ZERO_CAND = "2026-07-17 | 正常 | arXiv 180 · bio 20 · 板块流 90 · 候选 0 |"
SKIP = "2026-07-17 | 未运行 | arXiv 0 · bio 0 · 板块流 0 · 候选 0 | 当日已成功运行, 幂等跳过"
ABSTAIN = "2026-07-17 | 弃权 | arXiv 180 · bio 20 · 板块流 90 · 候选 3 |"
TODAY = datetime.date(2026, 7, 17)


class TestAdpLivenessCheck(unittest.TestCase):
    def setUp(self):
        self.m = _load()

    def test_the_script_exists_and_exposes_the_pure_evaluator(self):
        self.assertTrue(CHECK.is_file(), "watchdog script missing: {}".format(CHECK))
        self.assertTrue(hasattr(self.m, "evaluate_runs"), "evaluate_runs not exposed -- test cannot pin the logic")

    def test_healthy_latest_run_passes(self):
        ok, fail = self.m.evaluate_runs(HEALTHY, 3, TODAY)
        self.assertEqual(fail, [], "healthy run wrongly flagged: {}".format(fail))
        self.assertTrue(any("ingest ok" in x for x in ok))

    # ---- the decisive case the first version silently passed (review Attack C) ----
    def test_fresh_failure_on_top_is_caught(self):
        """Tonight's run FAILED; yesterday+ were healthy. Old code skipped past 失败 to the healthy run
        and went GREEN -- a watchdog green while the pipeline is broken. Must RED on the failure."""
        ok, fail = self.m.evaluate_runs(FAILED_TOP + "\n" + HEALTHY + "\n" + HEALTHY2, 3, TODAY)
        self.assertTrue(any("FAILED" in x for x in fail),
                        "fresh 失败 on top was NOT flagged: ok={} fail={}".format(ok, fail))

    def test_sustained_failure_fires_immediately_not_after_two_weeks(self):
        """12 straight 失败 with 2 healthy rows still in the 14-row window must RED now, not only once
        every visible row is non-executed (review Attack A)."""
        page = "\n".join("2026-07-%02d | 失败 | arXiv 0 · bio 0 · 板块流 0 · 候选 0 |" % d for d in range(17, 5, -1))
        page += "\n" + "2026-07-05 | 降级 | arXiv 200 · bio 20 · 板块流 100 · 候选 300 |"
        ok, fail = self.m.evaluate_runs(page, 3, TODAY)
        self.assertTrue(any("FAILED" in x for x in fail), "sustained failure not caught: {}".format(fail))

    def test_staleness_uses_newest_completed_not_a_fresh_failure_row(self):
        """Newest COMPLETED run is 12 days old; a fresh 失败 sits on top. Contract: staleness keys off
        the newest ACTUAL run, so it must flag stale (review Attack B)."""
        old_ran = "2026-07-05 | 降级 | arXiv 200 · bio 20 · 板块流 100 · 候选 300 |"
        ok, fail = self.m.evaluate_runs(FAILED_TOP + "\n" + old_ran, 3, TODAY)
        self.assertTrue(any("stale" in x for x in fail),
                        "staleness used the fresh 失败 row instead of the 12-day-old completed run: {}".format(fail))

    def test_abstain_streak_is_not_cry_wolf(self):
        """弃权 (abstain) is a HEALTHY completed run that ingested fine but selected nothing. A streak of
        them with healthy arXiv must NOT RED (review Attack D -- crying wolf gets a watchdog disabled)."""
        page = "\n".join("2026-07-%02d | 弃权 | arXiv 180 · bio 20 · 板块流 90 · 候选 3 |" % d for d in range(17, 3, -1))
        ok, fail = self.m.evaluate_runs(page, 3, TODAY)
        self.assertEqual(fail, [], "abstain streak with healthy ingest wrongly flagged: {}".format(fail))

    def test_silent_zero_arxiv_is_caught(self):
        ok, fail = self.m.evaluate_runs(ZERO_ARXIV + "\n" + HEALTHY, 3, TODAY)
        self.assertTrue(any("SILENT ZERO" in x and "arXiv=0" in x for x in fail),
                        "silent arXiv=0 not caught: ok={} fail={}".format(ok, fail))

    def test_silent_zero_candidates_is_caught(self):
        ok, fail = self.m.evaluate_runs(ZERO_CAND + "\n" + HEALTHY, 3, TODAY)
        self.assertTrue(any("SILENT ZERO" in x and "候选=0" in x for x in fail),
                        "silent 候选=0 not caught: ok={} fail={}".format(ok, fail))

    def test_idempotent_skip_on_top_of_a_healthy_run_passes(self):
        """A 未运行 skip is all-zeros but healthy; with a fresh completed run below it must NOT flag."""
        ok, fail = self.m.evaluate_runs(SKIP + "\n" + HEALTHY.replace("2026-07-16", "2026-07-17"), 3, TODAY)
        self.assertEqual(fail, [], "未运行 skip over a healthy same-day run wrongly flagged: {}".format(fail))

    def test_no_completed_run_in_window_is_flagged(self):
        page = "\n".join("2026-07-%02d | 未运行 | arXiv 0 · bio 0 · 板块流 0 · 候选 0 | skip" % d for d in range(17, 3, -1))
        ok, fail = self.m.evaluate_runs(page, 3, TODAY)
        self.assertTrue(any("no completed run" in x for x in fail), "all-未运行 window not flagged: {}".format(fail))

    def test_no_runs_at_all_is_flagged_not_silently_passed(self):
        ok, fail = self.m.evaluate_runs("<html>no run table here</html>", 3, TODAY)
        self.assertTrue(fail, "an unparseable /system passed vacuously -- watchdog would be blind")

    # ---- metadata silent-zero (P08's disease) via /api/runhealth ----
    def test_the_429_storm_meta_unset_but_degraded_marked_is_caught(self):
        """★The real P08★: all DOIs 429 -> enrichMeta early-returns before setting meta, so meta is
        UNSET but degraded carries a meta:http429 marker. The first version missed this entirely
        (keyed only off meta.matched). Must RED off the degraded marker."""
        rh = {"latest": {"as_of_date": "2026-07-18", "result": "降级", "meta": None,
                         "degraded": ["meta:http429x12"]}}
        ok, fail = self.m.evaluate_runhealth(rh)
        self.assertTrue(any("SILENT ZERO" in x for x in fail),
                        "429-storm (meta unset, degraded meta:http429) NOT caught: ok={} fail={}".format(ok, fail))

    def test_metadata_matched_zero_with_error_marker_is_caught(self):
        """meta present, matched=0, AND a meta: error marker -> errored to zero -> disease."""
        rh = {"latest": {"as_of_date": "2026-07-17", "result": "降级",
                         "meta": {"requested": 12, "matched": 0}, "degraded": ["meta:http429x8"]}}
        ok, fail = self.m.evaluate_runhealth(rh)
        self.assertTrue(any("SILENT ZERO" in x for x in fail), "errored-to-zero not caught: {}".format(fail))

    def test_all_404_no_errors_is_not_flagged(self):
        """matched=0 with NO meta error marker = the DOIs are genuinely absent from OpenAlex (404 is
        knowledge). Not breakage -- must NOT RED (avoid crying wolf on legitimate absence)."""
        rh = {"latest": {"as_of_date": "2026-07-17", "result": "降级",
                         "meta": {"requested": 12, "matched": 0}, "degraded": []}}
        ok, fail = self.m.evaluate_runhealth(rh)
        self.assertEqual(fail, [], "genuine all-404 wrongly flagged: {}".format(fail))

    def test_metadata_partial_match_with_error_marker_is_not_flagged(self):
        """Some 429s but some matched -> partial, degraded marks it but matched>0 -> not the disease."""
        rh = {"latest": {"as_of_date": "2026-07-17", "result": "降级",
                         "meta": {"requested": 12, "matched": 7}, "degraded": ["meta:http429x2"]}}
        ok, fail = self.m.evaluate_runhealth(rh)
        self.assertEqual(fail, [], "partial match wrongly flagged: {}".format(fail))

    def test_metadata_zero_requested_is_not_flagged(self):
        rh = {"latest": {"as_of_date": "2026-07-17", "result": "正常", "meta": {"requested": 0, "matched": 0}}}
        ok, fail = self.m.evaluate_runhealth(rh)
        self.assertEqual(fail, [], "zero-requested wrongly flagged: {}".format(fail))

    def test_runhealth_endpoint_absent_or_no_meta_is_tolerated(self):
        """None / no latest / meta unset with NO error marker -> skip, never a false alarm."""
        for rh in (None, {}, {"latest": None},
                   {"latest": {"as_of_date": "2026-07-17", "meta": None, "degraded": []}}):
            ok, fail = self.m.evaluate_runhealth(rh)
            self.assertEqual(fail, [], "tolerated case wrongly flagged for {}: {}".format(rh, fail))

    def test_the_liveness_workflow_stays_read_only(self):
        """The workflow probes the LIVE site, so it must never gain write power or handle secrets, and
        must never trigger on a PR (which would hit production on every push). Pin those properties so a
        later edit that adds `contents: write`, a secret, or a `pull_request` trigger fails here."""
        wf = ROOT / ".github" / "workflows" / "arxiv-daily-push-liveness.yml"
        self.assertTrue(wf.is_file(), "liveness workflow missing: {}".format(wf))
        text = wf.read_text(encoding="utf-8")
        import re
        # triggers: only schedule + workflow_dispatch
        for bad in ("pull_request", "pull_request_target"):
            self.assertNotIn(bad + ":", text,
                             "liveness workflow must not trigger on {} -- it would hit the live site on PRs".format(bad))
        self.assertIn("workflow_dispatch", text)
        self.assertIn("schedule", text)
        # permissions: read-only, no write scope anywhere
        self.assertRegex(text, r"permissions:\s*\n\s*contents:\s*read",
                         "liveness workflow must declare permissions: contents: read")
        self.assertNotRegex(text, r":\s*write\b", "liveness workflow must not grant any write permission")
        # no secrets in a read-only public probe
        self.assertNotIn("secrets.", text, "liveness workflow must not reference any secret")
        # actions SHA-pinned (repo convention), not bare tags
        for m in re.finditer(r"uses:\s*([^\s]+)", text):
            ref = m.group(1)
            if ref.startswith("actions/") or "/" in ref:
                self.assertRegex(ref, r"@[0-9a-f]{40}$",
                                 "action {} must be SHA-pinned (repo workflow-security convention)".format(ref))


if __name__ == "__main__":
    unittest.main()
