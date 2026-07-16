# Agent Loop Automation C

Automation C is a Zero-Open transaction pipeline. GitHub Issues are not a
queue, lock, audit log, or state machine. A transaction may create one
same-repository pull request; settlement must leave no open transaction PR and
no transaction branch.

## Roles and trust boundaries

| Role | Identity | Repository permission | Responsibility |
|---|---|---|---|
| Validator | `Agent Loop - Validate Approved Task Pack` | `contents: read` | Validate one approved Task Pack; never publish or settle |
| Publisher | External authenticated `gh` session | User-controlled | Publish one already-pushed, same-repository transaction branch as one PR |
| Required CI | `Project Governance / governance` | `contents: read` | Test the exact PR head without write permission or path filters |
| Settlement/Janitor | `Agent Loop Settlement` | `contents`/`pull-requests` write; cleanup-only `issues` write | Merge or close the exact transaction, delete only its exact branch ref, and close only authorized exact-marker accidental Issues |

Settlement and Janitor use the trusted default-branch workflow definition and
live GitHub APIs only. They do not checkout PR code, execute repository code,
download artifacts, restore caches, create Issues, or accept unbound branch
names.

## Transaction flow

1. Validate the dual-plane Task Pack locally or with the read-only validation
   workflow.
2. Implement and validate in an isolated worktree.
3. Push one temporary same-repository branch under the reserved
   `automation-c/` namespace using an external authenticated publisher.
   Repository workflows never receive publisher credentials.
4. Run `submit_taskpack.py` with `--confirm-publish`. It requires zero open PRs
   and zero standalone Issues, resolves the exact head/base SHAs, and creates
   one non-draft PR with an `AUTOMATION_C_TRANSACTION_V1` marker.
5. `Project Governance / governance` tests the exact PR head read-only.
6. Settlement verifies the marker, actor allowlist, same repository, non-draft
   state, `main` base, exact tested head/base, mergeability, and required check.
7. On success it squash-merges the exact head and deletes the exact ref. On a
   terminal failure it closes the PR and deletes only a trusted, marker-bound,
   exact ref. Unknown or untrusted refs fail closed.
8. Janitor runs every five minutes, reconciles only stale or duplicate
   marker-bound transactions, and closes an authorized exact-marker accidental
   Issue without using it as state. It never scans or deletes arbitrary branches.

## Stable identity contract

New governance objects use namespaced V2 IDs:

```text
TSK.<Project>.<Program>.NNNN
ACC.<Project>.<Program>.NNNN
PG.<Project>.<Program>.NNNN
```

Legacy V1 IDs remain readable. A Task/Acceptance pair must share namespace and
numeric suffix. Mixed V1/V2 references require an explicit project-scoped
alias; global fuzzy matching and suffix-only inference are forbidden.

## Local validation

```bash
python3 -B -m unittest discover -s tests/agent_loop -p 'test_*.py' -v
python3 -B scripts/agent_loop/validate_taskpack.py --taskpack TASKPACK.md
python3 -B scripts/agent_loop/submit_taskpack.py \
  --taskpack TASKPACK.md \
  --head automation-c/TSK.Project.Program.0001 \
  --dry-run-local
```

## Bootstrap and activation

Repository ruleset activation, final branch cleanup, and the single permitted
manual/native bootstrap settlement are owner operations. Until that final
activation run is evidenced, report `REMOTE_ACTIVATION_DEFERRED`; do not claim
that local code already enforces live GitHub settings. Follow
`docs/governance/AUTOMATION_C_BOOTSTRAP.md`.

## Protected control-plane paths

- `.github/workflows/agent-loop-*`
- `.github/workflows/project-governance.yml`
- `.github/PULL_REQUEST_TEMPLATE/codex-task.md`
- `.github/codex/prompts/**`
- `scripts/agent_loop/**`
- `scripts/governance_ids.py`
- `tests/agent_loop/**`
- `docs/governance/agent_loop/**`

Memory sync, backup, and history import processes must not rewrite these paths
unless the active Task Pack explicitly authorizes the change.
