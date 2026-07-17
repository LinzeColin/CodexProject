#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: every ADP V0.2 integration evidence bundle actually carries its evidence.

The V0.2 program deploys NOT_DEPLOYED V0.1 capabilities into production. Each phase ships an
evidence bundle under `docs/pursuing_goal/v0_2/evidence/<TASK>/`. The bundle is the only durable
record of what was claimed, measured, and reviewed; a phase whose bundle is missing pieces is a
production change with no auditable basis.

Why this exists: it was NOT holding. Auditing the bundles while shipping P09 found P08 and P09 had
NO `TASK_REPORT.md` at all — two production deploys, both reviewed, both missing the document that
states what shipped. Nothing noticed, because nothing looked. Both were backfilled; this guard is
what stops the next one.

What it asserts, and why only these:
  * `cost_value.json` exists, parses, and declares `release_mode` + a live build id.
    The task package's own cost_metric rule is 未知不得填 0 — cost accounting is mandatory, so a
    bundle without a parseable cost sheet is not a bundle.
  * `TASK_REPORT.md` and a non-empty `test-results/` exist.
  * A PRODUCTION bundle names the build it deployed, and that id looks like a real 12-hex build id
    (the worker's self-excluding stamp) rather than a placeholder.

What it deliberately does NOT assert: the presence of `nc_results.txt` or `known_gaps.md`. Only
P07-P09 carry negative controls and P01 has no known_gaps — those predate the discipline. Widening
this guard to fail on them would make it red on arrival and it would simply be deleted. It is
scoped to what is universally true today; tighten it when the older bundles are backfilled.
"""
import hashlib
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "arxiv-daily-push" / "docs" / "pursuing_goal" / "v0_2" / "evidence"
WORKER = ROOT / "arxiv-daily-push" / "deploy" / "cloudflare" / "worker_cloud.js"
BUILD_ID_RE = re.compile(r"^[0-9a-f]{12}$")
PHASE_RE = re.compile(r"^ADP-V02-P(\d{2})-")
STAMP_RE = re.compile(r"build_id: '([0-9a-f]{12})', source_sha256: '([0-9a-f]{64})'")


def _bundles():
    if not EVIDENCE.is_dir():
        return []
    return sorted(p for p in EVIDENCE.iterdir() if p.is_dir() and p.name.startswith("ADP-V02-"))


def _sheet(bundle):
    f = bundle / "cost_value.json"
    if not f.is_file():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None


def _production_bundles():
    """(phase_number, name, sheet) for every bundle whose sheet says PRODUCTION."""
    out = []
    for b in _bundles():
        d = _sheet(b)
        if not d or str(d.get("release_mode", "")).upper() != "PRODUCTION":
            continue
        m = PHASE_RE.match(b.name)
        if m:
            out.append((int(m.group(1)), b.name, d))
    return sorted(out)


class TestAdpV02EvidenceBundles(unittest.TestCase):
    def test_there_are_bundles_to_guard(self):
        """A guard over an empty set passes vacuously -- assert the set is real."""
        self.assertTrue(EVIDENCE.is_dir(), "V0.2 evidence directory is missing: {}".format(EVIDENCE))
        self.assertGreaterEqual(len(_bundles()), 5,
                                "expected the V0.2 integration bundles; found {}".format(len(_bundles())))

    def test_every_bundle_has_a_task_report(self):
        missing = [b.name for b in _bundles() if not (b / "TASK_REPORT.md").is_file()]
        self.assertEqual(
            missing, [],
            "V0.2 phase(s) shipped to production with no TASK_REPORT.md: {}\n"
            "The bundle is the only durable record of what was claimed and reviewed. P08 and P09 both "
            "shipped without one and nothing noticed, because nothing looked.".format(missing))

    def test_every_bundle_has_test_results(self):
        empty = []
        for b in _bundles():
            tr = b / "test-results"
            if not tr.is_dir() or not any(p.is_file() for p in tr.iterdir()):
                empty.append(b.name)
        self.assertEqual(empty, [], "V0.2 bundle(s) with no test-results artifacts: {}".format(empty))

    def test_every_bundle_has_a_parseable_cost_sheet(self):
        bad = []
        for b in _bundles():
            f = b / "cost_value.json"
            if not f.is_file():
                bad.append("{}: cost_value.json missing".format(b.name)); continue
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:
                bad.append("{}: cost_value.json does not parse ({})".format(b.name, type(e).__name__)); continue
            if not d.get("release_mode"):
                bad.append("{}: cost_value.json declares no release_mode".format(b.name))
        self.assertEqual(
            bad, [],
            "The task package requires cost accounting (cost_metric: 未知不得填 0). A bundle without a "
            "parseable cost sheet declaring release_mode is not auditable:\n  " + "\n  ".join(bad))

    def test_production_bundles_record_an_actual_change(self):
        """A PRODUCTION deploy must move the build: before != after.

        If a bundle claims PRODUCTION but names the same build before and after, either nothing was
        deployed or the sheet was copied from the previous phase and never updated -- both make the
        cost sheet a false record of what went live."""
        bad = []
        for b in _bundles():
            f = b / "cost_value.json"
            if not f.is_file():
                continue
            d = json.loads(f.read_text(encoding="utf-8"))
            if str(d.get("release_mode", "")).upper() != "PRODUCTION":
                continue
            before, after = str(d.get("live_build_before", "")), str(d.get("live_build_after", ""))
            if before and after and before == after:
                bad.append("{}: live_build_before == live_build_after == {}".format(b.name, after))
        self.assertEqual(bad, [], "PRODUCTION bundle(s) whose build did not move:\n  " + "\n  ".join(bad))

    def test_production_bundles_name_a_real_build_id(self):
        """A PRODUCTION deploy must say which build it put live, as a real 12-hex stamp.

        The build id is the worker's self-excluding hash (guarded by test_adp_worker_build_stamp).
        A bundle claiming PRODUCTION without naming a real one cannot be tied to what actually ran."""
        bad = []
        for b in _bundles():
            f = b / "cost_value.json"
            if not f.is_file():
                continue
            d = json.loads(f.read_text(encoding="utf-8"))
            if str(d.get("release_mode", "")).upper() != "PRODUCTION":
                continue
            after = str(d.get("live_build_after", ""))
            if not BUILD_ID_RE.match(after):
                bad.append("{}: live_build_after={!r} is not a 12-hex build id".format(b.name, after))
        self.assertEqual(bad, [], "PRODUCTION bundle(s) that do not name the build they deployed:\n  "
                         + "\n  ".join(bad))


    def test_latest_production_bundle_matches_the_committed_worker(self):
        """The newest PRODUCTION bundle must name the build the COMMITTED worker source hashes to.

        Two records claim to say what is running in production: the worker's self-excluding BUILD
        stamp (guarded by test_adp_worker_build_stamp) and the newest PRODUCTION bundle's
        `live_build_after`. They are written at different times by different hands, and nothing tied
        them together -- so they could disagree, and the disagreement is invisible.

        The disagreement is not hypothetical. This program's recurring failure is a claim recorded
        once and trusted forever: P08 shipped, its bundle said it worked, and it enriched 0 rows every night
        for weeks. This is the same shape one level up -- deploy build X, then keep editing the
        worker, and the bundle still names X while the repo holds Y. Whoever later asks "what source
        is live?" gets a confident, wrong answer from a file that was true once.

        The guard is cheap and exact: recompute the stamp from the committed bytes, compare to the
        sheet. It goes red on the two things that should be red -- a deploy whose bundle was never
        updated, and a worker edited after its bundle froze without a re-stamp+re-deploy."""
        prod = _production_bundles()
        self.assertTrue(prod, "no PRODUCTION bundle found -- this guard would pass vacuously")
        self.assertTrue(WORKER.is_file(), "the deployed worker is missing: {}".format(WORKER))
        src = WORKER.read_text(encoding="utf-8")
        m = STAMP_RE.search(src)
        self.assertIsNotNone(m, "worker_cloud.js carries no BUILD stamp to compare against")
        stamped = m.group(1)
        recomputed = hashlib.sha256(
            src.replace("build_id: '{}'".format(m.group(1)), "build_id: '{}'".format("0" * 12))
               .replace("source_sha256: '{}'".format(m.group(2)), "source_sha256: '{}'".format("0" * 64))
               .encode("utf-8")).hexdigest()[:12]
        self.assertEqual(stamped, recomputed,
                         "worker stamp does not reproduce -- test_adp_worker_build_stamp explains this")
        phase, name, sheet = prod[-1]
        self.assertEqual(
            str(sheet.get("live_build_after", "")), recomputed,
            "the newest PRODUCTION bundle ({}) says live_build_after={!r}, but the committed worker "
            "hashes to {!r}.\nEither the worker moved after that bundle froze (re-stamp, re-deploy, "
            "and open a new bundle) or a deploy never updated its sheet. Until they agree, the "
            "evidence names a source that is not the source.".format(
                name, sheet.get("live_build_after"), recomputed))

    def test_no_two_production_bundles_claim_the_same_deploy(self):
        """Distinct deploys put distinct builds live; a repeat means a sheet was copied, not written.

        `test_production_bundles_record_an_actual_change` catches before==after *within* one sheet.
        This catches the other half: two phases both claiming they put build X live. Only one of them
        can be true, and the copied one is a fabricated production record."""
        seen, dupes = {}, []
        for _, name, d in _production_bundles():
            after = str(d.get("live_build_after", ""))
            if not BUILD_ID_RE.match(after):
                continue
            if after in seen:
                dupes.append("{} and {} both claim they deployed {}".format(seen[after], name, after))
            seen[after] = name
        self.assertEqual(dupes, [], "PRODUCTION bundle(s) claiming a deploy another phase already "
                                    "claimed:\n  " + "\n  ".join(dupes))


if __name__ == "__main__":
    unittest.main()
