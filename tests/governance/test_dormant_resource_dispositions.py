#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: a dormant resource's recorded disposition must match what was actually done.

On 2026-07-20 the Owner decided "delete the dormant resources". Three were registered:

    adp-mirror worker  -> deleted (wrangler delete)          -- DONE by this line
    adp tunnel         -> deleted (Cloudflare API)           -- DONE by this line
    adp-origin DNS     -> NOT deleted; this line's credential is zone(read) only and the local
                          policy blocks DNS deletion, so it needs the Owner in the CF dashboard

The failure mode this guards is the one that would hurt most here: recording an authorised deletion
as done when it was not. A registry that says "deleted" for a record still resolving would send the
next agent (and the Owner) looking for a resource that is actually still live, and would quietly
retire a real to-do. It is the same "claimed but never verified" shape that independent review caught
three times in this program (pre-signed verdicts, an unrun breakage test, a live!=git drift).

So: every dormant entry whose `disposition` asserts completion ("已...删除") must NOT simultaneously
carry a hand-off marker, and every entry still needing the Owner must say so explicitly. The two
completed deletions are additionally pinned by name so a later edit cannot silently downgrade the
record of what was actually executed.
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "governance" / "infrastructure_registry.json"

DONE_RE = re.compile(r"已(?:于|用|经)?[^。;；]{0,60}删除")   # asserts the deletion happened (allows 已于 <date> 按 <who> 授权删除)
PENDING_RE = re.compile(r"需 Owner|待 Owner|Owner 在 Cloudflare|控制台")  # asserts it still needs a human


def _dormant():
    return json.loads(REGISTRY.read_text(encoding="utf-8")).get("dormant_resources", [])


class TestDormantResourceDispositions(unittest.TestCase):
    def setUp(self):
        self.assertTrue(REGISTRY.is_file(), "infrastructure registry missing: {}".format(REGISTRY))
        self.items = _dormant()

    def test_registry_has_dormant_entries(self):
        """Non-vacuity: the guard must be checking a real, non-empty set."""
        self.assertGreaterEqual(len(self.items), 3,
                                "expected the three registered dormant resources; found {}".format(len(self.items)))

    def test_no_entry_claims_done_and_pending_at_once(self):
        """A disposition cannot both assert 'already deleted' and 'still needs the Owner'."""
        contradictory = [
            i.get("resource_id") for i in self.items
            if DONE_RE.search(str(i.get("disposition", ""))) and PENDING_RE.search(str(i.get("disposition", "")))
        ]
        self.assertEqual(
            contradictory, [],
            "dormant entr(ies) claim BOTH completed deletion and pending Owner action: {}\n"
            "Pick one and make it true -- an ambiguous disposition is how a real to-do gets "
            "silently retired.".format(contradictory))

    def test_executed_deletions_stay_recorded_as_executed(self):
        """The two deletions this line actually performed must keep saying so (no silent downgrade)."""
        by_id = {i.get("resource_id"): str(i.get("disposition", "")) for i in self.items}
        for rid in ("adp-mirror-worker", "adp-tunnel"):
            self.assertIn(rid, by_id, "dormant entry {} disappeared from the registry".format(rid))
            self.assertRegex(
                by_id[rid], DONE_RE,
                "{} was actually deleted on 2026-07-20 (wrangler delete / Cloudflare API, each with a "
                "pre-delete identity+connection check); its disposition must keep recording that.".format(rid))

    def test_owner_pending_item_is_not_marked_done(self):
        """adp-origin DNS was NOT deleted -- this line has zone(read) only. It must not claim otherwise."""
        by_id = {i.get("resource_id"): str(i.get("disposition", "")) for i in self.items}
        self.assertIn("adp-origin-dns", by_id, "the adp-origin DNS entry disappeared from the registry")
        disp = by_id["adp-origin-dns"]
        self.assertRegex(
            disp, PENDING_RE,
            "adp-origin DNS still exists (this line cannot delete it: zone(read) credential + local "
            "policy blocks DNS deletion). Its disposition must keep saying the Owner has to do it in "
            "the dashboard -- marking it done would send people looking for a resource that is live.")


if __name__ == "__main__":
    unittest.main()
