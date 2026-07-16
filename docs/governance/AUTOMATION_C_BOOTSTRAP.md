# Automation C Owner Bootstrap Checklist

Task: `TSK.CodexProject.REPO1.0002`
Acceptance: `ACC.CodexProject.REPO1.0002`

This checklist is executed only during the final whole-Task-Pack publication.
Local implementation does not authorize an early GitHub write.

## Before the one bootstrap exception

- [ ] Confirm the final package is based on the accepted clean history and the
      GitHub repository has `0` open PRs and `0` open Issues.
- [ ] Confirm all pre-existing non-main heads have their approved exact-tip
      retention treatment and a complete named-ref transaction plan.
- [ ] Configure `AUTOMATION_C_AUTHORIZED_ACTORS` to the explicit publisher
      allowlist and `AUTOMATION_C_MAX_AGE_MINUTES` to an integer in `5..1440`
      (default `15`).
- [ ] Create one same-repository, non-draft whole-package PR with the
      `AUTOMATION_C_TRANSACTION_V1` exact head/base marker from a reserved
      `automation-c/` branch. Do not use a repository PAT/App secret or
      `GITHUB_TOKEN` as the PR creator.
- [ ] Run `Project Governance`; record the exact PR, head SHA, tested base SHA,
      workflow run, `governance` check run, and repository settings before-image.

## Bootstrap and enforcement

- [ ] Use the single manual/native auto-merge exception to install the trusted
      default-branch Settlement/Janitor definition.
- [ ] Install a main ruleset requiring the `governance` check, blocking force
      pushes/deletions, and preventing bypass except the documented Owner
      recovery path. Preserve the settings before-image for rollback.
- [ ] Confirm Settlement has `actions/checks: read`, `contents` and
      `pull-requests: write`, plus `issues: write` used only to close an
      authorized exact-marker accidental Issue. Confirm there is no Issue
      creation, checkout, PR-code execution, artifact download, or cache restore.
- [ ] Run the Janitor in dry-run, review exact named actions, then run it once in
      write mode. It may touch only marker-bound PRs, unchanged exact reserved
      refs, and authorized exact-marker accidental Issues.
- [ ] For manual bootstrap settlement, bind the exact PR number, tested head,
      tested base, and successful `Project Governance` run ID.

## Acceptance evidence

- [ ] Prove success and every required failure fixture: failure, cancelled,
      timeout, action-required, conflict, draft, fork, unauthorized, stale head,
      stale tested base, superseded, duplicate, trusted orphan, accidental Issue,
      and required-check failure.
- [ ] Prove final open PR / open Issue / non-main branch = `0 / 0 / 0` and no
      Issue was created by Agent Loop.
- [ ] Record ruleset ID/hash, required-check name, workflow/run/check IDs,
      before/after refs, merge result, exact branch deletion, and SHA-256 evidence.

## Rollback

Revert the bootstrap merge, restore the recorded repository settings
before-image, disable the Settlement schedule, close only the marker-bound PR,
delete only its unchanged exact ref, and re-audit `0/0/0`. Never rewrite history
or restore the retired incident objects as part of this rollback.
