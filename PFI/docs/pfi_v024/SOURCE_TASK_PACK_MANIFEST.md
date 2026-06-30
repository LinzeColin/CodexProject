# PFI v0.2.4 Source Task Pack Manifest

## Source Files

| Source | Path | Role |
| --- | --- | --- |
| Repair roadmap | `/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md` | User-provided roadmap for the repair package. |
| Repair task pack | `/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip` | User-provided Codex task pack and reference material. |

The source package uses `v0.2.3-repair` naming. The user has defined this
thread's target as `v0.2.4`, so repo artifacts for this run use `pfi_v024`
paths and `v0.2.4` target metadata.

## Current Main Reconciliation

The task pack's `GITHUB_CURRENT_AUDIT.md` says public GitHub `main` lacked
`PFI/docs/pfi_v023`, `stage_v023_*`, and `test_v023_*` material. That statement
is stale for the current checkout after the v0.2.3 closeout commit:

- `PFI/docs/pfi_v023` exists.
- v0.2.3 test files exist.
- `PFI/web/app/shell.js` currently passes `node --check`.

Pre stage 0 records this mismatch as source-context drift. It does not use the
stale audit to undo current v0.2.3 closeout evidence.

