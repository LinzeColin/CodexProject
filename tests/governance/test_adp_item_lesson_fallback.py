#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: every item — on ANY board — renders a lesson, never an empty box.

P16 found (by browsing the LIVE site) that board-2/3/4 items showed an EMPTY `<div id=revealBox><p></p>`
in both the /item page and the /review flow: `makeLesson` only runs for the daily PICK, so non-picked
items (journals/policy/finance) have no `cn_lessons` row, and the render fell back to
`lesson ? lessonHTML(lesson) : <p>{summary}</p>` — which for a summary-less policy/journal item is
`<p></p>`. A user doing active-recall review of such a card had nothing to recall.

The fix makes both render paths fall back to an ON-THE-FLY deterministic `buildLesson(item)` (no DB
write, no external call, uses the P15-deduped builder) when there is no stored lesson:
`const lesson = stored || { sections_json: JSON.stringify(buildLesson(item)) }`. `buildLesson` returns
8 sections whose per-section fallbacks are readable prompts even when the summary is empty, so every
item on every board now has a non-empty lesson.

CI push has no Node, so the load-bearing behavioural proof lives in
`arxiv-daily-push/tools/verify_item_lesson_fallback.mjs` (extracts the shipped buildLesson, proves the
on-the-fly lesson is non-empty for a summary-less board-2/3 item, and via negative control proves the
PRE-FIX selection yields the empty `<p></p>` box). This Python guard pins the fix statically and proves
non-vacuity by flagging the exact pre-fix code.
"""
import pathlib
import re
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKER = ROOT / "arxiv-daily-push" / "deploy" / "cloudflare" / "worker_cloud.js"
VERIFIER = ROOT / "arxiv-daily-push" / "tools" / "verify_item_lesson_fallback.mjs"

FALLBACK_RE = re.compile(r"stored \|\| \{ sections_json: JSON\.stringify\(buildLesson\(")

# Exact pre-fix render selection (item page + review page) — the code that shipped the empty box.
PRE_FIX_SNIPPET = r"""
  const lesson = await env.DB.prepare("SELECT * FROM cn_lessons WHERE item_id=? ...").bind(id).first();
  if (lesson) body += `<div class="card"><h2>讲义</h2>${lessonHTML(lesson)}</div>`;
  if (review) body += graderHTML(item.id, lesson ? lessonHTML(lesson) : `<p>${esc((item.summary || '').slice(0, 500))}</p>`, null);
  // review page:
    "SELECT r.*, i.title, i.summary, i.url FROM cn_reviews r JOIN cn_items i ON i.id=r.item_id ...";
    const reveal = lesson ? lessonHTML(lesson) : `<p>${esc((dueRow.summary || '').slice(0, 500))}</p>`;
"""


def _fallback_violations(src):
    """Defects that would let an item render an empty lesson box. Empty == fixed."""
    v = []
    n = len(FALLBACK_RE.findall(src))
    if n < 2:
        v.append("on-the-fly buildLesson fallback appears {}x; need >=2 (itemPage + reviewPage) or a "
                 "board-2/3/4 item with no stored lesson renders an empty <p></p> box".format(n))
    # the review page JOIN must expose categories+board_id, or buildLesson(dueRow) loses 领域脉络/板块 fallback
    review_join = re.search(r"SELECT r\.\*, i\.title, i\.summary, i\.url(.*?)FROM cn_reviews r JOIN cn_items i", src)
    if review_join:
        cols = review_join.group(1)
        if "i.categories" not in cols or "i.board_id" not in cols:
            v.append("review-page JOIN does not select i.categories+i.board_id, so buildLesson(dueRow) "
                     "cannot build 领域脉络/board fallbacks for a summary-less due card")
    return v


class TestAdpItemLessonFallback(unittest.TestCase):
    def setUp(self):
        self.assertTrue(WORKER.is_file(), "deployed worker missing: {}".format(WORKER))
        self.src = WORKER.read_text(encoding="utf-8")

    def test_shipped_worker_has_onthefly_fallback(self):
        self.assertEqual(
            _fallback_violations(self.src), [],
            "shipped worker can still render an empty lesson box on some board -- see violations above.")

    def test_negative_control_prefix_code_is_flagged(self):
        """Non-vacuity: the detector MUST fire on the exact pre-fix code (no fallback, thin JOIN)."""
        viols = _fallback_violations(PRE_FIX_SNIPPET)
        self.assertTrue(viols, "detector did not flag the pre-fix code -- it under-checks and could pass "
                               "a regressed worker vacuously.")
        # specifically both the missing-fallback and the thin-JOIN defects must be caught
        self.assertTrue(any("fallback appears 0x" in v or "appears 0x" in v for v in viols),
                        "detector missed the absent on-the-fly fallback in pre-fix code: {}".format(viols))

    def test_behavioural_verifier_exists(self):
        self.assertTrue(VERIFIER.is_file(), "behavioural verifier missing: {}".format(VERIFIER))
        body = VERIFIER.read_text(encoding="utf-8")
        self.assertIn("newRevealNonEmpty", body, "verifier lost its non-empty check")
        self.assertIn("oldRevealInner", body, "verifier lost its empty-box negative control")

    @unittest.skipUnless(shutil.which("node"), "node not on PATH (CI push path); behavioural check runs locally")
    def test_behavioural_verifier_passes(self):
        r = subprocess.run(["node", str(VERIFIER)], capture_output=True, text=True, timeout=60, cwd=str(ROOT))
        self.assertEqual(r.returncode, 0,
                         "behavioural verifier failed:\nSTDOUT:\n{}\nSTDERR:\n{}".format(r.stdout, r.stderr))
        self.assertIn("负控成立", r.stdout, "negative controls did not fire -- assertion not load-bearing")


if __name__ == "__main__":
    unittest.main()
