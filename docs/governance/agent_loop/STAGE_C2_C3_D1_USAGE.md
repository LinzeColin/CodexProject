# C2/C3 retirement and D1 publisher contract

## Current status

| Interface | Status | Reason |
|---|---|---|
| C2 Issue-triggered Task Pack | Retired | Zero-Open forbids Issues as queue or state |
| C3 Issue Form / prefilled Issue | Retired | The Issue template and URL builder are removed |
| D1 external `gh` publisher | Supported | Publisher credentials remain outside repository automation |
| Read-only validation workflow | Supported | Validation only; no GitHub publishing mutation |

Historical retrospective and scorecard entries may mention C2/C3 runs. Those
records are evidence of the former design, not current operating instructions.

## D1 dry run

```bash
python3 -B scripts/agent_loop/submit_taskpack.py \
  --taskpack docs/governance/agent_loop/examples/minimal_t1_taskpack.md \
  --head automation-c/dry-run-example \
  --repo LinzeColin/CodexProject \
  --dry-run-local
```

This validates locally and performs no GitHub call.

## D1 publish

After an authorized external user has pushed the exact same-repository branch:

```bash
python3 -B scripts/agent_loop/submit_taskpack.py \
  --taskpack path/to/taskpack.md \
  --head automation-c/TSK.Project.Program.0001 \
  --base main \
  --repo LinzeColin/CodexProject \
  --confirm-publish
```

The script checks Zero-Open, reads exact remote SHAs, and creates one marker-
bound PR. It has no Issue, dispatch, or workflow-publish mode. Settlement is a
separate privileged role and never executes PR code.

## Stop conditions

Stop without publishing or settling if any of these is true:

- Task Pack validation fails;
- an open PR or standalone Issue already exists;
- the head is a fork, `main`, missing, or changes after validation;
- the publisher is not explicitly authenticated and authorized;
- the required governance check is absent or not bound to the exact head;
- the tested base no longer equals the PR base SHA;
- the live ruleset/bootstrap state is unknown.

The owner activation checklist is
`docs/governance/AUTOMATION_C_BOOTSTRAP.md`.
