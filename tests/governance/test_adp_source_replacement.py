#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: the P20 replacement feeds stay wired, and the reachability diagnosis stays honest.

P20 replaced 4 long-unreachable sources after probing candidate endpoints from a Cloudflare EDGE IP
(temporary `adp-probe` worker, deleted after use):

    cell / cell-neuron / lancet -> rss.sciencedirect.com official per-journal RSS  (edge: 200, 70/52/87 items)
    gnews-us-tech               -> bing.com/news/search ... format=rss             (edge: 200, 11 items)

The probe also OVERTURNED the implementer's own prior claim. The repo had recorded all six blocked
sources as "walled off by datacenter IP". Six edge samples of the production Google News URL returned
2x200 (78 items) and 4x503 -- Google News is NOT hard-walled, it is ~67% INTERMITTENT. The real cause
there is intermittent failure + no retry (3 consecutive failures trip `disabled_auto`). cell/lancet by
contrast returned 403 on 3/3. That distinction matters for the NEXT decision: adding retry/backoff to
the original Google News feed may make the Bing swap unnecessary.

This guard pins both halves:
  * the four feeds still point at the replacement endpoints (a silent revert re-breaks them), and
  * the source keeps the honest wording (`间歇 503`) so nobody re-flattens "intermittent" into "walled",
    which is exactly the over-generalisation this phase had to correct.

The behavioural proof (shipped parseFeed run over 4 real XML specimens + a 403-block-page negative
control) lives in `arxiv-daily-push/tools/verify_p20_replacement_feeds.mjs`; CI's push path has no
Node, so this Python guard is the CI-safe anchor and carries its own negative control.
"""
import pathlib
import re
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKER = ROOT / "arxiv-daily-push" / "deploy" / "cloudflare" / "worker_cloud.js"
VERIFIER = ROOT / "arxiv-daily-push" / "tools" / "verify_p20_replacement_feeds.mjs"
SPECIMENS = ROOT / "arxiv-daily-push" / "tools" / "specimens_p20"

REPLACEMENTS = {
    "cell": "https://rss.sciencedirect.com/publication/science/00928674",
    "cell-neuron": "https://rss.sciencedirect.com/publication/science/08966273",
    "lancet": "https://rss.sciencedirect.com/publication/science/01406736",
    "gnews-us-tech": "https://www.bing.com/news/search?q=FTC+antitrust&format=rss&mkt=en-US",
}
# The exact pre-P20 config (endpoints proven unreachable/intermittent from the edge).
PRE_FIX_SNIPPET = """
    { id: 'cell', method: 'rss', feed: 'https://www.cell.com/cell/current.rss' },
    { id: 'gnews-us-tech', platform: 'Google News RSS 聚合', method: 'rss', feed: 'https://news.google.com/rss/search?q=x' },
"""


def _replacement_violations(src):
    """Defects that would silently restore unreachable feeds or flatten the diagnosis. Empty == fixed."""
    v = []
    for sid, feed in REPLACEMENTS.items():
        if feed not in src:
            v.append("source {!r} no longer points at its P20 replacement endpoint {!r} -- a silent "
                     "revert puts it back on an endpoint the edge probe proved unusable".format(sid, feed))
    # honesty pin: gnews must stay recorded as INTERMITTENT, not as a hard wall
    if "间歇 503" not in src:
        v.append("the gnews reachability note lost its 『间歇 503』 wording -- P20 measured 2x200/4x503 "
                 "from the edge; recording it as a hard wall is the over-generalisation this phase "
                 "corrected, and it would hide that retry/backoff is the cheaper fix")
    return v


class TestAdpSourceReplacement(unittest.TestCase):
    def setUp(self):
        self.assertTrue(WORKER.is_file(), "deployed worker missing: {}".format(WORKER))
        self.src = WORKER.read_text(encoding="utf-8")

    def test_shipped_worker_uses_replacement_feeds(self):
        self.assertEqual(
            _replacement_violations(self.src), [],
            "shipped worker regressed on P20's replacement feeds / honest diagnosis -- see above.")

    def test_negative_control_prefix_config_is_flagged(self):
        """Non-vacuity: the detector must fire on the exact pre-P20 config (old feeds, no honesty note)."""
        viols = _replacement_violations(PRE_FIX_SNIPPET)
        self.assertGreaterEqual(
            len(viols), 5,
            "detector did not flag the pre-P20 config on all four feeds plus the honesty pin (got {}) -- "
            "it under-checks and could pass a regressed worker vacuously.".format(viols))

    def test_unresolved_sources_are_not_silently_dropped(self):
        """P20 fixed 4 of 6. The other two must remain registered (visible as unhealthy), not deleted.

        Quietly removing a source that cannot be fetched would make /system look clean while coverage
        silently shrank -- the same 'green while broken' shape this project keeps guarding against."""
        for sid in ("science-advances", "stats-gov"):
            self.assertIn("id: '{}'".format(sid), self.src,
                          "{} was removed from the registry instead of being left visibly unhealthy; "
                          "P20 fixed 4 of 6 sources and must not hide the remaining 2".format(sid))

    def test_behavioural_verifier_and_specimens_exist(self):
        self.assertTrue(VERIFIER.is_file(), "behavioural verifier missing: {}".format(VERIFIER))
        self.assertTrue(SPECIMENS.is_dir(), "XML specimens missing: {}".format(SPECIMENS))
        xmls = sorted(p.name for p in SPECIMENS.glob("*.xml"))
        self.assertGreaterEqual(len(xmls), 4,
                                "expected 4 real feed specimens for the replacement endpoints, found {}".format(xmls))

    @unittest.skipUnless(shutil.which("node"), "node not on PATH (CI push path); behavioural check runs locally")
    def test_behavioural_verifier_passes(self):
        r = subprocess.run(["node", str(VERIFIER)], capture_output=True, text=True, timeout=60, cwd=str(ROOT))
        self.assertEqual(r.returncode, 0,
                         "behavioural verifier failed:\nSTDOUT:\n{}\nSTDERR:\n{}".format(r.stdout, r.stderr))
        self.assertIn("负控成立", r.stdout, "negative control did not fire -- assertion not load-bearing")


if __name__ == "__main__":
    unittest.main()
