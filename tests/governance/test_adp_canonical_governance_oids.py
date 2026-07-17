#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression guard for the ADP canonical-governance large-object allowlist.

Why this exists: arxiv-daily-push's canonical governance files (delivery_tasks.yaml,
DEVELOPMENT_LEDGER.md, development_events.jsonl, parameter_registry.csv) legitimately exceed
the policy's `regular_blob_max_bytes`. They are covered by the ARXIV_CANONICAL_GOVERNANCE
retained rule whose `change_policy` is `baseline_oid_only`.

The hygiene audit accepts an oversized blob only if its OID either (a) still matches the
policy's `baseline_tree` for that path, or (b) is listed in `reviewed_oids`. So EVERY content
change to one of these files must register the file's new blob OID.

That per-change step was silently skipped from T088 onward, so the Project Governance
large-object hygiene audit failed on every push touching these files -- a red only visible by
reading CI logs. This test mirrors the audit's rule locally so the failure is nameable BEFORE
the push, and is written against the invariant (not a hardcoded OID list) so it keeps working
as the files grow.
"""
import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
POLICY = ROOT / "governance" / "repository_hygiene_policy.json"
RULE_ID = "ARXIV_CANONICAL_GOVERNANCE"


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def _worktree_oid(path: pathlib.Path) -> str:
    """The blob OID the working-tree content would commit as (content-addressed)."""
    return _git("hash-object", str(path)).stdout.strip()


def _baseline_oid(baseline_tree, rel):
    """The blob OID this path had in the policy's baseline tree, or None if absent there.

    Annotation-free on purpose: this test must run on the repo's oldest supported interpreter
    (3.9 locally) as well as CI's 3.12 -- a guard you cannot run locally cannot guard anything.
    """
    proc = _git("rev-parse", "{}:{}".format(baseline_tree, rel))
    return proc.stdout.strip() if proc.returncode == 0 else None


class TestAdpCanonicalGovernanceOids(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        rules = [r for r in self.policy.get("retained_objects", []) if r.get("id") == RULE_ID]
        self.assertEqual(len(rules), 1, f"expected exactly one {RULE_ID} rule in the hygiene policy")
        self.rule = rules[0]

    def test_rule_is_baseline_oid_only(self):
        """The guarded invariant only holds if the rule really is baseline_oid_only."""
        self.assertEqual(self.rule.get("change_policy"), "baseline_oid_only")

    def test_baseline_tree_is_resolvable(self):
        """The whole audit is anchored on baseline_tree; if it is unreachable the audit degrades to a
        confusing 'FAIL with violations: []'. That exact failure mode has bitten this repo before
        ('baseline_tree is not available'), so guard it explicitly rather than by inference."""
        baseline = str(self.policy.get("baseline_tree") or "")
        self.assertRegex(baseline, r"^[0-9a-f]{40}$", "baseline_tree must be a 40-char Git tree OID")
        proc = _git("cat-file", "-e", "{}^{{tree}}".format(baseline))
        self.assertEqual(proc.returncode, 0,
                         "baseline_tree {} is not resolvable in this clone -- the hygiene audit cannot "
                         "compare against it and will fail with an empty violations list".format(baseline[:12]))

    def test_changed_oversized_governance_files_have_their_oid_registered(self):
        prefix = self.rule.get("prefix")
        self.assertTrue(prefix and prefix.endswith("/"), "rule must use a directory prefix")
        max_bytes = int(self.rule["max_bytes"])
        limit = int(self.policy["regular_blob_max_bytes"])
        baseline_tree = str(self.policy["baseline_tree"])
        reviewed = set(self.rule.get("reviewed_oids", []))

        directory = ROOT / prefix
        self.assertTrue(directory.is_dir(), f"prefix directory missing: {prefix}")

        unregistered, oversize = [], []
        for path in sorted(p for p in directory.rglob("*") if p.is_file()):
            size = path.stat().st_size
            if size <= limit:
                continue  # small files need no retained-OID registration
            rel = path.relative_to(ROOT).as_posix()
            if size > max_bytes:
                oversize.append(f"{rel} ({size} > rule max_bytes {max_bytes})")
            oid = _worktree_oid(path)
            # The audit accepts an unchanged file (still at its baseline OID) without registration.
            if oid == _baseline_oid(baseline_tree, rel):
                continue
            if oid not in reviewed:
                unregistered.append(f"{rel} (oid {oid[:12]} differs from baseline and is not in reviewed_oids)")

        self.assertEqual(oversize, [], "file exceeds the retained rule's max_bytes:\n  " + "\n  ".join(oversize))
        self.assertEqual(
            unregistered, [],
            "Oversized canonical governance file(s) changed without registering the new blob OID in "
            f"{RULE_ID}.reviewed_oids -- the large-object hygiene audit WILL fail on push:\n  "
            + "\n  ".join(unregistered))


if __name__ == "__main__":
    unittest.main()
