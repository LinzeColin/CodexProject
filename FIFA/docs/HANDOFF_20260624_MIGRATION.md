# TAB FIFA Migration Handoff

Updated: 2026-06-24 AEST

## Current Objective

Migrate the TAB FIFA research system to a new computer by ensuring GitHub contains the complete code, docs, public-safe artifacts, runtime data snapshot, development records, feature list, model parameter files, and recovery instructions. After GitHub push is verified, remove the old local workspace from this Mac.

## Current Status

- Canonical GitHub-backed project path is `LinzeColin/CodexProject/FIFA`.
- Standalone `LinzeColin/FIFA` was attempted but is not currently accessible from this machine.
- Source code and project docs already live under `FIFA/tab-research-pipeline/`, `FIFA/docs/`, `FIFA/ops/`, `FIFA/AGENTS.md`, `FIFA/功能清单`, `FIFA/开发记录`, and `FIFA/模型参数文件`.
- Runtime data backup for the old local workspace has been staged in `FIFA/artifacts/backups/20260624/`.
- The old local workspace scheduled for deletion is `/Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa`.

## Key Decisions

- Back up first, delete only after commit and push are verified.
- Do not upload real TAB credentials, OTP, cookies, Chrome profile databases, private account snapshots, or real API keys.
- Exclude only transient lock files from the 20260624 runtime snapshot.
- Preserve unrelated `arxiv-daily-push` changes in the same CodexProject worktree by staging only `FIFA/` paths.

## Files Added In This Migration Run

- `FIFA/artifacts/backups/20260624/runtime_outputs_snapshot_20260624.tar.gz`
- `FIFA/artifacts/backups/20260624/runtime_outputs_20260624.sha256`
- `FIFA/artifacts/backups/20260624/legacy_workspace_HANDOFF_20260624.md`
- `FIFA/ops/local_full_migration_backup_20260624.md`
- `FIFA/docs/HANDOFF_20260624_MIGRATION.md`

## Verification Commands

```bash
shasum -a 256 FIFA/artifacts/backups/20260624/runtime_outputs_snapshot_20260624.tar.gz
git status --short -- FIFA
git log -1 --oneline -- FIFA
git ls-remote origin HEAD
```

Expected archive SHA-256:

```text
70b60f7ac656f1e9c1ea38000e21367a23239db4773cbc3698f93bf7ec1c2c8e
```

## Remaining Risks

- The standalone `LinzeColin/FIFA` repository is not usable until access is fixed or the repo is created.
- The `CodexProject` worktree has unrelated arxiv changes; do not stage or revert them during FIFA migration.
- Runtime status is still research/reporting focused; full formal automation remains blocked by raw/provider/My Bets gates described in the existing handoff.

## Next Step

Commit and push the `FIFA/` migration backup files. After remote push proof is available, delete the old local workspace directory and report exact deleted size/count.

