# KM_IDS Migration Backup

Created: 2026-07-16 11:15:26 Australia/Sydney

## Source Identity

- Canonical worktree: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/KM_IDS`
- Branch: `codex/ids-v0-1-stages-001-010`
- HEAD: `e1679d247986eb03665d440185e04dd56223a364`
- Bundle prerequisite: `565babef3a610f289fed0da38b58e550b5707e3e`
- Repository: `git@github.com:LinzeColin/CodexProject.git`

## Backup Contents

- `KM_IDS-local-commits-565babef-to-e1679d24.bundle`: 12 local commits after the previously merged batch baseline.
- `KM_IDS-local-commits.mbox.gz`: compressed binary full-index patch series for the same 12 commits.
- `KM_IDS-main-integration-candidate.bundle`: 11 Stage041-043 commits replayed onto `origin/main` at `0aa4c1d7...`, preserving main's deleted dual-plane views.
- `KM_IDS-main-integration-candidate.mbox.gz`: compressed patch series for that replay candidate.
- `STAGE043-integration-candidate-check.json.txt`: fail-closed JSON evidence showing the replay candidate still requires commit-ancestry rebinding before active merge.
- `KM_IDS-HEAD-e1679d24-project-snapshot.tar.gz`: tracked KM_IDSystem and required root governance/tooling snapshot at HEAD.
- `KM_IDS-dirty-tracked.patch.gz`: compressed binary patch for the three modified tracked owner files.
- `KM_IDS-working-tree-overlay.tar.gz`: the three modified tracked files plus untracked `frontend/pnpm-workspace.yaml`.
- `opme-system-legacy-assets.tar.gz`: legacy non-Git Blender/GLB/DXF/Web/document assets, excluding `.DS_Store`.
- `opme-system-files.sha256`: source-file checksums for the legacy asset directory.
- `git-status-porcelain-v2.txt`: pre-migration worktree state.
- `local-commit-chain.tsv`: ordered local commit chain.
- `CHECKSUMS.sha256`: checksums for all backup payloads and this restore guide.

## Verify

```bash
cd /Users/linzezhang/Documents/Codex/backups/CodexProject/KM_IDS-migration-20260716T111526+1000
LC_ALL=C shasum -a 256 -c CHECKSUMS.sha256
git bundle verify KM_IDS-local-commits-565babef-to-e1679d24.bundle
```

## Restore Commits

Clone or open `LinzeColin/CodexProject` with prerequisite commit `565babef...`, then:

```bash
git fetch /absolute/path/KM_IDS-local-commits-565babef-to-e1679d24.bundle HEAD:refs/heads/recovery/km-ids-e1679d24
```

Alternative patch recovery:

```bash
gzip -dc KM_IDS-local-commits.mbox.gz | git am --3way
```

## Restore Working Overlay

Extract `KM_IDS-working-tree-overlay.tar.gz` at the repository root. The tracked-only alternative is:

```bash
gzip -dc KM_IDS-dirty-tracked.patch.gz | git apply --3way
```

## Boundaries

- `.DS_Store`, dependencies, caches, runtime databases, reports, outputs, secrets, and app-generated files are excluded.
- `/Users/linzezhang/Downloads/IDS_MetaData` was not listed, read, hashed, copied, archived, modified, or uploaded.
- Legacy `opme-system` assets contain documented assumptions and are backup material until separately classified; they are not proof of real production data.
- The main-integration candidate is not release-ready: `stage042_review_commit_bound=false` because main history was rewritten. Do not merge it as active Stage043 code until the hash-bound evidence chain is migrated and the full suite passes.
- This backup does not itself prove GitHub `main` synchronization. Remote verification is a separate gate.
