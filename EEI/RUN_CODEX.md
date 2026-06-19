# Running Codex Safely

## Recommended sequence

```bash
git init
git add .
git commit -m "chore: add corporate power map governance task pack v4.2"

bash scripts/preflight.sh

codex exec --sandbox read-only - \
  < prompts/01_PLAN_ONLY.md \
  | tee artifacts/01_plan_output.txt

codex exec --sandbox workspace-write - \
  < prompts/02_BUILD_MVP.md \
  | tee artifacts/02_build_output.txt

codex exec --sandbox workspace-write - \
  < prompts/03_QA_RELEASE.md \
  | tee artifacts/03_qa_output.txt
```

Codex CLI supports non-interactive `codex exec`; use read-only for planning and workspace-write for implementation/QA. Keep the OS-enforced sandbox and approval policy at least privilege.

## Autonomous wrapper

```bash
bash scripts/run_codex_autonomous.sh
```

The wrapper stops after plan unless `AUTO_CONTINUE_AFTER_PLAN=1` is set. Review the plan before continuing.

## Network policy

Network is off by default. Enable only for:

- dependency bootstrap from approved registries;
- an optional, single-object SEC live smoke;
- checking official sources listed in `SOURCES.md`.

Record domains and purpose. Restore network-off immediately. Required tests must pass without live network.

## Checkpoints

- G0: plan/ADRs/acceptance mapping.
- G4: reroot interaction and graph budgets.
- G6: formula/weights/log/calibration behavior.
- G8: data semantics/provenance.
- G9: release evidence and rollback.

## Recovery

Prefer Git revert or a disposable worktree. Do not use destructive reset when uncommitted user data may exist.

```bash
docker compose down -v                 # disposable volumes only
uv run --project apps/api alembic downgrade -1
```
