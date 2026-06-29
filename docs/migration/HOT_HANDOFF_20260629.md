# 2026-06-29 Hot Handoff Migration Notes

This file is the GitHub-visible handoff for moving the active CodexProject work
from the old Mac to a new computer. It intentionally excludes secrets,
passwords, API keys, private SSH keys, local keychains, and Codex auth files.

## Canonical Source

- GitHub repository: `git@github.com:LinzeColin/CodexProject.git`
- Old Mac canonical checkout:
  `/Users/linzezhang/Documents/Codex/2026-06-19/current-phase-phase-0-goal-scope/work/CodexProject`
- Migration backup branch:
  `migration/hot-handoff-20260629-legacy-mac`

On the new computer, clone this repository and check out the migration branch
first. Do not treat sibling `CodexProject*`, `PFI_OS`, `EVA_OS`, or temporary
worktrees as the active product root.

## Project Classes

| Class | Projects | What must move |
| --- | --- | --- |
| Simple project transfer | `KMFA`, `PFI`, `QBVS`, `MetaDatabase`, `whkmSalary`, `FIFA`, `OpMe_System` | Source files, governance files, latest reports/evidence, and project handoff notes. |
| Observation-period transfer | `Alpha`, `EEI` | Source files plus current observation evidence. Do not turn observation progress into final acceptance on the new computer. |
| Launcher-backed transfer | `OpenAIDatabase`, `Serenity-Alipay` | Source files, LaunchAgents, app launcher references, database backup, and startup verification steps. |
| Active-development transfer | `arxiv-daily-push` | Source files and runner configuration metadata. Keep old Mac running until the new computer proves it can run the same checks. |

## GitHub-Visible Backup Contents

This backup includes:

- current source and test changes for `Alpha`
- current `PFI` v0.2.3 stage files and evidence folders
- current `KMFA` folder
- current `Serenity-Alipay` source, governance, reports, notifications, preflight outputs, and database snapshot
- current root governance/project registration changes
- LaunchAgent copies under `docs/migration/launchagents/`

This backup deliberately excludes:

- `.DS_Store`
- local cache folders
- live lock files
- SQLite `-wal` and `-shm` files
- `~/.codex/auth.json`
- SSH private keys
- API keys, OAuth tokens, and local keychain entries

## Runtime State

The old Mac had these project services listening during the migration audit:

| Project | Local port(s) | Old Mac cwd |
| --- | --- | --- |
| `Alpha` | `127.0.0.1:8000` | `CodexProject/Alpha` |
| `PFI` | `127.0.0.1:8501`, `127.0.0.1:8766` | `CodexProject/PFI` |
| `Serenity-Alipay` | `127.0.0.1:8765` | `CodexProject/Serenity-Alipay` |

Do not shut down the old Mac until the new computer has passed the matching
startup checks for these services.

## Serenity Database

`Serenity-Alipay/data/serenity_daily.sqlite` was live on the old Mac. To avoid
depending on a raw live WAL state, this migration includes:

```text
Serenity-Alipay/data/serenity_daily_migration_backup_20260629.sqlite
```

Use the migration backup database for new-computer bootstrap. Keep the original
database in the repo as historical continuity, but prefer the migration backup
when validating the exact handoff state.

## LaunchAgents

Copied LaunchAgent files are under:

```text
docs/migration/launchagents/
```

They preserve old-Mac command shape and paths for:

- ADP local daily runner
- ADP health check
- ADP watchdog
- Alpha dashboard
- Alpha phase6 owner-gate sampler
- OpenAIDatabase daily sync
- Serenity daily analysis

On the new computer, update paths before loading them. Do not load these files
unchanged unless the new checkout uses the same absolute path.

## New Computer First Checks

Run these checks after cloning:

```bash
git status --short
python3 scripts/lean_governance.py ci --changed-only --base-ref origin/main
```

Then check each project class:

```bash
# Simple projects
python3 -m pytest PFI/tests/test_v023_stage0_contract.py

# Observation projects
python3 -m pytest Alpha/tests/test_phase6_owner_gate.py Alpha/tests/test_owner_base_files.py

# Launcher-backed projects
sqlite3 Serenity-Alipay/data/serenity_daily_migration_backup_20260629.sqlite 'PRAGMA quick_check;'

# Active-development project
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push local-runner preflight --project-root arxiv-daily-push --json
```

If a command depends on local secrets, run only after restoring the matching
secret on the new computer.

## Off-GitHub Migration Items

These must be moved through an encrypted local migration package or manually
re-authenticated on the new computer:

- `~/.codex/auth.json`
- `~/.codex/config.toml`
- `~/.codex/memories/`
- `~/.codex/skills/`
- `~/.agents/skills/`
- `~/.agents/plugins/`
- SSH private keys under `~/.ssh/`
- app connector OAuth state
- macOS Keychain entries
- `.env` files and API tokens
- local SMTP credentials for ADP

GitHub is not the right place for these files because the repository is a
public backup surface.

## Stop Conditions

Stop migration and keep the old Mac active if any of these happen:

- new computer cannot start `Alpha`, `PFI`, or `Serenity-Alipay`
- Serenity database quick check fails
- ADP local preflight fails because of missing secrets or missing runtime state
- Codex on the new computer does not load global skills/MCP/plugins
- LaunchAgent paths still point to the old Mac
