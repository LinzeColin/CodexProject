# KM_IDSystem Agent Migration Handoff - 2026-07-16

## Verified State

- GitHub repository: `LinzeColin/CodexProject`
- Canonical project path: `KM_IDSystem/`
- Latest GitHub main inspected during backup: `0aa4c1d726a6bdc483af7b840055a7d2808dbe51`
- Local pre-migration HEAD: `e1679d247986eb03665d440185e04dd56223a364`
- Local completed boundary: `IDS-V0_1-STAGE043-P1`; Phase 2 did not run.
- Open GitHub PRs and issues before publishing this archive: `0` and `0`.
- Local backup root:
  `/Users/linzezhang/Documents/Codex/backups/CodexProject/KM_IDS-migration-20260716T111526+1000`
- Repository archive:
  `KM_IDSystem/governance/archive/local_handoff_20260716/`

## Why Stage041-043 Is Archived First

GitHub main was rewritten after the earlier batch merge. Replaying the 11
Stage041-043 commits onto current main preserved the new dual-plane deletions,
but the Stage043 checker failed closed because the original Stage042 review
commit is no longer an ancestor of the rewritten main history. Other staged
commit bindings require the same controlled migration review.

The active replay was therefore not merged. Both the exact original history
and a current-main replay candidate are preserved as verified bundles and mbox
series. This prevents data loss without publishing a false green gate.

## Next Agent Run

1. Start from current GitHub `main`, not the old long-lived branch.
2. Verify `backup/CHECKSUMS.sha256` and both bundles.
3. Inspect `STAGE043-integration-candidate-check.json.txt`.
4. Migrate commit-bound evidence from the old Stage041-043 hashes to the new
   main lineage without restoring main-deleted dual-plane files.
5. Recompute any downstream artifact hashes and exact canonical contract
   digests affected by that migration.
6. Run focused Stage041-043 tests, Stage005 governance regression, full v0.1
   discovery, render, and changed-scope governance before activation.
7. Review the four owner dirty files separately. Their exact patch and overlay
   are archived; they are not approved active code.
8. Keep the legacy Blender/GLB/DXF/Web package archival until its specification
   is tied to approved real source evidence.

## Recovery

Exact commands and prerequisites are in
`governance/archive/local_handoff_20260716/backup/RESTORE.md`.

## Non-Negotiable Boundaries

- Do not read or upload `IDS_MetaData` content.
- Do not use virtual IDS business data.
- Do not restore files intentionally deleted by the repository-split migration.
- Do not merge the integration candidate while any hash/ancestry check is red.
