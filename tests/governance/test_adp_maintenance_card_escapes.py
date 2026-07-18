#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: every DB-sourced value in the /system source-maintenance card is HTML-escaped.

P14's review round 1 found that `s.fails` was the ONLY DB-sourced value in `maintenanceHTML` not
passed through `esc()` -- breaking this file's own universal-escaping rule (even the controlled
`health` enum is escaped elsewhere) and creating a latent injection sink the unit test missed because
it only fed numeric fails. The fix was `${s.fails ? esc(s.fails) : '—'}`.

This guard reads the SHIPPED worker and pins that the maintenance card keeps escaping every DB value,
so a future edit that reintroduces a bare `${s.fails}` / `${s.id}` / `${s.board_id}` -- exactly the R1
defect -- fails here in CI rather than silently shipping. It is intentionally scoped to the three
DB-sourced fields the card renders; `health` goes through a fixed-string `badge()` and the numeric
summary fields are computed, not DB text.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKER = ROOT / "arxiv-daily-push" / "deploy" / "cloudflare" / "worker_cloud.js"


def _maintenance_html_body():
    src = WORKER.read_text(encoding="utf-8")
    # maintenanceHTML sits between its declaration and the following `async function systemPage`.
    m = re.search(r"function maintenanceHTML\(g\)\s*\{(.*?)\nasync function systemPage", src, re.S)
    return m.group(1) if m else None


class TestAdpMaintenanceCardEscapes(unittest.TestCase):
    def setUp(self):
        self.assertTrue(WORKER.is_file(), "deployed worker missing: {}".format(WORKER))
        self.body = _maintenance_html_body()
        self.assertIsNotNone(
            self.body,
            "could not locate maintenanceHTML in worker_cloud.js -- the card was renamed/removed or the "
            "systemPage anchor moved; update this guard deliberately, don't let it pass vacuously.")

    def test_source_id_is_escaped(self):
        self.assertIn("esc(s.id)", self.body, "source id must be HTML-escaped in the maintenance card")

    def test_board_is_escaped(self):
        self.assertRegex(self.body, r"esc\(BOARD_NAMES\[s\.board_id\]",
                         "board name must be HTML-escaped in the maintenance card")

    def test_consecutive_failures_is_escaped(self):
        """The R1 defect: s.fails rendered without esc(). Pin the fix."""
        self.assertIn("esc(s.fails)", self.body,
                      "consecutive_failures (s.fails) must be HTML-escaped -- this was the P14 round-1 "
                      "injection sink. A bare ${s.fails} must not return.")

    def test_no_bare_db_value_interpolation(self):
        """No `${s.<dbfield>}` for a DB-sourced field may appear outside an esc(...) wrapper."""
        offenders = []
        for field in ("id", "board_id", "fails"):
            # a bare `${s.<field>` not immediately preceded by `esc(` within the template
            for m in re.finditer(r"\$\{[^}]*\bs\." + field + r"\b[^}]*\}", self.body):
                frag = m.group(0)
                if "esc(s.{}".format(field) not in frag and "esc(BOARD_NAMES[s.{}".format(field) not in frag:
                    offenders.append(frag)
        self.assertEqual(
            offenders, [],
            "DB-sourced value(s) interpolated into HTML without esc(): {}\n"
            "Every DB value in the maintenance card must go through esc() (the R1 rule).".format(offenders))


if __name__ == "__main__":
    unittest.main()
