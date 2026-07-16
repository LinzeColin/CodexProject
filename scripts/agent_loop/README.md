# Agent Loop Scripts — Automation C

Agent Loop uses PRs as the only transaction object. It never creates or uses a
GitHub Issue as a lock, queue, audit log, failure state, or completion record.

## Roles

| Role | Trust and permissions |
|---|---|
| External publisher | Existing authenticated `gh` identity; creates one same-repository non-draft PR from an already-pushed temporary branch. |
| Project Governance | Required CI candidate; `contents: read`, executes PR code, no path filters and no repository write. |
| Settlement/Janitor | Trusted default-branch workflow; live APIs only, no checkout, PR code, artifact, or cache. Issue write is cleanup-only for one authorized, exact-marker accidental Issue; Issue creation is absent. |

`submit_taskpack.py` is the external publisher boundary. It validates the Task
Pack, requires `0` open PRs and `0` open Issues, binds exact head/base SHAs in a
transaction marker, and requires explicit `--confirm-publish`. The local dry
run performs no GitHub call:

```bash
python3 scripts/agent_loop/submit_taskpack.py \
  --taskpack path/to/taskpack.md \
  --head automation-c/task-id/idempotency-key \
  --dry-run-local
```

The file `.github/workflows/agent-loop-run-approved-taskpack.yml` is retained
as a compatibility-named **read-only validator**. It does not implement, create
a branch/PR, or merge. Real implementation happens in the external controlled
workspace; final settlement is handled by `agent-loop-settlement.yml`.

Core helpers remain stdlib-only: routing/autofill, Task Pack/plan/result
validation, changed-file policy, review helpers, summary, deterministic
settlement policy, and the external publisher.
