#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: the deterministic lesson builder never puts the SAME abstract sentence in two sections.

P15 found (by observing the LIVE site) that the daily lesson rendered the same abstract sentence
verbatim in two sections at once -- e.g. a numeric sentence landed in both `机制拆解` (positional
`sents.slice(2,5)`) and `证据与数字` (`numeric`), and when an item had no categories the `领域脉络`
fallback (`sents.slice(2,3)`) duplicated `机制拆解`. Duplicated content in an authority-facing
"cognitive system" reads as a generation bug and dilutes depth. The fix makes each sentence go to
exactly one section: specific sections (人话版/证据与数字/反例与边界, then 领域脉络's positional
fallback) claim their sentences into a `claimed` set, and `机制拆解`/`领域脉络` exclude anything
already claimed.

CI's push path has no Node, so the load-bearing BEHAVIOURAL re-derivation lives in
`arxiv-daily-push/tools/verify_lesson_dedup.mjs` (it extracts the shipped buildLesson, runs it over
fixtures, and proves via negative controls that the PRE-FIX logic duplicated on every path). This
Python guard is the CI-safe regression anchor: it pins the dedup MECHANISM in the shipped source and
proves it is non-vacuous by running the same detector over the exact pre-fix code and requiring it to
fire. If `node` happens to be present locally it also runs the behavioural verifier.
"""
import os
import pathlib
import re
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKER = ROOT / "arxiv-daily-push" / "deploy" / "cloudflare" / "worker_cloud.js"
VERIFIER = ROOT / "arxiv-daily-push" / "tools" / "verify_lesson_dedup.mjs"

# The exact pre-fix buildLesson body (the code that shipped the duplicate). Used ONLY as the negative
# control: the detector below MUST flag it, or the detector proves nothing about the real worker.
PRE_FIX_SNIPPET = r"""
function buildLesson(it) {
  const sents = splitSentences(it.summary);
  const cats = (it.categories || '').split(',').filter(Boolean);
  const numeric = sents.filter(s => /\d/.test(s));
  const limits = sents.filter(s => /(however|but|limit|only|fail|不足|局限|但|然而|仅)/i.test(s));
  const sec = (title, arr, fallback) => ({ title, sentences: (arr.length ? arr : [fallback]).slice(0, 4).map(text => ({ text })) });
  return [
    sec('人话版', sents.slice(0, 2), `x`),
    sec('领域脉络', cats.length ? [`y`] : sents.slice(2, 3), `z`),
    sec('机制拆解', sents.slice(2, 5), 'a'),
    sec('证据与数字', numeric.slice(0, 3), 'b'),
    sec('反例与边界', limits, 'c'),
  ];
}
"""


def _extract_build_lesson(src):
    m = re.search(r"function buildLesson\(it\)\s*\{.*?\nasync function makeLesson", src, re.S)
    if m:
        return m.group(0)
    # PRE_FIX_SNIPPET has no makeLesson after it -- fall back to "to end of function at col-0 brace".
    m = re.search(r"function buildLesson\(it\)\s*\{.*?\n\}", src, re.S)
    return m.group(0) if m else None


def _dedup_violations(build_lesson_src):
    """Return the list of dedup-mechanism defects in a buildLesson source string. Empty == deduped.

    Each check keys on a concrete symptom of the pre-fix (duplicating) shape, so the SAME function
    both passes the real (fixed) worker and fires on PRE_FIX_SNIPPET (non-vacuity)."""
    v = []
    # 1) 机制拆解 must draw from a claimed-excluded set, never the raw positional slice.
    if re.search(r"'机制拆解',\s*sents\.slice\(", build_lesson_src):
        v.append("机制拆解 draws raw sents.slice(...) (no dedup) -- a positional sentence can dup 证据与数字/领域脉络")
    # 2) the claim-set must exist.
    if "new Set([" not in build_lesson_src or "claimed" not in build_lesson_src:
        v.append("missing `claimed` Set -- nothing prevents a sentence appearing in two sections")
    # 3) mechanism must actually exclude claimed sentences.
    if "!claimed.has(s)" not in build_lesson_src:
        v.append("mechanism does not filter out already-claimed sentences (!claimed.has(s) absent)")
    # 4) numeric must be intro-filtered so an opening numeric sentence can't dup 人话版.
    if re.search(r"const numeric = sents\.filter\(s => /\\d/\.test\(s\)\);", build_lesson_src):
        v.append("numeric not intro-filtered -- a numeric opening sentence dups 人话版 and 证据与数字")
    return v


class TestAdpLessonDedup(unittest.TestCase):
    def setUp(self):
        self.assertTrue(WORKER.is_file(), "deployed worker missing: {}".format(WORKER))
        self.src = _extract_build_lesson(WORKER.read_text(encoding="utf-8"))
        self.assertIsNotNone(
            self.src,
            "could not locate buildLesson in worker_cloud.js -- it was renamed/moved; update this guard "
            "deliberately, don't let it pass vacuously.")

    def test_shipped_worker_is_deduped(self):
        self.assertEqual(
            _dedup_violations(self.src), [],
            "shipped buildLesson has a cross-section duplication defect -- see violations above.")

    def test_negative_control_prefix_code_is_flagged(self):
        """Non-vacuity: the detector MUST fire on the exact pre-fix code, on every dedup dimension."""
        pre = _extract_build_lesson(PRE_FIX_SNIPPET)
        self.assertIsNotNone(pre, "pre-fix snippet did not parse -- fix the fixture")
        viols = _dedup_violations(pre)
        # all four symptoms must be present, or the detector under-checks the real worker
        self.assertEqual(len(viols), 4,
                         "detector did not flag all pre-fix defects (got {}): it under-checks and could "
                         "pass a regressed worker vacuously.".format(viols))

    def test_behavioural_verifier_exists(self):
        """The load-bearing behavioural proof (extract shipped code + run + negative controls) is in-repo."""
        self.assertTrue(VERIFIER.is_file(), "behavioural verifier missing: {}".format(VERIFIER))
        body = VERIFIER.read_text(encoding="utf-8")
        self.assertIn("crossSectionDupes", body, "verifier lost its dup detector")
        self.assertIn("buildLessonPreFix", body, "verifier lost its negative control")

    @unittest.skipUnless(shutil.which("node"), "node not on PATH (CI push path); behavioural check runs locally")
    def test_behavioural_verifier_passes(self):
        """When Node is available, actually run the shipped code over fixtures and require 0 dupes."""
        r = subprocess.run(["node", str(VERIFIER)], capture_output=True, text=True, timeout=60,
                           cwd=str(ROOT))
        self.assertEqual(r.returncode, 0,
                         "behavioural verifier failed:\nSTDOUT:\n{}\nSTDERR:\n{}".format(r.stdout, r.stderr))
        self.assertIn("负控成立", r.stdout, "negative controls did not fire -- assertion not load-bearing")


if __name__ == "__main__":
    unittest.main()
