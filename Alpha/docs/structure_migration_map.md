# Alpha S4PBT01 Structure Migration Map

Task: `S4PBT01`
Acceptance: `ACC-S4PBT01`
Date: 2026-06-25

## Scope

This map records the reversible structure simplification for Alpha. It moves
historical outputs and the reconstructed handoff out of the active Alpha project
root while keeping source code, tests, configs, and the private sample data path
unchanged.

## Old To New Paths

| Old path | New path | Status |
|---|---|---|
| `Alpha/HANDOFF.md` | `governance/archive/other8_wave1_pending/Alpha/HANDOFF.md` | archived |
| `Alpha/outputs/**` | `governance/archive/other8_wave1_pending/Alpha/outputs/**` | archived |
| `Alpha/data/sample_prices.csv` | `Alpha/data/sample_prices.csv` | unchanged; PRIVATE owner-review path |

## Compatibility Notes

- Source imports, test paths, configs, launcher scripts, and runtime state paths
  are unchanged.
- The old `Alpha/outputs/**` files were historical patch bundles and
  repository-local launchers; no active source or test reference consumed them
  at S4PBT01 implementation time.
- Future runtime or local output under `Alpha/outputs/` is ignored by
  `.gitignore` and should not become a tracked daily-development surface.
- The archived files remain checksum-bound by
  `governance/stage_gates/s4pa/wave1_archive_manifest.sha256`.
- If a migrated file's current checkout byte form differs from the S4PAT02
  historical checksum entry, the S4PBT01 run manifest records a reconciliation
  entry with both the historical checksum and the archived worktree checksum.

## Rollback

Rollback is a git revert of the S4PBT01 task commit. If manual restoration is
needed, restore each archived path from
`governance/archive/other8_wave1_pending/Alpha/` to its old `Alpha/` path and
verify checksums against `governance/stage_gates/s4pa/wave1_archive_manifest.sha256`.

## Stop Conditions Preserved

- Alpha automatic loop behavior changed: no.
- Alpha source import path changed: no.
- PRIVATE `Alpha/data/sample_prices.csv` moved or archived: no.
- Live-trading readiness promoted: no.
