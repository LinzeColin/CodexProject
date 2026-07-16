# Agent Loop settlement policy

Automation C has one terminal settlement role. It never implements, reviews,
checks out, or executes PR code.

## `MERGE_DELETE`

Squash merge is allowed only when all gates are true:

- PR contains a valid `AUTOMATION_C_TRANSACTION_V1` marker;
- PR is open, same-repository, non-draft, based on `main`, and authored by an
  explicitly allowlisted publisher;
- live PR head/base equal the marker and the completed governance run SHAs;
- the exact `Project Governance / governance` check succeeded;
- GitHub reports the PR mergeable;
- branch ref still resolves to the exact tested head at deletion time.

After a successful exact-head merge, delete only that exact transaction ref.

## `CLOSE_DELETE`

A terminal trusted transaction is closed on failed/cancelled/timed-out CI,
draft, wrong base, stale binding, conflict, or required-check failure. Delete a
branch only when it is same-repository, marker-bound, and still points to the
exact expected head. Otherwise close or block as permitted, but do not delete
the unknown ref.

## `NOOP`, `WAIT`, and `BLOCK`

- Duplicate or already-settled events are idempotent `NOOP`.
- A non-terminal governance run waits without mutation.
- Forks, unauthorized publishers, malformed markers, unknown branches, or
  drifted refs fail closed and are never deleted.
- Janitor can delete an orphan only when marker, actor, repository, ref, and
  exact head binding are all trusted.
- An accidental Issue is closed only when its single marker and actor are
  trusted; it is never created or used as transaction state.

## Prohibited bypasses

- no direct push or workflow-owned publisher credential;
- no merge on a stale or merely similar SHA;
- no Issue labels as state;
- no artifact-derived settlement authority;
- no checkout, cache restore, or PR-code execution in the privileged role;
- no broad branch cleanup.
