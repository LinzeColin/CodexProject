# KM_IDSystem Agent Migration Handoff - 2026-07-16

## Verified state

- GitHub repository: `LinzeColin/CodexProject`
- Canonical project path: `KM_IDSystem/`
- Local pre-migration HEAD: `e1679d247986eb03665d440185e04dd56223a364`
- Local completed boundary: `IDS-V0_1-STAGE043-P1`; Phase 2 did not run.
- Reachable archive-introducing commit: `f37ae7af823173aef8a34d9eb491c5606ac4d929`
- Repository archive: `KM_IDSystem/governance/archive/local_handoff_20260716/`

P45 removed five duplicate/current-tree binary backup containers. Their exact
Git blob and SHA-256 identities remain documented in
`governance/archive/local_handoff_20260716/backup/RESTORE.md`; the retained mbox,
patch, status, chain, and candidate-check files remain checksum-covered. The old
machine-local backup directory is not claimed as a live recovery dependency.

## Why Stage041-043 remains archived

The prior replay preserved the repository-split deletions, but the Stage043
checker failed closed because the original Stage042 review commit is not an
ancestor of the rewritten main lineage. That red evidence is retained; this
cleanup does not promote it to acceptance.

## Next agent run

1. Start from current GitHub `main`.
2. Verify `backup/CHECKSUMS.sha256` and inspect the candidate-check evidence.
3. Use the retained mbox in an isolated branch if source replay is required.
4. Rebind commit-bound Stage041-043 evidence without restoring split-deleted files.
5. Recompute downstream artifact and contract hashes affected by that migration.
6. Run focused Stage041-043 tests, Stage005 regression, full discovery/render,
   and changed-scope governance before activation.
7. Review owner dirty files separately; the retained patch is preservation, not approval.
8. Keep legacy model assets archival until tied to approved real-source evidence.

## Non-negotiable boundaries

- Do not read or upload `IDS_MetaData` content.
- Do not use virtual IDS business data as production proof.
- Do not restore files intentionally deleted by the repository split.
- Do not merge while any hash or ancestry gate is red.
- Do not re-add removed binary backup containers to the public current tree.
