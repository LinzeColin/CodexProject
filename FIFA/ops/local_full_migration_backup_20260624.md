# FIFA Local Full Migration Backup Audit

Updated: 2026-06-24 AEST

## Purpose

Prepare the TAB FIFA research system for migration to a new computer by backing up all local project data materials to GitHub-backed storage, then removing the legacy local workspace from this Mac.

## GitHub Backup Target

- Repository: `LinzeColin/CodexProject`
- Project path: `FIFA/`
- Backup directory: `FIFA/artifacts/backups/20260624/`

The standalone `LinzeColin/FIFA` repository was checked first but was not accessible from this machine:

- HTTPS clone required a GitHub username/password flow.
- SSH `git ls-remote git@github.com:LinzeColin/FIFA.git` returned `Repository not found`.

Therefore the durable backup target used for this run is the already established GitHub-backed `LinzeColin/CodexProject/FIFA` project.

## Backed Up Files

| File | Purpose |
| --- | --- |
| `runtime_outputs_snapshot_20260624.tar.gz` | Complete runtime snapshot of the legacy workspace `outputs/` plus root `HANDOFF.md`; excludes transient lock files only. |
| `runtime_outputs_20260624.sha256` | SHA-256 manifest for 241 non-lock runtime output files. |
| `legacy_workspace_HANDOFF_20260624.md` | Copy of the old root handoff from the legacy workspace before local deletion. |

## Backup Verification

- Source legacy workspace: `/Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa`
- Source size before deletion: about `38M`
- Source file count before deletion: `248`
- Runtime output file count in checksum manifest: `241`
- Tar listing count: `278` entries, including directories
- Archive size: about `8.2M` before copy, about `7.4M` on disk in the GitHub worktree
- Archive SHA-256: `70b60f7ac656f1e9c1ea38000e21367a23239db4773cbc3698f93bf7ec1c2c8e`

## Excluded From Backup

Only transient/non-data lock files were excluded:

- `outputs/.tab_fifa_daily_report 2.lock`
- `outputs/tab_fifa_reports.sqlite3.schema.lock`
- `outputs/tab_fifa_reports.sqlite3.schema 2.lock`

These are runtime lock artifacts and are safe to delete without backup under `docs/FILE_RETENTION_POLICY.md`.

## Secret Scan

Before backup, the legacy `outputs/` tree and root `HANDOFF.md` were scanned for:

- The known The Odds API key literal.
- `THE_ODDS_API_KEY`
- `OPTICODDS_API_KEY`
- common `password`, `otp`, `secret`, `cookie`, `session`, `token` terms.

No real API key was found in backed-up data. Matches were documentation/runtime code references only, including public notes saying keys are not emitted and a local HTML action-token helper.

## Local Deletion Plan

After the GitHub commit and push succeed, delete the legacy local system directory:

- `/Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa`

Do not delete unrelated CodexProject checkouts, browser profiles, Keychain, Chrome state, or non-FIFA project data.

## Restore On New Computer

1. Clone `LinzeColin/CodexProject`.
2. Enter `FIFA/`.
3. Read `FIFA/AGENTS.md`, `FIFA/docs/HANDOFF.md`, and this audit.
4. Restore runtime outputs if needed:

```bash
tar -xzf FIFA/artifacts/backups/20260624/runtime_outputs_snapshot_20260624.tar.gz
```

5. Continue development from `FIFA/tab-research-pipeline/`.

