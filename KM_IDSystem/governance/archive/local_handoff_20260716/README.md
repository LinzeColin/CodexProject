# KM_IDSystem Local Handoff Archive - 2026-07-16

## Purpose

This directory preserves the text-based KM_IDSystem migration evidence needed
to continue the archived Stage041-043 work. It is a recovery surface, not an
active runtime, production-data source, or Stage acceptance claim.

## Verified source identity

- Source branch: `codex/ids-v0-1-stages-001-010`
- Source HEAD: `e1679d247986eb03665d440185e04dd56223a364`
- Previously merged baseline: `565babef3a610f289fed0da38b58e550b5707e3e`
- Latest source task: `IDS-V0_1-STAGE043-P1`
- Archive-introducing commit: `f37ae7af823173aef8a34d9eb491c5606ac4d929`

`f37ae7af...` is an ancestor of the current integration base and remains the
authoritative Git recovery point for the five binary payloads removed from the
current tree by `TSK.CodexProject.REPO1.0009` P45.

## Current-tree contents

The current tree retains the compressed mbox series, dirty tracked patch,
candidate-check result, commit-chain/status evidence, and legacy per-file
checksums. `backup/CHECKSUMS.sha256` covers every retained payload.

The following duplicate/current-tree backup containers were removed:

- `KM_IDS-HEAD-e1679d24-project-snapshot.tar.gz`
- `KM_IDS-local-commits-565babef-to-e1679d24.bundle`
- `KM_IDS-main-integration-candidate.bundle`
- `KM_IDS-working-tree-overlay.tar.gz`
- `opme-system-legacy-assets.tar.gz`

Their exact blob identities and recovery commands are recorded in
`backup/RESTORE.md`. No claim is made that the previously documented
machine-local backup directory still exists.

## Safety boundary

- No file intentionally removed by the repository-split migration is restored.
- No archived launcher/dependency edit is activated.
- Runtime databases, secrets, caches, generated app entries, and private owner
  data remain outside this public repository.
- `/Users/linzezhang/Downloads/IDS_MetaData` was not accessed by this cleanup.
- Legacy model material remains unverified as production data.

See `backup/RESTORE.md` and
`KM_IDSystem/docs/MIGRATION_HANDOFF_20260716.md` before continuation.
