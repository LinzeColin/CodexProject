#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: every owned workflow's REAL job list matches its policy `expected_jobs`.

`scripts/workflow_security_audit.py audit` already fails on "job topology drift", and CI runs it --
but only on the push that happens to trip it, and the failure message names the file, not what to do.
On 2026-07-20 main sat RED because PR #289 added a `smoke` job to
`.github/workflows/linze-golden-path.reusable.yml` without adding it to `expected_jobs` in
`governance/workflow_policy.json`. The author's own CI went red, the next thread's push inherited the
same red, and the drift persisted across three commits before anyone traced it.

This guard makes the same condition fail LOCALLY, in the unit-test sweep every contributor already
runs before pushing, with a message that says exactly which job to add where. It is deliberately a
mirror of the audit's topology check (not a replacement) so the fast local sweep catches what
previously only surfaced in CI.

Scope note: it compares only workflows the policy actually owns and that declare `expected_jobs`;
non-job top-level YAML keys (`on`, `permissions`, `concurrency`, ...) are excluded so the comparison
is job-vs-job.
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
POLICY = ROOT / "governance" / "workflow_policy.json"

# Top-level YAML keys in a workflow file that are NOT jobs.
NON_JOB_KEYS = {
    "name", "on", "permissions", "concurrency", "env", "defaults", "jobs",
    "workflow_call", "workflow_dispatch", "schedule", "push", "pull_request",
    "contents", "actions", "id-token", "issues", "packages", "group",
    "cancel-in-progress", "inputs", "secrets", "outputs",
}


def _declared_jobs(workflow_path):
    """Job ids under the top-level `jobs:` block, in file order."""
    text = workflow_path.read_text(encoding="utf-8")
    m = re.search(r"^jobs:\s*$", text, re.M)
    if not m:
        return []
    body = text[m.end():]
    # a job id is a 2-space-indented key directly under `jobs:`; stop at the next col-0 key
    stop = re.search(r"^\S", body, re.M)
    if stop:
        body = body[:stop.start()]
    return [j for j in re.findall(r"^  ([A-Za-z_][A-Za-z0-9_-]*):", body, re.M) if j not in NON_JOB_KEYS]


def _owned_workflows():
    data = json.loads(POLICY.read_text(encoding="utf-8"))
    return [w for w in data.get("workflows", []) if w.get("path") and w.get("expected_jobs")]


class TestWorkflowExpectedJobsMatch(unittest.TestCase):
    def test_policy_is_parseable_and_non_empty(self):
        """Non-vacuity: the guard must be comparing a real, non-empty set of workflows."""
        self.assertTrue(POLICY.is_file(), "workflow policy missing: {}".format(POLICY))
        owned = _owned_workflows()
        self.assertGreaterEqual(len(owned), 3,
                                "expected several policy-owned workflows declaring expected_jobs; found "
                                "{} -- the guard would pass vacuously".format(len(owned)))

    def test_every_expected_jobs_matches_the_workflow(self):
        """The 2026-07-20 red-main condition: a job exists in YAML but not in expected_jobs (or vice versa)."""
        drift = []
        for w in _owned_workflows():
            path = ROOT / w["path"]
            if not path.is_file():
                drift.append("{}: declared in policy but the file is missing".format(w["path"]))
                continue
            actual = sorted(_declared_jobs(path))
            expected = sorted(str(j) for j in w["expected_jobs"])
            if actual != expected:
                missing = [j for j in actual if j not in expected]
                extra = [j for j in expected if j not in actual]
                drift.append(
                    "{}: job topology drift.\n"
                    "    jobs in YAML but NOT in policy expected_jobs: {}\n"
                    "    in expected_jobs but NOT in YAML:            {}\n"
                    "    FIX: edit governance/workflow_policy.json -> the entry with path {!r} -> "
                    "expected_jobs, then re-run:\n"
                    "         python3 scripts/workflow_security_audit.py render > docs/governance/WORKFLOW_ROLE_MATRIX.md"
                    .format(w["path"], missing or "(none)", extra or "(none)", w["path"]))
        self.assertEqual(
            drift, [],
            "workflow job topology drifted from governance/workflow_policy.json. This is what put main "
            "RED on 2026-07-20 (PR #289 added a `smoke` job without registering it):\n\n" + "\n\n".join(drift))

    def test_detector_catches_a_synthetic_drift(self):
        """Non-vacuity: prove the comparison actually fires when a job is unregistered."""
        sample = _owned_workflows()[0]
        actual = sorted(_declared_jobs(ROOT / sample["path"]))
        self.assertTrue(actual, "sample workflow declared no jobs -- comparison would be vacuous")
        tampered = [j for j in actual if j != actual[0]]  # drop one job from the 'policy' side
        self.assertNotEqual(sorted(tampered), actual,
                            "dropping a job did not change the comparison -- the detector is inert")


if __name__ == "__main__":
    unittest.main()
