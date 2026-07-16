# KM_IDSystem Local Handoff Archive - 2026-07-16

## Purpose

This directory preserves all KM_IDSystem development material found in the
canonical worktree and the legacy non-Git `opme-system` directory before an
agent migration. It is an archive and recovery surface, not an active runtime,
production-data source, or Stage acceptance claim.

## Source State

- Canonical worktree: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/KM_IDS`
- Source branch: `codex/ids-v0-1-stages-001-010`
- Source HEAD: `e1679d247986eb03665d440185e04dd56223a364`
- Previously merged batch baseline: `565babef3a610f289fed0da38b58e550b5707e3e`
- Latest source task: `IDS-V0_1-STAGE043-P1`
- GitHub main at archive preparation: `0aa4c1d726a6bdc483af7b840055a7d2808dbe51`

The source branch contains 12 commits after the prior batch baseline: one
merge-evidence commit, all Stage041 and Stage042 phases/reviews, and Stage043
Phase 1.

## Archive Classes

| Payload | Classification | Use |
|---|---|---|
| Original commit bundle and mbox | `VERIFIED_RECOVERY_SOURCE` | Recover the exact pre-migration commit chain. |
| HEAD project snapshot | `VERIFIED_RECOVERY_SOURCE` | Recover the tracked KM_IDSystem and required root governance/tooling tree. |
| Dirty patch and overlay | `UNREVIEWED_OWNER_WORK` | Preserve four local owner files without activating them on main. |
| Main-integration candidate | `BLOCKED_BY_HISTORY_REWRITE` | Starting point for a future hash-chain migration; do not merge directly. |
| Legacy Blender/GLB/DXF/Web package | `UNVERIFIED_AS_PRODUCTION` | Preserve the non-Git delivery package; documented assumptions prevent treating it as real production data. |

`backup/STAGE043-integration-candidate-check.json.txt` records the current blocking
fact: `stage042_review_commit_bound=false`. The replay candidate keeps main's
dual-plane file deletions, but the old commit-ancestry contract must be migrated
before Stage041-043 can become active on the rewritten main history.

## Integrity

From `backup/`:

```bash
LC_ALL=C shasum -a 256 -c CHECKSUMS.sha256
git bundle verify KM_IDS-local-commits-565babef-to-e1679d24.bundle
git bundle verify KM_IDS-main-integration-candidate.bundle
```

The source legacy package also has a per-file manifest in
`opme-system-files.sha256`. Its original eight-file delivery checksum passed
before this archive was created.

## Safety Boundary

- No active main file deleted by the repository-split migration is restored.
- No unreviewed launcher/dependency edit is applied to the active application.
- `.DS_Store`, dependencies, caches, runtime databases, reports, outputs,
  secrets, and generated app entries are excluded.
- `/Users/linzezhang/Downloads/IDS_MetaData` was not listed, read, opened,
  hashed, scanned, copied, modified, archived, or uploaded.
- The legacy model package explicitly contains assumptions and demonstration
  assumptions. It must stay archival until checked against an approved real
  source specification.

See `backup/RESTORE.md` and
`KM_IDSystem/docs/MIGRATION_HANDOFF_20260716.md` for recovery and continuation.
