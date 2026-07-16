# Run an approved Task Pack

The supported path is local/read-only validation followed by an explicit
external publisher. Issue triggers, Issue Forms, `repository_dispatch`, and a
workflow-owned publisher are retired.

## 1. Validate without GitHub mutation

```bash
python3 -B scripts/agent_loop/validate_taskpack.py --taskpack TASKPACK.md
python3 -B scripts/agent_loop/submit_taskpack.py \
  --taskpack TASKPACK.md \
  --head automation-c/TSK.Project.Program.0001 \
  --dry-run-local
```

The optional `Agent Loop - Validate Approved Task Pack` workflow performs the
same class of read-only validation. It has `contents: read` permission and does
not create an Issue, branch, PR, artifact, or merge.

## 2. Prepare one transaction branch

- Work in an isolated checkout.
- Use a temporary same-repository branch under `automation-c/`; forks and
  unreserved refs are not accepted.
- Run all Task Pack validation commands before publishing.
- Push the branch with an external authenticated user identity. Do not store a
  PAT or publisher credential in repository variables, secrets, workflows, or
  artifacts.

## 3. Publish one PR explicitly

```bash
python3 -B scripts/agent_loop/submit_taskpack.py \
  --taskpack TASKPACK.md \
  --head automation-c/TSK.Project.Program.0001 \
  --base main \
  --repo LinzeColin/CodexProject \
  --confirm-publish
```

The publisher fails closed unless:

- the Task Pack is valid;
- `base` is `main` and `head` is a non-main branch;
- `gh auth status` succeeds externally;
- there are zero open PRs and zero standalone Issues;
- both remote refs resolve to exact 40-character SHAs.

It creates one non-draft PR containing the exact Task ID, Acceptance ID, head
SHA, and base SHA. It does not create Issues or trigger a publishing workflow.

## 4. Read the result

`Project Governance / governance` is the required read-only CI role. The
trusted settlement workflow then chooses exactly one terminal action:

- `MERGE_DELETE`: squash-merge the exact validated head, then delete that ref;
- `CLOSE_DELETE`: close a failed trusted transaction, then delete that exact
  ref;
- `NOOP` or fail closed: already-settled, non-transaction, unknown, or
  untrusted state.

After settlement, verify open PRs, standalone Issues, and transaction branches
are all zero. If the live ruleset or first settlement has not been activated by
the owner, record `REMOTE_ACTIVATION_DEFERRED` rather than claiming completion.

## Troubleshooting

- `single-flight precheck failed`: settle existing open work before publishing.
- `branch tip drifted`: do not retry deletion; inspect who moved the ref.
- `stale_head` or `stale_tested_base`: create a fresh transaction against the
  current `main`.
- `unauthorized_actor`, `fork`, or `non_transaction_pr`: settlement must not
  execute or delete the untrusted ref.
- required check failure: fix the implementation in a new bounded transaction;
  do not bypass the governance role.
