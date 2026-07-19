#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: lesson/summary rendering strips inline LaTeX math delimiters, and never touches currency.

P17 observed on the LIVE site that lesson text rendered raw LaTeX inline-math delimiters to the reader
("$H = 0.91$ bits, near the $1.0$-bit maximum") -- generation-bug noise on an authority-facing surface.
Fix: a display-layer `deMath` applied (before esc) to lesson sentences AND the item-page summary
paragraph. It strips `$...$`/`$$...$$` ONLY when the inside looks like math (contains one of =\\^_{}
or has no whitespace); `$5 and $10 billion` style finance text is left alone (board-4 sources carry
real currency).

Lesson learned twice in one phase: the FIRST fix covered only lessonHTML and the live page still
showed 3 bare fragments from the summary paragraph -- caught by re-verifying online (9 -> 3 -> 0; the earlier '6' was a [:6] print slice).
This guard pins BOTH surfaces so neither regresses silently.

CI push has no Node; the behavioural proof lives in `arxiv-daily-push/tools/verify_lesson_demath.mjs`
(extracts shipped esc+deMath+lessonHTML, runs the observed NRR case, Greek letters, currency
preservation, unpaired-$ cases, plus a negative control proving the esc-only pre-fix render keeps the
bare $). This Python guard is the CI-safe anchor with its own negative control.
"""
import pathlib
import re
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKER = ROOT / "arxiv-daily-push" / "deploy" / "cloudflare" / "worker_cloud.js"
VERIFIER = ROOT / "arxiv-daily-push" / "tools" / "verify_lesson_demath.mjs"

# The exact pre-fix render lines (what shipped the bare $): esc() without deMath on both surfaces.
PRE_FIX_SNIPPET = r"""
    `<h3>${i + 1}. ${esc(s.title)}</h3>${(s.sentences || []).map(x => `<p>${esc(x.text)}</p>`).join('')}`).join('');
    ${item.summary ? `<p>${esc(item.summary)}</p>` : ''}
"""


def _demath_violations(src):
    """Defects that would let bare $math$ reach the reader. Empty == fixed."""
    v = []
    if "const deMath" not in src:
        v.append("deMath is missing entirely -- raw $...$ reaches the reader")
    if not re.search(r"esc\(deMath\(x\.text\)\)", src):
        v.append("lessonHTML renders sentences without deMath (bare $ in lesson body)")
    if not re.search(r"esc\(deMath\(item\.summary\)\)", src):
        v.append("item-page summary paragraph without deMath -- the exact surface the first fix "
                 "missed (live page kept 3 bare fragments)")
    return v


class TestAdpLessonDemath(unittest.TestCase):
    def setUp(self):
        self.assertTrue(WORKER.is_file(), "deployed worker missing: {}".format(WORKER))
        self.src = WORKER.read_text(encoding="utf-8")

    def test_shipped_worker_demaths_both_surfaces(self):
        self.assertEqual(
            _demath_violations(self.src), [],
            "shipped worker can render bare $math$ to the reader -- see violations above.")

    def test_demath_guards_currency(self):
        """The heuristic must keep the finance-text guard: only strip when inner looks like math."""
        m = re.search(r"const deMath = .*", self.src)
        self.assertIsNotNone(m, "deMath definition not found")
        line = m.group(0)
        self.assertIn("[=\\\\^_{}]", line,
                      "deMath lost its looks-like-math test -- it would strip '$5 and $10' finance text")
        self.assertIn("\\s", line,
                      "deMath lost its no-whitespace alternative -- '$1.0$' style would stay bare")

    def test_negative_control_prefix_code_is_flagged(self):
        """Non-vacuity: the detector must flag the exact pre-fix render (esc without deMath)."""
        viols = _demath_violations(PRE_FIX_SNIPPET)
        self.assertGreaterEqual(
            len(viols), 3,
            "detector did not flag the pre-fix esc-only render on all surfaces (got {}) -- it "
            "under-checks and could pass a regressed worker vacuously.".format(viols))

    def test_behavioural_verifier_exists(self):
        self.assertTrue(VERIFIER.is_file(), "behavioural verifier missing: {}".format(VERIFIER))
        body = VERIFIER.read_text(encoding="utf-8")
        self.assertIn("金融货币绝不动", body, "verifier lost its currency-preservation case")
        self.assertIn("负控", body, "verifier lost its negative control")

    @unittest.skipUnless(shutil.which("node"), "node not on PATH (CI push path); behavioural check runs locally")
    def test_behavioural_verifier_passes(self):
        r = subprocess.run(["node", str(VERIFIER)], capture_output=True, text=True, timeout=60, cwd=str(ROOT))
        self.assertEqual(r.returncode, 0,
                         "behavioural verifier failed:\nSTDOUT:\n{}\nSTDERR:\n{}".format(r.stdout, r.stderr))
        self.assertIn("负控成立", r.stdout, "negative control did not fire -- assertion not load-bearing")


if __name__ == "__main__":
    unittest.main()
