#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every workflow ON DISK must be registered in governance/workflow_policy.json.

Why this exists: `scripts/workflow_security_audit.py` enumerates workflows via `git ls-files`
(TRACKED files). So a newly created, not-yet-committed workflow is INVISIBLE to it — running the
audit locally returns PASS, and the failure only appears in CI after the push, as
`unowned workflows: .github/workflows/<new>.yml`. That is exactly how the six-theme visual gate
workflow turned Project Governance red: the pre-commit audit was vacuous for the very file being added.

This test reads the WORKING TREE instead, so an unregistered workflow fails locally BEFORE the push.
It deliberately does not re-implement the audit's other rules (pins/permissions/triggers) — the audit
owns those; this only closes the tracked-vs-worktree blind spot.
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
POLICY = ROOT / "governance" / "workflow_policy.json"
WORKFLOW_DIR = ROOT / ".github" / "workflows"


class TestWorkflowPolicyCoversAllWorkflows(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        self.entries = {str(w["path"]): w for w in self.policy.get("workflows") or [] if w.get("path")}

    def test_every_workflow_on_disk_is_registered(self):
        on_disk = sorted(
            p.relative_to(ROOT).as_posix()
            for p in WORKFLOW_DIR.glob("*.y*ml")
            if p.is_file()
        )
        self.assertTrue(on_disk, "no workflows found on disk -- test would be vacuous")
        unregistered = [p for p in on_disk if p not in self.entries]
        self.assertEqual(
            unregistered, [],
            "workflow(s) on disk but NOT in governance/workflow_policy.json -- the CI workflow audit "
            "will fail with 'unowned workflows' after you push:\n  " + "\n  ".join(unregistered))

    def test_policy_does_not_reference_missing_workflows(self):
        stale = [p for p in sorted(self.entries) if not (ROOT / p).is_file()]
        self.assertEqual(stale, [],
                         "workflow_policy.json references workflow(s) that no longer exist:\n  " + "\n  ".join(stale))

    def test_role_matrix_is_rendered_from_the_policy(self):
        """docs/governance/WORKFLOW_ROLE_MATRIX.md is a DERIVED view of workflow_policy.json. Editing the
        policy without re-rendering it makes CI fail with `workflow role matrix drift` — which is exactly
        what happened when the visual-gate workflow was registered. `render` writes to stdout (there is no
        --write), so the regeneration step is easy to forget; assert the sync locally instead.
        """
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "workflow_security_audit", ROOT / "scripts" / "workflow_security_audit.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # Call the SAME entry point CI calls -- no skip fallback: a guard that quietly skips is not a guard.
        report = mod.check_render(root=ROOT)
        self.assertEqual(
            report["status"], "PASS",
            "WORKFLOW_ROLE_MATRIX.md is out of sync with workflow_policy.json ({}). Regenerate it:\n"
            "  python3 -B scripts/workflow_security_audit.py render > docs/governance/WORKFLOW_ROLE_MATRIX.md"
            .format(report.get("errors")))

    def test_registered_roles_are_unique(self):
        """The audit counts duplicate roles; a copy-pasted entry that forgets to change `role` would
        otherwise sail through this test while failing CI."""
        roles = [w.get("role") for w in self.policy.get("workflows") or []]
        dupes = sorted({r for r in roles if r and roles.count(r) > 1})
        self.assertEqual(dupes, [], "duplicate workflow roles in policy: {}".format(dupes))


if __name__ == "__main__":
    unittest.main()
